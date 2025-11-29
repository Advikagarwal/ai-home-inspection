"""
Performance Monitoring System for AI-Assisted Home Inspection Workspace
Tracks query performance, system metrics, and provides optimization recommendations
"""

import time
import logging
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict, deque

from config import get_config


@dataclass
class QueryMetrics:
    """Metrics for a single query execution"""
    query_id: str
    query_type: str  # 'classification', 'aggregation', 'export', etc.
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    rows_processed: int = 0
    bytes_scanned: int = 0
    warehouse_size: str = ""
    success: bool = True
    error_message: Optional[str] = None
    
    def complete(self, success: bool = True, error_message: Optional[str] = None, 
                 rows_processed: int = 0, bytes_scanned: int = 0):
        """Mark query as completed and calculate duration"""
        self.end_time = datetime.now()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        self.success = success
        self.error_message = error_message
        self.rows_processed = rows_processed
        self.bytes_scanned = bytes_scanned


@dataclass
class SystemMetrics:
    """System-level performance metrics"""
    timestamp: datetime
    active_connections: int = 0
    cache_hit_rate: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    concurrent_queries: int = 0
    error_rate: float = 0.0


class PerformanceMonitor:
    """
    Monitors and tracks performance metrics for the application
    Provides insights and optimization recommendations
    """
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        
        # Metrics storage
        self.query_metrics: deque = deque(maxlen=1000)  # Keep last 1000 queries
        self.system_metrics: deque = deque(maxlen=288)  # Keep 24 hours (5min intervals)
        self.active_queries: Dict[str, QueryMetrics] = {}
        
        # Performance counters
        self.query_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.cache_stats = {'hits': 0, 'misses': 0}
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Start background monitoring
        self._start_background_monitoring()
    
    def start_query(self, query_id: str, query_type: str, warehouse_size: str = "") -> str:
        """
        Start tracking a query
        
        Args:
            query_id: Unique identifier for the query
            query_type: Type of query (classification, aggregation, etc.)
            warehouse_size: Snowflake warehouse size
            
        Returns:
            Query tracking ID
        """
        with self._lock:
            metrics = QueryMetrics(
                query_id=query_id,
                query_type=query_type,
                start_time=datetime.now(),
                warehouse_size=warehouse_size
            )
            self.active_queries[query_id] = metrics
            self.query_counts[query_type] += 1
            
        self.logger.debug(f"Started tracking query {query_id} of type {query_type}")
        return query_id
    
    def complete_query(self, query_id: str, success: bool = True, 
                      error_message: Optional[str] = None,
                      rows_processed: int = 0, bytes_scanned: int = 0):
        """
        Complete query tracking and store metrics
        
        Args:
            query_id: Query identifier
            success: Whether query succeeded
            error_message: Error message if failed
            rows_processed: Number of rows processed
            bytes_scanned: Bytes scanned by query
        """
        with self._lock:
            if query_id not in self.active_queries:
                self.logger.warning(f"Query {query_id} not found in active queries")
                return
            
            metrics = self.active_queries.pop(query_id)
            metrics.complete(success, error_message, rows_processed, bytes_scanned)
            
            # Store completed metrics
            self.query_metrics.append(metrics)
            
            # Update error counts
            if not success:
                self.error_counts[metrics.query_type] += 1
        
        duration = metrics.duration_seconds or 0
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Query {query_id} completed in {duration:.2f}s - {status}")
    
    def record_cache_hit(self):
        """Record a cache hit"""
        with self._lock:
            self.cache_stats['hits'] += 1
    
    def record_cache_miss(self):
        """Record a cache miss"""
        with self._lock:
            self.cache_stats['misses'] += 1
    
    def get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        with self._lock:
            total = self.cache_stats['hits'] + self.cache_stats['misses']
            if total == 0:
                return 0.0
            return self.cache_stats['hits'] / total
    
    def get_query_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance summary for recent queries
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Performance summary dictionary
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            recent_queries = [
                q for q in self.query_metrics 
                if q.start_time >= cutoff_time and q.duration_seconds is not None
            ]
        
        if not recent_queries:
            return {
                'total_queries': 0,
                'avg_duration': 0.0,
                'success_rate': 1.0,
                'query_types': {},
                'slowest_queries': []
            }
        
        # Calculate statistics
        total_queries = len(recent_queries)
        successful_queries = [q for q in recent_queries if q.success]
        success_rate = len(successful_queries) / total_queries
        
        durations = [q.duration_seconds for q in recent_queries]
        avg_duration = sum(durations) / len(durations)
        
        # Group by query type
        query_types = defaultdict(list)
        for query in recent_queries:
            query_types[query.query_type].append(query.duration_seconds)
        
        type_stats = {}
        for qtype, durations in query_types.items():
            type_stats[qtype] = {
                'count': len(durations),
                'avg_duration': sum(durations) / len(durations),
                'max_duration': max(durations),
                'min_duration': min(durations)
            }
        
        # Find slowest queries
        slowest_queries = sorted(recent_queries, key=lambda q: q.duration_seconds, reverse=True)[:5]
        slowest_summary = [
            {
                'query_id': q.query_id,
                'query_type': q.query_type,
                'duration': q.duration_seconds,
                'rows_processed': q.rows_processed,
                'warehouse_size': q.warehouse_size
            }
            for q in slowest_queries
        ]
        
        return {
            'total_queries': total_queries,
            'avg_duration': avg_duration,
            'success_rate': success_rate,
            'cache_hit_rate': self.get_cache_hit_rate(),
            'query_types': type_stats,
            'slowest_queries': slowest_summary
        }
    
    def get_optimization_recommendations(self) -> List[Dict[str, str]]:
        """
        Generate optimization recommendations based on performance data
        
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        summary = self.get_query_performance_summary()
        
        # Check cache hit rate
        cache_hit_rate = summary.get('cache_hit_rate', 0.0)
        if cache_hit_rate < 0.5:
            recommendations.append({
                'type': 'caching',
                'priority': 'high',
                'title': 'Low Cache Hit Rate',
                'description': f'Cache hit rate is {cache_hit_rate:.1%}. Consider increasing cache TTL or implementing more aggressive caching.',
                'action': 'Increase CACHE_TTL_SECONDS in configuration'
            })
        
        # Check average query duration
        avg_duration = summary.get('avg_duration', 0.0)
        if avg_duration > 30:  # 30 seconds threshold
            recommendations.append({
                'type': 'performance',
                'priority': 'high',
                'title': 'Slow Query Performance',
                'description': f'Average query duration is {avg_duration:.1f}s. Consider optimizing queries or scaling warehouse.',
                'action': 'Review slow queries and consider larger Snowflake warehouse'
            })
        
        # Check success rate
        success_rate = summary.get('success_rate', 1.0)
        if success_rate < 0.95:
            recommendations.append({
                'type': 'reliability',
                'priority': 'high',
                'title': 'Low Success Rate',
                'description': f'Query success rate is {success_rate:.1%}. Investigate error patterns.',
                'action': 'Review error logs and implement better error handling'
            })
        
        # Check for specific query type issues
        query_types = summary.get('query_types', {})
        for qtype, stats in query_types.items():
            if stats['avg_duration'] > 60:  # 1 minute threshold
                recommendations.append({
                    'type': 'query_optimization',
                    'priority': 'medium',
                    'title': f'Slow {qtype} Queries',
                    'description': f'{qtype} queries average {stats["avg_duration"]:.1f}s. Consider optimization.',
                    'action': f'Optimize {qtype} query patterns or use materialized views'
                })
        
        return recommendations
    
    def export_metrics(self, filepath: str):
        """
        Export performance metrics to JSON file
        
        Args:
            filepath: Path to export file
        """
        with self._lock:
            data = {
                'export_timestamp': datetime.now().isoformat(),
                'query_metrics': [
                    {
                        'query_id': q.query_id,
                        'query_type': q.query_type,
                        'start_time': q.start_time.isoformat(),
                        'duration_seconds': q.duration_seconds,
                        'success': q.success,
                        'rows_processed': q.rows_processed,
                        'bytes_scanned': q.bytes_scanned,
                        'warehouse_size': q.warehouse_size
                    }
                    for q in self.query_metrics
                ],
                'summary': self.get_query_performance_summary(),
                'recommendations': self.get_optimization_recommendations()
            }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Performance metrics exported to {filepath}")
    
    def _start_background_monitoring(self):
        """Start background thread for system monitoring"""
        if not self.config.monitoring.performance_monitoring:
            return
        
        def monitor_system():
            while True:
                try:
                    # Collect system metrics
                    metrics = SystemMetrics(
                        timestamp=datetime.now(),
                        active_connections=len(self.active_queries),
                        cache_hit_rate=self.get_cache_hit_rate(),
                        concurrent_queries=len(self.active_queries)
                    )
                    
                    with self._lock:
                        self.system_metrics.append(metrics)
                    
                    # Sleep for monitoring interval
                    time.sleep(300)  # 5 minutes
                    
                except Exception as e:
                    self.logger.error(f"Error in background monitoring: {e}")
                    time.sleep(60)  # Wait 1 minute before retrying
        
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
        self.logger.info("Background performance monitoring started")


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def track_query(query_type: str, warehouse_size: str = ""):
    """
    Decorator to track query performance
    
    Args:
        query_type: Type of query being tracked
        warehouse_size: Snowflake warehouse size
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            query_id = f"{func.__name__}_{int(time.time())}"
            
            monitor.start_query(query_id, query_type, warehouse_size)
            
            try:
                result = func(*args, **kwargs)
                monitor.complete_query(query_id, success=True)
                return result
            except Exception as e:
                monitor.complete_query(query_id, success=False, error_message=str(e))
                raise
        
        return wrapper
    return decorator