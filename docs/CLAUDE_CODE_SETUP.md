# การตั้งค่า Claude Code ใน Code-Server สำหรับใช้งาน AWS Bedrock

## ภาพรวม

คู่มือนี้จะอธิบายวิธีการตั้งค่า Claude Code extension ใน code-server ให้ใช้งาน AWS Bedrock โดยอัตโนมัติ โดยไม่ต้องแสดงหน้าจอ login

## สิ่งที่เปลี่ยนแปลง

### 1. Docker Compose Configuration

เพิ่ม environment variables สำหรับทุก developer container:

- `ANTHROPIC_BEDROCK=1` - บอก Claude Code ให้ใช้ Bedrock
- `AWS_REGION=ap-southeast-1` - Region สำหรับ Bedrock
- `ANTHROPIC_BEDROCK_AWS_REGION=ap-southeast-1` - Region สำหรับ Bedrock (specific)

เพิ่ม volume mount:

- `/home/ubuntu/.aws:/home/coder/.aws:ro` - Mount AWS credentials (read-only)

ลบ `version: '3.8'` ออกเพราะ obsolete ใน Docker Compose รุ่นใหม่

### 2. Dockerfile Updates

- ติดตั้ง Claude Code extension (anthropic.claude-code) โดยอัตโนมัติในขั้นตอน build

### 3. Configuration Files

Setup script จะสร้าง 2 ไฟล์สำหรับแต่ละ developer:

- `/mnt/ebs-data/devX/config/User/settings.json` - VSCode settings
- `/mnt/ebs-data/devX/workspace/.anthropic/config.json` - Claude Code config (ระบุ provider, region, model)

## ขั้นตอนการ Deploy

### บน Local Machine (คอมพิวเตอร์ของคุณ)

1. Upload ไฟล์ที่แก้ไขไปยัง EC2:

```bash
# เช็ค IP ของ EC2
aws ec2 describe-instances \
  --instance-ids i-06bb58792505ea98e \
  --region ap-southeast-7 \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text

# Upload files
scp -i ~/.ssh/code-server-admin-key.pem \
  cdk/scripts/docker-compose.yml \
  ubuntu@<EC2_IP>:/home/ubuntu/scripts/

scp -i ~/.ssh/code-server-admin-key.pem \
  cdk/scripts/Dockerfile.code-server \
  ubuntu@<EC2_IP>:/home/ubuntu/scripts/

scp -i ~/.ssh/code-server-admin-key.pem \
  cdk/scripts/setup-claude-code.sh \
  ubuntu@<EC2_IP>:/home/ubuntu/scripts/
```

### บน EC2 Instance

2. SSH เข้า EC2:

```bash
ssh -i ~/.ssh/code-server-admin-key.pem ubuntu@<EC2_IP>
```

3. ทำให้ script executable:

```bash
chmod +x /home/ubuntu/scripts/setup-claude-code.sh
```

4. รัน setup script:

```bash
cd /home/ubuntu/scripts
sudo ./setup-claude-code.sh
```

5. Rebuild Docker images:

```bash
cd /home/ubuntu/scripts
docker-compose build --no-cache
```

6. Restart containers:

```bash
docker-compose down
docker-compose up -d
```

7. เช็คว่า containers ทำงาน:

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}'
```

## การตรวจสอบการตั้งค่า

### ตรวจสอบ Environment Variables

```bash
# เช็คว่า Bedrock environment variables ถูกตั้งค่าแล้ว
docker exec code-server-dev1 env | grep -E "(BEDROCK|AWS_REGION)"

# ควรเห็น:
# ANTHROPIC_BEDROCK=1
# AWS_REGION=ap-southeast-1
# ANTHROPIC_BEDROCK_AWS_REGION=ap-southeast-1
```

### ตรวจสอบ VSCode Settings

```bash
# เช็คไฟล์ settings.json
cat /mnt/ebs-data/dev1/config/User/settings.json

# ควรเห็นการตั้งค่า Claude Code
```

### ทดสอบการเชื่อมต่อ Bedrock

```bash
# เข้าไปใน container
docker exec -it code-server-dev1 bash

