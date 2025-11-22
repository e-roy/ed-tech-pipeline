# Remove AWS Access Key from Git History
# WARNING: This rewrites git history. Make sure you have a backup!

param(
    [Parameter(Mandatory=$true)]
    [string]$AwsKey,  # Specify the key to remove, e.g., "AKIA_REDACTED_AWS_ACCESS_KEY"
    [string]$Replacement = "AKIA_REDACTED_AWS_ACCESS_KEY",
    [switch]$DryRun,
    [switch]$Force
)

Write-Host "Remove AWS Key from Git History" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Host "ERROR: Not in a git repository!" -ForegroundColor Red
    exit 1
}

# Check if git-filter-repo is installed
try {
    $version = git filter-repo --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git-filter-repo not found"
    }
    Write-Host "[OK] git-filter-repo is installed" -ForegroundColor Green
    Write-Host "  Version: $version" -ForegroundColor Gray
} catch {
    Write-Host "ERROR: git-filter-repo is not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install it with:" -ForegroundColor Yellow
    Write-Host "  pip install git-filter-repo" -ForegroundColor White
    Write-Host ""
    Write-Host "Or on Windows with pipx:" -ForegroundColor Yellow
    Write-Host "  pipx install git-filter-repo" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  AWS Key to remove: $AwsKey" -ForegroundColor White
Write-Host "  Replacement: $Replacement" -ForegroundColor White
Write-Host "  Dry Run: $DryRun" -ForegroundColor White
Write-Host ""

# Check for uncommitted changes
$status = git status --porcelain
if ($status) {
    Write-Host "WARNING: You have uncommitted changes!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Uncommitted files:" -ForegroundColor Yellow
    $status | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    Write-Host ""
    
    if (-not $Force) {
        Write-Host "Please commit or stash your changes before running this script." -ForegroundColor Yellow
        Write-Host "Or use -Force to proceed anyway (not recommended)." -ForegroundColor Yellow
        exit 1
    } else {
        Write-Host "Proceeding with -Force flag..." -ForegroundColor Yellow
    }
}

# Check current branch
$currentBranch = git rev-parse --abbrev-ref HEAD
Write-Host "Current branch: $currentBranch" -ForegroundColor Gray
Write-Host ""

# Create a backup branch before making changes
$backupBranch = "backup-before-filter-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Write-Host "Creating backup branch: $backupBranch" -ForegroundColor Yellow
git branch $backupBranch
Write-Host "[OK] Backup created" -ForegroundColor Green
Write-Host ""

# Create replacement file for git-filter-repo
$replaceFile = "filter-repo-replacements.txt"
$replacementLine = "$AwsKey==>$Replacement"
$replacementLine | Out-File -FilePath $replaceFile -Encoding ASCII -NoNewline
Write-Host "Created replacement file: $replaceFile" -ForegroundColor Gray
Write-Host "  Content: $replacementLine" -ForegroundColor Gray
Write-Host ""

if ($DryRun) {
    Write-Host "DRY RUN MODE - No changes will be made" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To actually perform the replacement, run:" -ForegroundColor Cyan
    Write-Host "  .\scripts\security\remove-aws-key-from-history.ps1" -ForegroundColor White
    Write-Host ""
    
    # Clean up
    Remove-Item $replaceFile -ErrorAction SilentlyContinue
    
    exit 0
}

# Final confirmation
Write-Host "WARNING: This will rewrite git history!" -ForegroundColor Red
Write-Host ""
Write-Host "This will:" -ForegroundColor Yellow
Write-Host "  1. Replace '$AwsKey' with '$Replacement' in ALL commits" -ForegroundColor White
Write-Host "  2. Rewrite commit hashes" -ForegroundColor White
Write-Host "  3. Require force push to update remote" -ForegroundColor White
Write-Host ""
Write-Host "Make sure:" -ForegroundColor Yellow
Write-Host "  [*] You have a backup (backup branch created: $backupBranch)" -ForegroundColor White
Write-Host "  [*] All team members are aware" -ForegroundColor White
Write-Host "  [*] You can force push to remote" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "Type 'yes' to proceed"
if ($confirm -ne "yes") {
    Write-Host "Aborted." -ForegroundColor Yellow
    
    # Clean up
    Remove-Item $replaceFile -ErrorAction SilentlyContinue
    
    exit 0
}

Write-Host ""
Write-Host "Running git-filter-repo..." -ForegroundColor Cyan
Write-Host ""

# Run git-filter-repo
$errorOccurred = $false

try {
    $null = git filter-repo --replace-text $replaceFile --force 2>&1
    if ($LASTEXITCODE -ne 0) {
        $errorOccurred = $true
    }
} catch {
    $errorOccurred = $true
    Write-Host ""
    Write-Host "ERROR: Failed to run git-filter-repo" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

# Clean up replacement file
if (Test-Path $replaceFile) {
    Remove-Item $replaceFile -ErrorAction SilentlyContinue
}

# Handle results
if ($errorOccurred) {
    Write-Host ""
    Write-Host "ERROR: git-filter-repo failed!" -ForegroundColor Red
    Write-Host "Exit code: $LASTEXITCODE" -ForegroundColor Red
    Write-Host ""
    Write-Host "To restore from backup, run:" -ForegroundColor Yellow
    Write-Host "  git reset --hard $backupBranch" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "Successfully removed AWS key from git history!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Review the changes: git log --all" -ForegroundColor White
    Write-Host "  2. Verify the key is gone: git log -S '$AwsKey' --all" -ForegroundColor White
    Write-Host "  3. Force push to remote (if needed):" -ForegroundColor White
    Write-Host "     git push origin --force --all" -ForegroundColor Yellow
    Write-Host "     git push origin --force --tags" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "WARNING: Force pushing rewrites remote history!" -ForegroundColor Red
    Write-Host "  Make sure all team members are aware and have pulled the changes." -ForegroundColor Yellow
}

Write-Host ""

