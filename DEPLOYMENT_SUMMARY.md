# Deployment Summary - CNAME Approach (No Route53)

**Date**: 2025-01-19
**Domain**: `tuworkshop.vibecode.letsrover.ai`
**Deployment Method**: CDK with Manual CNAME Setup

---

## What Changed

The CDK deployment has been updated to **NOT use AWS Route53** for DNS management. Instead, you will manually create CNAME records at your external DNS provider.

### Files Modified

1. **[cdk/config/prod.py](cdk/config/prod.py)**
   - Removed `ROUTE53_HOSTED_ZONE_ID` requirement
   - Set `BASE_DOMAIN = "tuworkshop.vibecode.letsrover.ai"`
   - Added notes about manual CNAME setup

2. **[cdk/app.py](cdk/app.py)**
   - Replaced `DNSStack` with `CertificateStack`
   - Removed Route53 dependency

3. **[cdk/stacks/certificate_stack.py](cdk/stacks/certificate_stack.py)** (NEW)
   - Creates ACM certificate with **manual DNS validation**
   - Outputs validation records for you to add at DNS provider
   - Replaces the old Route53-based DNS stack

4. **[cdk/stacks/loadbalancer_stack.py](cdk/stacks/loadbalancer_stack.py)**
   - Updated documentation to mention CNAME setup
   - Added output for CNAME setup instructions

5. **[cdk/stacks/__init__.py](cdk/stacks/__init__.py)**
   - Replaced `DNSStack` import with `CertificateStack`

### Documentation Added

1. **[CNAME_SETUP.md](CNAME_SETUP.md)** (NEW)
   - Comprehensive guide for setting up CNAME records
   - Instructions for popular DNS providers (Cloudflare, GoDaddy, Namecheap, Google)
   - Troubleshooting common DNS issues
   - Verification steps

2. **[cdk/QUICKSTART.md](cdk/QUICKSTART.md)** (UPDATED)
   - Step 1: Simplified configuration (no Route53 zone ID needed)
   - Step 6: Complete DNS setup instructions with substeps
   - Updated checklist with DNS-related tasks
   - Enhanced troubleshooting section

---

## How It Works

### Old Approach (Route53)
```
CDK Deploy → Route53 creates DNS records automatically → Certificate validated automatically → Ready
```

### New Approach (CNAME)
```
CDK Deploy → You get ALB DNS name → You create CNAME at DNS provider → Certificate validates → Ready
```

---

## Deployment Steps

### 1. Deploy Infrastructure
```bash
cd cdk/
cdk deploy --all
```

This creates:
- Network (VPC, subnets, security groups)
- Security (IAM roles, secrets)
- Compute (EC2 instance)
- Certificate (ACM wildcard cert - **pending validation**)
- Load Balancer (ALB with HTTPS listener)
- Monitoring (CloudWatch, backups)

### 2. Get Required Information

After deployment completes, get the **ALB DNS name**:

```bash
aws cloudformation describe-stacks \
  --stack-name code-server-multi-dev-loadbalancer \
  --query 'Stacks[0].Outputs[?OutputKey==`ALBDNSName`].OutputValue' \
  --output text \
  --region ap-southeast-7
```

Example: `code-server-multi-dev-alb-1234567890.ap-southeast-7.elb.amazonaws.com`

### 3. Add Certificate Validation CNAME

Go to **AWS Certificate Manager Console** (Singapore region):
- https://ap-southeast-1.console.aws.amazon.com/acm/

Find your certificate and copy the DNS validation CNAME record.

**Example**:
```
Name: _abc123def456.tuworkshop.vibecode.letsrover.ai
Type: CNAME
Value: _xyz789uvw012.acm-validations.aws.
```

Add this CNAME at your DNS provider. Wait 5-30 minutes for validation.

### 4. Add Developer Subdomain CNAMEs

Once certificate is validated, add these 8 CNAME records at your DNS provider:

```
dev1.tuworkshop.vibecode.letsrover.ai  →  [ALB DNS name]
dev2.tuworkshop.vibecode.letsrover.ai  →  [ALB DNS name]
dev3.tuworkshop.vibecode.letsrover.ai  →  [ALB DNS name]
dev4.tuworkshop.vibecode.letsrover.ai  →  [ALB DNS name]
dev5.tuworkshop.vibecode.letsrover.ai  →  [ALB DNS name]
dev6.tuworkshop.vibecode.letsrover.ai  →  [ALB DNS name]
dev7.tuworkshop.vibecode.letsrover.ai  →  [ALB DNS name]
dev8.tuworkshop.vibecode.letsrover.ai  →  [ALB DNS name]
```

All CNAME values should point to the same ALB DNS name.

### 5. Verify DNS Propagation

```bash
dig dev1.tuworkshop.vibecode.letsrover.ai CNAME
```

Should return the ALB DNS name.

### 6. Access Your Environments

Once DNS propagates (5-60 minutes):

