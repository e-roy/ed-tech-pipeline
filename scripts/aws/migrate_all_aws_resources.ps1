[CmdletBinding()]
param(
    [string]$SourceProfile = "default1",
    [string]$SourceRegion = "us-east-1",
    [string]$DestProfile = "default2",
    [string]$DestRegion = "us-east-2",
    [string]$BucketName = "pipeline-backend-assets",
    [string]$EcsClusterName = "pipeline-backend",
    [string]$EcsServiceName = "pipeline-backend-service",
    [string]$EcrRepositoryName = "pipeline-backend",
    [switch]$DryRun,
    [switch]$SkipS3,
    [switch]$SkipECS,
    [switch]$SkipECR
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
        [switch]$ParseJson,
        [switch]$AllowFailure
    )

    $baseArgs = @("--profile", $Profile)
    if ($Region) {
        $baseArgs += @("--region", $Region)
    }
    $baseArgs += $Arguments
    
    $output = & aws @baseArgs 2>&1

    if ($LASTEXITCODE -ne 0) {
        if ($AllowFailure) {
            return $null
        }
        $errorMsg = if ($output -is [string]) { $output } else { ($output | Out-String) }
        throw "AWS CLI command failed: aws $($Arguments -join ' ')`nExit Code: $LASTEXITCODE`n$errorMsg"
    }

    if ($ParseJson) {
        return $output | ConvertFrom-Json
    }

    return $output
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "Complete AWS Resource Migration Script" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Source: Profile=$SourceProfile, Region=$SourceRegion" -ForegroundColor Yellow
Write-Host "Destination: Profile=$DestProfile, Region=$DestRegion" -ForegroundColor Yellow
if ($DryRun) {
    Write-Host "Mode: DRY RUN (no changes will be made)" -ForegroundColor Cyan
}
Write-Host ""

# Verify AWS CLI is available
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    throw "AWS CLI not found. Please install AWS CLI first."
}

