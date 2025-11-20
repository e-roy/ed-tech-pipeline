# Deploy Backend Code for API Gateway Support
# Uses AWS profile to get EC2 instance details and deploys

$ErrorActionPreference = "Stop"

$AWS_PROFILE = "default1"
$AWS_REGION = "us-east-2"
$INSTANCE_ID = "i-051a27d0f69e98ca2"
$EC2_USER = "ec2-user"
$EC2_KEY = "$env:USERPROFILE\Downloads\pipeline_orchestrator.pem"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Deploying Backend Code for API Gateway" -ForegroundColor Green
Write-Host "Using AWS Profile: $AWS_PROFILE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Get EC2 instance IP using AWS CLI
Write-Host "Getting EC2 instance details..." -ForegroundColor Cyan
try {
    $instanceInfo = aws ec2 describe-instances `
        --profile $AWS_PROFILE `
        --region $AWS_REGION `
        --instance-ids $INSTANCE_ID `
        --query 'Reservations[0].Instances[0].[PublicIpAddress,State.Name]' `
        --output text 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to get instance info: $instanceInfo"
    }
    
    $instanceData = $instanceInfo -split "`t"
    $EC2_HOST = $instanceData[0].Trim()
    $instanceState = $instanceData[1].Trim()
    
    if ($instanceState -ne "running") {
        Write-Host "ERROR: Instance is not running. State: $instanceState" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Instance IP: $EC2_HOST" -ForegroundColor Green
    Write-Host "Instance State: $instanceState" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to get EC2 instance info: $_" -ForegroundColor Red
    Write-Host "Falling back to hardcoded IP: 13.58.115.166" -ForegroundColor Yellow
    $EC2_HOST = "13.58.115.166"
}

# Check if SSH key exists
if (-not (Test-Path $EC2_KEY)) {
    Write-Host "SSH key not found at: $EC2_KEY" -ForegroundColor Yellow
    Write-Host "Please update EC2_KEY in this script or place key at that location" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Connecting to EC2: $EC2_USER@$EC2_HOST" -ForegroundColor Cyan
Write-Host ""

# SSH commands to execute
$sshCommands = @"
cd /opt/pipeline
sudo git fetch origin
sudo git reset --hard origin/master
cd backend

# Update .env file with FRONTEND_URL
if grep -q "^FRONTEND_URL=" .env 2>/dev/null; then
    sudo sed -i 's|^FRONTEND_URL=.*|FRONTEND_URL=https://pipeline-q3b1.vercel.app|' .env
    echo "Updated FRONTEND_URL in .env"
else
    echo "FRONTEND_URL=https://pipeline-q3b1.vercel.app" | sudo tee -a .env
    echo "Added FRONTEND_URL to .env"
fi

# Verify .env update
echo ""
echo "Current FRONTEND_URL in .env:"
grep "^FRONTEND_URL=" .env || echo "FRONTEND_URL not found"

# Restart service
echo ""
echo "Restarting pipeline-backend service..."
sudo systemctl restart pipeline-backend
sleep 3

# Check status
echo ""
echo "Service status:"
sudo systemctl status pipeline-backend --no-pager -l | head -20

# Test health endpoint
echo ""
echo "Testing health endpoint..."
curl -s http://localhost:8000/health | python3 -m json.tool || echo "Health check failed"

echo ""
echo "======================================"
echo "Deployment Complete!"
echo "======================================"
"@

# Execute via SSH
Write-Host "Executing deployment commands..." -ForegroundColor Cyan
ssh -i $EC2_KEY -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" $sshCommands

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Deployment Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Update Vercel environment variables" -ForegroundColor White
    Write-Host "2. Test API Gateway endpoints" -ForegroundColor White
    Write-Host ""
    Write-Host "API Gateway URLs:" -ForegroundColor Cyan
    Write-Host "  REST:    https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod" -ForegroundColor White
    Write-Host "  WebSocket: wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "Deployment may have failed. Check output above." -ForegroundColor Red
    Write-Host "You may need to SSH manually and run the commands." -ForegroundColor Yellow
}

