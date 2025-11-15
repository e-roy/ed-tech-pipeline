[CmdletBinding()]
param(
    [string]$AwsProfile = "default1",
    [string]$Region = "us-east-1",
    [string]$BucketName = "pipeline-backend-assets"
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

# Ensure bucket exists
Invoke-Step "Checking S3 bucket exists" {
    $bucketExists = aws s3 ls "s3://$BucketName" --profile $AwsProfile --region $Region 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Creating bucket: $BucketName"
        aws s3 mb "s3://$BucketName" --profile $AwsProfile --region $Region
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create bucket"
        }
    } else {
        Write-Host "Bucket already exists: $BucketName"
    }
}

# Configure CORS
Invoke-Step "Configuring CORS for frontend access" {
    $corsConfig = @{
        CORSRules = @(
            @{
                AllowedOrigins = @("*")
                AllowedMethods = @("GET", "HEAD")
                AllowedHeaders = @("*")
                MaxAgeSeconds = 3000
            }
        )
    } | ConvertTo-Json -Depth 10 -Compress
    
    $corsFile = [System.IO.Path]::GetTempFileName()
    $corsConfig | Out-File -FilePath $corsFile -Encoding UTF8
    
    aws s3api put-bucket-cors `
        --bucket $BucketName `
        --cors-configuration "file://$corsFile" `
        --profile $AwsProfile `
        --region $Region
    
    Remove-Item $corsFile
    Write-Host "CORS configured successfully"
}

# Get backend service info
Invoke-Step "Getting backend service information" {
    Write-Host ""
    Write-Host "Backend ECS Service Info:" -ForegroundColor Yellow
    Write-Host "  Cluster: pipeline-backend"
    Write-Host "  Service: pipeline-backend-service"
    Write-Host ""
    Write-Host "To get the backend URL, you have two options:" -ForegroundColor Yellow
    Write-Host "  1. Get task public IP (temporary - changes on restart):"
    Write-Host "     aws ecs list-tasks --cluster pipeline-backend --service pipeline-backend-service --profile $AwsProfile --region $Region"
    Write-Host "     aws ecs describe-tasks --cluster pipeline-backend --tasks <task-arn> --profile $AwsProfile --region $Region --query 'tasks[0].attachments[0].details[?name==\`publicIpv4Address\`].value' --output text"
    Write-Host ""
    Write-Host "  2. Set up an Application Load Balancer (recommended for production)"
    Write-Host ""
}

# Display environment variables needed
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "ENVIRONMENT VARIABLES SUMMARY" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "BACKEND (ECS Task Definition) - Set these as environment variables:" -ForegroundColor Cyan
Write-Host "  AWS_REGION=$Region"
Write-Host "  S3_BUCKET_NAME=$BucketName"
Write-Host "  DATABASE_URL=<set-from-environment-variable>"
Write-Host "  JWT_SECRET_KEY=<set-from-environment-variable>"
Write-Host "  REPLICATE_API_KEY=<set-from-environment-variable>"
Write-Host "  FRONTEND_URL=<update-with-vercel-url-after-frontend-deployment>"
Write-Host "  ECS_EXECUTION_ROLE_ARN=<set-from-environment-variable>"
Write-Host "  ECS_TASK_ROLE_ARN=<set-from-environment-variable>"
Write-Host "  ECR_IMAGE_URI=<set-from-environment-variable>"
Write-Host ""
Write-Host "FRONTEND (Vercel/Next.js) - Set these in Vercel dashboard:" -ForegroundColor Cyan
Write-Host "  NEXT_PUBLIC_API_URL=http://<backend-ip>:8000  (or https://<alb-domain> if using ALB)"
Write-Host "  AUTH_SECRET=<set-from-environment-variable>"
Write-Host "  AUTH_GOOGLE_ID=<set-from-environment-variable>"
Write-Host "  AUTH_GOOGLE_SECRET=<set-from-environment-variable>"
Write-Host "  DATABASE_URL=<set-from-environment-variable>"
Write-Host ""
Write-Host "S3 Bucket Configuration:" -ForegroundColor Cyan
Write-Host "  Bucket: $BucketName"
Write-Host "  Region: $Region"
Write-Host "  CORS: Configured for frontend access"
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Deploy backend: .\deploy_aws.ps1"
Write-Host "  2. Get backend URL (task IP or set up ALB)"
Write-Host "  3. Set frontend env vars in Vercel dashboard (see values above)"
Write-Host "  4. Update FRONTEND_URL in task definition after frontend is deployed"
Write-Host "  5. Redeploy backend: .\deploy_aws.ps1"
Write-Host ""

