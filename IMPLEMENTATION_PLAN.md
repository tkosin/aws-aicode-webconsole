# Implementation Plan - AWS Multi-Developer Code-Server Environment

## Executive Summary

แผนการ implement ระบบ Multi-developer Code-Server environment บน AWS Region Bangkok (ap-southeast-7) สำหรับนักพัฒนา 8 คน โดยใช้ **AWS CLI + Shell Scripts + Docker Compose** แทน Terraform เพื่อความง่ายและยืดหยุ่น

## Implementation Approach

**Method**: Shell Scripts + AWS CLI + Docker Compose
- ✅ ไม่ต้องเรียนรู้ framework ใหม่
- ✅ ควบคุมได้ทุกขั้นตอน
- ✅ Debug ง่าย
- ✅ เหมาะกับ single EC2 deployment

---

## Phase 0: Prerequisites & Validation

### 0.1 ข้อมูลที่ต้องเตรียม

**Domain & DNS:**
- [ ] Domain name (e.g., `dev.example.com`)
- [ ] Route53 hosted zone ID
- [ ] Access to domain registrar (for NS records)

**AWS Account:**
- [ ] AWS Account ID
- [ ] IAM user with Admin permissions
- [ ] AWS CLI installed และ configured
- [ ] Default region set to `ap-southeast-7`

**Secrets:**
- [ ] 8 code-server passwords (16+ chars)
- [ ] 8 Claude API keys (หรือ 1 shared key)
- [ ] Admin SSH key pair

**Local Tools:**
- [ ] AWS CLI v2 (latest)
- [ ] jq (JSON processor)
- [ ] OpenSSL (for password generation)
- [ ] Git (for version control)

### 0.2 Environment Variables Setup

สร้างไฟล์ `.env` สำหรับเก็บ configuration:

```bash
# AWS Configuration
AWS_REGION=ap-southeast-7
AWS_ACCOUNT_ID=123456789012
AVAILABILITY_ZONE=ap-southeast-7a

# Domain Configuration
BASE_DOMAIN=dev.example.com
ROUTE53_HOSTED_ZONE_ID=Z1234567890ABC

# EC2 Configuration
EC2_INSTANCE_TYPE=t3.2xlarge
EC2_AMI_ID=ami-xxxxxxxxx  # Ubuntu 22.04 LTS in ap-southeast-7
EC2_KEY_NAME=code-server-admin-key
ADMIN_SSH_IP=1.2.3.4/32   # Your IP for SSH access

# Storage Configuration
EBS_DATA_VOLUME_SIZE=500  # GB
EBS_ROOT_VOLUME_SIZE=50   # GB

# Container Configuration
NUM_DEVELOPERS=8
CONTAINER_BASE_PORT=8443

# Project Name (for tagging)
PROJECT_NAME=code-server-multi-dev
ENVIRONMENT=production
```

### 0.3 Validation Script

```bash
#!/bin/bash
# scripts/00-validate-prerequisites.sh

echo "Validating prerequisites..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not installed"
    exit 1
fi
echo "✅ AWS CLI installed"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured"
    exit 1
fi
echo "✅ AWS credentials valid"

# Check region
if [ "$(aws configure get region)" != "ap-southeast-7" ]; then
    echo "⚠️  AWS region is not ap-southeast-7"
fi

# Check jq
if ! command -v jq &> /dev/null; then
    echo "❌ jq not installed"
    exit 1
fi
echo "✅ jq installed"

# Check .env file
if [ ! -f .env ]; then
    echo "❌ .env file not found"
    exit 1
fi
echo "✅ .env file exists"

echo "✅ All prerequisites validated"
```

---

## Phase 1: Network Infrastructure (VPC, Subnets, IGW)

**Duration:** 15-20 minutes
**Dependencies:** None

### 1.1 Create VPC

```bash
#!/bin/bash
# scripts/01-create-vpc.sh

source .env

# Create VPC
VPC_ID=$(aws ec2 create-vpc \
    --cidr-block 10.0.0.0/16 \
    --region $AWS_REGION \
    --tag-specifications "ResourceType=vpc,Tags=[
        {Key=Name,Value=${PROJECT_NAME}-vpc},
        {Key=Project,Value=${PROJECT_NAME}},
        {Key=Environment,Value=${ENVIRONMENT}}
    ]" \
    --query 'Vpc.VpcId' \
    --output text)

echo "VPC ID: $VPC_ID"

# Enable DNS hostnames
aws ec2 modify-vpc-attribute \
    --vpc-id $VPC_ID \
    --enable-dns-hostnames \
    --region $AWS_REGION

# Save VPC ID to file
echo "VPC_ID=$VPC_ID" >> infrastructure.env
```

### 1.2 Create Subnets (Multi-AZ for ALB)

```bash
#!/bin/bash
# scripts/02-create-subnets.sh

source .env
source infrastructure.env

# Public Subnet AZ-A (for EC2)
SUBNET_A_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.1.0/24 \
    --availability-zone ${AWS_REGION}a \
    --tag-specifications "ResourceType=subnet,Tags=[
        {Key=Name,Value=${PROJECT_NAME}-public-subnet-a},
        {Key=Project,Value=${PROJECT_NAME}}
    ]" \
    --query 'Subnet.SubnetId' \
    --output text)

# Public Subnet AZ-B (for ALB)
SUBNET_B_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.2.0/24 \
    --availability-zone ${AWS_REGION}b \
    --tag-specifications "ResourceType=subnet,Tags=[
        {Key=Name,Value=${PROJECT_NAME}-public-subnet-b},
        {Key=Project,Value=${PROJECT_NAME}}
    ]" \
    --query 'Subnet.SubnetId' \
    --output text)

echo "SUBNET_A_ID=$SUBNET_A_ID" >> infrastructure.env
echo "SUBNET_B_ID=$SUBNET_B_ID" >> infrastructure.env

# Enable auto-assign public IP
aws ec2 modify-subnet-attribute \
    --subnet-id $SUBNET_A_ID \
    --map-public-ip-on-launch

aws ec2 modify-subnet-attribute \
    --subnet-id $SUBNET_B_ID \
    --map-public-ip-on-launch
```

