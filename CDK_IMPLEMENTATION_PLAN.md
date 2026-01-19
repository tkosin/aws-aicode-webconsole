# AWS CDK Python Implementation Plan - Code-Server Multi-Developer Environment

## Executive Summary

แผนการ implement ระบบ Multi-developer Code-Server environment บน AWS Region Bangkok (ap-southeast-7) สำหรับนักพัฒนา 8 คน โดยใช้ **AWS CDK (Python)** เพื่อความ professional, maintainable, และ production-ready

## Why AWS CDK Python?

### ข้อดีสำหรับโปรเจกต์นี้

✅ **Type-safe Infrastructure** - IDE autocomplete, error checking
✅ **Reusable Code** - สร้าง constructs ที่ใช้ซ้ำได้
✅ **Loop for 8 Developers** - ไม่ต้องเขียนซ้ำ
✅ **State Management** - CloudFormation จัดการ state ให้
✅ **Automatic Rollback** - Deploy fail = auto rollback
✅ **Easy Testing** - Unit tests ได้
✅ **Professional** - เหมาะกับ production
✅ **Maintainable** - แก้ไขง่าย เพิ่ม/ลบ developer ง่าย

### เปรียบเทียบกับ Shell Scripts

| Feature | Shell Scripts | CDK Python |
|---------|--------------|------------|
| Lines of Code | 1,500+ | 400-500 |
| Number of Files | 23 files | 5-6 files |
| State Management | Manual | Auto |
| Rollback | Manual | Auto |
| Testing | Hard | Easy |
| Maintenance | Hard | Easy |
| Learning Curve | Low | Medium |
| Production Ready | 🟡 | 🟢 |

---

## Project Structure

```
cdk/
├── app.py                      # CDK app entry point
├── cdk.json                    # CDK configuration
├── cdk.context.json            # Context values (gitignore)
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Dev dependencies
├── README.md                   # Setup and usage guide
├── .gitignore                  # Git ignore file
│
├── config/
│   ├── __init__.py
│   ├── dev.py                  # Development config
│   ├── prod.py                 # Production config
│   └── common.py               # Shared config
│
├── stacks/
│   ├── __init__.py
│   ├── network_stack.py        # VPC, Subnets, IGW, SG
│   ├── security_stack.py       # IAM roles, Secrets Manager
│   ├── compute_stack.py        # EC2, EBS, User Data
│   ├── loadbalancer_stack.py   # ALB, Target Groups, Listeners
│   ├── dns_stack.py            # Route53 records, ACM cert
│   └── monitoring_stack.py     # CloudWatch, Alarms, Backup
│
├── constructs/                 # Custom reusable constructs
│   ├── __init__.py
│   ├── code_server_container.py
│   └── developer_workspace.py
│
├── scripts/
│   ├── deploy.sh               # Deployment script
│   ├── destroy.sh              # Cleanup script
│   ├── generate_secrets.py     # Generate passwords
│   └── test_deployment.py      # Post-deploy tests
│
└── tests/
    ├── __init__.py
    ├── unit/
    │   ├── test_network_stack.py
    │   ├── test_compute_stack.py
    │   └── test_loadbalancer_stack.py
    └── integration/
        └── test_full_deployment.py
```

---

## Phase 0: Prerequisites & Setup

### 0.1 System Requirements

**Required Software:**
- Python 3.9 or later
- Node.js 14+ (for CDK CLI)
- AWS CLI v2
- Git
- pip (Python package manager)

**AWS Requirements:**
- AWS Account with admin permissions
- AWS CLI configured with credentials
- Default region set to `ap-southeast-7`

### 0.2 Install CDK

```bash
# Install AWS CDK CLI globally
npm install -g aws-cdk

# Verify installation
cdk --version
# Should show: 2.x.x or later

# Verify AWS credentials
aws sts get-caller-identity
```

### 0.3 Bootstrap CDK (One-time per account/region)

```bash
# Bootstrap CDK in Bangkok region
cdk bootstrap aws://ACCOUNT-ID/ap-southeast-7

# This creates:
# - CDKToolkit CloudFormation stack
# - S3 bucket for CDK assets
# - ECR repository for Docker images
# - IAM roles for CloudFormation
```

### 0.4 Create Project Directory

