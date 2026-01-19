# Claude API Usage Tracking Guide

วิธีการติดตามและวิเคราะห์การใช้งาน Claude API ของแต่ละ developer

## 📊 Overview

มี **3 วิธีหลัก** ในการ track การใช้งาน:

1. **Anthropic Console** - ง่ายที่สุด แต่ดูทีละ key
2. **Proxy Layer + CloudWatch** - แนะนำสำหรับ production
3. **CloudWatch Logs Insights** - Query จาก logs โดยตรง

---

## วิธีที่ 1: Anthropic Console (ใช้ API Key แยกกัน)

### Setup

แต่ละ developer ต้องมี API key ของตัวเอง (ทั้งหมด 8 keys)

```bash
# Update secrets with individual API keys
for i in {1..8}; do
  aws secretsmanager update-secret \
    --secret-id code-server-multi-dev/dev${i}/claude-api-key \
    --secret-string "sk-ant-api03-YOUR_KEY_FOR_DEV${i}" \
    --region ap-southeast-7
done
```

### ดูข้อมูลการใช้งาน

**ผ่าน Web Console:**
1. ไปที่ https://console.anthropic.com
2. Login ด้วย account ที่มี API keys
3. เข้า **"API Keys"** → เลือก key → ดู **"Usage"**

**ผ่าน API:**
```bash
# Get usage for specific developer
curl https://api.anthropic.com/v1/usage \
  -H "x-api-key: $DEV1_CLAUDE_KEY" \
  -H "anthropic-version: 2023-06-01"
```

**Response:**
```json
{
  "data": {
    "input_tokens": 1250000,
    "output_tokens": 450000,
    "requests": 1523,
    "total_cost_usd": 10.50
  },
  "period": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  }
}
```

### ข้อดี/ข้อเสีย

✅ **ข้อดี:**
- ไม่ต้อง setup อะไรเพิ่ม
- ข้อมูลแม่นยำจาก Anthropic
- ดูได้ทันที

❌ **ข้อเสีย:**
- ต้องดูทีละ developer
- ไม่มี dashboard รวม
- ไม่มี real-time alerting

---

## วิธีที่ 2: Proxy Layer + CloudWatch (แนะนำ!) ⭐

### Architecture

```
Code-Server (dev1-8) → Claude Proxy (localhost:8000) → Claude API
                              ↓
                    CloudWatch Logs + Metrics
                              ↓
                    Dashboard + Alerts
```

### Step 1: Deploy Proxy

```bash
# SSH to EC2
ssh -i ~/.ssh/code-server-admin-key.pem ubuntu@$INSTANCE_IP

# Install dependencies
sudo pip3 install flask requests boto3

# Copy proxy script
cd /home/ubuntu
# (Copy claude-proxy.py from cdk/scripts/)

# Load environment variables (API keys)
source .env

# Create systemd service
sudo tee /etc/systemd/system/claude-proxy.service <<EOF
[Unit]
Description=Claude API Proxy with Usage Tracking
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu
EnvironmentFile=/home/ubuntu/.env
ExecStart=/usr/bin/python3 /home/ubuntu/claude-proxy.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable claude-proxy
sudo systemctl start claude-proxy

# Check status
sudo systemctl status claude-proxy
```

### Step 2: Configure Code-Server to Use Proxy

**On each container, update Claude extension settings:**

```json
{
  "claude.apiEndpoint": "http://localhost:8000/v1",
  "claude.apiKey": "${CLAUDE_API_KEY}"
}
```

Or via environment variable:
```bash
export ANTHROPIC_BASE_URL="http://localhost:8000/v1"
```

### Step 3: Create CloudWatch Log Group

```bash
aws logs create-log-group \
  --log-group-name /aws/ec2/code-server-multi-dev/claude-api \
  --region ap-southeast-7

aws logs put-retention-policy \
  --log-group-name /aws/ec2/code-server-multi-dev/claude-api \
  --retention-in-days 90 \
  --region ap-southeast-7
```

### Step 4: Query Usage

```bash
# Make script executable
chmod +x cdk/scripts/query-usage.sh

# Query last 30 days (default)
bash cdk/scripts/query-usage.sh

# Query last 7 days
bash cdk/scripts/query-usage.sh 7

# Query yesterday only
bash cdk/scripts/query-usage.sh 1
```

**Output:**
```
=========================================
Claude API Usage Report
=========================================

Period: Last 30 days

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Developer    Input Tokens    Output Tokens   Total Tokens    Cost (USD)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
dev1           1,250,000         450,000       1,700,000    $10.50
dev2             850,000         320,000       1,170,000    $7.35
dev3           2,100,000         780,000       2,880,000    $17.70
dev4             420,000         150,000         570,000    $3.51
dev5             680,000         240,000         920,000    $5.64
dev6             950,000         380,000       1,330,000    $8.22
dev7             310,000         120,000         430,000    $2.67
dev8           1,450,000         520,000       1,970,000    $12.09
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL          8,010,000       2,960,000      10,970,000    $67.68
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Monthly Projection: $67.68

Top 3 Users:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
dev3         $17.70
dev8         $12.09
dev1         $10.50
```

