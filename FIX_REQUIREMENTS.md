# What It Will Take to Fix Security Issues

**Based on:** `my-affected-files.md` and `batch-files-security-audit-report.txt`  
**Date:** 2025-11-22

## Quick Summary

- **Total Findings:** 386
- **Current Codebase:** 31 findings
- **Git History:** 355 findings
- **Estimated Fix Time:** 11-22 hours
- **Priority:** ⚠️ HIGH - Action required

## The Problem

### Breakdown by Source

| Source | Count | Priority | Action |
|--------|-------|---------|--------|
| **Filesystem (Current)** | 31 | 🔴 Critical | Fix immediately |
| **Git History** | 355 | 🟡 High | Clean up history |

### Breakdown by Type

| Secret Type | Count | Risk Level | Notes |
|-------------|-------|------------|-------|
| AWS Access Key ID | 258 | 🔴 Critical | `AKIA_REDACTED_AWS_ACCESS_KEY` found 258 times (rotated) |
| Database URL with password | 50 | 🔴 High | May contain real passwords |
| Generic API Key | 20 | 🟡 Medium | Need to verify if real |
| Password in variable | 19 | 🟢 Low | Likely false positives (variable names) |
| AWS Secret Access Key | 17 | 🔴 Critical | If real, high risk |
| Replicate API Key | 9 | 🟡 Medium | Need to verify |
| Private Key | 4 | 🔴 Critical | If real, very high risk |
| Generic Secret Key | 4 | 🟡 Medium | Need to verify |
| OpenAI API Key | 3 | 🟡 Medium | Need to verify |
| JWT Secret Key | 2 | 🟡 Medium | Need to verify |

## What Needs to Be Done

### Phase 1: Immediate Actions (2-4 hours) 🔴

#### 1.1 Verify Real Secrets

**Critical:** Determine which findings are REAL secrets vs false positives:

```powershell
# Run analysis script
.\scripts\security\analyze-findings.ps1 -ReportFile "batch-files-security-audit-report.txt"
```

**Key Questions:**
- ✅ AWS key has been rotated (was `AKIA_REDACTED_AWS_ACCESS_KEY`)
- Are database URLs with passwords pointing to real databases?
- Are the private keys real or examples?

#### 1.2 Rotate Exposed Credentials

**If secrets are real:**

1. **AWS Credentials:**
   ```bash
   # AWS key has been rotated (was AKIA_REDACTED_AWS_ACCESS_KEY):
   # 1. AWS Console → IAM → Deactivate key
   # 2. Create new access key
   # 3. Update all services
   # 4. Remove from codebase and history
   ```

2. **Database Passwords:**
   - Change all exposed database passwords
   - Update connection strings

3. **API Keys:**
   - Rotate OpenAI, Replicate, and other API keys
   - Revoke old keys

**Time:** 1-2 hours

#### 1.3 Fix Current Codebase (31 findings)

**Steps:**
1. Review each of the 31 filesystem findings
2. Remove real secrets from files
3. Replace with environment variables
4. Update code to read from env vars

**Files to Check:**
- Configuration files
- Documentation files
- Test files
- Script files

**Time:** 2-4 hours

### Phase 2: Git History Cleanup (4-8 hours) 🟡

**Options:**

#### Option A: Selective Removal (Recommended)

Remove only specific secrets from history:

```bash
# Install git-filter-repo
pip install git-filter-repo

# Remove specific AWS key
git filter-repo --replace-text <(echo "AKIA_REDACTED_AWS_ACCESS_KEY==>AKIA_REDACTED_AWS_ACCESS_KEY")

# Remove database URLs with passwords (be careful with this)
git filter-repo --replace-text <(echo "postgresql://user:password@==>postgresql://user:REDACTED@")
```

**Pros:**
- Keeps git history
- Only removes specific secrets
- Less disruptive to team

**Cons:**
- Takes longer
- Need to identify each secret

**Time:** 4-6 hours

#### Option B: Complete History Rewrite (Nuclear)

Remove all git history:

```bash
# Create orphan branch
git checkout --orphan new-main
git add .
git commit -m "Initial commit - security cleanup"
git branch -D main
git branch -m main
git push -f origin main
```

**Pros:**
- Fast
- Removes everything

**Cons:**
- Loses ALL history
- Team must re-clone
- Issues/PRs may break

**Time:** 1-2 hours + team coordination

### Phase 3: Prevention (2-4 hours) 🟢

#### 3.1 Update Audit Script

Add better exclusion patterns to reduce false positives:

```powershell
# Add to scripts/security/audit-batch-files.ps1
# Exclude patterns like:
# - pwd_context.hash (variable name)
# - Type.String (validation schema)
# - your-together-ai-key (placeholder)
```

**Time:** 1 hour

#### 3.2 Implement Pre-commit Hooks

