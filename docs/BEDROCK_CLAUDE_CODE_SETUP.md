# Using Claude Code with Amazon Bedrock

## Overview

Claude Code can use Amazon Bedrock instead of the direct Anthropic API. This guide shows you how to configure and use Claude Code with Bedrock.

**Benefits:**
- ✅ Use AWS billing and cost controls
- ✅ Centralized AWS credential management
- ✅ Lower latency from us-east-1
- ✅ Integration with AWS services

**Current Setup:**
- **Region:** us-east-1 (N. Virginia)
- **AWS Account:** 715346683168
- **User:** theerayooth.k

---

## Prerequisites

1. ✅ AWS credentials configured (`aws configure`)
2. ✅ Bedrock model access enabled in us-east-1
3. ✅ Claude Code CLI installed

---

## Configuration

### Automatic Setup (Already Done!)

The configuration has been automatically added to your `~/.zshrc` file:

```bash
# This runs automatically when you open a new terminal
source ~/.claude-code-bedrock-config.sh
```

### Manual Setup (if needed)

If you need to set it up manually:

```bash
# Set environment variables
export ANTHROPIC_BEDROCK=true
export AWS_REGION=us-east-1

# Optional: Specify model
export ANTHROPIC_MODEL=anthropic.claude-opus-4-5-20251101-v1:0
```

---

## Available Models

These models are available in us-east-1:

| Model | Model ID | Use Case |
|-------|----------|----------|
| **Claude Opus 4.5** | `global.anthropic.claude-opus-4-5-20251101-v1:0` | Most capable, complex tasks (Cross-Region) |
| **Claude Sonnet 4.5** | `global.anthropic.claude-sonnet-4-5-20250929-v1:0` | Balanced performance/cost (Cross-Region) |
| **Claude Haiku 4.5** | `global.anthropic.claude-haiku-4-5-20251001-v1:0` | Fastest, most cost-effective (Cross-Region) |
| **Claude Sonnet 4** | `anthropic.claude-sonnet-4-20250514-v1:0` | Fast, efficient (Regional) |
| **Claude 3.5 Haiku** | `anthropic.claude-3-5-haiku-20241022-v1:0` | Previous generation |
| **Claude 3 Haiku** | `anthropic.claude-3-haiku-20240307-v1:0` | Legacy model |

---

## Usage

### Method 1: Default Usage

Simply use Claude Code normally. It will automatically use Bedrock:

```bash
# Open a new terminal (config auto-loads)
claude-code

# Or manually load config in current terminal
source ~/.claude-code-bedrock-config.sh
claude-code
```

### Method 2: With Specific Model

Use helper scripts to select a specific model:

#### Use Claude Opus 4.5 (Most Powerful)
```bash
source ~/use-claude-bedrock.sh
claude-code
```

#### Use Claude Sonnet 4.5 (Balanced)
```bash
source ~/use-claude-sonnet-bedrock.sh
claude-code
```

#### Use Custom Model
```bash
export ANTHROPIC_BEDROCK=true
export AWS_REGION=us-east-1
export ANTHROPIC_MODEL=anthropic.claude-haiku-4-5-20251001-v1:0
claude-code
```

---

## Usage in Code-Server Environments

To use Bedrock in your code-server containers (dev1-dev8):

### Option 1: Add to Container Environment

Add to each container's `.bashrc` or `.zshrc`:

```bash
# SSH to EC2
ssh -i ~/.ssh/code-server-admin-key.pem ubuntu@43.210.15.73

# For each dev environment
for i in {1..8}; do
  docker exec -it code-server-dev$i bash -c '
    echo "export ANTHROPIC_BEDROCK=true" >> ~/.bashrc
    echo "export AWS_REGION=us-east-1" >> ~/.bashrc
  '
done
```

### Option 2: Mount AWS Credentials

Add AWS credentials volume to docker-compose.yml:

```yaml
volumes:
  - /home/ubuntu/.aws:/home/coder/.aws:ro
```

---

## Verification

### Check Configuration

```bash
# Verify environment variables
echo "ANTHROPIC_BEDROCK: $ANTHROPIC_BEDROCK"
echo "AWS_REGION: $AWS_REGION"
echo "ANTHROPIC_MODEL: $ANTHROPIC_MODEL"
```

