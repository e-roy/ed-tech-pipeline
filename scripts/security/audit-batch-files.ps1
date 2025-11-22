# Batch Files Security Audit Script
# Scans .sh, .ps1, .html, and .md files in codebase and git history for sensitive information

param(
    [string]$OutputFile = "batch-files-security-audit-report.txt",
    [string]$AffectedFilesList = "affected-files.md",
    [switch]$Verbose,
    [switch]$CurrentOnly,
    [switch]$HistoryOnly
)

Write-Host "Batch Files Security Audit" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

# Validate parameters
if ($CurrentOnly -and $HistoryOnly) {
    Write-Host "Error: Cannot use both -CurrentOnly and -HistoryOnly flags simultaneously" -ForegroundColor Red
    exit 1
}

# Target file extensions
$targetExtensions = @('.sh', '.ps1', '.html', '.md')

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
    'PASSWORD' = @{
        'regex' = '(?<=password[=:]\s*|PASSWORD[=:]\s*)[^\s"''`]{8,}'
        'description' = 'Password in variable'
    }
    'API_KEY' = @{
        'regex' = '(?<=API_KEY[=:]\s*|api_key[=:]\s*)[A-Za-z0-9_\-]{20,}'
        'description' = 'Generic API Key'
    }
    'SECRET_KEY' = @{
        'regex' = '(?<=SECRET_KEY[=:]\s*|secret_key[=:]\s*)[A-Za-z0-9+/=]{20,}'
        'description' = 'Generic Secret Key'
    }
    'PRIVATE_KEY' = @{
        'regex' = '-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----'
        'description' = 'Private Key'
    }
    'BEARER_TOKEN' = @{
        'regex' = '(?<=Bearer\s+|bearer\s+)[A-Za-z0-9_\-\.]{20,}'
        'description' = 'Bearer Token'
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
    'postgresql\+psycopg://postgres@',  # Local without password
    'YOUR_.*',
    'EXAMPLE.*',
    'PLACEHOLDER.*',
    'CHANGE.*',
    'password.*=.*password',
    'password.*=.*123456',
    'password.*=.*changeme'
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

function Test-IsTargetFile {
    param([string]$filePath)
    
    if ([string]::IsNullOrWhiteSpace($filePath)) {
        return $false
    }
    
    # Extract extension
    $ext = ""
    try {
        $normalizedPath = $filePath -replace '/', '\'
        $ext = [System.IO.Path]::GetExtension($normalizedPath)
    } catch {
        if ($filePath -match '\.([^.]+)$') {
            $ext = ".$($matches[1])"
        }
    }
    
    return $targetExtensions -contains $ext
}

function Get-CommitInfo {
    param([string]$commitHash)
    
    $info = git log -1 --pretty=format:"%H|%an|%ae|%ad|%s" --date=iso $commitHash 2>$null
    if ($info) {
        $parts = $info -split '\|'
        if ($parts.Count -ge 5) {
            return @{
                Hash = $parts[0]
                Author = $parts[1]
                Email = $parts[2]
                Date = $parts[3]
                Message = $parts[4..($parts.Count - 1)] -join '|'  # Join remaining parts in case message contains |
            }
        }
    }
    return $null
}

function Scan-FileContent {
    param(
        [string]$filePath,
        [string]$content,
        [string]$source = "filesystem",
        [string]$commitHash = $null
    )
    
    $fileFindings = @()
    $lineNumber = 0
    
    # Handle both Windows (\r\n) and Unix (\n) line endings
    $lines = $content -split "`r?`n"
    foreach ($line in $lines) {
        $lineNumber++
        
        # Check each pattern
        foreach ($patternName in $patterns.Keys) {
            $pattern = $patterns[$patternName]
            $matches = [regex]::Matches($line, $pattern.regex)
            
            foreach ($match in $matches) {
                $value = $match.Value
                
                # Skip if it's a placeholder
                if (Test-IsPlaceholder $value) {
                    continue
                }
                
                # Additional validation for specific patterns
                if ($patternName -eq 'DATABASE_URL') {
                    # Skip if no password in URL (username:password@host format)
                    if ($value -notmatch ':[^@]+@') {
                        continue
                    }
                }
                
                if ($patternName -eq 'PASSWORD') {
                    # Skip common placeholder passwords
                    if ($value -match '^(password|123456|changeme|test|example)$') {
                        continue
                    }
                }
                
                # Create finding
                $valuePreview = if ($value -and $value.Length -gt 30) { $value.Substring(0, 30) + "..." } else { $value }
                $finding = @{
                    FilePath = $filePath
                    LineNumber = $lineNumber
                    SecretType = $patternName
                    Description = $pattern.description
                    ValuePreview = $valuePreview
                    FullValue = $value
                    Source = $source
                    CommitHash = $commitHash
                }
                
                $fileFindings += $finding
                
                if ($Verbose) {
                    Write-Host "  Found $($pattern.description) in $filePath (line $lineNumber)" -ForegroundColor Yellow
                }
            }
        }
    }
    
    return $fileFindings
}

# Initialize findings
$findings = @()

# Scan current filesystem
if (-not $HistoryOnly) {
    Write-Host "Scanning current codebase..." -ForegroundColor Yellow
    Write-Host ""
    
    $repoRoot = git rev-parse --show-toplevel 2>$null
    if (-not $repoRoot) {
        Write-Host "Warning: Not in a git repository. Scanning current directory only." -ForegroundColor Yellow
        $repoRoot = (Get-Location).Path
    }
    
    $allFiles = Get-ChildItem -Path $repoRoot -Recurse -File | Where-Object {
        Test-IsTargetFile $_.FullName
    }
    
    $totalFiles = ($allFiles | Measure-Object).Count
    Write-Host "Found $totalFiles target files in codebase." -ForegroundColor Cyan
    Write-Host ""
    
    if ($totalFiles -gt 0) {
        $fileCount = 0
        foreach ($file in $allFiles) {
            $fileCount++
            if ($totalFiles -gt 0 -and $fileCount % 10 -eq 0) {
                Write-Progress -Activity "Scanning files" -Status "Processed $fileCount of $totalFiles" -PercentComplete (($fileCount / $totalFiles) * 100)
            }
            
            $relativePath = $file.FullName.Replace($repoRoot, '') -replace '^[\\/]+', ''
            
            if ($Verbose) {
                Write-Host "Scanning: $relativePath" -ForegroundColor Gray
            }
            
            try {
                $content = Get-Content -Path $file.FullName -Raw -ErrorAction Stop
                $fileFindings = Scan-FileContent -filePath $relativePath -content $content -source "filesystem"
                $findings += $fileFindings
            } catch {
                if ($Verbose) {
                    Write-Host "  Warning: Could not read file: $relativePath" -ForegroundColor Yellow
                }
            }
        }
        
        Write-Progress -Activity "Scanning files" -Completed
        Write-Host "Current codebase scan complete!" -ForegroundColor Green
        Write-Host ""
    }
}

# Scan git history
if (-not $CurrentOnly) {
    $repoRoot = git rev-parse --show-toplevel 2>$null
    if (-not $repoRoot) {
        Write-Host "Warning: Not in a git repository. Skipping git history scan." -ForegroundColor Yellow
        Write-Host ""
    } else {
        Write-Host "Scanning git history..." -ForegroundColor Yellow
        Write-Host "This may take several minutes depending on repository size." -ForegroundColor Gray
        Write-Host ""
        
        # Get all commits
        $allCommits = git log --all --pretty=format:"%H" 2>$null | Select-Object -Unique
        $totalCommits = ($allCommits | Measure-Object).Count
        
        Write-Host "Found $totalCommits unique commits to scan." -ForegroundColor Cyan
        Write-Host ""
        
        if ($totalCommits -eq 0) {
            Write-Host "No commits found in repository." -ForegroundColor Yellow
            Write-Host ""
        } else {
            $commitCount = 0
            $processedCommits = @{}
            $processedFiles = @{}
            
            foreach ($commit in $allCommits) {
                $commitCount++
                if ($totalCommits -gt 0 -and $commitCount % 100 -eq 0) {
                    Write-Progress -Activity "Scanning commits" -Status "Processed $commitCount of $totalCommits" -PercentComplete (($commitCount / $totalCommits) * 100)
                }
                
                if ($Verbose) {
                    $commitShort = if ($commit -and $commit.Length -ge 8) { $commit.Substring(0, 8) } else { $commit }
                    Write-Host "Scanning commit $commitCount/$totalCommits : $commitShort" -ForegroundColor Gray
                }
                
                # Get list of files changed in this commit
                $changedFiles = git diff-tree --no-commit-id --name-only -r $commit 2>$null
                
                if (-not $changedFiles) {
                    continue
                }
                
                foreach ($filePath in $changedFiles) {
                    # Only process target file types
                    if (-not (Test-IsTargetFile $filePath)) {
                        continue
                    }
                    
                    # Skip if we've already processed this file in this commit
                    $fileKey = "$commit|$filePath"
                    if ($processedFiles.ContainsKey($fileKey)) {
                        continue
                    }
                    $processedFiles[$fileKey] = $true
                    
                    # Get file content at this commit
                    try {
                        $content = git show "${commit}:$filePath" 2>$null
                        if ($content) {
                            $fileFindings = Scan-FileContent -filePath $filePath -content $content -source "git-history" -commitHash $commit
                            
                            # Add commit info to findings
                            if ($fileFindings.Count -gt 0) {
                                if (-not $processedCommits.ContainsKey($commit)) {
                                    $commitInfo = Get-CommitInfo $commit
                                    $processedCommits[$commit] = $commitInfo
                                }
                                
                                foreach ($finding in $fileFindings) {
                                    $finding.CommitInfo = $processedCommits[$commit]
                                }
                            }
                            
                            $findings += $fileFindings
                        }
                    } catch {
                        # File might have been deleted or doesn't exist in this commit
                        continue
                    }
                }
            }
            
            Write-Progress -Activity "Scanning commits" -Completed
            Write-Host "Git history scan complete!" -ForegroundColor Green
            Write-Host ""
        }
    }
}

# Generate report
Write-Host "Generating report..." -ForegroundColor Cyan

$repoPath = git rev-parse --show-toplevel 2>$null
if (-not $repoPath) {
    $repoPath = (Get-Location).Path
}

$branch = git rev-parse --abbrev-ref HEAD 2>$null
if (-not $branch) {
    $branch = "N/A (not a git repository)"
}

# Group findings by file (needed for both report and markdown)
$findingsByFile = $findings | Group-Object FilePath

$report = @"
Batch Files Security Audit Report
==================================
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Repository: $repoPath
Branch: $branch
Scanned Extensions: $($targetExtensions -join ', ')

SUMMARY
-------
Total Findings: $($findings.Count)
Files Scanned (Current): $(if (-not $HistoryOnly) { "Yes" } else { "Skipped" })
Git History Scanned: $(if (-not $CurrentOnly) { "Yes" } else { "Skipped" })

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

# Count by source
$sourceCounts = @{}
foreach ($finding in $findings) {
    if (-not $sourceCounts.ContainsKey($finding.Source)) {
        $sourceCounts[$finding.Source] = 0
    }
    $sourceCounts[$finding.Source]++
}

$report += "`n`nFindings by Source:"
foreach ($source in $sourceCounts.Keys | Sort-Object) {
    $count = $sourceCounts[$source]
    $report += "`n  $source : $count"
}

if ($findings.Count -eq 0) {
    $report += "`n`n✅ No sensitive information found in batch files!"
    $report += "`n`nThis is excellent - your batch files appear to be clean."
} else {
    $report += "`n`n`nDETAILED FINDINGS"
    $report += "`n=================="
    $report += "`n"
    
    foreach ($group in $findingsByFile) {
        $filePath = $group.Name
        $fileFindings = $group.Group
        
        $report += "`nFile: $filePath"
        $report += "`n  Source: $($fileFindings[0].Source)"
        
        if ($fileFindings[0].CommitHash) {
            $commitInfo = $fileFindings[0].CommitInfo
            if ($commitInfo) {
                $hashShort = if ($commitInfo.Hash -and $commitInfo.Hash.Length -ge 8) { $commitInfo.Hash.Substring(0, 8) } else { $commitInfo.Hash }
                $report += "`n  Commit: $hashShort"
                $report += "`n  Author: $($commitInfo.Author) <$($commitInfo.Email)>"
                $report += "`n  Date: $($commitInfo.Date)"
                $report += "`n  Message: $($commitInfo.Message)"
            }
        }
        
        $report += "`n"
        
        foreach ($finding in $fileFindings) {
            $report += "`n  Line: $($finding.LineNumber)"
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
    $report += "`n   - Remove sensitive information from affected files"
    $report += "`n"
    $report += "2. REMOVAL:"
    $report += "`n   - Remove sensitive information from affected files immediately"
    $report += "`n   - Use git-filter-repo (recommended) or git filter-branch to remove from history if already committed"
    $report += "`n   - Existing scripts: scripts/security/remove-secrets.ps1, scripts/security/replace-secrets-in-history.ps1"
    $report += "`n   - WARNING: History rewriting requires coordination with team before force pushing"
    $report += "`n"
    $report += "3. PREVENTION:"
    $report += "`n   - Use environment variables instead of hardcoding secrets"
    $report += "`n   - Use secret management services (AWS Secrets Manager, Azure Key Vault)"
    $report += "`n   - Never commit actual credentials, only use placeholders in code"
    $report += "`n   - Use git-secrets or pre-commit hooks to prevent future commits"
    $report += "`n   - Review batch files before committing"
    $report += "`n"
}

$report += "`n`n=========================================="
$report += "`nEnd of Report"
$report += "`n=========================================="

# Write report to file
$report | Out-File -FilePath $OutputFile -Encoding UTF8

Write-Host "Report saved to: $OutputFile" -ForegroundColor Green

# Generate markdown list of affected files
if ($findings.Count -gt 0) {
    Write-Host "Generating affected files list..." -ForegroundColor Cyan
    
    $mdContent = @"
# Affected Files with Sensitive Information

**Generated:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Total Files Affected:** $($findingsByFile.Count)
**Total Findings:** $($findings.Count)

## Files Requiring Attention

"@
    
    # Group findings by file and source
    $filesBySource = @{}
    foreach ($group in $findingsByFile) {
        $filePath = $group.Name
        $fileFindings = $group.Group
        $source = $fileFindings[0].Source
        
        if (-not $filesBySource.ContainsKey($source)) {
            $filesBySource[$source] = @()
        }
        
        # Count findings by type for this file
        $fileSecretTypes = @{}
        foreach ($finding in $fileFindings) {
            if (-not $fileSecretTypes.ContainsKey($finding.Description)) {
                $fileSecretTypes[$finding.Description] = 0
            }
            $fileSecretTypes[$finding.Description]++
        }
        
        $secretTypesList = ($fileSecretTypes.Keys | ForEach-Object { "$_ ($($fileSecretTypes[$_]))" }) -join ", "
        
        $filesBySource[$source] += @{
            Path = $filePath
            Count = $fileFindings.Count
            Types = $secretTypesList
            CommitHash = $fileFindings[0].CommitHash
            CommitInfo = $fileFindings[0].CommitInfo
        }
    }
    
    # Organize by source
    foreach ($source in $filesBySource.Keys | Sort-Object) {
        $files = $filesBySource[$source]
        $mdContent += "`n### $source ($($files.Count) files)`n`n"
        
        foreach ($file in $files | Sort-Object Path) {
            $mdContent += "- **$($file.Path)**`n"
            $mdContent += "  - Findings: $($file.Count)`n"
            $mdContent += "  - Types: $($file.Types)`n"
            
            if ($file.CommitHash -and $file.CommitInfo) {
                $hashShort = if ($file.CommitInfo.Hash -and $file.CommitInfo.Hash.Length -ge 8) { $file.CommitInfo.Hash.Substring(0, 8) } else { $file.CommitInfo.Hash }
                $mdContent += "  - Commit: $hashShort ($($file.CommitInfo.Date))`n"
            }
            $mdContent += "`n"
        }
    }
    
    $mdContent += @"

## Summary by Secret Type

"@
    
    foreach ($category in $categoryCounts.Keys | Sort-Object) {
        $description = $patterns[$category].description
        $count = $categoryCounts[$category]
        $mdContent += "- **$description**: $count finding(s)`n"
    }
    
    $mdContent += @"

## Action Required

1. **Review each file** listed above
2. **Remove or rotate** exposed credentials immediately
3. **Use git-filter-repo** to remove from history if already committed
4. **Update affected files** to use environment variables or secret management

## Scripts Available

- `scripts/security/remove-secrets.ps1` - Remove secrets from git history
- `scripts/security/replace-secrets-in-history.ps1` - Replace secrets in git history

---
*This file is auto-generated by audit-batch-files.ps1*
"@
    
    $mdContent | Out-File -FilePath $AffectedFilesList -Encoding UTF8
    Write-Host "Affected files list saved to: $AffectedFilesList" -ForegroundColor Green
    Write-Host ""
}

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
    
    Write-Host "`nFindings by Source:" -ForegroundColor Yellow
    foreach ($source in $sourceCounts.Keys | Sort-Object) {
        $count = $sourceCounts[$source]
        Write-Host "  $source : $count" -ForegroundColor White
    }
    
    Write-Host "`n⚠️  WARNING: Sensitive information found in batch files!" -ForegroundColor Red
    Write-Host "   Review the full report: $OutputFile" -ForegroundColor Yellow
    Write-Host "   Review affected files list: $AffectedFilesList" -ForegroundColor Yellow
    Write-Host "   Rotate all exposed credentials immediately!" -ForegroundColor Red
} else {
    Write-Host "`n✅ No sensitive information found!" -ForegroundColor Green
}

Write-Host ""