```bash
mkdir aws-code-server-cdk
cd aws-code-server-cdk

# Initialize CDK project
cdk init app --language python

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate.bat  # Windows
```

---

## Phase 1: Project Setup

**Duration:** 30 minutes
**Dependencies:** Phase 0

### 1.1 Update requirements.txt

```txt
# requirements.txt
aws-cdk-lib==2.120.0
constructs>=10.0.0
boto3>=1.34.0
pydantic>=2.5.0
python-dotenv>=1.0.0
```

```txt
# requirements-dev.txt
pytest>=7.4.0
pytest-cov>=4.1.0
black>=23.12.0
flake8>=6.1.0
mypy>=1.7.0
```

### 1.2 Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 1.3 Create Configuration Files

**config/common.py:**
```python
"""Common configuration shared across all environments"""
from typing import Dict, List

# Project Configuration
PROJECT_NAME = "code-server-multi-dev"
ENVIRONMENT = "production"

# AWS Configuration
AWS_REGION = "ap-southeast-7"
AVAILABILITY_ZONES = ["ap-southeast-7a", "ap-southeast-7b", "ap-southeast-7c"]

# Network Configuration
VPC_CIDR = "10.0.0.0/16"
PUBLIC_SUBNET_CIDRS = ["10.0.1.0/24", "10.0.2.0/24"]

# EC2 Configuration
EC2_INSTANCE_TYPE = "t3.2xlarge"
EC2_KEY_NAME = "code-server-admin-key"
EBS_ROOT_SIZE = 50  # GB
EBS_DATA_SIZE = 500  # GB

# Developer Configuration
NUM_DEVELOPERS = 8
CONTAINER_BASE_PORT = 8443

# Domain Configuration (override in environment-specific config)
BASE_DOMAIN = "dev.example.com"
ROUTE53_HOSTED_ZONE_ID = "Z1234567890ABC"

# Tags
TAGS: Dict[str, str] = {
    "Project": PROJECT_NAME,
    "Environment": ENVIRONMENT,
    "ManagedBy": "CDK",
    "CostCenter": "Engineering",
}

# Developer Port Mapping
def get_developer_ports() -> List[int]:
    """Get list of ports for all developers"""
    return [CONTAINER_BASE_PORT + i for i in range(NUM_DEVELOPERS)]

def get_developer_subdomains() -> List[str]:
    """Get list of subdomains for all developers"""
    return [f"dev{i+1}.{BASE_DOMAIN}" for i in range(NUM_DEVELOPERS)]
```

**config/prod.py:**
```python
"""Production environment configuration"""
from .common import *

ENVIRONMENT = "production"
BASE_DOMAIN = "dev.yourdomain.com"
ROUTE53_HOSTED_ZONE_ID = "YOUR_ZONE_ID"

# Override with production-specific settings
ADMIN_SSH_CIDR = "YOUR_IP/32"  # Restrict SSH access

# Enable backups
ENABLE_BACKUP = True
BACKUP_RETENTION_DAYS = 30

# Enable enhanced monitoring
ENABLE_DETAILED_MONITORING = True
```

### 1.4 Create .gitignore

```gitignore
# CDK
*.swp
package-lock.json
__pycache__
.pytest_cache
.venv
*.egg-info
.coverage
cdk.out
cdk.context.json

# Environment
.env
.env.local
*.pem

# IDE
.vscode/
.idea/
*.code-workspace

# OS
.DS_Store
Thumbs.db

# Secrets
secrets/
*.key
*.secret
```

---

## Phase 2: Network Stack

**Duration:** 1 hour
**Dependencies:** Phase 1

### 2.1 Create Network Stack