### Test Bedrock Connection

```bash
# Test Bedrock API directly
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-haiku-20240307-v1:0 \
  --region us-east-1 \
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":100,"messages":[{"role":"user","content":"Say hello"}]}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/response.json

cat /tmp/response.json | jq -r '.content[0].text'
```

### Check Available Models

```bash
aws bedrock list-foundation-models \
  --region us-east-1 \
  --by-provider anthropic \
  --query 'modelSummaries[?modelLifecycle.status==`ACTIVE`].{ModelId:modelId,Name:modelName}' \
  --output table
```

---

## Cost Comparison

### Bedrock Pricing (us-east-1)

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Claude Opus 4.5 | $15.00 | $75.00 |
| Claude Sonnet 4.5 | $3.00 | $15.00 |
| Claude Haiku 4.5 | $0.80 | $4.00 |
| Claude 3.5 Haiku | $0.80 | $4.00 |

**Note:** Prices may vary. Check [AWS Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/) for latest rates.

---

## Troubleshooting

### Issue: "Model not accessible"

**Solution:**
```bash
# Check model access
aws bedrock get-foundation-model \
  --model-identifier anthropic.claude-opus-4-5-20251101-v1:0 \
  --region us-east-1
```

If you get an error, request model access in AWS Console:
1. Go to AWS Bedrock Console (us-east-1)
2. Click "Model access" in sidebar
3. Request access for required models

### Issue: AWS credentials not found

**Solution:**
```bash
# Configure AWS credentials
aws configure

# Or set credentials explicitly
export AWS_ACCESS_KEY_ID=your_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

### Issue: Wrong region

**Solution:**
```bash
# Verify region
echo $AWS_REGION

# Set to us-east-1
export AWS_REGION=us-east-1
```

### Issue: Claude Code still using Anthropic API

**Solution:**
```bash
# Make sure Bedrock is enabled
export ANTHROPIC_BEDROCK=true

# Verify the variable is set
env | grep ANTHROPIC_BEDROCK

# Restart Claude Code
```

---

## Switching Back to Anthropic API

To switch back to using Anthropic API directly:

```bash
# Unset Bedrock variables
unset ANTHROPIC_BEDROCK
unset AWS_REGION

# Set Anthropic API key
export ANTHROPIC_API_KEY=your_api_key

# Use Claude Code normally
claude-code
```

Or comment out the Bedrock config in `~/.zshrc`:

```bash
# # Amazon Bedrock for Claude Code
# source ~/.claude-code-bedrock-config.sh
```

---

## Quick Reference

### Helper Scripts Location

- `~/.claude-code-bedrock-config.sh` - Main Bedrock configuration
- `~/use-claude-bedrock.sh` - Use Opus 4.5
- `~/use-claude-sonnet-bedrock.sh` - Use Sonnet 4.5

### Essential Commands

```bash
# Load Bedrock config
source ~/.claude-code-bedrock-config.sh

# Check current setup
env | grep -E "ANTHROPIC|AWS"

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1 --by-provider anthropic

# Use Claude Code
claude-code
```

---

## Best Practices

1. **Use appropriate model for task:**
   - Development/Testing: Haiku 4.5 (fast & cheap)
   - Code generation: Sonnet 4.5 (balanced)
   - Complex tasks: Opus 4.5 (most capable)

2. **Monitor costs:**
   ```bash
   # Check current month's Bedrock costs
   aws ce get-cost-and-usage \
     --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
     --granularity MONTHLY \
     --metrics "BlendedCost" \
     --filter '{"Dimensions":{"Key":"SERVICE","Values":["Amazon Bedrock"]}}' \
     --region us-east-1
   ```

3. **Use AWS Cost Allocation Tags:**
   Add tags to track usage by project/environment

4. **Set AWS Budget Alerts:**
   Create budget alerts in AWS Console to monitor spending

---

## Additional Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [Anthropic API Reference](https://docs.anthropic.com/api)
- [AWS CLI Configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)

---

*Last Updated: 2026-01-19*
*Region: us-east-1 (N. Virginia)*
*Account: 715346683168*
