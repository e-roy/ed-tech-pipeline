[CmdletBinding()]
param(
    [switch]$SkipFrontendChecks,
    [switch]$SkipBackendDeploy,
    [switch]$SkipFrontendDeploy,
    [string]$RailwayCommand = "railway up",
    [string]$VercelCommand = "vercel --prod"
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

function Ensure-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found on PATH. Install it before running this script."
    }
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Ensure-Command bun
if (-not $SkipBackendDeploy) { Ensure-Command railway }
if (-not $SkipFrontendDeploy) { Ensure-Command vercel }

if (-not $SkipFrontendChecks) {
    Invoke-Step "Installing frontend dependencies (bun install)" {
        Push-Location "$repoRoot/frontend"
        try {
            bun install --frozen-lockfile
        } finally {
            Pop-Location
        }
    }

    Invoke-Step "Running frontend quality checks (lint/typecheck/build)" {
        Push-Location "$repoRoot/frontend"
        try {
            bun run lint
            bun run typecheck
            bun run build
        } finally {
            Pop-Location
        }
    }
} else {
    Write-Host "Skipping frontend checks (per --SkipFrontendChecks)" -ForegroundColor Yellow
}

if (-not $SkipBackendDeploy) {
    Invoke-Step "Deploying backend to Railway" {
        Push-Location "$repoRoot/backend"
        try {
            Write-Host "Running: $RailwayCommand"
            Invoke-Expression $RailwayCommand
        } finally {
            Pop-Location
        }
    }
} else {
    Write-Host "Skipping backend deploy (per --SkipBackendDeploy)" -ForegroundColor Yellow
}

if (-not $SkipFrontendDeploy) {
    Invoke-Step "Deploying frontend to Vercel" {
        Push-Location "$repoRoot/frontend"
        try {
            Write-Host "Running: $VercelCommand"
            Invoke-Expression $VercelCommand
        } finally {
            Pop-Location
        }
    }
} else {
    Write-Host "Skipping frontend deploy (per --SkipFrontendDeploy)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Deployment script completed." -ForegroundColor Green

