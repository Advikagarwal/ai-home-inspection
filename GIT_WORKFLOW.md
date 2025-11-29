# Git Workflow & Auto-Sync Guide

## Overview

This project includes automated Git synchronization to keep your GitHub repository up-to-date with every change.

## Setup Options

### Option 1: Automatic Sync with Git Hooks (Recommended)

**Install Git hooks that auto-push after every commit:**

```bash
# Run the setup script
./scripts/setup_git_hooks.sh
```

**What this does:**
- ✅ Automatically pushes to GitHub after every commit
- ✅ Runs tests before pushing (prevents broken code)
- ✅ Works seamlessly in the background

**Usage:**
```bash
# Just commit as usual - push happens automatically
git add .
git commit -m "Your commit message"
# 🔄 Auto-push happens here!
```

### Option 2: Manual Sync Script

**Use the sync script when you want to commit and push everything:**

```bash
# Sync all changes with one command
./scripts/git_sync.sh
```

**What this does:**
- ✅ Stages all changes
- ✅ Creates timestamped commit
- ✅ Pulls latest changes
- ✅ Pushes to GitHub
- ✅ Shows summary

### Option 3: GitHub Actions (Automatic)

**Already configured!** The `.github/workflows/auto-sync.yml` workflow:
- ✅ Runs on every push to main/develop
- ✅ Ensures repository is in sync
- ✅ No manual action needed

## Quick Start

### First Time Setup

1. **Initialize Git (if not already done):**
```bash
git init
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
```

2. **Install Git hooks:**
```bash
./scripts/setup_git_hooks.sh
```

3. **Make your first sync:**
```bash
git add .
git commit -m "Initial commit with auto-sync"
# Push happens automatically!
```

### Daily Workflow

**With Git Hooks (Automatic):**
```bash
# Edit files...
git add .
git commit -m "Updated requirements"
# ✅ Automatically syncs to GitHub!
```

**With Sync Script:**
```bash
# Edit files...
./scripts/git_sync.sh
# ✅ Everything committed and pushed!
```

**Traditional Git:**
```bash
# Edit files...
git add .
git commit -m "Your message"
git push origin main
```

## Sync Triggers

### What Triggers Auto-Sync?

1. **Git Hooks** (if installed):
   - Every `git commit` → auto-push

2. **GitHub Actions**:
   - Every push to main/develop
   - Manual workflow dispatch

3. **Sync Script**:
   - When you run `./scripts/git_sync.sh`

## File Change Detection

The sync script automatically detects and tags changes:

- `[specs updated]` - Changes in `.kiro/specs/`
- `[code updated]` - Changes in `src/`
- `[tests updated]` - Changes in `tests/`
- `[docs updated]` - Changes in `.md` files

**Example commit message:**
```
Auto-sync: 2024-01-15 14:30:00 [specs updated] [docs updated]
```

## Conflict Resolution

### If Auto-Sync Fails

**Scenario:** Someone else pushed changes while you were working

**Solution:**
```bash
# Pull with rebase
git pull --rebase origin main

# Resolve any conflicts
git add .
git rebase --continue

# Push again
git push origin main
```

### Disable Hooks Temporarily

**If you need to commit without auto-push:**
```bash
git commit --no-verify -m "Work in progress"
```

**If you need to push without running tests:**
```bash
git push --no-verify
```

## Branch Strategy

### Recommended Branches

```
main (production)
  ↓
develop (staging)
  ↓
feature/* (development)
```

### Working with Branches

**Create feature branch:**
```bash
git checkout -b feature/mobile-app
# Work on feature...
git commit -m "Add mobile app"
# Auto-syncs to feature/mobile-app
```

**Merge to develop:**
```bash
git checkout develop
git merge feature/mobile-app
git push origin develop
```

**Merge to main:**
```bash
git checkout main
git merge develop
git push origin main
```

## Best Practices

### Commit Messages

**Good:**
```bash
git commit -m "Add health check endpoint for production deployment"
git commit -m "Fix: Resolve image classification timeout issue"
git commit -m "Docs: Update production deployment guide"
```

**Avoid:**
```bash
git commit -m "updates"
git commit -m "fix"
git commit -m "wip"
```

### Commit Frequency

**Recommended:**
- Commit after completing a logical unit of work
- Commit before switching tasks
- Commit at end of day

**With auto-sync:**
- Each commit immediately syncs to GitHub
- Provides automatic backup
- Enables collaboration

