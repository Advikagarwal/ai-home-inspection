"""
Query Optimization Module for AI-Assisted Home Inspection Workspace
Optimizes Snowflake queries for better performance and cost efficiency
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import snowflake.connector
from contextlib import contextmanager

from config import get_config
from performance_monitor import get_performance_monitor, track_query
from cache_manager import get_cache_manager, cached


class QueryOptimizer:
    """
    Optimizes Snowflake queries for performance and cost efficiency
    """
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = get_performance_monitor()
        self.cache_manager = get_cache_manager()
        
        # Query templates for common operations
        self.query_templates = {
            'property_list': """
                SELECT p.property_id, p.location, p.inspection_date, 
                       p.risk_score, p.risk_category, p.summary_text
                FROM properties p
                WHERE 1=1
                {filters}
                ORDER BY p.inspection_date DESC
                LIMIT {limit}
            """,
            
            'property_details': """
                SELECT p.*, 
                       COUNT(DISTINCT r.room_id) as room_count,
                       COUNT(DISTINCT f.finding_id) as finding_count
                FROM properties p
                LEFT JOIN rooms r ON p.property_id = r.property_id
                LEFT JOIN findings f ON r.room_id = f.room_id
                WHERE p.property_id = %s
                GROUP BY p.property_id, p.location, p.inspection_date, 
                         p.risk_score, p.risk_category, p.summary_text
            """,
            
            'room_defects': """
                SELECT r.room_id, r.room_type, r.room_location,
                       dt.defect_category, COUNT(*) as defect_count,
                       AVG(dt.confidence_score) as avg_confidence
                FROM rooms r
                JOIN findings f ON r.room_id = f.room_id
                JOIN defect_tags dt ON f.finding_id = dt.finding_id
                WHERE r.property_id = %s
                GROUP BY r.room_id, r.room_type, r.room_location, dt.defect_category
                ORDER BY defect_count DESC
            """,
            
            'defect_summary': """
                SELECT dt.defect_category, 
                       COUNT(*) as total_count,
                       COUNT(DISTINCT f.room_id) as affected_rooms,
                       AVG(dt.confidence_score) as avg_confidence,
                       SUM(dt.severity_weight) as total_severity
                FROM defect_tags dt
                JOIN findings f ON dt.finding_id = f.finding_id
                JOIN rooms r ON f.room_id = r.room_id
                WHERE r.property_id = %s
                GROUP BY dt.defect_category
                ORDER BY total_severity DESC
            """
        }
    
    @contextmanager
    def get_connection(self):
        """Get optimized Snowflake connection with connection pooling"""
        conn = None
        try:
            db_config = self.config.database
            
            conn = snowflake.connector.connect(
                account=db_config.account,
                user=db_config.user,
                password=db_config.password,
                warehouse=db_config.warehouse,
                database=db_config.database,
                schema=db_config.schema,
                role=db_config.role,
                # Performance optimizations
                client_session_keep_alive=True,
                client_session_keep_alive_heartbeat_frequency=3600,
                network_timeout=self.config.performance.query_timeout_seconds,
                # Connection pooling
                connection_timeout=30,
                login_timeout=30
            )
            
            yield conn
            
        except Exception as e:
            self.logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @track_query("property_list")
    @cached(ttl_seconds=300, key_prefix="property_list")
    def get_property_list(self, filters: Optional[Dict[str, Any]] = None, 
                         limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get optimized property list with caching and filtering
        
        Args:
            filters: Optional filters to apply
            limit: Maximum number of properties to return
            
        Returns:
            List of property dictionaries
        """
        # Build filter clause
        filter_clauses = []
        params = []
        
        if filters:
            if 'risk_category' in filters:
                filter_clauses.append("AND p.risk_category = %s")
                params.append(filters['risk_category'])
            
            if 'min_risk_score' in filters:
                filter_clauses.append("AND p.risk_score >= %s")
                params.append(filters['min_risk_score'])
            
            if 'location_search' in filters:
                filter_clauses.append("AND p.location ILIKE %s")
                params.append(f"%{filters['location_search']}%")
            
            if 'date_from' in filters:
                filter_clauses.append("AND p.inspection_date >= %s")
                params.append(filters['date_from'])
        
        filter_sql = " ".join(filter_clauses)
        query = self.query_templates['property_list'].format(
            filters=filter_sql,
            limit=limit
        )
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            cursor.close()
            return results
    
    @track_query("property_details")
    @cached(ttl_seconds=600, key_prefix="property_details")
    def get_property_details(self, property_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed property information with caching
        
        Args:
            property_id: Property identifier
            
        Returns:
            Property details dictionary or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(self.query_templates['property_details'], (property_id,))
            
            result = cursor.fetchone()
            if not result:
                cursor.close()
                return None
            
            columns = [desc[0] for desc in cursor.description]
            property_data = dict(zip(columns, result))
            
            cursor.close()
            return property_data
    
    @track_query("room_defects")
    @cached(ttl_seconds=600, key_prefix="room_defects")
    def get_room_defects(self, property_id: str) -> List[Dict[str, Any]]:
        """
        Get room defect information with optimization
        
        Args:
            property_id: Property identifier
            
        Returns:
            List of room defect dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(self.query_templates['room_defects'], (property_id,))
            
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            cursor.close()
            return results
    
    @track_query("defect_summary")
    @cached(ttl_seconds=600, key_prefix="defect_summary")
    def get_defect_summary(self, property_id: str) -> List[Dict[str, Any]]:
        """
        Get defect summary with caching
        
        Args:
            property_id: Property identifier
            
        Returns:
            List of defect summary dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(self.query_templates['defect_summary'], (property_id,))
            
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            cursor.close()
            return results
    
    @track_query("batch_classification")
    def batch_classify_findings(self, finding_ids: List[str], 
                               batch_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Batch process AI classifications for better performance
        
        Args:
            finding_ids: List of finding IDs to classify
            batch_size: Batch size (uses config default if None)
            
        Returns:
            Classification results dictionary
        """
        if batch_size is None:
            batch_size = self.config.performance.batch_size
        
        results = {'successful': [], 'failed': []}
        
        # Process in batches
        for i in range(0, len(finding_ids), batch_size):
            batch = finding_ids[i:i + batch_size]
            
            try:
                batch_results = self._process_classification_batch(batch)
                results['successful'].extend(batch_results)
            except Exception as e:
                self.logger.error(f"Batch classification failed for batch {i//batch_size + 1}: {e}")
                results['failed'].extend(batch)
        
        return results
    
    def _process_classification_batch(self, finding_ids: List[str]) -> List[Dict[str, Any]]:
        """Process a single batch of classifications"""
        # Placeholder for batch classification logic
        # In real implementation, this would use Snowflake's batch AI functions
        
        batch_query = """
            SELECT f.finding_id, f.note_text, f.image_filename,
                   CASE 
                       WHEN f.note_text IS NOT NULL THEN 
                           SNOWFLAKE.CORTEX.CLASSIFY_TEXT(
                               f.note_text, 
                               ['damp wall', 'exposed wiring', 'crack', 'mold', 'water leak', 'none']
                           )
                       ELSE NULL
                   END as text_classification,
                   CASE 
                       WHEN f.image_filename IS NOT NULL THEN 
                           AI_CLASSIFY(
                               TO_FILE('@inspections', f.image_filename),
                               ['crack', 'water leak', 'mold', 'electrical wiring', 'none']
                           )
                       ELSE NULL
                   END as image_classification
            FROM findings f
            WHERE f.finding_id IN ({})
        """.format(','.join(['%s'] * len(finding_ids)))
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(batch_query, finding_ids)
            
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            cursor.close()
            return results
    
    def optimize_materialized_views(self) -> Dict[str, Any]:
        """
        Refresh materialized views for better query performance
        
        Returns:
            Refresh status dictionary
        """
        views_to_refresh = [
            'room_defect_summary',
            'property_defect_summary'
        ]
        
        results = {'successful': [], 'failed': []}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for view_name in views_to_refresh:
                try:
                    refresh_query = f"ALTER MATERIALIZED VIEW {view_name} REFRESH"
                    cursor.execute(refresh_query)
                    results['successful'].append(view_name)
                    self.logger.info(f"Refreshed materialized view: {view_name}")
                except Exception as e:
                    self.logger.error(f"Failed to refresh materialized view {view_name}: {e}")
                    results['failed'].append({'view': view_name, 'error': str(e)})
            
            cursor.close()
        
        return results
    
    def get_query_performance_insights(self) -> Dict[str, Any]:
        """
        Get insights about query performance and optimization opportunities
        
        Returns:
            Performance insights dictionary
        """
        summary = self.performance_monitor.get_query_performance_summary()
        recommendations = self.performance_monitor.get_optimization_recommendations()
        cache_stats = self.cache_manager.get_stats()
        
        return {
            'query_performance': summary,
            'cache_performance': cache_stats,
            'optimization_recommendations': recommendations,
            'materialized_views_status': self._check_materialized_views_status()
        }
    
    def _check_materialized_views_status(self) -> Dict[str, Any]:
        """Check the status of materialized views"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check materialized view freshness
                query = """
                    SELECT table_name, last_altered
                    FROM information_schema.tables
                    WHERE table_type = 'MATERIALIZED VIEW'
                    AND table_schema = %s
                """
                
                cursor.execute(query, (self.config.database.schema,))
                results = cursor.fetchall()
                
                view_status = {}
                for view_name, last_altered in results:
                    age_hours = (datetime.now() - last_altered).total_seconds() / 3600
                    view_status[view_name] = {
                        'last_refreshed': last_altered.isoformat(),
                        'age_hours': age_hours,
                        'needs_refresh': age_hours > 1  # Refresh if older than 1 hour
                    }
                
                cursor.close()
                return view_status
                
        except Exception as e:
            self.logger.error(f"Error checking materialized views: {e}")
            return {}


# Global query optimizer instance
_query_optimizer: Optional[QueryOptimizer] = None


def get_query_optimizer() -> QueryOptimizer:
    """Get the global query optimizer instance"""
    global _query_optimizer
    if _query_optimizer is None:
        _query_optimizer = QueryOptimizer()
    return _query_optimizer