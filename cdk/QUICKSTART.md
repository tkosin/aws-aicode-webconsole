# AWS Code-Server CDK - Quick Start Guide

## 🚀 5-Minute Deployment Guide

### Prerequisites Check

```bash
# Check required tools
python3 --version  # Should be 3.9+
node --version     # Should be 14+
aws --version      # Should be v2
cdk --version      # Should be 2.x
```

### Step 1: Configure (2 minutes)

```bash
cd cdk/

# Edit config/prod.py (if needed - already set to tuworkshop.vibecode.letsrover.ai)
nano config/prod.py
```

**Change this value:**
```python
ADMIN_SSH_CIDR = "1.2.3.4/32"           # ⚠️ Change to YOUR IP for security!
```

**Note**: `BASE_DOMAIN` is already set to `tuworkshop.vibecode.letsrover.ai`

**Note**: This deployment does NOT use Route53. You will create CNAME records manually at your DNS provider after deployment (see Step 6).

### Step 2: Setup Environment (2 minutes)

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Bootstrap CDK (one-time per account/region)
export AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
cdk bootstrap aws://$AWS_ACCOUNT/ap-southeast-7
```

### Step 3: Deploy (1 minute to start, 20-30 minutes to complete)

```bash
# Deploy all stacks
bash scripts/deploy.sh

# Or manually:
cdk deploy --all
```

### Step 4: Post-Deployment (5 minutes)

```bash
# 1. Get EC2 IP
INSTANCE_ID=$(aws cloudformation describe-stacks --stack-name code-server-multi-dev-compute --query 'Stacks[0].Outputs[?OutputKey==`InstanceId`].OutputValue' --output text)
INSTANCE_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

# 2. SSH and setup containers
ssh -i ~/.ssh/code-server-admin-key.pem ubuntu@$INSTANCE_IP

# 3. On EC2, fetch secrets and start containers
cd /home/ubuntu
for i in {1..8}; do
  PASSWORD=$(aws secretsmanager get-secret-value --secret-id code-server-multi-dev/dev${i}/password --region ap-southeast-7 --query SecretString --output text)
  echo "DEV${i}_PASSWORD=${PASSWORD}" >> .env
done

# Note: No Claude API keys needed! Using AWS Bedrock with IAM authentication

# 4. Copy docker-compose.yml to EC2
exit  # Back to local machine
scp -i ~/.ssh/code-server-admin-key.pem scripts/docker-compose.yml ubuntu@$INSTANCE_IP:/home/ubuntu/

# 5. SSH back and start containers
ssh -i ~/.ssh/code-server-admin-key.pem ubuntu@$INSTANCE_IP
docker-compose up -d
docker-compose ps
```

### Step 5: Enable Bedrock Model Access

```bash
# IMPORTANT: Enable Claude model access in AWS Bedrock Console
# 1. Go to: https://ap-southeast-1.console.aws.amazon.com/bedrock/
# 2. Click "Model access" in left sidebar
# 3. Click "Manage model access"
# 4. Enable these models:
#    ✅ Claude 3 Haiku
#    ✅ Claude 3 Sonnet
#    ✅ Claude 3.5 Sonnet
#    ✅ Claude Sonnet 4.5
# 5. Click "Save changes"
# 6. Wait 2-5 minutes for access to be granted

# Verify access (run from EC2):
aws bedrock list-foundation-models \
  --region ap-southeast-1 \
  --query 'modelSummaries[?contains(modelId, `claude`)].modelId' \
  --output table
```

### Step 6: Setup DNS (10-15 minutes)

**⚠️ IMPORTANT**: This deployment does NOT use Route53. You must manually create DNS records at your DNS provider.

#### 6.1 Get Required Information

```bash
# Get ALB DNS name from CDK outputs
aws cloudformation describe-stacks \
  --stack-name code-server-multi-dev-loadbalancer \
  --query 'Stacks[0].Outputs[?OutputKey==`ALBDNSName`].OutputValue' \
  --output text \
  --region ap-southeast-7

# Example output: code-server-multi-dev-alb-123456789.ap-southeast-7.elb.amazonaws.com
```

#### 6.2 Add Certificate Validation CNAME

1. Go to **AWS Certificate Manager Console** (Singapore region): https://ap-southeast-1.console.aws.amazon.com/acm/
2. Click on your certificate for `*.tuworkshop.vibecode.letsrover.ai`
3. Copy the DNS validation CNAME record (Name and Value)
4. Go to your DNS provider's control panel
5. Add the validation CNAME record
6. Wait 5-30 minutes for certificate to be validated

**Example validation record:**
```
Name: _abc123def456.tuworkshop.vibecode.letsrover.ai
Type: CNAME
Value: _xyz789uvw012.acm-validations.aws.
```

#### 6.3 Add Developer Subdomain CNAMEs

At your DNS provider, create these CNAME records:

```
dev1.tuworkshop.vibecode.letsrover.ai  →  code-server-multi-dev-alb-xxx.ap-southeast-7.elb.amazonaws.com
dev2.tuworkshop.vibecode.letsrover.ai  →  code-server-multi-dev-alb-xxx.ap-southeast-7.elb.amazonaws.com
dev3.tuworkshop.vibecode.letsrover.ai  →  code-server-multi-dev-alb-xxx.ap-southeast-7.elb.amazonaws.com
dev4.tuworkshop.vibecode.letsrover.ai  →  code-server-multi-dev-alb-xxx.ap-southeast-7.elb.amazonaws.com
dev5.tuworkshop.vibecode.letsrover.ai  →  code-server-multi-dev-alb-xxx.ap-southeast-7.elb.amazonaws.com
dev6.tuworkshop.vibecode.letsrover.ai  →  code-server-multi-dev-alb-xxx.ap-southeast-7.elb.amazonaws.com
dev7.tuworkshop.vibecode.letsrover.ai  →  code-server-multi-dev-alb-xxx.ap-southeast-7.elb.amazonaws.com
dev8.tuworkshop.vibecode.letsrover.ai  →  code-server-multi-dev-alb-xxx.ap-southeast-7.elb.amazonaws.com
```

Replace `code-server-multi-dev-alb-xxx.ap-southeast-7.elb.amazonaws.com` with your actual ALB DNS name.

**See detailed instructions**: [CNAME_SETUP.md](../CNAME_SETUP.md)

#### 6.4 Verify DNS Propagation

```bash
# Check if CNAME is working
dig dev1.tuworkshop.vibecode.letsrover.ai CNAME