### 1.3 Create Internet Gateway

```bash
#!/bin/bash
# scripts/03-create-igw.sh

source .env
source infrastructure.env

# Create IGW
IGW_ID=$(aws ec2 create-internet-gateway \
    --tag-specifications "ResourceType=internet-gateway,Tags=[
        {Key=Name,Value=${PROJECT_NAME}-igw},
        {Key=Project,Value=${PROJECT_NAME}}
    ]" \
    --query 'InternetGateway.InternetGatewayId' \
    --output text)

# Attach to VPC
aws ec2 attach-internet-gateway \
    --vpc-id $VPC_ID \
    --internet-gateway-id $IGW_ID

echo "IGW_ID=$IGW_ID" >> infrastructure.env

# Create route table
RTB_ID=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications "ResourceType=route-table,Tags=[
        {Key=Name,Value=${PROJECT_NAME}-public-rtb},
        {Key=Project,Value=${PROJECT_NAME}}
    ]" \
    --query 'RouteTable.RouteTableId' \
    --output text)

# Add route to IGW
aws ec2 create-route \
    --route-table-id $RTB_ID \
    --destination-cidr-block 0.0.0.0/0 \
    --gateway-id $IGW_ID

# Associate with subnets
aws ec2 associate-route-table --subnet-id $SUBNET_A_ID --route-table-id $RTB_ID
aws ec2 associate-route-table --subnet-id $SUBNET_B_ID --route-table-id $RTB_ID

echo "RTB_ID=$RTB_ID" >> infrastructure.env
```

**Validation:**
```bash
aws ec2 describe-vpcs --vpc-ids $VPC_ID
aws ec2 describe-subnets --subnet-ids $SUBNET_A_ID $SUBNET_B_ID
aws ec2 describe-internet-gateways --internet-gateway-ids $IGW_ID
```

---

## Phase 2: Security Groups

**Duration:** 10 minutes
**Dependencies:** Phase 1 (VPC)

### 2.1 Create ALB Security Group

```bash
#!/bin/bash
# scripts/04-create-alb-security-group.sh

source .env
source infrastructure.env

ALB_SG_ID=$(aws ec2 create-security-group \
    --group-name ${PROJECT_NAME}-alb-sg \
    --description "Security group for ALB" \
    --vpc-id $VPC_ID \
    --tag-specifications "ResourceType=security-group,Tags=[
        {Key=Name,Value=${PROJECT_NAME}-alb-sg},
        {Key=Project,Value=${PROJECT_NAME}}
    ]" \
    --query 'GroupId' \
    --output text)

# Allow HTTPS from internet
aws ec2 authorize-security-group-ingress \
    --group-id $ALB_SG_ID \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0

# Allow HTTP (for redirect to HTTPS)
aws ec2 authorize-security-group-ingress \
    --group-id $ALB_SG_ID \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

echo "ALB_SG_ID=$ALB_SG_ID" >> infrastructure.env
```

### 2.2 Create EC2 Security Group

```bash
#!/bin/bash
# scripts/05-create-ec2-security-group.sh

source .env
source infrastructure.env

EC2_SG_ID=$(aws ec2 create-security-group \
    --group-name ${PROJECT_NAME}-ec2-sg \
    --description "Security group for EC2 code-server instance" \
    --vpc-id $VPC_ID \
    --tag-specifications "ResourceType=security-group,Tags=[
        {Key=Name,Value=${PROJECT_NAME}-ec2-sg},
        {Key=Project,Value=${PROJECT_NAME}}
    ]" \
    --query 'GroupId' \
    --output text)

# Allow ports 8443-8450 from ALB
aws ec2 authorize-security-group-ingress \
    --group-id $EC2_SG_ID \
    --protocol tcp \
    --port 8443-8450 \
    --source-group $ALB_SG_ID

# Allow SSH from admin IP
aws ec2 authorize-security-group-ingress \
    --group-id $EC2_SG_ID \
    --protocol tcp \
    --port 22 \
    --cidr $ADMIN_SSH_IP

echo "EC2_SG_ID=$EC2_SG_ID" >> infrastructure.env
```

**Validation:**
```bash
aws ec2 describe-security-groups --group-ids $ALB_SG_ID $EC2_SG_ID
```

---

## Phase 3: IAM Roles & Secrets Manager

**Duration:** 15 minutes
**Dependencies:** None

### 3.1 Create IAM Role for EC2

```bash
#!/bin/bash
# scripts/06-create-iam-role.sh

source .env

# Create trust policy
cat > /tmp/trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
    --role-name ${PROJECT_NAME}-ec2-role \
    --assume-role-policy-document file:///tmp/trust-policy.json

# Create policy
cat > /tmp/ec2-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:${PROJECT_NAME}/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:${AWS_REGION}:${AWS_ACCOUNT_ID}:log-group:/aws/ec2/${PROJECT_NAME}/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# Attach policy
aws iam put-role-policy \
    --role-name ${PROJECT_NAME}-ec2-role \
    --policy-name ${PROJECT_NAME}-ec2-policy \
    --policy-document file:///tmp/ec2-policy.json

# Create instance profile
aws iam create-instance-profile \
    --instance-profile-name ${PROJECT_NAME}-ec2-profile

aws iam add-role-to-instance-profile \
    --instance-profile-name ${PROJECT_NAME}-ec2-profile \
    --role-name ${PROJECT_NAME}-ec2-role

# Wait for instance profile to be ready
sleep 10

echo "IAM_ROLE=${PROJECT_NAME}-ec2-role" >> infrastructure.env
echo "INSTANCE_PROFILE=${PROJECT_NAME}-ec2-profile" >> infrastructure.env
```

