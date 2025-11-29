"""
Export Component for AI-Assisted Home Inspection Workspace
Generates PDF and CSV exports of inspection reports
"""

from typing import Dict, List, Optional, Any
import io
import csv
from datetime import datetime


class ExportComponent:
    """Handles export operations for property inspection reports"""
    
    SUPPORTED_FORMATS = ['pdf', 'csv']
    
    def __init__(self, snowflake_connection):
        """
        Initialize export component
        
        Args:
            snowflake_connection: Active Snowflake database connection
        """
        self.conn = snowflake_connection
    
    def export_property_report(self, property_id: str, format: str) -> bytes:
        """
        Export a property report in the specified format
        
        Args:
            property_id: Unique identifier for the property
            format: Export format ('pdf' or 'csv')
            
        Returns:
            Bytes of the generated export file
            
        Raises:
            ValueError: If format is not supported or property not found
        """
        # Validate format
        if format.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported export format: {format}. Supported formats: {', '.join(self.SUPPORTED_FORMATS)}")
        
        # Get property data
        property_data = self._get_complete_property_data(property_id)
        if not property_data:
            raise ValueError(f"Property {property_id} not found")
        
        # Generate export based on format
        if format.lower() == 'pdf':
            return self.export_pdf(property_id)
        elif format.lower() == 'csv':
            return self.export_csv([property_id])
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _get_complete_property_data(self, property_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve complete property data including all rooms, findings, and defect tags
        
        Args:
            property_id: Unique identifier for the property
            
        Returns:
            Dictionary with complete property data or None if not found
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
    
    def export_pdf(self, property_id: str) -> bytes:
        """
        Generate a PDF export for a property with images and annotations
        
        Args:
            property_id: Unique identifier for the property
            
        Returns:
            PDF file as bytes
            
        Raises:
            ValueError: If property not found
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
        except ImportError:
            raise ImportError("reportlab is required for PDF export. Install with: pip install reportlab")
        
        # Get complete property data
        property_data = self._get_complete_property_data(property_id)
        if not property_data:
            raise ValueError(f"Property {property_id} not found")
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Add custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title
        story.append(Paragraph("Property Inspection Report", title_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Property Information
        story.append(Paragraph("Property Information", heading_style))
        
        prop_info_data = [
            ['Property ID:', property_data['property_id']],
            ['Location:', property_data['location']],
            ['Inspection Date:', str(property_data['inspection_date'])],
            ['Risk Category:', property_data['risk_category'] or 'N/A'],
            ['Risk Score:', str(property_data['risk_score']) if property_data['risk_score'] is not None else 'N/A']
        ]
        
        prop_table = Table(prop_info_data, colWidths=[2*inch, 4*inch])
        prop_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(prop_table)
        story.append(Spacer(1, 0.3 * inch))
        
        # Summary
        if property_data['summary_text']:
            from xml.sax.saxutils import escape
            story.append(Paragraph("Executive Summary", heading_style))
            escaped_summary = escape(property_data['summary_text'])
            story.append(Paragraph(escaped_summary, styles['Normal']))
            story.append(Spacer(1, 0.3 * inch))
        
        # Rooms and Findings
        story.append(Paragraph("Detailed Findings", heading_style))
        
        for room in property_data['rooms']:
            # Room header
            room_title = f"Room: {room['room_type']}"
            if room['room_location']:
                room_title += f" ({room['room_location']})"
            story.append(Paragraph(room_title, styles['Heading3']))
            
            room_risk = f"Room Risk Score: {room['risk_score'] if room['risk_score'] is not None else 'N/A'}"
            story.append(Paragraph(room_risk, styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))
            
            # Findings
            if room['findings']:
                for finding in room['findings']:
                    # Finding details
                    finding_type = finding['finding_type'].capitalize()
                    story.append(Paragraph(f"<b>Finding ({finding_type}):</b>", styles['Normal']))
                    
                    if finding['note_text']:
                        # Escape special characters for ReportLab
                        from reportlab.lib.utils import simpleSplit
                        from xml.sax.saxutils import escape
                        escaped_note = escape(finding['note_text'])
                        story.append(Paragraph(f"Note: {escaped_note}", styles['Normal']))
                    
                    if finding['image_filename']:
                        story.append(Paragraph(f"Image: {finding['image_filename']}", styles['Normal']))
                        story.append(Paragraph(f"Path: {finding['image_stage_path']}", styles['Normal']))
                    
                    # Defect tags (annotations)
                    if finding['defect_tags']:
                        tags_text = "Detected Defects: " + ", ".join([
                            f"{tag['defect_category']} (severity: {tag['severity_weight']})"
                            for tag in finding['defect_tags']
                        ])
                        story.append(Paragraph(tags_text, styles['Normal']))
                    
                    story.append(Spacer(1, 0.15 * inch))
            else:
                story.append(Paragraph("No findings recorded for this room.", styles['Normal']))
                story.append(Spacer(1, 0.15 * inch))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def export_csv(self, property_ids: List[str]) -> bytes:
        """
        Generate a CSV export for one or more properties
        
        Args:
            property_ids: List of property IDs to export
            
        Returns:
            CSV file as bytes
        """
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'property_id', 'location', 'inspection_date', 'risk_category', 'risk_score', 'summary_text',
            'room_id', 'room_type', 'room_location', 'room_risk_score',
            'finding_id', 'finding_type', 'note_text', 'image_filename', 'image_stage_path', 'processing_status',
            'tag_id', 'defect_category', 'confidence_score', 'severity_weight', 'classified_at'
        ])
        
        # Write data for each property
        for property_id in property_ids:
            property_data = self._get_complete_property_data(property_id)
            if not property_data:
                continue
            
            # If property has no rooms, write property-level data only
            if not property_data['rooms']:
                writer.writerow([
                    property_data['property_id'],
                    property_data['location'],
                    property_data['inspection_date'],
                    property_data['risk_category'],
                    property_data['risk_score'],
                    property_data['summary_text'],
                    '', '', '', '',  # room fields
                    '', '', '', '', '', '',  # finding fields
                    '', '', '', '', ''  # tag fields
                ])
                continue
            
            # Write data for each room
            for room in property_data['rooms']:
                # If room has no findings, write room-level data only
                if not room['findings']:
                    writer.writerow([
                        property_data['property_id'],
                        property_data['location'],
                        property_data['inspection_date'],
                        property_data['risk_category'],
                        property_data['risk_score'],
                        property_data['summary_text'],
                        room['room_id'],
                        room['room_type'],
                        room['room_location'],
                        room['risk_score'],
                        '', '', '', '', '', '',  # finding fields
                        '', '', '', '', ''  # tag fields
                    ])
                    continue
                
                # Write data for each finding
                for finding in room['findings']:
                    # If finding has no tags, write finding-level data only
                    if not finding['defect_tags']:
                        writer.writerow([
                            property_data['property_id'],
                            property_data['location'],
                            property_data['inspection_date'],
                            property_data['risk_category'],
                            property_data['risk_score'],
                            property_data['summary_text'],
                            room['room_id'],
                            room['room_type'],
                            room['room_location'],
                            room['risk_score'],
                            finding['finding_id'],
                            finding['finding_type'],
                            finding['note_text'],
                            finding['image_filename'],
                            finding['image_stage_path'],
                            finding['processing_status'],
                            '', '', '', '', ''  # tag fields
                        ])
                        continue
                    
                    # Write data for each defect tag
                    for tag in finding['defect_tags']:
                        writer.writerow([
                            property_data['property_id'],
                            property_data['location'],
                            property_data['inspection_date'],
                            property_data['risk_category'],
                            property_data['risk_score'],
                            property_data['summary_text'],
                            room['room_id'],
                            room['room_type'],
                            room['room_location'],
                            room['risk_score'],
                            finding['finding_id'],
                            finding['finding_type'],
                            finding['note_text'],
                            finding['image_filename'],
                            finding['image_stage_path'],
                            finding['processing_status'],
                            tag['tag_id'],
                            tag['defect_category'],
                            tag['confidence_score'],
                            tag['severity_weight'],
                            tag['classified_at']
                        ])
        
        # Get CSV bytes
        csv_string = output.getvalue()
        output.close()
        
        return csv_string.encode('utf-8')
