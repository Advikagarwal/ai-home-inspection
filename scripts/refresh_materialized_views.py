#!/usr/bin/env python3
"""
Materialized View Refresh Script for AI-Assisted Home Inspection Workspace
Refreshes materialized views to optimize query performance
"""

import sys
import os
import logging
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import init_config, get_config
from query_optimizer import get_query_optimizer
from performance_monitor import get_performance_monitor


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/materialized_view_refresh.log')
        ]
    )
    return logging.getLogger(__name__)


def main():
    """Main refresh function"""
    logger = setup_logging()
    logger.info("Starting materialized view refresh")
    
    try:
        # Initialize configuration
        config_file = os.getenv('CONFIG_FILE', 'config/production.json')
        config = init_config(config_file)
        logger.info(f"Loaded configuration from {config_file}")
        
        # Get optimizer and performance monitor
        optimizer = get_query_optimizer()
        performance_monitor = get_performance_monitor()
        
        # Track the refresh operation
        query_id = f"materialized_view_refresh_{int(datetime.now().timestamp())}"
        performance_monitor.start_query(query_id, "materialized_view_refresh")
        
        try:
            # Refresh materialized views
            logger.info("Refreshing materialized views...")
            results = optimizer.optimize_materialized_views()
            
            # Log results
            successful = results['successful']
            failed = results['failed']
            
            logger.info(f"Successfully refreshed {len(successful)} materialized views: {', '.join(successful)}")
            
            if failed:
                logger.error(f"Failed to refresh {len(failed)} materialized views:")
                for failure in failed:
                    logger.error(f"  - {failure['view']}: {failure['error']}")
            
            # Complete performance tracking
            performance_monitor.complete_query(
                query_id, 
                success=len(failed) == 0,
                error_message=f"Failed views: {failed}" if failed else None
            )
            
            # Export performance metrics
            metrics_file = f"logs/performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            performance_monitor.export_metrics(metrics_file)
            logger.info(f"Performance metrics exported to {metrics_file}")
            
            # Return appropriate exit code
            return 0 if len(failed) == 0 else 1
            
        except Exception as e:
            logger.error(f"Error during materialized view refresh: {e}")
            performance_monitor.complete_query(query_id, success=False, error_message=str(e))
            return 1
    
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        return 1


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Run main function
    exit_code = main()
    sys.exit(exit_code)