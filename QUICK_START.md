# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Option 1: Automated Setup (Recommended)

```bash
# Run the setup script
./scripts/initial_setup.sh
```

This will:
- ✅ Initialize Git repository
- ✅ Configure GitHub remote
- ✅ Create environment file
- ✅ Set up Python virtual environment
- ✅ Install dependencies
- ✅ Configure Git auto-sync
- ✅ Create initial commit

### Option 2: Manual Setup

```bash
# 1. Clone or initialize repository
git init
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# 2. Set up Python environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your Snowflake credentials

# 4. Set up Git auto-sync (optional)
./scripts/setup_git_hooks.sh

# 5. Commit and push
git add .
git commit -m "Initial setup"
git push -u origin main
```

## 📋 Essential Commands

### Run Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test
pytest tests/test_data_ingestion.py
```

### Run Dashboard
```bash
# Start Streamlit dashboard
streamlit run src/dashboard_app.py

# Access at: http://localhost:8501
```

### Generate Sample Data
```bash
# Create test data
python tests/generate_sample_data.py
```

### Git Auto-Sync
```bash
# Manual sync (commits and pushes everything)
./scripts/git_sync.sh

# Or use normal Git (auto-pushes if hooks installed)
git add .
git commit -m "Your message"
# Auto-push happens here!
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview |
| `GIT_WORKFLOW.md` | Git auto-sync guide |
| `PRODUCTION_READINESS.md` | Deployment options |
| `ROADMAP.md` | Product roadmap |
| `PROJECT_STATUS.md` | Current status |
| `.kiro/specs/` | All specifications |

## 🎯 What to Do Next

### 1. Review the System
```bash
# Read the overview
cat README.md

# Check project status
cat PROJECT_STATUS.md

# Review specs
ls -la .kiro/specs/
```

### 2. Run Tests
```bash
# Verify everything works
pytest

# Check coverage
pytest --cov=src
```

### 3. Try the Dashboard
```bash
# Generate sample data
python tests/generate_sample_data.py

# Start dashboard
streamlit run src/dashboard_app.py
```

### 4. Choose Your Path

**Path A: Production Deployment**
```bash
# Review production spec
cat .kiro/specs/production-deployment/requirements.md

# Start with task 1
# See: .kiro/specs/production-deployment/tasks.md
```

**Path B: Future Features**
```bash
# Review future enhancements
cat .kiro/specs/future-enhancements/requirements.md

# Check roadmap
cat ROADMAP.md
```

**Path C: Demo Mode**
```bash
# Generate sample data
python tests/generate_sample_data.py

# Run dashboard
streamlit run src/dashboard_app.py

# Prepare presentation
```

## 🔧 Configuration

### Snowflake Setup
Edit `.env`:
```bash
SNOWFLAKE_ACCOUNT=your-account.region
SNOWFLAKE_USER=your-username
SNOWFLAKE_PASSWORD=your-password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=INSPECTION_DB
SNOWFLAKE_SCHEMA=PUBLIC
```

### GitHub Auto-Sync
```bash
# Install hooks
./scripts/setup_git_hooks.sh

# Test sync
./scripts/git_sync.sh
```

## 🆘 Troubleshooting

### Tests Failing?
```bash
# Check Python version (need 3.8+)
python --version

# Reinstall dependencies
pip install -r requirements.txt

# Run specific test
pytest tests/test_data_ingestion.py -v
```

### Dashboard Not Starting?
```bash
# Check Streamlit installation
pip install streamlit

# Try different port
streamlit run src/dashboard_app.py --server.port 8502
```

### Git Sync Issues?
```bash
# Check Git status
git status

# Verify remote
git remote -v

# Manual push
git push origin main
```

## 📚 Documentation

- **README.md** - Project overview and features
- **GIT_WORKFLOW.md** - Complete Git auto-sync guide
- **PRODUCTION_READINESS.md** - Deployment guide with 3 paths
- **ROADMAP.md** - 5-phase product roadmap
- **PROJECT_STATUS.md** - Current status and metrics
- **.kiro/specs/** - All technical specifications

## 💡 Tips

### Daily Workflow
```bash
# Morning: Pull latest
git pull

# Work: Edit files...

# Commit: Auto-syncs to GitHub
git add .
git commit -m "Your changes"

# Evening: Verify sync
git log --oneline -5
```

### Before Committing
```bash
# Check what changed
git status
git diff

# Run tests
pytest

# Commit
git add .
git commit -m "Descriptive message"
```

### Collaboration
```bash
# Create feature branch
git checkout -b feature/new-feature

# Work and commit
git commit -m "Add new feature"

# Push feature branch
git push origin feature/new-feature

# Merge via pull request on GitHub
```

## 🎓 Learning Resources

### Understand the System
1. Read `README.md` for overview
2. Review `.kiro/specs/ai-home-inspection/requirements.md`
3. Study `.kiro/specs/ai-home-inspection/design.md`
4. Explore source code in `src/`

### Production Deployment
1. Read `PRODUCTION_READINESS.md`
2. Review `.kiro/specs/production-deployment/`
3. Follow tasks in order

### Future Planning
1. Read `ROADMAP.md`
2. Review `.kiro/specs/future-enhancements/`
3. Prioritize features

## ✅ Checklist

- [ ] Repository cloned/initialized
- [ ] Python environment set up
- [ ] Dependencies installed
- [ ] `.env` file configured
- [ ] Tests passing
- [ ] Dashboard running
- [ ] Git auto-sync configured
- [ ] Initial commit pushed
- [ ] Documentation reviewed
- [ ] Next steps decided

## 🚀 You're Ready!

Your AI Home Inspection Workspace is set up and ready to go!

**Choose your path:**
1. **Production** → Review `PRODUCTION_READINESS.md`
2. **Future** → Review `ROADMAP.md`
3. **Demo** → Run `streamlit run src/dashboard_app.py`

**Questions?** Check the documentation or review the specs in `.kiro/specs/`

Happy coding! 🎉
