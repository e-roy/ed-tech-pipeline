# Security Remediation Plan

**Generated:** 2025-11-22  
**Total Findings:** 386  
**Filesystem Findings:** 31  
**Git History Findings:** 355

## Executive Summary

The security audit found **386 potential security issues** across batch files (.sh, .ps1, .html, .md):
- **31 findings** in current codebase (filesystem)
- **355 findings** in git history

### Critical Issues Identified

1. **AWS Access Key ID: `AKIA_REDACTED_AWS_ACCESS_KEY`** - Found 258 times in git history (key has been rotated)
2. **Database URLs with passwords** - 50 instances
3. **API Keys** - Various types found
4. **Private Keys** - 4 instances

## Analysis: Real vs False Positives

### Likely False Positives (Need Manual Review)

Many findings appear to be:
- **Placeholder values** (e.g., "your-together-ai-key", "sk-your-openai-api-key-here")
- **Variable names** containing "password" (e.g., `pwd_context.hash()`, `Type.String()`)
- **Example/test data** in documentation
- **Pattern matches** that aren't actual secrets

### Real Security Issues (Require Immediate Action)

1. **AWS Access Key: `AKIA_REDACTED_AWS_ACCESS_KEY`** - Key has been rotated, found 258 times in git history (needs cleanup)
2. **Database URLs with actual passwords** - Need to verify if these are real credentials
3. **Private keys** - Need to check if these are real or examples

## Remediation Strategy

### Phase 1: Immediate Actions (Critical - Do First)

#### 1.1 Rotate Exposed Credentials

**AWS Credentials:**
```bash
# AWS key has been rotated (was AKIA_REDACTED_AWS_ACCESS_KEY):
# 1. Log into AWS Console
# 2. Go to IAM → Users → Security Credentials
# 3. Deactivate the exposed access key
# 4. Create new access key
# 5. Update all services using the old key
```

**Database Passwords:**
- Change all database passwords that were exposed
- Update connection strings in environment variables

**API Keys:**
- Rotate OpenAI, Replicate, and other API keys
- Revoke old keys from service providers

#### 1.2 Verify Current Codebase (31 findings)

**Priority:** High - These are in active files

**Steps:**
1. Review each of the 31 filesystem findings
2. Determine if they're real secrets or false positives
3. Remove or replace real secrets immediately
4. Update code to use environment variables

**Files to Check:**
- Check the detailed report for specific file paths
- Focus on .env files, config files, and documentation

### Phase 2: Git History Cleanup (355 findings)

**Priority:** High - Secrets in git history are still accessible

**Options:**

#### Option A: Remove Specific Secrets from History (Recommended)

Use `git-filter-repo` to remove specific secrets:

```bash
# Install git-filter-repo
pip install git-filter-repo

# Remove specific AWS key from all history
git filter-repo --replace-text <(echo "AKIA_REDACTED_AWS_ACCESS_KEY==>AKIA_REDACTED_AWS_ACCESS_KEY")

# Remove database URLs with passwords
git filter-repo --replace-text <(echo "postgresql://user:password@==>postgresql://user:REDACTED@")
```

#### Option B: Complete History Rewrite (Nuclear Option)

If too many secrets are exposed, consider removing all history:

```bash
# Create orphan branch (no history)
git checkout --orphan new-main
git add .
git commit -m "Initial commit - security cleanup"
git branch -D main
git branch -m main
git push -f origin main
```

**⚠️ WARNING:** This removes ALL git history permanently!

### Phase 3: Prevention (Ongoing)

#### 3.1 Update .gitignore

Ensure these patterns are in `.gitignore`:
```
.env
.env.local
.env.*.local
*.pem
*.key
*.p12
secrets/
credentials/
```

#### 3.2 Use Pre-commit Hooks

Install `git-secrets` or create custom hooks:

```bash
# Install git-secrets
git secrets --install
git secrets --register-aws

# Add custom patterns
git secrets --add 'AKIA[0-9A-Z]{16}'
git secrets --add 'sk-[a-zA-Z0-9]{20,}'
```

#### 3.3 Environment Variables

**Current State:**
- Some config files use hardcoded defaults
- Need to migrate to environment variables

**Action Items:**
1. Update `backend/app/config.py` to require env vars (no defaults for secrets)
2. Create `.env.example` files with placeholders
3. Document required environment variables
4. Use secret management (AWS Secrets Manager, etc.)

## Step-by-Step Remediation

### Step 1: Review Current Filesystem Findings (1-2 hours)

```powershell
# Re-run audit for current filesystem only
.\scripts\security\audit-batch-files.ps1 -CurrentOnly -Verbose

# Review each finding manually
# Categorize: Real Secret | False Positive | Placeholder
```

