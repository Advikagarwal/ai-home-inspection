"""
Configuration Management System for AI-Assisted Home Inspection Workspace
Handles environment-specific settings with validation and secure credential management
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    account: str
    user: str
    password: str
    warehouse: str
    database: str
    schema: str = "PUBLIC"
    role: Optional[str] = None
    
    def validate(self) -> None:
        """Validate database configuration"""
        required_fields = {
            'account': self.account,
            'user': self.user,
            'password': self.password,
            'warehouse': self.warehouse,
            'database': self.database
        }
        
        missing = [name for name, value in required_fields.items() if not value]
        if missing:
            raise ValueError(f"Missing required database configuration: {', '.join(missing)}")
    
    def get_masked_dict(self) -> Dict[str, str]:
        """Get configuration dictionary with masked sensitive values"""
        return {
            'account': self.account,
            'user': self.user,
            'password': '***MASKED***',
            'warehouse': self.warehouse,
            'database': self.database,
            'schema': self.schema,
            'role': self.role
        }


@dataclass
class CortexAIConfig:
    """Cortex AI configuration"""
    enabled: bool = True
    timeout_seconds: int = 30
    retry_count: int = 3
    fallback_enabled: bool = True
    
    def validate(self) -> None:
        """Validate Cortex AI configuration"""
        if self.timeout_seconds <= 0:
            raise ValueError("Cortex AI timeout must be positive")
        if self.retry_count < 0:
            raise ValueError("Cortex AI retry count cannot be negative")


@dataclass
class MonitoringConfig:
    """Monitoring and alerting configuration"""
    metrics_enabled: bool = True
    log_level: str = "INFO"
    alert_email: Optional[str] = None
    alert_webhook: Optional[str] = None
    health_check_interval: int = 60
    error_threshold: int = 10
    performance_monitoring: bool = True
    audit_logging: bool = True
    
    def validate(self) -> None:
        """Validate monitoring configuration"""
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(f"Invalid log level: {self.log_level}. Must be one of {valid_log_levels}")
        
        self.log_level = self.log_level.upper()
        
        if self.health_check_interval <= 0:
            raise ValueError("Health check interval must be positive")
        if self.error_threshold < 0:
            raise ValueError("Error threshold cannot be negative")


@dataclass
class PerformanceConfig:
    """Performance optimization configuration"""
    batch_size: int = 100
    max_workers: int = 4
    cache_ttl_seconds: int = 300
    connection_pool_size: int = 5
    
    def validate(self) -> None:
        """Validate performance configuration"""
        if self.batch_size <= 0:
            raise ValueError("Batch size must be positive")
        if self.max_workers <= 0:
            raise ValueError("Max workers must be positive")
        if self.cache_ttl_seconds < 0:
            raise ValueError("Cache TTL cannot be negative")
        if self.connection_pool_size <= 0:
            raise ValueError("Connection pool size must be positive")


@dataclass
class FeatureFlags:
    """Feature flags for enabling/disabling features"""
    enable_image_classification: bool = True
    enable_text_classification: bool = True
    enable_summary_generation: bool = True
    enable_export: bool = True
    enable_materialized_views: bool = True
    
    def validate(self) -> None:
        """Validate feature flags"""
        # No specific validation needed for boolean flags
        pass


@dataclass
class Config:
    """Main configuration class"""
    environment: str
    database: DatabaseConfig
    cortex_ai: CortexAIConfig = field(default_factory=CortexAIConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    features: FeatureFlags = field(default_factory=FeatureFlags)
    
    def validate(self) -> None:
        """Validate all configuration sections"""
        # Validate environment
        valid_environments = ['development', 'staging', 'production']
        if self.environment not in valid_environments:
            raise ValueError(f"Invalid environment: {self.environment}. Must be one of {valid_environments}")
        
        # Validate each section
        self.database.validate()
        self.cortex_ai.validate()
        self.monitoring.validate()
        self.performance.validate()
        self.features.validate()
    
    def get_masked_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary with masked sensitive values"""
        return {
            'environment': self.environment,
            'database': self.database.get_masked_dict(),
            'cortex_ai': {
                'enabled': self.cortex_ai.enabled,
                'timeout_seconds': self.cortex_ai.timeout_seconds,
                'retry_count': self.cortex_ai.retry_count,
                'fallback_enabled': self.cortex_ai.fallback_enabled
            },
            'monitoring': {
                'metrics_enabled': self.monitoring.metrics_enabled,
                'log_level': self.monitoring.log_level,
                'alert_email': self.monitoring.alert_email,
                'alert_webhook': '***MASKED***' if self.monitoring.alert_webhook else None
            },
            'performance': {
                'batch_size': self.performance.batch_size,
                'max_workers': self.performance.max_workers,
                'cache_ttl_seconds': self.performance.cache_ttl_seconds,
                'connection_pool_size': self.performance.connection_pool_size
            },
            'features': {
                'enable_image_classification': self.features.enable_image_classification,
                'enable_text_classification': self.features.enable_text_classification,
                'enable_summary_generation': self.features.enable_summary_generation,
                'enable_export': self.features.enable_export,
                'enable_materialized_views': self.features.enable_materialized_views
            }
        }


