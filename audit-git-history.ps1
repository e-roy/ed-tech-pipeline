# Git History Security Audit Script
# Scans entire git history for sensitive information including AWS keys, API keys, and database credentials

param(
    [string]$OutputFile = "git-security-audit-report.txt",
    [switch]$Verbose
)

Write-Host "Git History Security Audit" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

# Define patterns to detect sensitive information
$patterns = @{
    'AWS_ACCESS_KEY' = @{
        'regex' = 'AKIA[0-9A-Z]{16}'
        'description' = 'AWS Access Key ID'
    }
    'AWS_SECRET_KEY' = @{
        'regex' = '(?<=AWS_SECRET_ACCESS_KEY[=:]\s*)[A-Za-z0-9/+=]{40,}'
        'description' = 'AWS Secret Access Key'
    }
    'REPLICATE_KEY' = @{
        'regex' = 'r8_[A-Za-z0-9]{20,}'
        'description' = 'Replicate API Key'
    }
    'OPENAI_KEY' = @{
        'regex' = 'sk-[A-Za-z0-9]{20,}'
        'description' = 'OpenAI API Key'
    }
    'ELEVENLABS_KEY' = @{
        'regex' = '(?<=ELEVENLABS_API_KEY[=:]\s*)[A-Za-z0-9]{20,}'
        'description' = 'ElevenLabs API Key'
    }
    'DATABASE_URL' = @{
        'regex' = 'postgresql[+:]?://[^:]+:[^@\s]+@'
        'description' = 'Database URL with password'
    }
    'JWT_SECRET' = @{
        'regex' = '(?<=JWT_SECRET_KEY[=:]\s*)[A-Za-z0-9+/=]{20,}'
        'description' = 'JWT Secret Key'
    }
    'AUTH_SECRET' = @{
        'regex' = '(?<=AUTH_SECRET[=:]\s*)[A-Za-z0-9+/=]{20,}'
        'description' = 'Auth Secret'
    }
    'GOOGLE_SECRET' = @{
        'regex' = '(?<=AUTH_GOOGLE_SECRET[=:]\s*)[A-Za-z0-9_\-]{20,}'
        'description' = 'Google OAuth Secret'
    }
}

# Patterns to exclude (placeholders and examples)
$excludePatterns = @(
    'sk-xxxxxxxx',
    'sk-your-openai-key',
    'sk-.*REDACTED',
    'r8_xxxxxxxx',
    'r8_your-replicate-key',
    'r8_.*REDACTED',
    'AKIAxxxxxxxx',
    'AKIA_REDACTED',
    'your-aws-access-key',
    'REDACTED.*',
    'REPLACE_WITH_ACTUAL.*',
    'dev-secret-key-change-in-production',
    'postgresql://postgres@',  # No password
    'postgresql://.*@localhost',  # Local without password
    'postgresql\+psycopg://postgres@'  # Local without password
)

