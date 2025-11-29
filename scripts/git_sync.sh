#!/bin/bash

# Git Auto-Sync Script
# Automatically commits and pushes changes to GitHub

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔄 Starting Git Auto-Sync...${NC}"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Not a git repository${NC}"
    exit 1
fi

# Check for uncommitted changes
if [[ -z $(git status -s) ]]; then
    echo -e "${YELLOW}✓ No changes to commit${NC}"
    exit 0
fi

# Get current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "${GREEN}📍 Current branch: ${BRANCH}${NC}"

# Stage all changes
echo -e "${GREEN}📦 Staging changes...${NC}"
git add -A

# Generate commit message with timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
COMMIT_MSG="Auto-sync: ${TIMESTAMP}"

# Check if there are specific file patterns to highlight
if git diff --cached --name-only | grep -q "\.kiro/specs"; then
    COMMIT_MSG="${COMMIT_MSG} [specs updated]"
fi

if git diff --cached --name-only | grep -q "src/"; then
    COMMIT_MSG="${COMMIT_MSG} [code updated]"
fi

if git diff --cached --name-only | grep -q "tests/"; then
    COMMIT_MSG="${COMMIT_MSG} [tests updated]"
fi

if git diff --cached --name-only | grep -q "\.md$"; then
    COMMIT_MSG="${COMMIT_MSG} [docs updated]"
fi

# Commit changes
echo -e "${GREEN}💾 Committing changes...${NC}"
git commit -m "${COMMIT_MSG}"

# Pull latest changes with rebase
echo -e "${GREEN}⬇️  Pulling latest changes...${NC}"
if ! git pull --rebase origin "${BRANCH}"; then
    echo -e "${RED}❌ Error: Failed to pull changes. Please resolve conflicts manually.${NC}"
    exit 1
fi

# Push changes
echo -e "${GREEN}⬆️  Pushing to GitHub...${NC}"
if git push origin "${BRANCH}"; then
    echo -e "${GREEN}✅ Successfully synced to GitHub!${NC}"
    echo -e "${GREEN}📊 Commit: ${COMMIT_MSG}${NC}"
else
    echo -e "${RED}❌ Error: Failed to push changes${NC}"
    exit 1
fi

# Show summary
echo -e "\n${GREEN}📈 Summary:${NC}"
git log -1 --stat
