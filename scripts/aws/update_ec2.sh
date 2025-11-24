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

# EC2 Configuration - IP retrieved dynamically from AWS
INSTANCE_ID="i-051a27d0f69e98ca2"
REGION="us-east-2"
EC2_USER="ec2-user"
EC2_KEY="${HOME}/Downloads/pipeline_orchestrator.pem"
ALB_URL="https://api.classclipscohort3.com"

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
echo "Test the deployed API (via ALB):"
echo "  curl $ALB_URL/health"
echo ""
echo "Test the deployed API (direct EC2):"
echo "  curl http://$EC2_HOST:8000/health"
echo ""
echo "View API docs (via ALB):"
echo "  $ALB_URL/docs"
echo ""
echo "View API docs (direct EC2):"
echo "  http://$EC2_HOST:8000/docs"
