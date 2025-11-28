"""
Pytest configuration and fixtures for AI Home Inspection tests
"""

import pytest
import os
from unittest.mock import Mock, MagicMock


@pytest.fixture(scope="session")
def snowflake_connection():
    """
    Provide a Snowflake database connection for testing.
    
    In a real implementation, this would connect to a test Snowflake instance.
    For now, we'll use a mock that simulates the database behavior.
    """
    # Check if we have real Snowflake credentials
    if os.getenv('SNOWFLAKE_ACCOUNT'):
        # Real Snowflake connection
        import snowflake.connector
        conn = snowflake.connector.connect(
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            database=os.getenv('SNOWFLAKE_DATABASE', 'HOME_INSPECTION_TEST'),
            schema=os.getenv('SNOWFLAKE_SCHEMA', 'PUBLIC'),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE')
        )
        yield conn
        conn.close()
    else:
        # Mock connection for testing without Snowflake
        conn = MagicMock()
        storage = {
            'properties': {}, 
            'rooms': {}, 
            'findings': {},
            'defect_tags': {},
            'classification_history': {},
            'error_log': {}
        }  # In-memory storage for mock
        
        def mock_cursor():
            cursor = MagicMock()
            
            def execute(query, params=None):
                # Simple mock implementation
                if 'INSERT INTO properties' in query:
                    if params:
                        prop_id, location, inspection_date = params
                        storage['properties'][prop_id] = {
                            'property_id': prop_id,
                            'location': location,
                            'inspection_date': inspection_date,
                            'risk_score': None,
                            'risk_category': None,
                            'summary_text': None
                        }
                elif 'INSERT INTO rooms' in query:
                    if params:
                        room_id, property_id, room_type, room_location = params
                        storage['rooms'][room_id] = {
                            'room_id': room_id,
                            'property_id': property_id,
                            'room_type': room_type,
                            'room_location': room_location,
                            'risk_score': None
                        }
                elif 'SELECT' in query and 'FROM properties' in query:
                    if params:
                        prop_id = params[0]
                        if prop_id in storage['properties']:
                            prop = storage['properties'][prop_id]
                            cursor.fetchone.return_value = (
                                prop['property_id'],
                                prop['location'],
                                prop['inspection_date'],
                                prop['risk_score'],
                                prop['risk_category'],
                                prop['summary_text']
                            )
                        else:
                            cursor.fetchone.return_value = None
                elif 'SELECT' in query and 'FROM rooms' in query:
                    if params:
                        room_id = params[0]
                        if room_id in storage['rooms']:
                            room = storage['rooms'][room_id]
                            cursor.fetchone.return_value = (
                                room['room_id'],
                                room['property_id'],
                                room['room_type'],
                                room['room_location'],
                                room['risk_score']
                            )
                        else:
                            cursor.fetchone.return_value = None
                elif 'INSERT INTO findings' in query:
                    if params:
                        # Handle both text and image findings
                        # Text finding: (finding_id, room_id, note_text) with 'text' literal in query
                        # Image finding: (finding_id, room_id, filename, stage_path) with 'image' literal in query
                        if 'note_text' in query:  # Text finding
                            finding_id, room_id, note_text = params
                            storage['findings'][finding_id] = {
                                'finding_id': finding_id,
                                'room_id': room_id,
                                'finding_type': 'text',
                                'note_text': note_text,
                                'image_filename': None,
                                'image_stage_path': None,
                                'processing_status': 'pending'
                            }
                        else:  # Image finding
                            finding_id, room_id, image_filename, image_stage_path = params
                            storage['findings'][finding_id] = {
                                'finding_id': finding_id,
                                'room_id': room_id,
                                'finding_type': 'image',
                                'note_text': None,
                                'image_filename': image_filename,
                                'image_stage_path': image_stage_path,
                                'processing_status': 'pending'
                            }
                elif 'SELECT' in query and 'FROM findings' in query:
                    if params:
                        finding_id = params[0]
                        if finding_id in storage['findings']:
                            finding = storage['findings'][finding_id]
                            # Check if this is the batch query (4 columns) or detail query (7 columns)
                            if 'finding_type, note_text, image_stage_path' in query:
                                # Batch query - 4 columns
                                cursor.fetchone.return_value = (
                                    finding['finding_id'],
                                    finding['finding_type'],
                                    finding['note_text'],
                                    finding['image_stage_path']
                                )
                            else:
                                # Detail query - 7 columns
                                cursor.fetchone.return_value = (
                                    finding['finding_id'],
                                    finding['room_id'],
                                    finding['finding_type'],
                                    finding['note_text'],
                                    finding['image_filename'],
                                    finding['image_stage_path'],
                                    finding['processing_status']
                                )
                        else:
                            cursor.fetchone.return_value = None
                elif 'DELETE FROM findings' in query:
                    if params:
                        finding_id = params[0]
                        if finding_id in storage['findings']:
                            del storage['findings'][finding_id]
                elif 'DELETE FROM properties' in query:
                    if params:
                        prop_id = params[0]
                        if prop_id in storage['properties']:
                            del storage['properties'][prop_id]
                elif 'DELETE FROM rooms' in query:
                    if params:
                        room_id = params[0]
                        if room_id in storage['rooms']:
                            del storage['rooms'][room_id]
                elif 'INSERT INTO defect_tags' in query:
                    if params:
                        tag_id, finding_id, defect_category, confidence_score, severity_weight = params
                        storage['defect_tags'][tag_id] = {
                            'tag_id': tag_id,
                            'finding_id': finding_id,
                            'defect_category': defect_category,
                            'confidence_score': confidence_score,
                            'severity_weight': severity_weight,
                            'classified_at': None  # Would be timestamp in real DB
                        }
                elif 'SELECT' in query and 'FROM defect_tags' in query:
                    if params:
                        finding_id = params[0]
                        matching_tags = [
                            (tag['tag_id'], tag['finding_id'], tag['defect_category'],
                             tag['confidence_score'], tag['severity_weight'], tag['classified_at'])
                            for tag in storage['defect_tags'].values()
                            if tag['finding_id'] == finding_id
                        ]
                        cursor.fetchall.return_value = matching_tags
                elif 'INSERT INTO classification_history' in query:
                    if params:
                        history_id, finding_id, defect_category, confidence_score, classification_method = params
                        storage['classification_history'][history_id] = {
                            'history_id': history_id,
                            'finding_id': finding_id,
                            'defect_category': defect_category,
                            'confidence_score': confidence_score,
                            'classification_method': classification_method,
                            'classified_at': None
                        }
                elif 'INSERT INTO error_log' in query:
                    if params:
                        error_id, error_type, error_message, entity_type, entity_id, stack_trace = params
                        storage['error_log'][error_id] = {
                            'error_id': error_id,
                            'error_type': error_type,
                            'error_message': error_message,
                            'entity_type': entity_type,
                            'entity_id': entity_id,
                            'stack_trace': stack_trace,
                            'occurred_at': None
                        }
                elif 'UPDATE findings' in query and 'processing_status' in query:
                    if params:
                        status_value = 'processed' if 'processed' in query else 'failed'
                        finding_id = params[0]
                        if finding_id in storage['findings']:
                            storage['findings'][finding_id]['processing_status'] = status_value
            
            cursor.execute = execute
            cursor.close = MagicMock()
            return cursor
        
        conn.cursor = mock_cursor
        conn.commit = MagicMock()
        
        yield conn
