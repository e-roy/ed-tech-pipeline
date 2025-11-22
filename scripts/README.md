# Scripts Directory

This directory contains all project scripts organized by category.

## Directory Structure

```
scripts/
├── archive/                    # Deprecated/outdated scripts
├── aws/                        # AWS infrastructure scripts
├── deployment/                 # Deployment scripts
├── security/                   # Security audit and secret management
├── setup/                      # Setup and configuration scripts
├── testing/                    # Test scripts
└── utilities/                  # Utility and maintenance scripts
```

## Script Categories

### Security Scripts (`security/`)

**Audit Scripts:**
- `audit-batch-files.ps1` - Audits .sh, .ps1, .html, .md files for sensitive information
- `audit-git-history.ps1` - Scans entire git history for secrets
- `test-audit-patterns.ps1` - Tests regex patterns for secret detection

**Secret Management:**
- `remove-secrets.ps1` - Removes secrets from git history
- `replace-secret.ps1` - Replaces a single secret in git history
- `replace-secrets-in-history.ps1` - Batch replace secrets in git history
- `replace-secrets.sh` - Linux version of secret replacement
- `replace-secrets.bat` - Windows batch version

**Usage:**
```powershell
# Audit current codebase and git history
.\scripts\security\audit-batch-files.ps1

# Audit git history only
.\scripts\security\audit-git-history.ps1 -OutputFile "security-report.txt"
```

### Deployment Scripts (`deployment/`)

**Main Deployment:**
- `deploy.ps1` - Main deployment script
- `deploy_aws.ps1` - AWS-specific deployment
- `deploy_ec2.ps1` - EC2 instance deployment
- `deploy_simple.ps1` - Simplified deployment
- `quick_deploy.ps1` - Quick deployment script

**Server Management:**
- `start-server.ps1` - Start backend server
- `stop-server.ps1` - Stop backend server

**Usage:**
```powershell
# Deploy to EC2
.\scripts\deployment\deploy_ec2.ps1

# Quick deploy
.\scripts\deployment\quick_deploy.ps1
```

### AWS Scripts (`aws/`)

**EC2 Management:**
- `check_ec2_status.ps1` - Check EC2 instance status and connectivity
- `install_bun_ec2.ps1` - Install Bun on EC2 (PowerShell)
- `install_bun_ec2.sh` - Install Bun on EC2 (Bash)
- `update_ec2.sh` - Update EC2 instance

**AWS Resources:**
- `migrate_all_aws_resources.ps1` - Migrate all AWS resources
- `migrate_s3_bucket.ps1` - Migrate S3 bucket
- `setup_s3_and_env.ps1` - Setup S3 and environment variables

**Usage:**
```powershell
# Check EC2 status
.\scripts\aws\check_ec2_status.ps1

# Setup S3
.\scripts\aws\setup_s3_and_env.ps1
```

### Setup Scripts (`setup/`)

- `setup-hooks.sh` - Setup git hooks
- `start-database.sh` - Start database (frontend)

**Usage:**
```bash
# Setup git hooks
./scripts/setup/setup-hooks.sh

# Start database
./scripts/setup/start-database.sh
```

### Testing Scripts (`testing/`)

Test scripts for various components:

- `test_agents.py` - Test agent functionality
- `test_audio_agent.py` - Test audio agent
- `test_full_pipeline.py` - End-to-end pipeline test
- `test_narrative.py` - Test narrative builder
- `test_orchestrator_audio.py` - Test orchestrator audio
- `test_person_c.py` - Test Person C components
- `test_replicate.py` - Test Replicate API
- `test_s3_access.py` - Test S3 access
- `test_script_image_generation.py` - Test script image generation
- `test_video_direct.py` - Test video generation (direct)
- `test_video_live.py` - Test video generation (live)
- `test_visual_pipeline.py` - Test visual pipeline
- `test_get_script.py` - Test script retrieval

**Usage:**
```bash
# Run specific test
python scripts/testing/test_agents.py

# Run all tests (from backend directory)
cd backend
pytest
```

### Utility Scripts (`utilities/`)

**Database/Data:**
- `seed_music_library.py` - Seed music library
- `seed_templates.py` - Seed templates
- `seed_test_music.py` - Seed test music data

**S3 Management:**
- `create_test_music.py` - Create test music files
- `fix_existing_s3_objects.py` - Fix S3 object permissions
- `set_s3_public_policy.py` - Set S3 bucket public policy
- `upload_music_to_s3.py` - Upload music to S3

**Verification:**
- `verify_person_b.py` - Verify Person B implementation

**Usage:**
```bash
# Seed database
python scripts/utilities/seed_templates.py

# Upload music to S3
python scripts/utilities/upload_music_to_s3.py
```

## Script Requirements

### PowerShell Scripts
- Windows PowerShell 5.1+ or PowerShell Core 7+
- AWS CLI (for AWS scripts)
- Git (for git-related scripts)

### Bash/Shell Scripts
- Bash 4.0+
- Linux/macOS or WSL/Git Bash on Windows

### Python Scripts
- Python 3.11+
- Dependencies from `backend/requirements.txt`

## Running Scripts

### From Root Directory

**PowerShell:**
```powershell
.\scripts\security\audit-batch-files.ps1
.\scripts\deployment\deploy_ec2.ps1
```

**Bash:**
```bash
./scripts/setup/setup-hooks.sh
```

**Python:**
```bash
python scripts/testing/test_agents.py
python scripts/utilities/seed_templates.py
```

### From Script Directory

```powershell
cd scripts\security
.\audit-batch-files.ps1
```

## Best Practices

1. **Review Before Running:** Always review scripts before executing, especially deployment and security scripts
2. **Backup First:** Backup important data before running migration or cleanup scripts
3. **Test Environment:** Test scripts in a development environment first
4. **Check Dependencies:** Ensure all required tools and credentials are configured
5. **Read Documentation:** Check script comments and this README for usage instructions

## Security Notes

- **Never commit secrets:** Use environment variables or secret management
- **Audit regularly:** Run security audit scripts regularly
- **Review changes:** Review git history changes before force pushing
- **Rotate credentials:** Rotate exposed credentials immediately if found

## Maintenance

When adding new scripts:
1. Place in appropriate category directory
2. Add usage instructions to this README
3. Include error handling and validation
4. Add comments explaining what the script does
5. Test in development environment first

## Archive

The `archive/` directory contains deprecated scripts that are kept for reference but should not be used in production.

