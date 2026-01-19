# CNAME Setup Guide for External DNS Providers

This guide explains how to configure your domain with CNAME records when NOT using AWS Route53 for DNS management.

## Overview

This deployment creates an Application Load Balancer (ALB) in AWS but does NOT automatically create DNS records. You must manually create CNAME records at your DNS provider (Cloudflare, GoDaddy, Namecheap, etc.) to point your domain to the ALB.

**Domain**: `tuworkshop.vibecode.letsrover.ai`

## Prerequisites

1. Completed CDK deployment (`cdk deploy --all`)
2. Access to your DNS provider's control panel
3. ALB DNS name from CDK outputs

## Step 1: Get ALB DNS Name

After deploying with `cdk deploy --all`, look for the output:

```
Outputs:
code-server-multi-dev-loadbalancer.ALBDNSName = code-server-multi-dev-alb-1234567890.ap-southeast-7.elb.amazonaws.com
code-server-multi-dev-loadbalancer.CNAMESetupInstructions = Create CNAME records...
```

**Copy the ALB DNS name** (e.g., `code-server-multi-dev-alb-1234567890.ap-southeast-7.elb.amazonaws.com`)

## Step 2: Get Certificate Validation Records

After deployment, go to AWS Console:

1. Navigate to **AWS Certificate Manager (ACM)** in Singapore region (ap-southeast-1)
2. Find your certificate for `*.tuworkshop.vibecode.letsrover.ai`
3. Click on the certificate
4. Under **Domains**, you'll see DNS validation records like:

```
Name: _abc123def456.tuworkshop.vibecode.letsrover.ai
Type: CNAME
Value: _xyz789uvw012.acm-validations.aws.
```

**Copy these validation records** - you'll need to add them to your DNS provider.

## Step 3: Create DNS Records at Your Provider

### A. Create Certificate Validation CNAME (First!)

At your DNS provider, create the validation CNAME record:

| Type  | Name                                        | Value/Target                                    | TTL  |
|-------|---------------------------------------------|-------------------------------------------------|------|
| CNAME | `_abc123def456.tuworkshop.vibecode.letsrover.ai` | `_xyz789uvw012.acm-validations.aws.` | 3600 |

**Important**:
- Use the EXACT values from AWS Certificate Manager
- Some DNS providers auto-append the domain, so you might only need to enter `_abc123def456`
- Wait 5-10 minutes for DNS propagation and certificate validation

### B. Create CNAME Records for Developers

Once the certificate is validated, create CNAME records for each developer:

| Type  | Name                                       | Value/Target                                             | TTL  |
|-------|--------------------------------------------|----------------------------------------------------------|------|
| CNAME | `dev1.tuworkshop.vibecode.letsrover.ai`   | `code-server-multi-dev-alb-xxx.ap-southeast-7.elb.amazonaws.com` | 3600 |
| CNAME | `dev2.tuworkshop.vibecode.letsrover.ai`   | `code-server-multi-dev-alb-xxx.ap-southeast-7.elb.amazonaws.com` | 3600 |
| CNAME | `dev3.tuworkshop.vibecode.letsrover.ai`   | `code-server-multi-dev-alb-xxx.ap-southeast-7.elb.amazonaws.com` | 3600 |
| CNAME | `dev4.tuworkshop.vibecode.letsrover.ai`   | `code-server-multi-dev-alb-xxx.ap-southeast-7.elb.amazonaws.com` | 3600 |
| CNAME | `dev5.tuworkshop.vibecode.letsrover.ai`   | `code-server-multi-dev-alb-xxx.ap-southeast-7.elb.amazonaws.com` | 3600 |
| CNAME | `dev6.tuworkshop.vibecode.letsrover.ai`   | `code-server-multi-dev-alb-xxx.ap-southeast-7.elb.amazonaws.com` | 3600 |
| CNAME | `dev7.tuworkshop.vibecode.letsrover.ai`   | `code-server-multi-dev-alb-xxx.ap-southeast-7.elb.amazonaws.com` | 3600 |
| CNAME | `dev8.tuworkshop.vibecode.letsrover.ai`   | `code-server-multi-dev-alb-xxx.ap-southeast-7.elb.amazonaws.com` | 3600 |

**Replace** `code-server-multi-dev-alb-xxx.ap-southeast-7.elb.amazonaws.com` with your actual ALB DNS name.

**Note**: Some DNS providers (like Cloudflare) may auto-append the base domain, so you might only need to enter:
- Name: `dev1` (instead of `dev1.tuworkshop.vibecode.letsrover.ai`)

