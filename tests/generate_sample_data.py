"""
Sample Data Generation Script for AI-Assisted Home Inspection Workspace
Generates realistic sample properties with various defect combinations for testing
"""

import uuid
from datetime import date, timedelta
from typing import List, Dict, Tuple
from src.data_ingestion import DataIngestion
from src.ai_classification import AIClassification
from src.risk_scoring import RiskScoring
from src.summary_generation import SummaryGeneration


class SampleDataGenerator:
    """Generates sample inspection data for testing and demonstration"""
    
    # Sample property locations
    LOCATIONS = [
        "123 Main St, Springfield",
        "456 Oak Ave, Riverside",
        "789 Elm Rd, Lakeside",
        "321 Pine Dr, Hillview",
        "654 Maple Ln, Greenfield"
    ]
    
    # Sample room types
    ROOM_TYPES = [
        "Kitchen",
        "Living Room",
        "Bedroom",
        "Bathroom",
        "Basement",
        "Attic",
        "Garage"
    ]
    
    # Sample defect scenarios
    DEFECT_SCENARIOS = {
        'high_risk': {
            'text_notes': [
                "Exposed wiring visible behind outlet",
                "Severe damp wall with visible water stains",
                "Black mold growth on ceiling",
                "Active water leak from ceiling pipe"
            ],
            'image_files': [
                "exposed_wiring_outlet.jpg",
                "damp_wall_stains.jpg",
                "mold_ceiling.jpg",
                "water_leak_pipe.jpg"
            ]
        },
        'medium_risk': {
            'text_notes': [
                "Large crack in wall near window",
                "Minor water leak under sink",
                "Small damp patch on wall"
            ],
            'image_files': [
                "crack_wall_window.jpg",
                "water_leak_sink.jpg",
                "damp_patch.jpg"
            ]
        },
        'low_risk': {
            'text_notes': [
                "Small hairline crack in ceiling",
                "Minor cosmetic crack in plaster"
            ],
            'image_files': [
                "hairline_crack.jpg",
                "cosmetic_crack.jpg"
            ]
        },
        'no_defects': {
            'text_notes': [
                "Room appears in good condition",
                "No visible defects observed"
            ],
            'image_files': [
                "clean_room.jpg",
                "good_condition.jpg"
            ]
        }
    }
    
    def __init__(self, snowflake_connection):
        """
        Initialize sample data generator
        
        Args:
            snowflake_connection: Active Snowflake database connection
        """
        self.conn = snowflake_connection
        self.data_ingestion = DataIngestion(snowflake_connection)
        self.ai_classification = AIClassification(snowflake_connection)
        self.risk_scoring = RiskScoring(snowflake_connection)
        self.summary_generation = SummaryGeneration(snowflake_connection)
    
    def generate_property(
        self,
        risk_level: str = 'medium',
        num_rooms: int = 3
    ) -> Tuple[str, Dict]:
        """
        Generate a single property with specified risk level
        
        Args:
            risk_level: 'high', 'medium', 'low', or 'no_defects'
            num_rooms: Number of rooms to generate
            
        Returns:
            Tuple of (property_id, property_data)
        """
        # Generate property metadata
        property_id = str(uuid.uuid4())
        location = self.LOCATIONS[hash(property_id) % len(self.LOCATIONS)]
        inspection_date = date.today() - timedelta(days=hash(property_id) % 30)
        
        property_data = {
            'property_id': property_id,
            'location': location,
            'inspection_date': inspection_date
        }
        
        # Ingest property
        self.data_ingestion.ingest_property(property_data)
        
        # Generate rooms with findings
        rooms = []
        for i in range(num_rooms):
            room_id = str(uuid.uuid4())
            room_type = self.ROOM_TYPES[i % len(self.ROOM_TYPES)]
            room_location = f"Floor {(i // 3) + 1}"
            
            room_data = {
                'room_id': room_id,
                'room_type': room_type,
                'room_location': room_location
            }
            
            self.data_ingestion.ingest_room(room_data, property_id)
            
            # Add findings based on risk level
            findings = self._generate_findings_for_room(room_id, risk_level, i)
            rooms.append({
                'room_id': room_id,
                'room_type': room_type,
                'findings': findings
            })
        
        return property_id, {
            'property_data': property_data,
            'rooms': rooms
        }
    
    def _generate_findings_for_room(
        self,
        room_id: str,
        risk_level: str,
        room_index: int
    ) -> List[Dict]:
        """
        Generate findings for a room based on risk level
        
        Args:
            room_id: Room identifier
            risk_level: Risk level for the property
            room_index: Index of the room (for variety)
            
        Returns:
            List of finding dictionaries
        """
        findings = []
        scenario = self.DEFECT_SCENARIOS.get(risk_level, self.DEFECT_SCENARIOS['medium_risk'])
        
        # Determine number of findings based on risk level
        num_findings = {
            'high_risk': 3,
            'medium_risk': 2,
            'low_risk': 1,
            'no_defects': 1
        }.get(risk_level, 2)
        
        # Add text findings
        for i in range(min(num_findings, len(scenario['text_notes']))):
            note_index = (room_index + i) % len(scenario['text_notes'])
            note = scenario['text_notes'][note_index]
            finding_id = self.data_ingestion.ingest_text_finding(note, room_id)
            findings.append({
                'finding_id': finding_id,
                'type': 'text',
                'content': note
            })
        
        # Add image findings
        for i in range(min(num_findings, len(scenario['image_files']))):
            image_index = (room_index + i) % len(scenario['image_files'])
            filename = scenario['image_files'][image_index]
            # Create dummy image data
            image_data = b'dummy_image_data'
            finding_id = self.data_ingestion.ingest_image_finding(
                image_data,
                filename,
                room_id
            )
            findings.append({
                'finding_id': finding_id,
                'type': 'image',
                'content': filename
            })
        
        return findings
    
    def classify_all_findings(self, property_id: str):
        """
        Classify all findings for a property
        
        Args:
            property_id: Property identifier
        """
        # Get all findings for this property
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT f.finding_id, f.finding_type, f.note_text, f.image_stage_path
                FROM findings f
                JOIN rooms r ON f.room_id = r.room_id
                WHERE r.property_id = %s
            """, (property_id,))
            
            findings = cursor.fetchall()
            
            for finding in findings:
                finding_id = finding[0]
                finding_type = finding[1]
                note_text = finding[2]
                image_stage_path = finding[3]
                
                try:
                    if finding_type == 'text' and note_text:
                        self.ai_classification.classify_text_finding(finding_id, note_text)
                    elif finding_type == 'image' and image_stage_path:
                        # Make sure image path doesn't contain 'missing' or 'corrupted'
                        if image_stage_path and not any(word in image_stage_path.lower() for word in ['missing', 'corrupted', 'notfound', 'nonexistent']):
                            self.ai_classification.classify_image_finding(finding_id, image_stage_path)
                except ValueError as ve:
                    # ValueError indicates missing/corrupted image - skip
                    print(f"Skipping finding {finding_id}: {ve}")
                    continue
                except Exception as e:
                    # Log error but continue with other findings
                    print(f"Error classifying finding {finding_id}: {e}")
                    continue
        finally:
            cursor.close()
    
    def compute_risk_scores(self, property_id: str):
        """
        Compute risk scores for all rooms and the property
        
        Args:
            property_id: Property identifier
        """
        # Get all rooms for this property
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT room_id
                FROM rooms
                WHERE property_id = %s
            """, (property_id,))
            
            rooms = cursor.fetchall()
            
            # Compute risk for each room
            for room in rooms:
                room_id = room[0]
                self.risk_scoring.compute_room_risk(room_id)
            
            # Compute property risk
            self.risk_scoring.compute_property_risk(property_id)
        finally:
            cursor.close()
    
    def generate_summary(self, property_id: str):
        """
        Generate summary for a property
        
        Args:
            property_id: Property identifier
        """
        self.summary_generation.generate_property_summary(property_id)
    
    def generate_complete_workflow(
        self,
        risk_level: str = 'medium',
        num_rooms: int = 3
    ) -> str:
        """
        Generate a complete property with full workflow:
        ingest → classify → score → summarize
        
        Args:
            risk_level: 'high', 'medium', 'low', or 'no_defects'
            num_rooms: Number of rooms to generate
            
        Returns:
            property_id: Generated property identifier
        """
        # Generate property and rooms with findings
        property_id, data = self.generate_property(risk_level, num_rooms)
        
        # Classify all findings
        self.classify_all_findings(property_id)
        
        # Compute risk scores
        self.compute_risk_scores(property_id)
        
        # Generate summary
        self.generate_summary(property_id)
        
        return property_id
    
    def generate_sample_dataset(self) -> List[str]:
        """
        Generate a complete sample dataset with multiple properties
        
        Returns:
            List of property IDs
        """
        property_ids = []
        
        # Generate high-risk properties
        for i in range(2):
            prop_id = self.generate_complete_workflow('high_risk', num_rooms=4)
            property_ids.append(prop_id)
            print(f"Generated high-risk property: {prop_id}")
        
        # Generate medium-risk properties
        for i in range(3):
            prop_id = self.generate_complete_workflow('medium_risk', num_rooms=3)
            property_ids.append(prop_id)
            print(f"Generated medium-risk property: {prop_id}")
        
        # Generate low-risk properties
        for i in range(2):
            prop_id = self.generate_complete_workflow('low_risk', num_rooms=3)
            property_ids.append(prop_id)
            print(f"Generated low-risk property: {prop_id}")
        
        # Generate no-defects property
        prop_id = self.generate_complete_workflow('no_defects', num_rooms=2)
        property_ids.append(prop_id)
        print(f"Generated no-defects property: {prop_id}")
        
        return property_ids


def main():
    """Main function to generate sample data"""
    import sys
    
    # This would connect to a real Snowflake instance
    # For testing, use the mock connection from conftest
    print("Sample data generator ready.")
    print("Use SampleDataGenerator class in tests or scripts.")
    print("Example:")
    print("  generator = SampleDataGenerator(snowflake_connection)")
    print("  property_ids = generator.generate_sample_dataset()")


if __name__ == '__main__':
    main()