# ============================================================================
# S3 BUCKET MIGRATION
# ============================================================================
if (-not $SkipS3) {
    Invoke-Step "S3 Bucket Migration" {
        # Check if source bucket exists
        Write-Host "Checking source bucket..." -ForegroundColor Gray
        try {
            $sourceBucket = Invoke-AwsCommand -Arguments @("s3api", "head-bucket", "--bucket", $BucketName) -Profile $SourceProfile -Region $SourceRegion -AllowFailure
            if ($null -eq $sourceBucket) {
                Write-Host "Source bucket not found, skipping S3 migration" -ForegroundColor Yellow
                return
            }
            Write-Host "Source bucket found: $BucketName" -ForegroundColor Green
        } catch {
            Write-Host "Source bucket not found, skipping S3 migration" -ForegroundColor Yellow
            return
        }

        # Get bucket configuration before migration
        Write-Host "Retrieving bucket configuration..." -ForegroundColor Gray
        $corsConfig = $null
        $bucketPolicy = $null
        
        try {
            $corsConfig = Invoke-AwsCommand -Arguments @("s3api", "get-bucket-cors", "--bucket", $BucketName) -Profile $SourceProfile -Region $SourceRegion -ParseJson -AllowFailure
        } catch {
            Write-Host "No CORS configuration found" -ForegroundColor Gray
        }
        
        try {
            $policy = Invoke-AwsCommand -Arguments @("s3api", "get-bucket-policy", "--bucket", $BucketName) -Profile $SourceProfile -Region $SourceRegion -ParseJson -AllowFailure
            if ($null -ne $policy) {
                $bucketPolicy = $policy.Policy
            }
        } catch {
            Write-Host "No bucket policy found" -ForegroundColor Gray
        }

        # Generate temporary bucket name
        $tempBucketName = "$BucketName-temp-migration-$(Get-Date -Format 'yyyyMMddHHmmss')"
        
        if ($DryRun) {
            Write-Host "[DRY RUN] Migration plan:" -ForegroundColor Cyan
            Write-Host "  1. Create temp bucket: $tempBucketName" -ForegroundColor Cyan
            Write-Host "  2. Sync data from $BucketName (us-east-1) to $tempBucketName (us-east-2)" -ForegroundColor Cyan
            Write-Host "  3. Delete old bucket: $BucketName (us-east-1)" -ForegroundColor Cyan
            Write-Host "  4. Recreate bucket: $BucketName (us-east-2)" -ForegroundColor Cyan
            Write-Host "  5. Sync data from $tempBucketName to $BucketName" -ForegroundColor Cyan
            Write-Host "  6. Delete temp bucket: $tempBucketName" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "  WARNING: This will delete the source bucket!" -ForegroundColor Red
            return
        }

        # Step 1: Create temporary bucket in us-east-2
        Write-Host "Step 1: Creating temporary bucket: $tempBucketName" -ForegroundColor Yellow
        try {
            Invoke-AwsCommand -Arguments @("s3", "mb", "s3://$tempBucketName") -Profile $DestProfile -Region $DestRegion
            Write-Host "Temporary bucket created" -ForegroundColor Green
        } catch {
            Write-Host "Failed to create temporary bucket: $_" -ForegroundColor Red
            throw
        }

        # Step 2: Sync data from old bucket to temp bucket
        Write-Host "Step 2: Syncing data from $BucketName (us-east-1) to $tempBucketName (us-east-2)..." -ForegroundColor Yellow
        Write-Host "This may take a while depending on bucket size..." -ForegroundColor Gray
        try {
            Invoke-AwsCommand -Arguments @(
                "s3", "sync",
                "s3://$BucketName",
                "s3://$tempBucketName",
                "--source-region", $SourceRegion,
                "--region", $DestRegion
            ) -Profile $DestProfile
            Write-Host "Data sync completed" -ForegroundColor Green
        } catch {
            Write-Host "Failed to sync data: $_" -ForegroundColor Red
            Write-Host "Cleaning up temporary bucket..." -ForegroundColor Yellow
            Invoke-AwsCommand -Arguments @("s3", "rb", "s3://$tempBucketName", "--force") -Profile $DestProfile -Region $DestRegion -AllowFailure | Out-Null
            throw
        }

        # Verify sync completed
        Write-Host "Verifying sync..." -ForegroundColor Gray
        $sourceCount = (aws s3 ls "s3://$BucketName" --profile $SourceProfile --region $SourceRegion --recursive 2>&1 | Measure-Object -Line).Lines
        $tempCount = (aws s3 ls "s3://$tempBucketName" --profile $DestProfile --region $DestRegion --recursive 2>&1 | Measure-Object -Line).Lines
        Write-Host "Source bucket objects: $sourceCount" -ForegroundColor Cyan
        Write-Host "Temp bucket objects: $tempCount" -ForegroundColor Cyan
        
        if ($sourceCount -ne $tempCount) {
            Write-Host "WARNING: Object count mismatch! Source: $sourceCount, Temp: $tempCount" -ForegroundColor Red
            $continue = Read-Host "Continue anyway? (yes/no)"
            if ($continue -ne "yes") {
                Write-Host "Aborting migration. Temp bucket will be kept for manual verification." -ForegroundColor Yellow
                Write-Host "Temp bucket: $tempBucketName" -ForegroundColor Cyan
                return
            }
        }

        # Step 3: Delete old bucket
        Write-Host "Step 3: Deleting old bucket: $BucketName (us-east-1)..." -ForegroundColor Yellow
        Write-Host "WARNING: This will permanently delete the source bucket!" -ForegroundColor Red
        try {
            # First, empty the bucket
            Write-Host "Emptying bucket..." -ForegroundColor Gray
            Invoke-AwsCommand -Arguments @("s3", "rm", "s3://$BucketName", "--recursive") -Profile $SourceProfile -Region $SourceRegion
            
            # Then delete the bucket
            Invoke-AwsCommand -Arguments @("s3", "rb", "s3://$BucketName", "--force") -Profile $SourceProfile -Region $SourceRegion
            Write-Host "Old bucket deleted" -ForegroundColor Green
        } catch {
            Write-Host "Failed to delete old bucket: $_" -ForegroundColor Red
            Write-Host "You may need to manually delete it later" -ForegroundColor Yellow
        }

        # Step 4: Recreate bucket with original name in us-east-2
        Write-Host "Step 4: Recreating bucket: $BucketName (us-east-2)..." -ForegroundColor Yellow
        try {
            Invoke-AwsCommand -Arguments @("s3", "mb", "s3://$BucketName") -Profile $DestProfile -Region $DestRegion
            Write-Host "Bucket recreated in us-east-2" -ForegroundColor Green
        } catch {
            Write-Host "Failed to recreate bucket: $_" -ForegroundColor Red
            throw
        }

        # Step 5: Copy data back from temp bucket
        Write-Host "Step 5: Syncing data from $tempBucketName to $BucketName..." -ForegroundColor Yellow
        try {
            Invoke-AwsCommand -Arguments @(
                "s3", "sync",
                "s3://$tempBucketName",
                "s3://$BucketName",
                "--region", $DestRegion
            ) -Profile $DestProfile
            Write-Host "Data sync completed" -ForegroundColor Green
        } catch {
            Write-Host "Failed to sync data: $_" -ForegroundColor Red
            throw
        }

        # Step 6: Delete temp bucket
        Write-Host "Step 6: Cleaning up temporary bucket: $tempBucketName..." -ForegroundColor Yellow
        try {
            Invoke-AwsCommand -Arguments @("s3", "rb", "s3://$tempBucketName", "--force") -Profile $DestProfile -Region $DestRegion
            Write-Host "Temporary bucket deleted" -ForegroundColor Green
        } catch {
            Write-Host "Failed to delete temp bucket: $_" -ForegroundColor Yellow
            Write-Host "You may need to manually delete: $tempBucketName" -ForegroundColor Yellow
        }

        # Restore bucket configuration
        Write-Host "Restoring bucket configuration..." -ForegroundColor Gray
        
        if ($null -ne $corsConfig) {
            try {
                $corsFile = [System.IO.Path]::GetTempFileName()
                $corsConfig | ConvertTo-Json -Depth 10 | Out-File -FilePath $corsFile -Encoding UTF8
                Invoke-AwsCommand -Arguments @("s3api", "put-bucket-cors", "--bucket", $BucketName, "--cors-configuration", "file://$corsFile") -Profile $DestProfile -Region $DestRegion | Out-Null
                Remove-Item $corsFile
                Write-Host "CORS configuration restored" -ForegroundColor Green
            } catch {
                Write-Host "Failed to restore CORS configuration: $_" -ForegroundColor Yellow
            }
        }
        
        if ($null -ne $bucketPolicy) {
            try {
                $policyFile = [System.IO.Path]::GetTempFileName()
                $bucketPolicy | Out-File -FilePath $policyFile -Encoding UTF8
                Invoke-AwsCommand -Arguments @("s3api", "put-bucket-policy", "--bucket", $BucketName, "--policy", "file://$policyFile") -Profile $DestProfile -Region $DestRegion | Out-Null
                Remove-Item $policyFile
                Write-Host "Bucket policy restored" -ForegroundColor Green
            } catch {
                Write-Host "Failed to restore bucket policy: $_" -ForegroundColor Yellow
            }
        }

        Write-Host ""
        Write-Host "S3 Migration Summary:" -ForegroundColor Cyan
        Write-Host "  Source bucket: $BucketName (us-east-1) - DELETED" -ForegroundColor Green
        Write-Host "  Destination bucket: $BucketName (us-east-2) - CREATED" -ForegroundColor Green
        Write-Host "  Configuration: Restored" -ForegroundColor Green
    }
}