# ทดสอบ AWS CLI
aws bedrock list-foundation-models \
  --region ap-southeast-1 \
  --by-provider anthropic \
  --query 'modelSummaries[?modelLifecycle.status==`ACTIVE`].modelId' \
  --output table
```

## การใช้งาน

1. เปิด browser ไปที่ URL ของ code-server (เช่น `https://dev1.yourdomain.com`)
2. Login ด้วย password
3. Claude Code จะเปิดในแท็บด้านข้างโดยอัตโนมัติ
4. ไม่ต้องเลือก login method - จะใช้ Bedrock ผ่าน IAM role ของ EC2 โดยตรง

## การแก้ปัญหา

### ถ้ายังเจอหน้าจอ Login

1. ตรวจสอบว่า environment variables ถูกตั้งค่า:
   ```bash
   docker exec code-server-dev1 env | grep BEDROCK
   ```

2. ตรวจสอบว่าไฟล์ settings.json มีอยู่:
   ```bash
   ls -la /mnt/ebs-data/dev1/config/User/settings.json
   ```

3. Restart container:
   ```bash
   docker-compose restart code-server-dev1
   ```

### ถ้า Claude Code ไม่ทำงาน

1. ตรวจสอบว่า extension ติดตั้งแล้ว:
   ```bash
   docker exec code-server-dev1 code-server --list-extensions | grep claude
   ```

2. ติดตั้ง extension manually (ภายใน code-server UI):
   - เปิด Extensions marketplace
   - ค้นหา "Claude Dev"
   - กด Install

3. ตรวจสอบ logs:
   ```bash
   docker logs code-server-dev1 --tail 50
   ```

### ถ้าไม่สามารถเชื่อมต่อ Bedrock

1. ตรวจสอบ IAM role ของ EC2:
   ```bash
   aws sts get-caller-identity
   ```

2. ตรวจสอบว่ามีสิทธิ์เข้าถึง Bedrock:
   ```bash
   aws bedrock list-foundation-models --region ap-southeast-1
   ```

3. ตรวจสอบ AWS credentials ใน container:
   ```bash
   docker exec code-server-dev1 ls -la /home/coder/.aws
   ```

## Model ที่ใช้ได้

ปัจจุบันตั้งค่าให้ใช้:
- **Model**: `anthropic.claude-sonnet-4-5-20250929-v1:0` (Claude Sonnet 4.5)
- **Region**: `ap-southeast-1` (Singapore)

Models อื่นที่ใช้ได้ใน Bedrock:
- `anthropic.claude-opus-4-5-20251101-v1:0` (Claude Opus 4.5)
- `anthropic.claude-sonnet-4-20250514-v1:0` (Claude Sonnet 4)
- `anthropic.claude-3-5-sonnet-20240620-v1:0` (Claude 3.5 Sonnet)

เปลี่ยน model ได้ใน `setup-claude-code.sh` ที่บรรทัด:
```json
"claude-code.model": "anthropic.claude-sonnet-4-5-20250929-v1:0"
```

## หมายเหตุสำคัญ

1. **AWS Credentials**: ไม่ต้องใส่ API key - ใช้ IAM role ของ EC2
2. **Security**: AWS credentials mount แบบ read-only (`:ro`)
3. **Cost**: การใช้งาน Bedrock จะคิดตาม API usage
4. **Region**: ใช้ Singapore (ap-southeast-1) เพราะใกล้ที่สุดกับ Bangkok

## การเปลี่ยนกลับไปใช้ Anthropic API

หากต้องการเปลี่ยนกลับไปใช้ Anthropic API แทน Bedrock:

1. แก้ไข `setup-claude-code.sh`:
   ```json
   {
     "claude-code.apiProvider": "anthropic",
     "claude-code.apiKey": "your-api-key-here"
   }
   ```

2. ลบ environment variables ที่เกี่ยวกับ Bedrock จาก `docker-compose.yml`

3. Deploy ใหม่ตามขั้นตอนข้างต้น