# Or use online tool
# https://dnschecker.org/
```

#### 6.5 Access! 🎉

Once DNS has propagated (5-60 minutes), access:

- https://dev1.tuworkshop.vibecode.letsrover.ai
- https://dev2.tuworkshop.vibecode.letsrover.ai
- (... dev3-dev8)

**Get passwords:**

```bash
aws secretsmanager get-secret-value \
  --secret-id code-server-multi-dev/dev1/password \
  --query SecretString \
  --output text \
  --region ap-southeast-7
```

### Step 7: Configure Claude Code Extension

After logging in to code-server:

1. Install **Claude Code** extension in VS Code
2. Configure for AWS Bedrock (see [CLAUDE_CODE_BEDROCK_SETUP.md](../CLAUDE_CODE_BEDROCK_SETUP.md))
3. Set API endpoint to: `https://bedrock-runtime.ap-southeast-1.amazonaws.com`
4. Set region to: `ap-southeast-1`
5. Authentication will use EC2 IAM role automatically (no API key needed)

**Quick settings:**

```json
{
  "claude.apiEndpoint": "https://bedrock-runtime.ap-southeast-1.amazonaws.com",
  "claude.authType": "aws",
  "claude.awsRegion": "ap-southeast-1",
  "claude.modelId": "anthropic.claude-3-sonnet-20240229-v1:0"
}
```

---

## 🛠️ Common Commands

### View Outputs
```bash
cdk deploy --all --outputs-file outputs.json
cat outputs.json
```

### View Logs
```bash
# CloudWatch logs
aws logs tail /aws/ec2/code-server-multi-dev/system --follow

# Container logs (on EC2)
docker logs -f code-server-dev1
```

### Restart Everything
```bash
# On EC2
docker-compose restart
```

### Destroy
```bash
bash scripts/destroy.sh
```

---

## 📋 Checklist

- [ ] Python 3.9+ installed
- [ ] AWS CLI v2 configured
- [ ] CDK CLI installed (`npm install -g aws-cdk`)
- [ ] Access to DNS provider (Cloudflare, GoDaddy, etc.) for creating CNAME records
- [ ] SSH key pair created (`code-server-admin-key`)
- [ ] Updated `config/prod.py` with your IP address
- [ ] CDK bootstrapped
- [ ] Deployed all stacks (`cdk deploy --all`)
- [ ] Added certificate validation CNAME at DNS provider
- [ ] Certificate validated in AWS Certificate Manager
- [ ] Added developer subdomain CNAMEs (dev1-dev8) at DNS provider
- [ ] Verified DNS propagation
- [ ] Enabled Bedrock model access in Singapore (ap-southeast-1)
- [ ] Started Docker containers on EC2
- [ ] Tested access to all subdomains (dev1-dev8)
- [ ] Configured Claude Code extension for Bedrock in each environment

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| CDK not found | `npm install -g aws-cdk` |
| Bootstrap failed | Check AWS credentials and region |
| Deploy failed | Check error message, may need to fix config |
| Can't SSH | Check security group allows your IP |
| Containers won't start | Check `docker logs`, verify EBS is mounted |
| Certificate stuck on "Pending" | Add validation CNAME at DNS provider, wait 5-30 min |
| Can't access subdomain | Verify CNAME records exist, check DNS propagation (`dig` command) |
| SSL certificate error | Wait for certificate validation in ACM, hard refresh browser |
| "Too many redirects" (Cloudflare) | Set SSL mode to "Full (strict)" in Cloudflare dashboard |
| Claude Code auth fails | Enable Bedrock model access in Singapore console |
| Bedrock not available | Bangkok doesn't have Bedrock - using Singapore |

**Detailed troubleshooting**: See [CNAME_SETUP.md](../CNAME_SETUP.md)

---

## 💰 Cost

**Infrastructure: ~$420-450/month** for 8 developers in Bangkok region

- EC2: $273/month (t3.2xlarge)
- Storage: $48/month (500GB EBS)
- ALB: $27/month
- Other: $70/month (CloudWatch, backups, etc.)

**AWS Bedrock (Claude API):** Variable based on usage

- Light usage (1M tokens/dev/month): ~$18/dev = $144/month total
- Medium usage (10M tokens/dev/month): ~$180/dev = $1,440/month total
- Heavy usage (50M tokens/dev/month): ~$900/dev = $7,200/month total

**Cross-region data transfer** (Bangkok → Singapore Bedrock):

- First 10TB: $0.09/GB
- Estimate: ~$5-20/month depending on usage

**Total estimated cost: $570-$8,000/month** (infrastructure + Claude API)

**Save 21-32% with Reserved Instances** (infrastructure only)

---

## 📚 Full Documentation

See [README.md](README.md) for complete documentation.

---

**Ready to deploy? Run:** `bash scripts/deploy.sh`