**stacks/network_stack.py:**
```python
"""Network infrastructure stack"""
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    Tags,
)
from constructs import Construct
from typing import List


class NetworkStack(Stack):
    """
    Creates VPC, Subnets, Internet Gateway, and Security Groups
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: dict,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC
        self.vpc = ec2.Vpc(
            self,
            "CodeServerVPC",
            vpc_name=f"{config['PROJECT_NAME']}-vpc",
            ip_addresses=ec2.IpAddresses.cidr(config['VPC_CIDR']),
            max_azs=2,
            nat_gateways=0,  # No NAT gateway to save cost
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                )
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True,
        )

        # Create Security Group for ALB
        self.alb_security_group = ec2.SecurityGroup(
            self,
            "ALBSecurityGroup",
            security_group_name=f"{config['PROJECT_NAME']}-alb-sg",
            vpc=self.vpc,
            description="Security group for Application Load Balancer",
            allow_all_outbound=True,
        )

        # Allow HTTPS from internet
        self.alb_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description="Allow HTTPS from internet",
        )

        # Allow HTTP (for redirect to HTTPS)
        self.alb_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="Allow HTTP for redirect to HTTPS",
        )

        # Create Security Group for EC2
        self.ec2_security_group = ec2.SecurityGroup(
            self,
            "EC2SecurityGroup",
            security_group_name=f"{config['PROJECT_NAME']}-ec2-sg",
            vpc=self.vpc,
            description="Security group for EC2 code-server instance",
            allow_all_outbound=True,
        )

        # Allow ports 8443-8450 from ALB
        for port in range(
            config['CONTAINER_BASE_PORT'],
            config['CONTAINER_BASE_PORT'] + config['NUM_DEVELOPERS']
        ):
            self.ec2_security_group.add_ingress_rule(
                peer=ec2.Peer.security_group_id(
                    self.alb_security_group.security_group_id
                ),
                connection=ec2.Port.tcp(port),
                description=f"Allow port {port} from ALB",
            )

        # Allow SSH from admin IP
        if 'ADMIN_SSH_CIDR' in config:
            self.ec2_security_group.add_ingress_rule(
                peer=ec2.Peer.ipv4(config['ADMIN_SSH_CIDR']),
                connection=ec2.Port.tcp(22),
                description="Allow SSH from admin",
            )

        # Apply tags
        for key, value in config['TAGS'].items():
            Tags.of(self.vpc).add(key, value)
            Tags.of(self.alb_security_group).add(key, value)
            Tags.of(self.ec2_security_group).add(key, value)

        # Output values for other stacks
        self.public_subnets = self.vpc.public_subnets
```

---

## Phase 3: Security Stack

**Duration:** 45 minutes
**Dependencies:** Phase 2

### 3.1 Create Security Stack

**stacks/security_stack.py:**
```python
"""Security infrastructure - IAM roles and Secrets Manager"""
from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    Tags,
    RemovalPolicy,
)
from constructs import Construct
import secrets
import string


class SecurityStack(Stack):
    """
    Creates IAM roles and Secrets Manager secrets
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: dict,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create IAM role for EC2
        self.ec2_role = iam.Role(
            self,
            "EC2Role",
            role_name=f"{config['PROJECT_NAME']}-ec2-role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            description="IAM role for code-server EC2 instance",
        )

        # Add policies to EC2 role
        self.ec2_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["secretsmanager:GetSecretValue"],
                resources=[
                    f"arn:aws:secretsmanager:{config['AWS_REGION']}:{self.account}:secret:{config['PROJECT_NAME']}/*"
                ],
            )
        )

        self.ec2_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=[
                    f"arn:aws:logs:{config['AWS_REGION']}:{self.account}:log-group:/aws/ec2/{config['PROJECT_NAME']}/*"
                ],
            )
        )

        self.ec2_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
            )
        )

        # Create Secrets Manager secrets for each developer
        self.secrets = {}

        for i in range(1, config['NUM_DEVELOPERS'] + 1):
            # Generate random password
            password = self._generate_password()

            # Create secret for password
            secret = secretsmanager.Secret(
                self,
                f"Dev{i}Password",
                secret_name=f"{config['PROJECT_NAME']}/dev{i}/password",
                description=f"Code-server password for developer {i}",
                secret_string_value=password,
                removal_policy=RemovalPolicy.DESTROY,  # CAUTION: Deletes secret on stack deletion
            )

            self.secrets[f"dev{i}_password"] = secret

            # Create placeholder for Claude API key (manual entry)
            claude_secret = secretsmanager.Secret(
                self,
                f"Dev{i}ClaudeKey",
                secret_name=f"{config['PROJECT_NAME']}/dev{i}/claude-api-key",
                description=f"Claude API key for developer {i}",
                secret_string_value="REPLACE_WITH_ACTUAL_KEY",
                removal_policy=RemovalPolicy.DESTROY,
            )

            self.secrets[f"dev{i}_claude_key"] = claude_secret

            # Apply tags
            Tags.of(secret).add("Developer", f"dev{i}")
            Tags.of(claude_secret).add("Developer", f"dev{i}")

    def _generate_password(self, length: int = 20) -> str:
        """Generate a secure random password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
```

