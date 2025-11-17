# Stop all backend server instances
# This script finds and stops all Python/uvicorn processes listening on port 8000

Write-Host "Stopping all backend server instances on port 8000..." -ForegroundColor Yellow

# Get all processes listening on port 8000
$listeners = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue

if ($listeners) {
    $pids = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
    Write-Host "Found $($pids.Count) process(es) listening on port 8000" -ForegroundColor Cyan
    
    foreach ($processId in $pids) {
        $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "  Stopping process $processId ($($proc.ProcessName))..." -ForegroundColor Gray
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
            Write-Host "    Stopped" -ForegroundColor Green
        }
    }
    
    # Wait a moment for processes to fully stop
    Start-Sleep -Seconds 2
    
    # Verify they're stopped
    $remaining = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if ($remaining) {
        Write-Host "Warning: Some processes may still be running. Remaining listeners: $($remaining.Count)" -ForegroundColor Yellow
    } else {
        Write-Host "All server instances stopped successfully" -ForegroundColor Green
    }
} else {
    Write-Host "No processes found listening on port 8000" -ForegroundColor Gray
}

Write-Host "Done." -ForegroundColor Cyan

