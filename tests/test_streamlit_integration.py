"""
Integration tests for Streamlit dashboard
Tests dashboard functionality without requiring live Snowflake connection
"""

import pytest
from unittest.mock import Mock, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.dashboard_data import DashboardData


class TestDashboardData:
    """Test dashboard data access layer"""
    
    def test_get_property_list_no_filters(self):
        """Test retrieving property list without filters"""
        # Mock Snowflake connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock query results
        mock_cursor.fetchall.return_value = [
            ('PROP001', '123 Main St', '2024-01-15', 'High', 15, 'High risk property'),
            ('PROP002', '456 Oak Ave', '2024-01-16', 'Low', 2, 'Low risk property'),
        ]
        
        dashboard = DashboardData(mock_conn)
        properties = dashboard.get_property_list()
        
        assert len(properties) == 2
        assert properties[0]['property_id'] == 'PROP001'
        assert properties[0]['risk_category'] == 'High'
        assert properties[1]['property_id'] == 'PROP002'
        assert properties[1]['risk_category'] == 'Low'
    
    def test_get_property_list_with_risk_filter(self):
        """Test filtering properties by risk level"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            ('PROP001', '123 Main St', '2024-01-15', 'High', 15, 'High risk property'),
        ]
        
        dashboard = DashboardData(mock_conn)
        properties = dashboard.get_property_list(risk_level='High')
        
        assert len(properties) == 1
        assert properties[0]['risk_category'] == 'High'
        
        # Verify query was called with risk filter
        mock_cursor.execute.assert_called_once()
        query = mock_cursor.execute.call_args[0][0]
        assert 'risk_category' in query
    
    def test_get_property_list_with_defect_filter(self):
        """Test filtering properties by defect type"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            ('PROP001', '123 Main St', '2024-01-15', 'High', 15, 'Has exposed wiring'),
        ]
        
        dashboard = DashboardData(mock_conn)
        properties = dashboard.get_property_list(defect_type='exposed wiring')
        
        assert len(properties) == 1
        
        # Verify query includes joins for defect filtering
        query = mock_cursor.execute.call_args[0][0]
        assert 'defect_tags' in query
    
    def test_get_property_list_with_search(self):
        """Test searching properties by term"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            ('PROP001', '123 Main St', '2024-01-15', 'High', 15, 'Main street property'),
        ]
        
        dashboard = DashboardData(mock_conn)
        properties = dashboard.get_property_list(search_term='Main')
        
        assert len(properties) == 1
        
        # Verify query includes LIKE clauses
        query = mock_cursor.execute.call_args[0][0]
        assert 'LIKE' in query
    
    def test_get_property_details(self):
        """Test retrieving complete property details"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock property query
        mock_cursor.fetchone.side_effect = [
            ('PROP001', '123 Main St', '2024-01-15', 'High', 15, 'High risk property'),
        ]
        
        # Mock rooms query
        mock_cursor.fetchall.side_effect = [
            [('ROOM001', 'Kitchen', 'First Floor', 8)],  # Rooms
            [('FIND001', 'text', 'Exposed wiring found', None, None, 'processed')],  # Findings
            [('TAG001', 'exposed wiring', 0.95, 3, '2024-01-15')],  # Tags
        ]
        
        dashboard = DashboardData(mock_conn)
        property_data = dashboard.get_property_details('PROP001')
        
        assert property_data is not None
        assert property_data['property_id'] == 'PROP001'
        assert len(property_data['rooms']) == 1
        assert property_data['rooms'][0]['room_id'] == 'ROOM001'
        assert len(property_data['rooms'][0]['findings']) == 1
        assert len(property_data['rooms'][0]['findings'][0]['defect_tags']) == 1
    
    def test_get_property_details_not_found(self):
        """Test retrieving non-existent property"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = None
        
        dashboard = DashboardData(mock_conn)
        property_data = dashboard.get_property_details('NONEXISTENT')
        
        assert property_data is None
    
    def test_get_room_details(self):
        """Test retrieving room details"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock room query
        mock_cursor.fetchone.return_value = (
            'ROOM001', 'PROP001', 'Kitchen', 'First Floor', 8
        )
        
        # Mock findings and tags
        mock_cursor.fetchall.side_effect = [
            [('FIND001', 'text', 'Exposed wiring', None, None, 'processed')],
            [('TAG001', 'exposed wiring', 0.95, 3, '2024-01-15')],
        ]
        
        dashboard = DashboardData(mock_conn)
        room_data = dashboard.get_room_details('ROOM001')
        
        assert room_data is not None
        assert room_data['room_id'] == 'ROOM001'
        assert room_data['room_type'] == 'Kitchen'
        assert len(room_data['findings']) == 1


class TestDashboardApp:
    """Test dashboard UI functions"""
    
    def test_sanitize_error_message_with_password(self):
        """Test error sanitization removes password"""
        from src.dashboard_app import sanitize_error_message
        
        error = Exception("Connection failed: password=secret123")
        sanitized = sanitize_error_message(error)
        
        assert 'password' not in sanitized.lower()
        assert 'secret123' not in sanitized
        assert 'contact support' in sanitized.lower()
    
    def test_sanitize_error_message_with_connection_string(self):
        """Test error sanitization removes connection details"""
        from src.dashboard_app import sanitize_error_message
        
        error = Exception("Failed to connect to host=snowflake.com user=admin")
        sanitized = sanitize_error_message(error)
        
        assert 'host=' not in sanitized
        assert 'user=' not in sanitized
        assert 'snowflake.com' not in sanitized
    
    def test_sanitize_error_message_with_path(self):
        """Test error sanitization removes file paths"""
        from src.dashboard_app import sanitize_error_message
        
        error = Exception("File not found: /home/user/secrets.txt")
        sanitized = sanitize_error_message(error)
        
        assert '/home/' not in sanitized
        assert 'secrets.txt' not in sanitized
    
    def test_sanitize_error_message_generic(self):
        """Test error sanitization for generic errors"""
        from src.dashboard_app import sanitize_error_message
        
        error = Exception("Invalid input value")
        sanitized = sanitize_error_message(error)
        
        assert 'unexpected error' in sanitized.lower()
    
    def test_get_risk_color(self):
        """Test risk color mapping"""
        from src.dashboard_app import get_risk_color
        
        assert get_risk_color('Low') == 'green'
        assert get_risk_color('Medium') == 'orange'
        assert get_risk_color('High') == 'red'
        assert get_risk_color(None) == 'gray'
        assert get_risk_color('Unknown') == 'gray'
    
    def test_format_date(self):
        """Test date formatting"""
        from src.dashboard_app import format_date
        from datetime import date
        
        assert format_date(None) == "N/A"
        assert format_date("2024-01-15") == "2024-01-15"
        assert format_date(date(2024, 1, 15)) == "2024-01-15"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
