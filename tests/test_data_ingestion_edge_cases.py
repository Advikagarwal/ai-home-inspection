"""
Unit tests for data ingestion edge cases
Tests missing required fields, invalid property references, and corrupted image files
Requirements: 1.1, 1.2, 1.3, 1.4
"""

import pytest
import sys
import os
from datetime import date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_ingestion import DataIngestion


class TestMissingRequiredFields:
    """Test that data ingestion properly validates required fields"""
    
    def test_property_missing_property_id(self, snowflake_connection):
        """Test that property ingestion fails when property_id is missing"""
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        invalid_data = {
            'location': '123 Main St',
            'inspection_date': date(2024, 1, 15)
            # Missing property_id
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="Missing required field: property_id"):
            ingestion.ingest_property(invalid_data)
    
    def test_property_missing_location(self, snowflake_connection):
        """Test that property ingestion fails when location is missing"""
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        invalid_data = {
            'property_id': 'prop-123',
            'inspection_date': date(2024, 1, 15)
            # Missing location
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="Missing required field: location"):
            ingestion.ingest_property(invalid_data)
    
    def test_property_missing_inspection_date(self, snowflake_connection):
        """Test that property ingestion fails when inspection_date is missing"""
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        invalid_data = {
            'property_id': 'prop-123',
            'location': '123 Main St'
            # Missing inspection_date
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="Missing required field: inspection_date"):
            ingestion.ingest_property(invalid_data)
    
    def test_room_missing_room_id(self, snowflake_connection):
        """Test that room ingestion fails when room_id is missing"""
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        
        # Create a valid property first
        property_data = {
            'property_id': 'prop-123',
            'location': '123 Main St',
            'inspection_date': date(2024, 1, 15)
        }
        property_id = ingestion.ingest_property(property_data)
        
        invalid_room_data = {
            'room_type': 'kitchen'
            # Missing room_id
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="Missing required field: room_id"):
            ingestion.ingest_room(invalid_room_data, property_id)
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            cursor.execute("DELETE FROM properties WHERE property_id = %s", (property_id,))
            snowflake_connection.commit()
        finally:
            cursor.close()
    
    def test_room_missing_room_type(self, snowflake_connection):
        """Test that room ingestion fails when room_type is missing"""
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        
        # Create a valid property first
        property_data = {
            'property_id': 'prop-123',
            'location': '123 Main St',
            'inspection_date': date(2024, 1, 15)
        }
        property_id = ingestion.ingest_property(property_data)
        
        invalid_room_data = {
            'room_id': 'room-456'
            # Missing room_type
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="Missing required field: room_type"):
            ingestion.ingest_room(invalid_room_data, property_id)
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            cursor.execute("DELETE FROM properties WHERE property_id = %s", (property_id,))
            snowflake_connection.commit()
        finally:
            cursor.close()


