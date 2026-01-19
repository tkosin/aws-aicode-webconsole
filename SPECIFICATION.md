# AWS Multi-Developer Code-Server Environment - Technical Specification

## 1. Executive Summary

ระบบ Multi-tenant Development Environment บน AWS Cloud ที่รองรับนักพัฒนา 8 คน โดยแต่ละคนจะมี code-server (VS Code in Browser) พร้อม Claude AI Extension ทำงานใน Docker container แยกกัน บน EC2 instance เดียว

## 2. System Requirements

### 2.1 AWS Resources

#### AWS Region Configuration

**Primary Region: Asia Pacific (Bangkok)**
- **Region Code**: `ap-southeast-7`
- **Region Name**: Asia Pacific (Bangkok)
- **Availability Zones**:
  - `ap-southeast-7a`
  - `ap-southeast-7b`
  - `ap-southeast-7c`

**Region Selection Rationale:**
- ✅ Lowest latency สำหรับผู้ใช้ในประเทศไทย (< 5ms)
- ✅ Data residency ภายในประเทศ (comply กับ PDPA)
- ✅ Support ทุก AWS services ที่จำเป็น
- ✅ Tier 1 region มี SLA สูง

**Network Considerations:**
- Claude API endpoint: `api.anthropic.com` (hosted in US regions)
- Expected latency to Claude API: 180-250ms (Bangkok → US West)
- Outbound internet via NAT Gateway หรือ Internet Gateway
- Inter-AZ communication: < 2ms latency

**High Availability Setup (Optional):**
- Deploy EC2 in single AZ: `ap-southeast-7a` (cost-effective)
- Future: Multi-AZ deployment with EBS replication
- ALB automatically distributes across multiple AZs

#### EC2 Instance
- **Instance Type**: `t3.2xlarge` (8 vCPU, 32 GB RAM)
  - Alternative: `t3a.2xlarge` (ประหยัดต้นทุน)
  - Production: `c5.4xlarge` (16 vCPU, 32 GB RAM) สำหรับ performance ที่ดีกว่า
- **OS**: Ubuntu 22.04 LTS (64-bit x86)
- **Storage**:
  - Root Volume: 50 GB gp3 (Boot disk)
  - Data Volume: 500 GB gp3 (EBS) สำหรับ developer workspaces
- **Network**: VPC with public subnet

#### Application Load Balancer (ALB)
- **Type**: Application Load Balancer
- **Scheme**: Internet-facing
- **IP Type**: IPv4
- **Listeners**: HTTPS (Port 443) with SSL/TLS certificate
- **Target Groups**: 8 target groups (1 per container)

#### Security Groups

**ALB Security Group**
- Inbound: HTTPS (443) from 0.0.0.0/0
- Outbound: All traffic

**EC2 Security Group**
- Inbound:
  - Ports 8443-8450 from ALB Security Group
  - SSH (22) from Admin IP only
- Outbound: All traffic (for Docker pulls, Claude API access)

### 2.2 Resource Calculations

**Per Developer:**
- CPU: 1 vCPU (allocated)
- Memory: 3-4 GB RAM
- Disk: 50 GB workspace
- Port: 1 unique port (8443-8450)

**Total Requirements:**
- CPU: 8 vCPU minimum
- Memory: 24-32 GB RAM
- Disk: 400-500 GB (8 developers × 50 GB + OS overhead)
- Ports: 8 ports

## 3. Architecture Design

### 3.1 Network Architecture

```
Internet
   ↓
Route53 (DNS)
   ↓
ALB (*.dev.example.com)
   ↓ (Subdomain routing)
   ├─→ dev1.dev.example.com → EC2:8443 (Container 1)
   ├─→ dev2.dev.example.com → EC2:8444 (Container 2)
   ├─→ dev3.dev.example.com → EC2:8445 (Container 3)
   ├─→ dev4.dev.example.com → EC2:8446 (Container 4)
   ├─→ dev5.dev.example.com → EC2:8447 (Container 5)
   ├─→ dev6.dev.example.com → EC2:8448 (Container 6)
   ├─→ dev7.dev.example.com → EC2:8449 (Container 7)
   └─→ dev8.dev.example.com → EC2:8450 (Container 8)
```

