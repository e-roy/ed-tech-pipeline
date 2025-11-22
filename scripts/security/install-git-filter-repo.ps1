# Install git-filter-repo
# This script helps install git-filter-repo on Windows

Write-Host "Installing git-filter-repo" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

# Check for Python
Write-Host "Checking for Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python from https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Check for pip
Write-Host "Checking for pip..." -ForegroundColor Yellow
try {
    $pipVersion = pip --version 2>&1
    Write-Host "✓ Found: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ pip not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install pip (usually comes with Python)" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Try to install git-filter-repo
Write-Host "Installing git-filter-repo..." -ForegroundColor Yellow
Write-Host ""

try {
    pip install git-filter-repo
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✓ git-filter-repo installed successfully!" -ForegroundColor Green
        Write-Host ""
        
        # Verify installation
        Write-Host "Verifying installation..." -ForegroundColor Yellow
        $version = git filter-repo --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Verified: $version" -ForegroundColor Green
            Write-Host ""
            Write-Host "You can now run:" -ForegroundColor Cyan
            Write-Host "  .\scripts\security\remove-aws-key-from-history.ps1" -ForegroundColor White
        } else {
            Write-Host "⚠ Installation may have succeeded but git can't find it." -ForegroundColor Yellow
            Write-Host "  Try restarting your terminal or adding Python Scripts to PATH." -ForegroundColor Yellow
        }
    } else {
        Write-Host ""
        Write-Host "✗ Installation failed!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Try installing manually:" -ForegroundColor Yellow
        Write-Host "  pip install git-filter-repo" -ForegroundColor White
        Write-Host ""
        Write-Host "Or with pipx (recommended):" -ForegroundColor Yellow
        Write-Host "  pipx install git-filter-repo" -ForegroundColor White
    }
} catch {
    Write-Host ""
    Write-Host "✗ Installation failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Try installing manually:" -ForegroundColor Yellow
    Write-Host "  pip install git-filter-repo" -ForegroundColor White
}

Write-Host ""