**Checklist:**
- [ ] Review all 31 filesystem findings
- [ ] Identify real secrets vs false positives
- [ ] Document which files need changes
- [ ] Prioritize by severity

### Step 2: Fix Current Codebase (2-4 hours)

**For Real Secrets:**
1. Remove hardcoded secrets
2. Replace with environment variables
3. Update documentation
4. Test changes

**For False Positives:**
1. Update patterns in audit script to exclude them
2. Or add to exclusion list

### Step 3: Clean Git History (4-8 hours)

**Before Starting:**
```bash
# Create backup
git clone --mirror <repo-url> backup-repo.git

# Verify backup
cd backup-repo.git
git log --oneline | head -10
```

**Option A: Remove Specific Secrets (Recommended)**

```bash
# Create replacement file
cat > replacements.txt << EOF
AKIA_REDACTED_AWS_ACCESS_KEY==>AKIA_REDACTED_AWS_ACCESS_KEY
# Add other specific secrets here
EOF

# Apply replacements
git filter-repo --replace-text replacements.txt --force
```

**Option B: Use Existing Scripts**

```powershell
# Review and update scripts/security/replace-secrets-in-history.ps1
# Add specific secrets to replace
.\scripts\security\replace-secrets-in-history.ps1
```

### Step 4: Verify Cleanup (1 hour)

```powershell
# Re-run full audit
.\scripts\security\audit-batch-files.ps1

# Should show significantly fewer findings
# Verify no real secrets remain
```

### Step 5: Force Push (Coordinate with Team)

```bash
# After history rewrite, force push
git push -f origin main

# Team members must:
# 1. Backup their work
# 2. Delete local repository
# 3. Re-clone from remote
```

## Estimated Time & Effort

| Phase | Task | Time Estimate | Priority |
|-------|------|---------------|----------|
| 1 | Rotate credentials | 2-4 hours | Critical |
| 2 | Review filesystem findings | 1-2 hours | High |
| 3 | Fix current codebase | 2-4 hours | High |
| 4 | Clean git history | 4-8 hours | High |
| 5 | Verify & test | 1-2 hours | Medium |
| 6 | Team coordination | 1-2 hours | Medium |
| **Total** | | **11-22 hours** | |

## Risk Assessment

### High Risk
- **AWS Access Key exposed** - Could allow unauthorized AWS access
- **Database passwords exposed** - Could allow database access
- **Private keys exposed** - Could allow system access

### Medium Risk
- **API keys exposed** - Could result in unauthorized API usage and costs
- **Secrets in git history** - Accessible to anyone with repo access

### Low Risk
- **False positives** - No actual security risk, but clutter reports

## Tools & Scripts Available

1. **Audit Scripts:**
   - `scripts/security/audit-batch-files.ps1` - Current audit
   - `scripts/security/audit-git-history.ps1` - Git history only

2. **Remediation Scripts:**
   - `scripts/security/remove-secrets.ps1` - Remove from history
   - `scripts/security/replace-secrets-in-history.ps1` - Replace in history

3. **External Tools:**
   - `git-filter-repo` - Recommended for history cleanup
   - `git-secrets` - Pre-commit hooks
   - `truffleHog` - Alternative secret scanner

## Next Steps

1. **Immediate (Today):**
   - [ ] Rotate AWS key `AKIA_REDACTED_AWS_ACCESS_KEY` if it's real
   - [ ] Review filesystem findings (31 files)
   - [ ] Create backup of repository

2. **This Week:**
   - [ ] Fix all real secrets in current codebase
   - [ ] Plan git history cleanup approach
   - [ ] Coordinate with team

3. **Ongoing:**
   - [ ] Implement pre-commit hooks
   - [ ] Migrate to environment variables
   - [ ] Set up secret management
   - [ ] Regular security audits

## Questions to Answer

1. **Is `AKIA_REDACTED_AWS_ACCESS_KEY` a real AWS key?**
   - If yes: Rotate immediately
   - If no: Add to exclusion patterns

2. **Are database URLs with passwords real?**
   - Check if they're production or test databases
   - Rotate if production

3. **What's the team's tolerance for history rewrite?**
   - If low: Use selective removal
   - If high: Consider complete rewrite

4. **Do we have backups?**
   - Verify before any history changes

## Support & Resources

- **AWS Key Rotation:** https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html
- **git-filter-repo:** https://github.com/newren/git-filter-repo
- **git-secrets:** https://github.com/awslabs/git-secrets
- **OWASP Secret Management:** https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html

---

**Status:** ⚠️ Action Required  
**Last Updated:** 2025-11-22  
**Next Review:** After Phase 1 completion

