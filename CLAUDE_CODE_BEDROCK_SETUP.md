# Claude Code Extension Setup for AWS Bedrock

This guide explains how to configure the Claude Code extension in VS Code (code-server) to use **AWS Bedrock** instead of the Anthropic API.

## Overview

By default, Claude Code extension uses the Anthropic API with API keys. However, in this deployment:
- ✅ **AWS Bedrock** is used for Claude API access
- ✅ **IAM authentication** (no API keys needed)
- ✅ **Singapore region** (ap-southeast-1) for Bedrock
- ✅ EC2 instance has IAM role with Bedrock permissions

## Prerequisites

1. Access to your code-server instance (dev1-dev8.yourdomain.com)
2. Code-server password (from AWS Secrets Manager)
3. AWS Bedrock enabled in Singapore region (ap-southeast-1)
4. EC2 instance IAM role has Bedrock permissions (configured automatically)

## Installation Steps

### 1. Install Claude Code Extension

In your code-server browser interface:

1. Click **Extensions** icon in left sidebar (or press `Ctrl+Shift+X`)
2. Search for "**Claude Code**" or "**Anthropic**"
3. Click **Install** on the official Claude Code extension
4. Wait for installation to complete

### 2. Configure for AWS Bedrock

After installation, you need to configure it for Bedrock instead of Anthropic API.

#### Option A: Using Extension Settings (Recommended)

1. Open **Settings** (File → Preferences → Settings or `Ctrl+,`)
2. Search for "**Claude**"
3. Find "**Claude: API Endpoint**" setting
4. Change from default to Bedrock endpoint:
   ```
   https://bedrock-runtime.ap-southeast-1.amazonaws.com
   ```

5. Find "**Claude: Authentication**" or similar setting
6. Set to "**AWS IAM**" or "**AWS Bedrock**" (instead of API Key)

#### Option B: Using settings.json (Advanced)

1. Open Command Palette (`Ctrl+Shift+P`)
2. Type: "**Preferences: Open Settings (JSON)**"
3. Add these settings:

```json
{
  "claude.apiEndpoint": "https://bedrock-runtime.ap-southeast-1.amazonaws.com",
  "claude.authType": "aws",
  "claude.awsRegion": "ap-southeast-1",
  "claude.modelId": "anthropic.claude-3-sonnet-20240229-v1:0"
}
```

### 3. Verify AWS Credentials

The Claude Code extension will automatically use the EC2 instance IAM role for authentication.

To verify it's working:

```bash
# In code-server terminal
aws sts get-caller-identity
```

You should see the EC2 IAM role ARN:
```json
{
  "UserId": "AIDXXXXXXXXXXXXXXXXXX",
  "Account": "123456789012",
  "Arn": "arn:aws:iam::123456789012:role/code-server-multi-dev-ec2-role"
}
```

### 4. Test Bedrock Connection

Test if you can invoke Bedrock models:

```bash
# Test invoke Claude via Bedrock
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-sonnet-20240229-v1:0 \
  --body '{"messages":[{"role":"user","content":"Hello"}],"anthropic_version":"bedrock-2023-05-31","max_tokens":100}' \
  --region ap-southeast-1 \
  output.json

cat output.json
```

If successful, you'll see Claude's response.

## Available Claude Models

You can choose from these models in Bedrock (Singapore region):

| Model ID | Description | Cost (Input/Output per 1M tokens) |
|----------|-------------|-----------------------------------|
| `anthropic.claude-3-haiku-20240307-v1:0` | Fast, low-cost | $0.25 / $1.25 |
| `anthropic.claude-3-sonnet-20240229-v1:0` | Balanced (recommended) | $3.00 / $15.00 |
| `anthropic.claude-3-5-sonnet-20240620-v1:0` | Most capable Sonnet | $3.00 / $15.00 |
| `anthropic.claude-3-opus-20240229-v1:0` | Most capable, expensive | $15.00 / $75.00 |
| `global.anthropic.claude-sonnet-4-5-20250929-v1:0` | Latest Sonnet 4.5 (Cross-Region) | $3.00 / $15.00 |

### Changing Models

To switch models in Claude Code extension:

1. Open Settings
2. Search for "**Claude: Model ID**"
3. Change to desired model ID from table above
4. Restart extension or reload window

## Troubleshooting

### Error: "Authentication failed"

**Cause:** Extension can't access AWS credentials or IAM role doesn't have Bedrock permissions.

**Solutions:**
1. Verify IAM role is attached to EC2:
   ```bash
   aws sts get-caller-identity
   ```

2. Check IAM role has Bedrock permissions:
   ```bash
   aws iam get-role-policy \
     --role-name code-server-multi-dev-ec2-role \
     --policy-name BedrockAccess
   ```

3. Restart code-server container:
   ```bash
   docker restart code-server-dev1
   ```

### Error: "Model not found" or "Access denied"

**Cause:** Bedrock model access not enabled in your AWS account.

**Solution:**
1. Go to AWS Bedrock Console: https://ap-southeast-1.console.aws.amazon.com/bedrock/
2. Navigate to **Model access**
3. Click **Manage model access**
4. Enable access for Claude models:
   - ✅ Claude 3 Haiku
   - ✅ Claude 3 Sonnet
   - ✅ Claude 3.5 Sonnet
   - ✅ Claude 3 Opus (optional)
   - ✅ Claude Sonnet 4.5 (latest)
5. Click **Save changes**
6. Wait 2-5 minutes for access to be granted

### Error: "Region not supported"

