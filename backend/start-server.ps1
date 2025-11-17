# Start backend server
# This script starts a single instance of the FastAPI backend server

$ErrorActionPreference = "Stop"

Write-Host "Starting backend server..." -ForegroundColor Yellow

# Get the script directory (backend folder)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Check if port 8000 is already in use
$existing = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "ERROR: Port 8000 is already in use!" -ForegroundColor Red
    Write-Host "Please run stop-server.ps1 first to stop existing instances." -ForegroundColor Yellow
    $existing | ForEach-Object {
        $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "  Process $($_.OwningProcess) ($($proc.ProcessName)) is using port 8000" -ForegroundColor Gray
        }
    }
    exit 1
}

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Using Python: $pythonVersion" -ForegroundColor Cyan
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if uvicorn is available
try {
    python -m uvicorn --help | Out-Null
} catch {
    Write-Host "ERROR: uvicorn is not installed. Install it with: pip install uvicorn" -ForegroundColor Red
    exit 1
}

# Check if app.main exists
if (-not (Test-Path "app\main.py")) {
    Write-Host "ERROR: app\main.py not found. Are you in the backend directory?" -ForegroundColor Red
    exit 1
}

Write-Host "Starting server on http://localhost:8000..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

# Start the server
try {
    python -m uvicorn app.main:app --reload --host localhost --port 8000
} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to start server: $_" -ForegroundColor Red
    exit 1
}


