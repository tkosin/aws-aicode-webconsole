#!/bin/bash
set -e

echo "======================================"
echo "AWS CDK Code-Server Destroy"
echo "======================================"
echo ""
echo "⚠️  WARNING: This will destroy ALL infrastructure!"
echo ""
echo "This includes:"
echo "  - EC2 Instance and all data in memory"
echo "  - EBS Volume (a snapshot will be created)"
echo "  - Application Load Balancer"
echo "  - Security Groups"
echo "  - CloudWatch Logs (will be deleted)"
echo "  - Secrets Manager secrets"
echo "  - Route53 DNS records"
echo "  - ACM Certificate"
echo ""
echo "⚠️  Developer workspaces on EBS will be backed up via snapshot"
echo "    but will not be automatically accessible after destruction."
echo ""
read -p "Are you absolutely sure? Type 'destroy' to confirm: " CONFIRM

if [ "$CONFIRM" != "destroy" ]; then
    echo "Destruction cancelled"
    exit 0
fi

# Activate virtual environment if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo ""
echo "Destroying all stacks..."
echo ""

# Destroy in reverse order
cdk destroy --all --force

echo ""
echo "======================================"
echo "Infrastructure Destroyed"
echo "======================================"
echo ""
echo "Cleanup complete. The following resources were removed:"
echo "  ✓ Monitoring stack"
echo "  ✓ Load Balancer stack"
echo "  ✓ DNS stack"
echo "  ✓ Compute stack (EBS snapshot created)"
echo "  ✓ Security stack"
echo "  ✓ Network stack"
echo ""
echo "Note: EBS snapshots are retained and can be used to restore data."
echo "To delete snapshots manually:"
echo "  aws ec2 describe-snapshots --owner-ids self --query 'Snapshots[?Tags[?Key==\`Project\`]].SnapshotId' --output text"
echo ""
