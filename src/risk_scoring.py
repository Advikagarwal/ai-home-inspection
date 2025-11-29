"""
Risk Scoring Engine for AI-Assisted Home Inspection Workspace
Computes risk scores for rooms and properties based on detected defects
"""

from typing import Dict, List, Optional, Tuple
from src.ai_classification import AIClassification


class RiskScoring:
    """Handles risk score calculation and categorization"""
    
    # Risk category thresholds
    RISK_THRESHOLDS = {
        'Low': (0, 5),      # score < 5
        'Medium': (5, 10),  # 5 <= score < 10
        'High': (10, float('inf'))  # score >= 10
    }
    
    def __init__(self, snowflake_connection):
        """
        Initialize risk scoring component
        
        Args:
            snowflake_connection: Active Snowflake database connection
        """
        self.conn = snowflake_connection
        # Use severity weights from AIClassification
        self.severity_weights = AIClassification.SEVERITY_WEIGHTS
    
    def get_severity_weight(self, defect_category: str) -> int:
        """
        Get severity weight for a defect category
        
        Args:
            defect_category: Defect category name
            
        Returns:
            Severity weight (0-3)
        """
        return self.severity_weights.get(defect_category, 0)
    
    def compute_room_risk(self, room_id: str) -> Tuple[int, List[Dict]]:
        """
        Compute risk score for a room based on its defect tags
        
        Args:
            room_id: Unique identifier for the room
            
        Returns:
            Tuple of (risk_score, defect_details)
            - risk_score: Sum of severity weights for all defects in the room
            - defect_details: List of dicts with defect_category and severity_weight
        """
        cursor = self.conn.cursor()
        try:
            # Query all defect tags for findings in this room
            cursor.execute("""
                SELECT dt.defect_category, dt.severity_weight, dt.tag_id
                FROM defect_tags dt
                JOIN findings f ON dt.finding_id = f.finding_id
                WHERE f.room_id = %s
            """, (room_id,))
            
            rows = cursor.fetchall()
            
            # Calculate total risk score and collect defect details
            risk_score = 0
            defect_details = []
            
            for row in rows:
                defect_category = row[0]
                severity_weight = row[1]
                tag_id = row[2]
                
                risk_score += severity_weight
                defect_details.append({
                    'tag_id': tag_id,
                    'defect_category': defect_category,
                    'severity_weight': severity_weight
                })
            
            # Update room table with calculated score
            cursor.execute("""
                UPDATE rooms
                SET risk_score = %s
                WHERE room_id = %s
            """, (risk_score, room_id))
            self.conn.commit()
            
            return risk_score, defect_details
            
        finally:
            cursor.close()
    
    def compute_property_risk(self, property_id: str) -> Tuple[int, str]:
        """
        Compute risk score for a property by aggregating room scores
        
        Args:
            property_id: Unique identifier for the property
            
        Returns:
            Tuple of (risk_score, risk_category)
            - risk_score: Sum of all room risk scores
            - risk_category: 'Low', 'Medium', or 'High'
        """
        cursor = self.conn.cursor()
        try:
            # Query all rooms for this property
            cursor.execute("""
                SELECT room_id, risk_score
                FROM rooms
                WHERE property_id = %s
            """, (property_id,))
            
            rows = cursor.fetchall()
            
            # Calculate total property risk score
            property_risk_score = 0
            
            for row in rows:
                room_id = row[0]
                room_risk_score = row[1]
                
                # If room doesn't have a risk score yet, compute it
                if room_risk_score is None:
                    room_risk_score, _ = self.compute_room_risk(room_id)
                
                property_risk_score += room_risk_score
            
            # Categorize risk level
            risk_category = self.categorize_risk(property_risk_score)
            
            # Update property table with calculated score and category
            cursor.execute("""
                UPDATE properties
                SET risk_score = %s, risk_category = %s
                WHERE property_id = %s
            """, (property_risk_score, risk_category, property_id))
            self.conn.commit()
            
            return property_risk_score, risk_category
            
        finally:
            cursor.close()
    
    def categorize_risk(self, risk_score: int) -> str:
        """
        Categorize a risk score into Low/Medium/High
        
        Args:
            risk_score: Numerical risk score
            
        Returns:
            Risk category: 'Low', 'Medium', or 'High'
        """
        if risk_score < 5:
            return 'Low'
        elif risk_score < 10:
            return 'Medium'
        else:
            return 'High'
    
    def get_risk_calculation_details(self, property_id: str) -> Dict:
        """
        Get detailed breakdown of risk calculation for a property
        
        Args:
            property_id: Unique identifier for the property
            
        Returns:
            Dictionary with risk calculation details including:
            - property_risk_score
            - risk_category
            - rooms: list of room details with their defects
        """
        cursor = self.conn.cursor()
        try:
            # Get property info
            cursor.execute("""
                SELECT property_id, risk_score, risk_category
                FROM properties
                WHERE property_id = %s
            """, (property_id,))
            
            prop_row = cursor.fetchone()
            if not prop_row:
                return None
            
            property_risk_score = prop_row[1]
            risk_category = prop_row[2]
            
            # Get all rooms for this property
            cursor.execute("""
                SELECT room_id, room_type, risk_score
                FROM rooms
                WHERE property_id = %s
            """, (property_id,))
            
            room_rows = cursor.fetchall()
            
            rooms_details = []
            for room_row in room_rows:
                room_id = room_row[0]
                room_type = room_row[1]
                room_risk_score = room_row[2]
                
                # Get defects for this room
                cursor.execute("""
                    SELECT dt.defect_category, dt.severity_weight, dt.tag_id
                    FROM defect_tags dt
                    JOIN findings f ON dt.finding_id = f.finding_id
                    WHERE f.room_id = %s
                """, (room_id,))
                
                defect_rows = cursor.fetchall()
                defects = [
                    {
                        'tag_id': row[2],
                        'defect_category': row[0],
                        'severity_weight': row[1]
                    }
                    for row in defect_rows
                ]
                
                rooms_details.append({
                    'room_id': room_id,
                    'room_type': room_type,
                    'room_risk_score': room_risk_score,
                    'defects': defects
                })
            
            return {
                'property_id': property_id,
                'property_risk_score': property_risk_score,
                'risk_category': risk_category,
                'rooms': rooms_details
            }
            
        finally:
            cursor.close()
