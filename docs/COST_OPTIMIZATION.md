# Cost Optimization Guide: Start/Stop Procedures

## Overview

This guide provides detailed instructions for starting and stopping AWS resources to save costs when the development environment is not in use.

**Current Infrastructure:**
- **Region:** ap-southeast-7 (Bangkok)
- **EC2 Instance:** i-06bb58792505ea98e (t3.2xlarge)
- **Public IP:** 43.209.211.56 (changes when stopped/started)
- **EBS Volume:** vol-07171e15c683a75a8 (500GB)
- **Containers:** 8 code-server instances (dev1-dev8)
- **ALB DNS:** code-server-multi-dev-alb-1784952202.ap-southeast-7.elb.amazonaws.com

---

## Cost Breakdown

| Service | Running Cost | Stopped Cost | Savings |
|---------|--------------|--------------|---------|
| EC2 t3.2xlarge | ~$120/month | $0 | 100% |
| EBS 500GB gp3 | ~$40/month | ~$40/month | 0% |
| ALB | ~$22/month | ~$22/month | 0% |
| Data Transfer | ~$15/month | ~$15/month | 0% |
| **Total** | **~$200/month** | **~$77/month** | **~$123/month** |

**💡 Key Insight:** Stopping the EC2 instance saves approximately 60% of monthly costs (~$123/month) while preserving all developer data.

---

## ⚠️ Important Warnings

1. **Public IP Changes:** The EC2 public IP will change every time you stop and start the instance. The ALB DNS remains the same.
2. **Containers Don't Auto-Start:** Docker containers must be manually started after EC2 restart.
3. **DNS Records Remain Valid:** Your CNAME records pointing to the ALB DNS don't need updating.
4. **Data is Always Safe:** All developer data is stored on the EBS volume (vol-07171e15c683a75a8) which persists independently.

---

## Method 1: Stop EC2 Instance (Recommended for Short-Term)

**Best For:** Nights, weekends, or short breaks (hours to weeks)
**Saves:** ~$123/month (~60% of total cost)
**Data Safety:** ✅ 100% safe - all data preserved on EBS volume

### Stop EC2 Instance

```bash
# Stop the EC2 instance
aws ec2 stop-instances \
  --instance-ids i-06bb58792505ea98e \
  --region ap-southeast-7

# Verify it's stopping/stopped
aws ec2 describe-instances \
  --instance-ids i-06bb58792505ea98e \
  --region ap-southeast-7 \
  --query 'Reservations[0].Instances[0].State.Name'
```

**Expected Output:** `"stopping"` → `"stopped"`

### Start EC2 Instance

```bash
# Start the EC2 instance
aws ec2 start-instances \
  --instance-ids i-06bb58792505ea98e \
  --region ap-southeast-7

# Wait for it to be running
aws ec2 wait instance-running \
  --instance-ids i-06bb58792505ea98e \
  --region ap-southeast-7

# Get the new public IP
aws ec2 describe-instances \
  --instance-ids i-06bb58792505ea98e \
  --region ap-southeast-7 \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text
```

### ✅ Containers Start Automatically (v1.1+)

**Good News:** Containers จะเปิดอัตโนมัติเมื่อ EC2 start!

**คุณสมบัติ:**
- ✅ Systemd service จะ start containers อัตโนมัติ
- ✅ Health check ทุก container ก่อนแจ้งเตือน
- ✅ Slack notification เมื่อพร้อมใช้งาน (ถ้าตั้งค่าไว้)
- ⏱️ รอประมาณ 2-3 นาที containers จะพร้อม

**ไม่ต้องทำอะไร - รอ Slack notification หรือตรวจสอบด้วย:**

```bash
# ตรวจสอบว่า containers พร้อมหรือยัง
NEW_IP=$(aws ec2 describe-instances \
  --instance-ids i-06bb58792505ea98e \
  --region ap-southeast-7 \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

ssh -i ~/.ssh/code-server-admin-key.pem ubuntu@$NEW_IP \
  "docker ps | grep healthy"
```

### Manual Start (ถ้าต้องการ)

ถ้า auto-start ไม่ทำงานหรือต้องการ start manual:

```bash
# SSH to the new IP
ssh -i ~/.ssh/code-server-admin-key.pem ubuntu@<NEW_PUBLIC_IP>

# Option 1: Use systemd service (recommended)
sudo systemctl start code-server-containers.service

# Option 2: Manual docker-compose
cd /home/ubuntu/scripts
docker-compose up -d

# Verify all containers are running
docker ps

# Check container health
docker-compose ps
```