- https://dev1.tuworkshop.vibecode.letsrover.ai
- https://dev2.tuworkshop.vibecode.letsrover.ai
- ... (dev3-dev8)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ External DNS Provider (Cloudflare / GoDaddy / etc.)             │
│                                                                  │
│ CNAME Records (Manual Setup):                                   │
│ - dev1.tuworkshop.vibecode.letsrover.ai → ALB DNS               │
│ - dev2.tuworkshop.vibecode.letsrover.ai → ALB DNS               │
│ - ... (dev3-dev8)                                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ AWS - Bangkok Region (ap-southeast-7)                           │
│                                                                  │
│ ┌─────────────────────────────────────────┐                     │
│ │ Application Load Balancer               │                     │
│ │ - HTTPS (443) with ACM Certificate      │                     │
│ │ - Host-based routing (dev1-dev8)        │                     │
│ └─────────────────────────────────────────┘                     │
│                      ↓                                           │
│ ┌─────────────────────────────────────────┐                     │
│ │ EC2 Instance (t3.2xlarge)               │                     │
│ │ - 8 Docker containers (code-server)     │                     │
│ │ - Ports 8443-8450                       │                     │
│ │ - IAM role with Bedrock permissions     │                     │
│ └─────────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ AWS Bedrock - Singapore Region (ap-southeast-1)                 │
│                                                                  │
│ - Claude 3 Haiku, Sonnet, 3.5 Sonnet, Sonnet 4.5              │
│ - IAM authentication (no API keys)                             │
│ - CloudWatch logging                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Benefits of CNAME Approach

### ✅ Advantages
1. **No Route53 required** - Use any DNS provider
2. **Lower cost** - No Route53 hosted zone fees (~$0.50/month per zone)
3. **Flexibility** - Keep domain at existing provider
4. **Simple architecture** - One less AWS service to manage

### ⚠️ Considerations
1. **Manual setup required** - Must create CNAME records yourself
2. **DNS propagation time** - 5-60 minutes depending on provider
3. **Certificate validation** - Manual CNAME addition required
4. **No automation** - Changes to ALB DNS require manual CNAME updates

---

## Cost Comparison

### With Route53
- Infrastructure: $420-450/month
- Route53 Hosted Zone: $0.50/month
- Route53 Queries: ~$0.40/month (estimated)
- **Total**: ~$421-451/month + Bedrock usage

### Without Route53 (CNAME Approach)
- Infrastructure: $420-450/month
- External DNS Provider: $0-20/month (many are free)
- **Total**: ~$420-470/month + Bedrock usage

**Savings**: Minimal (~$1/month), but removes AWS dependency

---

## Troubleshooting

### Certificate Not Validating

**Symptom**: ACM certificate stuck on "Pending validation"

**Solution**:
1. Verify validation CNAME is correct:
   ```bash
   dig _abc123def456.tuworkshop.vibecode.letsrover.ai CNAME
   ```
2. Check DNS provider for typos in CNAME record
3. Wait longer (can take up to 30 minutes)

### Subdomain Not Resolving

**Symptom**: Browser shows "This site can't be reached"

**Solution**:
1. Verify CNAME record exists:
   ```bash
   dig dev1.tuworkshop.vibecode.letsrover.ai
   ```
2. Check CNAME points to correct ALB DNS name
3. Wait for DNS propagation (check https://dnschecker.org/)
4. Clear browser DNS cache

### SSL Certificate Error

**Symptom**: "Your connection is not private"

**Solution**:
1. Verify certificate is "Issued" in ACM console
2. Hard refresh browser (Ctrl+Shift+R)
3. Check certificate matches domain in browser

### Cloudflare Issues

**Symptom**: "Too many redirects" or SSL errors

**Solution**:
1. Disable "Proxied" (orange cloud) - use "DNS only" (gray cloud)
2. Set SSL/TLS mode to "Full (strict)"
3. Wait 5 minutes for changes to propagate

---

## Next Steps

1. **Deploy**: Run `cdk deploy --all` in [cdk/](cdk/) directory
2. **Setup DNS**: Follow instructions in [CNAME_SETUP.md](CNAME_SETUP.md)
3. **Configure Claude**: Follow [CLAUDE_CODE_BEDROCK_SETUP.md](CLAUDE_CODE_BEDROCK_SETUP.md)
4. **Monitor Usage**: Use [BEDROCK_USAGE_TRACKING.md](BEDROCK_USAGE_TRACKING.md)

---

## Documentation Index

| Document | Purpose |
|----------|---------|
| [QUICKSTART.md](cdk/QUICKSTART.md) | 5-minute deployment guide |
| [CNAME_SETUP.md](CNAME_SETUP.md) | Detailed DNS setup instructions |
| [CLAUDE_CODE_BEDROCK_SETUP.md](CLAUDE_CODE_BEDROCK_SETUP.md) | Configure Claude Code extension |
| [BEDROCK_USAGE_TRACKING.md](BEDROCK_USAGE_TRACKING.md) | Track AI usage and costs |
| [PRESS_RELEASE.md](PRESS_RELEASE.md) | Product overview (English) |
| [PRESS_RELEASE_TH.md](PRESS_RELEASE_TH.md) | Product overview (Thai) |

---

## Support

If you encounter issues:

1. Check [CNAME_SETUP.md](CNAME_SETUP.md) troubleshooting section
2. Verify all checklist items in [QUICKSTART.md](cdk/QUICKSTART.md)
3. Check AWS Certificate Manager console for certificate status
4. Test DNS with `dig` command
5. Review CloudWatch Logs for ALB and EC2 errors

---

**Ready to deploy?**

```bash
cd cdk/
cdk deploy --all
```

Then follow [CNAME_SETUP.md](CNAME_SETUP.md) for DNS configuration.
