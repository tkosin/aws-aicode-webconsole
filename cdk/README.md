# AWS Code-Server Multi-Developer Environment - CDK

AWS CDK (Python) implementation for deploying a multi-developer code-server environment on AWS Bangkok region (ap-southeast-7).

## Overview

This project deploys infrastructure for **8 developers**, each with their own isolated code-server (VS Code in Browser) instance with Claude AI Extension, running in Docker containers on a single EC2 instance.

### Architecture

```
Internet → Route53 → ALB (HTTPS) → EC2 (Docker Containers × 8) → EBS Volume
                                     ↓
                              Secrets Manager
                              CloudWatch
```

### Features

- ✅ **8 isolated code-server instances** (one per developer)
- ✅ **Individual HTTPS subdomains** (dev1-dev8.yourdomain.com)
- ✅ **SSL/TLS encryption** via ACM certificate
- ✅ **Auto-generated passwords** stored in AWS Secrets Manager
- ✅ **Persistent workspaces** on EBS volume (500 GB)
- ✅ **Health monitoring** with CloudWatch
- ✅ **Daily backups** with AWS Backup
- ✅ **Infrastructure as Code** with AWS CDK

## Prerequisites

### Required Software

- **Python 3.9+**
- **Node.js 14+** (for AWS CDK CLI)
- **AWS CLI v2**
- **pip** (Python package manager)

### AWS Requirements

- **AWS Account** with admin permissions
- **AWS CLI configured** with credentials
- **Domain name** with Route53 hosted zone
- **SSH key pair** named `code-server-admin-key` (or change in config)

### Install AWS CDK

```bash
# Install CDK CLI globally
npm install -g aws-cdk

# Verify installation
cdk --version
```

## Quick Start

### 1. Clone and Setup

```bash
cd cdk/

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate.bat  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

Edit `config/prod.py`:

```python
# IMPORTANT: Update these values!
BASE_DOMAIN = "yourdomain.com"  # Your domain
ROUTE53_HOSTED_ZONE_ID = "Z1234567890ABC"  # Your hosted zone ID
ADMIN_SSH_CIDR = "1.2.3.4/32"  # Your IP address
```

### 3. Bootstrap CDK (One-time)

```bash
# Get your AWS account ID
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

# Bootstrap CDK in Bangkok region
cdk bootstrap aws://$AWS_ACCOUNT/ap-southeast-7
```

### 4. Deploy

```bash
# Option 1: Use deploy script (recommended)
bash scripts/deploy.sh

# Option 2: Manual deployment
cdk deploy --all
```

**Deployment takes approximately 20-30 minutes.**

## Post-Deployment Steps

### 1. Update Claude API Keys

```bash
# Update secrets in AWS Secrets Manager
for i in {1..8}; do
  aws secretsmanager update-secret \
    --secret-id code-server-multi-dev/dev${i}/claude-api-key \
    --secret-string "YOUR_ACTUAL_CLAUDE_API_KEY" \
    --region ap-southeast-7
done
```

### 2. Get EC2 Instance IP

```bash
INSTANCE_ID=$(aws cloudformation describe-stacks \
  --stack-name code-server-multi-dev-compute \
  --query 'Stacks[0].Outputs[?OutputKey==`InstanceId`].OutputValue' \
  --output text)

INSTANCE_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "Instance IP: $INSTANCE_IP"
```

### 3. SSH to EC2 and Setup Containers

```bash
# SSH to instance
ssh -i ~/.ssh/code-server-admin-key.pem ubuntu@$INSTANCE_IP

# On EC2 instance:
# Create .env file with passwords from Secrets Manager
cd /home/ubuntu

# Fetch secrets and create .env
for i in {1..8}; do
  PASSWORD=$(aws secretsmanager get-secret-value \
    --secret-id code-server-multi-dev/dev${i}/password \
    --region ap-southeast-7 \
    --query SecretString \
    --output text)

  CLAUDE_KEY=$(aws secretsmanager get-secret-value \
    --secret-id code-server-multi-dev/dev${i}/claude-api-key \
    --region ap-southeast-7 \
    --query SecretString \
    --output text)

  echo "DEV${i}_PASSWORD=${PASSWORD}" >> .env
  echo "DEV${i}_CLAUDE_KEY=${CLAUDE_KEY}" >> .env
done

# Copy docker-compose.yml (or create from the one in scripts/)
# Start containers
docker-compose up -d

# Check status
docker-compose ps
```

### 4. Get Passwords

```bash
# Get password for developer 1
aws secretsmanager get-secret-value \
  --secret-id code-server-multi-dev/dev1/password \
  --query SecretString \
  --output text
