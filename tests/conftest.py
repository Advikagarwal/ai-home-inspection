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
                import sys
                # Check for COUNT queries first (very specific)
                if 'COUNT(*)' in query and 'findings f' in query and 'rooms r' in query and 'property_id' in query and 'GROUP BY' not in query:
                    # Count findings for a property through rooms (but not defect counts with GROUP BY)
                    if params:
                        property_id = params[0]
                        # Find all rooms for this property
                        property_rooms = [r['room_id'] for r in storage['rooms'].values() 
                                        if r['property_id'] == property_id]
                        # Count findings in these rooms
                        count = sum(1 for f in storage['findings'].values() if f['room_id'] in property_rooms)
                        cursor.fetchone.return_value = (count,)
                # Check for dashboard queries first (most specific)
                elif 'SELECT DISTINCT' in query and 'p.property_id' in query and 'FROM properties p' in query:
                    # Dashboard get_property_list query
                    # Apply filters if present
                    results = []
                    
                    for prop in storage['properties'].values():
                        include = True
                        
                        # Apply risk level filter
                        if params and len(params) > 0 and 'risk_category' in query:
                            param_idx = 0
                            if 'p.risk_category = %s' in query:
                                if prop['risk_category'] != params[param_idx]:
                                    include = False
                                param_idx += 1
                        
                        # Apply defect type filter
                        if include and 'JOIN rooms r' in query and 'JOIN findings f' in query and 'JOIN defect_tags dt' in query:
                            # Need to check if property has the specified defect type
                            if params and len(params) > 0:
                                # Determine which parameter is the defect type
                                # If there's a risk_category filter, defect is second param
                                # Otherwise it's the first param
                                defect_param_idx = 1 if ('p.risk_category = %s' in query and len(params) > 1) else 0
                                
                                # Make sure we're not looking at a search param (which contains %)
                                target_defect = None
                                if defect_param_idx < len(params):
                                    param_val = params[defect_param_idx]
                                    if isinstance(param_val, str) and '%' not in param_val:
                                        target_defect = param_val
                                
                                if target_defect:
                                    # Find rooms for this property
                                    prop_rooms = [r['room_id'] for r in storage['rooms'].values() 
                                                if r['property_id'] == prop['property_id']]
                                    # Find findings for these rooms
                                    prop_findings = [f_id for f_id, f in storage['findings'].items() 
                                                   if f['room_id'] in prop_rooms]
                                    # Check if any defect tag matches
                                    has_defect = any(
                                        tag['defect_category'] == target_defect
                                        for tag in storage['defect_tags'].values()
                                        if tag['finding_id'] in prop_findings
                                    )
                                    if not has_defect:
                                        include = False
                        
                        # Apply search filter
                        if include and params and 'LIKE' in query:
                            # Find the search term (it's the last 3 params if present)
                            search_params = [p for p in params if isinstance(p, str) and '%' in p]
                            if search_params:
                                search_term = search_params[0].strip('%').lower()
                                location_match = search_term in (prop['location'] or '').lower()
                                id_match = search_term in (prop['property_id'] or '').lower()
                                summary_match = search_term in (prop['summary_text'] or '').lower()
                                if not (location_match or id_match or summary_match):
                                    include = False
                        
                        if include:
                            results.append((
                                prop['property_id'],
                                prop['location'],
                                prop['inspection_date'],
                                prop['risk_category'],
                                prop['risk_score'],
                                prop['summary_text']
                            ))
                    
                    cursor.fetchall.return_value = results
                # Check for JOIN queries first (more specific)
                elif 'SELECT dt.defect_category, dt.severity_weight, dt.tag_id' in query and 'JOIN findings' in query:
                    # Query for room risk calculation
                    if params:
                        room_id = params[0]
                        # Find all findings for this room
                        room_findings = [f_id for f_id, f in storage['findings'].items() 
                                       if f['room_id'] == room_id]
                        # Find all defect tags for these findings
                        matching_tags = [
                            (tag['defect_category'], tag['severity_weight'], tag['tag_id'])
                            for tag in storage['defect_tags'].values()
                            if tag['finding_id'] in room_findings
                        ]
                        cursor.fetchall.return_value = matching_tags
                elif 'INSERT INTO properties' in query:
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
                elif 'SELECT property_id, location, inspection_date' in query and 'risk_category, risk_score, summary_text' in query and 'FROM properties' in query:
                    # get_property_details query - returns full property details (6 columns)
                    if params:
                        prop_id = params[0]
                        if prop_id in storage['properties']:
                            prop = storage['properties'][prop_id]
                            cursor.fetchone.return_value = (
                                prop['property_id'],
                                prop['location'],
                                prop['inspection_date'],
                                prop['risk_category'],
                                prop['risk_score'],
                                prop['summary_text']
                            )
                        else:
                            cursor.fetchone.return_value = None
                elif 'SELECT property_id, location, inspection_date, risk_score' in query and 'FROM properties' in query:
                    # get_property query - returns full property details
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
                elif 'SELECT room_id, room_type, room_location, risk_score' in query and 'FROM rooms' in query and 'WHERE property_id' in query:
                    # get_property_details - get all rooms for a property
                    if params:
                        property_id = params[0]
                        matching_rooms = [
                            (room['room_id'], room['room_type'], room['room_location'], room['risk_score'])
                            for room in storage['rooms'].values()
                            if room['property_id'] == property_id
                        ]
                        cursor.fetchall.return_value = matching_rooms
                elif 'SELECT room_id, property_id, room_type, room_location, risk_score' in query and 'FROM rooms' in query:
                    # get_room query - returns a single room by room_id
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
                elif 'SELECT finding_id, finding_type, note_text' in query and 'FROM findings' in query and 'WHERE room_id' in query:
                    # get_property_details or get_room_details - get all findings for a room
                    if params:
                        room_id = params[0]
                        matching_findings = [
                            (f['finding_id'], f['finding_type'], f['note_text'], 
                             f['image_filename'], f['image_stage_path'], f['processing_status'])
                            for f in storage['findings'].values()
                            if f['room_id'] == room_id
                        ]
                        cursor.fetchall.return_value = matching_findings
                elif 'SELECT f.finding_id, f.room_id, r.room_id' in query and 'JOIN rooms r' in query:
                    # Referential integrity check for finding-room relationship (MUST BE BEFORE GENERAL SELECT)
                    if params:
                        finding_id = params[0]
                        if finding_id in storage['findings']:
                            finding = storage['findings'][finding_id]
                            room_id = finding['room_id']
                            if room_id in storage['rooms']:
                                cursor.fetchone.return_value = (finding_id, room_id, room_id)
                            else:
                                cursor.fetchone.return_value = None
                        else:
                            cursor.fetchone.return_value = None
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
                elif 'DELETE FROM defect_tags' in query:
                    if params:
                        # Handle both single finding_id and IN clause
                        if 'WHERE finding_id IN' in query:
                            # Multiple finding IDs
                            finding_ids = params
                            tags_to_delete = [tag_id for tag_id, tag in storage['defect_tags'].items()
                                            if tag['finding_id'] in finding_ids]
                            for tag_id in tags_to_delete:
                                del storage['defect_tags'][tag_id]
                        else:
                            # Single finding_id
                            finding_id = params[0]
                            tags_to_delete = [tag_id for tag_id, tag in storage['defect_tags'].items()
                                            if tag['finding_id'] == finding_id]
                            for tag_id in tags_to_delete:
                                del storage['defect_tags'][tag_id]
                elif 'DELETE FROM classification_history' in query:
                    if params:
                        if 'WHERE finding_id IN' in query:
                            finding_ids = params
                            history_to_delete = [h_id for h_id, h in storage['classification_history'].items()
                                               if h['finding_id'] in finding_ids]
                            for h_id in history_to_delete:
                                del storage['classification_history'][h_id]
                        else:
                            finding_id = params[0]
                            history_to_delete = [h_id for h_id, h in storage['classification_history'].items()
                                               if h['finding_id'] == finding_id]
                            for h_id in history_to_delete:
                                del storage['classification_history'][h_id]
                elif 'DELETE FROM findings' in query:
                    if params:
                        if 'WHERE finding_id IN' in query:
                            finding_ids = params
                            for finding_id in finding_ids:
                                if finding_id in storage['findings']:
                                    del storage['findings'][finding_id]
                        else:
                            finding_id = params[0]
                            if finding_id in storage['findings']:
                                del storage['findings'][finding_id]
                elif 'DELETE FROM rooms' in query:
                    if params:
                        if 'WHERE room_id IN' in query:
                            room_ids = params
                            for room_id in room_ids:
                                if room_id in storage['rooms']:
                                    del storage['rooms'][room_id]
                        else:
                            room_id = params[0]
                            if room_id in storage['rooms']:
                                del storage['rooms'][room_id]
                elif 'DELETE FROM properties' in query:
                    if params:
                        if 'WHERE property_id IN' in query:
                            prop_ids = params
                            for prop_id in prop_ids:
                                if prop_id in storage['properties']:
                                    del storage['properties'][prop_id]
                        else:
                            prop_id = params[0]
                            if prop_id in storage['properties']:
                                del storage['properties'][prop_id]
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
                elif 'SELECT dt.defect_category, COUNT(*)' in query and 'GROUP BY dt.defect_category' in query:
                    # Defect counts query for summary generation (must come before generic defect_tags SELECT)
                    if params:
                        property_id = params[0]
                        # Find all rooms for this property
                        property_rooms = [r['room_id'] for r in storage['rooms'].values() 
                                        if r['property_id'] == property_id]
                        # Find all findings for these rooms
                        room_findings = [f_id for f_id, f in storage['findings'].items() 
                                       if f['room_id'] in property_rooms]
                        # Count defect tags by category
                        defect_counts = {}
                        for tag in storage['defect_tags'].values():
                            if tag['finding_id'] in room_findings:
                                category = tag['defect_category']
                                defect_counts[category] = defect_counts.get(category, 0) + 1
                        # Return as list of tuples (category, count)
                        result = [(cat, count) for cat, count in defect_counts.items()]
                        cursor.fetchall.return_value = result
                elif 'SELECT defect_category' in query and 'FROM defect_tags' in query and 'WHERE finding_id' in query:
                    # Query for just defect categories (1 column)
                    if params:
                        finding_id = params[0]
                        matching_categories = [
                            (tag['defect_category'],)
                            for tag in storage['defect_tags'].values()
                            if tag['finding_id'] == finding_id
                        ]
                        cursor.fetchall.return_value = matching_categories
                elif 'SELECT tag_id, defect_category, confidence_score' in query and 'FROM defect_tags' in query and 'WHERE finding_id' in query:
                    # get_property_details or get_room_details - get all tags for a finding (5 columns)
                    if params:
                        finding_id = params[0]
                        matching_tags = [
                            (tag['tag_id'], tag['defect_category'], tag['confidence_score'],
                             tag['severity_weight'], tag['classified_at'])
                            for tag in storage['defect_tags'].values()
                            if tag['finding_id'] == finding_id
                        ]
                        cursor.fetchall.return_value = matching_tags
                elif 'SELECT dt.tag_id, dt.finding_id, f.finding_id' in query and 'JOIN findings f' in query:
                    # Referential integrity check for defect_tags-finding relationship (MUST BE BEFORE GENERAL SELECT)
                    if params:
                        finding_id = params[0]
                        matching_tags = []
                        for tag in storage['defect_tags'].values():
                            if tag['finding_id'] == finding_id:
                                if finding_id in storage['findings']:
                                    matching_tags.append((tag['tag_id'], finding_id, finding_id))
                        cursor.fetchall.return_value = matching_tags
                elif 'SELECT' in query and 'FROM defect_tags' in query and 'WHERE finding_id' in query:
                    if params:
                        finding_id = params[0]
                        matching_tags = [
                            (tag['tag_id'], tag['finding_id'], tag['defect_category'],
                             tag['confidence_score'], tag['severity_weight'], tag['classified_at'])
                            for tag in storage['defect_tags'].values()
                            if tag['finding_id'] == finding_id
                        ]
                        cursor.fetchall.return_value = matching_tags
                elif 'SELECT r.room_id, r.property_id, p.property_id' in query and 'JOIN properties p' in query:
                    # Referential integrity check for room-property relationship
                    if params:
                        room_id = params[0]
                        if room_id in storage['rooms']:
                            room = storage['rooms'][room_id]
                            property_id = room['property_id']
                            if property_id in storage['properties']:
                                cursor.fetchone.return_value = (room_id, property_id, property_id)
                            else:
                                cursor.fetchone.return_value = None
                        else:
                            cursor.fetchone.return_value = None
                elif 'SELECT ch.history_id, ch.finding_id, f.finding_id' in query and 'JOIN findings f' in query:
                    # Referential integrity check for classification_history-finding relationship
                    if params:
                        finding_id = params[0]
                        matching_history = []
                        for history in storage['classification_history'].values():
                            if history['finding_id'] == finding_id:
                                if finding_id in storage['findings']:
                                    matching_history.append((history['history_id'], finding_id, finding_id))
                        cursor.fetchall.return_value = matching_history
                elif 'SELECT COUNT(*)' in query and 'FROM rooms' in query and 'WHERE property_id' in query:
                    # Count rooms for a property
                    if params:
                        property_id = params[0]
                        count = sum(1 for room in storage['rooms'].values() if room['property_id'] == property_id)
                        cursor.fetchone.return_value = (count,)
                elif 'SELECT history_id, defect_category, confidence_score, classification_method' in query and 'FROM classification_history' in query:
                    # Query for classification history records (4 columns - no finding_id in SELECT)
                    if params:
                        finding_id = params[0]
                        matching_history = [
                            (h['history_id'], h['defect_category'], h['confidence_score'], h['classification_method'])
                            for h in storage['classification_history'].values()
                            if h['finding_id'] == finding_id
                        ]
                        cursor.fetchall.return_value = matching_history
                elif 'SELECT history_id, finding_id, defect_category' in query and 'FROM classification_history' in query:
                    # Query for classification history records (6 columns - includes finding_id)
                    if params:
                        finding_id = params[0]
                        matching_history = [
                            (h['history_id'], h['finding_id'], h['defect_category'],
                             h['confidence_score'], h['classification_method'], h['classified_at'])
                            for h in storage['classification_history'].values()
                            if h['finding_id'] == finding_id
                        ]
                        cursor.fetchall.return_value = matching_history
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
                elif 'UPDATE rooms' in query and 'risk_score' in query:
                    if params:
                        risk_score, room_id = params
                        if room_id in storage['rooms']:
                            storage['rooms'][room_id]['risk_score'] = risk_score
                elif 'UPDATE properties' in query and 'risk_score' in query and 'risk_category' in query:
                    # Update both risk_score and risk_category
                    if params and len(params) == 3:
                        risk_score, risk_category, property_id = params
                        if property_id in storage['properties']:
                            storage['properties'][property_id]['risk_score'] = risk_score
                            storage['properties'][property_id]['risk_category'] = risk_category
                elif 'UPDATE properties' in query and 'risk_score' in query:
                    # Update only risk_score (shouldn't happen but handle gracefully)
                    if params and len(params) == 2:
                        risk_score, property_id = params
                        if property_id in storage['properties']:
                            storage['properties'][property_id]['risk_score'] = risk_score
                elif 'SELECT room_id, risk_score' in query and 'FROM rooms' in query:
                    if params:
                        property_id = params[0]
                        matching_rooms = [
                            (room['room_id'], room['risk_score'])
                            for room in storage['rooms'].values()
                            if room['property_id'] == property_id
                        ]
                        cursor.fetchall.return_value = matching_rooms
                elif 'SELECT property_id, risk_score, risk_category' in query:
                    if params:
                        property_id = params[0]
                        if property_id in storage['properties']:
                            prop = storage['properties'][property_id]
                            cursor.fetchone.return_value = (
                                prop['property_id'],
                                prop['risk_score'],
                                prop['risk_category']
                            )
                        else:
                            cursor.fetchone.return_value = None
                elif 'SELECT room_id, room_type, risk_score' in query:
                    if params:
                        property_id = params[0]
                        matching_rooms = [
                            (room['room_id'], room['room_type'], room['risk_score'])
                            for room in storage['rooms'].values()
                            if room['property_id'] == property_id
                        ]
                        cursor.fetchall.return_value = matching_rooms
                elif 'SELECT COUNT(DISTINCT r.room_id)' in query and 'dt.defect_category' in query:
                    # Affected room count query
                    if params:
                        property_id = params[0]
                        # Find all rooms for this property
                        property_rooms = [r['room_id'] for r in storage['rooms'].values() 
                                        if r['property_id'] == property_id]
                        # Find rooms with non-'none' defects
                        affected_rooms = set()
                        for f_id, f in storage['findings'].items():
                            if f['room_id'] in property_rooms:
                                for tag in storage['defect_tags'].values():
                                    if tag['finding_id'] == f_id and tag['defect_category'] != 'none':
                                        affected_rooms.add(f['room_id'])
                        cursor.fetchone.return_value = (len(affected_rooms),)
                elif 'SELECT risk_score, risk_category' in query and 'FROM properties' in query:
                    # Risk info query for summary generation
                    if params:
                        property_id = params[0]
                        if property_id in storage['properties']:
                            prop = storage['properties'][property_id]
                            cursor.fetchone.return_value = (
                                prop['risk_score'],
                                prop['risk_category']
                            )
                        else:
                            cursor.fetchone.return_value = None
                elif 'UPDATE properties' in query and 'summary_text' in query:
                    # Update summary text
                    if params:
                        summary_text, property_id = params
                        if property_id in storage['properties']:
                            storage['properties'][property_id]['summary_text'] = summary_text
                elif 'SNOWFLAKE.CORTEX.SUMMARIZE' in query:
                    # Mock Cortex AI SUMMARIZE - just return the input text
                    if params:
                        cursor.fetchone.return_value = (params[0],)
                elif 'INSERT INTO classification_history' in query:
                    # Handle classification history inserts (already handled above, but ensure it's here)
                    pass
            
            cursor.execute = execute
            cursor.close = MagicMock()
            return cursor
        
        conn.cursor = mock_cursor
        conn.commit = MagicMock()
        
        yield conn