# ============================================================================
# ECR REPOSITORY MIGRATION
# ============================================================================
if (-not $SkipECR) {
    Invoke-Step "ECR Repository Migration" {
        # Check if source repository exists
        Write-Host "Checking source ECR repository..." -ForegroundColor Gray
        $sourceRepo = Invoke-AwsCommand -Arguments @("ecr", "describe-repositories", "--repository-names", $EcrRepositoryName) -Profile $SourceProfile -Region $SourceRegion -ParseJson -AllowFailure
        
        if ($null -eq $sourceRepo -or $sourceRepo.repositories.Count -eq 0) {
            Write-Host "Source ECR repository '$EcrRepositoryName' not found, skipping" -ForegroundColor Yellow
        } else {
            Write-Host "Source repository found: $EcrRepositoryName" -ForegroundColor Green
            
            # Check if destination repository exists
            $destRepo = Invoke-AwsCommand -Arguments @("ecr", "describe-repositories", "--repository-names", $EcrRepositoryName) -Profile $DestProfile -Region $DestRegion -ParseJson -AllowFailure
            
            if ($null -eq $destRepo -or $destRepo.repositories.Count -eq 0) {
                if ($DryRun) {
                    Write-Host "[DRY RUN] Would create ECR repository: $EcrRepositoryName" -ForegroundColor Cyan
                } else {
                    Write-Host "Creating ECR repository: $EcrRepositoryName" -ForegroundColor Yellow
                    Invoke-AwsCommand -Arguments @(
                        "ecr", "create-repository",
                        "--repository-name", $EcrRepositoryName,
                        "--image-scanning-configuration", "scanOnPush=true"
                    ) -Profile $DestProfile -Region $DestRegion | Out-Null
                    Write-Host "ECR repository created" -ForegroundColor Green
                }
            } else {
                Write-Host "Destination ECR repository already exists" -ForegroundColor Green
            }
            
            # Note: Docker images would need to be pulled from source and pushed to destination
            # This is a manual process or requires additional scripting
            Write-Host "Note: Docker images must be manually migrated by pulling from source and pushing to destination" -ForegroundColor Yellow
        }
    }
}

