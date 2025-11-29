"""
Unit tests for Streamlit dashboard application
Tests core functionality without requiring Streamlit runtime
"""

import pytest
from src.dashboard_app import sanitize_error_message, get_risk_color, format_date
from datetime import date


def test_sanitize_error_message_with_password():
    """Test that passwords are sanitized from error messages"""
    error = Exception("Connection failed: password=secret123")
    result = sanitize_error_message(error)
    
    assert "password" not in result.lower()
    assert "secret123" not in result
    assert "error occurred" in result.lower()


def test_sanitize_error_message_with_connection_string():
    """Test that connection strings are sanitized"""
    error = Exception("Failed to connect: host=db.example.com user=admin")
    result = sanitize_error_message(error)
    
    assert "host=" not in result.lower()
    assert "user=" not in result.lower()
    assert "error occurred" in result.lower()


def test_sanitize_error_message_with_database_error():
    """Test that database errors are genericized"""
    error = Exception("Database query failed")
    result = sanitize_error_message(error)
    
    assert "Unable to retrieve data" in result or "error occurred" in result.lower()


def test_get_risk_color_low():
    """Test risk color for Low risk"""
    assert get_risk_color("Low") == "green"


def test_get_risk_color_medium():
    """Test risk color for Medium risk"""
    assert get_risk_color("Medium") == "orange"


def test_get_risk_color_high():
    """Test risk color for High risk"""
    assert get_risk_color("High") == "red"


def test_get_risk_color_none():
    """Test risk color for None value"""
    assert get_risk_color(None) == "gray"


def test_get_risk_color_unknown():
    """Test risk color for unknown value"""
    assert get_risk_color("Unknown") == "gray"


def test_format_date_with_date_object():
    """Test date formatting with date object"""
    test_date = date(2024, 1, 15)
    result = format_date(test_date)
    assert result == "2024-01-15"


def test_format_date_with_string():
    """Test date formatting with string"""
    result = format_date("2024-01-15")
    assert result == "2024-01-15"


def test_format_date_with_none():
    """Test date formatting with None"""
    result = format_date(None)
    assert result == "N/A"