---

## Phase 4: Compute Stack

**Duration:** 1.5 hours
**Dependencies:** Phase 2, 3

### 4.1 Create User Data Script

**scripts/user_data.sh:**
```bash
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
COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
apt-get install -y unzip
unzip awscliv2.zip
./aws/install

# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
dpkg -i -E ./amazon-cloudwatch-agent.deb

# Create mount point
mkdir -p /mnt/ebs-data

# Create directory structure for developers
for i in {1..8}; do
    mkdir -p /mnt/ebs-data/dev${i}/{workspace,config}
    chown -R ubuntu:ubuntu /mnt/ebs-data/dev${i}
done

echo "User data script completed"
```

### 4.2 Create Docker Compose Template

**scripts/docker-compose.yml.template:**
```yaml
version: '3.8'

services:
{{#each developers}}
  code-server-dev{{this.id}}:
    image: codercom/code-server:latest
    container_name: code-server-dev{{this.id}}
    restart: unless-stopped
    ports:
      - "{{this.port}}:8080"
    environment:
      - PASSWORD={{this.password_placeholder}}
      - CLAUDE_API_KEY={{this.claude_key_placeholder}}
    volumes:
      - /mnt/ebs-data/dev{{this.id}}/workspace:/home/coder/workspace
      - /mnt/ebs-data/dev{{this.id}}/config:/home/coder/.local/share/code-server
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
{{/each}}
```

### 4.3 Create Compute Stack

**stacks/compute_stack.py:**
```python
"""Compute infrastructure - EC2 and EBS"""
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    Tags,
    CfnOutput,
)
from constructs import Construct
import os


class ComputeStack(Stack):
    """
    Creates EC2 instance and EBS volume
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        network_stack,
        security_stack,
        config: dict,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get latest Ubuntu 22.04 AMI
        ubuntu_ami = ec2.MachineImage.lookup(
            name="ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*",
            owners=["099720109477"],  # Canonical
        )

        # Read user data script
        with open("scripts/user_data.sh", "r") as f:
            user_data_script = f.read()

        user_data = ec2.UserData.for_linux()
        user_data.add_commands(user_data_script)

        # Create key pair (manual - must exist)
        key_pair = ec2.KeyPair.from_key_pair_name(
            self,
            "KeyPair",
            config['EC2_KEY_NAME']
        )

        # Create EC2 instance
        self.instance = ec2.Instance(
            self,
            "CodeServerInstance",
            instance_name=f"{config['PROJECT_NAME']}-ec2",
            instance_type=ec2.InstanceType(config['EC2_INSTANCE_TYPE']),
            machine_image=ubuntu_ami,
            vpc=network_stack.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC,
                availability_zones=[config['AVAILABILITY_ZONES'][0]],
            ),
            security_group=network_stack.ec2_security_group,
            role=security_stack.ec2_role,
            user_data=user_data,
            key_name=key_pair.key_pair_name,
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/sda1",
                    volume=ec2.BlockDeviceVolume.ebs(
                        volume_size=config['EBS_ROOT_SIZE'],
                        volume_type=ec2.EbsDeviceVolumeType.GP3,
                        delete_on_termination=True,
                    ),
                )
            ],
        )

        # Create EBS data volume
        self.data_volume = ec2.Volume(
            self,
            "DataVolume",
            volume_name=f"{config['PROJECT_NAME']}-data-volume",
            availability_zone=self.instance.instance_availability_zone,
            size=ec2.Size.gibibytes(config['EBS_DATA_SIZE']),
            volume_type=ec2.EbsDeviceVolumeType.GP3,
            removal_policy=RemovalPolicy.SNAPSHOT,  # Create snapshot on deletion
        )

        # Attach EBS volume
        self.data_volume.attach_to_instance(
            self.instance,
            device_name="/dev/sdf",
        )

        # Apply tags
        for key, value in config['TAGS'].items():
            Tags.of(self.instance).add(key, value)
            Tags.of(self.data_volume).add(key, value)

        # Outputs
        CfnOutput(
            self,
            "InstanceId",
            value=self.instance.instance_id,
            description="EC2 Instance ID",
        )

        CfnOutput(
            self,
            "InstancePublicIP",
            value=self.instance.instance_public_ip,
            description="EC2 Instance Public IP",
        )
```

