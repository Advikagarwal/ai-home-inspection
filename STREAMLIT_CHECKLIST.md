# ✅ Streamlit Dashboard Setup Checklist

Use this checklist to get your AI-Assisted Home Inspection Dashboard up and running.

## 📋 Pre-Setup Checklist

- [ ] Python 3.8 or higher installed
  ```bash
  python3 --version
  ```

- [ ] Snowflake account with Cortex AI enabled
  - [ ] Account identifier (e.g., `xy12345.us-east-1`)
  - [ ] Username and password (or SSO)
  - [ ] Warehouse name (e.g., `COMPUTE_WH`)
  - [ ] Database created (`HOME_INSPECTION_DB`)

- [ ] Git repository cloned
  ```bash
  git clone <your-repo-url>
  cd ai-home-inspection
  ```

## 🔧 Configuration Checklist

### Option 1: Streamlit Secrets (Recommended)

- [ ] Copy secrets template
  ```bash
  cp .streamlit/secrets.toml.example .streamlit/secrets.toml
  ```

- [ ] Edit `.streamlit/secrets.toml` with your credentials
  - [ ] `account` = Your Snowflake account identifier
  - [ ] `user` = Your Snowflake username
  - [ ] `password` = Your Snowflake password (or use `authenticator`)
  - [ ] `warehouse` = Your Snowflake warehouse name
  - [ ] `database` = `HOME_INSPECTION_DB`
  - [ ] `schema` = `PUBLIC`

- [ ] Verify secrets file is in `.gitignore`
  ```bash
  grep "secrets.toml" .gitignore
  ```

### Option 2: Environment Variables

- [ ] Set environment variables
  ```bash
  export SNOWFLAKE_ACCOUNT="xy12345.us-east-1"
  export SNOWFLAKE_USER="your_username"
  export SNOWFLAKE_PASSWORD="your_password"
  export SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
  export SNOWFLAKE_DATABASE="HOME_INSPECTION_DB"
  export SNOWFLAKE_SCHEMA="PUBLIC"
  ```

- [ ] Verify variables are set
  ```bash
  echo $SNOWFLAKE_ACCOUNT
  ```

## 🗄️ Database Setup Checklist

- [ ] Connect to Snowflake
  ```bash
  snowsql -a <account> -u <user>
  ```

- [ ] Create database
  ```sql
  CREATE DATABASE HOME_INSPECTION_DB;
  USE DATABASE HOME_INSPECTION_DB;
  ```

- [ ] Run schema initialization
  ```bash
  snowsql -a <account> -u <user> -f schema/init_schema.sql
  ```

- [ ] Verify tables created
  ```sql
  SHOW TABLES;
  ```
  Should see: `properties`, `rooms`, `findings`, `defect_tags`, `classification_history`, `error_log`

- [ ] Verify stage created
  ```sql
  SHOW STAGES;
  ```
  Should see: `inspections`

## 🚀 Launch Checklist

### Quick Start Method

- [ ] Run launch script
  ```bash
  ./run_dashboard.sh  # Linux/Mac
  # OR
  run_dashboard.bat   # Windows
  ```

- [ ] Wait for automatic setup
  - [ ] Virtual environment created
  - [ ] Dependencies installed
  - [ ] Dashboard launched

- [ ] Browser opens automatically at `http://localhost:8501`

### Manual Method

- [ ] Create virtual environment
  ```bash
  python3 -m venv venv
  ```

- [ ] Activate virtual environment
  ```bash
  source venv/bin/activate  # Linux/Mac
  # OR
  venv\Scripts\activate     # Windows
  ```

- [ ] Install dependencies
  ```bash
  pip install -r requirements.txt
  ```

- [ ] Run Streamlit
  ```bash
  streamlit run src/dashboard_app.py
  ```

- [ ] Open browser at `http://localhost:8501`

## ✅ Verification Checklist

### Connection Verification

- [ ] Dashboard loads without errors
- [ ] See "✅ Connected to Snowflake" message
- [ ] No connection error messages

### Data Verification

- [ ] Generate sample data (if needed)
  ```bash
  python tests/generate_sample_data.py
  ```

- [ ] Property list displays
- [ ] Can see property count
- [ ] Properties show risk indicators

### Feature Verification

- [ ] **Filtering**
  - [ ] Risk level filter works
  - [ ] Defect type filter works
  - [ ] Search works
  - [ ] Clear filters works

- [ ] **Property Details**
  - [ ] Can click "View Details"
  - [ ] Property details display
  - [ ] Rooms are listed
  - [ ] Findings are shown
  - [ ] Defect tags are visible

