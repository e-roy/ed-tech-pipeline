[CmdletBinding()]
param(
    [string]$AwsProfile = "default1",
    [string]$Region = "us-east-1",
    [string]$EcrRepository = "pipeline-backend",
    [string]$ClusterName = "pipeline-backend",
    [string]$ServiceName = "pipeline-backend-service",
    [string]$DockerContext = "backend",
    [string]$Dockerfile = "backend/Dockerfile",
    [string]$TaskDefinitionTemplate = "infra/aws/ecs-task-definition.json",
    [string]$RenderedTaskDefinition = "infra/aws/.rendered-task-definition.json",
    [string]$ContainerName = "pipeline-backend",
    [string]$ImageTag,
    [switch]$SkipBuild,
    [switch]$SkipDeploy
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Ensure-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' not found in PATH."
    }
}

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
        [switch]$ParseJson
    )

    $baseArgs = @("--profile", $AwsProfile, "--region", $Region) + $Arguments
    $output = & aws @baseArgs 2>&1

    if ($LASTEXITCODE -ne 0) {
        throw "AWS CLI command failed: aws $($Arguments -join ' ')`n$output"
    }

    if ($ParseJson) {
        return $output | ConvertFrom-Json
    }

    return $output
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$dockerContextPath = Join-Path $repoRoot $DockerContext
$dockerfilePath = Join-Path $repoRoot $Dockerfile
$taskTemplatePath = Join-Path $repoRoot $TaskDefinitionTemplate
$renderedTaskPath = Join-Path $repoRoot $RenderedTaskDefinition

Ensure-Command docker
Ensure-Command aws
if (-not $ImageTag) {
    if (Get-Command git -ErrorAction SilentlyContinue) {
        $sha = (& git -C $repoRoot rev-parse --short HEAD 2>$null).Trim()
        if ($sha) {
            $ImageTag = $sha
        }
    }

    if (-not $ImageTag) {
        $ImageTag = (Get-Date -Format "yyyyMMddHHmmss")
    }
}

$localImageName = "pipeline-backend:${ImageTag}"

Invoke-Step "Retrieving AWS account information" {
    $callerIdentity = Invoke-AwsCommand -Arguments @("sts", "get-caller-identity") -ParseJson
    $script:AccountId = $callerIdentity.Account
    Write-Host "Account: $($callerIdentity.Account), User: $($callerIdentity.Arn)"
}

$ecrRegistry = "$AccountId.dkr.ecr.$Region.amazonaws.com"
$imageUri = "$ecrRegistry/${EcrRepository}:${ImageTag}"

Invoke-Step "Ensuring ECR repository '$EcrRepository' exists" {
    try {
        Invoke-AwsCommand -Arguments @("ecr", "describe-repositories", "--repository-names", $EcrRepository) | Out-Null
        Write-Host "Repository exists."
    } catch {
        if ($_.Exception.Message -match "RepositoryNotFoundException") {
            Write-Host "Repository missing, creating..."
            Invoke-AwsCommand -Arguments @(
                "ecr", "create-repository",
                "--repository-name", $EcrRepository,
                "--image-scanning-configuration", "scanOnPush=true"
            ) | Out-Null
            Write-Host "Repository created."
        } else {
            throw
        }
    }
}

Invoke-Step "Authenticating Docker to ECR" {
    $password = Invoke-AwsCommand -Arguments @("ecr", "get-login-password")
    $password | docker login --username AWS --password-stdin $ecrRegistry | Out-Null
}

if (-not $SkipBuild) {
    Invoke-Step "Building backend image ($localImageName)" {
        docker build -t $localImageName -f $dockerfilePath $dockerContextPath
    }
} else {
    Write-Host "Skipping Docker build (per --SkipBuild)" -ForegroundColor Yellow
}

Invoke-Step "Tagging image as $imageUri" {
    docker tag $localImageName $imageUri
}

Invoke-Step "Pushing image to ECR" {
    docker push $imageUri
}

if (-not (Test-Path $taskTemplatePath)) {
    throw "Task definition template not found at $taskTemplatePath"
}

Invoke-Step "Rendering task definition" {
    $templateContent = Get-Content -Raw -Path $taskTemplatePath | ConvertFrom-Json

    if ($templateContent.executionRoleArn -match "123456789012" -or
        $templateContent.taskRoleArn -match "123456789012") {
        throw "Update role ARNs in $TaskDefinitionTemplate before running this script."
    }

    $container = $templateContent.containerDefinitions | Where-Object { $_.name -eq $ContainerName }
    if (-not $container) {
        throw "Container '$ContainerName' not found in task definition template."
    }

    $container.image = $imageUri

    $templateContent | ConvertTo-Json -Depth 10 | Set-Content -Path $renderedTaskPath -Encoding UTF8
    Write-Host "Rendered task definition written to $renderedTaskPath"
}

if (-not $SkipDeploy) {
    Invoke-Step "Registering task definition" {
        $registerResult = Invoke-AwsCommand -Arguments @(
            "ecs", "register-task-definition",
            "--cli-input-json", "file://$renderedTaskPath"
        ) -ParseJson

        $script:TaskDefinitionArn = $registerResult.taskDefinition.taskDefinitionArn
        Write-Host "Registered task definition: $TaskDefinitionArn"
    }

    Invoke-Step "Updating ECS service '$ServiceName'" {
        Invoke-AwsCommand -Arguments @(
            "ecs", "update-service",
            "--cluster", $ClusterName,
            "--service", $ServiceName,
            "--task-definition", $TaskDefinitionArn,
            "--force-new-deployment"
        ) -ParseJson | Out-Null
        Write-Host "Deployment triggered. Check ECS service for status."
    }
} else {
    Write-Host "Skipping ECS deployment (per --SkipDeploy)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "AWS deployment script completed successfully." -ForegroundColor Green

