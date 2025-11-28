"""
Property-based tests for data storage round-trip
Feature: ai-home-inspection, Property 1: Data storage round-trip preservation
Validates: Requirements 1.1
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import date, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_ingestion import DataIngestion


# Test data generators
@st.composite
def property_data(draw):
    """Generate valid property data for testing"""
    # Generate a random UUID-like string
    property_id = draw(st.uuids()).hex
    
    # Generate location string (non-empty, reasonable length)
    location = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pd')),
        min_size=1,
        max_size=100
    ))
    
    # Generate inspection date (within reasonable range)
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
    # Generate a random UUID-like string for room_id
    room_id = draw(st.uuids()).hex
    
    # Generate room type from common types
    room_type = draw(st.sampled_from([
        'kitchen', 'bedroom', 'bathroom', 'living room', 
        'dining room', 'basement', 'attic', 'garage'
    ]))
    
    # Generate optional room location
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
def text_finding_data(draw):
    """Generate valid text finding data for testing"""
    # Generate non-empty text note
    note_text = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pd', 'Po')),
        min_size=1,
        max_size=500
    ))
    
    return note_text


@st.composite
def image_finding_data(draw):
    """Generate valid image finding data for testing"""
    # Generate image filename
    filename = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
        min_size=1,
        max_size=50
    )) + draw(st.sampled_from(['.jpg', '.png', '.jpeg', '.gif']))
    
    # Generate mock image data (just some bytes)
    image_size = draw(st.integers(min_value=100, max_value=10000))
    image_bytes = bytes([draw(st.integers(min_value=0, max_value=255)) for _ in range(min(image_size, 100))])
    
    return {
        'filename': filename,
        'image_bytes': image_bytes
    }


class TestDataStorageRoundTrip:
    """
    **Feature: ai-home-inspection, Property 1: Data storage round-trip preservation**
    
    For any property metadata (identifier, location, inspection date), 
    storing it in the database and then retrieving it should return 
    equivalent values for all fields.
    """
    
    @given(prop_data=property_data())
    @settings(max_examples=100)
    def test_property_storage_round_trip(self, prop_data, snowflake_connection):
        """
        **Feature: ai-home-inspection, Property 1: Data storage round-trip preservation**
        **Validates: Requirements 1.1**
        
        Test that property data can be stored and retrieved with all fields preserved.
        """
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        
        # Act - Store the property
        stored_id = ingestion.ingest_property(prop_data)
        
        # Act - Retrieve the property
        retrieved = ingestion.get_property(stored_id)
        
        # Assert - All fields should match
        assert retrieved is not None, "Property should be retrievable after storage"
        assert retrieved['property_id'] == prop_data['property_id'], \
            "Property ID should be preserved"
        assert retrieved['location'] == prop_data['location'], \
            "Location should be preserved"
        assert retrieved['inspection_date'] == prop_data['inspection_date'], \
            "Inspection date should be preserved"
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            cursor.execute("DELETE FROM properties WHERE property_id = %s", 
                         (prop_data['property_id'],))
            snowflake_connection.commit()
        finally:
            cursor.close()



class TestRoomPropertyLinkage:
    """
    **Feature: ai-home-inspection, Property 2: Room-property linkage integrity**
    
    For any room created with a property association, querying the room 
    should return the correct property_id linkage.
    """
    
    @given(prop_data=property_data(), rm_data=room_data())
    @settings(max_examples=100)
    def test_room_property_linkage_integrity(self, prop_data, rm_data, snowflake_connection):
        """
        **Feature: ai-home-inspection, Property 2: Room-property linkage integrity**
        **Validates: Requirements 1.2**
        
        Test that room data maintains correct linkage to its parent property.
        """
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        
        # Act - Store the property first
        stored_property_id = ingestion.ingest_property(prop_data)
        
        # Act - Store the room linked to the property
        stored_room_id = ingestion.ingest_room(rm_data, stored_property_id)
        
        # Act - Retrieve the room
        retrieved_room = ingestion.get_room(stored_room_id)
        
        # Assert - Room should be retrievable and linked to correct property
        assert retrieved_room is not None, "Room should be retrievable after storage"
        assert retrieved_room['room_id'] == rm_data['room_id'], \
            "Room ID should be preserved"
        assert retrieved_room['property_id'] == prop_data['property_id'], \
            "Room should be linked to the correct property"
        assert retrieved_room['room_type'] == rm_data['room_type'], \
            "Room type should be preserved"
        assert retrieved_room['room_location'] == rm_data['room_location'], \
            "Room location should be preserved"
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            cursor.execute("DELETE FROM rooms WHERE room_id = %s", 
                         (rm_data['room_id'],))
            cursor.execute("DELETE FROM properties WHERE property_id = %s", 
                         (prop_data['property_id'],))
            snowflake_connection.commit()
        finally:
            cursor.close()


class TestFindingStorageAndRetrieval:
    """
    **Feature: ai-home-inspection, Property 3: Finding storage and retrieval**
    
    For any text or image finding stored with a room association, 
    retrieving the finding should return the correct room_id and finding content.
    """
    
    @given(
        prop_data=property_data(),
        rm_data=room_data(),
        note_text=text_finding_data()
    )
    @settings(max_examples=100)
    def test_text_finding_storage_and_retrieval(self, prop_data, rm_data, note_text, snowflake_connection):
        """
        **Feature: ai-home-inspection, Property 3: Finding storage and retrieval**
        **Validates: Requirements 1.3, 1.4**
        
        Test that text findings can be stored and retrieved with correct room linkage and content.
        """
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        
        # Act - Store property and room first
        stored_property_id = ingestion.ingest_property(prop_data)
        stored_room_id = ingestion.ingest_room(rm_data, stored_property_id)
        
        # Act - Store the text finding
        stored_finding_id = ingestion.ingest_text_finding(note_text, stored_room_id)
        
        # Act - Retrieve the finding
        retrieved_finding = ingestion.get_finding(stored_finding_id)
        
        # Assert - Finding should be retrievable with correct data
        assert retrieved_finding is not None, "Finding should be retrievable after storage"
        assert retrieved_finding['finding_id'] == stored_finding_id, \
            "Finding ID should be preserved"
        assert retrieved_finding['room_id'] == rm_data['room_id'], \
            "Finding should be linked to the correct room"
        assert retrieved_finding['finding_type'] == 'text', \
            "Finding type should be 'text'"
        assert retrieved_finding['note_text'] == note_text, \
            "Note text content should be preserved"
        assert retrieved_finding['image_filename'] is None, \
            "Text finding should not have image filename"
        assert retrieved_finding['image_stage_path'] is None, \
            "Text finding should not have image stage path"
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            cursor.execute("DELETE FROM findings WHERE finding_id = %s", 
                         (stored_finding_id,))
            cursor.execute("DELETE FROM rooms WHERE room_id = %s", 
                         (rm_data['room_id'],))
            cursor.execute("DELETE FROM properties WHERE property_id = %s", 
                         (prop_data['property_id'],))
            snowflake_connection.commit()
        finally:
            cursor.close()
    
    @given(
        prop_data=property_data(),
        rm_data=room_data(),
        img_data=image_finding_data()
    )
    @settings(max_examples=100)
    def test_image_finding_storage_and_retrieval(self, prop_data, rm_data, img_data, snowflake_connection):
        """
        **Feature: ai-home-inspection, Property 3: Finding storage and retrieval**
        **Validates: Requirements 1.3, 1.4**
        
        Test that image findings can be stored and retrieved with correct room linkage and metadata.
        """
        # Arrange
        ingestion = DataIngestion(snowflake_connection)
        
        # Act - Store property and room first
        stored_property_id = ingestion.ingest_property(prop_data)
        stored_room_id = ingestion.ingest_room(rm_data, stored_property_id)
        
        # Act - Store the image finding
        stored_finding_id = ingestion.ingest_image_finding(
            img_data['image_bytes'],
            img_data['filename'],
            stored_room_id
        )
        
        # Act - Retrieve the finding
        retrieved_finding = ingestion.get_finding(stored_finding_id)
        
        # Assert - Finding should be retrievable with correct data
        assert retrieved_finding is not None, "Finding should be retrievable after storage"
        assert retrieved_finding['finding_id'] == stored_finding_id, \
            "Finding ID should be preserved"
        assert retrieved_finding['room_id'] == rm_data['room_id'], \
            "Finding should be linked to the correct room"
        assert retrieved_finding['finding_type'] == 'image', \
            "Finding type should be 'image'"
        assert retrieved_finding['note_text'] is None, \
            "Image finding should not have note text"
        assert retrieved_finding['image_filename'] == img_data['filename'], \
            "Image filename should be preserved"
        assert retrieved_finding['image_stage_path'] is not None, \
            "Image finding should have stage path"
        assert stored_finding_id in retrieved_finding['image_stage_path'], \
            "Stage path should contain the finding ID"
        
        # Clean up
        cursor = snowflake_connection.cursor()
        try:
            cursor.execute("DELETE FROM findings WHERE finding_id = %s", 
                         (stored_finding_id,))
            cursor.execute("DELETE FROM rooms WHERE room_id = %s", 
                         (rm_data['room_id'],))
            cursor.execute("DELETE FROM properties WHERE property_id = %s", 
                         (prop_data['property_id'],))
            snowflake_connection.commit()
        finally:
            cursor.close()