### 3.2 Container Architecture

**Docker Compose Structure:**
```yaml
services:
  code-server-dev1:
    port: 8443
    volumes: /data/dev1
    env: CLAUDE_API_KEY_1

  code-server-dev2:
    port: 8444
    volumes: /data/dev2
    env: CLAUDE_API_KEY_2

  ... (repeated for dev3-dev8)
```

### 3.3 Storage Layout

```
/mnt/ebs-data/              # EBS Volume mount point
├── dev1/                   # Developer 1 workspace
│   ├── workspace/          # Project files
│   └── config/             # code-server config
├── dev2/
├── dev3/
├── dev4/
├── dev5/
├── dev6/
├── dev7/
└── dev8/
```

## 4. Component Specifications

### 4.1 Docker Container Specification

**Base Image:**
```
codercom/code-server:latest
```

**Container Configuration:**
```yaml
# Per container
Resources:
  CPU: 1.0 (limit: 1.5)
  Memory: 3GB (limit: 4GB)

Environment Variables:
  - PASSWORD: <unique-password>
  - CLAUDE_API_KEY: <developer-specific-key>
  - HASHED_PASSWORD: <bcrypt-hash>
  - PROXY_DOMAIN: devX.dev.example.com

Volumes:
  - /mnt/ebs-data/devX:/home/coder/workspace
  - /mnt/ebs-data/devX/config:/home/coder/.local/share/code-server

Ports:
  - "844X:8080"  # Map internal 8080 to external 844X

Restart: unless-stopped

Health Check:
  Test: curl -f http://localhost:8080/healthz || exit 1
  Interval: 30s
  Timeout: 10s
  Retries: 3
```

### 4.2 Code-Server Configuration

**Per Container `/home/coder/.local/share/code-server/config.yaml`:**
```yaml
bind-addr: 0.0.0.0:8080
auth: password
password: <unique-password>
cert: false  # ALB handles SSL
```

**Pre-installed Extensions:**
- Anthropic Claude for VS Code
- Language support (Python, Node.js, Go, etc.)
- Git integration

### 4.3 ALB Configuration

**Listener Rules (Priority order):**
```
1. dev1.dev.example.com → TargetGroup-Dev1 (EC2:8443)
2. dev2.dev.example.com → TargetGroup-Dev2 (EC2:8444)
3. dev3.dev.example.com → TargetGroup-Dev3 (EC2:8445)
4. dev4.dev.example.com → TargetGroup-Dev4 (EC2:8446)
5. dev5.dev.example.com → TargetGroup-Dev5 (EC2:8447)
6. dev6.dev.example.com → TargetGroup-Dev6 (EC2:8448)
7. dev7.dev.example.com → TargetGroup-Dev7 (EC2:8449)
8. dev8.dev.example.com → TargetGroup-Dev8 (EC2:8450)
```

**Target Group Configuration:**
```yaml
Protocol: HTTP
Port: 844X (per developer)
Health Check:
  Path: /healthz
  Interval: 30s
  Healthy Threshold: 2
  Unhealthy Threshold: 3
  Timeout: 5s
Stickiness: Enabled (1 hour)
Deregistration Delay: 30s
```

**SSL/TLS:**
- Certificate: ACM certificate for `*.dev.example.com`
- Security Policy: ELBSecurityPolicy-TLS-1-2-2017-01

## 5. Security Specifications

### 5.1 Authentication

**Code-Server:**
- Password authentication (unique per developer)
- Passwords: minimum 16 characters, alphanumeric + symbols
- Store hashed passwords in secrets manager

**Claude API:**
- Individual API keys per developer
- Store in AWS Secrets Manager
- Inject as environment variables
- Rotation policy: 90 days

