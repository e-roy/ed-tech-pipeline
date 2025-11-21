[CmdletBinding()]
param(
    [string]$SourceProfile = "default1",
    [string]$SourceRegion = "us-east-1",
    [string]$DestProfile = "default2",
    [string]$DestRegion = "us-east-2",
    [string]$BucketName = "pipeline-backend-assets",
    [switch]$DryRun,
    [switch]$SkipBucketCreation
)

$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [string]$Title,
        [ScriptBlock]$Action
    )
    Write-Host ""
    Write-Host "==> $Title" -ForegroundColor Cyan
    & $Action
}

function Invoke-AwsCommand {
    param(
        [string[]]$Arguments,
        [string]$Profile,
        [string]$Region,
        [switch]$ParseJson
    )

    $baseArgs = @("--profile", $Profile, "--region", $Region) + $Arguments
    $output = & aws @baseArgs 2>&1

    if ($LASTEXITCODE -ne 0) {
        throw "AWS CLI command failed: aws $($Arguments -join ' ')`n$output"
    }

    if ($ParseJson) {
        return $output | ConvertFrom-Json
    }

    return $output
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "S3 Bucket Migration Script" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Source: Profile=$SourceProfile, Region=$SourceRegion" -ForegroundColor Yellow
Write-Host "Destination: Profile=$DestProfile, Region=$DestRegion" -ForegroundColor Yellow
Write-Host "Bucket: $BucketName" -ForegroundColor Yellow
if ($DryRun) {
    Write-Host "Mode: DRY RUN (no changes will be made)" -ForegroundColor Cyan
}
Write-Host ""

# Verify AWS CLI is available
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    throw "AWS CLI not found. Please install AWS CLI first."
}

# Verify source bucket exists
Invoke-Step "Verifying source bucket exists" {
    try {
        $bucketInfo = Invoke-AwsCommand -Arguments @("s3api", "head-bucket", "--bucket", $BucketName) -Profile $SourceProfile -Region $SourceRegion
        Write-Host "Source bucket found: $BucketName" -ForegroundColor Green
    } catch {
        throw "Source bucket '$BucketName' not found in region $SourceRegion with profile $SourceProfile"
    }
}

# Create destination bucket if needed
if (-not $SkipBucketCreation) {
    Invoke-Step "Ensuring destination bucket exists" {
        try {
            $destBucketInfo = Invoke-AwsCommand -Arguments @("s3api", "head-bucket", "--bucket", $BucketName) -Profile $DestProfile -Region $DestRegion
            Write-Host "Destination bucket already exists: $BucketName" -ForegroundColor Green
        } catch {
            if ($DryRun) {
                Write-Host "Would create destination bucket: $BucketName" -ForegroundColor Yellow
            } else {
                Write-Host "Creating destination bucket: $BucketName"
                Invoke-AwsCommand -Arguments @("s3", "mb", "s3://$BucketName") -Profile $DestProfile -Region $DestRegion
                Write-Host "Destination bucket created" -ForegroundColor Green
            }
        }
    }
}

# List all objects in source bucket
Invoke-Step "Listing objects in source bucket" {
    $allObjects = @()
    $continuationToken = $null
    
    do {
        $listArgs = @("s3api", "list-objects-v2", "--bucket", $BucketName, "--max-items", "1000")
        if ($continuationToken) {
            $listArgs += @("--continuation-token", $continuationToken)
        }
        
        $response = Invoke-AwsCommand -Arguments $listArgs -Profile $SourceProfile -Region $SourceRegion -ParseJson
        
        if ($response.Contents) {
            $allObjects += $response.Contents
        }
        
        $continuationToken = $response.NextContinuationToken
    } while ($continuationToken)
    
    Write-Host "Found $($allObjects.Count) objects in source bucket"
    
    if ($allObjects.Count -eq 0) {
        Write-Host "No objects to migrate. Exiting." -ForegroundColor Yellow
        exit 0
    }
    
    # Calculate total size
    $totalSize = ($allObjects | Measure-Object -Property Size -Sum).Sum
    $totalSizeGB = [math]::Round($totalSize / 1GB, 2)
    Write-Host "Total size: $totalSizeGB GB"
}

