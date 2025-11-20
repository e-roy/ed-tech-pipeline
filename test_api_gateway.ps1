# Test API Gateway Endpoints
# Run this after backend is deployed

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Testing API Gateway Endpoints" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

$REST_API_URL = "https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod"
$WS_API_URL = "wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod"

# Test REST API Health Endpoint
Write-Host "Testing REST API Health Endpoint..." -ForegroundColor Cyan
Write-Host "URL: $REST_API_URL/api/health" -ForegroundColor Gray
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri "$REST_API_URL/api/health" -UseBasicParsing -ErrorAction Stop
    Write-Host "✅ REST API Health Check: SUCCESS" -ForegroundColor Green
    Write-Host "   Status Code: $($response.StatusCode)" -ForegroundColor Gray
    Write-Host "   Response: $($response.Content)" -ForegroundColor Gray
} catch {
    Write-Host "❌ REST API Health Check: FAILED" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "   Status Code: $statusCode" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "   This is expected if backend code hasn't been deployed yet." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "WebSocket Testing" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "WebSocket URL: $WS_API_URL" -ForegroundColor Gray
Write-Host ""
Write-Host "To test WebSocket, use browser console:" -ForegroundColor Yellow
Write-Host ""
Write-Host "JavaScript code to run in browser console:" -ForegroundColor Cyan
$wsTestCode = @"
const ws = new WebSocket('$WS_API_URL?session_id=test-123');
ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));
ws.onerror = (e) => console.error('Error', e);
"@
Write-Host $wsTestCode -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "Test Summary" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "If REST API returns 200 OK, backend is working!" -ForegroundColor Green
Write-Host "If REST API returns 502/500, backend needs deployment." -ForegroundColor Yellow
Write-Host ""