### 5.2 Network Security

**Security Group Rules (Detailed):**

ALB-SG:
```
Inbound:
  - Type: HTTPS, Port: 443, Source: 0.0.0.0/0
Outbound:
  - Type: Custom TCP, Port: 8443-8450, Destination: EC2-SG
```

EC2-SG:
```
Inbound:
  - Type: Custom TCP, Port: 8443-8450, Source: ALB-SG
  - Type: SSH, Port: 22, Source: <Admin-IP>/32
Outbound:
  - Type: All Traffic, Destination: 0.0.0.0/0
```

### 5.3 IAM Roles

**EC2 Instance Role:**
```json
{
  "Permissions": [
    "secretsmanager:GetSecretValue",
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents",
    "cloudwatch:PutMetricData"
  ]
}
```

## 6. Monitoring & Logging

### 6.1 CloudWatch Metrics

**EC2 Metrics:**
- CPU Utilization (alarm if > 80%)
- Memory Utilization (alarm if > 85%)
- Disk Usage (alarm if > 85%)
- Network In/Out

**Container Metrics:**
- Per-container CPU usage
- Per-container memory usage
- Container health status
- Restart count

**ALB Metrics:**
- Request count
- Target response time
- HTTP 5xx errors (alarm if > 10)
- Healthy/Unhealthy target count

### 6.2 Logging

**CloudWatch Log Groups:**
```
/aws/ec2/code-server/system          # System logs
/aws/ec2/code-server/docker          # Docker daemon logs
/aws/ec2/code-server/containers/dev1 # Container logs (per dev)
/aws/ec2/code-server/containers/dev2
...
/aws/ec2/code-server/alb             # ALB access logs
```

**Log Retention:** 30 days

## 7. Backup & Disaster Recovery

### 7.1 Backup Strategy

**EBS Snapshots:**
- Schedule: Daily at 2 AM UTC
- Retention: 7 daily, 4 weekly, 3 monthly
- Automation: AWS Backup or Lambda

**Developer Data:**
- Critical files: backup to S3 (optional)
- Git repositories: ensure remote backups

### 7.2 Recovery Procedures

**RTO (Recovery Time Objective):** 1 hour
**RPO (Recovery Point Objective):** 24 hours

**Recovery Steps:**
1. Launch new EC2 from latest snapshot
2. Restore EBS volume from snapshot
3. Update ALB target groups
4. Restart Docker containers
5. Verify health checks

## 8. Deployment Specifications

### 8.1 Prerequisites

**AWS Resources:**
- AWS Account with appropriate permissions
- VPC with public subnet
- Route53 hosted zone (e.g., dev.example.com)
- ACM certificate for *.dev.example.com

**Secrets:**
- 8 code-server passwords
- 8 Claude API keys (or 1 shared if preferred)

### 8.2 Deployment Steps

**Phase 1: Infrastructure (Terraform/CloudFormation)**
1. Create VPC and networking
2. Create security groups
3. Launch EC2 instance
4. Create and attach EBS volume
5. Create ALB and target groups
6. Configure Route53 DNS records

**Phase 2: Instance Setup (Ansible/Shell Scripts)**
1. Install Docker and Docker Compose
2. Mount EBS volume
3. Create directory structure
4. Pull code-server image
5. Create Docker Compose file
6. Retrieve secrets from Secrets Manager
7. Start all containers

**Phase 3: Configuration**
1. Install Claude extension in each container
2. Configure workspace settings
3. Test all endpoints
4. Configure monitoring and alarms

**Phase 4: Validation**
1. Health check validation
2. SSL certificate validation
3. Authentication testing
4. Claude API connectivity test
5. Performance baseline

### 8.3 Deployment Artifacts

