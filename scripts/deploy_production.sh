#!/bin/bash

# Production Deployment Script for AI-Assisted Home Inspection Workspace
# This script handles production deployment with proper configuration and security

set -e  # Exit on any error

echo "🚀 AI Home Inspection - Production Deployment"
echo "=============================================="
echo ""

# Configuration
DEPLOYMENT_ENV="production"
CONFIG_FILE="config/production.json"
SECRETS_FILE=".streamlit/secrets.toml"
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}
#
 Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check required files
    if [ ! -f "$CONFIG_FILE" ]; then
        error "Production config file not found: $CONFIG_FILE"
        exit 1
    fi
    
    if [ ! -f "requirements.txt" ]; then
        error "Requirements file not found: requirements.txt"
        exit 1
    fi
    
    # Check environment variables
    if [ -z "$SNOWFLAKE_PASSWORD" ]; then
        error "SNOWFLAKE_PASSWORD environment variable not set"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Setup virtual environment
setup_environment() {
    log "Setting up Python environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log "Created virtual environment"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip and install dependencies
    pip install --upgrade pip
    pip install -r requirements.txt
    
    success "Python environment ready"
}#
 Configure Streamlit secrets
configure_secrets() {
    log "Configuring Streamlit secrets..."
    
    # Create .streamlit directory if it doesn't exist
    mkdir -p .streamlit
    
    # Copy production secrets template if secrets.toml doesn't exist
    if [ ! -f "$SECRETS_FILE" ]; then
        if [ -f ".streamlit/secrets.toml.production" ]; then
            cp .streamlit/secrets.toml.production "$SECRETS_FILE"
            log "Copied production secrets template"
        else
            error "Production secrets template not found"
            exit 1
        fi
    fi
    
    # Validate secrets file
    if ! grep -q "qhvspfi-gx24863" "$SECRETS_FILE"; then
        error "Secrets file does not contain production Snowflake account"
        exit 1
    fi
    
    success "Streamlit secrets configured"
}

# Test Snowflake connection
test_connection() {
    log "Testing Snowflake connection..."
    
    # Create a simple test script
    cat > test_connection.py << 'EOF'
import sys
import os
sys.path.append('src')

try:
    from config import init_config, get_config
    import snowflake.connector
    
    # Initialize configuration
    config = init_config('config/production.json')
    db_config = config.database
    
    # Test connection
    conn = snowflake.connector.connect(
        account=db_config.account,
        user=db_config.user,
        password=os.getenv('SNOWFLAKE_PASSWORD', db_config.password),
        warehouse=db_config.warehouse,
        database=db_config.database,
        schema=db_config.schema,
        role=db_config.role
    )
    
    # Test query
    cursor = conn.cursor()
    cursor.execute("SELECT CURRENT_VERSION()")
    result = cursor.fetchone()
    
    print(f"✅ Connection successful - Snowflake version: {result[0]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Connection failed: {str(e)}")
    sys.exit(1)
EOF
    
    # Run test
    python test_connection.py
    rm test_connection.py
    
    success "Snowflake connection test passed"
}# M
ain deployment function
main() {
    log "Starting production deployment..."
    
    # Run deployment steps
    check_prerequisites
    setup_environment
    configure_secrets
    test_connection
    
    echo ""
    success "🎉 Production deployment completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Configure reverse proxy (nginx/apache) for HTTPS"
    echo "2. Set up monitoring and alerting"
    echo "3. Configure automated backups"
    echo ""
    echo "To start the dashboard:"
    echo "  source venv/bin/activate"
    echo "  export ENVIRONMENT=production"
    echo "  streamlit run src/dashboard_app.py"
    echo ""
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "test")
        check_prerequisites
        setup_environment
        test_connection
        ;;
    *)
        echo "Usage: $0 [deploy|test]"
        echo "  deploy - Full production deployment (default)"
        echo "  test   - Test connection and prerequisites only"
        exit 1
        ;;
esac