# ============================================================================
# ECS CLUSTER MIGRATION
# ============================================================================
if (-not $SkipECS) {
    Invoke-Step "ECS Cluster Migration" {
        # Check if source cluster exists
        Write-Host "Checking source ECS cluster..." -ForegroundColor Gray
        $sourceCluster = Invoke-AwsCommand -Arguments @("ecs", "describe-clusters", "--clusters", $EcsClusterName) -Profile $SourceProfile -Region $SourceRegion -ParseJson -AllowFailure
        
        if ($null -eq $sourceCluster -or $sourceCluster.clusters.Count -eq 0 -or $sourceCluster.clusters[0].status -ne "ACTIVE") {
            Write-Host "Source ECS cluster '$EcsClusterName' not found or not active, skipping" -ForegroundColor Yellow
        } else {
            Write-Host "Source cluster found: $EcsClusterName" -ForegroundColor Green
            
            # Check if destination cluster exists
            $destCluster = Invoke-AwsCommand -Arguments @("ecs", "describe-clusters", "--clusters", $EcsClusterName) -Profile $DestProfile -Region $DestRegion -ParseJson -AllowFailure
            
            if ($null -eq $destCluster -or $destCluster.clusters.Count -eq 0 -or $destCluster.clusters[0].status -ne "ACTIVE") {
                if ($DryRun) {
                    Write-Host "[DRY RUN] Would create ECS cluster: $EcsClusterName" -ForegroundColor Cyan
                } else {
                    Write-Host "Creating ECS cluster: $EcsClusterName" -ForegroundColor Yellow
                    Invoke-AwsCommand -Arguments @("ecs", "create-cluster", "--cluster-name", $EcsClusterName) -Profile $DestProfile -Region $DestRegion | Out-Null
                    Write-Host "ECS cluster created" -ForegroundColor Green
                }
            } else {
                Write-Host "Destination ECS cluster already exists" -ForegroundColor Green
            }
            
            # Check for ECS service
            Write-Host "Checking for ECS service..." -ForegroundColor Gray
            $sourceService = Invoke-AwsCommand -Arguments @("ecs", "describe-services", "--cluster", $EcsClusterName, "--services", $EcsServiceName) -Profile $SourceProfile -Region $SourceRegion -ParseJson -AllowFailure
            
            if ($null -ne $sourceService -and $sourceService.services.Count -gt 0) {
                Write-Host "Source ECS service found: $EcsServiceName" -ForegroundColor Green
                Write-Host "Note: ECS services and task definitions must be manually migrated" -ForegroundColor Yellow
                Write-Host "      Use deploy_aws.ps1 to deploy services to the new region" -ForegroundColor Yellow
            }
        }
    }
}

