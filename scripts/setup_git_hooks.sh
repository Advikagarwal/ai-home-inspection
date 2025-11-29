#!/bin/bash

# Setup Git Hooks for Auto-Sync
# This script installs git hooks that automatically sync changes

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🔧 Setting up Git hooks for auto-sync...${NC}"

# Create post-commit hook
cat > .git/hooks/post-commit << 'EOF'
#!/bin/bash
# Auto-sync after commit

echo "🔄 Auto-syncing to GitHub..."
git push origin $(git rev-parse --abbrev-ref HEAD) 2>/dev/null || echo "⚠️  Push failed - will retry later"
EOF

chmod +x .git/hooks/post-commit

# Create pre-push hook for validation
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
# Validate before push

echo "🔍 Running pre-push validation..."

# Run tests if they exist
if [ -f "pytest.ini" ] || [ -d "tests" ]; then
    echo "🧪 Running tests..."
    if ! pytest --tb=short -q 2>/dev/null; then
        echo "❌ Tests failed. Push aborted."
        echo "💡 Fix tests or use 'git push --no-verify' to skip"
        exit 1
    fi
fi

echo "✅ Validation passed"
EOF

chmod +x .git/hooks/pre-push

echo -e "${GREEN}✅ Git hooks installed successfully!${NC}"
echo -e "${YELLOW}📝 Hooks installed:${NC}"
echo -e "  - post-commit: Auto-push after commit"
echo -e "  - pre-push: Run tests before push"
echo -e "\n${YELLOW}💡 To disable hooks temporarily, use:${NC}"
echo -e "  git commit --no-verify"
echo -e "  git push --no-verify"
