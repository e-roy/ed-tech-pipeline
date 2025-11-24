# Agent5 Bun Installation Guide

## Problem

Agent5 video rendering requires **Bun** to run Remotion on the server. If you see this error:

```
Could not find bun or bunx. Please ensure bun is installed.
```

This means Bun is not installed on your EC2 server.

## Solution

### Quick Fix: Install Bun on EC2

Run this script from your local machine to install Bun on your EC2 server:

```bash
bash backend/install_bun_ec2.sh
```

This script will:
1. Connect to your EC2 instance
2. Install Bun using the official installer
3. Install Remotion dependencies
4. Verify the installation

### Manual Installation

If you prefer to install manually, SSH into your EC2 server and run:

```bash
# Get current EC2 IP (IP changes on restart)
# Option 1: Use AWS CLI
EC2_IP=$(aws ec2 describe-instances --instance-ids i-051a27d0f69e98ca2 --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
# Option 2: Get from AWS Console → EC2 → Instances → Select instance → Public IPv4 address

# SSH into EC2 (replace IP_ADDRESS with current IP)
ssh -i ~/Downloads/pipeline_orchestrator.pem ec2-user@IP_ADDRESS

# Install Bun
curl -fsSL https://bun.sh/install | bash

# Source bashrc to make bun available
source ~/.bashrc

# Navigate to Remotion project
cd /opt/pipeline/remotion

# Install dependencies
bun install
```

### Verify Installation

After installation, verify Bun is working:

```bash
bun --version
```

### How Agent5 Finds Bun

Agent5 searches for Bun in these locations (in order):
1. `bunx` in system PATH
2. `/home/ec2-user/.bun/bin/bunx`
3. `/usr/local/bin/bunx`
4. `~/.bun/bin/bunx`
5. Falls back to `bun x` if `bunx` not found

### Updating EC2

The `update_ec2.sh` script now checks if Bun is installed and warns you if it's missing.

## Technical Details

- **Bun** is a fast JavaScript runtime used to run Remotion
- **Remotion** is used to render the final video composition
- Agent5 successfully generates video clips with Replicate, but needs Bun to composite them into the final video

## Cost Note

If Agent5 fails after generating clips, you've already incurred the cost for video generation (~$0.10-0.11 per clip). Installing Bun allows you to retry video rendering without regenerating clips by using the "Restart from Remotion" option.

