#!/bin/bash

# Initial Project Setup Script
# Sets up Git, environment, and auto-sync

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AI Home Inspection - Initial Setup       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Check Git
echo -e "${GREEN}📋 Step 1: Checking Git configuration...${NC}"
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}⚠️  Git not found. Please install Git first.${NC}"
    exit 1
fi

if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${YELLOW}📦 Initializing Git repository...${NC}"
    git init
    echo -e "${GREEN}✅ Git repository initialized${NC}"
else
    echo -e "${GREEN}✅ Git repository already exists${NC}"
fi

# Step 2: Check remote
echo -e "\n${GREEN}📋 Step 2: Checking GitHub remote...${NC}"
if ! git remote | grep -q origin; then
    echo -e "${YELLOW}⚠️  No GitHub remote configured${NC}"
    echo -e "${BLUE}Please enter your GitHub repository URL:${NC}"
    read -p "URL: " REPO_URL
    git remote add origin "$REPO_URL"
    echo -e "${GREEN}✅ Remote added: $REPO_URL${NC}"
else
    REMOTE_URL=$(git remote get-url origin)
    echo -e "${GREEN}✅ Remote already configured: $REMOTE_URL${NC}"
fi

# Step 3: Environment setup
echo -e "\n${GREEN}📋 Step 3: Setting up environment...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ .env file created${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env with your credentials${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Step 4: Python environment
echo -e "\n${GREEN}📋 Step 4: Checking Python environment...${NC}"
if [ ! -d venv ]; then
    echo -e "${YELLOW}🐍 Creating Python virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

echo -e "${YELLOW}📦 Installing dependencies...${NC}"
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Step 5: Git hooks
echo -e "\n${GREEN}📋 Step 5: Setting up Git auto-sync...${NC}"
./scripts/setup_git_hooks.sh

# Step 6: Initial commit
echo -e "\n${GREEN}📋 Step 6: Creating initial commit...${NC}"
if [ -z "$(git log 2>/dev/null)" ]; then
    echo -e "${YELLOW}📝 Creating initial commit...${NC}"
    git add .
    git commit -m "Initial commit: AI Home Inspection Workspace

- Core system implementation complete (v1.0)
- Production deployment spec added
- Future enhancements roadmap created
- Git auto-sync configured
- Documentation complete"
    echo -e "${GREEN}✅ Initial commit created${NC}"
else
    echo -e "${GREEN}✅ Repository already has commits${NC}"
fi

# Step 7: Push to GitHub
echo -e "\n${GREEN}📋 Step 7: Pushing to GitHub...${NC}"
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "${BLUE}Push to GitHub? (y/n)${NC}"
read -p "Answer: " PUSH_CONFIRM

if [ "$PUSH_CONFIRM" = "y" ] || [ "$PUSH_CONFIRM" = "Y" ]; then
    if git push -u origin "$BRANCH"; then
        echo -e "${GREEN}✅ Successfully pushed to GitHub!${NC}"
    else
        echo -e "${YELLOW}⚠️  Push failed. You may need to set up authentication.${NC}"
        echo -e "${BLUE}💡 Try: git push -u origin $BRANCH${NC}"
    fi
else
    echo -e "${YELLOW}⏭️  Skipped push to GitHub${NC}"
fi

# Summary
echo -e "\n${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           Setup Complete! 🎉               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo -e "\n${GREEN}✅ What's been set up:${NC}"
echo -e "  • Git repository initialized"
echo -e "  • GitHub remote configured"
echo -e "  • Environment file created (.env)"
echo -e "  • Python virtual environment ready"
echo -e "  • Dependencies installed"
echo -e "  • Git auto-sync hooks installed"
echo -e "  • Initial commit created"
echo -e "\n${YELLOW}📝 Next steps:${NC}"
echo -e "  1. Edit .env with your Snowflake credentials"
echo -e "  2. Run tests: ${BLUE}pytest${NC}"
echo -e "  3. Start dashboard: ${BLUE}streamlit run src/dashboard_app.py${NC}"
echo -e "  4. Review specs in ${BLUE}.kiro/specs/${NC}"
echo -e "\n${YELLOW}📚 Documentation:${NC}"
echo -e "  • README.md - Project overview"
echo -e "  • GIT_WORKFLOW.md - Git auto-sync guide"
echo -e "  • PRODUCTION_READINESS.md - Deployment guide"
echo -e "  • ROADMAP.md - Product roadmap"
echo -e "\n${GREEN}🚀 Happy coding!${NC}"
