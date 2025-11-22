# Files That Need to Be Fixed

**Generated:** 2025-11-22 16:30:33
**Total Files Affected:** 9

## Files Requiring Immediate Attention

### C:\Users\franc\Documents\Github\pipeline\findings-analysis.md

**Findings:** 1

- ****: 1 occurrence(s)
  - Line ~30: "AKIA_REDACTED_AWS_ACCESS_KEY" (redacted)


### C:\Users\franc\Documents\Github\pipeline\FIX_REQUIREMENTS.md

**Findings:** 7

- ****: 7 occurrence(s)
  - Line ~111: "postgresql://user:password@="
  - Line ~27: "AKIA_REDACTED_AWS_ACCESS_KEY" (redacted)
  - Line ~52: "AKIA_REDACTED_AWS_ACCESS_KEY" (redacted)
  - ... and 4 more


### C:\Users\franc\Documents\Github\pipeline\prd.md

**Findings:** 1

- ****: 1 occurrence(s)
  - Line ~739: "postgresql://postgres:password"


### C:\Users\franc\Documents\Github\pipeline\REMEDIATION_PLAN.md

**Findings:** 8

- ****: 8 occurrence(s)
  - Line ~93: "postgresql://user:password@="
  - Line ~16: "AKIA_REDACTED_AWS_ACCESS_KEY" (redacted)
  - Line ~33: "AKIA_REDACTED_AWS_ACCESS_KEY" (redacted)
  - ... and 5 more


### C:\Users\franc\Documents\Github\pipeline\scripts\security\analyze-findings.ps1

**Findings:** 6

- ****: 6 occurrence(s)
  - Line ~92: "postgresql://user:password@'"
  - Line ~103: "-----BEGIN.*PRIVATE KEY-----"
  - Line ~131: "AKIA_REDACTED_AWS_ACCESS_KEY"
  - ... and 3 more


### C:\Users\franc\Documents\Github\pipeline\scripts\security\audit-batch-files.ps1

**Findings:** 2

- ****: 2 occurrence(s)
  - Line ~100: "postgresql://.*@localhost',  #"
  - Line ~76: "-----BEGIN (RSA |EC |DSA |OPEN"


### C:\Users\franc\Documents\Github\pipeline\scripts\security\audit-git-history.ps1

**Findings:** 1

- ****: 1 occurrence(s)
  - Line ~68: "postgresql://.*@localhost',  #"


### C:\Users\franc\Documents\Github\pipeline\scripts\security\identify-affected-files.ps1

**Findings:** 3

- ****: 3 occurrence(s)
  - Line ~22: "-----BEGIN.*PRIVATE KEY-----"
  - Line ~111: "AKIA_REDACTED_AWS_ACCESS_KEY"
  - Line ~215: "AKIA_REDACTED_AWS_ACCESS_KEY"


### C:\Users\franc\Documents\Github\pipeline\scripts\security\test-audit-patterns.ps1

**Findings:** 3

- ****: 3 occurrence(s)
  - Line ~61: "postgresql://.*@localhost',
 "
  - Line ~36: "sk-abc123def456ghi789jkl012mno"
  - Line ~30: "r8_abc123def456ghi789jkl012mno"


## Summary by Secret Type
- ****: Found in 32 location(s) across Microsoft.PowerShell.Commands.GenericMeasureInfo.Count file(s)

## What to Do

1. **Review each file listed above**
2. **Check if the secrets are real or placeholders**
3. **If real:**
   - Remove the hardcoded secret
   - Replace with environment variable
   - Update code to read from environment
4. **If placeholder:**
   - No action needed (these are examples)

## Priority Files

Files with **AWS Access Key AKIA_REDACTED_AWS_ACCESS_KEY** should be checked first, as this appears to be a real key.

---
*Review each file manually to determine if secrets are real or examples.*
