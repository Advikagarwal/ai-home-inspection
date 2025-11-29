"""
Property-based tests for risk scoring engine
Tests Properties 8-11 and 29 from the design document
"""

import pytest
from hypothesis import given, strategies as st, settings
from src.risk_scoring import RiskScoring
from src.ai_classification import AIClassification
from src.data_ingestion import DataIngestion
import uuid
from datetime import date


# Test generators
@st.composite
def defect_category(draw):
    """Generate a valid defect category"""
    all_categories = list(set(
        AIClassification.TEXT_DEFECT_CATEGORIES + 
        AIClassification.IMAGE_DEFECT_CATEGORIES
    ))
    return draw(st.sampled_from(all_categories))


@st.composite
def property_with_rooms_and_defects(draw):
    """Generate a property with rooms and defects for testing"""
    property_id = str(uuid.uuid4())
    num_rooms = draw(st.integers(min_value=1, max_value=5))
    
    rooms = []
    for _ in range(num_rooms):
        room_id = str(uuid.uuid4())
        num_defects = draw(st.integers(min_value=0, max_value=10))
        defects = [draw(defect_category()) for _ in range(num_defects)]
        rooms.append({
            'room_id': room_id,
            'room_type': draw(st.sampled_from(['kitchen', 'bedroom', 'bathroom', 'living room'])),
            'defects': defects
        })
    
    return {
        'property_id': property_id,
        'location': draw(st.text(min_size=1, max_size=50)),
        'inspection_date': date.today(),
        'rooms': rooms
    }


# Property 8: Severity weights are correctly applied
# **Feature: ai-home-inspection, Property 8: Severity weights are correctly applied**
# **Validates: Requirements 4.2**
@settings(max_examples=100)
@given(category=defect_category())
def test_severity_weight_correctness(snowflake_connection, category):
    """
    Property 8: For any defect tag, the severity weight used in calculations 
    must match the specification
    """
    risk_scoring = RiskScoring(snowflake_connection)
    
    # Expected weights from specification
    expected_weights = {
        'exposed wiring': 3,
        'electrical wiring': 3,
        'damp wall': 3,
        'mold': 3,
        'water leak': 2,
        'crack': 2,
        'none': 0
    }
    
    # Get the weight from the risk scoring engine
    actual_weight = risk_scoring.get_severity_weight(category)
    
    # Verify it matches the specification
    assert actual_weight == expected_weights[category], \
        f"Severity weight for '{category}' should be {expected_weights[category]}, got {actual_weight}"


