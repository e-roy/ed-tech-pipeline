#!/bin/bash
#
# Deploy backend code changes for API Gateway support
# Run this from your local machine (it will SSH into EC2)
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
echo -e "${GREEN}Deploying Backend Code for API Gateway${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if SSH key exists
if [ ! -f "$EC2_KEY" ]; then
    echo -e "${YELLOW}SSH key not found at: $EC2_KEY${NC}"
    echo -e "${YELLOW}Please update EC2_KEY in this script${NC}"
    exit 1
fi

echo -e "${GREEN}Connecting to EC2 instance: $EC2_USER@$EC2_HOST${NC}"

# Execute deployment commands on EC2
ssh -i "$EC2_KEY" "$EC2_USER@$EC2_HOST" << 'ENDSSH'
set -e

echo "======================================"
echo "Deploying Pipeline Backend"
echo "======================================"

# Navigate to repo
cd /opt/pipeline || { echo "Repository not found"; exit 1; }

# Pull latest changes
echo "Pulling latest changes from GitHub..."
sudo git fetch origin
sudo git reset --hard origin/master

# Navigate to backend
cd backend

# Update .env file with FRONTEND_URL
echo "Updating .env file..."
if [ -f .env ]; then
    # Check if FRONTEND_URL already exists
    if grep -q "^FRONTEND_URL=" .env; then
        sudo sed -i 's|^FRONTEND_URL=.*|FRONTEND_URL=https://pipeline-q3b1.vercel.app|' .env
        echo "Updated FRONTEND_URL in .env"
    else
        echo "FRONTEND_URL=https://pipeline-q3b1.vercel.app" | sudo tee -a .env
        echo "Added FRONTEND_URL to .env"
    fi
else
    echo "FRONTEND_URL=https://pipeline-q3b1.vercel.app" | sudo tee .env
    echo "Created .env file with FRONTEND_URL"
fi

# Install/update Python dependencies (if needed)
echo "Checking Python dependencies..."
sudo -u ec2-user bash -c "
    source venv/bin/activate
    pip install --upgrade fastapi uvicorn websockets
"

# Restart service
echo "Restarting pipeline-backend service..."
sudo systemctl restart pipeline-backend

# Wait a moment for service to start
sleep 3

# Check status
echo "Checking service status..."
sudo systemctl status pipeline-backend --no-pager

echo ""
echo "======================================"
echo "Deployment Complete!"
echo "======================================"
echo ""
echo "Service status:"
sudo systemctl is-active pipeline-backend && echo "✅ Service is running" || echo "❌ Service failed to start"
echo ""
echo "Recent logs:"
sudo journalctl -u pipeline-backend -n 20 --no-pager

ENDSSH

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Update Vercel environment variables"
echo "2. Test API Gateway endpoints"

