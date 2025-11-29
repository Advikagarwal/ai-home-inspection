"""
Application Performance Monitoring (APM) for AI-Assisted Home Inspection Workspace
Monitors application health, performance metrics, and provides alerting capabilities
"""

import time
import logging
import threading
import psutil
import requests
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import get_config
from performance_monitor import get_performance_monitor
from cache_manager import get_cache_manager


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    component: str
    status: str  # 'healthy', 'warning', 'critical'
    message: str
    response_time_ms: float
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


@dataclass
class SystemMetrics:
    """System resource metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_free_gb: float
    network_sent_mb: float
    network_recv_mb: float


class APMMonitor:
    """
    Application Performance Monitoring system
    Tracks health, performance, and sends alerts
    """
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = get_performance_monitor()
        self.cache_manager = get_cache_manager()
        
        # Health check registry
        self.health_checks: Dict[str, Callable] = {}
        self.health_results: List[HealthCheckResult] = []
        
        # System metrics storage
        self.system_metrics: List[SystemMetrics] = []
        self.max_metrics_history = 1440  # 24 hours at 1-minute intervals
        
        # Alert thresholds
        self.alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0,
            'error_rate': 0.05,  # 5%
            'response_time_ms': 5000.0  # 5 seconds
        }
        
        # Alert state tracking
        self.alert_states: Dict[str, bool] = {}
        self.last_alert_times: Dict[str, datetime] = {}
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Register default health checks
        self._register_default_health_checks()
        
        # Start monitoring threads
        self._start_monitoring_threads()
    
    def register_health_check(self, name: str, check_func: Callable) -> None:
        """
        Register a health check function
        
        Args:
            name: Name of the health check
            check_func: Function that returns HealthCheckResult
        """
        self.health_checks[name] = check_func
        self.logger.info(f"Registered health check: {name}")
    
    def run_health_checks(self) -> Dict[str, HealthCheckResult]:
        """
        Run all registered health checks
        
        Returns:
            Dictionary of health check results
        """
        results = {}
        
        for name, check_func in self.health_checks.items():
            try:
                start_time = time.time()
                result = check_func()
                
                if not isinstance(result, HealthCheckResult):
                    # Create result if function doesn't return HealthCheckResult
                    result = HealthCheckResult(
                        component=name,
                        status='healthy' if result else 'critical',
                        message=str(result),
                        response_time_ms=(time.time() - start_time) * 1000,
                        timestamp=datetime.now()
                    )
                
                results[name] = result
                
            except Exception as e:
                self.logger.error(f"Health check {name} failed: {e}")
                results[name] = HealthCheckResult(
                    component=name,
                    status='critical',
                    message=f"Health check failed: {str(e)}",
                    response_time_ms=0.0,
                    timestamp=datetime.now()
                )
        
        # Store results
        with self._lock:
            self.health_results = list(results.values())
        
        return results
    
    def get_system_metrics(self) -> SystemMetrics:
        """
        Collect current system metrics
        
        Returns:
            SystemMetrics object
        """
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_used_gb = disk.used / (1024 * 1024 * 1024)
            disk_free_gb = disk.free / (1024 * 1024 * 1024)
            
            # Network metrics
            network = psutil.net_io_counters()
            network_sent_mb = network.bytes_sent / (1024 * 1024)
            network_recv_mb = network.bytes_recv / (1024 * 1024)
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_percent=disk_percent,
                disk_used_gb=disk_used_gb,
                disk_free_gb=disk_free_gb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_percent=0.0,
                disk_used_gb=0.0,
                disk_free_gb=0.0,
                network_sent_mb=0.0,
                network_recv_mb=0.0
            )
    
    def check_alert_conditions(self) -> List[Dict[str, Any]]:
        """
        Check for alert conditions and return active alerts
        
        Returns:
            List of active alerts
        """
        alerts = []
        current_metrics = self.get_system_metrics()
        
        # Check system resource alerts
        if current_metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
            alerts.append({
                'type': 'system',
                'severity': 'warning',
                'component': 'cpu',
                'message': f'High CPU usage: {current_metrics.cpu_percent:.1f}%',
                'value': current_metrics.cpu_percent,
                'threshold': self.alert_thresholds['cpu_percent']
            })
        
        if current_metrics.memory_percent > self.alert_thresholds['memory_percent']:
            alerts.append({
                'type': 'system',
                'severity': 'warning',
                'component': 'memory',
                'message': f'High memory usage: {current_metrics.memory_percent:.1f}%',
                'value': current_metrics.memory_percent,
                'threshold': self.alert_thresholds['memory_percent']
            })
        
        if current_metrics.disk_percent > self.alert_thresholds['disk_percent']:
            alerts.append({
                'type': 'system',
                'severity': 'critical',
                'component': 'disk',
                'message': f'High disk usage: {current_metrics.disk_percent:.1f}%',
                'value': current_metrics.disk_percent,
                'threshold': self.alert_thresholds['disk_percent']
            })
        
        # Check application performance alerts
        perf_summary = self.performance_monitor.get_query_performance_summary()
        
        if perf_summary['success_rate'] < (1 - self.alert_thresholds['error_rate']):
            alerts.append({
                'type': 'application',
                'severity': 'critical',
                'component': 'error_rate',
                'message': f'High error rate: {(1-perf_summary["success_rate"])*100:.1f}%',
                'value': 1 - perf_summary['success_rate'],
                'threshold': self.alert_thresholds['error_rate']
            })
        
        if perf_summary['avg_duration'] * 1000 > self.alert_thresholds['response_time_ms']:
            alerts.append({
                'type': 'application',
                'severity': 'warning',
                'component': 'response_time',
                'message': f'Slow response time: {perf_summary["avg_duration"]*1000:.0f}ms',
                'value': perf_summary['avg_duration'] * 1000,
                'threshold': self.alert_thresholds['response_time_ms']
            })
        
        return alerts
    
    def send_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Send alert notification
        
        Args:
            alert: Alert dictionary
            
        Returns:
            True if alert was sent successfully
        """
        alert_key = f"{alert['component']}_{alert['type']}"
        
        # Check if we should send this alert (rate limiting)
        if self._should_send_alert(alert_key):
            try:
                # Send email alert
                if self.config.monitoring.alert_email:
                    self._send_email_alert(alert)
                
                # Send webhook alert
                if self.config.monitoring.alert_webhook:
                    self._send_webhook_alert(alert)
                
                # Update alert state
                self.alert_states[alert_key] = True
                self.last_alert_times[alert_key] = datetime.now()
                
                self.logger.warning(f"Alert sent: {alert['message']}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to send alert: {e}")
                return False
        
        return False
    
    def get_dashboard_status(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard status
        
        Returns:
            Status dictionary for dashboard display
        """
        health_results = self.run_health_checks()
        system_metrics = self.get_system_metrics()
        perf_summary = self.performance_monitor.get_query_performance_summary()
        cache_stats = self.cache_manager.get_stats()
        active_alerts = self.check_alert_conditions()
        
        # Determine overall status
        health_statuses = [result.status for result in health_results.values()]
        if 'critical' in health_statuses:
            overall_status = 'critical'
        elif 'warning' in health_statuses:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
        
        return {
            'overall_status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'health_checks': {name: asdict(result) for name, result in health_results.items()},
            'system_metrics': asdict(system_metrics),
            'performance': perf_summary,
            'cache': cache_stats,
            'active_alerts': active_alerts,
            'uptime_seconds': time.time() - self._start_time
        }
    
    def _register_default_health_checks(self):
        """Register default health checks"""
        
        def database_health_check() -> HealthCheckResult:
            """Check database connectivity"""
            try:
                from query_optimizer import get_query_optimizer
                optimizer = get_query_optimizer()
                
                start_time = time.time()
                with optimizer.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                    cursor.close()
                
                response_time = (time.time() - start_time) * 1000
                
                return HealthCheckResult(
                    component='database',
                    status='healthy',
                    message='Database connection successful',
                    response_time_ms=response_time,
                    timestamp=datetime.now()
                )
                
            except Exception as e:
                return HealthCheckResult(
                    component='database',
                    status='critical',
                    message=f'Database connection failed: {str(e)}',
                    response_time_ms=0.0,
                    timestamp=datetime.now()
                )
        
        def cache_health_check() -> HealthCheckResult:
            """Check cache system health"""
            try:
                cache_stats = self.cache_manager.get_stats()
                
                if cache_stats['hit_rate'] < 0.3:  # Less than 30% hit rate
                    status = 'warning'
                    message = f'Low cache hit rate: {cache_stats["hit_rate"]:.1%}'
                else:
                    status = 'healthy'
                    message = f'Cache operating normally (hit rate: {cache_stats["hit_rate"]:.1%})'
                
                return HealthCheckResult(
                    component='cache',
                    status=status,
                    message=message,
                    response_time_ms=1.0,  # Cache checks are fast
                    timestamp=datetime.now(),
                    details=cache_stats
                )
                
            except Exception as e:
                return HealthCheckResult(
                    component='cache',
                    status='critical',
                    message=f'Cache system error: {str(e)}',
                    response_time_ms=0.0,
                    timestamp=datetime.now()
                )
        
        # Register health checks
        self.register_health_check('database', database_health_check)
        self.register_health_check('cache', cache_health_check)
    
    def _should_send_alert(self, alert_key: str) -> bool:
        """Check if alert should be sent (rate limiting)"""
        if alert_key not in self.last_alert_times:
            return True
        
        # Don't send same alert more than once per hour
        time_since_last = datetime.now() - self.last_alert_times[alert_key]
        return time_since_last > timedelta(hours=1)
    
    def _send_email_alert(self, alert: Dict[str, Any]) -> None:
        """Send email alert notification"""
        # This is a placeholder - implement actual email sending
        self.logger.info(f"Email alert would be sent to {self.config.monitoring.alert_email}: {alert['message']}")
    
    def _send_webhook_alert(self, alert: Dict[str, Any]) -> None:
        """Send webhook alert notification"""
        try:
            payload = {
                'text': f"🚨 Alert: {alert['message']}",
                'attachments': [{
                    'color': 'danger' if alert['severity'] == 'critical' else 'warning',
                    'fields': [
                        {'title': 'Component', 'value': alert['component'], 'short': True},
                        {'title': 'Severity', 'value': alert['severity'], 'short': True},
                        {'title': 'Value', 'value': str(alert.get('value', 'N/A')), 'short': True},
                        {'title': 'Threshold', 'value': str(alert.get('threshold', 'N/A')), 'short': True}
                    ]
                }]
            }
            
            response = requests.post(
                self.config.monitoring.alert_webhook,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")
    
    def _start_monitoring_threads(self):
        """Start background monitoring threads"""
        self._start_time = time.time()
        
        def metrics_collector():
            """Collect system metrics periodically"""
            while True:
                try:
                    metrics = self.get_system_metrics()
                    
                    with self._lock:
                        self.system_metrics.append(metrics)
                        # Keep only recent metrics
                        if len(self.system_metrics) > self.max_metrics_history:
                            self.system_metrics = self.system_metrics[-self.max_metrics_history:]
                    
                    time.sleep(60)  # Collect every minute
                    
                except Exception as e:
                    self.logger.error(f"Error in metrics collection: {e}")
                    time.sleep(60)
        
        def alert_checker():
            """Check for alert conditions periodically"""
            while True:
                try:
                    alerts = self.check_alert_conditions()
                    
                    for alert in alerts:
                        self.send_alert(alert)
                    
                    time.sleep(self.config.monitoring.health_check_interval)
                    
                except Exception as e:
                    self.logger.error(f"Error in alert checking: {e}")
                    time.sleep(60)
        
        # Start threads
        metrics_thread = threading.Thread(target=metrics_collector, daemon=True)
        alert_thread = threading.Thread(target=alert_checker, daemon=True)
        
        metrics_thread.start()
        alert_thread.start()
        
        self.logger.info("APM monitoring threads started")


# Global APM monitor instance
_apm_monitor: Optional[APMMonitor] = None


def get_apm_monitor() -> APMMonitor:
    """Get the global APM monitor instance"""
    global _apm_monitor
    if _apm_monitor is None:
        _apm_monitor = APMMonitor()
    return _apm_monitor