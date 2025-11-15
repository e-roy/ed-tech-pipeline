# EC2 Deployment Guide - Pipeline Backend

This guide walks through deploying the Pipeline backend on AWS EC2 with the frontend deployed separately on Vercel.

## Architecture Overview

- **Frontend**: Deployed on Vercel (Next.js)
- **Backend**: Deployed on AWS EC2 (FastAPI)
- **Database**: Neon PostgreSQL (managed, cloud-hosted)
- **Storage**: AWS S3 for generated images/videos
- **Reverse Proxy**: Nginx with Let's Encrypt SSL
- **Process Manager**: systemd

## Prerequisites

### 1. AWS Account Setup

- AWS account with EC2 access
- EC2 instance (recommended: `t3.medium` or larger)
- Ubuntu 22.04 LTS AMI
- Security group allowing:
  - Port 22 (SSH)
  - Port 80 (HTTP)
  - Port 443 (HTTPS)
- Elastic IP assigned to instance

### 2. Domain Setup

- Domain name (e.g., `yourdomain.com`)
- DNS A record: `api.yourdomain.com` → EC2 Elastic IP

### 3. Required Credentials

Gather these before deployment:

```bash
# Database (Neon PostgreSQL)
DATABASE_URL=postgresql+psycopg://user:password@host/dbname

# JWT Secret (generate with: openssl rand -hex 32)
JWT_SECRET_KEY=<64-character-hex-string>

# Replicate API (for AI models)
REPLICATE_API_KEY=r8_...

# AWS S3 (for asset storage)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET_NAME=pipeline-backend-assets
AWS_REGION=us-east-1

# Frontend URL (Vercel deployment)
FRONTEND_URL=https://your-app.vercel.app
```

## Deployment Steps

### Step 1: Launch EC2 Instance

1. Launch Ubuntu 22.04 LTS instance
2. Choose `t3.medium` (2 vCPU, 4 GB RAM) or larger
3. Configure security group (ports 22, 80, 443)
4. Allocate and assign Elastic IP
5. SSH into instance:

```bash
ssh -i your-key.pem ubuntu@<elastic-ip>
```

### Step 2: Clone Repository

```bash
# Clone the repo to /opt
sudo mkdir -p /opt
cd /opt
sudo git clone https://github.com/your-org/pipeline.git
sudo chown -R ubuntu:ubuntu pipeline
```

### Step 3: Configure Environment Variables

Create `.env` file in backend directory:

```bash
cd /opt/pipeline/backend
nano .env
```

Paste your configuration:

```bash
# Database
DATABASE_URL=postgresql+psycopg://neondb_owner:YOUR_PASSWORD@ep-name.us-east-1.aws.neon.tech/neondb?sslmode=require

# JWT
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Replicate
REPLICATE_API_KEY=r8_...

# AWS S3
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET_NAME=pipeline-backend-assets
AWS_REGION=us-east-1

# Frontend (Vercel URL)
FRONTEND_URL=https://your-app.vercel.app

# Server
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
```

Save with `Ctrl+O`, `Enter`, `Ctrl+X`.

### Step 4: Run Deployment Script

The deployment script automates:
- System dependencies installation
- Python virtual environment setup
- Database migrations
- systemd service configuration
- Nginx reverse proxy setup

```bash
cd /opt/pipeline/backend
sudo ./deploy_ec2.sh
```

**Optional flags:**
- `--skip-deps`: Skip system dependency installation (for updates)
- `--skip-db`: Skip database migrations

### Step 5: Update Nginx Domain

Edit Nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/pipeline-backend
```

Update line 13:
```nginx
server_name api.yourdomain.com;  # Change this!
```

Test and reload Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Step 6: Enable HTTPS with Let's Encrypt

```bash
sudo certbot --nginx -d api.yourdomain.com
```

Follow prompts:
- Enter email address
- Agree to Terms of Service
- Choose whether to redirect HTTP to HTTPS (recommended: Yes)

Certbot will:
- Obtain SSL certificate
- Configure Nginx for HTTPS
- Set up auto-renewal

### Step 7: Verify Deployment

Check service status:

```bash
sudo systemctl status pipeline-backend
```

Test API endpoint:

```bash
curl https://api.yourdomain.com/health
```

Expected response:
```json
{"status":"healthy"}
```

## Frontend Deployment (Vercel)

### Step 1: Connect Repository to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Import GitHub repository
3. Select `frontend` as root directory
4. Framework preset: Next.js

### Step 2: Configure Environment Variables

In Vercel project settings > Environment Variables:

```bash
# Backend API URL (your EC2 domain)
NEXT_PUBLIC_API_URL=https://api.yourdomain.com

# Authentication Secret
AUTH_SECRET=<generate-with-node-e-console-log-require-crypto-randomBytes-32-toString-base64>

# Google OAuth
AUTH_GOOGLE_ID=<from-google-cloud-console>
AUTH_GOOGLE_SECRET=<from-google-cloud-console>

# Database (same Neon instance, no +psycopg)
DATABASE_URL=postgresql://neondb_owner:YOUR_PASSWORD@ep-name.us-east-1.aws.neon.tech/neondb?sslmode=require

