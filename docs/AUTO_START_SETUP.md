# Auto-Start Containers และ Slack Notification Setup Guide

## Overview

เอกสารนี้อธิบายวิธีการตั้งค่า auto-start containers และ Slack notification เมื่อ EC2 instance เปิดใช้งาน

**คุณสมบัติ:**
- ✅ Containers เปิดอัตโนมัติเมื่อ start EC2
- ✅ Health check ทุก container ก่อนแจ้งเตือน
- ✅ Slack notification พร้อม developer access URLs
- ✅ Systemd service สำหรับจัดการ lifecycle

---

## การทำงาน

1. เมื่อ EC2 instance เปิด systemd จะเรียก `code-server-containers.service`
2. Service จะรัน script `/home/ubuntu/scripts/start-containers-and-notify.sh`
3. Script จะ:
   - รอให้ Docker daemon พร้อม
   - Start containers ด้วย `docker-compose up -d`
   - ตรวจสอบ health status ของ containers ทั้ง 8 ตัว (รอสูงสุด 5 นาที)
   - เมื่อทุก container healthy แล้ว ส่ง notification ไปที่ Slack

---

## ขั้นตอนการติดตั้ง

### 1. สร้าง Slack Incoming Webhook

1. ไปที่ https://api.slack.com/messaging/webhooks
2. คลิก "Create your Slack app" (ถ้ายังไม่มี app)
3. เลือก "From scratch"
4. ตั้งชื่อ app เช่น "Code-Server Notifier"
5. เลือก workspace ที่ต้องการ
6. ไปที่ "Incoming Webhooks" ในเมนูด้านซ้าย
7. เปิด "Activate Incoming Webhooks"
8. คลิก "Add New Webhook to Workspace"
9. เลือก channel ที่ต้องการรับ notification
10. Copy Webhook URL (รูปแบบ: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX`)

### 2. เพิ่ม Webhook URL ใน Configuration

แก้ไขไฟล์ [cdk/config/prod.py](../cdk/config/prod.py):

```python
# Slack Notification Configuration
# Create a Slack Incoming Webhook at:
# https://api.slack.com/messaging/webhooks
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### 3. Deploy/Update Compute Stack

#### ถ้ายัง Deploy Infrastructure ครั้งแรก:

```bash
cd /Users/yod/Develop/aws-aicode-webconsole/cdk

# Deploy ทั้งหมด
cdk deploy --all
```

#### ถ้า Deploy แล้วและต้องการ Update:

```bash
cd /Users/yod/Develop/aws-aicode-webconsole/cdk

# Deploy เฉพาะ compute stack
cdk deploy code-server-multi-dev-compute
```

**⚠️ หมายเหตุ:** การ update compute stack จะทำให้ EC2 instance ถูก replace (ถ้า user data เปลี่ยน) แต่ข้อมูลบน EBS volume จะปลอดภัย

### 4. Deploy Docker Compose Files (ถ้ายังไม่ได้ Deploy)

SSH เข้า EC2 และ copy files:

```bash
# Get new public IP
NEW_IP=$(aws ec2 describe-instances \
  --instance-ids i-06bb58792505ea98e \
  --region ap-southeast-7 \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "New IP: $NEW_IP"

# SSH to EC2
ssh -i ~/.ssh/code-server-admin-key.pem ubuntu@$NEW_IP

# Copy docker-compose files to scripts directory
cd /home/ubuntu/scripts

# Download files (ถ้ามี Git repo)
# หรือ copy จากเครื่อง local
exit

# Copy from local machine
scp -i ~/.ssh/code-server-admin-key.pem \
  /Users/yod/Develop/aws-aicode-webconsole/cdk/scripts/docker-compose.yml \
  ubuntu@$NEW_IP:/home/ubuntu/scripts/

scp -i ~/.ssh/code-server-admin-key.pem \
  /Users/yod/Develop/aws-aicode-webconsole/cdk/scripts/Dockerfile.code-server \
  ubuntu@$NEW_IP:/home/ubuntu/scripts/

scp -i ~/.ssh/code-server-admin-key.pem \
  /tmp/.env \
  ubuntu@$NEW_IP:/home/ubuntu/scripts/
```

### 5. Build Docker Image และ Start Containers

```bash
# SSH back in
ssh -i ~/.ssh/code-server-admin-key.pem ubuntu@$NEW_IP

cd /home/ubuntu/scripts

# Build image
docker build -f Dockerfile.code-server -t code-server-dev:latest .

# Start containers manually first time
docker-compose up -d

# Verify all containers are running
docker-compose ps

# Check logs
tail -f /var/log/container-startup.log
```

---

## การทดสอบ Auto-Start

### Test 1: Stop และ Start EC2

```bash
# Stop EC2
aws ec2 stop-instances \
  --instance-ids i-06bb58792505ea98e \
  --region ap-southeast-7

# รอจน stopped
aws ec2 wait instance-stopped \
  --instance-ids i-06bb58792505ea98e \
  --region ap-southeast-7

# Start EC2
aws ec2 start-instances \
  --instance-ids i-06bb58792505ea98e \
  --region ap-southeast-7

# รอจน running
aws ec2 wait instance-running \
  --instance-ids i-06bb58792505ea98e \
  --region ap-southeast-7

# Get new IP
NEW_IP=$(aws ec2 describe-instances \
  --instance-ids i-06bb58792505ea98e \
  --region ap-southeast-7 \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "New IP: $NEW_IP"
```

### Test 2: ตรวจสอบว่า Containers เปิดอัตโนมัติ

รอประมาณ 2-3 นาทีหลัง EC2 เปิด จากนั้น:

```bash
# SSH เข้าไป
ssh -i ~/.ssh/code-server-admin-key.pem ubuntu@$NEW_IP

# ตรวจสอบ systemd service status
sudo systemctl status code-server-containers.service

# ตรวจสอบ container status
docker ps

# ดู logs
sudo tail -100 /var/log/container-startup.log

# ดู systemd journal
sudo journalctl -u code-server-containers.service -n 50 --no-pager
```

**Expected Output:**
```
● code-server-containers.service - Code-Server Docker Containers
     Loaded: loaded (/etc/systemd/system/code-server-containers.service; enabled; vendor preset: enabled)
     Active: active (exited) since Sun 2026-01-19 12:00:00 UTC; 2min ago
```

### Test 3: ตรวจสอบ Slack Notification

ตรวจสอบ Slack channel ที่คุณเลือกไว้ ควรได้รับข้อความแบบนี้:

```
🚀 Code-Server Environment Ready

Status: ✅ All 8 containers healthy
Instance: i-06bb58792505ea98e
Public IP: 43.209.211.56
Region: ap-southeast-7

Developer Access URLs:
• Dev 1  • Dev 2  • Dev 3  • Dev 4
• Dev 5  • Dev 6  • Dev 7  • Dev 8

Started at: Jan 19, 2026 7:00 PM
```

---

## Troubleshooting

### ปัญหา: Slack notification ไม่ส่ง

**วิธีแก้:**

1. ตรวจสอบ Webhook URL ใน config:
```bash
grep SLACK_WEBHOOK_URL /home/ubuntu/scripts/start-containers-and-notify.sh
```

2. ทดสอบส่ง Slack manual:
```bash
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test notification"}' \
  https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

3. ตรวจสอบ logs:
```bash
sudo tail -100 /var/log/container-startup.log | grep -i slack
```

### ปัญหา: Containers ไม่เปิดอัตโนมัติ

**วิธีแก้:**

1. ตรวจสอบ systemd service:
```bash
sudo systemctl status code-server-containers.service
```

2. ดู service logs:
```bash
sudo journalctl -u code-server-containers.service -n 100 --no-pager
```

3. ตรวจสอบว่า docker-compose.yml มีอยู่:
```bash
ls -la /home/ubuntu/scripts/docker-compose.yml
```

4. ตรวจสอบ permissions:
```bash
ls -la /home/ubuntu/scripts/start-containers-and-notify.sh
# ควร: -rwxr-xr-x 1 ubuntu ubuntu
```

5. เริ่ม service manual:
```bash
sudo systemctl start code-server-containers.service
sudo systemctl status code-server-containers.service
```

### ปัญหา: Containers unhealthy เกิน timeout (5 นาที)

**วิธีแก้:**

1. ตรวจสอบ container logs:
```bash
docker-compose logs code-server-dev1
```

2. ตรวจสอบ resource usage:
```bash
free -h
df -h
docker stats --no-stream
```

3. ตรวจสอบ health check endpoint:
```bash
curl http://localhost:8443/healthz
```

4. เพิ่ม timeout ใน script (แก้ไข MAX_WAIT):
```bash
sudo nano /home/ubuntu/scripts/start-containers-and-notify.sh
# เปลี่ยน MAX_WAIT=300 เป็น MAX_WAIT=600 (10 minutes)
```

### ปัญหา: Service ไม่ start หลัง reboot

**วิธีแก้:**

1. Enable service อีกครั้ง:
```bash
sudo systemctl enable code-server-containers.service
```

2. ตรวจสอบว่า Docker service enabled:
```bash
sudo systemctl is-enabled docker
# ควรได้: enabled
```

3. ตรวจสอบ service dependencies:
```bash
sudo systemctl list-dependencies code-server-containers.service
```

---

## Manual Control

### Start Containers Manually

```bash
sudo systemctl start code-server-containers.service
```

### Stop Containers Manually

```bash
sudo systemctl stop code-server-containers.service
# หรือ
cd /home/ubuntu/scripts && docker-compose down
```

### Restart Containers

```bash
sudo systemctl restart code-server-containers.service
```

### Disable Auto-Start

```bash
sudo systemctl disable code-server-containers.service
```

### Re-enable Auto-Start

```bash
sudo systemctl enable code-server-containers.service
```

---

## Slack Notification Format

Notification จะส่งข้อมูลดังนี้:

- **Status:** ✅ All 8 containers healthy
- **Instance ID:** i-06bb58792505ea98e
- **Public IP:** IP address ใหม่ (เปลี่ยนทุกครั้งที่ start)
- **Region:** ap-southeast-7 (Bangkok)
- **Developer URLs:** Links ไปที่ dev1-dev8 subdomains
- **Timestamp:** เวลาที่ containers พร้อมใช้งาน

---

## Cost Implications

**ไม่มีค่าใช้จ่ายเพิ่มเติม** สำหรับ:
- Systemd service (ฟรี - เป็น OS feature)
- Health check script (ฟรี - รันบน EC2)
- Slack notifications (ฟรี - Incoming Webhooks ไม่เสียค่าใช้จ่าย)

**Auto-start ช่วยประหยัดเวลา:**
- ไม่ต้อง SSH เข้าไป start containers manual
- ไม่ต้องกังวลว่าลืม start containers
- รู้ทันทีว่า environment พร้อมใช้งาน

---

## Security Considerations

1. **Slack Webhook URL:**
   - เก็บใน config file (prod.py)
   - ไม่ commit ใน Git (ควรใช้ .gitignore)
   - สามารถ rotate Webhook URL ได้ตามต้องการ

2. **Service Permissions:**
   - Service รันในฐานะ user `ubuntu` (ไม่ใช่ root)
   - มีสิทธิ์เฉพาะที่จำเป็น

3. **Log Files:**
   - `/var/log/container-startup.log` มี webhook URL
   - ตั้ง permission ให้เหมาะสม:
   ```bash
   sudo chmod 640 /var/log/container-startup.log
   ```

---

## Future Enhancements

Ideas สำหรับการพัฒนาต่อ:

1. **Slack Commands:**
   - สั่ง stop/start/restart containers ผ่าน Slack
   - ดู container status ผ่าน Slack

2. **More Notifications:**
   - แจ้งเตือนเมื่อ container unhealthy
   - แจ้งเตือนเมื่อ disk space ใกล้เต็ม
   - แจ้งเตือนเมื่อ CPU/Memory สูง

3. **Dashboard:**
   - Web dashboard แสดง container status
   - Real-time metrics

4. **Auto-Scaling:**
   - Auto-start containers ตามจำนวนที่ต้องการ
   - Dynamic port allocation

---

## References

- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)
- [Systemd Service Documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [AWS EC2 User Data](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html)

---

*Last Updated: 2026-01-19*
*Infrastructure Version: v1.1 (with auto-start)*
*Region: ap-southeast-7 (Bangkok)*
