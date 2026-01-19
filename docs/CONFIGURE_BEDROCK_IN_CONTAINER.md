# Configure Claude Code with Bedrock in Code-Server Containers

## ✅ สิ่งที่ติดตั้งเสร็จแล้ว

ตอนนี้ใน containers ทั้ง 8 ตัว (dev1-dev8) มีการติดตั้งแล้ว:
- ✅ Claude Code CLI (version 2.1.12)
- ✅ AWS CLI (version 2.33.2)
- ✅ Environment variables สำหรับ Bedrock (ANTHROPIC_BEDROCK=true, AWS_REGION=us-east-1)

## 🔑 ขั้นตอนสุดท้าย: Configure AWS Credentials

### วิธีที่ 1: ใช้ AWS Credentials ของคุณเอง (แนะนำ)

1. เปิด browser ไปที่ https://dev1.tuworkshop.vibecode.letsrover.ai (หรือ dev2-dev8)
2. เปิด Terminal ใน VS Code (View > Terminal หรือกด Ctrl+`)
3. รันคำสั่งต่อไปนี้:

```bash
aws configure
```

4. ใส่ข้อมูล AWS credentials ของคุณ:
```
AWS Access Key ID [None]: YOUR_ACCESS_KEY_ID
AWS Secret Access Key [None]: YOUR_SECRET_ACCESS_KEY
Default region name [None]: us-east-1
Default output format [None]: json
```

5. ทดสอบการเชื่อมต่อ:
```bash
aws sts get-caller-identity
```

6. ทดสอบ Bedrock:
```bash
aws bedrock list-foundation-models \
  --region us-east-1 \
  --by-provider anthropic \
  --output table
```

### วิธีที่ 2: ใช้ AWS IAM Role (สำหรับ Advanced Users)

ถ้าต้องการให้ container ใช้ EC2 instance role โดยอัตโนมัติ:

1. เพิ่ม IAM policy ให้ EC2 instance role สามารถเข้าถึง Bedrock:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:ListFoundationModels",
                "bedrock:GetFoundationModel"
            ],
            "Resource": "*"
        }
    ]
}
```

2. Configure container ให้ใช้ instance metadata:
```bash
# ใน container terminal
export AWS_EC2_METADATA_DISABLED=false
```

---

## 🚀 วิธีใช้ Claude Code

หลังจาก configure AWS credentials เสร็จแล้ว:

### 1. ใช้ผ่าน VS Code Extension

1. คลิกที่ปุ่ม Claude Code ในหน้า Welcome screen
2. เลือก **"Vertex or Bedrock"**
3. Claude Code จะใช้ Amazon Bedrock อัตโนมัติ!

### 2. ใช้ผ่าน Terminal

```bash
# เปิด terminal ใหม่ (เพื่อให้ environment variables ทำงาน)
# หรือรัน
source ~/.bashrc

# ตรวจสอบ environment variables
echo "ANTHROPIC_BEDROCK: $ANTHROPIC_BEDROCK"
echo "AWS_REGION: $AWS_REGION"

# ใช้ Claude Code
claude
```

### 3. ทดสอบ Bedrock API โดยตรง

```bash
# Create test payload
cat > /tmp/test-bedrock.json << 'EOF'
{
  "anthropic_version": "bedrock-2023-05-31",
  "max_tokens": 100,
  "messages": [
    {
      "role": "user",
      "content": "Say 'Hello from Bedrock in code-server!'"
    }
  ]
}
EOF

# Call Bedrock API
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-haiku-20240307-v1:0 \
  --region us-east-1 \
  --body file:///tmp/test-bedrock.json \
  --cli-binary-format raw-in-base64-out \
  /tmp/response.json

# Show response
cat /tmp/response.json | jq -r '.content[0].text'
```

---

## 🔍 Troubleshooting

### ปัญหา: "The security token included in the request is invalid"

**สาเหตุ:** AWS credentials ยังไม่ได้ configure หรือ credentials หมดอายุ

**แก้ไข:**
```bash
# Configure AWS credentials ใหม่
aws configure

# หรือ set environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

### ปัญหา: "claude: command not found"

**แก้ไข:**
```bash
# Reload environment
source ~/.bashrc

# หรือเปิด terminal ใหม่
```

### ปัญหา: Environment variables ว่างเปล่า

**แก้ไข:**
```bash
# เปิด terminal ใหม่ หรือรัน
source ~/.bashrc

# หรือ set manual
export ANTHROPIC_BEDROCK=true
export AWS_REGION=us-east-1
```

### ปัญหา: "Model not accessible"

**แก้ไข:**
1. ตรวจสอบว่า enable Bedrock model access แล้ว:
   - ไปที่ AWS Console > Bedrock > Model access
   - Request access สำหรับ Anthropic models

2. ตรวจสอบ IAM permissions:
```bash
# ทดสอบว่าสามารถเรียก Bedrock API ได้หรือไม่
aws bedrock list-foundation-models --region us-east-1
```

---

## 📖 Available Models in us-east-1

| Model | Model ID | Use Case |
|-------|----------|----------|
| **Claude Opus 4.5** | `anthropic.claude-opus-4-5-20251101-v1:0` | Most capable |
| **Claude Sonnet 4.5** | `anthropic.claude-sonnet-4-5-20250929-v1:0` | Balanced |
| **Claude Haiku 4.5** | `anthropic.claude-haiku-4-5-20251001-v1:0` | Fast & cheap |
| **Claude 3.5 Haiku** | `anthropic.claude-3-5-haiku-20241022-v1:0` | Previous gen |
| **Claude 3 Haiku** | `anthropic.claude-3-haiku-20240307-v1:0` | Legacy |

---

## 💾 Save Configuration for Future

เพื่อให้ configuration คงอยู่แม้ container restart:

1. **AWS Credentials** - ถูกเก็บใน `/home/coder/.aws/credentials` ซึ่ง mount กับ EBS volume แล้ว
2. **Environment Variables** - อยู่ใน `/home/coder/.bashrc` และ `/home/coder/.bash_profile`
3. **Claude Code** - ติดตั้งใน container แล้ว

**ข้อมูลเหล่านี้จะคงอยู่ตลอดไป!** ไม่ต้องตั้งค่าใหม่ทุกครั้ง

---

## 🎯 Quick Start Commands

```bash
# 1. Configure AWS (first time only)
aws configure

# 2. Test Bedrock connection
aws bedrock list-foundation-models --region us-east-1 --by-provider anthropic

# 3. Test Claude Code
claude --version

# 4. Use Claude Code
claude
```

---

## 📚 Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [Main Bedrock Setup Guide](./BEDROCK_CLAUDE_CODE_SETUP.md)

---

*Last Updated: 2026-01-19*
*Containers: dev1-dev8.tuworkshop.vibecode.letsrover.ai*
*Region: us-east-1 (N. Virginia)*
