#!/bin/bash

# Production Startup Script for AI-Assisted Home Inspection Workspace
# Simple script to start the dashboard in production mode

echo "🏠 Starting AI Home Inspection Dashboard (Production)"
echo "=================================================="

# Set production environment
export ENVIRONMENT=production
export CONFIG_FILE=config/production.json

# Load production environment variables if file exists
if [ -f ".env.production" ]; then
    echo "📋 Loading production environment variables..."
    set -a  # automatically export all variables
    source .env.production
    set +a
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

# Check if Streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the dashboard
echo "🚀 Starting dashboard on port 8501..."
echo "📍 Dashboard will be available at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop"
echo ""

streamlit run src/dashboard_app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=true