# Migrate objects
Invoke-Step "Migrating objects to destination bucket" {
    $successCount = 0
    $failCount = 0
    $skippedCount = 0
    
    foreach ($obj in $allObjects) {
        $key = $obj.Key
        $sizeMB = [math]::Round($obj.Size / 1MB, 2)
        
        # Check if object already exists in destination
        try {
            $destObj = Invoke-AwsCommand -Arguments @("s3api", "head-object", "--bucket", $BucketName, "--key", $key) -Profile $DestProfile -Region $DestRegion -ParseJson
            Write-Host "Skipping $key (already exists in destination)" -ForegroundColor Gray
            $skippedCount++
            continue
        } catch {
            # Object doesn't exist, proceed with migration
        }
        
        $sizeText = "$sizeMB MB"
        Write-Host "Migrating: $key ($sizeText)" -ForegroundColor White
        
        if ($DryRun) {
            Write-Host "   [DRY RUN] Would copy: s3://$BucketName/$key" -ForegroundColor Cyan
            $successCount++
        } else {
            try {
                # Use AWS S3 sync or copy command
                # Copy from source to destination using cross-region copy
                $copyArgs = @(
                    "s3", "cp",
                    "s3://$BucketName/$key",
                    "s3://$BucketName/$key",
                    "--source-region", $SourceRegion,
                    "--region", $DestRegion,
                    "--profile", $DestProfile
                )
                
                # Note: Cross-account/cross-profile copy requires proper credentials
                # Alternative: Download from source and upload to destination
                $tempFile = [System.IO.Path]::GetTempFileName()
                
                # Download from source
                Invoke-AwsCommand -Arguments @("s3", "cp", "s3://$BucketName/$key", $tempFile) -Profile $SourceProfile -Region $SourceRegion | Out-Null
                
                # Upload to destination
                Invoke-AwsCommand -Arguments @("s3", "cp", $tempFile, "s3://$BucketName/$key") -Profile $DestProfile -Region $DestRegion | Out-Null
                
                # Clean up temp file
                Remove-Item $tempFile -ErrorAction SilentlyContinue
                
                Write-Host "   Migrated successfully" -ForegroundColor Green
                $successCount++
            } catch {
                Write-Host "   Failed: $_" -ForegroundColor Red
                $failCount++
            }
        }
    }
    
    Write-Host ""
    Write-Host "Migration Summary:" -ForegroundColor Cyan
    Write-Host "  Success: $successCount" -ForegroundColor Green
    Write-Host "  Skipped: $skippedCount" -ForegroundColor Yellow
    if ($failCount -gt 0) {
        Write-Host "  Failed: $failCount" -ForegroundColor Red
    }
}

# Copy bucket configuration (CORS, policy, etc.)
Invoke-Step "Copying bucket configuration" {
    if ($DryRun) {
        Write-Host "[DRY RUN] Would copy bucket policies and CORS configuration" -ForegroundColor Cyan
    } else {
        # Copy CORS configuration
        try {
            $corsConfig = Invoke-AwsCommand -Arguments @("s3api", "get-bucket-cors", "--bucket", $BucketName) -Profile $SourceProfile -Region $SourceRegion -ParseJson
            $corsFile = [System.IO.Path]::GetTempFileName()
            $corsConfig | ConvertTo-Json -Depth 10 | Out-File -FilePath $corsFile -Encoding UTF8
            
            Invoke-AwsCommand -Arguments @("s3api", "put-bucket-cors", "--bucket", $BucketName, "--cors-configuration", "file://$corsFile") -Profile $DestProfile -Region $DestRegion | Out-Null
            Remove-Item $corsFile
            Write-Host "CORS configuration copied" -ForegroundColor Green
        } catch {
            Write-Host "Could not copy CORS configuration (may not exist): $_" -ForegroundColor Yellow
        }
        
        # Copy bucket policy
        try {
            $policy = Invoke-AwsCommand -Arguments @("s3api", "get-bucket-policy", "--bucket", $BucketName) -Profile $SourceProfile -Region $SourceRegion -ParseJson
            $policyFile = [System.IO.Path]::GetTempFileName()
            $policy.Policy | Out-File -FilePath $policyFile -Encoding UTF8
            
            Invoke-AwsCommand -Arguments @("s3api", "put-bucket-policy", "--bucket", $BucketName, "--policy", "file://$policyFile") -Profile $DestProfile -Region $DestRegion | Out-Null
            Remove-Item $policyFile
            Write-Host "Bucket policy copied" -ForegroundColor Green
        } catch {
            Write-Host "Could not copy bucket policy (may not exist): $_" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Migration Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Verify objects in destination bucket:"
Write-Host "     aws s3 ls s3://$BucketName --profile $DestProfile --region $DestRegion --recursive"
Write-Host ""
Write-Host "  2. Update your .env files to use:"
Write-Host "     AWS_REGION=$DestRegion"
Write-Host ""
Write-Host "  3. Test your application with the new region"
Write-Host ""
Write-Host "  4. Once verified, you can delete the source bucket (optional):"
Write-Host "     aws s3 rb s3://$BucketName --profile $SourceProfile --region $SourceRegion --force"
Write-Host ""