**Cause:** Trying to use Bedrock in Bangkok (ap-southeast-7) - not supported.

**Solution:**
- Bedrock must use Singapore region: `ap-southeast-1`
- Update settings to use correct region
- Verify endpoint: `https://bedrock-runtime.ap-southeast-1.amazonaws.com`

### Extension not finding AWS credentials

**Cause:** Code-server running outside Docker container or IAM role not propagated.

**Solution:**

1. Check if code-server is running in Docker:
   ```bash
   docker ps | grep code-server
   ```

2. Verify container has AWS credentials:
   ```bash
   docker exec code-server-dev1 aws sts get-caller-identity
   ```

3. If not working, manually mount AWS credentials:
   ```bash
   # On EC2 host
   docker exec -it code-server-dev1 bash

   # Inside container
   curl http://169.254.169.254/latest/meta-data/iam/security-credentials/code-server-multi-dev-ec2-role
   ```

### High latency or slow responses

**Cause:** Cross-region network latency (Bangkok → Singapore).

**Solutions:**
1. Accept ~20-50ms additional latency (Bangkok → Singapore is close)
2. Use faster models (Claude 3 Haiku) for quick tasks
3. For lowest latency, consider deploying EC2 in Singapore too

## Advanced Configuration

### Custom AWS Credentials (Not Recommended)

If you need to use different AWS credentials (not IAM role):

```json
{
  "aws.profile": "my-profile",
  "aws.region": "ap-southeast-1"
}
```

Or set environment variables in docker-compose.yml:
```yaml
environment:
  - AWS_PROFILE=my-profile
  - AWS_REGION=ap-southeast-1
```

**Warning:** This overrides IAM role authentication and requires managing credentials manually.

### Using AWS CLI Credentials

If Claude Code extension doesn't automatically detect IAM role:

```bash
# Configure AWS CLI to use IMDSv2
export AWS_EC2_METADATA_SERVICE_ENDPOINT=http://169.254.169.254
export AWS_EC2_METADATA_SERVICE_ENDPOINT_MODE=IPv4
```

### Debugging Connection Issues

Enable debug logging in Claude Code extension:

1. Open Output panel (`Ctrl+Shift+U`)
2. Select "**Claude Code**" from dropdown
3. Look for connection errors or authentication issues

Or check CloudWatch Logs:
```bash
# On EC2 host
aws logs tail /aws/bedrock/code-server-multi-dev --follow
```

## Usage Tips

### 1. Choose the Right Model

- **Quick questions/simple tasks:** Claude 3 Haiku ($0.25/1M input tokens)
- **General development:** Claude 3 Sonnet ($3/1M input tokens) ✅ Recommended
- **Complex reasoning/large codebases:** Claude Sonnet 4.5 ($3/1M input tokens)
- **Maximum capability (expensive):** Claude 3 Opus ($15/1M input tokens)

### 2. Monitor Your Usage

Check your Bedrock usage:
```bash
# See recent Bedrock invocations
aws logs tail /aws/bedrock/code-server-multi-dev --since 1h
```

See [BEDROCK_USAGE_TRACKING.md](BEDROCK_USAGE_TRACKING.md) for detailed tracking.

### 3. Optimize Costs

- Use Claude 3 Haiku for simple tasks
- Keep context focused (fewer tokens = lower cost)
- Avoid uploading very large files unless necessary
- Monitor monthly spending via AWS Budgets

## Security Best Practices

### 1. IAM Role Permissions

The EC2 IAM role should only have minimal Bedrock permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:ap-southeast-1::foundation-model/*"
    }
  ]
}
```

### 2. Enable Logging

Ensure all Bedrock invocations are logged:
- ✅ Model invocation logs enabled
- ✅ CloudWatch Logs retention: 30 days
- ✅ CloudTrail for audit trail

### 3. Cost Controls

Set up budget alerts:
```bash
# Alert when Bedrock costs exceed $100/month
aws budgets create-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget '{
    "BudgetName": "BedrockMonthly",
    "BudgetLimit": {"Amount": "100", "Unit": "USD"},
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST",
    "CostFilters": {"Service": ["Amazon Bedrock"]}
  }'
```

## Summary Checklist

- [ ] Claude Code extension installed in code-server
- [ ] API endpoint set to: `https://bedrock-runtime.ap-southeast-1.amazonaws.com`
- [ ] Authentication type set to AWS IAM
- [ ] AWS region set to: `ap-southeast-1`
- [ ] Model ID configured (default: Claude 3 Sonnet)
- [ ] AWS credentials verified (`aws sts get-caller-identity`)
- [ ] Bedrock model access enabled in AWS console
- [ ] Test invocation successful
- [ ] Usage tracking configured (CloudWatch Logs)
- [ ] Budget alerts set up

## Getting Help

If you encounter issues:

1. Check [BEDROCK_USAGE_TRACKING.md](BEDROCK_USAGE_TRACKING.md) for monitoring
2. Review CloudWatch Logs for errors
3. Verify IAM role permissions
4. Check Bedrock model access in AWS Console
5. Test direct Bedrock API call with AWS CLI

## Additional Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Claude Code Extension Documentation](https://claude.com/claude-code)
- [AWS IAM Roles for EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html)
- [Bedrock Model IDs](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html)

---

**Important Notes:**
- 🚨 Bangkok (ap-southeast-7) does NOT have Bedrock - must use Singapore (ap-southeast-1)
- ✅ No API keys needed - uses EC2 IAM role automatically
- 💰 Track usage via CloudWatch to monitor costs
- 🔒 All API calls are logged for audit and usage tracking
