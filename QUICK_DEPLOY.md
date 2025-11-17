# Quick EC2 Deployment Guide

## Status
- Files are being copied to EC2 via SCP
- Neon database is ready
- JWT secret generated: `a6ea64cbaff035ec0012c6bd418f228153fb517edaf2a4570c4880129d5c36a9`

## Simple 5-Step Deployment

### 1. SSH into EC2
```bash
ssh -i ~/Downloads/pipeline_orchestrator.pem ec2-user@13.58.115.166
```

### 2. Setup files
```bash
sudo mkdir -p /opt/pipeline
sudo mv /tmp/backend /opt/pipeline/
sudo chown -R ec2-user:ec2-user /opt/pipeline
cd /opt/pipeline/backend
```

### 3. Create .env file
```bash
cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql+psycopg://neondb_owner:npg_kZnmUstlWA26@ep-falling-meadow-adnv9yz9-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require

# JWT
JWT_SECRET_KEY=a6ea64cbaff035ec0012c6bd418f228153fb517edaf2a4570c4880129d5c36a9
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Replicate
REPLICATE_API_KEY="r8_CCVI54mxcBx1GgIGbAe4cttw4SRvAS13Hw8tT"

# AWS S3
AWS_ACCESS_KEY_ID=AKIA6ELKOKYDEGNFZQXH
AWS_SECRET_ACCESS_KEY=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
S3_BUCKET_NAME=pipeline-backend-assets
AWS_REGION=us-east-1

# Frontend
FRONTEND_URL=http://13.58.115.166:3000

# Server
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
EOF
```

### 4. Install dependencies
```bash
sudo yum install -y python3.11 python3.11-pip python3-devel gcc

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Run database migrations and start
```bash
# Run migrations
alembic upgrade head

# Start the backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Test It
Open in browser: `http://13.58.115.166:8000/docs`

## Keep it Running (Optional)
To keep it running after you disconnect:

```bash
# Install screen
sudo yum install -y screen

# Start in screen session
screen -S backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Detach: Press Ctrl+A then D
# Reattach later: screen -r backend
```

## Your API is now at:
- **Docs**: http://13.58.115.166:8000/docs
- **Health**: http://13.58.115.166:8000/health
- **Base URL**: http://13.58.115.166:8000