**📖 ดูรายละเอียดเพิ่มเติม:** [AUTO_START_SETUP.md](AUTO_START_SETUP.md)

### Verify Target Groups are Healthy

```bash
# Check target group health for all 8 environments
for i in {1..8}; do
  echo "Checking dev$i target group..."
  TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups \
    --region ap-southeast-7 \
    --query "TargetGroups[?contains(TargetGroupName, 'dev$i')].TargetGroupArn" \
    --output text)

  aws elbv2 describe-target-health \
    --target-group-arn $TARGET_GROUP_ARN \
    --region ap-southeast-7 \
    --query 'TargetHealthDescriptions[0].TargetHealth.State' \
    --output text
done
```

**Expected Output:** All should show `healthy`

---

## Method 2: Stop Only Docker Containers (NOT Recommended)

**Best For:** Never - provides no cost savings
**Saves:** $0 (EC2 still charged when running)
**Data Safety:** ✅ 100% safe

This method is only useful for maintenance/updates, not cost savings.

```bash
# SSH to the EC2 instance
ssh -i ~/.ssh/code-server-admin-key.pem ubuntu@43.209.211.56

# Stop all containers
cd /home/ubuntu/scripts
docker-compose down

# To restart
docker-compose up -d
```

---

## Method 3: Destroy Stack + Snapshot (For Long-Term Shutdown)

**Best For:** Extended shutdown (months+) or permanent decommissioning
**Saves:** ~$160/month (80% of total cost - only pay for snapshot storage ~$40/month)
**Data Safety:** ✅ Safe if snapshot is created properly

### Create EBS Snapshot Before Destroying

```bash
# Create a snapshot of the EBS volume
aws ec2 create-snapshot \
  --volume-id vol-07171e15c683a75a8 \
  --description "code-server-backup-$(date +%Y%m%d)" \
  --region ap-southeast-7 \
  --tag-specifications 'ResourceType=snapshot,Tags=[{Key=Name,Value=code-server-backup},{Key=Environment,Value=production}]'

# Wait for snapshot to complete (can take 10-30 minutes)
SNAPSHOT_ID=$(aws ec2 describe-snapshots \
  --region ap-southeast-7 \
  --filters "Name=volume-id,Values=vol-07171e15c683a75a8" \
  --query 'Snapshots | sort_by(@, &StartTime) | [-1].SnapshotId' \
  --output text)

aws ec2 wait snapshot-completed \
  --snapshot-ids $SNAPSHOT_ID \
  --region ap-southeast-7

echo "Snapshot created: $SNAPSHOT_ID"
```

### Destroy All Stacks

```bash
cd /Users/yod/Develop/aws-aicode-webconsole/cdk

# Destroy stacks in reverse order (dependencies)
cdk destroy monitoring-stack --force
cdk destroy alb-stack --force
cdk destroy compute-stack --force
cdk destroy network-stack --force
cdk destroy backup-stack --force
cdk destroy certificate-stack --force
```

### Restore from Snapshot (When Needed)

To restore the environment:

1. **Create volume from snapshot:**
```bash
aws ec2 create-volume \
  --snapshot-id $SNAPSHOT_ID \
  --availability-zone ap-southeast-7a \
  --volume-type gp3 \
  --size 500 \
  --region ap-southeast-7 \
  --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=code-server-data-restored}]'
```

2. **Modify compute_stack.py** to use the restored volume instead of creating a new one.

3. **Re-deploy all stacks:**
```bash
cdk deploy --all
```

---

## Quick Reference Commands

### Check Current Status

```bash
# Check EC2 status
aws ec2 describe-instances \
  --instance-ids i-06bb58792505ea98e \
  --region ap-southeast-7 \
  --query 'Reservations[0].Instances[0].[State.Name,PublicIpAddress]' \
  --output table

# Check container status (requires SSH)
ssh -i ~/.ssh/code-server-admin-key.pem ubuntu@43.209.211.56 \
  "cd /home/ubuntu/scripts && docker-compose ps"

# Check estimated monthly cost (when running)
echo "Estimated monthly cost: ~\$200 (EC2: \$120, EBS: \$40, ALB: \$22, Transfer: \$15)"
```

### Emergency Stop (Fastest Method)

```bash
# Stop everything immediately
aws ec2 stop-instances \
  --instance-ids i-06bb58792505ea98e \
  --region ap-southeast-7 \
  --force
```

---

## Recommended Usage Patterns

