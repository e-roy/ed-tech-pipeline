# Complete Next Steps for API Gateway Implementation
# This script helps you complete the remaining manual steps

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "API Gateway - Next Steps Helper" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

$REST_API_URL = "https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod"
$WS_API_URL = "wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod"

Write-Host "Step 1: Deploy Backend Code" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Run the deployment script:" -ForegroundColor Yellow
Write-Host "  bash backend/deploy_to_ec2_api_gateway.sh" -ForegroundColor White
Write-Host ""
Write-Host "Or manually SSH and deploy:" -ForegroundColor Yellow
Write-Host "  ssh -i ~/Downloads/pipeline_orchestrator.pem ec2-user@13.58.115.166" -ForegroundColor White
Write-Host "  cd /opt/pipeline" -ForegroundColor White
Write-Host "  sudo git pull" -ForegroundColor White
Write-Host "  sudo nano /opt/pipeline/backend/.env  # Add: FRONTEND_URL=https://pipeline-q3b1.vercel.app" -ForegroundColor White
Write-Host "  sudo systemctl restart pipeline-backend" -ForegroundColor White
Write-Host ""

Write-Host "Step 2: Update Vercel Environment Variables" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Option A - Via Vercel Dashboard (Recommended):" -ForegroundColor Yellow
Write-Host "  1. Go to: https://vercel.com/dashboard" -ForegroundColor White
Write-Host "  2. Select your project" -ForegroundColor White
Write-Host "  3. Go to: Settings -> Environment Variables" -ForegroundColor White
Write-Host "  4. Add/Update these variables:" -ForegroundColor White
Write-Host "     NEXT_PUBLIC_API_URL = $REST_API_URL" -ForegroundColor Green
Write-Host "     NEXT_PUBLIC_WS_URL = $WS_API_URL" -ForegroundColor Green
Write-Host "  5. Select 'Production' environment for both" -ForegroundColor White
Write-Host "  6. Vercel will auto-redeploy" -ForegroundColor White
Write-Host ""
Write-Host "Option B - Via Vercel CLI:" -ForegroundColor Yellow
Write-Host "  cd frontend" -ForegroundColor White
Write-Host "  vercel env add NEXT_PUBLIC_API_URL production" -ForegroundColor White
Write-Host "    # When prompted, enter: $REST_API_URL" -ForegroundColor Gray
Write-Host "  vercel env add NEXT_PUBLIC_WS_URL production" -ForegroundColor White
Write-Host "    # When prompted, enter: $WS_API_URL" -ForegroundColor Gray
Write-Host ""

Write-Host "Step 3: Test API Gateway" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Testing REST API Gateway..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$REST_API_URL/api/health" -UseBasicParsing -ErrorAction Stop
    Write-Host "  Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "  Response: $($response.Content)" -ForegroundColor Gray
    Write-Host "  REST API Gateway: WORKING" -ForegroundColor Green
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "  Status: $statusCode" -ForegroundColor $(if ($statusCode -eq 502) { "Yellow" } else { "Red" })
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($statusCode -eq 502) {
        Write-Host "  Note: 502 means backend not deployed yet (expected)" -ForegroundColor Yellow
    }
}
Write-Host ""

Write-Host "WebSocket Testing:" -ForegroundColor Yellow
Write-Host "  Open browser console on https://pipeline-q3b1.vercel.app/" -ForegroundColor White
Write-Host "  Run this JavaScript:" -ForegroundColor White
Write-Host ""
$wsCode = "const ws = new WebSocket('$WS_API_URL?session_id=test-123');`nws.onopen = () => console.log('Connected');`nws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));"
Write-Host $wsCode -ForegroundColor Cyan
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "Summary" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "API Gateway URLs:" -ForegroundColor Cyan
Write-Host "  REST:    $REST_API_URL" -ForegroundColor White
Write-Host "  WebSocket: $WS_API_URL" -ForegroundColor White
Write-Host ""
Write-Host "Next Actions:" -ForegroundColor Cyan
Write-Host "  1. Deploy backend code (Step 1)" -ForegroundColor Yellow
Write-Host "  2. Update Vercel env vars (Step 2)" -ForegroundColor Yellow
Write-Host "  3. Test everything (Step 3)" -ForegroundColor Yellow
Write-Host ""

