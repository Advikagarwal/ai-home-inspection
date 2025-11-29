"""
Tests for configuration management system
Includes property-based tests and unit tests for configuration validation
"""

import pytest
import os
import json
import tempfile
from hypothesis import given, strategies as st, settings
from pathlib import Path

from src.config import (
    Config, DatabaseConfig, CortexAIConfig, MonitoringConfig,
    PerformanceConfig, FeatureFlags, ConfigLoader,
    init_config, get_config
)


# ============================================================================
# Property-Based Tests
# ============================================================================

@st.composite
def valid_database_config(draw):
    """Generate valid database configuration"""
    return {
        'account': draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='.-'))),
        'user': draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_'))),
        'password': draw(st.text(min_size=8, max_size=50)),
        'warehouse': draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'), whitelist_characters='_'))),
        'database': draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'), whitelist_characters='_'))),
        'schema': draw(st.sampled_from(['PUBLIC', 'PRIVATE', 'STAGING'])),
        'role': draw(st.one_of(st.none(), st.text(min_size=1, max_size=30)))
    }


@st.composite
def valid_config_dict(draw):
    """Generate valid complete configuration dictionary"""
    db_config = draw(valid_database_config())
    
    return {
        'environment': draw(st.sampled_from(['development', 'staging', 'production'])),
        'database': db_config,
        'cortex_ai': {
            'enabled': draw(st.booleans()),
            'timeout_seconds': draw(st.integers(min_value=1, max_value=300)),
            'retry_count': draw(st.integers(min_value=0, max_value=10)),
            'fallback_enabled': draw(st.booleans())
        },
        'monitoring': {
            'metrics_enabled': draw(st.booleans()),
            'log_level': draw(st.sampled_from(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])),
            'alert_email': draw(st.one_of(st.none(), st.emails())),
            'alert_webhook': draw(st.one_of(st.none(), st.text(min_size=10)))
        },
        'performance': {
            'batch_size': draw(st.integers(min_value=1, max_value=1000)),
            'max_workers': draw(st.integers(min_value=1, max_value=32)),
            'cache_ttl_seconds': draw(st.integers(min_value=0, max_value=3600)),
            'connection_pool_size': draw(st.integers(min_value=1, max_value=50))
        },
        'features': {
            'enable_image_classification': draw(st.booleans()),
            'enable_text_classification': draw(st.booleans()),
            'enable_summary_generation': draw(st.booleans()),
            'enable_export': draw(st.booleans()),
            'enable_materialized_views': draw(st.booleans())
        }
    }


@given(config_dict=valid_config_dict())
@settings(max_examples=100)
def test_property_configuration_completeness(config_dict):
    """
    **Feature: production-deployment, Property 1: Configuration completeness**
    **Validates: Requirements 1.1, 1.3**
    
    For any environment deployment, all required configuration values must be 
    present and valid before the system starts.
    
    This property test verifies that:
    1. Valid configuration can be loaded and parsed
    2. All required fields are validated
    3. Configuration can be retrieved after initialization
    """
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_dict, f)
        config_file = f.name
    
    try:
        # Load configuration from file
        config = ConfigLoader.load(config_file)
        
        # Verify all required database fields are present
        assert config.database.account
        assert config.database.user
        assert config.database.password
        assert config.database.warehouse
        assert config.database.database
        
        # Verify environment is valid
        assert config.environment in ['development', 'staging', 'production']
        
        # Verify configuration validates successfully
        config.validate()  # Should not raise
        
        # Verify configuration can be retrieved as masked dict
        masked = config.get_masked_dict()
        assert masked['database']['password'] == '***MASKED***'
        assert masked['database']['account'] == config.database.account
        
    finally:
        # Clean up temp file
        os.unlink(config_file)


# ============================================================================
# Unit Tests for Configuration Validation
# ============================================================================

