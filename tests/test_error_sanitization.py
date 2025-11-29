"""
Property-based tests for error message sanitization
Validates: Requirements 9.5
"""

import pytest
from hypothesis import given, strategies as st, settings
from src.dashboard_app import sanitize_error_message


# Define sensitive patterns that should be hidden
SENSITIVE_PATTERNS = [
    'password', 'connection string', 'api key', 'secret',
    'token', 'credential', 'host=', 'user=', 'pwd=',
    'database=', 'server=', '/home/', '/usr/', 'c:\\',
    'snowflake.snowflakecomputing.com'
]


@st.composite
def error_with_sensitive_data(draw):
    """
    Generate error messages containing sensitive information
    """
    # Choose a sensitive pattern
    sensitive_pattern = draw(st.sampled_from(SENSITIVE_PATTERNS))
    
    # Generate some context around it
    prefix = draw(st.text(min_size=0, max_size=50))
    suffix = draw(st.text(min_size=0, max_size=50))
    
    # Create error message with sensitive data
    error_message = f"{prefix}{sensitive_pattern}{suffix}"
    
    return Exception(error_message)


@st.composite
def database_error(draw):
    """
    Generate database-related error messages
    """
    db_keywords = ['database', 'connection', 'query', 'sql', 'SQL']
    keyword = draw(st.sampled_from(db_keywords))
    
    prefix = draw(st.text(min_size=0, max_size=50))
    suffix = draw(st.text(min_size=0, max_size=50))
    
    error_message = f"{prefix}{keyword}{suffix}"
    
    return Exception(error_message)


@st.composite
def generic_error(draw):
    """
    Generate generic error messages without sensitive data
    """
    # Generate text that doesn't contain sensitive patterns or database keywords
    safe_chars = st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters=' .,!?'
    )
    error_message = draw(st.text(alphabet=safe_chars, min_size=1, max_size=100))
    
    # Make sure it doesn't accidentally contain sensitive patterns
    for pattern in SENSITIVE_PATTERNS + ['database', 'connection', 'query', 'sql']:
        if pattern.lower() in error_message.lower():
            # Skip this example if it contains sensitive data
            return Exception("Safe error message")
    
    return Exception(error_message)


# **Feature: ai-home-inspection, Property 27: Error messages hide sensitive details**
@given(error=error_with_sensitive_data())
@settings(max_examples=100)
def test_property_27_sensitive_data_is_hidden(error):
    """
    Property 27: Error messages hide sensitive details
    
    For any error containing sensitive information (passwords, connection strings,
    API keys, file paths, etc.), the sanitized message should not contain that
    sensitive information.
    
    **Validates: Requirements 9.5**
    """
    sanitized = sanitize_error_message(error)
    
    # Check that sanitized message doesn't contain any sensitive patterns
    sanitized_lower = sanitized.lower()
    
    for pattern in SENSITIVE_PATTERNS:
        assert pattern not in sanitized_lower, (
            f"Sanitized message contains sensitive pattern '{pattern}': {sanitized}"
        )


# **Feature: ai-home-inspection, Property 27: Error messages hide sensitive details**
@given(error=database_error())
@settings(max_examples=100)
def test_property_27_database_errors_are_generic(error):
    """
    Property 27: Error messages hide sensitive details (database errors)
    
    For any database-related error, the sanitized message should be generic
    and not expose database details.
    
    **Validates: Requirements 9.5**
    """
    sanitized = sanitize_error_message(error)
    
    # Database errors should return a generic message
    assert "Unable to retrieve data" in sanitized or "error occurred" in sanitized, (
        f"Database error should return generic message, got: {sanitized}"
    )


# **Feature: ai-home-inspection, Property 27: Error messages hide sensitive details**
@given(error=generic_error())
@settings(max_examples=100)
def test_property_27_sanitization_always_returns_safe_message(error):
    """
    Property 27: Error messages hide sensitive details (always safe)
    
    For any error, the sanitized message should always be a safe, user-friendly
    message without exposing system internals.
    
    **Validates: Requirements 9.5**
    """
    sanitized = sanitize_error_message(error)
    
    # Should return a string
    assert isinstance(sanitized, str), "Sanitized message should be a string"
    
    # Should not be empty
    assert len(sanitized) > 0, "Sanitized message should not be empty"
    
    # Should not contain any sensitive patterns
    sanitized_lower = sanitized.lower()
    for pattern in SENSITIVE_PATTERNS:
        assert pattern not in sanitized_lower, (
            f"Sanitized message contains sensitive pattern '{pattern}': {sanitized}"
        )


# Unit tests for specific edge cases
def test_password_in_connection_string():
    """Test that password in connection string is hidden"""
    error = Exception("Connection failed: host=db.example.com user=admin password=secret123")
    sanitized = sanitize_error_message(error)
    
    assert "password" not in sanitized.lower()
    assert "secret123" not in sanitized
    assert "admin" not in sanitized


def test_api_key_exposure():
    """Test that API keys are hidden"""
    error = Exception("API request failed with key: sk_live_abc123xyz")
    sanitized = sanitize_error_message(error)
    
    assert "api key" not in sanitized.lower()
    assert "sk_live_abc123xyz" not in sanitized


def test_file_path_exposure():
    """Test that file paths are hidden"""
    error = Exception("File not found: /home/user/.config/secrets.json")
    sanitized = sanitize_error_message(error)
    
    assert "/home/" not in sanitized
    assert "secrets.json" not in sanitized


def test_snowflake_connection_details():
    """Test that Snowflake connection details are hidden"""
    error = Exception("Failed to connect to account.snowflake.snowflakecomputing.com")
    sanitized = sanitize_error_message(error)
    
    assert "snowflake.snowflakecomputing.com" not in sanitized.lower()
    assert "account" not in sanitized or "error occurred" in sanitized


def test_database_query_error():
    """Test that database query errors are genericized"""
    error = Exception("SQL query failed: SELECT * FROM sensitive_table")
    sanitized = sanitize_error_message(error)
    
    assert "Unable to retrieve data" in sanitized or "error occurred" in sanitized
    assert "SELECT" not in sanitized
    assert "sensitive_table" not in sanitized


def test_generic_error_passthrough():
    """Test that truly generic errors get a safe message"""
    error = Exception("Invalid input format")
    sanitized = sanitize_error_message(error)
    
    # Should return a generic safe message
    assert isinstance(sanitized, str)
    assert len(sanitized) > 0