## Step 4: Verify DNS Propagation

### Check Certificate Validation

```bash
# Check if validation CNAME is propagating
dig _abc123def456.tuworkshop.vibecode.letsrover.ai CNAME

# Should return the validation target
```

In AWS Console (Certificate Manager), the certificate status should change from "Pending validation" to "Issued" within 5-30 minutes.

### Check Developer Subdomains

```bash
# Check if CNAME records are working
dig dev1.tuworkshop.vibecode.letsrover.ai CNAME

# Should return the ALB DNS name
```

Or use online tools:
- https://dnschecker.org/
- https://mxtoolbox.com/DNSLookup.aspx

## Step 5: Test Access

Once DNS has propagated (can take 5-60 minutes):

1. Open browser to: https://dev1.tuworkshop.vibecode.letsrover.ai
2. You should see code-server login page
3. Enter password from AWS Secrets Manager
4. Repeat for dev2-dev8

## Common DNS Provider Instructions

### Cloudflare

1. Log in to Cloudflare Dashboard
2. Select your domain: `letsrover.ai` or the appropriate parent domain
3. Go to **DNS** → **Records**
4. Click **Add record**
5. Fill in:
   - **Type**: CNAME
   - **Name**: `_abc123def456.tuworkshop.vibecode` (validation) or `dev1.tuworkshop.vibecode` (subdomain)
   - **Target**: ALB DNS name
   - **Proxy status**: DNS only (gray cloud) - ⚠️ NOT proxied!
   - **TTL**: Auto or 3600
6. Click **Save**

**Important for Cloudflare**: Disable "Proxy" (orange cloud) - must be "DNS only" (gray cloud) for ALB to work properly.

### GoDaddy

1. Log in to GoDaddy Domain Manager
2. Find your domain and click **DNS**
3. Under **Records**, click **Add**
4. Fill in:
   - **Type**: CNAME
   - **Name**: `_abc123def456.tuworkshop.vibecode` or `dev1.tuworkshop.vibecode`
   - **Value**: ALB DNS name
   - **TTL**: 3600 seconds (1 hour)
5. Click **Save**

### Namecheap

1. Log in to Namecheap Account
2. Go to **Domain List** → Click **Manage** on your domain
3. Go to **Advanced DNS** tab
4. Click **Add New Record**
5. Fill in:
   - **Type**: CNAME Record
   - **Host**: `_abc123def456.tuworkshop.vibecode` or `dev1.tuworkshop.vibecode`
   - **Value**: ALB DNS name
   - **TTL**: Automatic
6. Click **Save All Changes**

### Google Domains / Google Cloud DNS

1. Log in to Google Domains or Cloud DNS
2. Select your domain
3. Go to **DNS** settings
4. Click **Manage custom records**
5. Add CNAME record:
   - **Host name**: `_abc123def456.tuworkshop.vibecode` or `dev1.tuworkshop.vibecode`
   - **Type**: CNAME
   - **TTL**: 3600
   - **Data**: ALB DNS name
6. Click **Save**

## Troubleshooting

### Certificate Stuck on "Pending Validation"

**Problem**: ACM certificate not validating

**Solutions**:
1. Verify validation CNAME record is correct:
   ```bash
   dig _abc123def456.tuworkshop.vibecode.letsrover.ai CNAME
   ```
2. Check you didn't accidentally create an A record instead of CNAME
3. Wait longer - DNS propagation can take up to 48 hours (usually 5-30 minutes)
4. Check your DNS provider's status page for outages

### "This site can't be reached" Error

**Problem**: Browser can't resolve subdomain

**Solutions**:
1. Check CNAME record exists:
   ```bash
   dig dev1.tuworkshop.vibecode.letsrover.ai
   ```
2. Verify CNAME points to correct ALB DNS name
3. Clear your browser DNS cache:
   - Chrome: `chrome://net-internals/#dns` → Clear host cache
   - Firefox: Restart browser
   - Safari: Restart browser
4. Flush your system DNS cache:
   ```bash
   # macOS
   sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder

   # Windows
   ipconfig /flushdns

   # Linux
   sudo systemd-resolve --flush-caches
   ```

### SSL Certificate Error

**Problem**: "Your connection is not private" or "NET::ERR_CERT_AUTHORITY_INVALID"