class TestDatabaseConfig:
    """Tests for DatabaseConfig validation"""
    
    def test_valid_database_config(self):
        """Test that valid database configuration passes validation"""
        config = DatabaseConfig(
            account='test-account',
            user='test_user',
            password='test_password',
            warehouse='TEST_WH',
            database='TEST_DB',
            schema='PUBLIC'
        )
        config.validate()  # Should not raise
    
    def test_missing_account_raises_error(self):
        """Test that missing account raises ValueError"""
        config = DatabaseConfig(
            account='',
            user='test_user',
            password='test_password',
            warehouse='TEST_WH',
            database='TEST_DB'
        )
        with pytest.raises(ValueError, match='Missing required database configuration.*account'):
            config.validate()
    
    def test_missing_user_raises_error(self):
        """Test that missing user raises ValueError"""
        config = DatabaseConfig(
            account='test-account',
            user='',
            password='test_password',
            warehouse='TEST_WH',
            database='TEST_DB'
        )
        with pytest.raises(ValueError, match='Missing required database configuration.*user'):
            config.validate()
    
    def test_missing_password_raises_error(self):
        """Test that missing password raises ValueError"""
        config = DatabaseConfig(
            account='test-account',
            user='test_user',
            password='',
            warehouse='TEST_WH',
            database='TEST_DB'
        )
        with pytest.raises(ValueError, match='Missing required database configuration.*password'):
            config.validate()
    
    def test_missing_warehouse_raises_error(self):
        """Test that missing warehouse raises ValueError"""
        config = DatabaseConfig(
            account='test-account',
            user='test_user',
            password='test_password',
            warehouse='',
            database='TEST_DB'
        )
        with pytest.raises(ValueError, match='Missing required database configuration.*warehouse'):
            config.validate()
    
    def test_missing_database_raises_error(self):
        """Test that missing database raises ValueError"""
        config = DatabaseConfig(
            account='test-account',
            user='test_user',
            password='test_password',
            warehouse='TEST_WH',
            database=''
        )
        with pytest.raises(ValueError, match='Missing required database configuration.*database'):
            config.validate()
    
    def test_password_masking(self):
        """Test that password is masked in get_masked_dict"""
        config = DatabaseConfig(
            account='test-account',
            user='test_user',
            password='secret_password_123',
            warehouse='TEST_WH',
            database='TEST_DB'
        )
        masked = config.get_masked_dict()
        assert masked['password'] == '***MASKED***'
        assert masked['account'] == 'test-account'
        assert masked['user'] == 'test_user'


class TestCortexAIConfig:
    """Tests for CortexAIConfig validation"""
    
    def test_valid_cortex_config(self):
        """Test that valid Cortex AI configuration passes validation"""
        config = CortexAIConfig(
            enabled=True,
            timeout_seconds=30,
            retry_count=3,
            fallback_enabled=True
        )
        config.validate()  # Should not raise
    
    def test_negative_timeout_raises_error(self):
        """Test that negative timeout raises ValueError"""
        config = CortexAIConfig(timeout_seconds=-1)
        with pytest.raises(ValueError, match='timeout must be positive'):
            config.validate()
    
    def test_zero_timeout_raises_error(self):
        """Test that zero timeout raises ValueError"""
        config = CortexAIConfig(timeout_seconds=0)
        with pytest.raises(ValueError, match='timeout must be positive'):
            config.validate()
    
    def test_negative_retry_count_raises_error(self):
        """Test that negative retry count raises ValueError"""
        config = CortexAIConfig(retry_count=-1)
        with pytest.raises(ValueError, match='retry count cannot be negative'):
            config.validate()


class TestMonitoringConfig:
    """Tests for MonitoringConfig validation"""
    
    def test_valid_monitoring_config(self):
        """Test that valid monitoring configuration passes validation"""
        config = MonitoringConfig(
            metrics_enabled=True,
            log_level='INFO',
            alert_email='test@example.com'
        )
        config.validate()  # Should not raise
    
    def test_invalid_log_level_raises_error(self):
        """Test that invalid log level raises ValueError"""
        config = MonitoringConfig(log_level='INVALID')
        with pytest.raises(ValueError, match='Invalid log level'):
            config.validate()
    
    def test_log_level_case_insensitive(self):
        """Test that log level is normalized to uppercase"""
        config = MonitoringConfig(log_level='info')
        config.validate()
        assert config.log_level == 'INFO'


class TestPerformanceConfig:
    """Tests for PerformanceConfig validation"""
    
    def test_valid_performance_config(self):
        """Test that valid performance configuration passes validation"""
        config = PerformanceConfig(
            batch_size=100,
            max_workers=4,
            cache_ttl_seconds=300,
            connection_pool_size=5
        )
        config.validate()  # Should not raise
    
    def test_negative_batch_size_raises_error(self):
        """Test that negative batch size raises ValueError"""
        config = PerformanceConfig(batch_size=-1)
        with pytest.raises(ValueError, match='Batch size must be positive'):
            config.validate()
    
    def test_zero_batch_size_raises_error(self):
        """Test that zero batch size raises ValueError"""
        config = PerformanceConfig(batch_size=0)
        with pytest.raises(ValueError, match='Batch size must be positive'):
            config.validate()
    
    def test_negative_max_workers_raises_error(self):
        """Test that negative max workers raises ValueError"""
        config = PerformanceConfig(max_workers=-1)
        with pytest.raises(ValueError, match='Max workers must be positive'):
            config.validate()
    
    def test_negative_cache_ttl_raises_error(self):
        """Test that negative cache TTL raises ValueError"""
        config = PerformanceConfig(cache_ttl_seconds=-1)
        with pytest.raises(ValueError, match='Cache TTL cannot be negative'):
            config.validate()
    
    def test_zero_connection_pool_raises_error(self):
        """Test that zero connection pool size raises ValueError"""
        config = PerformanceConfig(connection_pool_size=0)
        with pytest.raises(ValueError, match='Connection pool size must be positive'):
            config.validate()