### Daily Use (Active Development)
- **Action:** Keep everything running
- **Cost:** ~$200/month
- **Best for:** Active 8-developer team

### Evening/Weekend Shutdown
- **Action:** Stop EC2 at 6pm, start at 9am
- **Cost:** ~$150/month (25% savings)
- **Commands:**
  ```bash
  # At 6pm
  aws ec2 stop-instances --instance-ids i-06bb58792505ea98e --region ap-southeast-7

  # At 9am
  aws ec2 start-instances --instance-ids i-06bb58792505ea98e --region ap-southeast-7
  # Then SSH and run: docker-compose up -d
  ```

### Extended Break (1+ weeks)
- **Action:** Stop EC2 entirely
- **Cost:** ~$77/month (60% savings)
- **Duration:** As long as needed

### Long-Term Shutdown (Months+)
- **Action:** Snapshot + destroy all stacks
- **Cost:** ~$40/month (80% savings)
- **Note:** Requires full redeployment when resuming

---

## Automation Tips

### Schedule Automatic Stop/Start

You can use AWS Systems Manager or Lambda with EventBridge to automate EC2 stop/start:

```bash
# Example: Stop EC2 every night at 8pm (UTC+7 = 13:00 UTC)
# Create EventBridge rule that triggers Lambda to stop instance

# Example: Start EC2 every morning at 8am (UTC+7 = 01:00 UTC)
# Create EventBridge rule that triggers Lambda to start instance + SSH to start containers
```

### Monitor Costs

```bash
# Check current month's costs
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics "BlendedCost" \
  --region us-east-1
```

---

## Troubleshooting

### Issue: Containers won't start after EC2 restart

**Solution:**
```bash
ssh -i ~/.ssh/code-server-admin-key.pem ubuntu@<NEW_IP>
sudo systemctl status docker
sudo systemctl start docker
cd /home/ubuntu/scripts
docker-compose up -d
```

### Issue: Target groups showing unhealthy

**Wait:** It takes 30-60 seconds for containers to pass health checks.

**Check:**
```bash
# Check container logs
docker logs code-server-dev1

# Check if port is listening
netstat -tlnp | grep 8443
```

### Issue: Can't SSH to EC2

**Check security group allows your IP:**
```bash
aws ec2 describe-security-groups \
  --region ap-southeast-7 \
  --filters "Name=group-name,Values=code-server-multi-dev-sg" \
  --query 'SecurityGroups[0].IpPermissions[?FromPort==`22`]'
```

---

## Data Safety Guarantees

✅ **EBS Volume Persists Independently**
- Volume ID: vol-07171e15c683a75a8
- Size: 500GB
- Mount point: /mnt/ebs-data
- Contains all developer workspaces and configs

✅ **What's Preserved When EC2 Stops:**
- All code and files in `/mnt/ebs-data/dev1-dev8/workspace`
- All VS Code settings in `/mnt/ebs-data/dev1-dev8/config`
- Docker images (unless explicitly deleted)
- All environment variables in `/home/ubuntu/scripts/.env`

❌ **What's Lost When EC2 Stops:**
- Public IP address (changes on restart)
- Running processes in containers
- System logs (unless exported)
- Temporary files in /tmp

✅ **Automatic Backups (When Enabled)**
- Daily snapshots of EBS volume
- 30-day retention
- Managed by AWS Backup service

---

## Cost Optimization Checklist

- [ ] Stop EC2 when not in use (saves $123/month)
- [ ] Monitor actual usage patterns to optimize stop/start schedule
- [ ] Consider downsizing EC2 instance if resource usage is consistently low
- [ ] Review ALB necessity - if external access isn't needed, could use direct access
- [ ] Enable AWS Budget alerts to monitor spending
- [ ] Review EBS volume size - current usage is 34GB out of 500GB
- [ ] Consider Reserved Instances if usage is consistent (up to 70% savings)

---

## Support Contacts

**AWS Documentation:**
- EC2 Stop/Start: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Stop_Start.html
- EBS Snapshots: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSSnapshots.html
- Cost Optimization: https://aws.amazon.com/pricing/cost-optimization/

**Emergency Commands:**
```bash
# Force stop everything
aws ec2 stop-instances --instance-ids i-06bb58792505ea98e --region ap-southeast-7 --force

# Check what's costing money right now
aws ce get-cost-and-usage --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) --granularity DAILY --metrics "BlendedCost" --region us-east-1
```

---

*Last Updated: 2026-01-19*
*Infrastructure Version: v1.0*
*Region: ap-southeast-7 (Bangkok)*
