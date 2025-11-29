"""
Dashboard Data Access Layer for AI-Assisted Home Inspection Workspace
Provides data retrieval and filtering functions for the dashboard UI
"""

from typing import Dict, List, Optional, Any


class DashboardData:
    """Handles data access operations for the dashboard"""
    
    def __init__(self, snowflake_connection):
        """
        Initialize dashboard data access component
        
        Args:
            snowflake_connection: Active Snowflake database connection
        """
        self.conn = snowflake_connection
    
    def get_property_list(
        self,
        risk_level: Optional[str] = None,
        defect_type: Optional[str] = None,
        search_term: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve list of all properties with optional filtering
        
        Args:
            risk_level: Filter by risk category ('Low', 'Medium', 'High')
            defect_type: Filter by defect category
            search_term: Search in location, identifier, or summary
            
        Returns:
            List of property dictionaries with required fields:
            - property_id
            - location
            - inspection_date
            - risk_category
            - risk_score
        """
        cursor = self.conn.cursor()
        try:
            # Build base query
            query = """
                SELECT DISTINCT
                    p.property_id,
                    p.location,
                    p.inspection_date,
                    p.risk_category,
                    p.risk_score,
                    p.summary_text
                FROM properties p
            """
            
            # Add joins if filtering by defect type
            if defect_type:
                query += """
                    JOIN rooms r ON p.property_id = r.property_id
                    JOIN findings f ON r.room_id = f.room_id
                    JOIN defect_tags dt ON f.finding_id = dt.finding_id
                """
            
            # Build WHERE clause
            where_clauses = []
            params = []
            
            if risk_level:
                where_clauses.append("p.risk_category = %s")
                params.append(risk_level)
            
            if defect_type:
                where_clauses.append("dt.defect_category = %s")
                params.append(defect_type)
            
            if search_term:
                where_clauses.append(
                    "(p.location LIKE %s OR p.property_id LIKE %s OR p.summary_text LIKE %s)"
                )
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern])
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            query += " ORDER BY p.property_id"
            
            # Execute query
            cursor.execute(query, tuple(params) if params else None)
            rows = cursor.fetchall()
            
            # Format results
            properties = []
            for row in rows:
                properties.append({
                    'property_id': row[0],
                    'location': row[1],
                    'inspection_date': row[2],
                    'risk_category': row[3],
                    'risk_score': row[4],
                    'summary_text': row[5]
                })
            
            return properties
            
        finally:
            cursor.close()

    def get_property_details(self, property_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve complete details for a property including rooms, findings, and defect tags
        
        Args:
            property_id: Unique identifier for the property
            
        Returns:
            Dictionary containing:
            - property_id
            - location
            - inspection_date
            - risk_category
            - risk_score
            - summary_text
            - rooms: list of room dictionaries with findings and defect tags
        """
        cursor = self.conn.cursor()
        try:
            # Get property information
            cursor.execute("""
                SELECT property_id, location, inspection_date, 
                       risk_category, risk_score, summary_text
                FROM properties
                WHERE property_id = %s
            """, (property_id,))
            
            prop_row = cursor.fetchone()
            if not prop_row:
                return None
            
            property_data = {
                'property_id': prop_row[0],
                'location': prop_row[1],
                'inspection_date': prop_row[2],
                'risk_category': prop_row[3],
                'risk_score': prop_row[4],
                'summary_text': prop_row[5],
                'rooms': []
            }
            
            # Get all rooms for this property
            cursor.execute("""
                SELECT room_id, room_type, room_location, risk_score
                FROM rooms
                WHERE property_id = %s
                ORDER BY room_id
            """, (property_id,))
            
            room_rows = cursor.fetchall()
            
            for room_row in room_rows:
                room_id = room_row[0]
                room_data = {
                    'room_id': room_id,
                    'room_type': room_row[1],
                    'room_location': room_row[2],
                    'risk_score': room_row[3],
                    'findings': []
                }
                
                # Get all findings for this room
                cursor.execute("""
                    SELECT finding_id, finding_type, note_text, 
                           image_filename, image_stage_path, processing_status
                    FROM findings
                    WHERE room_id = %s
                    ORDER BY finding_id
                """, (room_id,))
                
                finding_rows = cursor.fetchall()
                
                for finding_row in finding_rows:
                    finding_id = finding_row[0]
                    finding_data = {
                        'finding_id': finding_id,
                        'finding_type': finding_row[1],
                        'note_text': finding_row[2],
                        'image_filename': finding_row[3],
                        'image_stage_path': finding_row[4],
                        'processing_status': finding_row[5],
                        'defect_tags': []
                    }
                    
                    # Get all defect tags for this finding
                    cursor.execute("""
                        SELECT tag_id, defect_category, confidence_score, 
                               severity_weight, classified_at
                        FROM defect_tags
                        WHERE finding_id = %s
                        ORDER BY severity_weight DESC, defect_category
                    """, (finding_id,))
                    
                    tag_rows = cursor.fetchall()
                    
                    for tag_row in tag_rows:
                        finding_data['defect_tags'].append({
                            'tag_id': tag_row[0],
                            'defect_category': tag_row[1],
                            'confidence_score': tag_row[2],
                            'severity_weight': tag_row[3],
                            'classified_at': tag_row[4]
                        })
                    
                    room_data['findings'].append(finding_data)
                
                property_data['rooms'].append(room_data)
            
            return property_data
            
        finally:
            cursor.close()
    
    def get_room_details(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve complete details for a room including images and annotations
        
        Args:
            room_id: Unique identifier for the room
            
        Returns:
            Dictionary containing:
            - room_id
            - property_id
            - room_type
            - room_location
            - risk_score
            - findings: list of findings with images and defect tags
        """
        cursor = self.conn.cursor()
        try:
            # Get room information
            cursor.execute("""
                SELECT room_id, property_id, room_type, room_location, risk_score
                FROM rooms
                WHERE room_id = %s
            """, (room_id,))
            
            room_row = cursor.fetchone()
            if not room_row:
                return None
            
            room_data = {
                'room_id': room_row[0],
                'property_id': room_row[1],
                'room_type': room_row[2],
                'room_location': room_row[3],
                'risk_score': room_row[4],
                'findings': []
            }
            
            # Get all findings for this room
            cursor.execute("""
                SELECT finding_id, finding_type, note_text, 
                       image_filename, image_stage_path, processing_status
                FROM findings
                WHERE room_id = %s
                ORDER BY finding_id
            """, (room_id,))
            
            finding_rows = cursor.fetchall()
            
            for finding_row in finding_rows:
                finding_id = finding_row[0]
                finding_data = {
                    'finding_id': finding_id,
                    'finding_type': finding_row[1],
                    'note_text': finding_row[2],
                    'image_filename': finding_row[3],
                    'image_stage_path': finding_row[4],
                    'processing_status': finding_row[5],
                    'defect_tags': []
                }
                
                # Get all defect tags for this finding
                cursor.execute("""
                    SELECT tag_id, defect_category, confidence_score, 
                           severity_weight, classified_at
                    FROM defect_tags
                    WHERE finding_id = %s
                    ORDER BY severity_weight DESC, defect_category
                """, (finding_id,))
                
                tag_rows = cursor.fetchall()
                
                for tag_row in tag_rows:
                    finding_data['defect_tags'].append({
                        'tag_id': tag_row[0],
                        'defect_category': tag_row[1],
                        'confidence_score': tag_row[2],
                        'severity_weight': tag_row[3],
                        'classified_at': tag_row[4]
                    })
                
                room_data['findings'].append(finding_data)
            
            return room_data
            
        finally:
            cursor.close()