class TestConfig:
    """Tests for main Config class"""
    
    def test_valid_config(self):
        """Test that valid complete configuration passes validation"""
        config = Config(
            environment='development',
            database=DatabaseConfig(
                account='test-account',
                user='test_user',
                password='test_password',
                warehouse='TEST_WH',
                database='TEST_DB'
            )
        )
        config.validate()  # Should not raise
    
    def test_invalid_environment_raises_error(self):
        """Test that invalid environment raises ValueError"""
        config = Config(
            environment='invalid',
            database=DatabaseConfig(
                account='test-account',
                user='test_user',
                password='test_password',
                warehouse='TEST_WH',
                database='TEST_DB'
            )
        )
        with pytest.raises(ValueError, match='Invalid environment'):
            config.validate()
    
    def test_config_validates_all_sections(self):
        """Test that config validation checks all sections"""
        config = Config(
            environment='development',
            database=DatabaseConfig(
                account='',  # Invalid
                user='test_user',
                password='test_password',
                warehouse='TEST_WH',
                database='TEST_DB'
            )
        )
        with pytest.raises(ValueError):
            config.validate()


class TestConfigLoader:
    """Tests for ConfigLoader"""
    
    def test_load_from_valid_file(self):
        """Test loading configuration from valid JSON file"""
        config_data = {
            'environment': 'development',
            'database': {
                'account': 'test-account',
                'user': 'test_user',
                'password': 'test_password',
                'warehouse': 'TEST_WH',
                'database': 'TEST_DB',
                'schema': 'PUBLIC'
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            config = ConfigLoader.load_from_file(config_file)
            assert config.environment == 'development'
            assert config.database.account == 'test-account'
        finally:
            os.unlink(config_file)
    
    def test_load_from_nonexistent_file_raises_error(self):
        """Test that loading from nonexistent file raises FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load_from_file('/nonexistent/config.json')
    
    def test_load_from_invalid_json_raises_error(self):
        """Test that loading invalid JSON raises ValueError"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{ invalid json }')
            config_file = f.name
        
        try:
            with pytest.raises(ValueError, match='Invalid JSON'):
                ConfigLoader.load_from_file(config_file)
        finally:
            os.unlink(config_file)
    
    def test_load_from_env_variables(self, monkeypatch):
        """Test loading configuration from environment variables"""
        monkeypatch.setenv('ENVIRONMENT', 'staging')
        monkeypatch.setenv('SNOWFLAKE_ACCOUNT', 'test-account')
        monkeypatch.setenv('SNOWFLAKE_USER', 'test_user')
        monkeypatch.setenv('SNOWFLAKE_PASSWORD', 'test_password')
        monkeypatch.setenv('SNOWFLAKE_WAREHOUSE', 'TEST_WH')
        monkeypatch.setenv('SNOWFLAKE_DATABASE', 'TEST_DB')
        monkeypatch.setenv('LOG_LEVEL', 'DEBUG')
        
        config = ConfigLoader.load_from_env()
        assert config.environment == 'staging'
        assert config.database.account == 'test-account'
        assert config.monitoring.log_level == 'DEBUG'
    
    def test_load_validates_configuration(self):
        """Test that load() validates the configuration"""
        config_data = {
            'environment': 'development',
            'database': {
                'account': '',  # Invalid - missing required field
                'user': 'test_user',
                'password': 'test_password',
                'warehouse': 'TEST_WH',
                'database': 'TEST_DB'
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            with pytest.raises(ValueError, match='Configuration validation failed'):
                ConfigLoader.load(config_file)
        finally:
            os.unlink(config_file)


class TestCredentialMasking:
    """Tests for credential masking in error messages"""
    
    def test_password_not_in_masked_dict(self):
        """Test that password is masked in configuration dictionary"""
        config = Config(
            environment='development',
            database=DatabaseConfig(
                account='test-account',
                user='test_user',
                password='super_secret_password',
                warehouse='TEST_WH',
                database='TEST_DB'
            )
        )
        
        masked = config.get_masked_dict()
        
        # Password should be masked
        assert 'super_secret_password' not in str(masked)
        assert masked['database']['password'] == '***MASKED***'
    
    def test_webhook_masked_in_dict(self):
        """Test that webhook URL is masked in configuration dictionary"""
        config = Config(
            environment='development',
            database=DatabaseConfig(
                account='test-account',
                user='test_user',
                password='test_password',
                warehouse='TEST_WH',
                database='TEST_DB'
            ),
            monitoring=MonitoringConfig(
                alert_webhook='https://hooks.slack.com/services/SECRET/TOKEN/HERE'
            )
        )
        
        masked = config.get_masked_dict()
        
        # Webhook should be masked
        assert 'SECRET' not in str(masked)
        assert masked['monitoring']['alert_webhook'] == '***MASKED***'
    
    def test_validation_error_does_not_expose_password(self):
        """Test that validation errors don't expose passwords"""
        config = DatabaseConfig(
            account='',
            user='test_user',
            password='super_secret_password_123',
            warehouse='TEST_WH',
            database='TEST_DB'
        )
        
        try:
            config.validate()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            error_message = str(e)
            # Password should not appear in error message
            assert 'super_secret_password_123' not in error_message
            assert 'password' not in error_message.lower() or 'missing' in error_message.lower()
