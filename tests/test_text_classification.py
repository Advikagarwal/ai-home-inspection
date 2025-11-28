"""
Property-based tests for AI text classification
Feature: ai-home-inspection
"""

import pytest
from hypothesis import given, strategies as st, settings
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
def text_finding_note(draw):
    """Generate text notes that may contain defect keywords"""
    # Generate notes with various defect-related content
    defect_templates = [
        'Found {defect} in the {location}',
        'There is {defect} visible on the {surface}',
        'Noticed {defect} near the {location}',
        'Significant {defect} detected',
        '{defect} present in this area',
        'No issues found',
        'Everything looks good',
        'Area is clean and well-maintained'
    ]
    
    defects = [
        'a crack', 'cracks', 'a large crack',
        'damp wall', 'dampness', 'moisture on the wall',
        'exposed wiring', 'exposed wires', 'live wires',
        'mold', 'mold growth', 'mildew',
        'water leak', 'leaking water', 'water damage',
        'nothing unusual'
    ]
    
    locations = ['ceiling', 'floor', 'wall', 'corner', 'window', 'door']
    surfaces = ['wall', 'ceiling', 'floor', 'surface']
    
    template = draw(st.sampled_from(defect_templates))
    defect = draw(st.sampled_from(defects))
    location = draw(st.sampled_from(locations))
    surface = draw(st.sampled_from(surfaces))
    
    note = template.format(defect=defect, location=location, surface=surface)
    
    # Sometimes add additional context
    if draw(st.booleans()):
        additional = draw(st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')),
            min_size=0,
            max_size=100
        ))
        note = note + '. ' + additional
    
    return note


class TestTextClassificationCategories:
    """
    **Feature: ai-home-inspection, Property 4: Text classification produces valid categories**
    
    For any text finding that is classified, the resulting defect tag must be one of:
    "damp wall", "exposed wiring", "crack", "mold", "water leak", or "none".
    """
    
    @given(
        prop_data=property_data(),
        rm_data=room_data(),
        note_text=text_finding_note()
    )
    @settings(max_examples=100)
    def test_text_classification_produces_valid_categories(
        self, 
        prop_data, 
        rm_data, 
        note_text, 
        snowflake_connection
    ):
        """
        **Feature: ai-home-inspection, Property 4: Text classification produces valid categories**
        **Validates: Requirements 2.1, 2.2**
        
        Test that text classification always returns a valid defect category.
        """
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        classifier = AIClassification(snowflake_connection)
        
        # Create property and room
        property_id = ingestion.ingest_property(prop_data)
        room_id = ingestion.ingest_room(rm_data, property_id)
        
        # Create text finding
        finding_id = ingestion.ingest_text_finding(note_text, room_id)
        
        # Act - Classify the text finding
        defect_tags = classifier.classify_text_finding(finding_id, note_text)
        
        # Assert - All returned tags must be valid categories
        assert defect_tags is not None, "Classification should return tags"
        assert len(defect_tags) > 0, "Classification should return at least one tag"
        
        for tag in defect_tags:
            assert tag in classifier.TEXT_DEFECT_CATEGORIES, \
                f"Defect tag '{tag}' must be one of the valid categories: {classifier.TEXT_DEFECT_CATEGORIES}"
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            # Delete in reverse order of dependencies
            cursor.execute("DELETE FROM defect_tags WHERE finding_id = %s", (finding_id,))
            cursor.execute("DELETE FROM classification_history WHERE finding_id = %s", (finding_id,))
            cursor.execute("DELETE FROM findings WHERE finding_id = %s", (finding_id,))
            cursor.execute("DELETE FROM rooms WHERE room_id = %s", (room_id,))
            cursor.execute("DELETE FROM properties WHERE property_id = %s", (property_id,))
            snowflake_connection.commit()
        finally:
            cursor.close()