**Required Files:**
```
deployment/
├── terraform/
│   ├── main.tf                 # Main infrastructure
│   ├── variables.tf            # Input variables
│   ├── outputs.tf              # Outputs
│   └── terraform.tfvars        # Variable values
├── docker/
│   └── docker-compose.yml      # Container definitions
├── scripts/
│   ├── setup.sh                # Initial setup
│   ├── start-containers.sh     # Start all containers
│   ├── stop-containers.sh      # Stop all containers
│   └── backup.sh               # Backup script
└── config/
    ├── alb-rules.json          # ALB routing rules
    └── secrets.json.example    # Secrets template
```

## 9. Cost Estimation (Monthly)

### 9.1 AWS Resources Cost (ap-southeast-1 - Bangkok Region)

**Compute:**
- EC2 t3.2xlarge (8 vCPU, 32GB RAM)
  - On-Demand: ~$273/month (24/7)
  - Reserved Instance (1 year): ~$175/month (36% savings)
  - Reserved Instance (3 years): ~$121/month (56% savings)
  - Spot Instance: ~$82/month (70% savings, not recommended for production)

**Storage:**
- EBS gp3 500GB (data volume): ~$48/month
- EBS gp3 50GB (root volume): ~$5/month
- EBS snapshots (average 300GB stored): ~$15/month

**Networking:**
- Application Load Balancer (ALB): ~$27/month
- ALB data processing (1TB): ~$8/month
- Data Transfer OUT to Internet (500GB): ~$45/month
- Data Transfer to Claude API (US region, 100GB): ~$9/month

**Management & Monitoring:**
- CloudWatch Logs (20GB ingestion): ~$10/month
- CloudWatch Metrics (custom metrics): ~$3/month
- CloudWatch Alarms (10 alarms): ~$1/month
- AWS Secrets Manager (16 secrets): ~$6/month

**DNS:**
- Route53 Hosted Zone: $0.50/month
- Route53 Queries (1M queries): ~$0.40/month

**Security:**
- ACM SSL Certificate: Free
- Security Groups: Free
- IAM: Free

**Backup:**
- AWS Backup (optional): ~$5/month
- EBS Snapshots (already counted above)

### 9.2 Cost Summary (Bangkok Region)

**Option 1: On-Demand EC2 (Pay-as-you-go)**
```
Total Monthly Cost: ~$455-475/month
Per Developer Cost: ~$57-59/month
```

**Breakdown:**
- EC2 Instance: $273
- Storage (EBS + Snapshots): $68
- Networking (ALB + Data Transfer): $89
- Monitoring & Logs: $14
- Secrets Manager: $6
- DNS: $1
- Backup: $5

**Option 2: 1-Year Reserved Instance (Recommended)**
```
Total Monthly Cost: ~$360-380/month
Per Developer Cost: ~$45-48/month
```

**Savings: ~$95-100/month (21% reduction)**

**Option 3: 3-Year Reserved Instance (Best value)**
```
Total Monthly Cost: ~$310-330/month
Per Developer Cost: ~$39-41/month
```

**Savings: ~$145-150/month (32% reduction)**

### 9.3 Cost Comparison: Bangkok vs Other Regions

| Region | On-Demand Cost | 1Y Reserved | Notes |
|--------|----------------|-------------|-------|
| **ap-southeast-7 (Bangkok)** | **$455** | **$360** | **Selected** |
| ap-southeast-1 (Singapore) | $440 | $350 | ใกล้กัน, latency ต่ำ (10-15ms) แต่ไม่ใช่ไทย |
| ap-southeast-3 (Jakarta) | $425 | $335 | ราคาถูกกว่า แต่ latency สูงกว่า (15-20ms) |
| ap-southeast-2 (Sydney) | $485 | $385 | ราคาแพงกว่า, latency สูง (50-60ms) |
| ap-south-1 (Mumbai) | $395 | $310 | ราคาถูกกว่า แต่ latency สูงกว่า (30-40ms) |
| us-east-1 (N. Virginia) | $380 | $285 | ราคาถูกสุด แต่ latency สูงมาก (250-300ms) |

**Recommendation:** ใช้ Bangkok region เพื่อ user experience ที่ดีที่สุด แม้ cost จะสูงกว่า ~15-20%