- [ ] **Navigation**
  - [ ] "Back to Property List" works
  - [ ] Can navigate between properties

- [ ] **Export**
  - [ ] Export format selector works
  - [ ] "Export All Properties" button works
  - [ ] Download button appears
  - [ ] File downloads successfully

## 🧪 Testing Checklist

- [ ] Run integration tests
  ```bash
  pytest tests/test_streamlit_integration.py -v
  ```

- [ ] All tests pass (13/13)

- [ ] Run full test suite
  ```bash
  pytest --cov=src
  ```

- [ ] Coverage report generated

## 🔒 Security Checklist

- [ ] Secrets file not committed to git
  ```bash
  git status
  # Should NOT see .streamlit/secrets.toml
  ```

- [ ] No credentials in code
  ```bash
  grep -r "password" src/
  # Should only see variable names, not actual passwords
  ```

- [ ] Error messages don't expose sensitive data
  - [ ] Test by entering wrong credentials
  - [ ] Verify error message is generic

- [ ] HTTPS enabled (for production)

## 📚 Documentation Checklist

- [ ] Read `STREAMLIT_README.md`
- [ ] Review `STREAMLIT_DEPLOYMENT.md`
- [ ] Understand `STREAMLIT_ARCHITECTURE.md`
- [ ] Check `IMPLEMENTATION_SUMMARY.md`

## 🎯 Production Deployment Checklist

### Pre-Deployment

- [ ] Choose deployment option
  - [ ] Streamlit Community Cloud
  - [ ] Snowflake Native App
  - [ ] Docker Container
  - [ ] Cloud Platform (AWS/Azure/GCP)

- [ ] Review deployment guide
  - [ ] See `STREAMLIT_DEPLOYMENT.md`

- [ ] Set up production Snowflake environment
  - [ ] Production database
  - [ ] Production warehouse
  - [ ] Production roles and permissions

### Deployment

- [ ] Deploy application
- [ ] Configure production secrets
- [ ] Test production connection
- [ ] Verify all features work

### Post-Deployment

- [ ] Set up monitoring
- [ ] Configure alerts
- [ ] Document access procedures
- [ ] Train users

## 🐛 Troubleshooting Checklist

### Connection Issues

- [ ] Verify Snowflake account identifier format
  - Should be: `xy12345.us-east-1` (not just `xy12345`)

- [ ] Check username and password
  - [ ] Try logging in via Snowflake web UI

- [ ] Verify warehouse exists and is running
  ```sql
  SHOW WAREHOUSES;
  ```

- [ ] Check database and schema exist
  ```sql
  SHOW DATABASES;
  USE DATABASE HOME_INSPECTION_DB;
  SHOW SCHEMAS;
  ```

### Data Issues

- [ ] Verify tables have data
  ```sql
  SELECT COUNT(*) FROM properties;
  ```

- [ ] Generate sample data if empty
  ```bash
  python tests/generate_sample_data.py
  ```

- [ ] Check for errors in error_log table
  ```sql
  SELECT * FROM error_log ORDER BY occurred_at DESC LIMIT 10;
  ```

### Performance Issues

- [ ] Check Snowflake warehouse size
  ```sql
  SHOW WAREHOUSES;
  ```

- [ ] Consider using MEDIUM or LARGE warehouse

- [ ] Verify materialized views are refreshed
  ```sql
  SHOW MATERIALIZED VIEWS;
  ```

## 📊 Success Criteria

Your dashboard is ready when:

- ✅ Dashboard loads without errors
- ✅ Snowflake connection successful
- ✅ Properties display with correct data
- ✅ All filters work correctly
- ✅ Property details show complete information
- ✅ Export functionality works
- ✅ All tests pass
- ✅ No security issues

## 🎉 Completion

Once all items are checked:

- [ ] Dashboard is fully functional
- [ ] All features tested and working
- [ ] Documentation reviewed
- [ ] Ready for production (if applicable)

**Congratulations! Your AI-Assisted Home Inspection Dashboard is ready to use! 🏠✨**

---

## 📞 Need Help?

- **Quick Start**: See `STREAMLIT_README.md`
- **Deployment**: See `STREAMLIT_DEPLOYMENT.md`
- **Architecture**: See `STREAMLIT_ARCHITECTURE.md`
- **Troubleshooting**: See `STREAMLIT_DEPLOYMENT.md` section "Troubleshooting"

## 🔄 Next Steps

After completing this checklist:

1. Start using the dashboard for inspections
2. Gather user feedback
3. Plan enhancements
4. Consider production deployment
5. Set up monitoring and alerts
