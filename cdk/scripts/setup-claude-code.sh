#!/bin/bash
# Setup Claude Code extension with Bedrock configuration for all developers
# This script should be run on the EC2 instance with sudo

set -e

echo "=== Setting up Claude Code Extension with AWS Bedrock ==="

# Check if running on EC2 instance
if [ ! -d "/mnt/ebs-data" ]; then
    echo "Error: /mnt/ebs-data not found. This script should run on the EC2 instance."
    exit 1
fi

# Create settings for all 8 developers
for i in {1..8}; do
  echo "Creating settings for dev${i}..."

  # Create User settings directory
  mkdir -p "/mnt/ebs-data/dev${i}/config/User"

  # Create settings.json with proper JSON format
  cat > "/mnt/ebs-data/dev${i}/config/User/settings.json" <<'EOF'
{
  "workbench.colorTheme": "Default Dark+",
  "workbench.startupEditor": "none"
}
EOF

  # Create workspace config directory for Claude Code
  mkdir -p "/mnt/ebs-data/dev${i}/workspace/.anthropic"

  # Create Claude Code config
  cat > "/mnt/ebs-data/dev${i}/workspace/.anthropic/config.json" <<'EOF'
{
  "provider": "bedrock",
  "region": "ap-southeast-1",
  "model": "global.anthropic.claude-sonnet-4-5-20250929-v1:0"
}
EOF

curl -fsSL https://claude.ai/install.sh | bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Restart all containers: cd /home/ubuntu/scripts && docker-compose restart"
echo "2. Wait 30 seconds for containers to fully start"
echo "3. Access code-server at https://dev1.tuworkshop.vibecode.letsrover.ai"
echo "4. Click 'Vertex or Bedrock' when Claude Code asks for login"
echo ""
echo "To verify Bedrock environment variables:"
echo "  docker exec code-server-dev1 env | grep -E '(BEDROCK|AWS_REGION)'"
