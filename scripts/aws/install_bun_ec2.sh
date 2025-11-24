#!/bin/bash
#
# Install Bun on EC2 instance
# Runs from local machine to install Bun on the deployed EC2 instance
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# EC2 Configuration - IP retrieved dynamically from AWS
INSTANCE_ID="i-051a27d0f69e98ca2"
REGION="us-east-2"
EC2_USER="ec2-user"
EC2_KEY="${HOME}/Downloads/pipeline_orchestrator.pem"

# Try to get current IP from AWS (requires AWS CLI configured)
EC2_HOST=""
if command -v aws &> /dev/null; then
    # Try different profiles
    for profile in default1 default2 default; do
        EC2_HOST=$(aws ec2 describe-instances \
            --instance-ids "$INSTANCE_ID" \
            --profile "$profile" \
            --region "$REGION" \
            --query 'Reservations[0].Instances[0].PublicIpAddress' \
            --output text 2>/dev/null)
        # Trim whitespace and check if valid IP
        EC2_HOST=$(echo "$EC2_HOST" | tr -d '[:space:]')
        if [ -n "$EC2_HOST" ] && [ "$EC2_HOST" != "None" ] && [ "$EC2_HOST" != "null" ]; then
            echo -e "${GREEN}Retrieved EC2 IP from AWS (profile: $profile): $EC2_HOST${NC}"
            break
        fi
    done
fi

# Fallback: prompt for IP if AWS CLI failed
if [ -z "$EC2_HOST" ] || [ "$EC2_HOST" = "None" ] || [ "$EC2_HOST" = "null" ]; then
    echo -e "${YELLOW}Could not retrieve IP from AWS. Please enter the current EC2 IP address:${NC}"
    read -p "EC2 IP: " EC2_HOST
    # Trim user input
    EC2_HOST=$(echo "$EC2_HOST" | tr -d '[:space:]')
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Installing Bun on EC2${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if SSH key exists
if [ ! -f "$EC2_KEY" ]; then
    echo -e "${YELLOW}SSH key not found at: $EC2_KEY${NC}"
    echo -e "${YELLOW}Looking for alternative keys...${NC}"

    # Try to find any .pem file
    if [ -f "${HOME}/.ssh/id_rsa" ]; then
        EC2_KEY="${HOME}/.ssh/id_rsa"
        echo -e "${GREEN}Using: $EC2_KEY${NC}"
    else
        echo -e "${RED}No SSH key found. Please specify the path to your EC2 key:${NC}"
        read -p "Key path: " EC2_KEY
        if [ ! -f "$EC2_KEY" ]; then
            echo -e "${RED}Key not found: $EC2_KEY${NC}"
            exit 1
        fi
    fi
fi

echo -e "${GREEN}Connecting to EC2 instance: $EC2_USER@$EC2_HOST${NC}"

# Execute installation commands on EC2
ssh -i "$EC2_KEY" "$EC2_USER@$EC2_HOST" << 'ENDSSH'
set -e

echo "======================================"
echo "Installing Bun"
echo "======================================"

# Check if bun is already installed
if command -v bun &> /dev/null; then
    echo "Bun is already installed:"
    bun --version
    echo ""
    echo "Updating to latest version..."
    curl -fsSL https://bun.sh/install | bash
else
    echo "Installing Bun..."
    curl -fsSL https://bun.sh/install | bash
fi

# Source bashrc to make bun available in current session
source ~/.bashrc

# Verify installation
echo ""
echo "Verifying Bun installation..."
~/.bun/bin/bun --version

# Navigate to Remotion project and install dependencies
echo ""
echo "======================================"
echo "Installing Remotion dependencies"
echo "======================================"

cd /opt/pipeline/remotion || { echo "Remotion directory not found"; exit 1; }

# Install dependencies with bun
echo "Installing Remotion packages..."
~/.bun/bin/bun install

echo ""
echo "======================================"
echo "Making Bun available system-wide"
echo "======================================"

# Create symlinks so systemd services can find bun
sudo ln -sf /home/ec2-user/.bun/bin/bun /usr/local/bin/bun
sudo ln -sf /home/ec2-user/.bun/bin/bunx /usr/local/bin/bunx

echo "Created symlinks:"
ls -l /usr/local/bin/bun /usr/local/bin/bunx

echo ""
echo "======================================"
echo "Installation complete!"
echo "======================================"
echo ""
echo "Bun version:"
bun --version
echo ""
echo "Bun location:"
which bun

ENDSSH

echo ""
echo -e "${GREEN}======================================"
echo -e "Bun Installation Complete!"
echo -e "======================================${NC}"
echo ""
echo "You can now run Agent5 video generation."

