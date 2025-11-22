# Analyze Security Audit Findings
# Helps categorize findings as real secrets vs false positives

param(
    [string]$ReportFile = "batch-files-security-audit-report.txt",
    [string]$OutputFile = "findings-analysis.md"
)

Write-Host "Analyzing Security Audit Findings" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $ReportFile)) {
    Write-Host "Error: Report file not found: $ReportFile" -ForegroundColor Red
    exit 1
}

$content = Get-Content -Path $ReportFile -Raw
$findings = @()

# Parse the report
$lines = $content -split "`r?`n"
$currentFile = $null
$currentSource = $null
$inDetailedSection = $false

for ($i = 0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]
    
    if ($line -match '^DETAILED FINDINGS') {
        $inDetailedSection = $true
        continue
    }
    
    if ($inDetailedSection) {
        if ($line -match '^File:\s*(.+)$') {
            $currentFile = $matches[1].Trim()
            continue
        }
        
        if ($line -match 'Source:\s*(.+)$') {
            $currentSource = $matches[1].Trim()
            continue
        }
        
        if ($line -match 'Line:\s*(\d+)$') {
            $lineNum = [int]$matches[1]
            $finding = @{
                File = $currentFile
                Source = $currentSource
                Line = $lineNum
                Type = $null
                Preview = $null
            }
            
            # Get next few lines for type and preview
            if ($i + 1 -lt $lines.Count -and $lines[$i + 1] -match 'Type:\s*(.+)$') {
                $finding.Type = $matches[1].Trim()
            }
            if ($i + 2 -lt $lines.Count -and $lines[$i + 2] -match 'Preview:\s*(.+)$') {
                $finding.Preview = $matches[1].Trim()
            }
            
            $findings += $finding
        }
    }
}

Write-Host "Found $($findings.Count) findings to analyze" -ForegroundColor Yellow
Write-Host ""

# Categorize findings
$realSecrets = @()
$falsePositives = @()
$needsReview = @()

# Patterns that are definitely false positives
$falsePositivePatterns = @(
    'pwd_context\.hash',
    'Type\.String',
    'v\.string',
    'z\.number',
    'Schema\.String',
    'vine\.string',
    'your-together-ai',
    'your-openai-api-key',
    'sk-your-',
    'sk-xxxxxxxx',
    'YOURSECRETKEYGOESHERE',
    'dev-secret-key-change-in-production',
    'postgresql://user:pass@',
    'postgresql://user:password@',
    'postgresql://postgres:password',
    'AKIA_REDACTED',
    'REDACTED.*'
)

# Patterns that are likely real secrets
$realSecretPatterns = @(
    'AKIA[0-9A-Z]{16}',  # AWS keys (but exclude placeholders)
    'sk-[a-zA-Z0-9]{32,}',  # OpenAI keys (long ones)
    'r8_[a-zA-Z0-9]{32,}',  # Replicate keys (long ones)
    '-----BEGIN.*PRIVATE KEY-----'
)

foreach ($finding in $findings) {
    $isFalsePositive = $false
    $isRealSecret = $false
    
    # Check against false positive patterns
    foreach ($pattern in $falsePositivePatterns) {
        if ($finding.Preview -match $pattern) {
            $isFalsePositive = $true
            break
        }
    }
    
    # Check against real secret patterns (but exclude known placeholders)
    if (-not $isFalsePositive) {
        foreach ($pattern in $realSecretPatterns) {
            if ($finding.Preview -match $pattern) {
                # Additional check: exclude if it's a placeholder
                if ($finding.Preview -notmatch '(REDACTED|placeholder|example|your-|xxxx)') {
                    $isRealSecret = $true
                    break
                }
            }
        }
    }
    
    # Special case: AWS keys (check for real AWS key pattern)
    if ($finding.Preview -match 'AKIA[0-9A-Z]{16}' -and $finding.Preview -notmatch 'REDACTED|EXAMPLE|PLACEHOLDER') {
        $isRealSecret = $true
    }
    
    if ($isFalsePositive) {
        $falsePositives += $finding
    } elseif ($isRealSecret) {
        $realSecrets += $finding
    } else {
        $needsReview += $finding
    }
}

# Generate analysis report
$analysis = @"
# Security Findings Analysis

**Generated:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Report Source:** $ReportFile

## Summary

- **Total Findings:** $($findings.Count)
- **Real Secrets (Action Required):** $($realSecrets.Count)
- **False Positives:** $($falsePositives.Count)
- **Needs Manual Review:** $($needsReview.Count)

## Real Secrets Requiring Immediate Action

**Priority: CRITICAL** - These appear to be actual secrets that need to be rotated/removed.

"@

