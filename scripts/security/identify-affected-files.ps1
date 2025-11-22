# Identify Files with Sensitive Information
# Scans codebase directly to find which files contain secrets

param(
    [switch]$Verbose
)

Write-Host "Identifying Affected Files" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

# Target file extensions
$targetExtensions = @('.sh', '.ps1', '.html', '.md')

# Patterns that indicate real secrets (not placeholders)
$realSecretPatterns = @{
    'AWS_ACCESS_KEY' = 'AKIA[0-9A-Z]{16}'
    'AWS_SECRET_KEY' = '(?<=AWS_SECRET_ACCESS_KEY[=:]\s*)[A-Za-z0-9/+=]{40,}'
    'REPLICATE_KEY' = 'r8_[A-Za-z0-9]{32,}'
    'OPENAI_KEY' = 'sk-[A-Za-z0-9]{32,}'
    'DATABASE_URL' = 'postgresql[+:]?://[^:]+:[^@\s]+@[^localhost]'
    'PRIVATE_KEY' = '-----BEGIN.*PRIVATE KEY-----'
}

# Exclude patterns (placeholders)
$excludePatterns = @(
    'AKIA_REDACTED',
    'AKIAxxxxxxxx',
    'REDACTED.*',
    'your-.*-key',
    'sk-your-',
    'sk-xxxxxxxx',
    'r8_your-',
    'r8_xxxxxxxx',
    'YOURSECRETKEYGOESHERE',
    'dev-secret-key-change-in-production',
    'postgresql://postgres@localhost',
    'postgresql://user:pass@',
    'postgresql://user:password@localhost'
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
    
    $ext = [System.IO.Path]::GetExtension($filePath)
    return $targetExtensions -contains $ext
}

# Get repository root
$repoRoot = git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) {
    $repoRoot = (Get-Location).Path
}

Write-Host "Scanning: $repoRoot" -ForegroundColor Gray
Write-Host ""

# Get all target files
$allFiles = Get-ChildItem -Path $repoRoot -Recurse -File | Where-Object {
    Test-IsTargetFile $_.FullName
}

$affectedFiles = @{}

Write-Host "Scanning $($allFiles.Count) files..." -ForegroundColor Yellow
Write-Host ""

$fileCount = 0
foreach ($file in $allFiles) {
    $fileCount++
    if ($fileCount % 50 -eq 0) {
        Write-Progress -Activity "Scanning files" -Status "Processed $fileCount of $($allFiles.Count)" -PercentComplete (($fileCount / $allFiles.Count) * 100)
    }
    
    $relativePath = $file.FullName.Replace($repoRoot, '') -replace '^[\\/]+', ''
    
    # Skip .git and node_modules
    if ($relativePath -like '*\.git\*' -or $relativePath -like '*\node_modules\*') {
        continue
    }
    
    try {
        $content = Get-Content -Path $file.FullName -Raw -ErrorAction Stop
        
        $fileFindings = @()
        
        foreach ($patternName in $realSecretPatterns.Keys) {
            $pattern = $realSecretPatterns[$patternName]
            $matches = [regex]::Matches($content, $pattern)
            
            foreach ($match in $matches) {
                $value = $match.Value
                
                # Skip placeholders
                if (Test-IsPlaceholder $value) {
                    continue
                }
                
                # Special check for AWS key (redacted example - replace with actual key if needed)
                if ($patternName -eq 'AWS_ACCESS_KEY' -and $value -match 'AKIA[0-9A-Z]{16}') {
                    $fileFindings += @{
                        Type = $patternName
                        Value = $value
                        Line = ($content.Substring(0, $match.Index) -split "`r?`n").Count
                    }
                } elseif ($patternName -ne 'AWS_ACCESS_KEY') {
                    # For other patterns, check if it looks real
                    if ($value.Length -gt 20 -and $value -notmatch '(REDACTED|placeholder|example|your-|xxxx)') {
                        $fileFindings += @{
                            Type = $patternName
                            Value = $value.Substring(0, [Math]::Min(30, $value.Length))
                            Line = ($content.Substring(0, $match.Index) -split "`r?`n").Count
                        }
                    }
                }
            }
        }
        
        if ($fileFindings.Count -gt 0) {
            $affectedFiles[$relativePath] = $fileFindings
        }
    } catch {
        if ($Verbose) {
            Write-Host "  Warning: Could not read $relativePath" -ForegroundColor Yellow
        }
    }
}

