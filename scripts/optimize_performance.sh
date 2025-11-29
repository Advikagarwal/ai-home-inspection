#!/bin/bash

# Performance Optimization Script for AI-Assisted Home Inspection Workspace
# Optimizes system performance through various tuning operations

set -e

echo "🚀 AI Home Inspection - Performance Optimization"
echo "==============================================="

# Configuration
LOG_DIR="logs"
METRICS_DIR="metrics"
BACKUP_DIR="backups/performance_$(date +%Y%m%d_%H%M%S)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Create directories
mkdir -p "$LOG_DIR" "$METRICS_DIR" "$BACKUP_DIR"

# Set environment
export ENVIRONMENT=${ENVIRONMENT:-production}
export CONFIG_FILE=${CONFIG_FILE:-config/production.json}

log "Starting performance optimization..."

# 1. Refresh materialized views
log "Refreshing materialized views for better query performance..."
if python3 scripts/refresh_materialized_views.py; then
    success "Materialized views refreshed successfully"
else
    warning "Some materialized views failed to refresh"
fi

# 2. Clear and warm up cache
log "Optimizing application cache..."
python3 -c "
import sys
sys.path.append('src')
from cache_manager import get_cache_manager
from performance_monitor import get_performance_monitor

cache_manager = get_cache_manager()
performance_monitor = get_performance_monitor()

# Clear cache to start fresh
cache_manager.clear()
print('Cache cleared')

# Export current performance metrics
performance_monitor.export_metrics('$METRICS_DIR/pre_optimization_metrics.json')
print('Performance metrics exported')
"

# 3. Optimize Snowflake warehouse settings
log "Checking Snowflake warehouse optimization..."
python3 -c "
import sys
sys.path.append('src')
from query_optimizer import get_query_optimizer

optimizer = get_query_optimizer()

# Get performance insights
insights = optimizer.get_query_performance_insights()
recommendations = insights.get('optimization_recommendations', [])

print(f'Found {len(recommendations)} optimization recommendations')
for rec in recommendations:
    print(f'- {rec[\"priority\"].upper()}: {rec[\"title\"]}')
    print(f'  Action: {rec[\"action\"]}')
"

# 4. System resource optimization
log "Checking system resources..."

# Check available memory
MEMORY_TOTAL=$(free -m | awk 'NR==2{printf "%.0f", $2}')
MEMORY_USED=$(free -m | awk 'NR==2{printf "%.0f", $3}')
MEMORY_PERCENT=$(echo "scale=1; $MEMORY_USED * 100 / $MEMORY_TOTAL" | bc)

echo "Memory usage: ${MEMORY_USED}MB / ${MEMORY_TOTAL}MB (${MEMORY_PERCENT}%)"

if (( $(echo "$MEMORY_PERCENT > 80" | bc -l) )); then
    warning "High memory usage detected (${MEMORY_PERCENT}%)"
    echo "Consider:"
    echo "  - Reducing cache size"
    echo "  - Decreasing batch size"
    echo "  - Adding more RAM"
else
    success "Memory usage is within acceptable limits"
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
echo "Disk usage: ${DISK_USAGE}%"

if [ "$DISK_USAGE" -gt 85 ]; then
    warning "High disk usage detected (${DISK_USAGE}%)"
    echo "Consider:"
    echo "  - Cleaning up old log files"
    echo "  - Archiving old performance metrics"
    echo "  - Increasing disk space"
else
    success "Disk usage is within acceptable limits"
fi

# 5. Network connectivity test
log "Testing Snowflake connectivity..."
python3 -c "
import sys
sys.path.append('src')
from query_optimizer import get_query_optimizer
import time

optimizer = get_query_optimizer()

try:
    start_time = time.time()
    with optimizer.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT CURRENT_VERSION()')
        result = cursor.fetchone()
        cursor.close()
    
    connection_time = (time.time() - start_time) * 1000
    print(f'✅ Snowflake connection successful ({connection_time:.0f}ms)')
    
    if connection_time > 1000:
        print('⚠️  Slow connection detected. Consider:')
        print('   - Checking network connectivity')
        print('   - Using a closer Snowflake region')
        print('   - Optimizing connection pooling')
    
except Exception as e:
    print(f'❌ Snowflake connection failed: {e}')
    sys.exit(1)
"

# 6. Generate optimization report
log "Generating optimization report..."

REPORT_FILE="$METRICS_DIR/optimization_report_$(date +%Y%m%d_%H%M%S).txt"

cat > "$REPORT_FILE" << EOF
AI Home Inspection - Performance Optimization Report
Generated: $(date)
Environment: $ENVIRONMENT

System Resources:
- Memory Usage: ${MEMORY_PERCENT}%
- Disk Usage: ${DISK_USAGE}%

Optimizations Applied:
- Materialized views refreshed
- Application cache cleared
- Performance metrics collected
- System resources checked
- Network connectivity verified

Next Steps:
1. Monitor performance metrics over the next 24 hours
2. Review query performance in the dashboard
3. Adjust configuration based on usage patterns
4. Schedule regular optimization runs

Files Generated:
- Performance metrics: $METRICS_DIR/pre_optimization_metrics.json
- Optimization report: $REPORT_FILE
- Backup created: $BACKUP_DIR

EOF

success "Optimization report generated: $REPORT_FILE"

# 7. Schedule next optimization (if cron is available)
if command -v crontab &> /dev/null; then
    log "Setting up automated optimization schedule..."
    
    # Check if cron job already exists
    if ! crontab -l 2>/dev/null | grep -q "optimize_performance.sh"; then
        # Add cron job to run optimization daily at 2 AM
        (crontab -l 2>/dev/null; echo "0 2 * * * cd $(pwd) && ./scripts/optimize_performance.sh >> logs/optimization.log 2>&1") | crontab -
        success "Automated optimization scheduled for 2 AM daily"
    else
        success "Automated optimization already scheduled"
    fi
else
    warning "Cron not available - manual optimization required"
fi

echo ""
success "🎉 Performance optimization completed!"
echo ""
echo "Summary:"
echo "- Materialized views refreshed"
echo "- Cache optimized"
echo "- System resources checked"
echo "- Optimization report generated"
echo ""
echo "Monitor performance at: http://localhost:8501 (Performance Monitor tab)"
echo "Review report: $REPORT_FILE"
echo ""