# SSH Connection Fix Plan

## Problem Summary

SSH connections to the EC2 instance were timing out during deployment attempts. The connection would fail during the banner exchange phase, preventing code deployments and service management.

## Root Cause Analysis

### Symptoms
- SSH connection timeouts: "Connection timed out during banner exchange"
- Port 22 was reachable (TCP connection succeeded)
- Instance was running and healthy according to AWS status checks
- Security group allowed SSH from anywhere (0.0.0.0/0)
- Backend service was not responding on port 8000

### Possible Causes Identified
1. SSH service not running or misconfigured on the instance
2. Instance-level firewall blocking SSH connections
3. Network/firewall blocking outbound SSH from local machine
4. IP address changes (instance not using Elastic IP)

## Solution Implemented

### 1. Diagnostic Script Created

Created `check_ec2_status.ps1` to diagnose EC2 connectivity issues:

**Features:**
- Checks AWS CLI installation and credentials
- Verifies EC2 instance status (running/stopped)
- Fetches current public IP address
- Validates security group rules for SSH
- Tests network connectivity to port 22
- Locates SSH key files
- Provides troubleshooting recommendations

**Usage:**
```powershell
.\check_ec2_status.ps1
```

### 2. Enhanced Deployment Script

Updated `deploy_ec2.ps1` with automatic IP detection:

**Key Improvements:**
- **Auto IP Detection**: Automatically fetches current EC2 IP from AWS using instance ID
- **Multiple Profile Support**: Tries multiple AWS profiles (default1, default2, default) to find valid credentials
- **Manual Override**: Allows specifying IP via parameter: `.\deploy_ec2.ps1 -EC2Host "ip.address"`
- **Fallback Mechanism**: Falls back to hardcoded IP with warning if AWS fetch fails

**Implementation Details:**
```powershell
# Try to fetch current IP from AWS, fallback to hardcoded IP
$awsProfiles = @("default1", "default2", "default")
foreach ($profile in $awsProfiles) {
    try {
        $publicIp = aws ec2 describe-instances `
            --instance-ids $INSTANCE_ID `
            --profile $profile `
            --region $REGION `
            --query 'Reservations[0].Instances[0].PublicIpAddress' `
            --output text
        if ($LASTEXITCODE -eq 0 -and $publicIp -and $publicIp -ne "None") {
            $EC2_HOST = $publicIp.Trim()
            break
        }
    } catch {
        continue
    }
}
```

### 3. ALB Configuration Verified

Confirmed the deployment architecture:

**ALB Setup:**
- ALB Name: `classclips-backend-alb`
- Public URL: `https://api.classclipscohort3.com`
- Listeners:
  - HTTPS (443): Forwarding to target group
  - HTTP (80): Forwarding to target group (redirects to HTTPS)
- Target Group: Points to EC2 instance on port 8000
- Health Check: `/api/health` endpoint

**Purpose:**
- Provides HTTPS termination for secure communication
- Routes traffic from public domain to EC2 backend
- Enables SSL/TLS without managing certificates on EC2

## Resolution

The SSH connection issue resolved itself (likely after instance reboot or network changes). The enhanced deployment script now:

1. **Automatically detects current IP** - No need to manually update IP addresses
2. **Handles IP changes** - Works even if instance IP changes (non-Elastic IP)
3. **Provides better error messages** - Guides user when connection fails

## Deployment Process

### Successful Deployment Steps

1. **Fetch Current IP**: Script automatically gets current EC2 IP from AWS
2. **Test SSH Connection**: Validates SSH access before proceeding
3. **Pull Latest Code**: `git fetch origin && git reset --hard origin/master`
4. **Update Dependencies**: Install/upgrade Python packages
5. **Run Migrations**: Execute Alembic database migrations
6. **Restart Service**: `sudo systemctl restart pipeline-backend`
7. **Verify Health**: Test `/health` endpoint

### Service Management

