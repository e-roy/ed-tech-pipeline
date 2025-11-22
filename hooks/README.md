# Git Hooks

This directory contains shared Git hooks for the project.

## Setup

To enable these hooks locally, run:

```bash
git config core.hooksPath ./hooks
```

Or simply run the setup script from the project root:

```bash
./setup-hooks.sh
```

## Hooks

### pre-commit

Runs gitleaks to scan for secrets in staged files before allowing a commit.

**Requirements:**
- [gitleaks](https://github.com/gitleaks/gitleaks) must be installed

**Install gitleaks:**
- macOS: `brew install gitleaks`
- Linux: Download from [releases](https://github.com/gitleaks/gitleaks/releases)
- Windows: `choco install gitleaks` or download from releases

**Bypass (not recommended):**
```bash
git commit --no-verify
```
