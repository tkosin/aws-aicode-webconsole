#!/bin/bash
set -e

echo "======================================"
echo "AWS CDK Code-Server Deployment"
echo "======================================"
echo ""

# Check if running in project directory
if [ ! -f "cdk.json" ]; then
    echo "Error: cdk.json not found. Please run this script from the cdk directory."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check AWS credentials
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "Error: AWS credentials not configured"
    echo "Please run: aws configure"
    exit 1
fi

echo "AWS Account: $(aws sts get-caller-identity --query Account --output text)"
echo "AWS Region: $(aws configure get region)"
echo ""

# Check if CDK is bootstrapped
echo "Checking CDK bootstrap status..."
REGION=$(aws configure get region)
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

if ! aws cloudformation describe-stacks --stack-name CDKToolkit --region $REGION > /dev/null 2>&1; then
    echo ""
    echo "⚠️  CDK is not bootstrapped in this region"
    echo "Run: cdk bootstrap aws://$ACCOUNT/$REGION"
    exit 1
fi

# Synthesize CloudFormation templates
echo "Synthesizing CDK stacks..."
cdk synth --quiet

# Show what will be deployed
echo ""
echo "The following stacks will be deployed:"
cdk list

echo ""
read -p "Do you want to proceed with deployment? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled"
    exit 0
fi

# Deploy all stacks
echo ""
echo "Deploying all stacks..."
cdk deploy --all --require-approval never

echo ""
echo "======================================"
echo "Deployment Complete!"
echo "======================================"
echo ""
echo "⚠️  Important Next Steps:"
echo ""
echo "1. Update Claude API Keys in AWS Secrets Manager:"
echo "   - Go to AWS Console → Secrets Manager"
echo "   - Update secrets: code-server-multi-dev/dev1/claude-api-key (and dev2-dev8)"
echo "   - Replace 'REPLACE_WITH_ACTUAL_KEY_AFTER_DEPLOYMENT' with actual keys"
echo ""
echo "2. Retrieve EC2 Instance IP:"
echo "   INSTANCE_ID=\$(aws cloudformation describe-stacks --stack-name code-server-multi-dev-compute --query 'Stacks[0].Outputs[?OutputKey==\`InstanceId\`].OutputValue' --output text)"
echo "   INSTANCE_IP=\$(aws ec2 describe-instances --instance-ids \$INSTANCE_ID --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)"
echo "   echo \"Instance IP: \$INSTANCE_IP\""
echo ""
echo "3. SSH to EC2 and setup Docker containers:"
echo "   ssh -i ~/.ssh/code-server-admin-key.pem ubuntu@\$INSTANCE_IP"
echo ""
echo "4. Wait for DNS propagation (5-10 minutes)"
echo ""
echo "5. Test developer URLs:"
for i in {1..8}; do
    echo "   https://dev${i}.dev.yourdomain.com"
done
echo ""
echo "6. Retrieve passwords from Secrets Manager:"
echo "   aws secretsmanager get-secret-value --secret-id code-server-multi-dev/dev1/password --query SecretString --output text"
echo ""
