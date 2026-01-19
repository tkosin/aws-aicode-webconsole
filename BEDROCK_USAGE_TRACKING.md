# AWS Bedrock Usage Tracking Guide

This guide explains how to track individual developer Claude API usage when using **AWS Bedrock** (not Anthropic API directly).

## Overview

With AWS Bedrock, Claude API calls are authenticated via IAM roles (no API keys needed). Usage tracking is done through:
1. **AWS Bedrock Model Invocation Logs** - CloudWatch Logs
2. **CloudWatch Metrics** - Custom metrics from log data
3. **CloudWatch Insights** - Query and analyze usage patterns

## Architecture

```
Developer → Code-Server → Claude Code Extension → AWS Bedrock (Singapore)
                                                        ↓
                                                   CloudWatch Logs
                                                        ↓
                                                   Usage Analytics
```

## Setup Bedrock Logging

### 1. Enable Model Invocation Logging

Bedrock can log all model invocations to CloudWatch. This is configured automatically in the CDK deployment.

```python
# In CDK (already configured)
bedrock_log_group = logs.LogGroup(
    self,
    "BedrockLogGroup",
    log_group_name="/aws/bedrock/code-server-multi-dev",
    retention=logs.RetentionDays.ONE_MONTH,
    removal_policy=RemovalPolicy.DESTROY
)
```

### 2. Enable Logging in Bedrock Console

You need to manually enable model invocation logging in the Bedrock console:

1. Go to AWS Bedrock Console (Singapore region: ap-southeast-1)
2. Navigate to **Settings** → **Model invocation logging**
3. Click **Edit**
4. Enable **CloudWatch Logs**
5. Select log group: `/aws/bedrock/code-server-multi-dev`
6. Save settings

## Tracking Usage

### Method 1: CloudWatch Logs Insights

Query usage by developer using CloudWatch Logs Insights.

#### A. View All Invocations

```sql
fields @timestamp, modelId, inputTokenCount, outputTokenCount, @message
| filter @message like /InvokeModel/
| sort @timestamp desc
| limit 100
```

#### B. Track Usage by Developer (via IAM Principal)

```sql
fields @timestamp,
       identity.arn as developer,
       modelId,
       usage.inputTokens as input_tokens,
       usage.outputTokens as output_tokens,
       (usage.inputTokens + usage.outputTokens) as total_tokens
| filter @message like /InvokeModel/
| stats sum(input_tokens) as total_input,
        sum(output_tokens) as total_output,
        sum(total_tokens) as total_tokens,
        count(*) as api_calls
  by developer
| sort total_tokens desc
```

#### C. Calculate Costs

```sql
fields @timestamp,
       identity.arn as developer,
       modelId,
       usage.inputTokens as input_tokens,
       usage.outputTokens as output_tokens,
       # Claude 3 Sonnet pricing
       (usage.inputTokens * 0.000003) as input_cost,
       (usage.outputTokens * 0.000015) as output_cost
| filter @message like /InvokeModel/
| stats sum(input_tokens) as total_input_tokens,
        sum(output_tokens) as total_output_tokens,
        sum(input_cost) + sum(output_cost) as total_cost_usd
  by developer
| sort total_cost_usd desc
```

#### D. Usage by Model

```sql
fields modelId,
       usage.inputTokens as input_tokens,
       usage.outputTokens as output_tokens
| filter @message like /InvokeModel/
| stats sum(input_tokens) as total_input,
        sum(output_tokens) as total_output,
        count(*) as invocations
  by modelId
| sort invocations desc
```

### Method 2: AWS CLI Queries

#### Query Recent Bedrock Logs

```bash
#!/bin/bash
# Query Bedrock usage from CloudWatch Logs

REGION="ap-southeast-1"  # Bedrock region
LOG_GROUP="/aws/bedrock/code-server-multi-dev"
DAYS=7

START_TIME=$(date -u -d "$DAYS days ago" +%s)000
END_TIME=$(date -u +%s)000

# Query with CloudWatch Insights
QUERY_ID=$(aws logs start-query \
  --log-group-name "$LOG_GROUP" \
  --start-time $START_TIME \
  --end-time $END_TIME \
  --query-string 'fields @timestamp, identity.arn, modelId, usage.inputTokens, usage.outputTokens
| filter @message like /InvokeModel/
| stats sum(usage.inputTokens) as total_input, sum(usage.outputTokens) as total_output by identity.arn
| sort total_input + total_output desc' \
  --region $REGION \
  --query 'queryId' \
  --output text)

echo "Query ID: $QUERY_ID"
echo "Waiting for results..."
sleep 5

# Get results
aws logs get-query-results \
  --query-id $QUERY_ID \
  --region $REGION \
  --output table
```

### Method 3: Create Usage Dashboard

Create a CloudWatch Dashboard to visualize usage:

```bash
# Create dashboard JSON
cat > bedrock-dashboard.json <<EOF
{
  "widgets": [
    {
      "type": "log",
      "properties": {
        "query": "SOURCE '/aws/bedrock/code-server-multi-dev'\\n| fields @timestamp, identity.arn, usage.inputTokens, usage.outputTokens\\n| stats sum(usage.inputTokens + usage.outputTokens) by identity.arn",
        "region": "ap-southeast-1",
        "stacked": false,
        "title": "Token Usage by Developer",
        "view": "bar"
      }
    }
  ]
}
EOF

# Create dashboard
aws cloudwatch put-dashboard \
  --dashboard-name BedrockUsage \
  --dashboard-body file://bedrock-dashboard.json \
  --region ap-southeast-1
```

## Pricing Information