---

## Phase 5: Load Balancer Stack

**Duration:** 1.5 hours
**Dependencies:** Phase 2, 4

### 5.1 Create Load Balancer Stack

**stacks/loadbalancer_stack.py:**
```python
"""Load balancer infrastructure - ALB, Target Groups, Listeners"""
from aws_cdk import (
    Stack,
    aws_elasticloadbalancingv2 as elbv2,
    aws_elasticloadbalancingv2_targets as targets,
    aws_certificatemanager as acm,
    Tags,
    CfnOutput,
    Duration,
)
from constructs import Construct


class LoadBalancerStack(Stack):
    """
    Creates Application Load Balancer, Target Groups, and Listeners
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        network_stack,
        compute_stack,
        config: dict,
        certificate_arn: str = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Application Load Balancer
        self.alb = elbv2.ApplicationLoadBalancer(
            self,
            "ALB",
            load_balancer_name=f"{config['PROJECT_NAME']}-alb",
            vpc=network_stack.vpc,
            internet_facing=True,
            security_group=network_stack.alb_security_group,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
        )

        # Create target groups for each developer
        self.target_groups = []

        for i in range(1, config['NUM_DEVELOPERS'] + 1):
            port = config['CONTAINER_BASE_PORT'] + i - 1

            target_group = elbv2.ApplicationTargetGroup(
                self,
                f"TargetGroupDev{i}",
                target_group_name=f"{config['PROJECT_NAME']}-dev{i}-tg",
                vpc=network_stack.vpc,
                port=port,
                protocol=elbv2.ApplicationProtocol.HTTP,
                targets=[
                    targets.InstanceTarget(
                        instance=compute_stack.instance,
                        port=port,
                    )
                ],
                health_check=elbv2.HealthCheck(
                    path="/healthz",
                    protocol=elbv2.Protocol.HTTP,
                    interval=Duration.seconds(30),
                    timeout=Duration.seconds(5),
                    healthy_threshold_count=2,
                    unhealthy_threshold_count=3,
                ),
                deregistration_delay=Duration.seconds(30),
                stickiness_cookie_duration=Duration.hours(1),
            )

            self.target_groups.append({
                'id': i,
                'port': port,
                'target_group': target_group,
                'subdomain': f"dev{i}.{config['BASE_DOMAIN']}",
            })

            Tags.of(target_group).add("Developer", f"dev{i}")

        # Create HTTPS listener (if certificate provided)
        if certificate_arn:
            certificate = acm.Certificate.from_certificate_arn(
                self,
                "Certificate",
                certificate_arn
            )

            https_listener = self.alb.add_listener(
                "HTTPSListener",
                port=443,
                protocol=elbv2.ApplicationProtocol.HTTPS,
                certificates=[certificate],
                default_action=elbv2.ListenerAction.fixed_response(
                    status_code=404,
                    content_type="text/plain",
                    message_body="Not Found",
                ),
            )

            # Add rules for each developer subdomain
            for tg_config in self.target_groups:
                https_listener.add_action(
                    f"Dev{tg_config['id']}Rule",
                    priority=tg_config['id'],
                    conditions=[
                        elbv2.ListenerCondition.host_headers(
                            [tg_config['subdomain']]
                        )
                    ],
                    action=elbv2.ListenerAction.forward(
                        target_groups=[tg_config['target_group']]
                    ),
                )

        # Create HTTP listener (redirect to HTTPS)
        http_listener = self.alb.add_listener(
            "HTTPListener",
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            default_action=elbv2.ListenerAction.redirect(
                protocol="HTTPS",
                port="443",
                permanent=True,
            ),
        )

        # Apply tags
        for key, value in config['TAGS'].items():
            Tags.of(self.alb).add(key, value)

        # Outputs
        CfnOutput(
            self,
            "ALBDNSName",
            value=self.alb.load_balancer_dns_name,
            description="ALB DNS Name",
        )

        CfnOutput(
            self,
            "ALBArn",
            value=self.alb.load_balancer_arn,
            description="ALB ARN",
        )
```

---

## Phase 6: DNS Stack

**Duration:** 30 minutes
**Dependencies:** Phase 5