### 3.2 Store Secrets in Secrets Manager

```bash
#!/bin/bash
# scripts/07-create-secrets.sh

source .env

# Generate random passwords
for i in {1..8}; do
    PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-20)

    aws secretsmanager create-secret \
        --name ${PROJECT_NAME}/dev${i}/password \
        --secret-string "$PASSWORD" \
        --region $AWS_REGION \
        --tags Key=Project,Value=${PROJECT_NAME}

    echo "Created password for dev${i}"
done

# Store Claude API keys (example - replace with actual keys)
echo "Please enter Claude API keys (or press Enter to use shared key):"
for i in {1..8}; do
    read -p "Claude API Key for dev${i} (or leave empty): " CLAUDE_KEY

    if [ -z "$CLAUDE_KEY" ]; then
        echo "Skipping dev${i}"
    else
        aws secretsmanager create-secret \
            --name ${PROJECT_NAME}/dev${i}/claude-api-key \
            --secret-string "$CLAUDE_KEY" \
            --region $AWS_REGION \
            --tags Key=Project,Value=${PROJECT_NAME}
    fi
done
```

**Validation:**
```bash
aws secretsmanager list-secrets --filters Key=name,Values=${PROJECT_NAME}
```

---

## Phase 4: EC2 Instance & EBS Volume

**Duration:** 10-15 minutes
**Dependencies:** Phase 1, 2, 3

### 4.1 Create SSH Key Pair

```bash
#!/bin/bash
# scripts/08-create-key-pair.sh

source .env

aws ec2 create-key-pair \
    --key-name $EC2_KEY_NAME \
    --query 'KeyMaterial' \
    --output text > ~/.ssh/${EC2_KEY_NAME}.pem

chmod 400 ~/.ssh/${EC2_KEY_NAME}.pem

echo "SSH key created: ~/.ssh/${EC2_KEY_NAME}.pem"
```

### 4.2 Create EBS Volume

```bash
#!/bin/bash
# scripts/09-create-ebs-volume.sh

source .env
source infrastructure.env

EBS_VOLUME_ID=$(aws ec2 create-volume \
    --availability-zone $AVAILABILITY_ZONE \
    --size $EBS_DATA_VOLUME_SIZE \
    --volume-type gp3 \
    --tag-specifications "ResourceType=volume,Tags=[
        {Key=Name,Value=${PROJECT_NAME}-data-volume},
        {Key=Project,Value=${PROJECT_NAME}}
    ]" \
    --query 'VolumeId' \
    --output text)

echo "EBS_VOLUME_ID=$EBS_VOLUME_ID" >> infrastructure.env

# Wait for volume to be available
aws ec2 wait volume-available --volume-ids $EBS_VOLUME_ID
```

### 4.3 Launch EC2 Instance

```bash
#!/bin/bash
# scripts/10-launch-ec2.sh

source .env
source infrastructure.env

# Get Ubuntu 22.04 AMI ID for ap-southeast-7
AMI_ID=$(aws ec2 describe-images \
    --owners 099720109477 \
    --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --output text)

echo "Using AMI: $AMI_ID"

# Create user data script
cat > /tmp/user-data.sh <<'EOF'
#!/bin/bash
set -e

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
apt-get install -y unzip
unzip awscliv2.zip
./aws/install

# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
dpkg -i -E ./amazon-cloudwatch-agent.deb

# Create mount point for EBS
mkdir -p /mnt/ebs-data

echo "Instance initialization complete"
EOF

# Launch instance
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $EC2_INSTANCE_TYPE \
    --key-name $EC2_KEY_NAME \
    --security-group-ids $EC2_SG_ID \
    --subnet-id $SUBNET_A_ID \
    --iam-instance-profile Name=$INSTANCE_PROFILE \
    --user-data file:///tmp/user-data.sh \
    --block-device-mappings "[
        {
            \"DeviceName\": \"/dev/sda1\",
            \"Ebs\": {
                \"VolumeSize\": ${EBS_ROOT_VOLUME_SIZE},
                \"VolumeType\": \"gp3\",
                \"DeleteOnTermination\": true
            }
        }
    ]" \
    --tag-specifications "ResourceType=instance,Tags=[
        {Key=Name,Value=${PROJECT_NAME}-ec2},
        {Key=Project,Value=${PROJECT_NAME}},
        {Key=Environment,Value=${ENVIRONMENT}}
    ]" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "INSTANCE_ID=$INSTANCE_ID" >> infrastructure.env
echo "Waiting for instance to be running..."

# Wait for instance
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "PUBLIC_IP=$PUBLIC_IP" >> infrastructure.env
echo "Instance is running at: $PUBLIC_IP"
```

### 4.4 Attach EBS Volume

```bash
#!/bin/bash
# scripts/11-attach-ebs.sh

source infrastructure.env

# Attach volume
aws ec2 attach-volume \
    --volume-id $EBS_VOLUME_ID \
    --instance-id $INSTANCE_ID \
    --device /dev/sdf

# Wait for attachment
aws ec2 wait volume-in-use --volume-ids $EBS_VOLUME_ID

echo "EBS volume attached"
```

**Validation:**
```bash
aws ec2 describe-instances --instance-ids $INSTANCE_ID
aws ec2 describe-volumes --volume-ids $EBS_VOLUME_ID
ssh -i ~/.ssh/${EC2_KEY_NAME}.pem ubuntu@$PUBLIC_IP "docker --version"
```