```

### 5. Access Code-Server

After DNS propagation (5-10 minutes), access:

- Developer 1: https://dev1.yourdomain.com
- Developer 2: https://dev2.yourdomain.com
- ... (and so on)

## Project Structure

```
cdk/
├── app.py                      # CDK app entry point
├── cdk.json                    # CDK configuration
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── config/
│   ├── common.py               # Shared configuration
│   └── prod.py                 # Production config (edit this!)
│
├── stacks/
│   ├── network_stack.py        # VPC, Subnets, Security Groups
│   ├── security_stack.py       # IAM, Secrets Manager
│   ├── compute_stack.py        # EC2, EBS
│   ├── loadbalancer_stack.py   # ALB, Target Groups
│   ├── dns_stack.py            # Route53, ACM Certificate
│   └── monitoring_stack.py     # CloudWatch, Backup
│
└── scripts/
    ├── deploy.sh               # Deployment script
    ├── destroy.sh              # Cleanup script
    └── docker-compose.yml      # Docker Compose for containers
```

## CDK Commands

```bash
# Synthesize CloudFormation templates
cdk synth

# List all stacks
cdk list

# Show differences for a stack
cdk diff code-server-multi-dev-network

# Deploy specific stack
cdk deploy code-server-multi-dev-network

# Deploy all stacks
cdk deploy --all

# Destroy all stacks
cdk destroy --all
```

## Useful Commands

### View Stack Outputs

```bash
# Get all outputs from compute stack
aws cloudformation describe-stacks \
  --stack-name code-server-multi-dev-compute \
  --query 'Stacks[0].Outputs'
```

### View Logs

```bash
# View CloudWatch logs
aws logs tail /aws/ec2/code-server-multi-dev/system --follow

# View container logs on EC2
ssh -i ~/.ssh/code-server-admin-key.pem ubuntu@$INSTANCE_IP
docker logs code-server-dev1
```

### Restart Containers

```bash
# On EC2 instance
docker-compose restart

# Restart specific container
docker-compose restart code-server-dev1
```

### Update Code-Server Image

```bash
# On EC2 instance
docker-compose pull
docker-compose up -d
```

## Cost Estimation

**Monthly cost in Bangkok region (ap-southeast-7):**

- EC2 t3.2xlarge (on-demand): ~$273/month
- EBS 500GB: ~$48/month
- ALB: ~$27/month
- Data Transfer: ~$50/month
- CloudWatch/Backup: ~$20/month
- **Total: ~$420-450/month** (~$53-56 per developer)

**Cost Optimization:**
- Use 1-year Reserved Instance: Save ~21% ($95/month)
- Use 3-year Reserved Instance: Save ~32% ($145/month)

## Troubleshooting

### Issue: CDK bootstrap failed

```bash
# Ensure you have correct region
export AWS_DEFAULT_REGION=ap-southeast-7

# Bootstrap again
cdk bootstrap
```

### Issue: Certificate validation pending

ACM certificate validation can take 5-30 minutes. Check status:

```bash
aws acm describe-certificate \
  --certificate-arn YOUR_CERT_ARN \
  --region ap-southeast-7
```

### Issue: Cannot access subdomains

1. Check DNS propagation: `dig dev1.yourdomain.com`
2. Check ALB target health:
   ```bash
   aws elbv2 describe-target-health \
     --target-group-arn YOUR_TG_ARN
   ```
3. Check security groups allow HTTPS (443)

### Issue: Containers not starting

```bash
# SSH to EC2 and check
docker ps -a
docker logs code-server-dev1

# Check if EBS is mounted
df -h | grep ebs-data

# Check if directories exist
ls -la /mnt/ebs-data/
```

## Maintenance

### Adding Developer 9

1. Update `config/prod.py`: `NUM_DEVELOPERS = 9`
2. Run `cdk deploy --all`
3. Update docker-compose.yml with new container
4. Restart containers

### Backup and Restore

**Automatic Backups:**
- Daily backups at 2 AM UTC
- 30-day retention
- Managed by AWS Backup

**Manual Backup:**
```bash
aws ec2 create-snapshot \
  --volume-id vol-xxxxx \
  --description "Manual backup"
```

**Restore from Snapshot:**
```bash
# Create volume from snapshot
aws ec2 create-volume \
  --snapshot-id snap-xxxxx \
  --availability-zone ap-southeast-7a

# Attach to new instance (via CDK or console)
```

## Cleanup

### Destroy All Infrastructure

```bash
# Option 1: Use destroy script (recommended)
bash scripts/destroy.sh

# Option 2: Manual destruction
cdk destroy --all --force
```

**Note:** EBS volume will create a final snapshot before deletion.

## Security Considerations

- ✅ All traffic encrypted with HTTPS
- ✅ Passwords stored in AWS Secrets Manager
- ✅ SSH access restricted to admin IP
- ✅ Individual workspaces (no cross-access)
- ✅ CloudWatch logging enabled
- ⚠️ Update `ADMIN_SSH_CIDR` in config to your IP!
- ⚠️ Rotate passwords regularly
- ⚠️ Review security groups before production

## Support

- CDK Documentation: https://docs.aws.amazon.com/cdk/
- Code-Server Docs: https://coder.com/docs/code-server
- Claude API Docs: https://docs.anthropic.com/

## License

This project is provided as-is for educational and development purposes.

---

**Version:** 1.0
**Last Updated:** 2026-01-16
**Region:** ap-southeast-7 (Bangkok)