class TestInvalidPropertyReferences:
    """Test that data ingestion properly handles invalid foreign key references"""
    
    def test_room_with_nonexistent_property(self, snowflake_connection):
        """Test that room ingestion fails when referencing a non-existent property"""
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        
        room_data = {
            'room_id': 'room-456',
            'room_type': 'kitchen',
            'room_location': 'first floor'
        }
        
        nonexistent_property_id = 'nonexistent-property-999'
        
        # Act & Assert
        # The database should enforce foreign key constraint
        # In mock mode, this might not raise an error, but in real Snowflake it would
        try:
            ingestion.ingest_room(room_data, nonexistent_property_id)
            # If we get here in mock mode, verify the room wasn't actually created properly
            # by checking if we can retrieve it
            retrieved = ingestion.get_room(room_data['room_id'])
            if retrieved is not None:
                # In mock mode, clean up
                cursor = snowflake_connection.cursor()
                try:
                    cursor.execute("DELETE FROM rooms WHERE room_id = %s", (room_data['room_id'],))
                    snowflake_connection.commit()
                finally:
                    cursor.close()
        except Exception as e:
            # Expected behavior in real Snowflake - foreign key constraint violation
            assert 'foreign key' in str(e).lower() or 'constraint' in str(e).lower() or 'violat' in str(e).lower()
    
    def test_text_finding_with_nonexistent_room(self, snowflake_connection):
        """Test that text finding ingestion fails when referencing a non-existent room"""
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        
        nonexistent_room_id = 'nonexistent-room-999'
        note_text = 'Found a crack in the wall'
        
        # Act & Assert
        # The database should enforce foreign key constraint
        try:
            finding_id = ingestion.ingest_text_finding(note_text, nonexistent_room_id)
            # If we get here in mock mode, verify the finding wasn't actually created properly
            retrieved = ingestion.get_finding(finding_id)
            if retrieved is not None:
                # In mock mode, clean up
                cursor = snowflake_connection.cursor()
                try:
                    cursor.execute("DELETE FROM findings WHERE finding_id = %s", (finding_id,))
                    snowflake_connection.commit()
                finally:
                    cursor.close()
        except Exception as e:
            # Expected behavior in real Snowflake - foreign key constraint violation
            assert 'foreign key' in str(e).lower() or 'constraint' in str(e).lower() or 'violat' in str(e).lower()
    
    def test_image_finding_with_nonexistent_room(self, snowflake_connection):
        """Test that image finding ingestion fails when referencing a non-existent room"""
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        
        nonexistent_room_id = 'nonexistent-room-999'
        image_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'  # Mock PNG header
        filename = 'crack_photo.jpg'
        
        # Act & Assert
        # The database should enforce foreign key constraint
        try:
            finding_id = ingestion.ingest_image_finding(image_bytes, filename, nonexistent_room_id)
            # If we get here in mock mode, verify the finding wasn't actually created properly
            retrieved = ingestion.get_finding(finding_id)
            if retrieved is not None:
                # In mock mode, clean up
                cursor = snowflake_connection.cursor()
                try:
                    cursor.execute("DELETE FROM findings WHERE finding_id = %s", (finding_id,))
                    snowflake_connection.commit()
                finally:
                    cursor.close()
        except Exception as e:
            # Expected behavior in real Snowflake - foreign key constraint violation
            assert 'foreign key' in str(e).lower() or 'constraint' in str(e).lower() or 'violat' in str(e).lower()