Write-Progress -Activity "Scanning files" -Completed

Write-Host "Scan complete!" -ForegroundColor Green
Write-Host ""

# Generate report
$report = @"
# Files That Need to Be Fixed

**Generated:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Total Files Affected:** $($affectedFiles.Count)

## Files Requiring Immediate Attention

"@

if ($affectedFiles.Count -eq 0) {
    $report += "`n✅ **No files with real secrets found in current codebase!**`n`n"
    $report += "All findings are likely in git history or are false positives.`n"
} else {
    # Group by file
    foreach ($filePath in $affectedFiles.Keys | Sort-Object) {
        $findings = $affectedFiles[$filePath]
        
        $report += "`n### $filePath`n`n"
        $report += "**Findings:** $($findings.Count)`n`n"
        
        $findingsByType = $findings | Group-Object Type
        foreach ($typeGroup in $findingsByType) {
            $report += "- **$($typeGroup.Name)**: $($typeGroup.Count) occurrence(s)`n"
            
            # Show sample lines
            $samples = $typeGroup.Group | Select-Object -First 3
            foreach ($finding in $samples) {
                $preview = if ($finding.Value.Length -gt 40) { $finding.Value.Substring(0, 40) + "..." } else { $finding.Value }
                $report += "  - Line ~$($finding.Line): `"$preview`"`n"
            }
            if ($typeGroup.Count -gt 3) {
                $report += "  - ... and $($typeGroup.Count - 3) more`n"
            }
        }
        
        $report += "`n"
    }
    
    # Summary by type
    $report += @"

## Summary by Secret Type

"@
    
    $allFindings = $affectedFiles.Values | ForEach-Object { $_ }
    $typeSummary = $allFindings | Group-Object Type
    
    foreach ($typeGroup in $typeSummary | Sort-Object Count -Descending) {
        $report += "- **$($typeGroup.Name)**: Found in $($typeGroup.Count) location(s) across $($affectedFiles.Keys | Where-Object { $affectedFiles[$_] | Where-Object { $_.Type -eq $typeGroup.Name } } | Measure-Object).Count file(s)`n"
    }
}

$report += @"

## What to Do

1. **Review each file listed above**
2. **Check if the secrets are real or placeholders**
3. **If real:**
   - Remove the hardcoded secret
   - Replace with environment variable
   - Update code to read from environment
4. **If placeholder:**
   - No action needed (these are examples)

## Priority Files

Files with **AWS Access Keys** should be checked first. Any exposed keys should be rotated immediately.

---
*Review each file manually to determine if secrets are real or examples.*
"@

$outputFile = "files-to-fix.md"
$report | Out-File -FilePath $outputFile -Encoding UTF8

Write-Host "Report generated: $outputFile" -ForegroundColor Green
Write-Host ""
Write-Host "Files that need review: $($affectedFiles.Count)" -ForegroundColor $(if ($affectedFiles.Count -eq 0) { "Green" } else { "Yellow" })

if ($affectedFiles.Count -gt 0) {
    Write-Host "`nAffected files:" -ForegroundColor Yellow
    foreach ($filePath in $affectedFiles.Keys | Sort-Object) {
        $count = $affectedFiles[$filePath].Count
        Write-Host "  - $filePath ($count finding(s))" -ForegroundColor White
    }
}

Write-Host ""