---

## Phase 5: Configure EC2 Instance

**Duration:** 20-30 minutes
**Dependencies:** Phase 4

### 5.1 Format and Mount EBS Volume

```bash
#!/bin/bash
# scripts/12-setup-storage.sh

source .env
source infrastructure.env

ssh -i ~/.ssh/${EC2_KEY_NAME}.pem ubuntu@$PUBLIC_IP << 'ENDSSH'
set -e

# Wait for device to appear
while [ ! -e /dev/nvme1n1 ]; do
    echo "Waiting for EBS device..."
    sleep 5
done

# Check if filesystem exists
if ! sudo file -s /dev/nvme1n1 | grep -q ext4; then
    echo "Creating ext4 filesystem..."
    sudo mkfs.ext4 /dev/nvme1n1
fi

# Mount volume
sudo mount /dev/nvme1n1 /mnt/ebs-data

# Add to fstab for auto-mount on reboot
UUID=$(sudo blkid -s UUID -o value /dev/nvme1n1)
echo "UUID=$UUID /mnt/ebs-data ext4 defaults,nofail 0 2" | sudo tee -a /etc/fstab

# Create directory structure
sudo mkdir -p /mnt/ebs-data/{dev1,dev2,dev3,dev4,dev5,dev6,dev7,dev8}

# Set permissions
sudo chown -R ubuntu:ubuntu /mnt/ebs-data

echo "Storage setup complete"
ENDSSH
```

### 5.2 Create Docker Compose File

สร้างไฟล์ `docker-compose.yml` locally:

```yaml
# docker/docker-compose.yml
version: '3.8'

services:
  code-server-dev1:
    image: codercom/code-server:latest
    container_name: code-server-dev1
    restart: unless-stopped
    ports:
      - "8443:8080"
    environment:
      - PASSWORD=${DEV1_PASSWORD}
      - CLAUDE_API_KEY=${DEV1_CLAUDE_KEY}
    volumes:
      - /mnt/ebs-data/dev1/workspace:/home/coder/workspace
      - /mnt/ebs-data/dev1/config:/home/coder/.local/share/code-server
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 3G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3

  code-server-dev2:
    image: codercom/code-server:latest
    container_name: code-server-dev2
    restart: unless-stopped
    ports:
      - "8444:8080"
    environment:
      - PASSWORD=${DEV2_PASSWORD}
      - CLAUDE_API_KEY=${DEV2_CLAUDE_KEY}
    volumes:
      - /mnt/ebs-data/dev2/workspace:/home/coder/workspace
      - /mnt/ebs-data/dev2/config:/home/coder/.local/share/code-server
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 3G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Repeat for dev3-dev8 with ports 8445-8450
  code-server-dev3:
    image: codercom/code-server:latest
    container_name: code-server-dev3
    restart: unless-stopped
    ports:
      - "8445:8080"
    environment:
      - PASSWORD=${DEV3_PASSWORD}
      - CLAUDE_API_KEY=${DEV3_CLAUDE_KEY}
    volumes:
      - /mnt/ebs-data/dev3/workspace:/home/coder/workspace
      - /mnt/ebs-data/dev3/config:/home/coder/.local/share/code-server
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 3G

  code-server-dev4:
    image: codercom/code-server:latest
    container_name: code-server-dev4
    restart: unless-stopped
    ports:
      - "8446:8080"
    environment:
      - PASSWORD=${DEV4_PASSWORD}
      - CLAUDE_API_KEY=${DEV4_CLAUDE_KEY}
    volumes:
      - /mnt/ebs-data/dev4/workspace:/home/coder/workspace
      - /mnt/ebs-data/dev4/config:/home/coder/.local/share/code-server
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 3G

  code-server-dev5:
    image: codercom/code-server:latest
    container_name: code-server-dev5
    restart: unless-stopped
    ports:
      - "8447:8080"
    environment:
      - PASSWORD=${DEV5_PASSWORD}
      - CLAUDE_API_KEY=${DEV5_CLAUDE_KEY}
    volumes:
      - /mnt/ebs-data/dev5/workspace:/home/coder/workspace
      - /mnt/ebs-data/dev5/config:/home/coder/.local/share/code-server
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 3G

  code-server-dev6:
    image: codercom/code-server:latest
    container_name: code-server-dev6
    restart: unless-stopped
    ports:
      - "8448:8080"
    environment:
      - PASSWORD=${DEV6_PASSWORD}
      - CLAUDE_API_KEY=${DEV6_CLAUDE_KEY}
    volumes:
      - /mnt/ebs-data/dev6/workspace:/home/coder/workspace
      - /mnt/ebs-data/dev6/config:/home/coder/.local/share/code-server
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 3G

  code-server-dev7:
    image: codercom/code-server:latest
    container_name: code-server-dev7
    restart: unless-stopped
    ports:
      - "8449:8080"
    environment:
      - PASSWORD=${DEV7_PASSWORD}
      - CLAUDE_API_KEY=${DEV7_CLAUDE_KEY}
    volumes:
      - /mnt/ebs-data/dev7/workspace:/home/coder/workspace
      - /mnt/ebs-data/dev7/config:/home/coder/.local/share/code-server
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 3G

  code-server-dev8:
    image: codercom/code-server:latest
    container_name: code-server-dev8
    restart: unless-stopped
    ports:
      - "8450:8080"
    environment:
      - PASSWORD=${DEV8_PASSWORD}
      - CLAUDE_API_KEY=${DEV8_CLAUDE_KEY}
    volumes:
      - /mnt/ebs-data/dev8/workspace:/home/coder/workspace
      - /mnt/ebs-data/dev8/config:/home/coder/.local/share/code-server
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 3G
```

### 5.3 Deploy to EC2 and Start Containers

