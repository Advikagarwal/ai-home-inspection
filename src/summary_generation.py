"""
Summary Generation Component for AI-Assisted Home Inspection Workspace
Generates plain-language summaries of inspection results using Cortex AI
"""

from typing import Dict, List, Optional
import uuid


class SummaryGeneration:
    """Handles summary generation for property inspection results"""
    
    def __init__(self, snowflake_connection):
        """
        Initialize summary generation component
        
        Args:
            snowflake_connection: Active Snowflake database connection
        """
        self.conn = snowflake_connection
    
    def get_defect_counts(self, property_id: str) -> Dict[str, int]:
        """
        Aggregate defect counts by type for a property
        
        Args:
            property_id: Unique identifier for the property
            
        Returns:
            Dictionary mapping defect category to count
        """
        cursor = self.conn.cursor()
        try:
            # Query all defect tags for this property
            cursor.execute("""
                SELECT dt.defect_category, COUNT(*) as count
                FROM defect_tags dt
                JOIN findings f ON dt.finding_id = f.finding_id
                JOIN rooms r ON f.room_id = r.room_id
                WHERE r.property_id = %s
                GROUP BY dt.defect_category
            """, (property_id,))
            
            rows = cursor.fetchall()
            
            # Build defect counts dictionary
            defect_counts = {}
            for row in rows:
                defect_category = row[0]
                count = row[1]
                # Exclude 'none' category from counts
                if defect_category != 'none':
                    defect_counts[defect_category] = count
            
            return defect_counts
            
        finally:
            cursor.close()

    def get_affected_room_count(self, property_id: str) -> int:
        """
        Count rooms with at least one defect
        
        Args:
            property_id: Unique identifier for the property
            
        Returns:
            Number of rooms with defects
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT COUNT(DISTINCT r.room_id)
                FROM rooms r
                JOIN findings f ON r.room_id = f.room_id
                JOIN defect_tags dt ON f.finding_id = dt.finding_id
                WHERE r.property_id = %s
                  AND dt.defect_category != 'none'
            """, (property_id,))
            
            row = cursor.fetchone()
            return row[0] if row else 0
            
        finally:
            cursor.close()
    
    def format_defect_description(self, defect_counts: Dict[str, int]) -> str:
        """
        Format defect counts into a readable description
        
        Args:
            defect_counts: Dictionary mapping defect category to count
            
        Returns:
            Formatted string describing defects
        """
        if not defect_counts:
            return "no significant defects found"
        
        # Sort defects by severity (high severity first)
        severity_order = {
            'exposed wiring': 3,
            'electrical wiring': 3,
            'damp wall': 3,
            'mold': 3,
            'water leak': 2,
            'crack': 2
        }
        
        sorted_defects = sorted(
            defect_counts.items(),
            key=lambda x: (severity_order.get(x[0], 0), x[1]),
            reverse=True
        )
        
        # Build description
        parts = []
        for defect_category, count in sorted_defects:
            if count > 0:
                parts.append(f"{count} {defect_category}")
        
        if len(parts) == 0:
            return "no significant defects found"
        elif len(parts) == 1:
            return parts[0]
        elif len(parts) == 2:
            return f"{parts[0]} and {parts[1]}"
        else:
            return ", ".join(parts[:-1]) + f", and {parts[-1]}"

    def generate_property_summary(self, property_id: str) -> str:
        """
        Generate a plain-language summary for a property
        
        Args:
            property_id: Unique identifier for the property
            
        Returns:
            Human-readable summary text
        """
        cursor = self.conn.cursor()
        try:
            # Get property risk information
            cursor.execute("""
                SELECT risk_score, risk_category
                FROM properties
                WHERE property_id = %s
            """, (property_id,))
            
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Property {property_id} not found")
            
            risk_score = row[0] if row[0] is not None else 0
            risk_category = row[1] if row[1] else 'Low'
            
            # Get defect counts and affected room count
            defect_counts = self.get_defect_counts(property_id)
            affected_rooms = self.get_affected_room_count(property_id)
            
            # Format defect description
            defect_description = self.format_defect_description(defect_counts)
            
            # Build structured text for AI summarization
            if not defect_counts and risk_score == 0:
                # No defects case
                structured_text = (
                    f"Property inspection completed with risk level: {risk_category}. "
                    f"No significant defects were found. "
                    f"The property appears to be in good condition."
                )
            else:
                # Has defects case
                structured_text = (
                    f"Property inspection found {affected_rooms} room(s) with defects. "
                    f"Overall risk level: {risk_category} (score: {risk_score}). "
                    f"Defects identified: {defect_description}."
                )
            
            # Try to use Cortex AI SUMMARIZE for natural language generation
            try:
                summary_query = """
                    SELECT SNOWFLAKE.CORTEX.SUMMARIZE(%s) AS summary
                """
                cursor.execute(summary_query, (structured_text,))
                result = cursor.fetchone()
                
                if result and result[0]:
                    summary_text = result[0]
                else:
                    # Fallback to structured text
                    summary_text = structured_text
                    
            except Exception as e:
                # If Cortex AI fails, use fallback summary
                self._log_error(
                    'summary_generation_error',
                    f"Cortex AI SUMMARIZE failed: {str(e)}",
                    'property',
                    property_id
                )
                summary_text = self._generate_fallback_summary(
                    risk_category,
                    affected_rooms,
                    defect_counts
                )
            
            # Update property table with generated summary
            cursor.execute("""
                UPDATE properties
                SET summary_text = %s
                WHERE property_id = %s
            """, (summary_text, property_id))
            self.conn.commit()
            
            return summary_text
            
        finally:
            cursor.close()

    def _generate_fallback_summary(
        self,
        risk_category: str,
        affected_rooms: int,
        defect_counts: Dict[str, int]
    ) -> str:
        """
        Generate a basic fallback summary when AI summarization fails
        
        Args:
            risk_category: Risk category (Low/Medium/High)
            affected_rooms: Number of rooms with defects
            defect_counts: Dictionary of defect counts by category
            
        Returns:
            Basic summary text
        """
        if not defect_counts or affected_rooms == 0:
            return (
                f"Risk: {risk_category}. "
                f"No major issues found. "
                f"Property appears to be in good condition."
            )
        
        # Get top defect (highest severity, then highest count)
        severity_order = {
            'exposed wiring': 3,
            'electrical wiring': 3,
            'damp wall': 3,
            'mold': 3,
            'water leak': 2,
            'crack': 2
        }
        
        sorted_defects = sorted(
            defect_counts.items(),
            key=lambda x: (severity_order.get(x[0], 0), x[1]),
            reverse=True
        )
        
        top_defect = sorted_defects[0][0] if sorted_defects else 'defects'
        total_defects = sum(defect_counts.values())
        
        return (
            f"Risk: {risk_category}. "
            f"Found {total_defects} defect(s) in {affected_rooms} room(s) "
            f"including {top_defect}."
        )
    
    def _log_error(
        self,
        error_type: str,
        error_message: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        stack_trace: Optional[str] = None
    ):
        """
        Log an error to the error_log table
        
        Args:
            error_type: Type of error
            error_message: Error message
            entity_type: Type of entity involved (optional)
            entity_id: ID of entity involved (optional)
            stack_trace: Stack trace (optional)
        """
        error_id = str(uuid.uuid4())
        
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO error_log (
                    error_id, error_type, error_message,
                    entity_type, entity_id, stack_trace
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (error_id, error_type, error_message, entity_type, entity_id, stack_trace))
            
            self.conn.commit()
        finally:
            cursor.close()