### Claude 3 Models (Bedrock Pricing)

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Claude 3 Haiku | $0.25 | $1.25 |
| Claude 3 Sonnet | $3.00 | $15.00 |
| Claude 3.5 Sonnet | $3.00 | $15.00 |
| Claude 3 Opus | $15.00 | $75.00 |
| Claude Sonnet 4.5 | $3.00 | $15.00 |

### Example Cost Calculation

```python
# Example: 10M input tokens, 2M output tokens on Claude 3 Sonnet
input_cost = 10_000_000 * (3.0 / 1_000_000)   # $30.00
output_cost = 2_000_000 * (15.0 / 1_000_000)  # $30.00
total_cost = input_cost + output_cost         # $60.00
```

## Setting Up Alerts

### Create Budget Alert

```bash
# Create monthly budget alert
aws budgets create-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

**budget.json:**
```json
{
  "BudgetName": "BedrockMonthlyBudget",
  "BudgetLimit": {
    "Amount": "500",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST",
  "CostFilters": {
    "Service": ["Amazon Bedrock"]
  }
}
```

### Create CloudWatch Alarm for High Usage

```bash
# Alert when daily tokens exceed threshold
aws cloudwatch put-metric-alarm \
  --alarm-name bedrock-high-usage \
  --alarm-description "Alert when Bedrock usage is high" \
  --metric-name InvocationCount \
  --namespace AWS/Bedrock \
  --statistic Sum \
  --period 86400 \
  --threshold 100000 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --region ap-southeast-1
```

## Best Practices

### 1. Tag IAM Users

Ensure each developer has a unique IAM identity so you can track usage:

```bash
# The EC2 IAM role is shared, but you can use CloudTrail to see which
# container (and thus developer) made the call if needed
```

### 2. Enable Detailed Logging

Enable all Bedrock logging options:
- Model invocation logs (CloudWatch Logs)
- CloudTrail for API calls
- VPC Flow Logs if using VPC endpoints

### 3. Regular Reporting

Create a weekly/monthly report:

```bash
#!/bin/bash
# Generate monthly usage report

MONTH=$(date +%Y-%m)
START_TIME=$(date -d "$MONTH-01" +%s)000
END_TIME=$(date +%s)000

aws logs start-query \
  --log-group-name /aws/bedrock/code-server-multi-dev \
  --start-time $START_TIME \
  --end-time $END_TIME \
  --query-string 'fields identity.arn, modelId, usage.inputTokens, usage.outputTokens
| stats sum(usage.inputTokens) as input, sum(usage.outputTokens) as output by identity.arn
| sort input + output desc' \
  --region ap-southeast-1
```

### 4. Cost Allocation Tags

Use tags to track costs by team/project:

```json
{
  "Tags": [
    {
      "Key": "Project",
      "Value": "code-server-multi-dev"
    },
    {
      "Key": "CostCenter",
      "Value": "Engineering"
    }
  ]
}
```

## Troubleshooting

### No Logs Appearing

1. Check Bedrock logging is enabled in console
2. Verify IAM role has permissions to write to CloudWatch
3. Check log group exists: `/aws/bedrock/code-server-multi-dev`
4. Verify developers are actually making Bedrock API calls

### Can't Identify Individual Developers

Since all containers share the same EC2 IAM role, you need to:
1. Use separate IAM roles per container (complex)
2. Use application-level logging in Claude Code extension
3. Parse container IDs from CloudWatch Logs

### High Costs

1. Check which models are being used (Opus is 5x more expensive than Sonnet)
2. Implement rate limiting per developer
3. Set up budget alerts
4. Review usage patterns for inefficiencies

## Automation Scripts

### Daily Usage Report Script

Save as `/usr/local/bin/bedrock-daily-report.sh`:

```bash
#!/bin/bash
set -e

REGION="ap-southeast-1"
LOG_GROUP="/aws/bedrock/code-server-multi-dev"
DAYS=1

echo "======================================"
echo "Bedrock Daily Usage Report"
echo "Date: $(date +%Y-%m-%d)"
echo "======================================"

START_TIME=$(date -u -d "$DAYS days ago" +%s)000
END_TIME=$(date -u +%s)000

QUERY_ID=$(aws logs start-query \
  --log-group-name "$LOG_GROUP" \
  --start-time $START_TIME \
  --end-time $END_TIME \
  --query-string 'fields identity.arn, modelId, usage.inputTokens, usage.outputTokens
| stats sum(usage.inputTokens) as input, sum(usage.outputTokens) as output, count(*) as calls by identity.arn
| sort input + output desc' \
  --region $REGION \
  --query 'queryId' \
  --output text)

sleep 5

aws logs get-query-results \
  --query-id $QUERY_ID \
  --region $REGION \
  --output table

echo ""
echo "To see detailed logs, visit:"
echo "https://ap-southeast-1.console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#logsV2:logs-insights"
```

### Make executable:
```bash
chmod +x /usr/local/bin/bedrock-daily-report.sh
```

## Additional Resources

- [AWS Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [CloudWatch Logs Insights Query Syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html)
- [AWS Bedrock Model IDs](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html)

## Summary

**Key Points:**
1. ✅ No API keys needed - uses IAM authentication
2. ✅ Bedrock must be in Singapore (ap-southeast-1) region
3. ✅ Enable model invocation logging in Bedrock console
4. ✅ Use CloudWatch Logs Insights for querying usage
5. ✅ Set up budget alerts to control costs
6. ⚠️ All containers share EC2 IAM role - harder to track per-developer
7. ⚠️ Cross-region data transfer costs (Bangkok EC2 → Singapore Bedrock)

**Monthly Cost Estimate:**
- Light usage (1M tokens/developer): ~$18/month per developer
- Medium usage (10M tokens/developer): ~$180/month per developer
- Heavy usage (50M tokens/developer): ~$900/month per developer

For 8 developers with medium usage: **~$1,440/month** (just for Claude API)