class ConfigLoader:
    """Loads configuration from files and environment variables"""
    
    @staticmethod
    def load_from_file(config_path: str) -> Config:
        """
        Load configuration from JSON file
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Config object
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(path, 'r') as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        
        return ConfigLoader._parse_config_dict(config_data)
    
    @staticmethod
    def load_from_env() -> Config:
        """
        Load configuration from environment variables
        
        Returns:
            Config object
            
        Raises:
            ValueError: If required environment variables are missing
        """
        # Determine environment
        environment = os.getenv('ENVIRONMENT', 'development')
        
        # Database configuration
        database = DatabaseConfig(
            account=os.getenv('SNOWFLAKE_ACCOUNT', ''),
            user=os.getenv('SNOWFLAKE_USER', ''),
            password=os.getenv('SNOWFLAKE_PASSWORD', ''),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE', ''),
            database=os.getenv('SNOWFLAKE_DATABASE', ''),
            schema=os.getenv('SNOWFLAKE_SCHEMA', 'PUBLIC'),
            role=os.getenv('SNOWFLAKE_ROLE')
        )
        
        # Cortex AI configuration
        cortex_ai = CortexAIConfig(
            enabled=os.getenv('CORTEX_AI_ENABLED', 'true').lower() == 'true',
            timeout_seconds=int(os.getenv('CORTEX_AI_TIMEOUT', '30')),
            retry_count=int(os.getenv('CORTEX_AI_RETRY_COUNT', '3')),
            fallback_enabled=os.getenv('CORTEX_AI_FALLBACK_ENABLED', 'true').lower() == 'true'
        )
        
        # Monitoring configuration
        monitoring = MonitoringConfig(
            metrics_enabled=os.getenv('METRICS_ENABLED', 'true').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            alert_email=os.getenv('ALERT_EMAIL'),
            alert_webhook=os.getenv('ALERT_WEBHOOK')
        )
        
        # Performance configuration
        performance = PerformanceConfig(
            batch_size=int(os.getenv('BATCH_SIZE', '100')),
            max_workers=int(os.getenv('MAX_WORKERS', '4')),
            cache_ttl_seconds=int(os.getenv('CACHE_TTL_SECONDS', '300')),
            connection_pool_size=int(os.getenv('CONNECTION_POOL_SIZE', '5'))
        )
        
        # Feature flags
        features = FeatureFlags(
            enable_image_classification=os.getenv('ENABLE_IMAGE_CLASSIFICATION', 'true').lower() == 'true',
            enable_text_classification=os.getenv('ENABLE_TEXT_CLASSIFICATION', 'true').lower() == 'true',
            enable_summary_generation=os.getenv('ENABLE_SUMMARY_GENERATION', 'true').lower() == 'true',
            enable_export=os.getenv('ENABLE_EXPORT', 'true').lower() == 'true',
            enable_materialized_views=os.getenv('ENABLE_MATERIALIZED_VIEWS', 'true').lower() == 'true'
        )
        
        return Config(
            environment=environment,
            database=database,
            cortex_ai=cortex_ai,
            monitoring=monitoring,
            performance=performance,
            features=features
        )
    
    @staticmethod
    def load(config_path: Optional[str] = None) -> Config:
        """
        Load configuration from file or environment variables
        
        Priority:
        1. If config_path is provided, load from file
        2. If CONFIG_FILE env var is set, load from that file
        3. Otherwise, load from environment variables
        
        Args:
            config_path: Optional path to configuration file
            
        Returns:
            Validated Config object
            
        Raises:
            ValueError: If configuration is invalid or incomplete
        """
        # Determine config source
        if config_path:
            config = ConfigLoader.load_from_file(config_path)
        elif os.getenv('CONFIG_FILE'):
            config = ConfigLoader.load_from_file(os.getenv('CONFIG_FILE'))
        else:
            config = ConfigLoader.load_from_env()
        
        # Validate configuration
        try:
            config.validate()
        except ValueError as e:
            raise ValueError(f"Configuration validation failed: {e}")
        
        return config
    
    @staticmethod
    def _parse_config_dict(config_data: Dict[str, Any]) -> Config:
        """Parse configuration dictionary into Config object"""
        # Parse database config
        db_data = config_data.get('database', {})
        database = DatabaseConfig(
            account=db_data.get('account', ''),
            user=db_data.get('user', ''),
            password=db_data.get('password', ''),
            warehouse=db_data.get('warehouse', ''),
            database=db_data.get('database', ''),
            schema=db_data.get('schema', 'PUBLIC'),
            role=db_data.get('role')
        )
        
        # Parse Cortex AI config
        cortex_data = config_data.get('cortex_ai', {})
        cortex_ai = CortexAIConfig(
            enabled=cortex_data.get('enabled', True),
            timeout_seconds=cortex_data.get('timeout_seconds', 30),
            retry_count=cortex_data.get('retry_count', 3),
            fallback_enabled=cortex_data.get('fallback_enabled', True)
        )
        
        # Parse monitoring config
        mon_data = config_data.get('monitoring', {})
        monitoring = MonitoringConfig(
            metrics_enabled=mon_data.get('metrics_enabled', True),
            log_level=mon_data.get('log_level', 'INFO'),
            alert_email=mon_data.get('alert_email'),
            alert_webhook=mon_data.get('alert_webhook'),
            health_check_interval=mon_data.get('health_check_interval', 60),
            error_threshold=mon_data.get('error_threshold', 10),
            performance_monitoring=mon_data.get('performance_monitoring', True),
            audit_logging=mon_data.get('audit_logging', True)
        )
        
        # Parse performance config
        perf_data = config_data.get('performance', {})
        performance = PerformanceConfig(
            batch_size=perf_data.get('batch_size', 100),
            max_workers=perf_data.get('max_workers', 4),
            cache_ttl_seconds=perf_data.get('cache_ttl_seconds', 300),
            connection_pool_size=perf_data.get('connection_pool_size', 5)
        )
        
        # Parse feature flags
        feat_data = config_data.get('features', {})
        features = FeatureFlags(
            enable_image_classification=feat_data.get('enable_image_classification', True),
            enable_text_classification=feat_data.get('enable_text_classification', True),
            enable_summary_generation=feat_data.get('enable_summary_generation', True),
            enable_export=feat_data.get('enable_export', True),
            enable_materialized_views=feat_data.get('enable_materialized_views', True)
        )
        
        return Config(
            environment=config_data.get('environment', 'development'),
            database=database,
            cortex_ai=cortex_ai,
            monitoring=monitoring,
            performance=performance,
            features=features
        )


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance
    
    Returns:
        Config object
        
    Raises:
        RuntimeError: If configuration hasn't been initialized
    """
    global _config
    if _config is None:
        raise RuntimeError("Configuration not initialized. Call init_config() first.")
    return _config


def init_config(config_path: Optional[str] = None) -> Config:
    """
    Initialize the global configuration
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Config object
    """
    global _config
    _config = ConfigLoader.load(config_path)
    return _config


def is_production() -> bool:
    """Check if running in production environment"""
    try:
        config = get_config()
        return config.environment == 'production'
    except RuntimeError:
        return False


def is_development() -> bool:
    """Check if running in development environment"""
    try:
        config = get_config()
        return config.environment == 'development'
    except RuntimeError:
        return True  # Default to development if not initialized
