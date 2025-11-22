#!/bin/bash
#
# Update EC2 deployment script
# Runs from local machine to update the deployed EC2 instance
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
echo -e "${GREEN}Updating Pipeline Backend on EC2${NC}"
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

# Execute deployment commands on EC2
ssh -i "$EC2_KEY" "$EC2_USER@$EC2_HOST" << 'ENDSSH'
set -e

echo "======================================"
echo "Updating Pipeline Backend"
echo "======================================"

# Navigate to repo
cd /opt/pipeline || { echo "Repository not found"; exit 1; }

# Pull latest changes
echo "Pulling latest changes from GitHub..."
sudo git fetch origin
sudo git reset --hard origin/master

# Navigate to backend
cd backend

# Install/update Python dependencies
echo "Installing Python dependencies..."
sudo -u ec2-user bash -c "
    source venv/bin/activate
    pip install --upgrade bcrypt psycopg2-binary greenlet asyncpg
"

# Run database migrations
echo "Running database migrations..."
sudo -u ec2-user bash -c "
    source venv/bin/activate
    alembic upgrade head
"

# Check if bun is installed (needed for Agent5 video rendering)
echo "Checking for Bun installation..."
if command -v bun &> /dev/null || [ -f "/home/ec2-user/.bun/bin/bun" ]; then
    echo "✓ Bun is installed"
    if [ -f "/home/ec2-user/.bun/bin/bun" ]; then
        /home/ec2-user/.bun/bin/bun --version
    else
        bun --version
    fi
else
    echo "⚠️  WARNING: Bun is not installed!"
    echo "   Agent5 video rendering will fail without Bun."
    echo "   Run: bash backend/install_bun_ec2.sh"
fi

# Restart the service
echo "Restarting pipeline-backend service..."
sudo systemctl restart pipeline-backend

# Wait a moment for service to start
sleep 3

# Check service status
echo ""
echo "Service status:"
sudo systemctl status pipeline-backend --no-pager -l

# Test the API
echo ""
echo "Testing API health endpoint..."
curl -s http://localhost:8000/health | python3 -m json.tool || echo "Health check failed"

echo ""
echo "Testing generate-images endpoint with header auth..."
curl -s -X POST http://localhost:8000/api/generate-images \
    -H "Content-Type: application/json" \
    -H "X-User-Email: test@example.com" \
    -d '{"prompt": "test deployment", "num_images": 1}' | python3 -m json.tool || echo "Generate-images test failed"

echo ""
echo "======================================"
echo "Deployment complete!"
echo "======================================"
ENDSSH

echo ""
echo -e "${GREEN}======================================"
echo -e "EC2 Update Complete!"
echo -e "======================================${NC}"
echo ""
echo "Test the deployed API:"
echo "  curl http://$EC2_HOST:8000/health"
echo ""
echo "View API docs:"
echo "  http://$EC2_HOST:8000/docs"
