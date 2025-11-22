# Test script to validate regex patterns against known examples
# This helps ensure patterns catch real secrets but exclude placeholders

Write-Host "Testing Audit Patterns" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan
Write-Host ""

# Define patterns (same as in audit script)
$patterns = @{
    'AWS_ACCESS_KEY' = 'AKIA[0-9A-Z]{16}'
    'AWS_SECRET_KEY' = '(?<=AWS_SECRET_ACCESS_KEY[=:]\s*)[A-Za-z0-9/+=]{40,}'
    'REPLICATE_KEY' = 'r8_[A-Za-z0-9]{20,}'
    'OPENAI_KEY' = 'sk-[A-Za-z0-9]{20,}'
    'DATABASE_URL' = 'postgresql[+:]?://[^:]+:[^@\s]+@'
}

# Test cases: @{input, shouldMatch, description}
$testCases = @(
    # AWS Access Keys
    @{input='AKIAIOSFODNN7EXAMPLE'; shouldMatch=$true; description='Valid AWS Access Key'},
    @{input='AKIAxxxxxxxxxxxxx'; shouldMatch=$false; description='Placeholder AWS Key'},
    @{input='AKIA_REDACTED_AWS_ACCESS_KEY'; shouldMatch=$false; description='Redacted AWS Key'},
    
    # AWS Secret Keys
    @{input='AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'; shouldMatch=$true; description='Valid AWS Secret Key'},
    @{input='AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'; shouldMatch=$false; description='Placeholder AWS Secret'},
    @{input='AWS_SECRET_ACCESS_KEY=REDACTED_AWS_SECRET_KEY'; shouldMatch=$false; description='Redacted AWS Secret'},
    
    # Replicate Keys
    @{input='r8_abc123def456ghi789jkl012mno345pqr678stu901vwx234yz'; shouldMatch=$true; description='Valid Replicate Key'},
    @{input='r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'; shouldMatch=$false; description='Placeholder Replicate Key'},
    @{input='r8_your-replicate-key-here'; shouldMatch=$false; description='Example Replicate Key'},
    @{input='r8_REDACTED_REPLICATE_API_KEY'; shouldMatch=$false; description='Redacted Replicate Key'},
    
    # OpenAI Keys
    @{input='sk-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz'; shouldMatch=$true; description='Valid OpenAI Key'},
    @{input='sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'; shouldMatch=$false; description='Placeholder OpenAI Key'},
    @{input='sk-your-openai-key-here'; shouldMatch=$false; description='Example OpenAI Key'},
    
    # Database URLs
    @{input='postgresql://user:password123@host:5432/dbname'; shouldMatch=$true; description='Database URL with password'},
    @{input='postgresql://postgres@localhost:5432/dbname'; shouldMatch=$false; description='Database URL without password'},
    @{input='postgresql+psycopg://postgres@localhost:5432/gauntlet_pipeline'; shouldMatch=$false; description='Local database without password'},
    @{input='postgresql://user:pass@localhost:5432/db'; shouldMatch=$true; description='Database URL with short password'}
)

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
    'postgresql://postgres@',
    'postgresql://.*@localhost',
    'postgresql\+psycopg://postgres@'
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

$passed = 0
$failed = 0

foreach ($testCase in $testCases) {
    $input = $testCase.input
    $expectedMatch = $testCase.shouldMatch
    $description = $testCase.description
    
    # Determine which pattern to test
    $patternToTest = $null
    $patternName = $null
    
    if ($input -match '^AKIA') {
        $patternName = 'AWS_ACCESS_KEY'
        $patternToTest = $patterns['AWS_ACCESS_KEY']
    } elseif ($input -match 'AWS_SECRET_ACCESS_KEY') {
        $patternName = 'AWS_SECRET_KEY'
        $patternToTest = $patterns['AWS_SECRET_KEY']
    } elseif ($input -match '^r8_') {
        $patternName = 'REPLICATE_KEY'
        $patternToTest = $patterns['REPLICATE_KEY']
    } elseif ($input -match '^sk-') {
        $patternName = 'OPENAI_KEY'
        $patternToTest = $patterns['OPENAI_KEY']
    } elseif ($input -match 'postgresql') {
        $patternName = 'DATABASE_URL'
        $patternToTest = $patterns['DATABASE_URL']
    }
    
    if (-not $patternToTest) {
        Write-Host "⚠️  Could not determine pattern for: $input" -ForegroundColor Yellow
        continue
    }
    
    # Test pattern match
    $matches = $input -match $patternToTest
    $isPlaceholder = Test-IsPlaceholder $input
    
    # For database URLs, additional validation
    if ($patternName -eq 'DATABASE_URL' -and $matches) {
        if ($input -notmatch ':[^@]+@') {
            $matches = $false
        }
        if ($input -match '@localhost' -and $input -notmatch ':[^@]+@') {
            $matches = $false
        }
    }
    
    # Final result: should match pattern AND not be a placeholder
    $actualResult = $matches -and (-not $isPlaceholder)
    
    if ($actualResult -eq $expectedMatch) {
        Write-Host "✅ PASS: $description" -ForegroundColor Green
        Write-Host "   Input: $($input.Substring(0, [Math]::Min(60, $input.Length)))" -ForegroundColor Gray
        $passed++
    } else {
        Write-Host "❌ FAIL: $description" -ForegroundColor Red
        Write-Host "   Input: $input" -ForegroundColor Gray
        Write-Host "   Expected: $expectedMatch, Got: $actualResult" -ForegroundColor Yellow
        Write-Host "   Pattern matched: $matches, Is placeholder: $isPlaceholder" -ForegroundColor Yellow
        $failed++
    }
}

Write-Host ""
Write-Host "Test Results" -ForegroundColor Cyan
Write-Host "------------" -ForegroundColor Cyan
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($failed -eq 0) {
    Write-Host "✅ All pattern tests passed!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some tests failed. Review patterns before running audit." -ForegroundColor Yellow
}

