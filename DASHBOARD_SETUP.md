# AI-Assisted Home Inspection Dashboard Setup

## Overview

The Streamlit dashboard provides an interactive interface for viewing and analyzing home inspection data with AI-powered defect detection and risk scoring.

## Prerequisites

- Python 3.8 or higher
- Snowflake account with Cortex AI enabled
- Required Python packages (see requirements.txt)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### Snowflake Connection

Create a `.streamlit/secrets.toml` file in your project root with your Snowflake credentials:

```toml
[connections.snowflake]
account = "your_account"
user = "your_username"
password = "your_password"
warehouse = "your_warehouse"
database = "your_database"
schema = "your_schema"
role = "your_role"
```

**Important:** Never commit the `secrets.toml` file to version control. Add it to `.gitignore`.

### Alternative: Environment Variables

You can also configure the connection using environment variables:

```bash
export SNOWFLAKE_ACCOUNT="your_account"
export SNOWFLAKE_USER="your_username"
export SNOWFLAKE_PASSWORD="your_password"
export SNOWFLAKE_WAREHOUSE="your_warehouse"
export SNOWFLAKE_DATABASE="your_database"
export SNOWFLAKE_SCHEMA="your_schema"
```

## Running the Dashboard

Start the Streamlit application:

```bash
streamlit run src/dashboard_app.py
```

The dashboard will open in your default web browser at `http://localhost:8501`.

## Features

### Property List View

- Browse all inspected properties
- View risk indicators with color coding:
  - 🟢 Green: Low risk (score < 5)
  - 🟠 Orange: Medium risk (5 ≤ score < 10)
  - 🔴 Red: High risk (score ≥ 10)
- See AI-generated summaries for each property

### Filtering and Search

Use the sidebar to filter properties:

- **Risk Level**: Filter by Low, Medium, or High risk
- **Defect Type**: Filter by specific defect categories:
  - Damp wall
  - Exposed wiring
  - Crack
  - Mold
  - Water leak
  - Electrical wiring
- **Search**: Search by location, property ID, or summary text
- **Clear Filters**: Reset all filters to view all properties

### Property Details

Click "View Details" on any property to see:

- Complete property information
- Risk score and category
- AI-generated summary
- All rooms with their findings
- Detected defects with severity weights
- Confidence scores for AI classifications

### Room Details

Each room displays:

- Room type and location
- Risk score
- Text findings (inspection notes)
- Image findings with detected defects
- Defect tags with severity indicators

## Error Handling

The dashboard includes robust error handling:

- Sensitive information (passwords, connection strings, API keys) is automatically sanitized from error messages
- User-friendly error notifications
- Graceful degradation when data is unavailable

## Security Notes

1. **Never expose sensitive credentials** in the application code
2. Use Snowflake's role-based access control (RBAC) to limit data access
3. Error messages are sanitized to prevent information leakage
4. Consider using Snowflake's OAuth or SSO for production deployments

## Troubleshooting

### Connection Issues

If you see "Snowflake connection not configured":
1. Verify your `.streamlit/secrets.toml` file exists and has correct credentials
2. Check that your Snowflake account is accessible
3. Ensure your warehouse is running

### No Data Displayed

If the dashboard shows no properties:
1. Verify data has been ingested into the database
2. Check that the schema matches the expected structure
3. Run the data ingestion scripts to populate test data

### Performance Issues

For large datasets:
1. Ensure materialized views are refreshed
2. Consider adding database indexes on frequently queried columns
3. Use appropriate Snowflake warehouse sizes

## Development

### Running Tests

Run all tests:
```bash
pytest tests/
```

Run specific test files:
```bash
pytest tests/test_dashboard_app.py -v
pytest tests/test_error_sanitization.py -v
```

### Code Structure

- `src/dashboard_app.py`: Main Streamlit application
- `src/dashboard_data.py`: Data access layer
- `tests/test_dashboard_app.py`: Unit tests
- `tests/test_error_sanitization.py`: Property-based tests for error handling

## Next Steps

1. Configure Snowflake connection
2. Ingest sample inspection data
3. Run AI classification on findings
4. Compute risk scores
5. Generate summaries
6. Launch the dashboard to view results

For more information, see the main project README.md.