if ($realSecrets.Count -gt 0) {
    $analysis += "`n### Count by Type:`n`n"
    $realSecretsByType = $realSecrets | Group-Object Type
    foreach ($group in $realSecretsByType | Sort-Object Count -Descending) {
        $analysis += "- **$($group.Name)**: $($group.Count) finding(s)`n"
    }
    
    $analysis += "`n### Files with Real Secrets:`n`n"
    $realSecretsByFile = $realSecrets | Group-Object File
    foreach ($group in $realSecretsByFile | Sort-Object Count -Descending) {
        $file = $group.Name
        if ([string]::IsNullOrWhiteSpace($file)) {
            $file = "(File path missing - check report)"
        }
        $analysis += "- **$file** ($($group.Count) finding(s))`n"
        $analysis += "  - Source: $($group.Group[0].Source)`n"
        $analysis += "  - Types: $(($group.Group | Select-Object -Unique Type | ForEach-Object { $_.Type }) -join ', ')`n"
        $analysis += "`n"
    }
    
    # Highlight AWS keys
    $awsKeyFindings = $realSecrets | Where-Object { $_.Preview -match 'AKIA[0-9A-Z]{16}' -and $_.Preview -notmatch 'REDACTED' }
    if ($awsKeyFindings.Count -gt 0) {
        $analysis += @"

### CRITICAL: AWS Access Key Found

**Occurrences:** $($awsKeyFindings.Count)  
**Action Required:** 
1. Verify if this is a real, active AWS key
2. If real: Rotate immediately in AWS Console
3. Remove from all files and git history
4. Update all services using this key

"@
    }
} else {
    $analysis += "`n✅ No obvious real secrets detected in automated analysis.`n"
}

$analysis += @"

## False Positives

These are likely not real secrets (variable names, placeholders, examples):

"@

if ($falsePositives.Count -gt 0) {
    $analysis += "`n**Total:** $($falsePositives.Count) finding(s)`n`n"
    $analysis += "**Recommendation:** Update audit script exclusion patterns to filter these out.`n`n"
    
    $falsePosByType = $falsePositives | Group-Object Type
    foreach ($group in $falsePosByType | Sort-Object Count -Descending) {
        $analysis += "- **$($group.Name)**: $($group.Count) finding(s)`n"
    }
} else {
    $analysis += "`n✅ No false positives detected.`n"
}

$analysis += @"

## Needs Manual Review

These findings require human review to determine if they're real secrets:

"@

if ($needsReview.Count -gt 0) {
    $analysis += "`n**Total:** $($needsReview.Count) finding(s)`n`n"
    
    $reviewByType = $needsReview | Group-Object Type
    foreach ($group in $reviewByType | Sort-Object Count -Descending) {
        $analysis += "`n### $($group.Name) ($($group.Count) finding(s))`n`n"
        
        $sampleFindings = $group.Group | Select-Object -First 5
        foreach ($finding in $sampleFindings) {
            $file = $finding.File
            if ([string]::IsNullOrWhiteSpace($file)) {
                $file = "(File path missing)"
            }
            $analysis += "- File: `$file`n"
            $analysis += "  - Line: $($finding.Line)`n"
            $analysis += "  - Preview: $($finding.Preview)`n"
            $analysis += "  - Source: $($finding.Source)`n"
            $analysis += "`n"
        }
        
        if ($group.Count -gt 5) {
            $analysis += "*... and $($group.Count - 5) more*`n`n"
        }
    }
} else {
    $analysis += "`n✅ No findings require manual review.`n"
}

$analysis += @"

## Recommendations

### Immediate Actions

1. **Review Real Secrets Section** - Rotate/remove all identified real secrets
2. **Review Manual Review Section** - Determine if these are real secrets
3. **Update Exclusion Patterns** - Add false positive patterns to audit script

### Next Steps

1. Fix current codebase files (if any real secrets found)
2. Clean git history using git-filter-repo
3. Rotate all exposed credentials
4. Update audit script to reduce false positives

### Scripts to Use

- `scripts/security/remove-secrets.ps1` - Remove from git history
- `scripts/security/replace-secrets-in-history.ps1` - Replace in git history
- `git filter-repo` - Recommended tool for history cleanup

---
*This analysis is automated and may contain errors. Always manually verify findings before taking action.*
"@

$analysis | Out-File -FilePath $OutputFile -Encoding UTF8

Write-Host "Analysis complete!" -ForegroundColor Green
Write-Host "Results saved to: $OutputFile" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Real Secrets: $($realSecrets.Count)" -ForegroundColor $(if ($realSecrets.Count -gt 0) { "Red" } else { "Green" })
Write-Host "  False Positives: $($falsePositives.Count)" -ForegroundColor Yellow
Write-Host "  Needs Review: $($needsReview.Count)" -ForegroundColor Yellow
Write-Host ""