```bash
#!/bin/bash
# scripts/13-deploy-containers.sh

source .env
source infrastructure.env

# Copy docker-compose.yml to EC2
scp -i ~/.ssh/${EC2_KEY_NAME}.pem docker/docker-compose.yml ubuntu@$PUBLIC_IP:/home/ubuntu/

# Create .env file with secrets on EC2
ssh -i ~/.ssh/${EC2_KEY_NAME}.pem ubuntu@$PUBLIC_IP << ENDSSH
# Fetch secrets from Secrets Manager and create .env
for i in {1..8}; do
    PASSWORD=\$(aws secretsmanager get-secret-value \
        --secret-id ${PROJECT_NAME}/dev\${i}/password \
        --region $AWS_REGION \
        --query SecretString \
        --output text)

    # Try to get Claude API key (may not exist)
    CLAUDE_KEY=\$(aws secretsmanager get-secret-value \
        --secret-id ${PROJECT_NAME}/dev\${i}/claude-api-key \
        --region $AWS_REGION \
        --query SecretString \
        --output text 2>/dev/null || echo "")

    echo "DEV\${i}_PASSWORD=\$PASSWORD" >> .env
    echo "DEV\${i}_CLAUDE_KEY=\$CLAUDE_KEY" >> .env
done

# Pull images
docker-compose pull

# Start containers
docker-compose up -d

# Check status
docker-compose ps

echo "Containers deployed successfully"
ENDSSH
```

**Validation:**
```bash
ssh -i ~/.ssh/${EC2_KEY_NAME}.pem ubuntu@$PUBLIC_IP "docker ps"
curl -k http://$PUBLIC_IP:8443/healthz
```

---

## Phase 6: ACM Certificate & ALB Setup

**Duration:** 30-40 minutes (includes DNS validation wait time)
**Dependencies:** Phase 1, 2, Domain ownership

### 6.1 Request ACM Certificate

```bash
#!/bin/bash
# scripts/14-request-certificate.sh

source .env
source infrastructure.env

# Request wildcard certificate
CERT_ARN=$(aws acm request-certificate \
    --domain-name "*.${BASE_DOMAIN}" \
    --validation-method DNS \
    --subject-alternative-names "${BASE_DOMAIN}" \
    --region $AWS_REGION \
    --tags Key=Project,Value=${PROJECT_NAME} \
    --query 'CertificateArn' \
    --output text)

echo "CERT_ARN=$CERT_ARN" >> infrastructure.env
echo "Certificate requested: $CERT_ARN"

# Get DNS validation records
echo "Add these DNS records to Route53:"
aws acm describe-certificate \
    --certificate-arn $CERT_ARN \
    --region $AWS_REGION \
    --query 'Certificate.DomainValidationOptions[*].[ResourceRecord.Name,ResourceRecord.Value]' \
    --output table
```

### 6.2 Create DNS Validation Records (Auto)

```bash
#!/bin/bash
# scripts/15-validate-certificate.sh

source .env
source infrastructure.env

# Get validation records
VALIDATION_RECORD=$(aws acm describe-certificate \
    --certificate-arn $CERT_ARN \
    --region $AWS_REGION \
    --query 'Certificate.DomainValidationOptions[0].ResourceRecord' \
    --output json)

RECORD_NAME=$(echo $VALIDATION_RECORD | jq -r '.Name')
RECORD_VALUE=$(echo $VALIDATION_RECORD | jq -r '.Value')

# Create validation record in Route53
aws route53 change-resource-record-sets \
    --hosted-zone-id $ROUTE53_HOSTED_ZONE_ID \
    --change-batch "{
        \"Changes\": [{
            \"Action\": \"CREATE\",
            \"ResourceRecordSet\": {
                \"Name\": \"$RECORD_NAME\",
                \"Type\": \"CNAME\",
                \"TTL\": 300,
                \"ResourceRecords\": [{\"Value\": \"$RECORD_VALUE\"}]
            }
        }]
    }"

echo "Waiting for certificate validation..."
aws acm wait certificate-validated \
    --certificate-arn $CERT_ARN \
    --region $AWS_REGION

echo "Certificate validated!"
```

### 6.3 Create Application Load Balancer

```bash
#!/bin/bash
# scripts/16-create-alb.sh

source .env
source infrastructure.env

# Create ALB
ALB_ARN=$(aws elbv2 create-load-balancer \
    --name ${PROJECT_NAME}-alb \
    --subnets $SUBNET_A_ID $SUBNET_B_ID \
    --security-groups $ALB_SG_ID \
    --scheme internet-facing \
    --type application \
    --ip-address-type ipv4 \
    --tags Key=Project,Value=${PROJECT_NAME} \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text)

echo "ALB_ARN=$ALB_ARN" >> infrastructure.env

# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --load-balancer-arns $ALB_ARN \
    --query 'LoadBalancers[0].DNSName' \
    --output text)

echo "ALB_DNS=$ALB_DNS" >> infrastructure.env
echo "ALB DNS: $ALB_DNS"
```

### 6.4 Create Target Groups (8 groups)

```bash
#!/bin/bash
# scripts/17-create-target-groups.sh

source .env
source infrastructure.env

for i in {1..8}; do
    PORT=$((8442 + i))

    TG_ARN=$(aws elbv2 create-target-group \
        --name ${PROJECT_NAME}-dev${i}-tg \
        --protocol HTTP \
        --port $PORT \
        --vpc-id $VPC_ID \
        --health-check-enabled \
        --health-check-protocol HTTP \
        --health-check-path /healthz \
        --health-check-interval-seconds 30 \
        --health-check-timeout-seconds 5 \
        --healthy-threshold-count 2 \
        --unhealthy-threshold-count 3 \
        --target-type instance \
        --query 'TargetGroups[0].TargetGroupArn' \
        --output text)

    echo "TG_DEV${i}_ARN=$TG_ARN" >> infrastructure.env

    # Register EC2 instance
    aws elbv2 register-targets \
        --target-group-arn $TG_ARN \
        --targets Id=$INSTANCE_ID,Port=$PORT

    echo "Created target group for dev${i} on port $PORT"
done
```