### 9.4 Additional Costs (Not included in base price)

**Claude API Usage (Variable):**
- Claude Sonnet: $3 per 1M input tokens, $15 per 1M output tokens
- Claude Haiku: $0.25 per 1M input tokens, $1.25 per 1M output tokens
- Estimated: $50-200/developer/month (depends on usage)
- **Total for 8 developers: $400-1,600/month**

**Optional Services:**
- VPN Connection (if needed): ~$36/month
- NAT Gateway (if private subnet): ~$45/month + data processing
- CloudFront CDN (for faster static assets): ~$20/month
- AWS Support (Business): ~$100/month (minimum)

### 9.5 Cost Optimization Recommendations

**Immediate Savings:**
1. **Reserved Instance**: -21% ($95/month savings)
2. **Reduce EBS snapshot retention**: -$5-10/month
3. **CloudWatch log optimization**: -$3-5/month
4. **Compress ALB logs to S3**: -$2-3/month

**Medium-term Savings:**
1. **Right-size EC2 after 3 months usage**: potential -15-25%
2. **Use Spot Instances for dev/test**: -70% for non-prod
3. **Implement S3 Intelligent-Tiering for backups**: -20-30%
4. **Schedule EC2 stop during off-hours**: -30-50% (if applicable)

**Advanced Optimization:**
1. **Savings Plans (1-3 year)**: additional -5-10%
2. **Move static content to S3 + CloudFront**: -$10-20/month
3. **Implement container auto-scaling**: pay only for used resources
4. **Leverage AWS Graviton2 (ARM-based)**: -20% cost, same performance

### 9.6 Monthly Cost Breakdown Chart

```
Production Setup (Bangkok Region with 1Y Reserved Instance):

EC2 t3.2xlarge (Reserved)    $175  ████████████████████ 49%
Data Transfer OUT            $62   ███████████ 17%
EBS Storage + Snapshots      $68   ████████████ 19%
ALB                          $35   ██████ 10%
CloudWatch & Logs            $14   ███ 4%
Secrets Manager              $6    █ 2%
Other (DNS, Backup)          $6    █ 2%
                            ────
Total                       $366/month
```

### 9.7 Annual Cost Projection

**Year 1 (Pay-as-you-go):**
- Setup costs: $500 (one-time)
- Monthly: $455 × 12 = $5,460
- **Total: $5,960**

**Year 1 (With 1Y Reserved Instance):**
- Setup costs: $500 (one-time)
- Upfront RI payment: $1,050
- Monthly: $360 × 12 = $4,320
- **Total: $5,870**
- **Savings: $90 first year**

**Year 2-3 (With Reserved Instance):**
- Monthly: $360 × 12 = $4,320/year
- **Savings vs On-Demand: ~$1,140/year**

### 9.8 Cost Alerts Configuration

**Recommended CloudWatch Billing Alarms:**
1. Monthly cost > $400 → Warning alert
2. Monthly cost > $500 → Critical alert
3. Data transfer > 600GB → Investigate alert
4. EBS storage > 550GB → Capacity alert

**Budget Setup:**
- Monthly budget: $400 (with 1Y RI)
- Alert at 80% ($320)
- Alert at 100% ($400)
- Alert at 120% ($480)

## 10. Operational Procedures

### 10.1 Adding New Developer

1. Create new directory: `/mnt/ebs-data/dev9`
2. Generate new password and store in Secrets Manager
3. Add new service to docker-compose.yml
4. Create new ALB target group
5. Add listener rule for new subdomain
6. Start new container
7. Create DNS record: dev9.dev.example.com

### 10.2 Removing Developer

1. Stop container
2. Remove from docker-compose.yml
3. Remove ALB target group and listener rule
4. Archive workspace data to S3
5. Delete workspace directory
6. Remove DNS record

### 10.3 Maintenance Windows

**Regular Maintenance:**
- Weekly: Check disk usage, review logs
- Monthly: Update code-server image, security patches
- Quarterly: Review and rotate secrets

