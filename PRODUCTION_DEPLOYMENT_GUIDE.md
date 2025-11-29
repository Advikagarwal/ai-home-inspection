# Production Deployment Guide

## Overview

This guide covers deploying the AI-Assisted Home Inspection Workspace to production using Streamlit Cloud or self-hosted options.

## Prerequisites

- Snowflake account with Cortex AI enabled
- GitHub repository with your code
- Production Snowflake credentials configured

## Deployment Options

### Option 1: Streamlit Community Cloud (Recommended)

**Advantages:**
- Free hosting
- Automatic deployments from GitHub
- Built-in SSL/HTTPS
- Easy configuration management

**Steps:**

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Production deployment configuration"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set main file path: `src/dashboard_app.py`
   - Click "Deploy"

3. **Configure Production Secrets**
   In Streamlit Cloud dashboard → App Settings → Secrets:
   ```toml
   [connections.snowflake]
   account = "qhvspfi-gx24863"
   user = "KUKUU81"
   password = "uZDPZHd2XibLK7h"
   warehouse = "COMPUTE_WH"
   database = "HOME_INSPECTION_DB"
   schema = "PUBLIC"
   role = "ACCOUNTADMIN"

   [general]
   environment = "production"
   ```

4. **Configure Advanced Settings**
   - Python version: 3.10
   - Main file path: `src/dashboard_app.py`
   - Requirements file: `requirements.txt`

### Option 2: Self-Hosted Production Server

**Use Case:** When you need more control or have specific security requirements

**Steps:**

1. **Prepare Server**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip python3-venv nginx certbot

   # Create application directory
   sudo mkdir -p /opt/home-inspection
   sudo chown $USER:$USER /opt/home-inspection
   cd /opt/home-inspection
   ```

2. **Deploy Application**
   ```bash
   # Clone repository
   git clone https://github.com/your-username/your-repo.git .

   # Run deployment script
   export SNOWFLAKE_PASSWORD="uZDPZHd2XibLK7h"
   ./scripts/deploy_production.sh
   ```

3. **Configure System Service**
   ```bash
   # Create systemd service
   sudo cp home-inspection-dashboard.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable home-inspection-dashboard
   sudo systemctl start home-inspection-dashboard
   ```

4. **Configure Reverse Proxy (Optional)**
   ```bash
   # Install and configure nginx for HTTPS
   sudo apt install nginx certbot python3-certbot-nginx

   # Get SSL certificate
   sudo certbot --nginx -d your-domain.com

   # Configure nginx (see nginx configuration below)
   ```

## Configuration Files

### Production Environment Variables

Create `.env.production`:
```bash
ENVIRONMENT=production
SNOWFLAKE_ACCOUNT=qhvspfi-gx24863
SNOWFLAKE_USER=KUKUU81
SNOWFLAKE_PASSWORD=uZDPZHd2XibLK7h
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=HOME_INSPECTION_DB
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=ACCOUNTADMIN
CONFIG_FILE=config/production.json
```

### Streamlit Configuration

The app uses `streamlit_cloud_config.toml` for production settings.

## Security Configuration

### 1. Snowflake Security

**Role-Based Access Control:**
```sql
-- Create production roles
CREATE ROLE INSPECTOR_ROLE;
CREATE ROLE STAKEHOLDER_ROLE;
CREATE ROLE ADMIN_ROLE;

-- Grant permissions
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE INSPECTOR_ROLE;
GRANT USAGE ON DATABASE HOME_INSPECTION_DB TO ROLE INSPECTOR_ROLE;
GRANT ALL ON SCHEMA HOME_INSPECTION_DB.PUBLIC TO ROLE INSPECTOR_ROLE;

-- Read-only access for stakeholders
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE STAKEHOLDER_ROLE;
GRANT USAGE ON DATABASE HOME_INSPECTION_DB TO ROLE STAKEHOLDER_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA HOME_INSPECTION_DB.PUBLIC TO ROLE STAKEHOLDER_ROLE;
```

### 2. Application Security

**Environment Variables:**
- Never commit passwords to Git
- Use Streamlit secrets for sensitive data
- Rotate credentials regularly

**Network Security:**
- Use HTTPS in production
- Configure firewall rules
- Enable rate limiting

## Monitoring and Maintenance

### Health Checks

The deployment script includes connection testing:
```bash
# Test deployment
./scripts/deploy_production.sh test
```

### Monitoring

**Streamlit Cloud:**
- Built-in app metrics
- Error logging in dashboard
- Automatic restarts

**Self-Hosted:**
- System logs: `journalctl -u home-inspection-dashboard`
- Application logs: Check Streamlit output
- Snowflake logs: Query history in Snowflake console

### Updates

**Streamlit Cloud:**
- Automatic deployment on Git push
- No manual intervention needed

**Self-Hosted:**
```bash
# Update application
cd /opt/home-inspection
git pull origin main
sudo systemctl restart home-inspection-dashboard
```

## Performance Optimization

### Snowflake Optimization

1. **Warehouse Sizing:**
   - Start with SMALL warehouse
   - Scale up based on usage
   - Use auto-suspend for cost control

2. **Query Optimization:**
   - Use materialized views for aggregations
   - Implement result caching
   - Monitor query performance

### Application Optimization

1. **Caching:**
   ```python
   @st.cache_data(ttl=600)  # 10 minutes
   def load_properties():
       # Expensive query
   ```

2. **Pagination:**
   - Limit results per page
   - Implement lazy loading
   - Use filters to reduce data

## Troubleshooting

### Common Issues

**Connection Errors:**
```
snowflake.connector.errors.DatabaseError: 250001: None: Connection error
```
- Check network connectivity
- Verify Snowflake account identifier
- Confirm credentials

**Permission Errors:**
```
SQL access control error: Insufficient privileges
```
- Check user roles and permissions
- Verify warehouse access
- Contact Snowflake administrator

**Performance Issues:**
- Check Snowflake warehouse size
- Review query execution plans
- Implement caching strategies

### Getting Help

1. **Streamlit Cloud:** Check app logs in dashboard
2. **Self-Hosted:** Check system logs with `journalctl`
3. **Snowflake:** Review query history and error messages
4. **Application:** Enable debug logging in configuration

## Cost Management

### Snowflake Costs

1. **Warehouse Management:**
   - Use auto-suspend (1 minute)
   - Right-size warehouses
   - Monitor credit usage

2. **Storage Optimization:**
   - Archive old inspection data
   - Use appropriate data types
   - Compress large text fields

3. **Cortex AI Usage:**
   - Batch process classifications
   - Cache results when possible
   - Monitor AI function costs

### Streamlit Cloud

- Free tier includes:
  - 1 GB RAM
  - Unlimited public apps
  - Community support

## Next Steps

After successful deployment:

1. **Generate Sample Data:**
   ```bash
   python tests/generate_sample_data.py
   ```

2. **User Training:**
   - Create user accounts
   - Provide dashboard training
   - Document workflows

3. **Monitoring Setup:**
   - Configure alerts
   - Set up regular backups
   - Monitor performance metrics

4. **Feedback Collection:**
   - Gather user feedback
   - Plan feature enhancements
   - Iterate based on usage patterns