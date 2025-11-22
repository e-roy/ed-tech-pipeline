# Script to replace a single secret in a file
param($filePath)

if (Test-Path $filePath) {
    $content = Get-Content $filePath -Raw -ErrorAction SilentlyContinue
    if ($content) {
        # WARNING: Replace placeholder values with actual secrets before use
        $content = $content -replace 'REPLACE_WITH_ACTUAL_REPLICATE_API_KEY', 'r8_REDACTED_REPLICATE_API_KEY'
        $content = $content -replace 'REPLACE_WITH_ACTUAL_AWS_ACCESS_KEY', 'AKIA_REDACTED_AWS_ACCESS_KEY'
        $content = $content -replace 'REPLACE_WITH_ACTUAL_AWS_SECRET_KEY', 'REDACTED_AWS_SECRET_KEY'
        $content = $content -replace 'REPLACE_WITH_ACTUAL_DB_PASSWORD', 'REDACTED_DB_PASSWORD'
        $content = $content -replace 'REPLACE_WITH_ACTUAL_JWT_SECRET', 'REDACTED_JWT_SECRET'
        Set-Content $filePath -Value $content -NoNewline -ErrorAction SilentlyContinue
    }
}

