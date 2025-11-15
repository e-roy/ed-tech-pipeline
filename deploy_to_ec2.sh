#!/bin/bash
# Local script to deploy backend to EC2
# Run from your local machine: ./deploy_to_ec2.sh

set -e

# Configuration
EC2_IP="13.58.115.166"
EC2_USER="ec2-user"
SSH_KEY="$HOME/Downloads/pipeline_orchestrator.pem"
REPO_URL="https://github.com/Gauntlet-Pipeline/pipeline.git"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Pipeline Backend EC2 Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Step 1: Clone repository
echo -e "\n${YELLOW}[1/5] Cloning repository to EC2...${NC}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no $EC2_USER@$EC2_IP << 'ENDSSH'
sudo mkdir -p /opt
cd /opt
if [ -d "pipeline" ]; then
    echo "Repository exists, pulling latest..."
    cd pipeline
    sudo git pull
else
    echo "Cloning repository..."
    sudo git clone https://github.com/Gauntlet-Pipeline/pipeline.git
fi
sudo chown -R ec2-user:ec2-user /opt/pipeline
ENDSSH

echo -e "${GREEN}✓ Repository cloned${NC}"

# Step 2: Upload .env file
echo -e "\n${YELLOW}[2/5] Creating .env file...${NC}"

# Generate JWT secret
JWT_SECRET=$(openssl rand -hex 32)

# Create .env content
ssh -i "$SSH_KEY" $EC2_USER@$EC2_IP << EOF
cat > /opt/pipeline/backend/.env << 'ENVFILE'
# Database Configuration
# TODO: Replace with your Neon PostgreSQL connection string
DATABASE_URL=postgresql+psycopg://REPLACE_WITH_NEON_URL

# JWT Authentication
JWT_SECRET_KEY=$JWT_SECRET
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Replicate API
REPLICATE_API_KEY="r8_CCVI54mxcBx1GgIGbAe4cttw4SRvAS13Hw8tT"

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=AKIA6ELKOKYDEGNFZQXH
AWS_SECRET_ACCESS_KEY=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
S3_BUCKET_NAME=pipeline-backend-assets
AWS_REGION=us-east-1

# Frontend URL
FRONTEND_URL=http://13.58.115.166:3000

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
ENVFILE
EOF

echo -e "${GREEN}✓ .env file created${NC}"
echo -e "${YELLOW}⚠️  WARNING: You need to update DATABASE_URL with your Neon PostgreSQL connection string${NC}"

# Step 3: Make deployment script executable
echo -e "\n${YELLOW}[3/5] Preparing deployment script...${NC}"
ssh -i "$SSH_KEY" $EC2_USER@$EC2_IP << 'ENDSSH'
chmod +x /opt/pipeline/backend/deploy_ec2.sh
ENDSSH

echo -e "${GREEN}✓ Deployment script ready${NC}"

# Step 4: Run deployment script
echo -e "\n${YELLOW}[4/5] Running deployment script on EC2...${NC}"
echo -e "${YELLOW}This will take several minutes (installing dependencies, setting up Python, etc.)${NC}"

ssh -i "$SSH_KEY" -t $EC2_USER@$EC2_IP << 'ENDSSH'
cd /opt/pipeline/backend
sudo ./deploy_ec2.sh --skip-db
ENDSSH

# Step 5: Verify deployment
echo -e "\n${YELLOW}[5/5] Verifying deployment...${NC}"
sleep 5

# Test health endpoint
if curl -s http://$EC2_IP:8000/health | grep -q "healthy"; then
    echo -e "${GREEN}✓ Backend is running successfully!${NC}"
    echo -e "${GREEN}✓ API accessible at: http://$EC2_IP:8000${NC}"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
    echo -e "${YELLOW}Check logs with: ssh -i $SSH_KEY $EC2_USER@$EC2_IP 'sudo journalctl -u pipeline-backend -n 50'${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo -e "1. Update DATABASE_URL in /opt/pipeline/backend/.env with your Neon connection string"
echo -e "2. Restart service: ssh -i $SSH_KEY $EC2_USER@$EC2_IP 'sudo systemctl restart pipeline-backend'"
echo -e "3. Run database migrations: ssh -i $SSH_KEY $EC2_USER@$EC2_IP 'cd /opt/pipeline/backend && source venv/bin/activate && alembic upgrade head'"
echo -e "4. Test API: curl http://$EC2_IP:8000/health"
echo -e "\n${YELLOW}API URL: http://$EC2_IP:8000${NC}"
echo -e "${YELLOW}Docs URL: http://$EC2_IP:8000/docs${NC}"