**Update Procedure:**
1. Notify developers (24h notice)
2. Pull latest code-server image
3. Rolling restart (1 container at a time)
4. Verify health checks
5. Confirm with developers

## 11. Performance Tuning

### 11.1 EC2 Instance Optimization

**Kernel Parameters `/etc/sysctl.conf`:**
```
net.core.somaxconn = 4096
net.ipv4.tcp_max_syn_backlog = 8192
vm.swappiness = 10
fs.file-max = 65536
```

**Docker Daemon `/etc/docker/daemon.json`:**
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
  }
}
```

### 11.2 Container Resource Limits

**CPU Shares:**
```yaml
# Ensure fair CPU distribution
cpu_shares: 1024  # Default weight
```

**Memory Limits:**
```yaml
mem_limit: 4g
mem_reservation: 3g
```

## 12. Troubleshooting Guide

### 12.1 Common Issues

**Issue: Container won't start**
- Check logs: `docker logs code-server-devX`
- Verify port not in use: `netstat -tulpn | grep 844X`
- Check disk space: `df -h`

**Issue: Cannot access via subdomain**
- Verify DNS resolution: `nslookup devX.dev.example.com`
- Check ALB target health
- Verify security group rules

**Issue: High CPU usage**
- Check per-container usage: `docker stats`
- Identify resource-heavy processes
- Consider scaling to larger instance

**Issue: Claude API not working**
- Verify API key: `env | grep CLAUDE`
- Check outbound connectivity: `curl https://api.anthropic.com`
- Review API quota limits

## 13. Success Criteria

### 13.1 Functional Requirements
- ✅ 8 developers can access their individual code-server instances
- ✅ Each instance has working Claude extension
- ✅ SSL/TLS encryption on all connections
- ✅ Individual workspace data persistence
- ✅ Health monitoring and alerting

### 13.2 Performance Requirements
- ✅ Page load time < 3 seconds
- ✅ Code editor responsiveness < 100ms
- ✅ Claude API response time < 5 seconds
- ✅ System uptime > 99.5%

### 13.3 Security Requirements
- ✅ Individual authentication per developer
- ✅ Encrypted data in transit (HTTPS)
- ✅ Isolated workspaces
- ✅ Secrets stored in AWS Secrets Manager
- ✅ Regular security updates

## 14. Future Enhancements

### 14.1 Short-term (3 months)
- Auto-scaling based on usage
- GitLab/GitHub integration
- Automated backups to S3
- Custom workspace templates

### 14.2 Long-term (6-12 months)
- Multi-region deployment
- Kubernetes migration (EKS)
- Centralized log aggregation (ELK)
- SSO integration (SAML/OAuth)
- GPU support for ML workloads

## 15. Appendix

### 15.1 Port Mapping Reference

| Developer | Subdomain | EC2 Port | Container Internal Port |
|-----------|-----------|----------|-------------------------|
| Dev 1 | dev1.dev.example.com | 8443 | 8080 |
| Dev 2 | dev2.dev.example.com | 8444 | 8080 |
| Dev 3 | dev3.dev.example.com | 8445 | 8080 |
| Dev 4 | dev4.dev.example.com | 8446 | 8080 |
| Dev 5 | dev5.dev.example.com | 8447 | 8080 |
| Dev 6 | dev6.dev.example.com | 8448 | 8080 |
| Dev 7 | dev7.dev.example.com | 8449 | 8080 |
| Dev 8 | dev8.dev.example.com | 8450 | 8080 |

### 15.2 Reference Links

- Code-Server Documentation: https://coder.com/docs/code-server
- Claude API Documentation: https://docs.anthropic.com/
- AWS Application Load Balancer: https://docs.aws.amazon.com/elasticloadbalancing/
- Docker Compose: https://docs.docker.com/compose/

---

**Document Version:** 1.0
**Last Updated:** 2026-01-16
**Author:** System Specification
**Status:** Ready for Implementation