### Step 5: Create CloudWatch Dashboard

```bash
# Create dashboard JSON
cat > /tmp/claude-dashboard.json <<'EOF'
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "CodeServer/ClaudeAPI", "TotalCost", { "stat": "Sum", "period": 86400 } ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "ap-southeast-7",
        "title": "Daily Claude API Cost",
        "period": 300
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "CodeServer/ClaudeAPI", "InputTokens", { "stat": "Sum" } ],
          [ ".", "OutputTokens", { "stat": "Sum" } ]
        ],
        "view": "timeSeries",
        "stacked": true,
        "region": "ap-southeast-7",
        "title": "Token Usage Over Time",
        "period": 300
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "CodeServer/ClaudeAPI", "TotalCost", { "stat": "Sum", "dimensions": {"Developer": "dev1"} } ],
          [ "...", { "dimensions": {"Developer": "dev2"} } ],
          [ "...", { "dimensions": {"Developer": "dev3"} } ],
          [ "...", { "dimensions": {"Developer": "dev4"} } ],
          [ "...", { "dimensions": {"Developer": "dev5"} } ],
          [ "...", { "dimensions": {"Developer": "dev6"} } ],
          [ "...", { "dimensions": {"Developer": "dev7"} } ],
          [ "...", { "dimensions": {"Developer": "dev8"} } ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "ap-southeast-7",
        "title": "Cost per Developer",
        "period": 86400
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "CodeServer/ClaudeAPI", "APICall", { "stat": "Sum" } ]
        ],
        "view": "singleValue",
        "region": "ap-southeast-7",
        "title": "Total API Calls (Today)",
        "period": 86400
      }
    }
  ]
}
EOF

# Create dashboard
aws cloudwatch put-dashboard \
  --dashboard-name CodeServerClaudeUsage \
  --dashboard-body file:///tmp/claude-dashboard.json \
  --region ap-southeast-7
```

**ดู Dashboard:**
```
AWS Console → CloudWatch → Dashboards → CodeServerClaudeUsage
```

### Step 6: Setup Alerts

```bash
# Alert when daily cost exceeds $10
aws cloudwatch put-metric-alarm \
  --alarm-name claude-daily-cost-high \
  --alarm-description "Alert when daily Claude API cost exceeds $10" \
  --metric-name TotalCost \
  --namespace CodeServer/ClaudeAPI \
  --statistic Sum \
  --period 86400 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --region ap-southeast-7

# Alert when single developer exceeds $5/day
for i in {1..8}; do
  aws cloudwatch put-metric-alarm \
    --alarm-name claude-dev${i}-cost-high \
    --alarm-description "Alert when dev${i} daily cost exceeds $5" \
    --metric-name TotalCost \
    --namespace CodeServer/ClaudeAPI \
    --dimensions Name=Developer,Value=dev${i} \
    --statistic Sum \
    --period 86400 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 1 \
    --region ap-southeast-7
done
```

---

## วิธีที่ 3: CloudWatch Logs Insights

**ถ้าคุณ log API calls ใน CloudWatch Logs**

### Query Examples

**Total usage per developer (last 7 days):**
```sql
fields developer, input_tokens, output_tokens, cost_usd
| filter status = "success"
| stats
    sum(input_tokens) as total_input,
    sum(output_tokens) as total_output,
    sum(cost_usd) as total_cost,
    count() as api_calls
  by developer
| sort total_cost desc
```

**Hourly usage pattern:**
```sql
fields @timestamp, developer, input_tokens, output_tokens
| filter status = "success"
| stats
    sum(input_tokens) as input,
    sum(output_tokens) as output
  by bin(1h), developer
```

**Model usage distribution:**
```sql
fields model, developer
| filter status = "success"
| stats count() as calls by model, developer
```

**Top 10 most expensive API calls:**
```sql
fields @timestamp, developer, model, cost_usd, input_tokens, output_tokens
| filter status = "success"
| sort cost_usd desc
| limit 10
```

**Run queries:**
```
AWS Console → CloudWatch → Logs Insights
→ Select log group: /aws/ec2/code-server-multi-dev/claude-api
→ Paste query → Run
```

---

## 📈 สร้าง Monthly Report

### Script สำหรับ generate report