### 6.5 Create ALB Listeners and Rules

```bash
#!/bin/bash
# scripts/18-create-alb-listeners.sh

source .env
source infrastructure.env

# Create HTTPS listener
LISTENER_ARN=$(aws elbv2 create-listener \
    --load-balancer-arn $ALB_ARN \
    --protocol HTTPS \
    --port 443 \
    --certificates CertificateArn=$CERT_ARN \
    --default-actions Type=fixed-response,FixedResponseConfig="{StatusCode=404,ContentType=text/plain,MessageBody='Not Found'}" \
    --query 'Listeners[0].ListenerArn' \
    --output text)

echo "LISTENER_ARN=$LISTENER_ARN" >> infrastructure.env

# Create rules for each developer subdomain
source infrastructure.env

for i in {1..8}; do
    TG_ARN_VAR="TG_DEV${i}_ARN"
    TG_ARN=${!TG_ARN_VAR}

    aws elbv2 create-rule \
        --listener-arn $LISTENER_ARN \
        --priority $i \
        --conditions Field=host-header,Values=dev${i}.${BASE_DOMAIN} \
        --actions Type=forward,TargetGroupArn=$TG_ARN

    echo "Created rule for dev${i}.${BASE_DOMAIN}"
done

# Create HTTP listener (redirect to HTTPS)
aws elbv2 create-listener \
    --load-balancer-arn $ALB_ARN \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=redirect,RedirectConfig="{Protocol=HTTPS,Port=443,StatusCode=HTTP_301}"
```

**Validation:**
```bash
aws elbv2 describe-load-balancers --load-balancer-arns $ALB_ARN
aws elbv2 describe-target-health --target-group-arn $TG_DEV1_ARN
```

---

## Phase 7: Route53 DNS Configuration

**Duration:** 5-10 minutes
**Dependencies:** Phase 6 (ALB)

### 7.1 Create DNS Records

```bash
#!/bin/bash
# scripts/19-create-dns-records.sh

source .env
source infrastructure.env

# Create A records for each developer subdomain
for i in {1..8}; do
    aws route53 change-resource-record-sets \
        --hosted-zone-id $ROUTE53_HOSTED_ZONE_ID \
        --change-batch "{
            \"Changes\": [{
                \"Action\": \"CREATE\",
                \"ResourceRecordSet\": {
                    \"Name\": \"dev${i}.${BASE_DOMAIN}\",
                    \"Type\": \"A\",
                    \"AliasTarget\": {
                        \"HostedZoneId\": \"$(aws elbv2 describe-load-balancers --load-balancer-arns $ALB_ARN --query 'LoadBalancers[0].CanonicalHostedZoneId' --output text)\",
                        \"DNSName\": \"$ALB_DNS\",
                        \"EvaluateTargetHealth\": true
                    }
                }
            }]
        }"

    echo "Created DNS record for dev${i}.${BASE_DOMAIN}"
done
```

**Validation:**
```bash
for i in {1..8}; do
    dig dev${i}.${BASE_DOMAIN} +short
done
```

---

## Phase 8: Monitoring & Logging

**Duration:** 20 minutes
**Dependencies:** Phase 4, 5

### 8.1 Configure CloudWatch Logs

```bash
#!/bin/bash
# scripts/20-setup-cloudwatch-logs.sh

source .env

# Create log groups
LOG_GROUPS=(
    "/aws/ec2/${PROJECT_NAME}/system"
    "/aws/ec2/${PROJECT_NAME}/docker"
)

for i in {1..8}; do
    LOG_GROUPS+=("/aws/ec2/${PROJECT_NAME}/containers/dev${i}")
done

for LOG_GROUP in "${LOG_GROUPS[@]}"; do
    aws logs create-log-group --log-group-name "$LOG_GROUP" --region $AWS_REGION
    aws logs put-retention-policy --log-group-name "$LOG_GROUP" --retention-in-days 30 --region $AWS_REGION
    echo "Created log group: $LOG_GROUP"
done
```

### 8.2 Configure CloudWatch Alarms

```bash
#!/bin/bash
# scripts/21-create-alarms.sh

source .env
source infrastructure.env

# CPU Utilization Alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "${PROJECT_NAME}-high-cpu" \
    --alarm-description "Alert when CPU exceeds 80%" \
    --metric-name CPUUtilization \
    --namespace AWS/EC2 \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --dimensions Name=InstanceId,Value=$INSTANCE_ID

# Disk Usage Alarm (requires CloudWatch agent)
# Memory Alarm (requires CloudWatch agent)
# ALB 5xx errors alarm

echo "CloudWatch alarms created"
```

### 8.3 Setup AWS Backup

