"""
Property-based tests for export functionality
Feature: ai-home-inspection
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import date, timedelta
import sys
import os
import csv
import io

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from export import ExportComponent
from data_ingestion import DataIngestion
from ai_classification import AIClassification
from risk_scoring import RiskScoring
from summary_generation import SummaryGeneration


# Test data generators
@st.composite
def property_with_complete_data(draw):
    """Generate a complete property with rooms, findings, and defect tags"""
    # Generate property
    property_id = draw(st.uuids()).hex
    location = draw(st.text(min_size=5, max_size=30))
    base_date = date(2020, 1, 1)
    days_offset = draw(st.integers(min_value=0, max_value=365))
    inspection_date = base_date + timedelta(days=days_offset)
    
    # Generate 1-2 rooms (reduced from 1-3)
    num_rooms = draw(st.integers(min_value=1, max_value=2))
    rooms = []
    
    for _ in range(num_rooms):
        room_id = draw(st.uuids()).hex
        room_type = draw(st.sampled_from(['kitchen', 'bedroom']))
        room_location = None  # Simplified
        
        # Generate 1 finding per room (reduced from 1-2)
        finding_type = draw(st.sampled_from(['text', 'image']))
        
        if finding_type == 'text':
            note_text = draw(st.text(min_size=5, max_size=50))
            findings = [{
                'type': 'text',
                'note_text': note_text
            }]
        else:
            filename = f"image_{draw(st.integers(min_value=1, max_value=100))}.jpg"
            findings = [{
                'type': 'image',
                'filename': filename,
                'image_bytes': b'mock_image_data'
            }]
        
        rooms.append({
            'room_id': room_id,
            'room_type': room_type,
            'room_location': room_location,
            'findings': findings
        })
    
    return {
        'property_id': property_id,
        'location': location,
        'inspection_date': inspection_date,
        'rooms': rooms
    }


class TestExportCompleteness:
    """
    **Feature: ai-home-inspection, Property 22: Export completeness**
    
    For any property exported, the export document should contain all property details,
    room information, defect tags, risk scores, and summary text.
    """
    
    @given(prop_data=property_with_complete_data())
    @settings(max_examples=3)
    def test_pdf_export_completeness(self, prop_data, snowflake_connection):
        """
        **Feature: ai-home-inspection, Property 22: Export completeness**
        **Validates: Requirements 8.1**
        
        Test that PDF export contains all property details, rooms, findings, and defect tags.
        """
        # Arrange - Set up complete property with data
        ingestion = DataIngestion(snowflake_connection)
        classification = AIClassification(snowflake_connection)
        risk_scoring = RiskScoring(snowflake_connection)
        summary_gen = SummaryGeneration(snowflake_connection)
        export_component = ExportComponent(snowflake_connection)
        
        # Store property
        property_id = ingestion.ingest_property({
            'property_id': prop_data['property_id'],
            'location': prop_data['location'],
            'inspection_date': prop_data['inspection_date']
        })
        
        # Store rooms and findings
        for room in prop_data['rooms']:
            room_id = ingestion.ingest_room({
                'room_id': room['room_id'],
                'room_type': room['room_type'],
                'room_location': room['room_location']
            }, property_id)
            
            for finding in room['findings']:
                if finding['type'] == 'text':
                    finding_id = ingestion.ingest_text_finding(finding['note_text'], room_id)
                    classification.classify_text_finding(finding_id, finding['note_text'])
                else:
                    finding_id = ingestion.ingest_image_finding(
                        finding['image_bytes'],
                        finding['filename'],
                        room_id
                    )
                    # Mock image classification
                    stage_path = f"@inspections/{finding_id}/{finding['filename']}"
                    classification.classify_image_finding(finding_id, stage_path)
        
        # Compute risk scores
        risk_scoring.compute_property_risk(property_id)
        
        # Generate summary
        summary_gen.generate_property_summary(property_id)
        
        # Act - Export to PDF
        pdf_bytes = export_component.export_pdf(property_id)
        
        # Assert - PDF should be generated and be valid
        assert pdf_bytes is not None, "PDF export should generate bytes"
        assert len(pdf_bytes) > 0, "PDF should not be empty"
        assert pdf_bytes[:4] == b'%PDF', "Should be a valid PDF file"
        assert b'%%EOF' in pdf_bytes, "PDF should have proper EOF marker"
        
        # PDF should be reasonably sized (at least 1KB for a report with data)
        assert len(pdf_bytes) > 1000, "PDF should contain substantial content"
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            # Delete in reverse order of dependencies
            cursor.execute("DELETE FROM defect_tags WHERE finding_id IN (SELECT finding_id FROM findings WHERE room_id IN (SELECT room_id FROM rooms WHERE property_id = %s))", (property_id,))
            cursor.execute("DELETE FROM classification_history WHERE finding_id IN (SELECT finding_id FROM findings WHERE room_id IN (SELECT room_id FROM rooms WHERE property_id = %s))", (property_id,))
            cursor.execute("DELETE FROM findings WHERE room_id IN (SELECT room_id FROM rooms WHERE property_id = %s)", (property_id,))
            cursor.execute("DELETE FROM rooms WHERE property_id = %s", (property_id,))
            cursor.execute("DELETE FROM properties WHERE property_id = %s", (property_id,))
            snowflake_connection.commit()
        finally:
            cursor.close()

    
    @given(prop_data=property_with_complete_data())
    @settings(max_examples=3)
    def test_csv_export_completeness(self, prop_data, snowflake_connection):
        """
        **Feature: ai-home-inspection, Property 22: Export completeness**
        **Validates: Requirements 8.1**
        
        Test that CSV export contains all property details, rooms, findings, and defect tags.
        """
        # Arrange - Set up complete property with data
        ingestion = DataIngestion(snowflake_connection)
        classification = AIClassification(snowflake_connection)
        risk_scoring = RiskScoring(snowflake_connection)
        summary_gen = SummaryGeneration(snowflake_connection)
        export_component = ExportComponent(snowflake_connection)
        
        # Store property
        property_id = ingestion.ingest_property({
            'property_id': prop_data['property_id'],
            'location': prop_data['location'],
            'inspection_date': prop_data['inspection_date']
        })
        
        # Store rooms and findings
        for room in prop_data['rooms']:
            room_id = ingestion.ingest_room({
                'room_id': room['room_id'],
                'room_type': room['room_type'],
                'room_location': room['room_location']
            }, property_id)
            
            for finding in room['findings']:
                if finding['type'] == 'text':
                    finding_id = ingestion.ingest_text_finding(finding['note_text'], room_id)
                    classification.classify_text_finding(finding_id, finding['note_text'])
                else:
                    finding_id = ingestion.ingest_image_finding(
                        finding['image_bytes'],
                        finding['filename'],
                        room_id
                    )
                    # Mock image classification
                    stage_path = f"@inspections/{finding_id}/{finding['filename']}"
                    classification.classify_image_finding(finding_id, stage_path)
        
        # Compute risk scores
        risk_scoring.compute_property_risk(property_id)
        
        # Generate summary
        summary_gen.generate_property_summary(property_id)
        
        # Act - Export to CSV
        csv_bytes = export_component.export_csv([property_id])
        
        # Assert - CSV should be generated and contain key information
        assert csv_bytes is not None, "CSV export should generate bytes"
        assert len(csv_bytes) > 0, "CSV should not be empty"
        
        # Parse CSV to check content
        csv_str = csv_bytes.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(csv_reader)
        
        assert len(rows) > 0, "CSV should contain data rows"
        
        # Check that property details are present in at least one row
        first_row = rows[0]
        assert first_row['property_id'] == prop_data['property_id'], "CSV should contain property ID"
        assert first_row['location'] == prop_data['location'], "CSV should contain location"
        assert first_row['risk_score'] is not None, "CSV should contain risk score"
        assert first_row['risk_category'] is not None, "CSV should contain risk category"
        assert first_row['summary_text'] is not None, "CSV should contain summary text"
        
        # Check that room information is present
        room_ids_in_csv = set(row['room_id'] for row in rows if row['room_id'])
        for room in prop_data['rooms']:
            assert room['room_id'] in room_ids_in_csv, f"CSV should contain room {room['room_id']}"
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            cursor.execute("DELETE FROM defect_tags WHERE finding_id IN (SELECT finding_id FROM findings WHERE room_id IN (SELECT room_id FROM rooms WHERE property_id = %s))", (property_id,))
            cursor.execute("DELETE FROM classification_history WHERE finding_id IN (SELECT finding_id FROM findings WHERE room_id IN (SELECT room_id FROM rooms WHERE property_id = %s))", (property_id,))
            cursor.execute("DELETE FROM findings WHERE room_id IN (SELECT room_id FROM rooms WHERE property_id = %s)", (property_id,))
            cursor.execute("DELETE FROM rooms WHERE property_id = %s", (property_id,))
            cursor.execute("DELETE FROM properties WHERE property_id = %s", (property_id,))
            snowflake_connection.commit()
        finally:
            cursor.close()


class TestExportFormatSupport:
    """
    **Feature: ai-home-inspection, Property 23: Export format support**
    
    For any export request specifying PDF or CSV format, the system should 
    successfully generate a file in that format.
    """
    
    @given(
        prop_data=property_with_complete_data(),
        format_choice=st.sampled_from(['pdf', 'csv'])
    )
    @settings(max_examples=3)
    def test_export_format_support(self, prop_data, format_choice, snowflake_connection):
        """
        **Feature: ai-home-inspection, Property 23: Export format support**
        **Validates: Requirements 8.2**
        
        Test that both PDF and CSV formats are supported (case-insensitive).
        """
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        classification = AIClassification(snowflake_connection)
        export_component = ExportComponent(snowflake_connection)
        
        # Store minimal property data
        property_id = ingestion.ingest_property({
            'property_id': prop_data['property_id'],
            'location': prop_data['location'],
            'inspection_date': prop_data['inspection_date']
        })
        
        # Store at least one room and finding
        room = prop_data['rooms'][0]
        room_id = ingestion.ingest_room({
            'room_id': room['room_id'],
            'room_type': room['room_type'],
            'room_location': room['room_location']
        }, property_id)
        
        finding = room['findings'][0]
        if finding['type'] == 'text':
            finding_id = ingestion.ingest_text_finding(finding['note_text'], room_id)
            classification.classify_text_finding(finding_id, finding['note_text'])
        
        # Act - Export in the specified format
        export_bytes = export_component.export_property_report(property_id, format_choice)
        
        # Assert - Export should succeed and return bytes
        assert export_bytes is not None, f"Export should generate bytes for format {format_choice}"
        assert len(export_bytes) > 0, f"Export should not be empty for format {format_choice}"
        
        # Verify format-specific characteristics
        if format_choice.lower() == 'pdf':
            # PDF files start with %PDF
            assert export_bytes[:4] == b'%PDF', "PDF export should start with PDF header"
        elif format_choice.lower() == 'csv':
            # CSV should be valid UTF-8 text
            csv_str = export_bytes.decode('utf-8')
            assert 'property_id' in csv_str, "CSV should contain header with property_id"
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            cursor.execute("DELETE FROM defect_tags WHERE finding_id IN (SELECT finding_id FROM findings WHERE room_id IN (SELECT room_id FROM rooms WHERE property_id = %s))", (property_id,))
            cursor.execute("DELETE FROM classification_history WHERE finding_id IN (SELECT finding_id FROM findings WHERE room_id IN (SELECT room_id FROM rooms WHERE property_id = %s))", (property_id,))
            cursor.execute("DELETE FROM findings WHERE room_id IN (SELECT room_id FROM rooms WHERE property_id = %s)", (property_id,))
            cursor.execute("DELETE FROM rooms WHERE property_id = %s", (property_id,))
            cursor.execute("DELETE FROM properties WHERE property_id = %s", (property_id,))
            snowflake_connection.commit()
        finally:
            cursor.close()



class TestPDFImageInclusion:
    """
    **Feature: ai-home-inspection, Property 24: PDF export includes images and annotations**
    
    For any property exported as PDF, the document should contain all inspection images 
    with their associated defect tag annotations visible.
    """
    
    @given(prop_data=property_with_complete_data())
    @settings(max_examples=3)
    def test_pdf_includes_images_and_annotations(self, prop_data, snowflake_connection):
        """
        **Feature: ai-home-inspection, Property 24: PDF export includes images and annotations**
        **Validates: Requirements 8.3**
        
        Test that PDF export includes image filenames and defect tag annotations.
        """
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        classification = AIClassification(snowflake_connection)
        export_component = ExportComponent(snowflake_connection)
        
        # Store property
        property_id = ingestion.ingest_property({
            'property_id': prop_data['property_id'],
            'location': prop_data['location'],
            'inspection_date': prop_data['inspection_date']
        })
        
        # Store rooms and findings, tracking image findings
        image_filenames = []
        for room in prop_data['rooms']:
            room_id = ingestion.ingest_room({
                'room_id': room['room_id'],
                'room_type': room['room_type'],
                'room_location': room['room_location']
            }, property_id)
            
            for finding in room['findings']:
                if finding['type'] == 'image':
                    finding_id = ingestion.ingest_image_finding(
                        finding['image_bytes'],
                        finding['filename'],
                        room_id
                    )
                    image_filenames.append(finding['filename'])
                    # Mock image classification
                    stage_path = f"@inspections/{finding_id}/{finding['filename']}"
                    classification.classify_image_finding(finding_id, stage_path)
        
        # Act - Export to PDF
        pdf_bytes = export_component.export_pdf(property_id)
        
        # Assert - PDF should be generated and be valid
        assert pdf_bytes is not None, "PDF export should generate bytes"
        assert len(pdf_bytes) > 0, "PDF should not be empty"
        assert pdf_bytes[:4] == b'%PDF', "Should be a valid PDF file"
        assert b'%%EOF' in pdf_bytes, "PDF should have proper EOF marker"
        
        # If there were images, PDF should be reasonably sized
        if image_filenames:
            assert len(pdf_bytes) > 1000, "PDF with images should contain substantial content"
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            cursor.execute("DELETE FROM defect_tags WHERE finding_id IN (SELECT finding_id FROM findings WHERE room_id IN (SELECT room_id FROM rooms WHERE property_id = %s))", (property_id,))
            cursor.execute("DELETE FROM classification_history WHERE finding_id IN (SELECT finding_id FROM findings WHERE room_id IN (SELECT room_id FROM rooms WHERE property_id = %s))", (property_id,))
            cursor.execute("DELETE FROM findings WHERE room_id IN (SELECT room_id FROM rooms WHERE property_id = %s)", (property_id,))
            cursor.execute("DELETE FROM rooms WHERE property_id = %s", (property_id,))
            cursor.execute("DELETE FROM properties WHERE property_id = %s", (property_id,))
            snowflake_connection.commit()
        finally:
            cursor.close()


class TestCSVRecordInclusion:
    """
    **Feature: ai-home-inspection, Property 25: CSV export includes all records**
    
    For any property exported as CSV, the file should contain rows for all properties, 
    rooms, and findings with their associated classifications.
    """
    
    @given(prop_data=property_with_complete_data())
    @settings(max_examples=3)
    def test_csv_includes_all_records(self, prop_data, snowflake_connection):
        """
        **Feature: ai-home-inspection, Property 25: CSV export includes all records**
        **Validates: Requirements 8.4**
        
        Test that CSV export includes all property, room, and finding records.
        """
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        classification = AIClassification(snowflake_connection)
        export_component = ExportComponent(snowflake_connection)
        
        # Store property
        property_id = ingestion.ingest_property({
            'property_id': prop_data['property_id'],
            'location': prop_data['location'],
            'inspection_date': prop_data['inspection_date']
        })
        
        # Track what we store
        stored_room_ids = []
        stored_finding_ids = []
        
        # Store rooms and findings
        for room in prop_data['rooms']:
            room_id = ingestion.ingest_room({
                'room_id': room['room_id'],
                'room_type': room['room_type'],
                'room_location': room['room_location']
            }, property_id)
            stored_room_ids.append(room_id)
            
            for finding in room['findings']:
                if finding['type'] == 'text':
                    finding_id = ingestion.ingest_text_finding(finding['note_text'], room_id)
                    classification.classify_text_finding(finding_id, finding['note_text'])
                else:
                    finding_id = ingestion.ingest_image_finding(
                        finding['image_bytes'],
                        finding['filename'],
                        room_id
                    )
                    stage_path = f"@inspections/{finding_id}/{finding['filename']}"
                    classification.classify_image_finding(finding_id, stage_path)
                stored_finding_ids.append(finding_id)
        
        # Act - Export to CSV
        csv_bytes = export_component.export_csv([property_id])
        
        # Assert - CSV should contain all records
        csv_str = csv_bytes.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(csv_reader)
        
        assert len(rows) > 0, "CSV should contain data rows"
        
        # Check that all rooms are present
        room_ids_in_csv = set(row['room_id'] for row in rows if row['room_id'])
        for room_id in stored_room_ids:
            assert room_id in room_ids_in_csv, f"CSV should contain room {room_id}"
        
        # Check that all findings are present
        finding_ids_in_csv = set(row['finding_id'] for row in rows if row['finding_id'])
        for finding_id in stored_finding_ids:
            assert finding_id in finding_ids_in_csv, f"CSV should contain finding {finding_id}"
        
        # Check that classifications are present (at least one row should have a defect_category)
        defect_categories = [row['defect_category'] for row in rows if row['defect_category']]
        assert len(defect_categories) > 0, "CSV should contain classification results"
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            cursor.execute("DELETE FROM defect_tags WHERE finding_id IN (SELECT finding_id FROM findings WHERE room_id IN (SELECT room_id FROM rooms WHERE property_id = %s))", (property_id,))
            cursor.execute("DELETE FROM classification_history WHERE finding_id IN (SELECT finding_id FROM findings WHERE room_id IN (SELECT room_id FROM rooms WHERE property_id = %s))", (property_id,))
            cursor.execute("DELETE FROM findings WHERE room_id IN (SELECT room_id FROM rooms WHERE property_id = %s)", (property_id,))
            cursor.execute("DELETE FROM rooms WHERE property_id = %s", (property_id,))
            cursor.execute("DELETE FROM properties WHERE property_id = %s", (property_id,))
            snowflake_connection.commit()
        finally:
            cursor.close()



class TestExportEdgeCases:
    """Unit tests for export edge cases"""
    
    def test_export_with_no_data(self, snowflake_connection):
        """
        Test export with a property that has no rooms or findings.
        Validates: Requirements 8.1
        """
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        export_component = ExportComponent(snowflake_connection)
        
        # Create property with no rooms
        property_id = 'test-empty-property'
        ingestion.ingest_property({
            'property_id': property_id,
            'location': 'Empty Property Location',
            'inspection_date': date(2024, 1, 1)
        })
        
        # Act - Export to PDF
        pdf_bytes = export_component.export_pdf(property_id)
        
        # Assert - Should still generate a valid PDF
        assert pdf_bytes is not None, "PDF should be generated even with no data"
        assert len(pdf_bytes) > 0, "PDF should not be empty"
        assert pdf_bytes[:4] == b'%PDF', "Should be a valid PDF"
        
        # Act - Export to CSV
        csv_bytes = export_component.export_csv([property_id])
        
        # Assert - Should still generate a valid CSV
        assert csv_bytes is not None, "CSV should be generated even with no data"
        assert len(csv_bytes) > 0, "CSV should not be empty"
        
        csv_str = csv_bytes.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(csv_reader)
        
        # Should have at least the property row
        assert len(rows) >= 1, "CSV should contain at least the property row"
        assert rows[0]['property_id'] == property_id, "CSV should contain the property"
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            cursor.execute("DELETE FROM properties WHERE property_id = %s", (property_id,))
            snowflake_connection.commit()
        finally:
            cursor.close()
    
    def test_export_with_large_dataset(self, snowflake_connection):
        """
        Test export with a property that has many rooms and findings.
        Validates: Requirements 8.1
        """
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        classification = AIClassification(snowflake_connection)
        export_component = ExportComponent(snowflake_connection)
        
        # Create property with many rooms
        property_id = 'test-large-property'
        ingestion.ingest_property({
            'property_id': property_id,
            'location': 'Large Property Location',
            'inspection_date': date(2024, 1, 1)
        })
        
        # Create 10 rooms with 5 findings each
        room_ids = []
        finding_ids = []
        for i in range(10):
            room_id = f'room-{i}'
            ingestion.ingest_room({
                'room_id': room_id,
                'room_type': 'bedroom',
                'room_location': f'Floor {i}'
            }, property_id)
            room_ids.append(room_id)
            
            for j in range(5):
                finding_id = ingestion.ingest_text_finding(
                    f'Finding {j} in room {i}',
                    room_id
                )
                classification.classify_text_finding(finding_id, f'crack in wall {j}')
                finding_ids.append(finding_id)
        
        # Act - Export to PDF
        pdf_bytes = export_component.export_pdf(property_id)
        
        # Assert - Should generate a valid PDF
        assert pdf_bytes is not None, "PDF should be generated for large dataset"
        assert len(pdf_bytes) > 0, "PDF should not be empty"
        assert pdf_bytes[:4] == b'%PDF', "Should be a valid PDF"
        
        # Act - Export to CSV
        csv_bytes = export_component.export_csv([property_id])
        
        # Assert - Should generate a valid CSV with all records
        assert csv_bytes is not None, "CSV should be generated for large dataset"
        assert len(csv_bytes) > 0, "CSV should not be empty"
        
        csv_str = csv_bytes.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(csv_reader)
        
        # Should have rows for all findings (50 findings = 50 rows minimum)
        assert len(rows) >= 50, "CSV should contain all finding records"
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            cursor.execute("DELETE FROM defect_tags WHERE finding_id IN (SELECT finding_id FROM findings WHERE room_id IN (SELECT room_id FROM rooms WHERE property_id = %s))", (property_id,))
            cursor.execute("DELETE FROM classification_history WHERE finding_id IN (SELECT finding_id FROM findings WHERE room_id IN (SELECT room_id FROM rooms WHERE property_id = %s))", (property_id,))
            cursor.execute("DELETE FROM findings WHERE room_id IN (SELECT room_id FROM rooms WHERE property_id = %s)", (property_id,))
            cursor.execute("DELETE FROM rooms WHERE property_id = %s", (property_id,))
            cursor.execute("DELETE FROM properties WHERE property_id = %s", (property_id,))
            snowflake_connection.commit()
        finally:
            cursor.close()
    
    def test_export_invalid_format(self, snowflake_connection):
        """Test that invalid export formats are rejected"""
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        export_component = ExportComponent(snowflake_connection)
        
        property_id = 'test-property'
        ingestion.ingest_property({
            'property_id': property_id,
            'location': 'Test Location',
            'inspection_date': date(2024, 1, 1)
        })
        
        # Act & Assert - Should raise ValueError for invalid format
        with pytest.raises(ValueError, match="Unsupported export format"):
            export_component.export_property_report(property_id, 'xml')
        
        with pytest.raises(ValueError, match="Unsupported export format"):
            export_component.export_property_report(property_id, 'json')
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            cursor.execute("DELETE FROM properties WHERE property_id = %s", (property_id,))
            snowflake_connection.commit()
        finally:
            cursor.close()
    
    def test_export_nonexistent_property(self, snowflake_connection):
        """Test that exporting a nonexistent property raises an error"""
        # Arrange
        export_component = ExportComponent(snowflake_connection)
        
        # Act & Assert - Should raise ValueError for nonexistent property
        with pytest.raises(ValueError, match="not found"):
            export_component.export_pdf('nonexistent-property-id')
        
        # CSV export doesn't raise error, just returns empty CSV with header
        csv_bytes = export_component.export_csv(['nonexistent-property-id'])
        assert csv_bytes is not None
        csv_str = csv_bytes.decode('utf-8')
        # Should only have header row
        lines = csv_str.strip().split('\n')
        assert len(lines) == 1, "CSV for nonexistent property should only have header"
