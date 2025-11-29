"""
Streamlit Dashboard UI for AI-Assisted Home Inspection Workspace
Interactive dashboard for viewing and filtering property inspection results
"""

import streamlit as st
import os
from typing import Optional, Dict, Any
from datetime import datetime

# Import data access layer
from src.dashboard_data import DashboardData


def sanitize_error_message(error: Exception) -> str:
    """
    Sanitize error messages to hide sensitive details
    
    Args:
        error: Exception object
        
    Returns:
        User-friendly error message without sensitive information
    """
    error_str = str(error).lower()
    
    # Check for sensitive patterns
    sensitive_patterns = [
        'password', 'connection string', 'api key', 'secret',
        'token', 'credential', 'host=', 'user=', 'pwd=',
        'database=', 'server=', '/home/', '/usr/', 'c:\\',
        'snowflake.snowflakecomputing.com'
    ]
    
    for pattern in sensitive_patterns:
        if pattern in error_str:
            return "An error occurred while processing your request. Please contact support."
    
    # Return generic message for any database or system errors
    if any(keyword in error_str for keyword in ['database', 'connection', 'query', 'sql']):
        return "Unable to retrieve data. Please try again later."
    
    # For other errors, return a generic message
    return "An unexpected error occurred. Please try again."


def get_risk_color(risk_category: Optional[str]) -> str:
    """
    Get color code for risk category
    
    Args:
        risk_category: Risk level (Low, Medium, High)
        
    Returns:
        Color code for display
    """
    if not risk_category:
        return "gray"
    
    risk_colors = {
        'Low': 'green',
        'Medium': 'orange',
        'High': 'red'
    }
    return risk_colors.get(risk_category, 'gray')


def format_date(date_obj) -> str:
    """Format date for display"""
    if date_obj is None:
        return "N/A"
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime("%Y-%m-%d")


def display_property_list(dashboard: DashboardData, filters: Dict[str, Any]):
    """
    Display the property list view with filters
    
    Args:
        dashboard: DashboardData instance
        filters: Dictionary of active filters
    """
    try:
        # Get filtered property list
        properties = dashboard.get_property_list(
            risk_level=filters.get('risk_level'),
            defect_type=filters.get('defect_type'),
            search_term=filters.get('search_term')
        )
        
        if not properties:
            st.info("No properties found matching the current filters.")
            return
        
        st.subheader(f"Properties ({len(properties)})")
        
        # Display each property as a card
        for prop in properties:
            risk_color = get_risk_color(prop.get('risk_category'))
            
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                
                with col1:
                    st.markdown(f"**{prop['property_id']}**")
                    st.text(prop['location'])
                
                with col2:
                    st.text(f"Inspected: {format_date(prop.get('inspection_date'))}")
                
                with col3:
                    risk_score = prop.get('risk_score', 0)
                    st.metric("Risk Score", risk_score)
                
                with col4:
                    risk_category = prop.get('risk_category', 'Low')
                    st.markdown(f":{risk_color}[**{risk_category}**]")
                
                # Show summary if available
                if prop.get('summary_text'):
                    with st.expander("Summary"):
                        st.write(prop['summary_text'])
                
                # View details button
                if st.button("View Details", key=f"view_{prop['property_id']}"):
                    st.session_state['selected_property'] = prop['property_id']
                    st.rerun()
                
                st.divider()
    
    except Exception as e:
        error_msg = sanitize_error_message(e)
        st.error(f"❌ {error_msg}")


def display_property_details(dashboard: DashboardData, property_id: str):
    """
    Display detailed view for a selected property
    
    Args:
        dashboard: DashboardData instance
        property_id: ID of property to display
    """
    try:
        # Back button
        if st.button("← Back to Property List"):
            st.session_state['selected_property'] = None
            st.rerun()
        
        # Get property details
        property_data = dashboard.get_property_details(property_id)
        
        if not property_data:
            st.error("Property not found.")
            return
        
        # Display property header
        st.title(f"Property: {property_data['property_id']}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Location", property_data['location'])
        with col2:
            st.metric("Risk Score", property_data.get('risk_score', 0))
        with col3:
            risk_category = property_data.get('risk_category', 'Low')
            risk_color = get_risk_color(risk_category)
            st.markdown(f"**Risk Level:** :{risk_color}[{risk_category}]")
        
        st.text(f"Inspection Date: {format_date(property_data.get('inspection_date'))}")
        
        # Display summary prominently
        if property_data.get('summary_text'):
            st.info(f"📋 **Summary:** {property_data['summary_text']}")
        
        st.divider()
        
        # Display rooms
        rooms = property_data.get('rooms', [])
        
        if not rooms:
            st.warning("No rooms found for this property.")
            return
        
        st.subheader(f"Rooms ({len(rooms)})")
        
        for room in rooms:
            with st.expander(f"🚪 {room['room_type']} - {room.get('room_location', 'N/A')} (Risk: {room.get('risk_score', 0)})"):
                display_room_details(room)
    
    except Exception as e:
        error_msg = sanitize_error_message(e)
        st.error(f"❌ {error_msg}")


