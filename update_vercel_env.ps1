# Update Vercel Environment Variables for API Gateway
# Requires Vercel CLI: npm install -g vercel

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Updating Vercel Environment Variables" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if Vercel CLI is installed
if (-not (Get-Command vercel -ErrorAction SilentlyContinue)) {
    Write-Host "Vercel CLI not found. Installing..." -ForegroundColor Yellow
    npm install -g vercel
}

# API Gateway URLs
$REST_API_URL = "https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod"
$WS_API_URL = "wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod"

Write-Host "Setting environment variables:" -ForegroundColor Cyan
Write-Host "  NEXT_PUBLIC_API_URL = $REST_API_URL"
Write-Host "  NEXT_PUBLIC_WS_URL = $WS_API_URL"
Write-Host ""

# Check if we're in a Vercel project
if (-not (Test-Path ".vercel")) {
    Write-Host "Not in a Vercel project directory." -ForegroundColor Yellow
    Write-Host "Please run this from the frontend directory or link the project first:" -ForegroundColor Yellow
    Write-Host "  cd frontend" -ForegroundColor Yellow
    Write-Host "  vercel link" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Alternatively, update environment variables via Vercel Dashboard:" -ForegroundColor Yellow
    Write-Host "  https://vercel.com/dashboard -> Your Project -> Settings -> Environment Variables" -ForegroundColor Yellow
    exit 1
}

# Set environment variables
Write-Host "Setting NEXT_PUBLIC_API_URL..." -ForegroundColor Cyan
vercel env add NEXT_PUBLIC_API_URL production
# Note: This will prompt for value - user needs to enter: $REST_API_URL

Write-Host "Setting NEXT_PUBLIC_WS_URL..." -ForegroundColor Cyan
vercel env add NEXT_PUBLIC_WS_URL production
# Note: This will prompt for value - user needs to enter: $WS_API_URL

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Manual Steps Required:" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Vercel CLI will prompt you for values. Enter:" -ForegroundColor Yellow
Write-Host "  For NEXT_PUBLIC_API_URL: $REST_API_URL" -ForegroundColor Cyan
Write-Host "  For NEXT_PUBLIC_WS_URL: $WS_API_URL" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or update via Vercel Dashboard:" -ForegroundColor Yellow
Write-Host "  https://vercel.com/dashboard" -ForegroundColor Cyan
Write-Host ""