# ============================================================================
# CLOUDWATCH LOGS (if needed)
# ============================================================================
Invoke-Step "CloudWatch Logs Groups" {
    Write-Host "Checking CloudWatch log groups..." -ForegroundColor Gray
    
    $logGroups = Invoke-AwsCommand -Arguments @("logs", "describe-log-groups", "--log-group-name-prefix", "/ecs/pipeline-backend") -Profile $SourceProfile -Region $SourceRegion -ParseJson -AllowFailure
    
    if ($null -ne $logGroups -and $logGroups.logGroups.Count -gt 0) {
        Write-Host "Found $($logGroups.logGroups.Count) log group(s)" -ForegroundColor Green
        
        foreach ($logGroup in $logGroups.logGroups) {
            $logGroupName = $logGroup.logGroupName
            Write-Host "Checking log group: $logGroupName" -ForegroundColor Gray
            
            # Check if log group exists (need exact match, not prefix)
            $destLogGroup = Invoke-AwsCommand -Arguments @("logs", "describe-log-groups", "--log-group-name-prefix", $logGroupName) -Profile $DestProfile -Region $DestRegion -ParseJson -AllowFailure
            
            $logGroupExists = $false
            if ($null -ne $destLogGroup -and $destLogGroup.logGroups.Count -gt 0) {
                # Check for exact match
                foreach ($lg in $destLogGroup.logGroups) {
                    if ($lg.logGroupName -eq $logGroupName) {
                        $logGroupExists = $true
                        break
                    }
                }
            }
            
            if (-not $logGroupExists) {
                if ($DryRun) {
                    Write-Host "[DRY RUN] Would create log group: $logGroupName" -ForegroundColor Cyan
                } else {
                    Write-Host "Creating log group: $logGroupName" -ForegroundColor Yellow
                    try {
                        $createArgs = @("logs", "create-log-group", "--log-group-name", $logGroupName)
                        
                        Invoke-AwsCommand -Arguments $createArgs -Profile $DestProfile -Region $DestRegion | Out-Null
                        Write-Host "Log group created" -ForegroundColor Green
                        
                        # Set retention separately if it exists
                        if ($logGroup.retentionInDays) {
                            try {
                                Invoke-AwsCommand -Arguments @(
                                    "logs", "put-retention-policy",
                                    "--log-group-name", $logGroupName,
                                    "--retention-in-days", [string]$logGroup.retentionInDays
                                ) -Profile $DestProfile -Region $DestRegion | Out-Null
                                Write-Host "Retention policy set to $($logGroup.retentionInDays) days" -ForegroundColor Green
                            } catch {
                                Write-Host "Warning: Could not set retention policy: $_" -ForegroundColor Yellow
                            }
                        }
                    } catch {
                        $errorMsg = $_.Exception.Message
                        if ($errorMsg -match "ResourceAlreadyExistsException" -or $errorMsg -match "already exists") {
                            Write-Host "Log group already exists (created by another process)" -ForegroundColor Yellow
                        } else {
                            Write-Host "Failed to create log group: $errorMsg" -ForegroundColor Red
                        }
                    }
                }
            } else {
                Write-Host "Log group already exists" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "No CloudWatch log groups found" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Migration Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Verify S3 bucket contents:" -ForegroundColor Cyan
Write-Host "     aws s3 ls s3://$BucketName --profile $DestProfile --region $DestRegion --recursive"
Write-Host ""
Write-Host "  2. Update your .env files to use:" -ForegroundColor Cyan
Write-Host "     AWS_REGION=$DestRegion"
Write-Host ""
Write-Host "  3. If using ECS, deploy your services:" -ForegroundColor Cyan
Write-Host "     .\deploy_aws.ps1 -AwsProfile $DestProfile -Region $DestRegion"
Write-Host ""
Write-Host "  4. Test your application with the new region" -ForegroundColor Cyan
Write-Host ""
Write-Host "  5. Once verified, you can optionally delete source resources:" -ForegroundColor Cyan
Write-Host "     (Be careful - only delete after full verification!)"
Write-Host ""

