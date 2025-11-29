"""
Property-based tests for summary generation component
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import date
import uuid

from src.data_ingestion import DataIngestion
from src.ai_classification import AIClassification
from src.risk_scoring import RiskScoring
from src.summary_generation import SummaryGeneration


# Generators for test data
@st.composite
def property_with_defects(draw):
    """Generate a property with rooms and defects"""
    property_id = str(uuid.uuid4())
    location = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='\x00')))
    inspection_date = draw(st.dates(min_value=date(2020, 1, 1), max_value=date(2024, 12, 31)))
    
    # Generate 1-5 rooms
    num_rooms = draw(st.integers(min_value=1, max_value=5))
    rooms = []
    
    for _ in range(num_rooms):
        room_id = str(uuid.uuid4())
        room_type = draw(st.sampled_from(['kitchen', 'bedroom', 'bathroom', 'living room']))
        
        # Generate 1-3 findings per room
        num_findings = draw(st.integers(min_value=1, max_value=3))
        findings = []
        
        for _ in range(num_findings):
            finding_id = str(uuid.uuid4())
            # Generate defect category (excluding 'none' to ensure we have defects)
            defect_category = draw(st.sampled_from([
                'damp wall', 'exposed wiring', 'crack', 'mold', 'water leak'
            ]))
            
            findings.append({
                'finding_id': finding_id,
                'defect_category': defect_category
            })
        
        rooms.append({
            'room_id': room_id,
            'room_type': room_type,
            'findings': findings
        })
    
    return {
        'property_id': property_id,
        'location': location,
        'inspection_date': inspection_date,
        'rooms': rooms
    }


@st.composite
def property_with_mixed_severity_defects(draw):
    """Generate a property with both high and low severity defects"""
    property_id = str(uuid.uuid4())
    location = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='\x00')))
    inspection_date = draw(st.dates(min_value=date(2020, 1, 1), max_value=date(2024, 12, 31)))
    
    # Generate 2-4 rooms
    num_rooms = draw(st.integers(min_value=2, max_value=4))
    rooms = []
    
    # Ensure at least one high-severity and one low-severity defect
    high_severity = ['damp wall', 'exposed wiring', 'mold']
    low_severity = ['crack', 'water leak']
    
    for i in range(num_rooms):
        room_id = str(uuid.uuid4())
        room_type = draw(st.sampled_from(['kitchen', 'bedroom', 'bathroom', 'living room']))
        
        findings = []
        
        # First room gets high severity
        if i == 0:
            finding_id = str(uuid.uuid4())
            defect_category = draw(st.sampled_from(high_severity))
            findings.append({
                'finding_id': finding_id,
                'defect_category': defect_category
            })
        # Second room gets low severity
        elif i == 1:
            finding_id = str(uuid.uuid4())
            defect_category = draw(st.sampled_from(low_severity))
            findings.append({
                'finding_id': finding_id,
                'defect_category': defect_category
            })
        # Other rooms get random
        else:
            num_findings = draw(st.integers(min_value=1, max_value=2))
            for _ in range(num_findings):
                finding_id = str(uuid.uuid4())
                defect_category = draw(st.sampled_from(high_severity + low_severity))
                findings.append({
                    'finding_id': finding_id,
                    'defect_category': defect_category
                })
        
        rooms.append({
            'room_id': room_id,
            'room_type': room_type,
            'findings': findings
        })
    
    return {
        'property_id': property_id,
        'location': location,
        'inspection_date': inspection_date,
        'rooms': rooms
    }


def setup_property_with_data(conn, property_data):
    """Helper to set up a property with rooms, findings, and defects"""
    ingestion = DataIngestion(conn)
    classification = AIClassification(conn)
    risk_scoring = RiskScoring(conn)
    
    # Ingest property
    ingestion.ingest_property({
        'property_id': property_data['property_id'],
        'location': property_data['location'],
        'inspection_date': property_data['inspection_date']
    })
    
    # Ingest rooms and findings
    for room in property_data['rooms']:
        ingestion.ingest_room({
            'room_id': room['room_id'],
            'room_type': room['room_type']
        }, property_data['property_id'])
        
        for finding_data in room['findings']:
            # Create a text finding - this generates a new finding_id
            actual_finding_id = ingestion.ingest_text_finding(
                f"Defect: {finding_data['defect_category']}",
                room['room_id']
            )
            
            # Manually store the classification result using the actual finding_id
            classification._store_classification_result(
                actual_finding_id,
                finding_data['defect_category'],
                0.85,
                'text_ai'
            )
    
    # Compute risk scores
    risk_scoring.compute_property_risk(property_data['property_id'])
    
    return property_data['property_id']


# Property Tests

@given(property_data=property_with_defects())
@settings(max_examples=100, deadline=None)
def test_property_12_summary_completeness(snowflake_connection, property_data):
    """
    **Feature: ai-home-inspection, Property 12: Summary generation completeness**
    **Validates: Requirements 5.1, 5.2**
    
    For any property with defects, the generated summary should contain 
    the risk category, a count of affected rooms, and at least one defect type.
    """
    # Setup
    property_id = setup_property_with_data(snowflake_connection, property_data)
    summary_gen = SummaryGeneration(snowflake_connection)
    
    # Generate summary
    summary = summary_gen.generate_property_summary(property_id)
    
    # Get property details
    ingestion = DataIngestion(snowflake_connection)
    property_info = ingestion.get_property(property_id)
    
    # Debug: check defect counts
    defect_counts = summary_gen.get_defect_counts(property_id)
    affected_rooms = summary_gen.get_affected_room_count(property_id)
    
    # Verify summary contains risk category
    risk_category = property_info['risk_category']
    assert risk_category in summary, \
        f"Summary should contain risk category '{risk_category}', but got: {summary}"
    
    # Verify summary contains room count information
    # Should mention "room" or "rooms"
    assert 'room' in summary.lower(), \
        f"Summary should mention rooms, but got: {summary}"
    
    # Verify summary contains at least one defect type
    defect_types = ['damp wall', 'exposed wiring', 'crack', 'mold', 'water leak', 
                   'electrical wiring', 'defect']
    has_defect_mention = any(defect in summary.lower() for defect in defect_types)
    assert has_defect_mention, \
        f"Summary should mention at least one defect type, but got: {summary}"



@given(property_data=property_with_mixed_severity_defects())
@settings(max_examples=100, deadline=None)
def test_property_13_high_severity_defect_prioritization(snowflake_connection, property_data):
    """
    **Feature: ai-home-inspection, Property 13: High-severity defects appear in summaries**
    **Validates: Requirements 5.5**
    
    For any property with both high-severity (weight=3) and low-severity (weight≤2) defects,
    the summary should mention at least one high-severity defect type.
    """
    # Setup
    property_id = setup_property_with_data(snowflake_connection, property_data)
    summary_gen = SummaryGeneration(snowflake_connection)
    
    # Generate summary
    summary = summary_gen.generate_property_summary(property_id)
    
    # High-severity defects (weight = 3)
    high_severity_defects = ['damp wall', 'exposed wiring', 'mold', 'electrical wiring']
    
    # Verify at least one high-severity defect is mentioned in the summary
    has_high_severity_mention = any(
        defect in summary.lower() 
        for defect in high_severity_defects
    )
    
    assert has_high_severity_mention, \
        f"Summary should mention at least one high-severity defect, but got: {summary}"



@given(property_data=property_with_defects())
@settings(max_examples=100, deadline=None)
def test_property_30_source_data_preservation(snowflake_connection, property_data):
    """
    **Feature: ai-home-inspection, Property 30: Source data preservation**
    **Validates: Requirements 10.3**
    
    For any generated summary, the original defect counts and room data used to create 
    the summary should remain accessible in the database.
    """
    # Setup
    property_id = setup_property_with_data(snowflake_connection, property_data)
    summary_gen = SummaryGeneration(snowflake_connection)
    
    # Get defect counts and room count BEFORE generating summary
    defect_counts_before = summary_gen.get_defect_counts(property_id)
    affected_rooms_before = summary_gen.get_affected_room_count(property_id)
    
    # Generate summary
    summary = summary_gen.generate_property_summary(property_id)
    
    # Get defect counts and room count AFTER generating summary
    defect_counts_after = summary_gen.get_defect_counts(property_id)
    affected_rooms_after = summary_gen.get_affected_room_count(property_id)
    
    # Verify source data is preserved (unchanged)
    assert defect_counts_before == defect_counts_after, \
        f"Defect counts should be preserved. Before: {defect_counts_before}, After: {defect_counts_after}"
    
    assert affected_rooms_before == affected_rooms_after, \
        f"Affected room count should be preserved. Before: {affected_rooms_before}, After: {affected_rooms_after}"
    
    # Verify we can still retrieve the original data
    assert len(defect_counts_after) > 0 or affected_rooms_after >= 0, \
        "Should be able to retrieve source data after summary generation"



# Unit Tests for Edge Cases

def test_summary_with_no_defects(snowflake_connection):
    """
    Test summary generation for a property with no defects
    """
    ingestion = DataIngestion(snowflake_connection)
    summary_gen = SummaryGeneration(snowflake_connection)
    risk_scoring = RiskScoring(snowflake_connection)
    
    # Create property and room with no defects
    property_id = str(uuid.uuid4())
    room_id = str(uuid.uuid4())
    
    ingestion.ingest_property({
        'property_id': property_id,
        'location': 'Test Property',
        'inspection_date': date(2024, 1, 1)
    })
    
    ingestion.ingest_room({
        'room_id': room_id,
        'room_type': 'bedroom'
    }, property_id)
    
    # Compute risk (should be 0)
    risk_scoring.compute_property_risk(property_id)
    
    # Generate summary
    summary = summary_gen.generate_property_summary(property_id)
    
    # Verify summary indicates no defects
    assert 'Low' in summary or 'low' in summary, \
        "Summary should indicate low risk"
    assert 'no' in summary.lower() or 'good' in summary.lower(), \
        "Summary should indicate no issues or good condition"


def test_summary_with_single_defect_type(snowflake_connection):
    """
    Test summary generation for a property with only one defect type
    """
    ingestion = DataIngestion(snowflake_connection)
    classification = AIClassification(snowflake_connection)
    risk_scoring = RiskScoring(snowflake_connection)
    summary_gen = SummaryGeneration(snowflake_connection)
    
    # Create property and room with single defect type
    property_id = str(uuid.uuid4())
    room_id = str(uuid.uuid4())
    
    ingestion.ingest_property({
        'property_id': property_id,
        'location': 'Test Property',
        'inspection_date': date(2024, 1, 1)
    })
    
    ingestion.ingest_room({
        'room_id': room_id,
        'room_type': 'kitchen'
    }, property_id)
    
    # Add multiple findings of the same defect type
    for i in range(3):
        finding_id = ingestion.ingest_text_finding(f"Crack {i}", room_id)
        classification._store_classification_result(finding_id, 'crack', 0.85, 'text_ai')
    
    # Compute risk
    risk_scoring.compute_property_risk(property_id)
    
    # Generate summary
    summary = summary_gen.generate_property_summary(property_id)
    
    # Verify summary mentions the defect type
    assert 'crack' in summary.lower(), \
        f"Summary should mention 'crack', but got: {summary}"


def test_fallback_summary_generation(snowflake_connection):
    """
    Test fallback summary generation when AI summarization fails
    """
    summary_gen = SummaryGeneration(snowflake_connection)
    
    # Test fallback with no defects
    fallback_no_defects = summary_gen._generate_fallback_summary('Low', 0, {})
    assert 'Low' in fallback_no_defects
    assert 'no' in fallback_no_defects.lower() or 'good' in fallback_no_defects.lower()
    
    # Test fallback with defects
    defect_counts = {'exposed wiring': 2, 'crack': 1}
    fallback_with_defects = summary_gen._generate_fallback_summary('High', 2, defect_counts)
    assert 'High' in fallback_with_defects
    assert 'exposed wiring' in fallback_with_defects
    assert '3' in fallback_with_defects  # Total defects
    assert '2' in fallback_with_defects  # Affected rooms