### 6.1 Create DNS Stack

**stacks/dns_stack.py:**
```python
"""DNS infrastructure - Route53 records and ACM certificate"""
from aws_cdk import (
    Stack,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_certificatemanager as acm,
    Tags,
    CfnOutput,
)
from constructs import Construct


class DNSStack(Stack):
    """
    Creates Route53 records and ACM certificate
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        loadbalancer_stack,
        config: dict,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get hosted zone
        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self,
            "HostedZone",
            hosted_zone_id=config['ROUTE53_HOSTED_ZONE_ID'],
            zone_name=config['BASE_DOMAIN'],
        )

        # Request wildcard certificate
        self.certificate = acm.Certificate(
            self,
            "Certificate",
            domain_name=f"*.{config['BASE_DOMAIN']}",
            subject_alternative_names=[config['BASE_DOMAIN']],
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )

        # Create A records for each developer subdomain
        for i in range(1, config['NUM_DEVELOPERS'] + 1):
            subdomain = f"dev{i}"

            route53.ARecord(
                self,
                f"ARecordDev{i}",
                record_name=subdomain,
                zone=hosted_zone,
                target=route53.RecordTarget.from_alias(
                    targets.LoadBalancerTarget(loadbalancer_stack.alb)
                ),
            )

        # Outputs
        CfnOutput(
            self,
            "CertificateArn",
            value=self.certificate.certificate_arn,
            description="ACM Certificate ARN",
        )

        for i in range(1, config['NUM_DEVELOPERS'] + 1):
            CfnOutput(
                self,
                f"Dev{i}URL",
                value=f"https://dev{i}.{config['BASE_DOMAIN']}",
                description=f"Developer {i} URL",
            )
```

---

## Phase 7: Monitoring Stack

**Duration:** 45 minutes
**Dependencies:** Phase 4, 5

### 7.1 Create Monitoring Stack

**stacks/monitoring_stack.py:**
```python
"""Monitoring infrastructure - CloudWatch logs, alarms, and backups"""
from aws_cdk import (
    Stack,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_logs as logs,
    aws_backup as backup,
    aws_events as events,
    Tags,
    Duration,
    RemovalPolicy,
)
from constructs import Construct


class MonitoringStack(Stack):
    """
    Creates CloudWatch logs, metrics, alarms, and backup plan
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        compute_stack,
        config: dict,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create log groups
        log_groups = [
            f"/aws/ec2/{config['PROJECT_NAME']}/system",
            f"/aws/ec2/{config['PROJECT_NAME']}/docker",
        ]

        for i in range(1, config['NUM_DEVELOPERS'] + 1):
            log_groups.append(
                f"/aws/ec2/{config['PROJECT_NAME']}/containers/dev{i}"
            )

        for log_group_name in log_groups:
            logs.LogGroup(
                self,
                log_group_name.replace("/", "-"),
                log_group_name=log_group_name,
                retention=logs.RetentionDays.ONE_MONTH,
                removal_policy=RemovalPolicy.DESTROY,
            )

        # Create CloudWatch alarms
        # CPU Utilization Alarm
        cpu_alarm = cloudwatch.Alarm(
            self,
            "HighCPUAlarm",
            alarm_name=f"{config['PROJECT_NAME']}-high-cpu",
            alarm_description="Alert when CPU exceeds 80%",
            metric=cloudwatch.Metric(
                namespace="AWS/EC2",
                metric_name="CPUUtilization",
                dimensions_map={
                    "InstanceId": compute_stack.instance.instance_id
                },
                statistic="Average",
                period=Duration.minutes(5),
            ),
            threshold=80,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        )

        # Disk Usage Alarm (requires CloudWatch agent)
        # Memory Alarm (requires CloudWatch agent)

        # Create backup plan if enabled
        if config.get('ENABLE_BACKUP', True):
            backup_vault = backup.BackupVault(
                self,
                "BackupVault",
                backup_vault_name=f"{config['PROJECT_NAME']}-vault",
            )

            backup_plan = backup.BackupPlan(
                self,
                "BackupPlan",
                backup_plan_name=f"{config['PROJECT_NAME']}-daily-backup",
                backup_vault=backup_vault,
            )

            backup_plan.add_rule(
                backup.BackupPlanRule(
                    rule_name="DailyBackup",
                    schedule_expression=events.Schedule.cron(
                        hour="2",
                        minute="0",
                    ),
                    delete_after=Duration.days(
                        config.get('BACKUP_RETENTION_DAYS', 30)
                    ),
                )
            )

            # Add EBS volume to backup selection
            backup_plan.add_selection(
                "BackupSelection",
                resources=[
                    backup.BackupResource.from_arn(
                        compute_stack.data_volume.volume_arn
                    )
                ],
            )

        # Apply tags
        for key, value in config['TAGS'].items():
            Tags.of(cpu_alarm).add(key, value)
```