# Property 9: Room risk score calculation
# **Feature: ai-home-inspection, Property 9: Room risk score calculation**
# **Validates: Requirements 4.1, 4.3**
@settings(max_examples=100)
@given(data=st.data())
def test_room_risk_calculation(snowflake_connection, data):
    """
    Property 9: For any room with a known set of defect tags, 
    the computed risk score should equal the sum of the severity weights for those tags
    """
    risk_scoring = RiskScoring(snowflake_connection)
    data_ingestion = DataIngestion(snowflake_connection)
    ai_classification = AIClassification(snowflake_connection)
    
    # Create a property and room
    property_id = str(uuid.uuid4())
    room_id = str(uuid.uuid4())
    
    data_ingestion.ingest_property({
        'property_id': property_id,
        'location': data.draw(st.text(min_size=1, max_size=50)),
        'inspection_date': date.today()
    })
    
    data_ingestion.ingest_room({
        'room_id': room_id,
        'room_type': 'bedroom'
    }, property_id)
    
    # Generate random defects
    num_defects = data.draw(st.integers(min_value=0, max_value=10))
    defects = [data.draw(defect_category()) for _ in range(num_defects)]
    
    # Calculate expected risk score
    expected_risk_score = sum(
        risk_scoring.get_severity_weight(defect) for defect in defects
    )
    
    # Create findings and defect tags for each defect
    for defect in defects:
        # Create finding and get its ID
        finding_id = data_ingestion.ingest_text_finding(f"Found {defect}", room_id)
        
        # Manually insert defect tag (simulating classification)
        tag_id = str(uuid.uuid4())
        cursor = snowflake_connection.cursor()
        cursor.execute("""
            INSERT INTO defect_tags (
                tag_id, finding_id, defect_category, 
                confidence_score, severity_weight
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (tag_id, finding_id, defect, 0.9, risk_scoring.get_severity_weight(defect)))
        snowflake_connection.commit()
        cursor.close()
    
    # Compute room risk
    actual_risk_score, defect_details = risk_scoring.compute_room_risk(room_id)
    
    # Verify the risk score matches the sum of severity weights
    assert actual_risk_score == expected_risk_score, \
        f"Room risk score should be {expected_risk_score}, got {actual_risk_score}"
    
    # Verify the defect details are correct
    assert len(defect_details) == len(defects), \
        f"Should have {len(defects)} defect details, got {len(defect_details)}"


# Property 10: Property risk score aggregation
# **Feature: ai-home-inspection, Property 10: Property risk score aggregation**
# **Validates: Requirements 4.4**
@settings(max_examples=100)
@given(prop_data=property_with_rooms_and_defects())
def test_property_risk_aggregation(snowflake_connection, prop_data):
    """
    Property 10: For any property with rooms that have known risk scores, 
    the property risk score should equal the sum of all room risk scores
    """
    risk_scoring = RiskScoring(snowflake_connection)
    data_ingestion = DataIngestion(snowflake_connection)
    
    # Create property
    property_id = prop_data['property_id']
    data_ingestion.ingest_property({
        'property_id': property_id,
        'location': prop_data['location'],
        'inspection_date': prop_data['inspection_date']
    })
    
    # Create rooms and defects, track expected scores
    expected_room_scores = []
    
    for room_data in prop_data['rooms']:
        room_id = room_data['room_id']
        data_ingestion.ingest_room({
            'room_id': room_id,
            'room_type': room_data['room_type']
        }, property_id)
        
        # Calculate expected room score
        room_score = sum(
            risk_scoring.get_severity_weight(defect) 
            for defect in room_data['defects']
        )
        expected_room_scores.append(room_score)
        
        # Create findings and defect tags
        for defect in room_data['defects']:
            # Create finding and get its ID
            finding_id = data_ingestion.ingest_text_finding(f"Found {defect}", room_id)
            
            # Manually insert defect tag
            tag_id = str(uuid.uuid4())
            cursor = snowflake_connection.cursor()
            cursor.execute("""
                INSERT INTO defect_tags (
                    tag_id, finding_id, defect_category, 
                    confidence_score, severity_weight
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (tag_id, finding_id, defect, 0.9, risk_scoring.get_severity_weight(defect)))
            snowflake_connection.commit()
            cursor.close()
    
    # Calculate expected property score
    expected_property_score = sum(expected_room_scores)
    
    # Compute property risk (which will compute room risks internally if needed)
    actual_property_score, risk_category = risk_scoring.compute_property_risk(property_id)
    
    # Verify the property score equals the sum of room scores
    assert actual_property_score == expected_property_score, \
        f"Property risk score should be {expected_property_score}, got {actual_property_score}"


# Property 11: Risk categorization correctness
# **Feature: ai-home-inspection, Property 11: Risk categorization correctness**
# **Validates: Requirements 4.5**
@settings(max_examples=100)
@given(risk_score=st.integers(min_value=0, max_value=50))
def test_risk_categorization(snowflake_connection, risk_score):
    """
    Property 11: For any property with a computed risk score, 
    the risk category should be "Low" if score < 5, "Medium" if 5 <= score < 10, 
    or "High" if score >= 10
    """
    risk_scoring = RiskScoring(snowflake_connection)
    
    # Determine expected category based on specification
    if risk_score < 5:
        expected_category = 'Low'
    elif risk_score < 10:
        expected_category = 'Medium'
    else:
        expected_category = 'High'
    
    # Get actual category from risk scoring engine
    actual_category = risk_scoring.categorize_risk(risk_score)
    
    # Verify categorization is correct
    assert actual_category == expected_category, \
        f"Risk score {risk_score} should be categorized as '{expected_category}', got '{actual_category}'"


# Property 29: Risk calculation traceability
# **Feature: ai-home-inspection, Property 29: Risk calculation traceability**
# **Validates: Requirements 10.2**
@settings(max_examples=100)
@given(prop_data=property_with_rooms_and_defects())
def test_risk_calculation_traceability(snowflake_connection, prop_data):
    """
    Property 29: For any computed risk score, the system should store 
    which defect tags contributed to the score and their individual weights
    """
    risk_scoring = RiskScoring(snowflake_connection)
    data_ingestion = DataIngestion(snowflake_connection)
    
    # Create property
    property_id = prop_data['property_id']
    data_ingestion.ingest_property({
        'property_id': property_id,
        'location': prop_data['location'],
        'inspection_date': prop_data['inspection_date']
    })
    
    # Track all defects we create
    all_defects = []
    
    for room_data in prop_data['rooms']:
        room_id = room_data['room_id']
        data_ingestion.ingest_room({
            'room_id': room_id,
            'room_type': room_data['room_type']
        }, property_id)
        
        # Create findings and defect tags
        for defect in room_data['defects']:
            # Create finding and get its ID
            finding_id = data_ingestion.ingest_text_finding(f"Found {defect}", room_id)
            
            # Manually insert defect tag
            tag_id = str(uuid.uuid4())
            severity_weight = risk_scoring.get_severity_weight(defect)
            
            cursor = snowflake_connection.cursor()
            cursor.execute("""
                INSERT INTO defect_tags (
                    tag_id, finding_id, defect_category, 
                    confidence_score, severity_weight
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (tag_id, finding_id, defect, 0.9, severity_weight))
            snowflake_connection.commit()
            cursor.close()
            
            all_defects.append({
                'defect_category': defect,
                'severity_weight': severity_weight
            })
    
    # Compute property risk
    risk_scoring.compute_property_risk(property_id)
    
    # Get risk calculation details
    details = risk_scoring.get_risk_calculation_details(property_id)
    
    # Verify we can trace back all defects
    assert details is not None, "Should be able to retrieve risk calculation details"
    
    # Collect all defects from the details
    traced_defects = []
    for room in details['rooms']:
        for defect in room['defects']:
            traced_defects.append({
                'defect_category': defect['defect_category'],
                'severity_weight': defect['severity_weight']
            })
    
    # Verify all defects are traceable
    assert len(traced_defects) == len(all_defects), \
        f"Should be able to trace {len(all_defects)} defects, found {len(traced_defects)}"
    
    # Verify the sum of traced weights matches the property score
    traced_total = sum(d['severity_weight'] for d in traced_defects)
    # Convert to int in case the database returns a string
    property_score = int(details['property_risk_score']) if details['property_risk_score'] is not None else 0
    assert property_score == traced_total, \
        f"Property risk score {property_score} should equal sum of traced weights {traced_total}"


# Unit tests for edge cases

def test_risk_calculation_with_no_defects(snowflake_connection):
    """Test risk calculation when a property has no defects"""
    risk_scoring = RiskScoring(snowflake_connection)
    data_ingestion = DataIngestion(snowflake_connection)
    
    # Create property and room with no defects
    property_id = str(uuid.uuid4())
    room_id = str(uuid.uuid4())
    
    data_ingestion.ingest_property({
        'property_id': property_id,
        'location': 'Test Location',
        'inspection_date': date.today()
    })
    
    data_ingestion.ingest_room({
        'room_id': room_id,
        'room_type': 'bedroom'
    }, property_id)
    
    # Compute property risk (no defects)
    property_score, risk_category = risk_scoring.compute_property_risk(property_id)
    
    # Should be 0 and Low
    assert property_score == 0, f"Expected score 0, got {property_score}"
    assert risk_category == 'Low', f"Expected 'Low', got '{risk_category}'"


def test_risk_categorization_boundary_values(snowflake_connection):
    """Test risk categorization at boundary values (4, 5, 9, 10)"""
    risk_scoring = RiskScoring(snowflake_connection)
    
    # Test boundary values
    assert risk_scoring.categorize_risk(4) == 'Low', "Score 4 should be Low"
    assert risk_scoring.categorize_risk(5) == 'Medium', "Score 5 should be Medium"
    assert risk_scoring.categorize_risk(9) == 'Medium', "Score 9 should be Medium"
    assert risk_scoring.categorize_risk(10) == 'High', "Score 10 should be High"
    
    # Test values just outside boundaries
    assert risk_scoring.categorize_risk(0) == 'Low', "Score 0 should be Low"
    assert risk_scoring.categorize_risk(6) == 'Medium', "Score 6 should be Medium"
    assert risk_scoring.categorize_risk(15) == 'High', "Score 15 should be High"
