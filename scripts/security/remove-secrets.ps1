# Script to remove secrets from git history
# This will rewrite git history - use with caution!

# WARNING: This script should be configured with actual secrets before use
# Replace the placeholder values below with the actual secrets you need to remove
$secrets = @(
    @{old="REPLACE_WITH_ACTUAL_REPLICATE_API_KEY"; new="r8_REDACTED_REPLICATE_API_KEY"},
    @{old="REPLACE_WITH_ACTUAL_AWS_ACCESS_KEY"; new="AKIA_REDACTED_AWS_ACCESS_KEY"},
    @{old="REPLACE_WITH_ACTUAL_AWS_SECRET_KEY"; new="REDACTED_AWS_SECRET_KEY"},
    @{old="REPLACE_WITH_ACTUAL_DB_PASSWORD"; new="REDACTED_DB_PASSWORD"},
    @{old="REPLACE_WITH_ACTUAL_JWT_SECRET"; new="REDACTED_JWT_SECRET"}
)

Write-Host "Removing secrets from git history..." -ForegroundColor Yellow
Write-Host "This will rewrite all commits. This may take several minutes." -ForegroundColor Yellow

# Use git filter-branch to rewrite history
$env:GIT_EDITOR = "true"  # Skip editor prompts

foreach ($secret in $secrets) {
    Write-Host "Removing: $($secret.old[0..20])..." -ForegroundColor Cyan
    
    # Use git filter-branch with tree-filter to replace in all files
    git filter-branch --force --index-filter `
        "git ls-files -s | sed 's/`t.*//' | git update-index --index-info && git ls-files | ForEach-Object { `$content = Get-Content `$_ -Raw; if (`$content -match [regex]::Escape('$($secret.old)')) { `$content = `$content -replace [regex]::Escape('$($secret.old)'), '$($secret.new)'; Set-Content `$_ -Value `$content -NoNewline } }" `
        --prune-empty --tag-name-filter cat -- --all 2>&1 | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error removing secret. Trying alternative method..." -ForegroundColor Red
        # Alternative: use sed if available, or manual replacement
        git filter-branch --force --tree-filter `
            "powershell -Command `"Get-ChildItem -Recurse -File | ForEach-Object { `$content = Get-Content `$_.FullName -Raw -ErrorAction SilentlyContinue; if (`$content) { `$newContent = `$content -replace [regex]::Escape('$($secret.old)'), '$($secret.new)'; if (`$newContent -ne `$content) { Set-Content `$_.FullName -Value `$newContent -NoNewline } } }`"" `
            --prune-empty --tag-name-filter cat -- --all 2>&1 | Out-Null
    }
}

Write-Host "`nSecrets removed from history!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Review the changes: git log --all --oneline" -ForegroundColor White
Write-Host "2. Verify secrets are gone: git log --all -p | Select-String 'REPLACE_WITH_ACTUAL_REPLICATE_API_KEY'" -ForegroundColor White
Write-Host "3. Force push (coordinate with team first): git push origin --force --all" -ForegroundColor White
Write-Host "4. Force push tags: git push origin --force --tags" -ForegroundColor White

