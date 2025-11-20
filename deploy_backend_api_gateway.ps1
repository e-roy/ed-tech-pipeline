# Deploy Backend Code for API Gateway Support
# This script SSHs into EC2 and deploys the code changes

$ErrorActionPreference = "Stop"

$EC2_HOST = "13.58.115.166"
$EC2_USER = "ec2-user"
$EC2_KEY = "$env:USERPROFILE\Downloads\pipeline_orchestrator.pem"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Deploying Backend Code for API Gateway" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if SSH key exists
if (-not (Test-Path $EC2_KEY)) {
    Write-Host "SSH key not found at: $EC2_KEY" -ForegroundColor Yellow
    Write-Host "Please update EC2_KEY in this script or place key at that location" -ForegroundColor Yellow
    exit 1
}

Write-Host "Connecting to EC2: $EC2_USER@$EC2_HOST" -ForegroundColor Cyan
Write-Host ""

# SSH commands to execute
$sshCommands = @"
cd /opt/pipeline
sudo git fetch origin
sudo git reset --hard origin/master
cd backend

# Update .env file
if grep -q "^FRONTEND_URL=" .env 2>/dev/null; then
    sudo sed -i 's|^FRONTEND_URL=.*|FRONTEND_URL=https://pipeline-q3b1.vercel.app|' .env
    echo "Updated FRONTEND_URL in .env"
else
    echo "FRONTEND_URL=https://pipeline-q3b1.vercel.app" | sudo tee -a .env
    echo "Added FRONTEND_URL to .env"
fi

# Restart service
sudo systemctl restart pipeline-backend
sleep 2
sudo systemctl status pipeline-backend --no-pager -l
"@

# Execute via SSH
Write-Host "Executing deployment commands..." -ForegroundColor Cyan
ssh -i $EC2_KEY "$EC2_USER@$EC2_HOST" $sshCommands

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Deployment Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next: Update Vercel environment variables" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "Deployment may have failed. Check output above." -ForegroundColor Red
    Write-Host "You may need to SSH manually and run the commands." -ForegroundColor Yellow
}