class TestClassificationPersistence:
    """
    **Feature: ai-home-inspection, Property 5: Classification results are persisted**
    
    For any finding that undergoes classification, querying the defect_tags table 
    should return the classification result associated with that finding.
    """
    
    @given(
        prop_data=property_data(),
        rm_data=room_data(),
        note_text=text_finding_note()
    )
    @settings(max_examples=100)
    def test_classification_results_are_persisted(
        self,
        prop_data,
        rm_data,
        note_text,
        snowflake_connection
    ):
        """
        **Feature: ai-home-inspection, Property 5: Classification results are persisted**
        **Validates: Requirements 2.3, 3.3**
        
        Test that classification results are stored and retrievable from the database.
        """
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        classifier = AIClassification(snowflake_connection)
        
        # Create property and room
        property_id = ingestion.ingest_property(prop_data)
        room_id = ingestion.ingest_room(rm_data, property_id)
        
        # Create text finding
        finding_id = ingestion.ingest_text_finding(note_text, room_id)
        
        # Act - Classify the text finding
        defect_tags = classifier.classify_text_finding(finding_id, note_text)
        
        # Act - Retrieve the stored classification
        stored_tags = classifier.get_defect_tags(finding_id)
        
        # Assert - Classification should be persisted
        assert stored_tags is not None, "Should be able to retrieve stored tags"
        assert len(stored_tags) > 0, "At least one tag should be stored"
        
        # Assert - Stored tags should match classified tags
        stored_categories = [tag['defect_category'] for tag in stored_tags]
        for classified_tag in defect_tags:
            assert classified_tag in stored_categories, \
                f"Classified tag '{classified_tag}' should be in stored tags"
        
        # Assert - Each stored tag should have required metadata
        for tag in stored_tags:
            assert tag['finding_id'] == finding_id, \
                "Tag should be associated with correct finding"
            assert tag['defect_category'] in classifier.TEXT_DEFECT_CATEGORIES, \
                "Stored category should be valid"
            assert tag['confidence_score'] is not None, \
                "Confidence score should be recorded"
            assert tag['severity_weight'] is not None, \
                "Severity weight should be recorded"
            assert tag['severity_weight'] >= 0, \
                "Severity weight should be non-negative"
        
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


class TestClassificationFailureIsolation:
    """
    **Feature: ai-home-inspection, Property 26: Classification failure isolation**
    
    For any batch of findings being classified, if one classification fails, 
    all other findings in the batch should still be processed successfully.
    """
    
    @given(
        prop_data=property_data(),
        rm_data=room_data(),
        note_texts=st.lists(text_finding_note(), min_size=3, max_size=10)
    )
    @settings(max_examples=100)
    def test_classification_failure_isolation(
        self,
        prop_data,
        rm_data,
        note_texts,
        snowflake_connection
    ):
        """
        **Feature: ai-home-inspection, Property 26: Classification failure isolation**
        **Validates: Requirements 9.1**
        
        Test that batch classification continues processing even when individual items fail.
        """
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        classifier = AIClassification(snowflake_connection)
        
        # Create property and room
        property_id = ingestion.ingest_property(prop_data)
        room_id = ingestion.ingest_room(rm_data, property_id)
        
        # Create multiple text findings
        finding_ids = []
        for note_text in note_texts:
            finding_id = ingestion.ingest_text_finding(note_text, room_id)
            finding_ids.append(finding_id)
        
        # Insert one invalid finding ID to simulate a failure case
        invalid_finding_id = str(uuid.uuid4())
        finding_ids_with_invalid = finding_ids + [invalid_finding_id]
        
        # Act - Batch classify all findings (including the invalid one)
        results = classifier.batch_classify_findings(finding_ids_with_invalid)
        
        # Assert - Valid findings should be processed despite the invalid one
        # At least some of the valid findings should have been classified
        assert len(results) > 0, \
            "Some findings should be classified even if one fails"
        
        # Assert - All successfully classified findings should have valid tags
        for finding_id, tags in results.items():
            assert finding_id in finding_ids, \
                "Only valid finding IDs should be in results"
            assert len(tags) > 0, \
                "Classified findings should have at least one tag"
            for tag in tags:
                assert tag in classifier.TEXT_DEFECT_CATEGORIES, \
                    f"Tag '{tag}' should be a valid category"
        
        # Assert - The invalid finding should not be in results
        assert invalid_finding_id not in results, \
            "Invalid finding should not be in results"
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            for finding_id in finding_ids:
                cursor.execute("DELETE FROM defect_tags WHERE finding_id = %s", (finding_id,))
                cursor.execute("DELETE FROM classification_history WHERE finding_id = %s", (finding_id,))
                cursor.execute("DELETE FROM findings WHERE finding_id = %s", (finding_id,))
            cursor.execute("DELETE FROM rooms WHERE room_id = %s", (room_id,))
            cursor.execute("DELETE FROM properties WHERE property_id = %s", (property_id,))
            snowflake_connection.commit()
        finally:
            cursor.close()