**Solutions**:
1. Wait for certificate validation to complete in ACM (check AWS Console)
2. Verify certificate domain matches (wildcard `*.tuworkshop.vibecode.letsrover.ai`)
3. Hard refresh browser: Ctrl+Shift+R (Cmd+Shift+R on Mac)
4. Check certificate in browser:
   - Click the padlock icon → Certificate
   - Should be issued by Amazon and valid for `*.tuworkshop.vibecode.letsrover.ai`

### Cloudflare "Too Many Redirects" Error

**Problem**: Infinite redirect loop

**Solution**: In Cloudflare, set SSL/TLS encryption mode to **Full (strict)** or **Full**:
1. Cloudflare Dashboard → SSL/TLS
2. Change mode from "Flexible" to "Full (strict)"
3. Wait a few minutes

### CNAME Already Exists Error

**Problem**: DNS provider says "CNAME record already exists for this hostname"

**Solutions**:
1. Check if there's an existing A record for the same subdomain - delete it
2. Some providers don't allow CNAME and A records for the same hostname
3. Look for existing CNAME with same name - edit it instead of creating new one

### DNS Propagation Taking Too Long

**Problem**: CNAME records not propagating after 1+ hour

**Solutions**:
1. Check DNS provider's propagation status tools
2. Lower TTL values (but this won't help existing cached records)
3. Use different DNS server for testing:
   ```bash
   # Query Google's DNS directly
   dig @8.8.8.8 dev1.tuworkshop.vibecode.letsrover.ai

   # Query Cloudflare's DNS
   dig @1.1.1.1 dev1.tuworkshop.vibecode.letsrover.ai
   ```
4. Check global DNS propagation: https://www.whatsmydns.net/

## Security Best Practices

### 1. Enable DNSSEC

If your DNS provider supports DNSSEC, enable it for additional security:
- Protects against DNS spoofing and cache poisoning
- Most providers: Domain settings → DNSSEC → Enable

### 2. Set Appropriate TTL Values

- **Initial setup**: Use low TTL (300-600 seconds) for easy corrections
- **After stable**: Increase to 3600 seconds (1 hour) or more

### 3. Use DNS Provider's Security Features

Many DNS providers offer additional security:
- Cloudflare: DNSSEC, DDoS protection (but disable proxy for ALB!)
- Google Cloud DNS: DNSSEC
- Route53: DNSSEC, Shield for DDoS protection

### 4. Restrict DNS Zone Access

- Limit who can modify DNS records
- Use 2FA on DNS provider account
- Enable audit logs if available

## Alternative: Using Path-Based Routing

If CNAME setup is too complex, you can modify the CDK to use path-based routing instead:

**Original (Host-based)**:
- https://dev1.tuworkshop.vibecode.letsrover.ai
- https://dev2.tuworkshop.vibecode.letsrover.ai

**Alternative (Path-based)**:
- https://tuworkshop.vibecode.letsrover.ai/dev1
- https://tuworkshop.vibecode.letsrover.ai/dev2

This requires:
1. Only ONE CNAME record (tuworkshop.vibecode.letsrover.ai)
2. Modifying loadbalancer_stack.py to use path-based routing
3. Different certificate (not wildcard)

Contact if you need help implementing path-based routing.

## Summary Checklist

After deployment:

- [ ] Get ALB DNS name from CDK outputs
- [ ] Get certificate validation CNAME from AWS Certificate Manager
- [ ] Create validation CNAME at DNS provider
- [ ] Wait for certificate to be validated (check ACM console)
- [ ] Create 8 CNAME records (dev1-dev8) pointing to ALB
- [ ] Verify DNS propagation with `dig` command
- [ ] Test access to https://dev1.tuworkshop.vibecode.letsrover.ai
- [ ] Verify SSL certificate is valid in browser
- [ ] Test all developer subdomains (dev1-dev8)
- [ ] Document ALB DNS name for future reference

## Getting Help

If you encounter issues:

1. Check AWS Certificate Manager console for certificate status
2. Verify DNS records with `dig` command
3. Test from different networks (mobile, different ISP)
4. Check CloudWatch Logs for ALB access logs
5. Verify security groups allow inbound HTTPS (443)

## Additional Resources

- [AWS Certificate Manager DNS Validation](https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html)
- [Application Load Balancer Host-based Routing](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-listeners.html#host-conditions)
- [CNAME Record Setup](https://en.wikipedia.org/wiki/CNAME_record)
- [DNS Propagation Checker](https://www.whatsmydns.net/)

---

**Last Updated**: 2025-01-19
**Domain**: tuworkshop.vibecode.letsrover.ai
**ALB Region**: Bangkok (ap-southeast-7)
**Certificate Region**: Singapore (ap-southeast-1)