```bash
# Install git-secrets
git secrets --install
git secrets --register-aws

# Add custom patterns
git secrets --add 'AKIA[0-9A-Z]{16}'
git secrets --add 'sk-[a-zA-Z0-9]{32,}'
```

**Time:** 1 hour

#### 3.3 Migrate to Environment Variables

- Update all config files
- Create .env.example files
- Document required variables
- Use secret management (AWS Secrets Manager)

**Time:** 2-4 hours

## Time & Resource Estimate

| Task | Time | Priority | Dependencies |
|------|------|----------|--------------|
| Verify real secrets | 1-2 hours | Critical | None |
| Rotate credentials | 1-2 hours | Critical | Verification |
| Fix current codebase | 2-4 hours | High | Verification |
| Clean git history | 4-8 hours | High | Fix codebase |
| Update audit script | 1 hour | Medium | None |
| Pre-commit hooks | 1 hour | Medium | None |
| Environment variables | 2-4 hours | Medium | Fix codebase |
| **Total** | **12-22 hours** | | |

## Step-by-Step Action Plan

### Step 1: Analyze Findings (1 hour)

```powershell
# Run analysis to categorize findings
.\scripts\security\analyze-findings.ps1

# Review findings-analysis.md
# Identify which are real secrets
```

### Step 2: Rotate Credentials (1-2 hours)

**If `AKIA_REDACTED_AWS_ACCESS_KEY` is real:**
1. Log into AWS Console
2. IAM → Users → Security Credentials
3. Deactivate the key
4. Create new key
5. Update services

**For other credentials:**
- Change database passwords
- Rotate API keys
- Revoke old keys

### Step 3: Fix Current Files (2-4 hours)

```powershell
# Re-run audit for current files only
.\scripts\security\audit-batch-files.ps1 -CurrentOnly -Verbose

# For each file with real secrets:
# 1. Remove hardcoded secret
# 2. Replace with environment variable
# 3. Update code to read from env
# 4. Test changes
```

### Step 4: Clean Git History (4-8 hours)

**Before starting:**
```bash
# Create backup
git clone --mirror <repo-url> backup-repo.git
```

**Then choose approach:**
- **Selective:** Use git-filter-repo for specific secrets
- **Complete:** Remove all history (nuclear option)

### Step 5: Verify (1 hour)

```powershell
# Re-run full audit
.\scripts\security\audit-batch-files.ps1

# Should show significantly fewer findings
# Verify no real secrets remain
```

### Step 6: Team Coordination (1-2 hours)

**If history was rewritten:**
- Notify team
- Provide re-clone instructions
- Update documentation

## Cost Considerations

### If Secrets Are Real:

- **AWS:** Potential unauthorized access → financial risk
- **Database:** Data breach risk
- **API Keys:** Unauthorized usage → costs
- **Private Keys:** System compromise risk

### Remediation Costs:

- **Time:** 12-22 hours of developer time
- **Service Disruption:** Minimal if done carefully
- **Team Coordination:** 1-2 hours

## Risk Assessment

### High Risk (Do First)
- ✅ AWS Access Key (rotated, 258 occurrences in git history to be cleaned)
- ✅ Database passwords (50 occurrences)
- ✅ Private keys (4 occurrences)

### Medium Risk
- ⚠️ API keys (various types)
- ⚠️ Secrets in git history (accessible to repo viewers)

### Low Risk
- ℹ️ False positives (variable names, placeholders)

## Tools & Scripts

1. **Analysis:**
   - `scripts/security/analyze-findings.ps1` - Categorize findings
   - `scripts/security/audit-batch-files.ps1` - Full audit

2. **Remediation:**
   - `scripts/security/remove-secrets.ps1` - Remove from history
   - `scripts/security/replace-secrets-in-history.ps1` - Replace in history
   - `git-filter-repo` - Recommended tool

3. **Prevention:**
   - `git-secrets` - Pre-commit hooks
   - Pre-commit hooks in `hooks/` directory

## Quick Start

**To get started immediately:**

```powershell
# 1. Analyze findings
.\scripts\security\analyze-findings.ps1

# 2. Review findings-analysis.md

# 3. If real secrets found, rotate credentials first

# 4. Fix current codebase
.\scripts\security\audit-batch-files.ps1 -CurrentOnly -Verbose

# 5. Clean git history (after fixing codebase)
# See REMEDIATION_PLAN.md for detailed steps
```

## Next Steps

1. **Today:** Run analysis, verify real secrets, rotate credentials
2. **This Week:** Fix current codebase, plan history cleanup
3. **Ongoing:** Implement prevention measures

---

**Status:** ⚠️ Action Required  
**Created:** 2025-11-22  
**See Also:** `REMEDIATION_PLAN.md` for detailed remediation steps