```bash
#!/bin/bash
# scripts/22-setup-backup.sh

source .env
source infrastructure.env

# Create backup vault
aws backup create-backup-vault \
    --backup-vault-name ${PROJECT_NAME}-vault \
    --region $AWS_REGION

# Create backup plan (daily at 2 AM UTC)
cat > /tmp/backup-plan.json <<EOF
{
  "BackupPlanName": "${PROJECT_NAME}-daily-backup",
  "Rules": [{
    "RuleName": "DailyBackup",
    "TargetBackupVaultName": "${PROJECT_NAME}-vault",
    "ScheduleExpression": "cron(0 2 * * ? *)",
    "StartWindowMinutes": 60,
    "CompletionWindowMinutes": 120,
    "Lifecycle": {
      "DeleteAfterDays": 30
    }
  }]
}
EOF

BACKUP_PLAN_ID=$(aws backup create-backup-plan \
    --backup-plan file:///tmp/backup-plan.json \
    --region $AWS_REGION \
    --query 'BackupPlanId' \
    --output text)

# Assign resources (EBS volume)
aws backup create-backup-selection \
    --backup-plan-id $BACKUP_PLAN_ID \
    --backup-selection "{
        \"SelectionName\": \"${PROJECT_NAME}-ebs-backup\",
        \"IamRoleArn\": \"arn:aws:iam::${AWS_ACCOUNT_ID}:role/service-role/AWSBackupDefaultServiceRole\",
        \"Resources\": [
            \"arn:aws:ec2:${AWS_REGION}:${AWS_ACCOUNT_ID}:volume/${EBS_VOLUME_ID}\"
        ]
    }" \
    --region $AWS_REGION

echo "Backup configured"
```

---

## Phase 9: Testing & Validation

**Duration:** 30 minutes
**Dependencies:** All previous phases

### 9.1 Comprehensive Testing Script

```bash
#!/bin/bash
# scripts/23-test-deployment.sh

source .env
source infrastructure.env

echo "=== Deployment Testing ==="

# Test 1: EC2 Instance
echo "Test 1: EC2 Instance Status"
aws ec2 describe-instance-status --instance-ids $INSTANCE_ID --query 'InstanceStatuses[0].InstanceStatus.Status' --output text

# Test 2: Docker Containers
echo "Test 2: Docker Containers"
ssh -i ~/.ssh/${EC2_KEY_NAME}.pem ubuntu@$PUBLIC_IP "docker ps --format 'table {{.Names}}\t{{.Status}}'"

# Test 3: Health Checks
echo "Test 3: Container Health Checks"
for i in {1..8}; do
    PORT=$((8442 + i))
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$PUBLIC_IP:$PORT/healthz)
    echo "dev${i} (port $PORT): $STATUS"
done

# Test 4: ALB Target Health
echo "Test 4: ALB Target Health"
for i in {1..8}; do
    TG_ARN_VAR="TG_DEV${i}_ARN"
    TG_ARN=${!TG_ARN_VAR}
    aws elbv2 describe-target-health --target-group-arn $TG_ARN --query 'TargetHealthDescriptions[0].TargetHealth.State' --output text
done

# Test 5: DNS Resolution
echo "Test 5: DNS Resolution"
for i in {1..8}; do
    dig dev${i}.${BASE_DOMAIN} +short | head -1
done

# Test 6: HTTPS Endpoints
echo "Test 6: HTTPS Endpoints (will take a few minutes for DNS propagation)"
sleep 30
for i in {1..8}; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://dev${i}.${BASE_DOMAIN} --max-time 10 || echo "TIMEOUT")
    echo "https://dev${i}.${BASE_DOMAIN}: $STATUS"
done

echo "=== Testing Complete ==="
```

### 9.2 Manual Testing Checklist

```markdown
## Manual Testing Checklist

### Infrastructure Tests
- [ ] EC2 instance is running and accessible via SSH
- [ ] EBS volume is mounted at /mnt/ebs-data
- [ ] All 8 directories exist in /mnt/ebs-data
- [ ] Docker and Docker Compose are installed
- [ ] All 8 containers are running

### Network Tests
- [ ] ALB is in "active" state
- [ ] All 8 target groups show "healthy" targets
- [ ] Security groups allow correct traffic
- [ ] DNS records resolve to ALB

### Application Tests
- [ ] Can access each developer subdomain via HTTPS
- [ ] Code-server login page appears
- [ ] Can login with password from Secrets Manager
- [ ] Claude extension is visible (may need manual install)
- [ ] Can create and save files in workspace
- [ ] Files persist after container restart

### Security Tests
- [ ] HTTPS enforced (HTTP redirects to HTTPS)
- [ ] SSL certificate is valid (no browser warnings)
- [ ] Cannot access other developer workspaces
- [ ] SSH only accessible from admin IP
- [ ] Secrets Manager API calls work from EC2

### Monitoring Tests
- [ ] CloudWatch log groups created
- [ ] Logs appearing in CloudWatch
- [ ] CloudWatch alarms configured
- [ ] Backup plan active

### Performance Tests
- [ ] Code-server loads in < 5 seconds
- [ ] Editor typing latency < 100ms
- [ ] Claude API responses working
- [ ] No CPU/memory alerts triggered
```

---

## Phase 10: Documentation & Handoff

### 10.1 Create Operations Guide

Create `OPERATIONS.md` with:
- How to add/remove developers
- How to restart containers
- How to update code-server
- How to check logs
- How to restore from backup
- Troubleshooting guide

### 10.2 Credential Handoff

```bash
# Generate credentials document for each developer
for i in {1..8}; do
    PASSWORD=$(aws secretsmanager get-secret-value \
        --secret-id ${PROJECT_NAME}/dev${i}/password \
        --region $AWS_REGION \
        --query SecretString \
        --output text)

    cat > developer-credentials/dev${i}.txt <<EOF
Developer ${i} Access Credentials
================================

URL: https://dev${i}.${BASE_DOMAIN}
Password: $PASSWORD

First Login Instructions:
1. Open URL in browser
2. Enter password above
3. Install Claude extension (if needed)
4. Configure Claude API key in settings

Support: contact-admin@example.com
EOF
done
```

---

## Complete Deployment Script

### Master Deployment Script