**Systemd Service**: `pipeline-backend.service`
- Location: `/etc/systemd/system/pipeline-backend.service`
- Working Directory: `/opt/pipeline/backend`
- Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1`
- Auto-restart: Enabled (`Restart=always`)

**Service Commands:**
```bash
# Check status
sudo systemctl status pipeline-backend

# Restart service
sudo systemctl restart pipeline-backend

# View logs
sudo journalctl -u pipeline-backend -f
```

## Best Practices

### 1. Use Elastic IP (Recommended)
- Current setup uses dynamic IP (changes on restart)
- Consider allocating Elastic IP for stable access
- Update ALB target group if IP changes

### 2. Monitor Service Health
- ALB health checks: `/api/health`
- CloudWatch logs: `/var/log/journal/` (systemd)
- Service logs: `journalctl -u pipeline-backend`

### 3. Deployment Verification
- Check ALB health: `https://api.classclipscohort3.com/health`
- Verify service status: `sudo systemctl status pipeline-backend`
- Test endpoints through ALB

## Troubleshooting

### If SSH Fails Again

1. **Run Diagnostic Script**:
   ```powershell
   .\check_ec2_status.ps1
   ```

2. **Check Instance Status**:
   ```powershell
   aws ec2 describe-instance-status --instance-ids <INSTANCE_ID> --profile default2 --region us-east-2
   ```

3. **Verify Security Group**:
   - Ensure port 22 is open (0.0.0.0/0 or your IP)
   - Check network ACLs

4. **Try Instance Reboot**:
   ```powershell
   aws ec2 reboot-instances --instance-ids <INSTANCE_ID> --profile default2 --region us-east-2
   ```

5. **Alternative Access Methods**:
   - AWS Systems Manager Session Manager (if configured)
   - EC2 Instance Connect (browser-based)
   - VPN to VPC (if available)

### If Service Fails to Start

1. **Check Logs**:
   ```bash
   sudo journalctl -u pipeline-backend -n 50
   ```

2. **Verify Dependencies**:
   ```bash
   source venv/bin/activate
   pip list
   ```

3. **Check Environment Variables**:
   ```bash
   sudo systemctl show pipeline-backend --property=EnvironmentFile
   ```

4. **Test Manual Start**:
   ```bash
   cd /opt/pipeline/backend
   source venv/bin/activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## Files Modified

1. **`deploy_ec2.ps1`**: Enhanced with auto IP detection
2. **`check_ec2_status.ps1`**: New diagnostic script (created)

## ALB Health Check Timeout Fix

### Problem
ALB target health checks were timing out during "Restart Remotion" operations, causing the target to be marked as unhealthy. This occurred because the Remotion rendering process (2-4 minutes) was blocking the event loop in the single-worker FastAPI application.

### Root Cause
- Service runs with `--workers 1` (single worker)
- `process.wait()` in `render_video_with_remotion()` was blocking the event loop
- During 2-4 minute Remotion renders, health checks couldn't be processed
- ALB marked target as unhealthy due to timeout

### Solution Implemented
**File**: `backend/app/agents/agent_5.py`

Wrapped `process.wait()` in `asyncio.to_thread()` to prevent blocking the event loop:

```python
# Wait for process to complete without blocking the event loop
# CRITICAL: This prevents the single worker from being blocked during health checks
await asyncio.to_thread(process.wait)
```

**Key Changes:**
- `read_output()` already runs in a thread (non-blocking)
- `process.wait()` now also runs in a thread pool
- Event loop remains free to handle health checks during long renders
- Health check endpoint (`/health`) is synchronous and runs in FastAPI's thread pool

### Verification
- Health checks should now respond even during active Remotion rendering
- ALB target should remain healthy during video generation
- Background tasks continue processing without blocking the main event loop

## Notes

- Instance uses dynamic IP (not Elastic IP) - may change on restart
- ALB provides HTTPS termination and routing
- Backend runs as systemd service on EC2
- Deployment requires SSH access to EC2 instance
- Code is pulled from GitHub master branch
- Single worker configuration requires careful async/threading to avoid blocking