# Node Environment
NODE_ENV=production

# AWS S3 (same credentials as backend)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET_NAME=pipeline-backend-assets
AWS_REGION=us-east-1
```

### Step 3: Deploy

Vercel will automatically deploy on every push to `main` branch.

Manual deployment:
```bash
vercel --prod
```

## Management Commands

### View Logs

```bash
# Real-time logs
sudo journalctl -u pipeline-backend -f

# Last 100 lines
sudo journalctl -u pipeline-backend -n 100

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Restart Service

```bash
sudo systemctl restart pipeline-backend
```

### Update Deployment

```bash
cd /opt/pipeline
sudo git pull origin main
cd backend
sudo systemctl restart pipeline-backend
```

### Check Service Status

```bash
sudo systemctl status pipeline-backend
```

### Database Migrations

```bash
cd /opt/pipeline/backend
source venv/bin/activate
alembic upgrade head
```

## Troubleshooting

### Service won't start

```bash
# Check logs
sudo journalctl -u pipeline-backend -n 50

# Common issues:
# 1. Missing .env file → Create /opt/pipeline/backend/.env
# 2. Invalid DATABASE_URL → Check connection string
# 3. Missing dependencies → Run: sudo ./deploy_ec2.sh --skip-db
```

### Nginx 502 Bad Gateway

```bash
# Check if backend is running
sudo systemctl status pipeline-backend

# Check if port 8000 is listening
sudo lsof -i :8000

# Restart both services
sudo systemctl restart pipeline-backend
sudo systemctl reload nginx
```

### Database connection errors

```bash
# Test connection from EC2
psql "postgresql://..." -c "SELECT 1;"

# Check Neon dashboard for:
# - Connection pooling enabled
# - IP allowlist (if configured)
# - Database user permissions
```

### SSL certificate renewal

Certbot auto-renews certificates. Test renewal:

```bash
sudo certbot renew --dry-run
```

### High memory usage

```bash
# Check memory
free -h

# Reduce uvicorn workers in systemd service
sudo nano /etc/systemd/system/pipeline-backend.service
# Change --workers 4 to --workers 2

sudo systemctl daemon-reload
sudo systemctl restart pipeline-backend
```

## Cost Estimate

### Monthly Costs

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| EC2 t3.medium | 2 vCPU, 4 GB RAM | ~$30 |
| Elastic IP | (assigned to instance) | Free |
| Neon PostgreSQL | Free tier | $0 |
| AWS S3 | Pay per use | ~$5-20 |
| Vercel | Hobby plan | Free |
| **Total** | | **~$35-50** |

### API Usage Costs (Replicate)

- Llama 3.1 70B: ~$0.001 per prompt parse
- Flux-Schnell: ~$0.003 per image
- Gen-4-Turbo: ~$0.015 per second of video
- Veo 3.1: ~$0.20 per second of video

Example: "man buys hat" workflow
- 1× prompt parse: $0.001
- 4× images: $0.012
- 2× 8-second videos (gen-4-turbo): $0.24
- **Total: ~$0.25 per generation**

## Security Best Practices

1. **Firewall**: Only allow ports 22, 80, 443
2. **SSH**: Use key-based authentication, disable password auth
3. **Environment variables**: Never commit `.env` to git
4. **Database**: Use Neon's connection pooling, SSL mode required
5. **CORS**: Configure `FRONTEND_URL` correctly in backend `.env`
6. **Rate limiting**: Consider adding Nginx rate limits for production
7. **Monitoring**: Set up CloudWatch or similar for alerts

## Monitoring Setup (Optional)

### CloudWatch Logs

Install CloudWatch agent:

```bash
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb
```

Configure to send systemd logs to CloudWatch.

### Uptime Monitoring

Use services like:
- UptimeRobot (free tier)
- Pingdom
- AWS CloudWatch Synthetics

Monitor endpoint: `https://api.yourdomain.com/health`

## Backup Strategy

### Database Backups

Neon provides automatic backups. For additional safety:

```bash
# Manual backup
pg_dump "postgresql://..." > backup_$(date +%Y%m%d).sql

# Restore
psql "postgresql://..." < backup_20250115.sql
```

### S3 Backups

Enable S3 versioning:

```bash
aws s3api put-bucket-versioning \
  --bucket pipeline-backend-assets \
  --versioning-configuration Status=Enabled
```

## Scaling Considerations

### Vertical Scaling (Bigger Instance)

Upgrade to `t3.large` or `t3.xlarge` for more traffic:

```bash
# Stop instance, change instance type, restart
# Update uvicorn workers in systemd service
```

### Horizontal Scaling (Load Balancer)

For high traffic:
1. Create Application Load Balancer
2. Deploy multiple EC2 instances
3. Update Nginx config to use ALB
4. Use RDS instead of Neon for better connection pooling

## Support

- GitHub Issues: https://github.com/your-org/pipeline/issues
- Documentation: https://github.com/your-org/pipeline/blob/main/README.md
