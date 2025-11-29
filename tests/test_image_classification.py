"""
Property-based tests for AI image classification
Feature: ai-home-inspection
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import date, timedelta
import sys
import os
import uuid

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_ingestion import DataIngestion
from ai_classification import AIClassification


# Test data generators
@st.composite
def property_data(draw):
    """Generate valid property data for testing"""
    property_id = draw(st.uuids()).hex
    location = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pd')),
        min_size=1,
        max_size=100
    ))
    base_date = date(2020, 1, 1)
    days_offset = draw(st.integers(min_value=0, max_value=2000))
    inspection_date = base_date + timedelta(days=days_offset)
    
    return {
        'property_id': property_id,
        'location': location,
        'inspection_date': inspection_date
    }


@st.composite
def room_data(draw):
    """Generate valid room data for testing"""
    room_id = draw(st.uuids()).hex
    room_type = draw(st.sampled_from([
        'kitchen', 'bedroom', 'bathroom', 'living room', 
        'dining room', 'basement', 'attic', 'garage'
    ]))
    room_location = draw(st.one_of(
        st.none(),
        st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pd')),
            min_size=1,
            max_size=50
        )
    ))
    
    return {
        'room_id': room_id,
        'room_type': room_type,
        'room_location': room_location
    }


@st.composite
def image_filename(draw):
    """Generate image filenames that may contain defect-related keywords"""
    # Base filename components
    prefixes = ['inspection', 'photo', 'image', 'finding', 'defect', 'issue']
    defect_hints = [
        'crack', 'water_leak', 'mold', 'wiring', 'electrical',
        'wall', 'ceiling', 'floor', 'damage', 'normal', 'clean'
    ]
    extensions = ['jpg', 'jpeg', 'png', 'bmp']
    
    prefix = draw(st.sampled_from(prefixes))
    hint = draw(st.sampled_from(defect_hints))
    number = draw(st.integers(min_value=1, max_value=9999))
    ext = draw(st.sampled_from(extensions))
    
    # Sometimes include the hint, sometimes not
    if draw(st.booleans()):
        filename = f"{prefix}_{hint}_{number}.{ext}"
    else:
        filename = f"{prefix}_{number}.{ext}"
    
    return filename


class TestImageClassificationCategories:
    """
    **Feature: ai-home-inspection, Property 6: Image classification produces valid categories**
    
    For any image finding that is classified, all resulting defect tags must be from the set:
    "crack", "water leak", "mold", "electrical wiring", or "none".
    """
    
    @given(
        prop_data=property_data(),
        rm_data=room_data(),
        filename=image_filename()
    )
    @settings(max_examples=100)
    def test_image_classification_produces_valid_categories(
        self, 
        prop_data, 
        rm_data, 
        filename,
        snowflake_connection
    ):
        """
        **Feature: ai-home-inspection, Property 6: Image classification produces valid categories**
        **Validates: Requirements 3.1, 3.2**
        
        Test that image classification always returns valid defect categories.
        """
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        classifier = AIClassification(snowflake_connection)
        
        # Create property and room
        property_id = ingestion.ingest_property(prop_data)
        room_id = ingestion.ingest_room(rm_data, property_id)
        
        # Create image finding with mock image data
        image_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100  # Mock PNG header
        finding_id = ingestion.ingest_image_finding(image_data, filename, room_id)
        
        # Get the image stage path
        finding = ingestion.get_finding(finding_id)
        image_stage_path = finding['image_stage_path']
        
        # Act - Classify the image finding
        defect_tags = classifier.classify_image_finding(finding_id, image_stage_path)
        
        # Assert - All returned tags must be valid categories
        assert defect_tags is not None, "Classification should return tags"
        assert len(defect_tags) > 0, "Classification should return at least one tag"
        
        for tag in defect_tags:
            assert tag in classifier.IMAGE_DEFECT_CATEGORIES, \
                f"Defect tag '{tag}' must be one of the valid image categories: {classifier.IMAGE_DEFECT_CATEGORIES}"
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            cursor.execute("DELETE FROM defect_tags WHERE finding_id = %s", (finding_id,))
            cursor.execute("DELETE FROM classification_history WHERE finding_id = %s", (finding_id,))
            cursor.execute("DELETE FROM findings WHERE finding_id = %s", (finding_id,))
            cursor.execute("DELETE FROM rooms WHERE room_id = %s", (room_id,))
            cursor.execute("DELETE FROM properties WHERE property_id = %s", (property_id,))
            snowflake_connection.commit()
        finally:
            cursor.close()


class TestMultipleTagPreservation:
    """
    **Feature: ai-home-inspection, Property 7: Multiple tags are preserved**
    
    For any image finding with multiple detected defects, all detected tags 
    should be stored and retrievable from the database.
    """
    
    @given(
        prop_data=property_data(),
        rm_data=room_data(),
        filename=image_filename()
    )
    @settings(max_examples=100)
    def test_multiple_tags_are_preserved(
        self,
        prop_data,
        rm_data,
        filename,
        snowflake_connection
    ):
        """
        **Feature: ai-home-inspection, Property 7: Multiple tags are preserved**
        **Validates: Requirements 3.4**
        
        Test that when an image has multiple defect tags, all are stored and retrievable.
        """
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        classifier = AIClassification(snowflake_connection)
        
        # Create property and room
        property_id = ingestion.ingest_property(prop_data)
        room_id = ingestion.ingest_room(rm_data, property_id)
        
        # Create image finding
        image_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        finding_id = ingestion.ingest_image_finding(image_data, filename, room_id)
        
        # Get the image stage path
        finding = ingestion.get_finding(finding_id)
        image_stage_path = finding['image_stage_path']
        
        # Act - Classify the image finding
        classified_tags = classifier.classify_image_finding(finding_id, image_stage_path)
        
        # Act - Retrieve stored tags
        stored_tags = classifier.get_defect_tags(finding_id)
        
        # Assert - All classified tags should be stored
        assert stored_tags is not None, "Should be able to retrieve stored tags"
        assert len(stored_tags) == len(classified_tags), \
            f"Number of stored tags ({len(stored_tags)}) should match classified tags ({len(classified_tags)})"
        
        # Assert - All classified tags should be in stored tags
        stored_categories = [tag['defect_category'] for tag in stored_tags]
        for classified_tag in classified_tags:
            assert classified_tag in stored_categories, \
                f"Classified tag '{classified_tag}' should be in stored tags"
        
        # Assert - If multiple tags were classified, verify they're all present
        if len(classified_tags) > 1:
            # Multiple tags should all be preserved
            assert len(stored_tags) > 1, \
                "Multiple classified tags should result in multiple stored tags"
            
            # Each tag should be unique
            assert len(set(stored_categories)) == len(stored_categories), \
                "Stored tags should not contain duplicates"
        
        # Assert - Each stored tag should have required metadata
        for tag in stored_tags:
            assert tag['finding_id'] == finding_id, \
                "Tag should be associated with correct finding"
            assert tag['defect_category'] in classifier.IMAGE_DEFECT_CATEGORIES, \
                "Stored category should be valid"
            assert tag['confidence_score'] is not None, \
                "Confidence score should be recorded"
            assert tag['severity_weight'] is not None, \
                "Severity weight should be recorded"
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            cursor.execute("DELETE FROM defect_tags WHERE finding_id = %s", (finding_id,))
            cursor.execute("DELETE FROM classification_history WHERE finding_id = %s", (finding_id,))
            cursor.execute("DELETE FROM findings WHERE finding_id = %s", (finding_id,))
            cursor.execute("DELETE FROM rooms WHERE room_id = %s", (room_id,))
            cursor.execute("DELETE FROM properties WHERE property_id = %s", (property_id,))
            snowflake_connection.commit()
        finally:
            cursor.close()
