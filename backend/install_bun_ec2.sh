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

EC2_HOST="13.58.115.166"
EC2_USER="ec2-user"
EC2_KEY="${HOME}/Downloads/pipeline_orchestrator.pem"

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
echo "Installation complete!"
echo "======================================"
echo ""
echo "Bun version:"
~/.bun/bin/bun --version
echo ""
echo "Bun location:"
which bun || echo "Bun location: ~/.bun/bin/bun"

ENDSSH

echo ""
echo -e "${GREEN}======================================"
echo -e "Bun Installation Complete!"
echo -e "======================================${NC}"
echo ""
echo "You can now run Agent5 video generation."

