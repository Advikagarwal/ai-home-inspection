# Streamlit Dashboard Deployment Guide

## Overview

The AI-Assisted Home Inspection Dashboard is built with Streamlit and integrates directly with Snowflake for data access and AI processing.

## Prerequisites

- Python 3.8 or higher
- Snowflake account with Cortex AI enabled
- Database schema initialized (see `schema/init_schema.sql`)

## Local Development Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `streamlit>=1.28.0`
- `snowflake-connector-python>=3.0.0`
- `snowflake-snowpark-python` (optional, for advanced features)

### 2. Configure Snowflake Connection

#### Option A: Streamlit Secrets (Recommended)

Create `.streamlit/secrets.toml`:

```toml
[connections.snowflake]
account = "xy12345.us-east-1"
user = "your_username"
password = "your_password"
warehouse = "COMPUTE_WH"
database = "HOME_INSPECTION_DB"
schema = "PUBLIC"
role = "ACCOUNTADMIN"  # Optional
```

#### Option B: Environment Variables

```bash
export SNOWFLAKE_ACCOUNT="xy12345.us-east-1"
export SNOWFLAKE_USER="your_username"
export SNOWFLAKE_PASSWORD="your_password"
export SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
export SNOWFLAKE_DATABASE="HOME_INSPECTION_DB"
export SNOWFLAKE_SCHEMA="PUBLIC"
```

#### Option C: SSO Authentication

For browser-based SSO:

```toml
[connections.snowflake]
account = "xy12345.us-east-1"
user = "your_username"
authenticator = "externalbrowser"
warehouse = "COMPUTE_WH"
database = "HOME_INSPECTION_DB"
schema = "PUBLIC"
```

### 3. Initialize Database Schema

```bash
# Connect to Snowflake and run the schema initialization
snowsql -a your-account -u your-user -f schema/init_schema.sql
```

### 4. Run the Dashboard

```bash
streamlit run src/dashboard_app.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Deployment Options

### Option 1: Streamlit Community Cloud (Free)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add Streamlit dashboard"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set main file path: `src/dashboard_app.py`
   - Click "Deploy"

3. **Configure Secrets**
   - In Streamlit Cloud dashboard, go to app settings
   - Click "Secrets"
   - Add your Snowflake credentials:
   ```toml
   [connections.snowflake]
   account = "xy12345.us-east-1"
   user = "your_username"
   password = "your_password"
   warehouse = "COMPUTE_WH"
   database = "HOME_INSPECTION_DB"
   schema = "PUBLIC"
   ```

### Option 2: Snowflake Native App (Streamlit in Snowflake)

Deploy directly within Snowflake for maximum security and performance.

1. **Create Streamlit App in Snowflake**
   ```sql
   CREATE STREAMLIT HOME_INSPECTION_DASHBOARD
     ROOT_LOCATION = '@streamlit_stage'
     MAIN_FILE = 'dashboard_app.py'
     QUERY_WAREHOUSE = 'COMPUTE_WH';
   ```

2. **Upload Files**
   ```sql
   PUT file://src/dashboard_app.py @streamlit_stage AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
   PUT file://src/dashboard_data.py @streamlit_stage AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
   ```

3. **Grant Access**
   ```sql
   GRANT USAGE ON STREAMLIT HOME_INSPECTION_DASHBOARD TO ROLE INSPECTOR_ROLE;
   GRANT USAGE ON STREAMLIT HOME_INSPECTION_DASHBOARD TO ROLE STAKEHOLDER_ROLE;
   ```

### Option 3: Docker Container

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.10-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY src/ ./src/
   COPY .streamlit/ ./.streamlit/
   
   EXPOSE 8501
   
   CMD ["streamlit", "run", "src/dashboard_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```

2. **Build and Run**
   ```bash
   docker build -t home-inspection-dashboard .
   docker run -p 8501:8501 \
     -e SNOWFLAKE_ACCOUNT="your-account" \
     -e SNOWFLAKE_USER="your-user" \
     -e SNOWFLAKE_PASSWORD="your-password" \
     -e SNOWFLAKE_WAREHOUSE="COMPUTE_WH" \
     -e SNOWFLAKE_DATABASE="HOME_INSPECTION_DB" \
     home-inspection-dashboard
   ```

### Option 4: AWS/Azure/GCP

Deploy to cloud platforms using their container services:

- **AWS**: ECS, Fargate, or App Runner
- **Azure**: Container Instances or App Service
- **GCP**: Cloud Run or App Engine

## Dashboard Features

### Property List View
- Browse all inspected properties
- Color-coded risk indicators (🟢 Low, 🟠 Medium, 🔴 High)
- Quick summary preview
- Sortable and filterable

### Filtering & Search
- **Risk Level**: Filter by Low, Medium, or High risk
- **Defect Type**: Filter by specific defect categories
- **Search**: Search by location, property ID, or summary text
- **Multi-filter**: Combine multiple filters

### Property Details
- Complete property information
- Room-by-room breakdown
- All findings with defect tags
- AI-generated summaries
- Risk scores and categorization

### Room Details
- Finding-level information
- Text notes and image references
- Detected defects with confidence scores
- Severity indicators

## Configuration

### Streamlit Configuration

Create `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
```

### Performance Optimization

For large datasets, consider:

1. **Caching**: Use `@st.cache_data` for expensive queries
2. **Pagination**: Implement pagination for property lists
3. **Lazy Loading**: Load room details on demand
4. **Materialized Views**: Use Snowflake materialized views for aggregations

## Security Best Practices

1. **Never commit secrets**: Add `.streamlit/secrets.toml` to `.gitignore`
2. **Use least privilege**: Create dedicated Snowflake roles with minimal permissions
3. **Enable MFA**: Require multi-factor authentication for Snowflake accounts
4. **Audit logging**: Enable Snowflake query history and access logs
5. **HTTPS only**: Always use HTTPS in production
6. **Session management**: Configure appropriate session timeouts

## Monitoring & Maintenance

### Health Checks

Monitor:
- Snowflake connection status
- Query performance
- Error rates
- User activity

### Logging

Streamlit logs are available at:
- Local: Terminal output
- Cloud: Streamlit Cloud logs dashboard
- Snowflake: Query history and access logs

### Updates

To update the dashboard:

1. **Local/Docker**: Pull latest code and restart
2. **Streamlit Cloud**: Push to GitHub (auto-deploys)
3. **Snowflake Native**: Re-upload files to stage

## Troubleshooting

### Connection Issues

**Problem**: "Snowflake connection not configured"
- **Solution**: Check secrets.toml or environment variables
- **Verify**: Account identifier format (e.g., `xy12345.us-east-1`)

**Problem**: "Authentication failed"
- **Solution**: Verify username and password
- **Check**: User has necessary permissions

### Performance Issues

**Problem**: Slow dashboard loading
- **Solution**: Implement caching with `@st.cache_data`
- **Check**: Snowflake warehouse size
- **Optimize**: Use materialized views

### Data Issues

**Problem**: "No properties found"
- **Solution**: Verify data exists in database
- **Check**: Run sample data generator: `python tests/generate_sample_data.py`

## Support

For issues or questions:
1. Check Streamlit documentation: https://docs.streamlit.io
2. Check Snowflake documentation: https://docs.snowflake.com
3. Review application logs
4. Contact your Snowflake administrator

## Next Steps

After deployment:
1. Generate sample data for testing
2. Configure user roles and permissions
3. Set up monitoring and alerts
4. Train users on dashboard features
5. Gather feedback and iterate