```bash
#!/bin/bash
# generate-monthly-report.sh

MONTH=$(date -d "last month" +%Y-%m)
OUTPUT_FILE="claude-usage-report-${MONTH}.txt"

echo "Generating Claude API Usage Report for $MONTH"
echo "================================================" > $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

# Get usage for each developer
for i in {1..8}; do
    DEVELOPER="dev$i"

    # Query CloudWatch Metrics
    COST=$(aws cloudwatch get-metric-statistics \
        --namespace CodeServer/ClaudeAPI \
        --metric-name TotalCost \
        --dimensions Name=Developer,Value=$DEVELOPER \
        --start-time "${MONTH}-01T00:00:00Z" \
        --end-time "${MONTH}-31T23:59:59Z" \
        --period 2592000 \
        --statistics Sum \
        --region ap-southeast-7 \
        --query 'Datapoints[0].Sum' \
        --output text)

    echo "$DEVELOPER: \$$COST" >> $OUTPUT_FILE
done

echo "" >> $OUTPUT_FILE
echo "Report generated: $OUTPUT_FILE"
cat $OUTPUT_FILE
```

---

## 💰 Cost Calculation

### Token Pricing (2024)

| Model | Input Token | Output Token |
|-------|-------------|--------------|
| **Claude 3 Sonnet** | $3 / 1M | $15 / 1M |
| **Claude 3 Haiku** | $0.25 / 1M | $1.25 / 1M |
| **Claude 3 Opus** | $15 / 1M | $75 / 1M |

### Example Calculations

**Scenario 1: Moderate Usage (Sonnet)**
```
Input tokens:  500,000
Output tokens: 200,000
═══════════════════════════
Cost: (500k × $3/1M) + (200k × $15/1M)
    = $1.50 + $3.00
    = $4.50/month per developer
```

**Scenario 2: Heavy Usage (Sonnet)**
```
Input tokens:  2,000,000
Output tokens: 800,000
═══════════════════════════
Cost: (2M × $3/1M) + (800k × $15/1M)
    = $6.00 + $12.00
    = $18.00/month per developer
```

**Scenario 3: Mixed Usage (70% Haiku, 30% Sonnet)**
```
Haiku:
  Input:  1,400,000 × $0.25/1M = $0.35
  Output:   560,000 × $1.25/1M = $0.70

Sonnet:
  Input:    600,000 × $3/1M    = $1.80
  Output:   240,000 × $15/1M   = $3.60
═══════════════════════════
Total: $6.45/month per developer
```

---

## 🎯 Best Practices

### 1. Set Budget Limits

```bash
# Per developer per day
MAX_DAILY_COST=5.00

# Per developer per month
MAX_MONTHLY_COST=150.00

# Total project per month
MAX_PROJECT_MONTHLY=1000.00
```

### 2. Optimize Model Selection

**Use Claude 3 Haiku for:**
- Simple code completion
- Documentation generation
- Basic questions
- Code formatting

**Use Claude 3 Sonnet for:**
- Complex code generation
- Architecture discussions
- Debugging complex issues
- Code reviews

### 3. Monitor Patterns

**Look for:**
- ❌ Unusually high usage (possible loop/bug)
- ❌ After-hours usage (automation?)
- ❌ Very long responses (inefficient prompts)
- ✅ Steady, consistent usage
- ✅ Appropriate model selection

### 4. Educate Developers

**Share guidelines:**
- Be specific in prompts
- Use Haiku for simple tasks
- Don't repeatedly ask same question
- Review generated code (don't blindly accept)

---

## 🚨 Troubleshooting

### Proxy not logging to CloudWatch

```bash
# Check proxy status
sudo systemctl status claude-proxy

# Check logs
sudo journalctl -u claude-proxy -f

# Verify IAM permissions
aws sts get-caller-identity
```

### Metrics not showing in CloudWatch

```bash
# List available metrics
aws cloudwatch list-metrics \
  --namespace CodeServer/ClaudeAPI \
  --region ap-southeast-7

# Check if data is being sent
aws cloudwatch get-metric-statistics \
  --namespace CodeServer/ClaudeAPI \
  --metric-name APICall \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum \
  --region ap-southeast-7
```

### High unexpected costs

```bash
# Check which developer
bash cdk/scripts/query-usage.sh 1  # Last 24 hours

# Review recent API calls
aws logs filter-log-events \
  --log-group-name /aws/ec2/code-server-multi-dev/claude-api \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --region ap-southeast-7 \
  --query 'events[*].message' \
  --output text | jq '.developer, .cost_usd, .model'
```

---

## 📊 Summary

| Method | Setup Difficulty | Real-time | Cost | Best For |
|--------|-----------------|-----------|------|----------|
| **Anthropic Console** | Easy | No | Free | Quick checks |
| **Proxy + CloudWatch** | Medium | Yes | ~$5/mo | Production |
| **Logs Insights** | Easy | No | ~$1/mo | Analysis |

**แนะนำ:** ใช้ **Proxy + CloudWatch** สำหรับ production เพื่อ:
- ✅ Real-time monitoring
- ✅ Per-developer tracking
- ✅ Automated alerts
- ✅ Historical analysis
- ✅ Cost optimization

---

**ติดตั้ง proxy:** ดูที่ [`cdk/scripts/claude-proxy.py`](cdk/scripts/claude-proxy.py)
**Query usage:** ใช้ [`cdk/scripts/query-usage.sh`](cdk/scripts/query-usage.sh)