```bash
#!/bin/bash
# deploy-all.sh - Master deployment script

set -e

echo "========================================="
echo "AWS Code-Server Multi-Developer Setup"
echo "========================================="

# Source configuration
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    exit 1
fi

source .env

# Phase 0: Validate
echo "Phase 0: Validating prerequisites..."
bash scripts/00-validate-prerequisites.sh

# Phase 1: Network Infrastructure
echo "Phase 1: Creating network infrastructure..."
bash scripts/01-create-vpc.sh
bash scripts/02-create-subnets.sh
bash scripts/03-create-igw.sh

# Phase 2: Security Groups
echo "Phase 2: Creating security groups..."
bash scripts/04-create-alb-security-group.sh
bash scripts/05-create-ec2-security-group.sh

# Phase 3: IAM & Secrets
echo "Phase 3: Setting up IAM and secrets..."
bash scripts/06-create-iam-role.sh
bash scripts/07-create-secrets.sh

# Phase 4: EC2 & EBS
echo "Phase 4: Launching EC2 instance..."
bash scripts/08-create-key-pair.sh
bash scripts/09-create-ebs-volume.sh
bash scripts/10-launch-ec2.sh
bash scripts/11-attach-ebs.sh

# Wait for EC2 to be ready
echo "Waiting for EC2 instance to be fully ready..."
sleep 60

# Phase 5: Configure EC2
echo "Phase 5: Configuring EC2 instance..."
bash scripts/12-setup-storage.sh
bash scripts/13-deploy-containers.sh

# Phase 6: ALB Setup
echo "Phase 6: Setting up ALB..."
bash scripts/14-request-certificate.sh
bash scripts/15-validate-certificate.sh
bash scripts/16-create-alb.sh
bash scripts/17-create-target-groups.sh
bash scripts/18-create-alb-listeners.sh

# Phase 7: DNS
echo "Phase 7: Configuring DNS..."
bash scripts/19-create-dns-records.sh

# Phase 8: Monitoring
echo "Phase 8: Setting up monitoring..."
bash scripts/20-setup-cloudwatch-logs.sh
bash scripts/21-create-alarms.sh
bash scripts/22-setup-backup.sh

# Phase 9: Testing
echo "Phase 9: Running tests..."
bash scripts/23-test-deployment.sh

echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Next Steps:"
echo "1. Review test results above"
echo "2. Manually verify each endpoint"
echo "3. Install Claude extensions in containers"
echo "4. Distribute credentials to developers"
echo ""
echo "Access URLs:"
for i in {1..8}; do
    echo "  Developer ${i}: https://dev${i}.${BASE_DOMAIN}"
done
echo ""
echo "Infrastructure details saved in: infrastructure.env"
```

---

## Cleanup Script

### Complete Teardown

```bash
#!/bin/bash
# cleanup-all.sh - Complete infrastructure teardown

source .env
source infrastructure.env

echo "WARNING: This will delete ALL resources!"
read -p "Are you sure? (type 'yes' to confirm): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted"
    exit 1
fi

# Delete ALB
aws elbv2 delete-load-balancer --load-balancer-arn $ALB_ARN
sleep 10

# Delete target groups
for i in {1..8}; do
    TG_ARN_VAR="TG_DEV${i}_ARN"
    aws elbv2 delete-target-group --target-group-arn ${!TG_ARN_VAR}
done

# Terminate EC2
aws ec2 terminate-instances --instance-ids $INSTANCE_ID
aws ec2 wait instance-terminated --instance-ids $INSTANCE_ID

# Delete EBS volume
aws ec2 delete-volume --volume-id $EBS_VOLUME_ID

# Delete security groups
aws ec2 delete-security-group --group-id $EC2_SG_ID
aws ec2 delete-security-group --group-id $ALB_SG_ID

# Delete VPC components
aws ec2 delete-route-table --route-table-id $RTB_ID
aws ec2 detach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID
aws ec2 delete-internet-gateway --internet-gateway-id $IGW_ID
aws ec2 delete-subnet --subnet-id $SUBNET_A_ID
aws ec2 delete-subnet --subnet-id $SUBNET_B_ID
aws ec2 delete-vpc --vpc-id $VPC_ID

# Delete secrets
for i in {1..8}; do
    aws secretsmanager delete-secret --secret-id ${PROJECT_NAME}/dev${i}/password --force-delete-without-recovery
    aws secretsmanager delete-secret --secret-id ${PROJECT_NAME}/dev${i}/claude-api-key --force-delete-without-recovery 2>/dev/null || true
done

echo "Cleanup complete!"
```

---

## Timeline Summary

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| 0. Prerequisites | 30 min | None |
| 1. Network | 15 min | Prerequisites |
| 2. Security Groups | 10 min | Network |
| 3. IAM & Secrets | 15 min | None |
| 4. EC2 & EBS | 15 min | Network, Security, IAM |
| 5. Configure EC2 | 30 min | EC2 launched |
| 6. ALB & Certificate | 40 min | Network, Security, Domain |
| 7. DNS | 10 min | ALB |
| 8. Monitoring | 20 min | EC2, ALB |
| 9. Testing | 30 min | All |
| **Total** | **3.5-4 hours** | |

---

## Success Criteria

✅ All 8 code-server instances accessible via HTTPS
✅ SSL certificates valid
✅ Each developer has isolated workspace
✅ Containers restart automatically
✅ Health checks passing
✅ Monitoring and alarms configured
✅ Backups scheduled
✅ Documentation complete

---

## Next Steps After Implementation

1. **Install Claude Extension** in each container
2. **Configure workspace templates** (optional)
3. **Setup Git integration** (optional)
4. **Enable additional monitoring** (optional)
5. **Configure cost alerts**
6. **Train developers** on system usage
7. **Document troubleshooting procedures**
8. **Plan for scaling** (if needed)

---

**Document Version:** 1.0
**Last Updated:** 2026-01-16
**Status:** Ready for Implementation
