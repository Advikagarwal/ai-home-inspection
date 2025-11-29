# Streamlit Dashboard - Quick Start Guide

## 🚀 Quick Start

### Run Locally (Easiest)

**Linux/Mac:**
```bash
./run_dashboard.sh
```

**Windows:**
```bash
run_dashboard.bat
```

The dashboard will automatically:
1. Create a virtual environment (if needed)
2. Install dependencies
3. Launch at http://localhost:8501

### Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run dashboard
streamlit run src/dashboard_app.py
```

## 🔧 Configuration

### Snowflake Connection

Create `.streamlit/secrets.toml`:

```toml
[connections.snowflake]
account = "xy12345.us-east-1"
user = "your_username"
password = "your_password"
warehouse = "COMPUTE_WH"
database = "HOME_INSPECTION_DB"
schema = "PUBLIC"
```

See `.streamlit/secrets.toml.example` for a complete template.

### Alternative: Environment Variables

```bash
export SNOWFLAKE_ACCOUNT="xy12345.us-east-1"
export SNOWFLAKE_USER="your_username"
export SNOWFLAKE_PASSWORD="your_password"
export SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
export SNOWFLAKE_DATABASE="HOME_INSPECTION_DB"
```

## 📊 Dashboard Features

### Property List View
- **Browse Properties**: View all inspected properties with risk indicators
- **Color Coding**: 🟢 Low, 🟠 Medium, 🔴 High risk levels
- **Quick Summaries**: AI-generated summaries at a glance

### Filtering & Search
- **Risk Level Filter**: Show only Low, Medium, or High risk properties
- **Defect Type Filter**: Filter by specific defect categories
  - Damp wall
  - Exposed wiring
  - Crack
  - Mold
  - Water leak
  - Electrical wiring
- **Search**: Find properties by location, ID, or summary text
- **Multi-Filter**: Combine multiple filters for precise results

### Property Details
- **Complete Information**: All property metadata and inspection data
- **Room Breakdown**: Detailed view of each room with risk scores
- **Findings**: Text notes and image references
- **Defect Tags**: AI-detected defects with confidence scores
- **Severity Indicators**: Color-coded severity levels

### Export
- **PDF Reports**: Generate detailed PDF reports with images
- **CSV Export**: Export all data for external analysis
- **Download**: One-click download of generated reports

## 🎨 Dashboard Navigation

### Main View (Property List)
1. Use sidebar filters to narrow down properties
2. Click "View Details" on any property to see full information
3. Use "Clear All Filters" to reset

### Detail View
1. Click "← Back to Property List" to return
2. Expand room sections to see findings
3. View defect tags with confidence scores
4. See AI-generated summaries

### Export
1. Select format (PDF or CSV) in sidebar
2. Click "Export All Properties"
3. Download generated file

## 🔒 Security

The dashboard implements several security features:

1. **Error Sanitization**: Sensitive information is never displayed in error messages
2. **Secure Connections**: All Snowflake connections use encrypted channels
3. **Secrets Management**: Credentials stored securely in secrets.toml (not in code)
4. **Input Validation**: All user inputs are validated before processing

## 🐛 Troubleshooting

### "Snowflake connection not configured"
- **Cause**: Missing or incorrect connection configuration
- **Fix**: Create `.streamlit/secrets.toml` with valid credentials
- **Check**: Verify account identifier format (e.g., `xy12345.us-east-1`)

### "No properties found"
- **Cause**: Database is empty or filters are too restrictive
- **Fix**: Generate sample data: `python tests/generate_sample_data.py`
- **Check**: Clear all filters to see all properties

### Dashboard won't start
- **Cause**: Missing dependencies or Python version issues
- **Fix**: Ensure Python 3.8+ is installed
- **Run**: `pip install -r requirements.txt`

### Slow performance
- **Cause**: Large dataset or slow Snowflake warehouse
- **Fix**: Use a larger Snowflake warehouse
- **Optimize**: Ensure materialized views are refreshed

## 📈 Performance Tips

1. **Use Materialized Views**: Pre-aggregate data for faster queries
2. **Appropriate Warehouse Size**: Use MEDIUM or LARGE for production
3. **Caching**: Streamlit caches query results automatically
4. **Pagination**: For very large datasets, implement pagination

## 🌐 Deployment Options

### 1. Streamlit Community Cloud (Free)
- Push to GitHub
- Deploy at share.streamlit.io
- Add secrets in cloud dashboard

### 2. Snowflake Native App
- Deploy directly in Snowflake
- Maximum security and performance
- No external hosting needed

### 3. Docker Container
- Build: `docker build -t home-inspection-dashboard .`
- Run: `docker run -p 8501:8501 home-inspection-dashboard`

### 4. Cloud Platforms
- AWS ECS/Fargate
- Azure Container Instances
- Google Cloud Run

See `STREAMLIT_DEPLOYMENT.md` for detailed deployment instructions.

## 📚 Additional Resources

- **Full Deployment Guide**: See `STREAMLIT_DEPLOYMENT.md`
- **Project Documentation**: See `README.md`
- **Database Schema**: See `schema/init_schema.sql`
- **Design Document**: See `.kiro/specs/ai-home-inspection/design.md`

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review `STREAMLIT_DEPLOYMENT.md` for detailed setup
3. Check Streamlit docs: https://docs.streamlit.io
4. Check Snowflake docs: https://docs.snowflake.com

## 🎯 Next Steps

1. ✅ Configure Snowflake connection
2. ✅ Generate sample data for testing
3. ✅ Explore dashboard features
4. ✅ Customize for your needs
5. ✅ Deploy to production

Happy inspecting! 🏠✨
