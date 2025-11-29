#!/bin/bash

# Quick start script for AI Home Inspection Dashboard

echo "🏠 AI-Assisted Home Inspection Dashboard"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if Streamlit secrets are configured
if [ ! -f ".streamlit/secrets.toml" ]; then
    echo ""
    echo "⚠️  Snowflake connection not configured"
    echo ""
    echo "To connect to Snowflake, create .streamlit/secrets.toml with your credentials."
    echo "See .streamlit/secrets.toml.example for a template."
    echo ""
    echo "The dashboard will still run, but you'll need to configure the connection to view data."
    echo ""
    read -p "Press Enter to continue..."
fi

# Run Streamlit
echo ""
echo "🚀 Starting dashboard..."
echo "📍 Dashboard will open at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo ""

streamlit run src/dashboard_app.py