### What to Commit

**Always commit:**
- ✅ Source code (`src/`)
- ✅ Tests (`tests/`)
- ✅ Documentation (`.md` files)
- ✅ Specs (`.kiro/specs/`)
- ✅ Configuration files
- ✅ Scripts

**Never commit:**
- ❌ Secrets/credentials (`.env` files)
- ❌ Virtual environments (`venv/`)
- ❌ Build artifacts (`__pycache__/`)
- ❌ IDE settings (`.idea/`, `.vscode/`)
- ❌ Large binary files

## Troubleshooting

### "Permission denied" Error

**Problem:** Can't push to GitHub

**Solution:**
```bash
# Set up SSH key or use HTTPS with token
git remote set-url origin https://YOUR_TOKEN@github.com/USER/REPO.git
```

### "Divergent branches" Error

**Problem:** Local and remote have different histories

**Solution:**
```bash
# Option 1: Rebase (recommended)
git pull --rebase origin main

# Option 2: Merge
git pull origin main

# Option 3: Force push (dangerous!)
git push --force origin main
```

### Hook Not Running

**Problem:** Auto-push not happening after commit

**Solution:**
```bash
# Reinstall hooks
./scripts/setup_git_hooks.sh

# Check hook permissions
ls -la .git/hooks/
chmod +x .git/hooks/post-commit
```

### Tests Failing on Push

**Problem:** Pre-push hook blocks push due to test failures

**Solution:**
```bash
# Fix tests first
pytest

# Or skip tests temporarily
git push --no-verify
```

## Advanced Configuration

### Customize Auto-Sync Behavior

**Edit `.git/hooks/post-commit`:**
```bash
#!/bin/bash
# Custom auto-sync behavior

# Only push during work hours
HOUR=$(date +%H)
if [ $HOUR -ge 9 ] && [ $HOUR -le 17 ]; then
    git push origin $(git rev-parse --abbrev-ref HEAD)
fi
```

### Sync Specific Files Only

**Create selective sync:**
```bash
# Only sync documentation
git add *.md
git commit -m "Update docs"

# Only sync code
git add src/ tests/
git commit -m "Update code"
```

### Schedule Periodic Syncs

**Add to crontab:**
```bash
# Sync every hour
0 * * * * cd /path/to/project && ./scripts/git_sync.sh

# Sync at end of day
0 17 * * * cd /path/to/project && ./scripts/git_sync.sh
```

## Integration with IDEs

### VS Code

**Install Git extension:**
- Auto-commit on save
- Visual diff viewer
- Branch management

**Settings:**
```json
{
  "git.enableSmartCommit": true,
  "git.autofetch": true,
  "git.confirmSync": false
}
```

### PyCharm/IntelliJ

**Enable auto-push:**
1. Settings → Version Control → Git
2. Check "Push automatically on commit"
3. Check "Run tests before push"

## Monitoring Sync Status

### Check Last Sync

```bash
# View recent commits
git log --oneline -5

# Check remote status
git remote show origin

# View sync history
git log --all --graph --oneline
```

### GitHub Actions Status

**View in GitHub:**
1. Go to repository
2. Click "Actions" tab
3. See auto-sync workflow runs

## Security Considerations

### Protect Sensitive Data

**Use `.gitignore`:**
```
# Secrets
.env
*.key
*.pem
secrets/

# Credentials
config/credentials.json
snowflake_credentials.txt

# Personal data
data/personal/
*.csv
```

### Review Before Push

**Even with auto-sync:**
```bash
# Check what will be committed
git status
git diff

# Review staged changes
git diff --cached
```

## Summary

### Quick Reference

| Task | Command |
|------|---------|
| Setup auto-sync | `./scripts/setup_git_hooks.sh` |
| Manual sync | `./scripts/git_sync.sh` |
| Commit only | `git commit --no-verify -m "msg"` |
| Push only | `git push origin main` |
| Check status | `git status` |
| View history | `git log --oneline` |
| Disable hooks | `git commit --no-verify` |

### Support

**Issues with auto-sync?**
1. Check `.git/hooks/` permissions
2. Verify GitHub credentials
3. Review error messages
4. Disable hooks temporarily: `git commit --no-verify`

**Need help?**
- Review this guide
- Check GitHub Actions logs
- Test with `./scripts/git_sync.sh`

---

*Auto-sync keeps your work backed up and enables seamless collaboration!* 🚀