def display_room_details(room: Dict[str, Any]):
    """
    Display details for a single room including findings and images
    
    Args:
        room: Room data dictionary
    """
    st.markdown(f"**Room ID:** {room['room_id']}")
    st.markdown(f"**Risk Score:** {room.get('risk_score', 0)}")
    
    findings = room.get('findings', [])
    
    if not findings:
        st.info("No findings recorded for this room.")
        return
    
    st.markdown(f"**Findings ({len(findings)}):**")
    
    for finding in findings:
        finding_type = finding.get('finding_type', 'unknown')
        
        with st.container():
            st.markdown(f"**Finding ID:** {finding['finding_id']}")
            st.markdown(f"**Type:** {finding_type}")
            
            # Display text notes
            if finding_type == 'text' and finding.get('note_text'):
                st.text_area(
                    "Notes",
                    finding['note_text'],
                    key=f"notes_{finding['finding_id']}",
                    disabled=True,
                    height=100
                )
            
            # Display image information
            if finding_type == 'image':
                st.markdown(f"**Image:** {finding.get('image_filename', 'N/A')}")
                st.markdown(f"**Status:** {finding.get('processing_status', 'unknown')}")
                
                # Note: Actual image display would require retrieving from Snowflake stage
                # For now, just show the path
                if finding.get('image_stage_path'):
                    st.caption(f"Path: {finding['image_stage_path']}")
            
            # Display defect tags
            defect_tags = finding.get('defect_tags', [])
            
            if defect_tags:
                st.markdown("**Detected Defects:**")
                
                for tag in defect_tags:
                    defect_category = tag.get('defect_category', 'unknown')
                    severity_weight = tag.get('severity_weight', 0)
                    confidence_score = tag.get('confidence_score')
                    
                    # Color code by severity
                    if severity_weight >= 3:
                        tag_color = 'red'
                    elif severity_weight >= 2:
                        tag_color = 'orange'
                    else:
                        tag_color = 'gray'
                    
                    confidence_text = f" ({confidence_score:.2%})" if confidence_score else ""
                    st.markdown(f"- :{tag_color}[**{defect_category}**] (severity: {severity_weight}){confidence_text}")
            
            st.divider()


def main():
    """Main Streamlit application"""
    
    # Page configuration
    st.set_page_config(
        page_title="AI Home Inspection Dashboard",
        page_icon="🏠",
        layout="wide"
    )
    
    st.title("🏠 AI-Assisted Home Inspection Dashboard")
    
    # Initialize session state
    if 'selected_property' not in st.session_state:
        st.session_state['selected_property'] = None
    
    # Get Snowflake connection (would be configured via secrets or environment)
    # For now, this is a placeholder - actual implementation would use st.connection
    try:
        # This would be replaced with actual Snowflake connection
        # conn = st.connection("snowflake")
        # For testing purposes, we'll need to handle this gracefully
        
        # Placeholder for connection - in production this would be:
        # import snowflake.connector
        # conn = snowflake.connector.connect(...)
        
        st.warning("⚠️ Snowflake connection not configured. Please set up connection in Streamlit secrets.")
        st.info("To configure: Add Snowflake credentials to `.streamlit/secrets.toml`")
        
        # For demo purposes, show the UI structure without live data
        conn = None
        
    except Exception as e:
        error_msg = sanitize_error_message(e)
        st.error(f"❌ Connection Error: {error_msg}")
        st.stop()
    
    # Check if we have a valid connection
    if conn is None:
        st.info("Dashboard UI is ready. Connect to Snowflake to view inspection data.")
        
        # Show example UI structure
        st.subheader("Dashboard Features")
        st.markdown("""
        - **Property List View**: Browse all inspected properties with risk indicators
        - **Filtering**: Filter by risk level, defect type, or search terms
        - **Property Details**: View complete inspection data including rooms and findings
        - **Image Annotations**: See detected defects overlaid on inspection images
        - **Plain-Language Summaries**: AI-generated summaries of inspection results
        """)
        st.stop()
    
    # Initialize dashboard data access
    dashboard = DashboardData(conn)
    
    # Check if viewing property details
    if st.session_state.get('selected_property'):
        display_property_details(dashboard, st.session_state['selected_property'])
        return
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Risk level filter
    risk_level = st.sidebar.selectbox(
        "Risk Level",
        options=["All", "Low", "Medium", "High"],
        index=0
    )
    
    # Defect type filter
    defect_type = st.sidebar.selectbox(
        "Defect Type",
        options=[
            "All",
            "damp wall",
            "exposed wiring",
            "crack",
            "mold",
            "water leak",
            "electrical wiring"
        ],
        index=0
    )
    
    # Search input
    search_term = st.sidebar.text_input(
        "Search",
        placeholder="Search by location, ID, or summary..."
    )
    
    # Clear filters button
    if st.sidebar.button("Clear All Filters"):
        st.session_state['filters_cleared'] = True
        st.rerun()
    
    # Build filters dictionary
    filters = {}
    
    if risk_level != "All":
        filters['risk_level'] = risk_level
    
    if defect_type != "All":
        filters['defect_type'] = defect_type
    
    if search_term:
        filters['search_term'] = search_term
    
    # Display property list
    display_property_list(dashboard, filters)


if __name__ == "__main__":
    main()