---

## Phase 8: Main App

**Duration:** 30 minutes
**Dependencies:** All stacks

### 8.1 Create Main App

**app.py:**
```python
#!/usr/bin/env python3
"""CDK application entry point"""
import os
from aws_cdk import App, Environment, Tags
from config import prod as config
from stacks.network_stack import NetworkStack
from stacks.security_stack import SecurityStack
from stacks.compute_stack import ComputeStack
from stacks.loadbalancer_stack import LoadBalancerStack
from stacks.dns_stack import DNSStack
from stacks.monitoring_stack import MonitoringStack


app = App()

# Define environment
env = Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=config.AWS_REGION,
)

# Convert config module to dict
config_dict = {
    key: getattr(config, key)
    for key in dir(config)
    if not key.startswith('__')
}

# Create stacks
network_stack = NetworkStack(
    app,
    f"{config.PROJECT_NAME}-network",
    config=config_dict,
    env=env,
)

security_stack = SecurityStack(
    app,
    f"{config.PROJECT_NAME}-security",
    config=config_dict,
    env=env,
)

compute_stack = ComputeStack(
    app,
    f"{config.PROJECT_NAME}-compute",
    network_stack=network_stack,
    security_stack=security_stack,
    config=config_dict,
    env=env,
)

# DNS stack first (to get certificate)
dns_stack = DNSStack(
    app,
    f"{config.PROJECT_NAME}-dns",
    loadbalancer_stack=None,  # Will be updated
    config=config_dict,
    env=env,
)

loadbalancer_stack = LoadBalancerStack(
    app,
    f"{config.PROJECT_NAME}-loadbalancer",
    network_stack=network_stack,
    compute_stack=compute_stack,
    config=config_dict,
    certificate_arn=dns_stack.certificate.certificate_arn,
    env=env,
)

monitoring_stack = MonitoringStack(
    app,
    f"{config.PROJECT_NAME}-monitoring",
    compute_stack=compute_stack,
    config=config_dict,
    env=env,
)

# Add dependencies
compute_stack.add_dependency(network_stack)
compute_stack.add_dependency(security_stack)
loadbalancer_stack.add_dependency(compute_stack)
loadbalancer_stack.add_dependency(dns_stack)
monitoring_stack.add_dependency(compute_stack)

# Apply global tags
for key, value in config.TAGS.items():
    Tags.of(app).add(key, value)

app.synth()
```

---

## Phase 9: Deployment Scripts

### 9.1 Deploy Script

**scripts/deploy.sh:**
```bash
#!/bin/bash
set -e

echo "======================================"
echo "AWS CDK Code-Server Deployment"
echo "======================================"

# Activate virtual environment
source .venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Synthesize CloudFormation templates
echo "Synthesizing CDK stacks..."
cdk synth

# Deploy all stacks
echo "Deploying all stacks..."
cdk deploy --all --require-approval never

echo "======================================"
echo "Deployment Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Wait for DNS propagation (5-10 minutes)"
echo "2. Update Claude API keys in Secrets Manager"
echo "3. SSH to EC2 and setup Docker containers"
echo "4. Test all developer URLs"
```

### 9.2 Destroy Script

**scripts/destroy.sh:**
```bash
#!/bin/bash
set -e

echo "WARNING: This will destroy all infrastructure!"
read -p "Are you sure? (type 'yes' to confirm): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted"
    exit 1
fi

source .venv/bin/activate

cdk destroy --all --force

echo "Infrastructure destroyed"
```

---

## Deployment Timeline