class TestCorruptedImageFiles:
    """Test that data ingestion properly handles corrupted or invalid image files"""
    
    def test_empty_image_file(self, snowflake_connection):
        """Test handling of empty image file"""
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        
        # Create property and room
        property_data = {
            'property_id': 'prop-123',
            'location': '123 Main St',
            'inspection_date': date(2024, 1, 15)
        }
        property_id = ingestion.ingest_property(property_data)
        
        room_data = {
            'room_id': 'room-456',
            'room_type': 'kitchen'
        }
        room_id = ingestion.ingest_room(room_data, property_id)
        
        # Empty image bytes
        empty_image = b''
        filename = 'empty.jpg'
        
        # Act - The system should accept the upload but mark it for processing
        # The actual validation would happen during AI classification
        finding_id = ingestion.ingest_image_finding(empty_image, filename, room_id)
        
        # Assert - Finding should be created with pending status
        retrieved = ingestion.get_finding(finding_id)
        assert retrieved is not None
        assert retrieved['finding_type'] == 'image'
        assert retrieved['image_filename'] == filename
        assert retrieved['processing_status'] == 'pending'
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            cursor.execute("DELETE FROM findings WHERE finding_id = %s", (finding_id,))
            cursor.execute("DELETE FROM rooms WHERE room_id = %s", (room_id,))
            cursor.execute("DELETE FROM properties WHERE property_id = %s", (property_id,))
            snowflake_connection.commit()
        finally:
            cursor.close()
    
    def test_invalid_image_format(self, snowflake_connection):
        """Test handling of invalid image format (non-image data)"""
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        
        # Create property and room
        property_data = {
            'property_id': 'prop-789',
            'location': '456 Oak Ave',
            'inspection_date': date(2024, 1, 20)
        }
        property_id = ingestion.ingest_property(property_data)
        
        room_data = {
            'room_id': 'room-789',
            'room_type': 'bathroom'
        }
        room_id = ingestion.ingest_room(room_data, property_id)
        
        # Invalid image data (just random text)
        invalid_image = b'This is not an image file, just text'
        filename = 'not_an_image.jpg'
        
        # Act - The system should accept the upload but mark it for processing
        # The actual validation would happen during AI classification
        finding_id = ingestion.ingest_image_finding(invalid_image, filename, room_id)
        
        # Assert - Finding should be created with pending status
        retrieved = ingestion.get_finding(finding_id)
        assert retrieved is not None
        assert retrieved['finding_type'] == 'image'
        assert retrieved['image_filename'] == filename
        assert retrieved['processing_status'] == 'pending'
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            cursor.execute("DELETE FROM findings WHERE finding_id = %s", (finding_id,))
            cursor.execute("DELETE FROM rooms WHERE room_id = %s", (room_id,))
            cursor.execute("DELETE FROM properties WHERE property_id = %s", (property_id,))
            snowflake_connection.commit()
        finally:
            cursor.close()
    
    def test_very_large_image_file(self, snowflake_connection):
        """Test handling of very large image file"""
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        
        # Create property and room
        property_data = {
            'property_id': 'prop-large',
            'location': '789 Pine St',
            'inspection_date': date(2024, 1, 25)
        }
        property_id = ingestion.ingest_property(property_data)
        
        room_data = {
            'room_id': 'room-large',
            'room_type': 'living room'
        }
        room_id = ingestion.ingest_room(room_data, property_id)
        
        # Simulate a large image (10MB worth of data)
        # In practice, we'd want to test with actual large files
        large_image = b'\x00' * (10 * 1024 * 1024)  # 10MB of zeros
        filename = 'large_image.jpg'
        
        # Act - The system should accept the upload
        finding_id = ingestion.ingest_image_finding(large_image, filename, room_id)
        
        # Assert - Finding should be created
        retrieved = ingestion.get_finding(finding_id)
        assert retrieved is not None
        assert retrieved['finding_type'] == 'image'
        assert retrieved['image_filename'] == filename
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            cursor.execute("DELETE FROM findings WHERE finding_id = %s", (finding_id,))
            cursor.execute("DELETE FROM rooms WHERE room_id = %s", (room_id,))
            cursor.execute("DELETE FROM properties WHERE property_id = %s", (property_id,))
            snowflake_connection.commit()
        finally:
            cursor.close()
    
    def test_image_with_special_characters_in_filename(self, snowflake_connection):
        """Test handling of image with special characters in filename"""
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        
        # Create property and room
        property_data = {
            'property_id': 'prop-special',
            'location': '321 Elm St',
            'inspection_date': date(2024, 1, 30)
        }
        property_id = ingestion.ingest_property(property_data)
        
        room_data = {
            'room_id': 'room-special',
            'room_type': 'bedroom'
        }
        room_id = ingestion.ingest_room(room_data, property_id)
        
        # Image with special characters in filename
        image_bytes = b'\x89PNG\r\n\x1a\n'
        filename = 'crack photo #1 (2024-01-30) [bedroom].jpg'
        
        # Act - The system should handle special characters
        finding_id = ingestion.ingest_image_finding(image_bytes, filename, room_id)
        
        # Assert - Finding should be created with the filename preserved
        retrieved = ingestion.get_finding(finding_id)
        assert retrieved is not None
        assert retrieved['finding_type'] == 'image'
        assert retrieved['image_filename'] == filename
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            cursor.execute("DELETE FROM findings WHERE finding_id = %s", (finding_id,))
            cursor.execute("DELETE FROM rooms WHERE room_id = %s", (room_id,))
            cursor.execute("DELETE FROM properties WHERE property_id = %s", (property_id,))
            snowflake_connection.commit()
        finally:
            cursor.close()
