@echo off
REM Quick start script for AI Home Inspection Dashboard (Windows)

echo 🏠 AI-Assisted Home Inspection Dashboard
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo ✅ Python found
python --version

REM Check if virtual environment exists
if not exist "venv\" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo 📥 Installing dependencies...
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt

REM Check if Streamlit secrets are configured
if not exist ".streamlit\secrets.toml" (
    echo.
    echo ⚠️  Snowflake connection not configured
    echo.
    echo To connect to Snowflake, create .streamlit\secrets.toml with your credentials.
    echo See .streamlit\secrets.toml.example for a template.
    echo.
    echo The dashboard will still run, but you'll need to configure the connection to view data.
    echo.
    pause
)

REM Run Streamlit
echo.
echo 🚀 Starting dashboard...
echo 📍 Dashboard will open at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the dashboard
echo.

streamlit run src\dashboard_app.py