| Phase | Task | Duration | Total |
|-------|------|----------|-------|
| 0 | Prerequisites & Setup | 30 min | 0:30 |
| 1 | Project Setup | 30 min | 1:00 |
| 2 | Network Stack | 1 hour | 2:00 |
| 3 | Security Stack | 45 min | 2:45 |
| 4 | Compute Stack | 1.5 hours | 4:15 |
| 5 | Load Balancer Stack | 1.5 hours | 5:45 |
| 6 | DNS Stack | 30 min | 6:15 |
| 7 | Monitoring Stack | 45 min | 7:00 |
| 8 | Main App | 30 min | 7:30 |
| 9 | Deployment | 30 min | **8 hours** |

**Actual CDK Deploy Time:** 20-30 minutes
**Total Development + Deploy:** ~8-9 hours

---

## Deployment Commands

### Initial Deployment

```bash
# Clone/setup project
cd cdk/

# Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Update config
# Edit config/prod.py with your values

# Bootstrap CDK (one-time)
cdk bootstrap

# Deploy
cdk deploy --all

# Or use script
bash scripts/deploy.sh
```

### Update Deployment

```bash
# Make changes to stacks
# Deploy only changed stacks
cdk deploy <stack-name>

# Or deploy all
cdk deploy --all
```

### View Diff

```bash
cdk diff
```

### Destroy

```bash
cdk destroy --all
# Or
bash scripts/destroy.sh
```

---

## Advantages Over Shell Scripts

### Code Comparison

**Shell Scripts (23 files, 1500+ lines):**
```bash
# Create 8 target groups (repetitive)
for i in {1..8}; do
    PORT=$((8442 + i))
    TG_ARN=$(aws elbv2 create-target-group ...)
    echo "TG_DEV${i}_ARN=$TG_ARN" >> infrastructure.env
done
```

**CDK Python (1 loop, type-safe):**
```python
# Create 8 target groups (clean, reusable)
for i in range(1, config['NUM_DEVELOPERS'] + 1):
    target_group = elbv2.ApplicationTargetGroup(
        self, f"TargetGroupDev{i}",
        # ... configuration
    )
```

### Maintenance Example

**Add Developer 9:**

Shell Scripts:
- Edit 5+ files
- Update port ranges
- Add new target group script
- Update DNS script
- Update docker-compose manually

CDK Python:
- Change `NUM_DEVELOPERS = 9`
- Run `cdk deploy`
- Done!

---

## Testing

### Unit Tests

**tests/unit/test_network_stack.py:**
```python
import aws_cdk as cdk
from stacks.network_stack import NetworkStack
from config import prod as config

def test_vpc_created():
    app = cdk.App()
    stack = NetworkStack(app, "test-network", config=config.__dict__)
    template = cdk.assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::EC2::VPC", {
        "CidrBlock": "10.0.0.0/16"
    })
```

### Run Tests

```bash
pytest tests/
pytest --cov=stacks tests/
```

---

## Next Steps After CDK Deployment

1. **Wait for DNS** (5-10 minutes)
2. **Update Secrets Manager** with Claude API keys
3. **SSH to EC2** and verify Docker setup
4. **Deploy Docker Compose** containers
5. **Test all endpoints**
6. **Distribute credentials** to developers

---

## Comparison: Shell vs CDK

| Metric | Shell Scripts | CDK Python |
|--------|--------------|------------|
| **Dev Time** | 6 hours | 8 hours |
| **Deploy Time** | 3-4 hours | 20-30 min |
| **Total Lines** | 1,500+ | 400-500 |
| **Files** | 23 | 6 |
| **Maintainability** | Low | High |
| **Testability** | None | Full |
| **Type Safety** | None | Full |
| **Rollback** | Manual | Auto |
| **State Mgmt** | Manual | Auto |
| **Reusability** | Low | High |
| **Learning Curve** | Low | Medium |
| **Production Ready** | 🟡 OK | 🟢 Excellent |

---

## Conclusion

**AWS CDK Python is superior for this project because:**

✅ **Maintainable** - Easy to modify and extend
✅ **Professional** - Production-grade infrastructure
✅ **Type-safe** - Catch errors before deployment
✅ **Testable** - Unit and integration tests
✅ **Efficient** - Deploy in 20-30 minutes
✅ **Scalable** - Add developers with one config change
✅ **Reliable** - Automatic rollback on failure

**Ready to implement!** 🚀

---

**Document Version:** 1.0
**Last Updated:** 2026-01-16
**Author:** CDK Implementation Plan
**Status:** Ready for Development
