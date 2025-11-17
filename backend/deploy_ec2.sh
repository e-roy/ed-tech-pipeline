#!/bin/bash
#
# EC2 Deployment Script for Pipeline Backend
# Run this script on your EC2 instance after cloning the repository
#
# Usage: ./deploy_ec2.sh [--skip-deps] [--skip-db]
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REPO_DIR="/opt/pipeline"
APP_DIR="/opt/pipeline/backend"
APP_USER="ubuntu"
SERVICE_NAME="pipeline-backend"
NGINX_CONFIG="/etc/nginx/sites-available/pipeline-backend"

# Parse arguments
SKIP_DEPS=false
SKIP_DB=false

for arg in "$@"
do
    case $arg in
        --skip-deps)
        SKIP_DEPS=true
        shift
        ;;
        --skip-db)
        SKIP_DB=true
        shift
        ;;
    esac
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Pipeline Backend EC2 Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if running as root or sudo
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run with sudo${NC}"
   exit 1
fi

# Step 1: Install system dependencies
if [ "$SKIP_DEPS" = false ]; then
    echo -e "\n${YELLOW}[1/7] Installing system dependencies...${NC}"
    apt-get update
    apt-get install -y \
        python3.11 \
        python3.11-venv \
        python3-pip \
        ffmpeg \
        postgresql-client \
        nginx \
        certbot \
        python3-certbot-nginx \
        git \
        curl
    echo -e "${GREEN}✓ System dependencies installed${NC}"
else
    echo -e "\n${YELLOW}[1/7] Skipping system dependencies...${NC}"
fi

# Step 2: Create application directory (if not exists)
echo -e "\n${YELLOW}[2/7] Setting up application directory...${NC}"
if [ ! -d "$APP_DIR" ]; then
    mkdir -p "$APP_DIR"
    chown $APP_USER:$APP_USER "$APP_DIR"
fi
echo -e "${GREEN}✓ Application directory ready at $APP_DIR${NC}"

# Step 3: Set up Python virtual environment
echo -e "\n${YELLOW}[3/7] Setting up Python virtual environment...${NC}"
cd "$APP_DIR"
if [ ! -d "venv" ]; then
    sudo -u $APP_USER python3.11 -m venv venv
fi
sudo -u $APP_USER bash -c "source venv/bin/activate && pip install --upgrade pip"
sudo -u $APP_USER bash -c "source venv/bin/activate && pip install -r requirements.txt"
echo -e "${GREEN}✓ Python virtual environment configured${NC}"

# Step 4: Set up environment variables
echo -e "\n${YELLOW}[4/7] Checking environment variables...${NC}"
if [ ! -f "$APP_DIR/.env" ]; then
    echo -e "${RED}ERROR: .env file not found!${NC}"
    echo -e "${YELLOW}Please create $APP_DIR/.env with the following variables:${NC}"
    cat <<EOF

# Database
DATABASE_URL=postgresql://neondb_owner:npg_kZnmUstlWA26@ep-falling-meadow-adnv9yz9-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require

# JWT
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Replicate
REPLICATE_API_KEY=r8_...

# AWS S3
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET_NAME=pipeline-backend-assets
AWS_REGION=us-east-1

# Frontend (Vercel URL)
FRONTEND_URL=https://your-app.vercel.app

# Server
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

EOF
    exit 1
fi
echo -e "${GREEN}✓ Environment variables found${NC}"

# Step 5: Run database migrations
if [ "$SKIP_DB" = false ]; then
    echo -e "\n${YELLOW}[5/7] Running database migrations...${NC}"
    sudo -u $APP_USER bash -c "cd $APP_DIR && source venv/bin/activate && alembic upgrade head"
    echo -e "${GREEN}✓ Database migrations complete${NC}"
else
    echo -e "\n${YELLOW}[5/7] Skipping database migrations...${NC}"
fi

# Step 6: Set up systemd service
echo -e "\n${YELLOW}[6/7] Configuring systemd service...${NC}"

cat > /etc/systemd/system/$SERVICE_NAME.service <<EOF
[Unit]
Description=Pipeline Backend FastAPI Application
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=pipeline-backend

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl restart $SERVICE_NAME

echo -e "${GREEN}✓ Systemd service configured and started${NC}"
sleep 2

# Check service status
if systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${GREEN}✓ Service is running${NC}"
else
    echo -e "${RED}✗ Service failed to start. Check logs with: journalctl -u $SERVICE_NAME -n 50${NC}"
fi

# Step 7: Configure Nginx reverse proxy
echo -e "\n${YELLOW}[7/7] Configuring Nginx...${NC}"

# Create Nginx config if it doesn't exist
if [ ! -f "$NGINX_CONFIG" ]; then
    cat > $NGINX_CONFIG <<'EOF'
# Pipeline Backend Nginx Configuration
# Update server_name with your domain

upstream pipeline_backend {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name api.yourdomain.com;  # UPDATE THIS!

    client_max_body_size 100M;

    # WebSocket support
    location / {
        proxy_pass http://pipeline_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket headers
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

    # Enable site
    ln -sf $NGINX_CONFIG /etc/nginx/sites-enabled/pipeline-backend

    # Test Nginx configuration
    nginx -t

    # Reload Nginx
    systemctl reload nginx

    echo -e "${GREEN}✓ Nginx configured${NC}"
    echo -e "${YELLOW}  → Remember to update server_name in $NGINX_CONFIG${NC}"
    echo -e "${YELLOW}  → Run certbot to enable HTTPS: sudo certbot --nginx -d api.yourdomain.com${NC}"
else
    echo -e "${YELLOW}  → Nginx config already exists at $NGINX_CONFIG${NC}"
fi

# Deployment summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${YELLOW}Service Status:${NC}"
systemctl status $SERVICE_NAME --no-pager -l

echo -e "\n${YELLOW}Useful Commands:${NC}"
echo -e "  View logs:        journalctl -u $SERVICE_NAME -f"
echo -e "  Restart service:  sudo systemctl restart $SERVICE_NAME"
echo -e "  Check status:     sudo systemctl status $SERVICE_NAME"
echo -e "  Edit env vars:    sudo nano $APP_DIR/.env"
echo -e "  View Nginx logs:  sudo tail -f /var/log/nginx/error.log"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo -e "  1. Update Nginx server_name: sudo nano $NGINX_CONFIG"
echo -e "  2. Point your domain DNS A record to this EC2's Elastic IP"
echo -e "  3. Enable HTTPS: sudo certbot --nginx -d api.yourdomain.com"
echo -e "  4. Test API: curl http://localhost:8000/health"
echo -e "  5. Update Vercel frontend env var: NEXT_PUBLIC_API_URL=https://api.yourdomain.com"

echo -e "\n${GREEN}Done!${NC}\n"
