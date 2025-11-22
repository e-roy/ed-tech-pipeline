# PowerShell script to replace secrets in all files in git history
Write-Host "Replacing secrets in git history. This will take several minutes..." -ForegroundColor Yellow

$env:FILTER_BRANCH_SQUELCH_WARNING = "1"

# Use git filter-branch with tree-filter to replace secrets in all files
git filter-branch --force --tree-filter @"
powershell -Command `"
Get-ChildItem -Recurse -File | Where-Object { `$_.FullName -notlike '*\.git\*' } | ForEach-Object {
    try {
        `$content = Get-Content `$_.FullName -Raw -ErrorAction SilentlyContinue
        if (`$content) {
            `$original = `$content
            # WARNING: Replace placeholder values with actual secrets before use
            `$content = `$content -replace 'REPLACE_WITH_ACTUAL_REPLICATE_API_KEY', 'r8_REDACTED_REPLICATE_API_KEY'
            `$content = `$content -replace 'REPLACE_WITH_ACTUAL_AWS_ACCESS_KEY', 'AKIA_REDACTED_AWS_ACCESS_KEY'
            `$content = `$content -replace 'REPLACE_WITH_ACTUAL_AWS_SECRET_KEY', 'REDACTED_AWS_SECRET_KEY'
            `$content = `$content -replace 'REPLACE_WITH_ACTUAL_DB_PASSWORD', 'REDACTED_DB_PASSWORD'
            `$content = `$content -replace 'REPLACE_WITH_ACTUAL_JWT_SECRET', 'REDACTED_JWT_SECRET'
            if (`$content -ne `$original) {
                Set-Content `$_.FullName -Value `$content -NoNewline -ErrorAction SilentlyContinue
            }
        }
    } catch {
        # Ignore errors for binary files
    }
}
`"
"@ --prune-empty --tag-name-filter cat -- --all

Write-Host "`nSecrets replaced in history!" -ForegroundColor Green