# File extensions to exclude (documentation, images, etc.)
$excludeExtensions = @('.md', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.pdf', '.ico')

# Documentation file patterns to exclude
$excludeFilePatterns = @(
    'README',
    'TEST_UI',
    'ENV_SETUP',
    'quick-reference',
    'Samples',
    'Doc2',
    'ARCHITECTURE',
    'Tasks-',
    'NewPRD',
    'MUSIC_',
    'AUDIO_',
    'PERSON_',
    'DEPLOY_',
    'START_',
    'STORY_',
    'style_prompts'
)

function Test-IsPlaceholder {
    param([string]$value)
    
    foreach ($pattern in $excludePatterns) {
        if ($value -match $pattern) {
            return $true
        }
    }
    return $false
}

function Test-ShouldExcludeFile {
    param([string]$filePath)
    
    if ([string]::IsNullOrWhiteSpace($filePath)) {
        return $false
    }
    
    # Check file extension - use string manipulation to handle git paths safely
    $ext = ""
    try {
        # Normalize path separators for Windows compatibility
        $normalizedPath = $filePath -replace '/', '\'
        $ext = [System.IO.Path]::GetExtension($normalizedPath)
    } catch {
        # Fallback: extract extension manually
        if ($filePath -match '\.([^.]+)$') {
            $ext = ".$($matches[1])"
        }
    }
    
    if ($ext -and $excludeExtensions -contains $ext) {
        return $true
    }
    
    # Check file name patterns
    foreach ($pattern in $excludeFilePatterns) {
        if ($filePath -like "*$pattern*") {
            return $true
        }
    }
    
    return $false
}

function Get-CommitInfo {
    param([string]$commitHash)
    
    $info = git log -1 --pretty=format:"%H|%an|%ae|%ad|%s" --date=iso $commitHash
    if ($info) {
        $parts = $info -split '\|'
        return @{
            Hash = $parts[0]
            Author = $parts[1]
            Email = $parts[2]
            Date = $parts[3]
            Message = $parts[4]
        }
    }
    return $null
}

# Initialize findings
$findings = @()
$commitCount = 0
$processedCommits = @{}

Write-Host "Scanning git history..." -ForegroundColor Yellow
Write-Host "This may take several minutes depending on repository size." -ForegroundColor Gray
Write-Host ""

# Get all commits
$allCommits = git log --all --pretty=format:"%H" | Select-Object -Unique
$totalCommits = ($allCommits | Measure-Object).Count

Write-Host "Found $totalCommits unique commits to scan." -ForegroundColor Cyan
Write-Host ""

# Process each commit
foreach ($commit in $allCommits) {
    $commitCount++
    if ($commitCount % 100 -eq 0) {
        Write-Progress -Activity "Scanning commits" -Status "Processed $commitCount of $totalCommits" -PercentComplete (($commitCount / $totalCommits) * 100)
    }
    
    if ($Verbose) {
        Write-Host "Scanning commit $commitCount/$totalCommits : $($commit.Substring(0, 8))" -ForegroundColor Gray
    }
    
    # Get the diff for this commit
    $diff = git show $commit --format="" 2>$null
    
    if (-not $diff) {
        continue
    }
    
    # Track current file being processed
    $currentFile = $null
    $lineNumber = 0
    
    # Process each line of the diff
    $diffLines = $diff -split "`n"
    foreach ($line in $diffLines) {
        # Track file changes
        if ($line -match '^\+\+\+ b/(.+)') {
            $currentFile = $matches[1]
            # Skip special git paths
            if ($currentFile -eq '/dev/null' -or $currentFile -eq 'NUL') {
                $currentFile = $null
            }
            $lineNumber = 0
            continue
        }
        
        # Skip if no valid file
        if (-not $currentFile) {
            continue
        }
        
        # Skip file if it should be excluded
        if (Test-ShouldExcludeFile $currentFile) {
            continue
        }
        
        # Only check added lines (lines starting with +)
        if ($line -match '^\+(.+)') {
            $lineNumber++
            $content = $matches[1]
            
            # Check each pattern
            foreach ($patternName in $patterns.Keys) {
                $pattern = $patterns[$patternName]
                $matches = [regex]::Matches($content, $pattern.regex)
                
                foreach ($match in $matches) {
                    $value = $match.Value
                    
                    # Skip if it's a placeholder
                    if (Test-IsPlaceholder $value) {
                        continue
                    }
                    
                    # Additional validation for specific patterns
                    if ($patternName -eq 'DATABASE_URL') {
                        # Skip if no password in URL (just username@host)
                        if ($value -notmatch ':[^@]+@') {
                            continue
                        }
                        # Skip localhost without password
                        if ($value -match '@localhost' -and $value -notmatch ':[^@]+@') {
                            continue
                        }
                    }
                    
                    # Create finding
                    $finding = @{
                        CommitHash = $commit
                        FilePath = $currentFile
                        LineNumber = $lineNumber
                        SecretType = $patternName
                        Description = $pattern.description
                        ValuePreview = if ($value.Length -gt 20) { $value.Substring(0, 20) + "..." } else { $value }
                        FullValue = $value
                    }
                    
                    # Get commit info if not already cached
                    if (-not $processedCommits.ContainsKey($commit)) {
                        $commitInfo = Get-CommitInfo $commit
                        $processedCommits[$commit] = $commitInfo
                    }
                    
                    $finding.CommitInfo = $processedCommits[$commit]
                    
                    $findings += $finding
                    
                    if ($Verbose) {
                        Write-Host "  Found $($pattern.description) in $currentFile" -ForegroundColor Yellow
                    }
                }
            }
        }
    }
}

Write-Progress -Activity "Scanning commits" -Completed

Write-Host ""
Write-Host "Scan complete!" -ForegroundColor Green
Write-Host ""

# Generate report
Write-Host "Generating report..." -ForegroundColor Cyan

$report = @"
Git History Security Audit Report
==================================
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Repository: $(git rev-parse --show-toplevel)
Branch: $(git rev-parse --abbrev-ref HEAD)

SUMMARY
-------
Total Commits Scanned: $totalCommits
Total Findings: $($findings.Count)

Findings by Category:
"@

# Count by category
$categoryCounts = @{}
foreach ($finding in $findings) {
    if (-not $categoryCounts.ContainsKey($finding.SecretType)) {
        $categoryCounts[$finding.SecretType] = 0
    }
    $categoryCounts[$finding.SecretType]++
}

foreach ($category in $categoryCounts.Keys | Sort-Object) {
    $description = $patterns[$category].description
    $count = $categoryCounts[$category]
    $report += "`n  $description : $count"
}

if ($findings.Count -eq 0) {
    $report += "`n`n✅ No sensitive information found in git history!"
    $report += "`n`nThis is excellent - your repository appears to be clean."
} else {
    $report += "`n`n`nDETAILED FINDINGS"
    $report += "`n=================="
    $report += "`n"
    
    # Group by commit
    $findingsByCommit = $findings | Group-Object CommitHash
    
    foreach ($group in $findingsByCommit) {
        $commit = $group.Group[0]
        $commitInfo = $commit.CommitInfo
        
        $report += "`nCommit: $($commit.CommitHash.Substring(0, 8))"
        $report += "`n  Author: $($commitInfo.Author) <$($commitInfo.Email)>"
        $report += "`n  Date: $($commitInfo.Date)"
        $report += "`n  Message: $($commitInfo.Message)"
        $report += "`n"
        
        foreach ($finding in $group.Group) {
            $report += "`n  File: $($finding.FilePath)"
            $report += "`n    Line: $($finding.LineNumber)"
            $report += "`n    Type: $($finding.Description)"
            $report += "`n    Preview: $($finding.ValuePreview)"
            $report += "`n"
        }
    }
    
    $report += "`n`nRECOMMENDATIONS"
    $report += "`n================"
    $report += "`n"
    $report += "1. IMMEDIATE ACTIONS:"
    $report += "`n   - Rotate all exposed credentials immediately"
    $report += "`n   - Review each finding to determine if credentials are still in use"
    $report += "`n"
    $report += "2. REMOVAL FROM HISTORY:"
    $report += "`n   - Use git-filter-repo (recommended) or git filter-branch to remove secrets"
    $report += "`n   - Existing scripts: remove-secrets.ps1, replace-secrets-in-history.ps1"
    $report += "`n   - WARNING: This rewrites history - coordinate with team before force pushing"
    $report += "`n"
    $report += "3. PREVENTION:"
    $report += "`n   - Add .env files to .gitignore (already done)"
    $report += "`n   - Use git-secrets or pre-commit hooks to prevent future commits"
    $report += "`n   - Use environment variables or secret management services (AWS Secrets Manager)"
    $report += "`n   - Never commit actual credentials, only use placeholders in code"
    $report += "`n"
}

$report += "`n`n=========================================="
$report += "`nEnd of Report"
$report += "`n=========================================="

# Write report to file
$report | Out-File -FilePath $OutputFile -Encoding UTF8

Write-Host "Report saved to: $OutputFile" -ForegroundColor Green
Write-Host ""

# Display summary
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "-------" -ForegroundColor Cyan
Write-Host "Total Findings: $($findings.Count)" -ForegroundColor $(if ($findings.Count -eq 0) { "Green" } else { "Red" })

if ($findings.Count -gt 0) {
    Write-Host "`nFindings by Category:" -ForegroundColor Yellow
    foreach ($category in $categoryCounts.Keys | Sort-Object) {
        $description = $patterns[$category].description
        $count = $categoryCounts[$category]
        Write-Host "  $description : $count" -ForegroundColor White
    }
    Write-Host "`n⚠️  WARNING: Sensitive information found in git history!" -ForegroundColor Red
    Write-Host "   Review the full report: $OutputFile" -ForegroundColor Yellow
    Write-Host "   Rotate all exposed credentials immediately!" -ForegroundColor Red
} else {
    Write-Host "`n✅ No sensitive information found!" -ForegroundColor Green
}

Write-Host ""

