# Install Bun on EC2 instance (PowerShell version)
# Runs from local machine to install Bun on the deployed EC2 instance

$ErrorActionPreference = "Stop"

# EC2 Configuration
$EC2_HOST = "13.58.115.166"
$EC2_USER = "ec2-user"
$EC2_KEY = "$env:USERPROFILE\Downloads\pipeline_orchestrator.pem"

Write-Host "========================================" -ForegroundColor Green
Write-Host "Installing Bun on EC2 (api.classclipscohort3.com)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if SSH key exists
if (-not (Test-Path $EC2_KEY)) {
    Write-Host "SSH key not found at: $EC2_KEY" -ForegroundColor Yellow
    Write-Host "Looking for alternative keys..." -ForegroundColor Yellow
    
    # Try to find .ssh/id_rsa
    $AltKey = "$env:USERPROFILE\.ssh\id_rsa"
    if (Test-Path $AltKey) {
        $EC2_KEY = $AltKey
        Write-Host "Using: $EC2_KEY" -ForegroundColor Green
    } else {
        $EC2_KEY = Read-Host "Please enter the full path to your EC2 key"
        if (-not (Test-Path $EC2_KEY)) {
            Write-Host "Key not found: $EC2_KEY" -ForegroundColor Red
            exit 1
        }
    }
}

Write-Host "Connecting to EC2 instance: $EC2_USER@$EC2_HOST" -ForegroundColor Green
Write-Host "Target: api.classclipscohort3.com" -ForegroundColor Cyan
Write-Host ""

# Create the installation commands as a here-string
$InstallCommands = @'
set -e

echo "======================================"
echo "Installing Bun"
echo "======================================"

# Check if bun is already installed
if command -v bun &> /dev/null; then
    echo "Bun is already installed:"
    bun --version
    echo ""
    echo "Updating to latest version..."
    curl -fsSL https://bun.sh/install | bash
else
    echo "Installing Bun..."
    curl -fsSL https://bun.sh/install | bash
fi

# Source bashrc to make bun available in current session
source ~/.bashrc

# Verify installation
echo ""
echo "Verifying Bun installation..."
~/.bun/bin/bun --version

# Navigate to Remotion project and install dependencies
echo ""
echo "======================================"
echo "Installing Remotion dependencies"
echo "======================================"

cd /opt/pipeline/remotion || { echo "Remotion directory not found"; exit 1; }

# Install dependencies with bun
echo "Installing Remotion packages..."
~/.bun/bin/bun install

echo ""
echo "======================================"
echo "Making Bun available system-wide"
echo "======================================"

# Create symlinks so systemd services can find bun
sudo ln -sf /home/ec2-user/.bun/bin/bun /usr/local/bin/bun
sudo ln -sf /home/ec2-user/.bun/bin/bunx /usr/local/bin/bunx

echo "Created symlinks:"
ls -l /usr/local/bin/bun /usr/local/bin/bunx

echo ""
echo "======================================"
echo "Installation complete!"
echo "======================================"
echo ""
echo "Bun version:"
bun --version
echo ""
echo "Bun location:"
which bun
'@

try {
    # Execute SSH command with the installation script
    Write-Host "Executing installation commands on EC2..." -ForegroundColor Yellow
    
    # Write to temp file with Unix line endings
    $TempScript = Join-Path $env:TEMP "install_bun_temp.sh"
    $UnixCommands = $InstallCommands -replace "`r`n", "`n"
    [System.IO.File]::WriteAllText($TempScript, $UnixCommands, [System.Text.UTF8Encoding]::new($false))
    
    # Execute via SSH
    Get-Content $TempScript -Raw | ssh.exe -i $EC2_KEY -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" "bash -s"
    
    # Clean up temp file
    Remove-Item $TempScript -ErrorAction SilentlyContinue
    
    Write-Host ""
    Write-Host "======================================" -ForegroundColor Green
    Write-Host "Bun Installation Complete!" -ForegroundColor Green
    Write-Host "======================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now run Agent5 video generation." -ForegroundColor Cyan
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "======================================" -ForegroundColor Red
    Write-Host "Installation Failed!" -ForegroundColor Red
    Write-Host "======================================" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    exit 1
}

