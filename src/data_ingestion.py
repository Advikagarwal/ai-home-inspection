"""
Data Ingestion Component for AI-Assisted Home Inspection Workspace
Handles uploads of property metadata, room information, text findings, and image files
"""

from typing import Dict, Optional
from datetime import date
import uuid


class DataIngestion:
    """Handles data ingestion operations for the inspection system"""
    
    def __init__(self, snowflake_connection):
        """
        Initialize data ingestion component
        
        Args:
            snowflake_connection: Active Snowflake database connection
        """
        self.conn = snowflake_connection
    
    def ingest_property(self, property_data: Dict) -> str:
        """
        Ingest property metadata into the database
        
        Args:
            property_data: Dictionary containing property_id, location, inspection_date
            
        Returns:
            property_id: Unique identifier for the stored property
            
        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        required_fields = ['property_id', 'location', 'inspection_date']
        for field in required_fields:
            if field not in property_data:
                raise ValueError(f"Missing required field: {field}")
        
        property_id = property_data['property_id']
        location = property_data['location']
        inspection_date = property_data['inspection_date']
        
        # Insert into database
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO properties (property_id, location, inspection_date)
                VALUES (%s, %s, %s)
            """, (property_id, location, inspection_date))
            self.conn.commit()
            return property_id
        finally:
            cursor.close()
    
    def get_property(self, property_id: str) -> Optional[Dict]:
        """
        Retrieve property metadata from the database
        
        Args:
            property_id: Unique identifier for the property
            
        Returns:
            Dictionary containing property data or None if not found
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT property_id, location, inspection_date, risk_score, 
                       risk_category, summary_text
                FROM properties
                WHERE property_id = %s
            """, (property_id,))
            
            row = cursor.fetchone()
            if row is None:
                return None
            
            return {
                'property_id': row[0],
                'location': row[1],
                'inspection_date': row[2],
                'risk_score': row[3],
                'risk_category': row[4],
                'summary_text': row[5]
            }
        finally:
            cursor.close()
    
    def ingest_room(self, room_data: Dict, property_id: str) -> str:
        """
        Ingest room information linked to a property
        
        Args:
            room_data: Dictionary containing room_id, room_type, room_location
            property_id: ID of the parent property
            
        Returns:
            room_id: Unique identifier for the stored room
        """
        required_fields = ['room_id', 'room_type']
        for field in required_fields:
            if field not in room_data:
                raise ValueError(f"Missing required field: {field}")
        
        room_id = room_data['room_id']
        room_type = room_data['room_type']
        room_location = room_data.get('room_location')
        
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO rooms (room_id, property_id, room_type, room_location)
                VALUES (%s, %s, %s, %s)
            """, (room_id, property_id, room_type, room_location))
            self.conn.commit()
            return room_id
        finally:
            cursor.close()
    
    def get_room(self, room_id: str) -> Optional[Dict]:
        """
        Retrieve room metadata from the database
        
        Args:
            room_id: Unique identifier for the room
            
        Returns:
            Dictionary containing room data or None if not found
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT room_id, property_id, room_type, room_location, risk_score
                FROM rooms
                WHERE room_id = %s
            """, (room_id,))
            
            row = cursor.fetchone()
            if row is None:
                return None
            
            return {
                'room_id': row[0],
                'property_id': row[1],
                'room_type': row[2],
                'room_location': row[3],
                'risk_score': row[4]
            }
        finally:
            cursor.close()
    
    def ingest_text_finding(self, note: str, room_id: str) -> str:
        """
        Ingest text finding linked to a room
        
        Args:
            note: Text description of the finding
            room_id: ID of the parent room
            
        Returns:
            finding_id: Unique identifier for the stored finding
        """
        finding_id = str(uuid.uuid4())
        
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO findings (finding_id, room_id, finding_type, note_text)
                VALUES (%s, %s, 'text', %s)
            """, (finding_id, room_id, note))
            self.conn.commit()
            return finding_id
        finally:
            cursor.close()
    
    def ingest_image_finding(self, image_file: bytes, filename: str, room_id: str) -> str:
        """
        Ingest image finding linked to a room
        
        Args:
            image_file: Binary image data
            filename: Name of the image file
            room_id: ID of the parent room
            
        Returns:
            finding_id: Unique identifier for the stored finding
        """
        finding_id = str(uuid.uuid4())
        stage_path = f"@inspections/{finding_id}/{filename}"
        
        cursor = self.conn.cursor()
        try:
            # Upload image to stage (simplified - actual implementation would use PUT command)
            # For now, just store the metadata
            cursor.execute("""
                INSERT INTO findings (finding_id, room_id, finding_type, 
                                    image_filename, image_stage_path)
                VALUES (%s, %s, 'image', %s, %s)
            """, (finding_id, room_id, filename, stage_path))
            self.conn.commit()
            return finding_id
        finally:
            cursor.close()
    
    def get_finding(self, finding_id: str) -> Optional[Dict]:
        """
        Retrieve finding metadata from the database
        
        Args:
            finding_id: Unique identifier for the finding
            
        Returns:
            Dictionary containing finding data or None if not found
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT finding_id, room_id, finding_type, note_text, 
                       image_filename, image_stage_path, processing_status
                FROM findings
                WHERE finding_id = %s
            """, (finding_id,))
            
            row = cursor.fetchone()
            if row is None:
                return None
            
            return {
                'finding_id': row[0],
                'room_id': row[1],
                'finding_type': row[2],
                'note_text': row[3],
                'image_filename': row[4],
                'image_stage_path': row[5],
                'processing_status': row[6]
            }
        finally:
            cursor.close()
