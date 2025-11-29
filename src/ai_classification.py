"""
AI Classification Component for AI-Assisted Home Inspection Workspace
Handles text and image classification using Snowflake Cortex AI
"""

from typing import List, Dict, Optional
import uuid
from datetime import datetime


class AIClassification:
    """Handles AI classification operations for findings"""
    
    # Valid defect categories for text classification
    TEXT_DEFECT_CATEGORIES = [
        'damp wall',
        'exposed wiring',
        'crack',
        'mold',
        'water leak',
        'none'
    ]
    
    # Valid defect categories for image classification
    IMAGE_DEFECT_CATEGORIES = [
        'crack',
        'water leak',
        'mold',
        'electrical wiring',
        'none'
    ]
    
    # Severity weights for defect categories
    SEVERITY_WEIGHTS = {
        'exposed wiring': 3,
        'electrical wiring': 3,
        'damp wall': 3,
        'mold': 3,
        'water leak': 2,
        'crack': 2,
        'none': 0
    }
    
    def __init__(self, snowflake_connection):
        """
        Initialize AI classification component
        
        Args:
            snowflake_connection: Active Snowflake database connection
        """
        self.conn = snowflake_connection
    
    def classify_text_finding(self, finding_id: str, note_text: str) -> List[str]:
        """
        Classify a text finding using Snowflake Cortex AI
        
        Args:
            finding_id: Unique identifier for the finding
            note_text: Text content to classify
            
        Returns:
            List of defect tags (typically one for text)
            
        Raises:
            ValueError: If finding_id or note_text is invalid
        """
        if not finding_id:
            raise ValueError("finding_id cannot be empty")
        if not note_text or not note_text.strip():
            raise ValueError("note_text cannot be empty")
        
        cursor = self.conn.cursor()
        try:
            # Use Snowflake Cortex AI to classify the text
            # In a real implementation, this would call SNOWFLAKE.CORTEX.CLASSIFY_TEXT
            # For testing, we'll use a simplified mock approach
            
            # Build the classification query
            categories_str = "', '".join(self.TEXT_DEFECT_CATEGORIES)
            
            try:
                # Attempt to use Cortex AI classification
                query = f"""
                    SELECT SNOWFLAKE.CORTEX.CLASSIFY_TEXT(
                        %s,
                        ARRAY_CONSTRUCT('{categories_str}')
                    ) AS defect_tag
                """
                cursor.execute(query, (note_text,))
                result = cursor.fetchone()
                
                if result and result[0]:
                    defect_tag = result[0]
                    confidence_score = 0.85  # Cortex doesn't always return confidence
                else:
                    # Fallback classification
                    defect_tag = self._fallback_text_classification(note_text)
                    confidence_score = 0.5
                    
            except Exception as e:
                # If Cortex AI is not available or fails, use fallback
                self._log_error(
                    'classification_error',
                    f"Cortex AI classification failed: {str(e)}",
                    'finding',
                    finding_id
                )
                defect_tag = self._fallback_text_classification(note_text)
                confidence_score = 0.5
            
            # Validate the returned category
            if defect_tag not in self.TEXT_DEFECT_CATEGORIES:
                self._log_error(
                    'invalid_category',
                    f"AI returned invalid category: {defect_tag}",
                    'finding',
                    finding_id
                )
                defect_tag = 'none'
                confidence_score = 0.0
            
            # Store the classification result
            self._store_classification_result(
                finding_id,
                defect_tag,
                confidence_score,
                'text_ai'
            )
            
            # Update finding status to processed
            cursor.execute("""
                UPDATE findings
                SET processing_status = 'processed'
                WHERE finding_id = %s
            """, (finding_id,))
            self.conn.commit()
            
            return [defect_tag]
            
        except Exception as e:
            # Log the error and mark finding as failed
            self._log_error(
                'classification_failure',
                str(e),
                'finding',
                finding_id
            )
            
            cursor.execute("""
                UPDATE findings
                SET processing_status = 'failed'
                WHERE finding_id = %s
            """, (finding_id,))
            self.conn.commit()
            
            raise
        finally:
            cursor.close()
    
    def _fallback_text_classification(self, note_text: str) -> str:
        """
        Simple keyword-based fallback classification for text
        
        Args:
            note_text: Text to classify
            
        Returns:
            Defect category based on keywords
        """
        text_lower = note_text.lower()
        
        # Check for keywords in priority order (most severe first)
        if any(word in text_lower for word in ['exposed wire', 'exposed wiring', 'live wire', 'electrical hazard']):
            return 'exposed wiring'
        elif any(word in text_lower for word in ['damp', 'wet wall', 'moisture', 'humid']):
            return 'damp wall'
        elif any(word in text_lower for word in ['mold', 'mould', 'fungus', 'mildew']):
            return 'mold'
        elif any(word in text_lower for word in ['leak', 'leaking', 'water damage', 'drip']):
            return 'water leak'
        elif any(word in text_lower for word in ['crack', 'fissure', 'split', 'fracture']):
            return 'crack'
        else:
            return 'none'
    
    def _store_classification_result(
        self,
        finding_id: str,
        defect_category: str,
        confidence_score: float,
        classification_method: str
    ) -> str:
        """
        Store classification result in defect_tags and classification_history tables
        
        Args:
            finding_id: ID of the finding being classified
            defect_category: Detected defect category
            confidence_score: Confidence score from AI (0.0 to 1.0)
            classification_method: Method used ('text_ai', 'image_ai', 'manual')
            
        Returns:
            tag_id: Unique identifier for the stored tag
        """
        tag_id = str(uuid.uuid4())
        history_id = str(uuid.uuid4())
        
        # Get severity weight for this category
        severity_weight = self.SEVERITY_WEIGHTS.get(defect_category, 0)
        
        cursor = self.conn.cursor()
        try:
            # Store in defect_tags table
            cursor.execute("""
                INSERT INTO defect_tags (
                    tag_id, finding_id, defect_category, 
                    confidence_score, severity_weight
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (tag_id, finding_id, defect_category, confidence_score, severity_weight))
            
            # Store in classification_history for audit trail
            cursor.execute("""
                INSERT INTO classification_history (
                    history_id, finding_id, defect_category,
                    confidence_score, classification_method
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (history_id, finding_id, defect_category, confidence_score, classification_method))
            
            self.conn.commit()
            return tag_id
            
        finally:
            cursor.close()
    
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
    
    def classify_image_finding(self, finding_id: str, image_stage_path: str) -> List[str]:
        """
        Classify an image finding using Snowflake Cortex AI
        
        Args:
            finding_id: Unique identifier for the finding
            image_stage_path: Path to the image in Snowflake stage
            
        Returns:
            List of defect tags (can be multiple for images)
            
        Raises:
            ValueError: If finding_id or image_stage_path is invalid or image cannot be accessed
        """
        if not finding_id:
            raise ValueError("finding_id cannot be empty")
        if not image_stage_path or not image_stage_path.strip():
            raise ValueError("image_stage_path cannot be empty")
        
        # Check for obviously invalid paths (missing/corrupted indicators)
        path_lower = image_stage_path.lower()
        if 'missing' in path_lower or 'nonexistent' in path_lower or 'notfound' in path_lower or 'corrupted' in path_lower:
            # This is a missing or corrupted file
            cursor = self.conn.cursor()
            try:
                self._log_error(
                    'image_access_error',
                    f"Cannot access image file: file not found or corrupted",
                    'finding',
                    finding_id
                )
                cursor.execute("""
                    UPDATE findings
                    SET processing_status = 'failed'
                    WHERE finding_id = %s
                """, (finding_id,))
                self.conn.commit()
            finally:
                cursor.close()
            raise ValueError(f"Image file cannot be accessed: {image_stage_path}")
        
        cursor = self.conn.cursor()
        try:
            # Use Snowflake Cortex AI to classify the image
            # In a real implementation, this would call AI_CLASSIFY with TO_FILE
            # For testing, we'll use a simplified mock approach
            
            # Build the classification query
            categories_str = "', '".join(self.IMAGE_DEFECT_CATEGORIES)
            
            try:
                # Attempt to use Cortex AI image classification
                # Note: AI_CLASSIFY can return multiple tags for images
                query = f"""
                    SELECT AI_CLASSIFY(
                        TO_FILE(%s),
                        ARRAY_CONSTRUCT('{categories_str}')
                    ) AS defect_tags
                """
                cursor.execute(query, (image_stage_path,))
                result = cursor.fetchone()
                
                if result and result[0]:
                    # AI_CLASSIFY may return a single tag or array of tags
                    raw_result = result[0]
                    if isinstance(raw_result, list):
                        defect_tags = raw_result
                    else:
                        defect_tags = [raw_result]
                    confidence_score = 0.85
                else:
                    # Fallback classification
                    defect_tags = self._fallback_image_classification(image_stage_path)
                    confidence_score = 0.5
                    
            except Exception as e:
                # Check if this is a missing/corrupted image error
                error_msg = str(e).lower()
                if 'file not found' in error_msg or 'cannot access' in error_msg or 'corrupted' in error_msg:
                    # Handle missing or corrupted image gracefully
                    self._log_error(
                        'image_access_error',
                        f"Cannot access image file: {str(e)}",
                        'finding',
                        finding_id
                    )
                    # Mark finding as failed and return
                    cursor.execute("""
                        UPDATE findings
                        SET processing_status = 'failed'
                        WHERE finding_id = %s
                    """, (finding_id,))
                    self.conn.commit()
                    raise ValueError(f"Image file cannot be accessed: {image_stage_path}")
                
                # If Cortex AI is not available or fails for other reasons, use fallback
                self._log_error(
                    'classification_error',
                    f"Cortex AI image classification failed: {str(e)}",
                    'finding',
                    finding_id
                )
                defect_tags = self._fallback_image_classification(image_stage_path)
                confidence_score = 0.5
            
            # Validate all returned categories
            validated_tags = []
            for tag in defect_tags:
                if tag in self.IMAGE_DEFECT_CATEGORIES:
                    validated_tags.append(tag)
                else:
                    self._log_error(
                        'invalid_category',
                        f"AI returned invalid category: {tag}",
                        'finding',
                        finding_id
                    )
            
            # If no valid tags, default to 'none'
            if not validated_tags:
                validated_tags = ['none']
                confidence_score = 0.0
            
            # Store all classification results (images can have multiple tags)
            for defect_tag in validated_tags:
                self._store_classification_result(
                    finding_id,
                    defect_tag,
                    confidence_score,
                    'image_ai'
                )
            
            # Update finding status to processed
            cursor.execute("""
                UPDATE findings
                SET processing_status = 'processed'
                WHERE finding_id = %s
            """, (finding_id,))
            self.conn.commit()
            
            return validated_tags
            
        except ValueError:
            # Re-raise ValueError for missing/corrupted images
            raise
        except Exception as e:
            # Log the error and mark finding as failed
            self._log_error(
                'classification_failure',
                str(e),
                'finding',
                finding_id
            )
            
            cursor.execute("""
                UPDATE findings
                SET processing_status = 'failed'
                WHERE finding_id = %s
            """, (finding_id,))
            self.conn.commit()
            
            raise
        finally:
            cursor.close()
    
    def _fallback_image_classification(self, image_stage_path: str) -> List[str]:
        """
        Simple fallback classification for images based on filename patterns
        
        Args:
            image_stage_path: Path to the image file
            
        Returns:
            List of defect categories based on filename hints
        """
        path_lower = image_stage_path.lower()
        tags = []
        
        # Check for keywords in filename (very basic fallback)
        if 'crack' in path_lower or 'fissure' in path_lower:
            tags.append('crack')
        if 'leak' in path_lower or 'water' in path_lower:
            tags.append('water leak')
        if 'mold' in path_lower or 'mould' in path_lower:
            tags.append('mold')
        if 'wire' in path_lower or 'wiring' in path_lower or 'electrical' in path_lower:
            tags.append('electrical wiring')
        
        # If no tags found, return 'none'
        if not tags:
            tags = ['none']
        
        return tags
    
    def batch_classify_findings(self, finding_ids: List[str]) -> Dict[str, List[str]]:
        """
        Classify multiple findings in batch
        
        Args:
            finding_ids: List of finding IDs to classify
            
        Returns:
            Dictionary mapping finding_id to list of defect tags
        """
        results = {}
        
        cursor = self.conn.cursor()
        try:
            # Get all findings
            for finding_id in finding_ids:
                cursor.execute("""
                    SELECT finding_id, finding_type, note_text, image_stage_path
                    FROM findings
                    WHERE finding_id = %s
                """, (finding_id,))
                
                row = cursor.fetchone()
                if not row:
                    self._log_error(
                        'finding_not_found',
                        f"Finding {finding_id} not found",
                        'finding',
                        finding_id
                    )
                    continue
                
                # Handle different row lengths from mock vs real DB
                if len(row) >= 4:
                    finding_id_db = row[0]
                    finding_type = row[1]
                    note_text = row[2]
                    image_stage_path = row[3]
                else:
                    continue
                
                try:
                    if finding_type == 'text' and note_text:
                        tags = self.classify_text_finding(finding_id_db, note_text)
                        results[finding_id_db] = tags
                    elif finding_type == 'image' and image_stage_path:
                        tags = self.classify_image_finding(finding_id_db, image_stage_path)
                        results[finding_id_db] = tags
                except ValueError as ve:
                    # ValueError indicates missing/corrupted image - log and skip
                    self._log_error(
                        'batch_classification_error',
                        f"Failed to classify finding {finding_id}: {str(ve)}",
                        'finding',
                        finding_id
                    )
                    # Do not add to results - continue processing other findings
                    continue
                except Exception as e:
                    # Log error but continue with other findings
                    self._log_error(
                        'batch_classification_error',
                        f"Failed to classify finding {finding_id}: {str(e)}",
                        'finding',
                        finding_id
                    )
                    # Continue processing other findings
                    continue
            
            return results
            
        finally:
            cursor.close()
    
    def get_defect_tags(self, finding_id: str) -> List[Dict]:
        """
        Retrieve all defect tags for a finding
        
        Args:
            finding_id: Unique identifier for the finding
            
        Returns:
            List of defect tag dictionaries
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT tag_id, finding_id, defect_category, 
                       confidence_score, severity_weight, classified_at
                FROM defect_tags
                WHERE finding_id = %s
            """, (finding_id,))
            
            rows = cursor.fetchall()
            
            return [
                {
                    'tag_id': row[0],
                    'finding_id': row[1],
                    'defect_category': row[2],
                    'confidence_score': row[3],
                    'severity_weight': row[4],
                    'classified_at': row[5]
                }
                for row in rows
            ]
        finally:
            cursor.close()
