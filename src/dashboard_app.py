"""
Streamlit Dashboard UI for AI-Assisted Home Inspection Workspace
Interactive dashboard for viewing and filtering property inspection results
"""

import streamlit as st
import os
from typing import Optional, Dict, Any
from datetime import datetime

# Add src to path for imports
import sys
import os
sys.path.append(os.path.dirname(__file__))

# Import data access layer
from dashboard_data import DashboardData

# Import performance monitoring modules
try:
    from performance_monitor import get_performance_monitor
    from cache_manager import get_cache_manager
    from query_optimizer import get_query_optimizer
    from apm_monitor import get_apm_monitor
    PERFORMANCE_MONITORING_AVAILABLE = True
except ImportError:
    PERFORMANCE_MONITORING_AVAILABLE = False


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


def get_snowflake_connection():
    """
    Establish Snowflake connection using Streamlit secrets or environment variables
    
    Returns:
        Snowflake connection object or None if connection fails
    """
    try:
        # Try using Streamlit's native connection (Streamlit >= 1.28)
        try:
            conn = st.connection("snowflake", type="snowflake")
            return conn
        except Exception:
            pass
        
        # Fallback to snowflake-connector-python
        import snowflake.connector
        
        # Try to get credentials from Streamlit secrets
        if hasattr(st, 'secrets') and 'connections' in st.secrets and 'snowflake' in st.secrets['connections']:
            config = st.secrets['connections']['snowflake']
            
            conn_params = {
                'account': config['account'],
                'user': config['user'],
                'warehouse': config.get('warehouse'),
                'database': config.get('database'),
                'schema': config.get('schema', 'PUBLIC'),
            }
            
            # Add password or authenticator
            if 'password' in config:
                conn_params['password'] = config['password']
            elif 'authenticator' in config:
                conn_params['authenticator'] = config['authenticator']
            
            # Add optional parameters
            if 'role' in config:
                conn_params['role'] = config['role']
            
            conn = snowflake.connector.connect(**conn_params)
            return conn
        
        # Try environment variables as fallback
        conn_params = {
            'account': os.getenv('SNOWFLAKE_ACCOUNT'),
            'user': os.getenv('SNOWFLAKE_USER'),
            'password': os.getenv('SNOWFLAKE_PASSWORD'),
            'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
            'database': os.getenv('SNOWFLAKE_DATABASE', 'HOME_INSPECTION_DB'),
            'schema': os.getenv('SNOWFLAKE_SCHEMA', 'PUBLIC'),
        }
        
        # Check if we have minimum required parameters
        if all([conn_params['account'], conn_params['user'], conn_params['password']]):
            if 'role' in os.environ:
                conn_params['role'] = os.getenv('SNOWFLAKE_ROLE')
            
            conn = snowflake.connector.connect(**conn_params)
            return conn
        
        return None
        
    except Exception as e:
        st.error(f"Connection error: {sanitize_error_message(e)}")
        return None


def show_connection_instructions():
    """Display instructions for setting up Snowflake connection"""
    st.warning("⚠️ Snowflake connection not configured")
    
    st.markdown("""
    ### Setup Instructions
    
    Choose one of the following methods to connect to Snowflake:
    
    #### Option 1: Streamlit Secrets (Recommended for Streamlit Cloud)
    
    1. Create a file `.streamlit/secrets.toml` in your project root
    2. Add your Snowflake credentials:
    
    ```toml
    [connections.snowflake]
    account = "your-account-identifier"
    user = "your-username"
    password = "your-password"
    warehouse = "COMPUTE_WH"
    database = "HOME_INSPECTION_DB"
    schema = "PUBLIC"
    ```
    
    #### Option 2: Environment Variables
    
    Set the following environment variables:
    
    ```bash
    export SNOWFLAKE_ACCOUNT="your-account-identifier"
    export SNOWFLAKE_USER="your-username"
    export SNOWFLAKE_PASSWORD="your-password"
    export SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
    export SNOWFLAKE_DATABASE="HOME_INSPECTION_DB"
    export SNOWFLAKE_SCHEMA="PUBLIC"
    ```
    
    #### Option 3: SSO Authentication
    
    For SSO/browser-based authentication, use:
    
    ```toml
    [connections.snowflake]
    account = "your-account-identifier"
    user = "your-username"
    authenticator = "externalbrowser"
    warehouse = "COMPUTE_WH"
    database = "HOME_INSPECTION_DB"
    schema = "PUBLIC"
    ```
    """)
    
    st.info("📝 See `.streamlit/secrets.toml.example` for a template")
    
    # Show example UI structure
    with st.expander("Preview Dashboard Features"):
        st.markdown("""
        - **Property List View**: Browse all inspected properties with risk indicators
        - **Filtering**: Filter by risk level, defect type, or search terms
        - **Property Details**: View complete inspection data including rooms and findings
        - **Image Annotations**: See detected defects overlaid on inspection images
        - **Plain-Language Summaries**: AI-generated summaries of inspection results
        - **Export**: Download reports as PDF or CSV
        """)


def display_performance_monitor():
    """Display performance monitoring dashboard"""
    if not PERFORMANCE_MONITORING_AVAILABLE:
        st.error("Performance monitoring modules not available")
        return
    
    st.header("📊 Performance Monitor")
    
    # Get monitoring instances
    try:
        apm_monitor = get_apm_monitor()
        performance_monitor = get_performance_monitor()
        cache_manager = get_cache_manager()
        query_optimizer = get_query_optimizer()
    except Exception as e:
        st.error(f"Failed to initialize monitoring: {sanitize_error_message(e)}")
        return
    
    # Get dashboard status
    try:
        status = apm_monitor.get_dashboard_status()
    except Exception as e:
        st.error(f"Failed to get status: {sanitize_error_message(e)}")
        return
    
    # Overall status
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_color = {"healthy": "🟢", "warning": "🟡", "critical": "🔴"}
        st.metric(
            "System Status", 
            f"{status_color.get(status['overall_status'], '⚪')} {status['overall_status'].title()}"
        )
    
    with col2:
        uptime_hours = status['uptime_seconds'] / 3600
        st.metric("Uptime", f"{uptime_hours:.1f} hours")
    
    with col3:
        cache_hit_rate = status['cache']['hit_rate']
        st.metric("Cache Hit Rate", f"{cache_hit_rate:.1%}")
    
    with col4:
        avg_response = status['performance']['avg_duration']
        st.metric("Avg Response Time", f"{avg_response:.2f}s")
    
    # Tabs for different monitoring views
    tab1, tab2, tab3, tab4 = st.tabs(["System Metrics", "Query Performance", "Health Checks", "Alerts"])
    
    with tab1:
        st.subheader("System Resource Usage")
        
        # System metrics
        sys_metrics = status['system_metrics']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("CPU Usage", f"{sys_metrics['cpu_percent']:.1f}%")
        with col2:
            st.metric("Memory Usage", f"{sys_metrics['memory_percent']:.1f}%")
        with col3:
            st.metric("Disk Usage", f"{sys_metrics['disk_percent']:.1f}%")
        
        # Resource usage bars
        import plotly.graph_objects as go
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Usage %',
            x=['CPU', 'Memory', 'Disk'],
            y=[sys_metrics['cpu_percent'], sys_metrics['memory_percent'], sys_metrics['disk_percent']],
            marker_color=['red' if x > 80 else 'orange' if x > 60 else 'green' 
                         for x in [sys_metrics['cpu_percent'], sys_metrics['memory_percent'], sys_metrics['disk_percent']]]
        ))
        fig.update_layout(title="Resource Usage", yaxis_title="Percentage")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Query Performance Analysis")
        
        perf_data = status['performance']
        
        # Performance metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Queries", perf_data['total_queries'])
        with col2:
            st.metric("Success Rate", f"{perf_data['success_rate']:.1%}")
        with col3:
            st.metric("Avg Duration", f"{perf_data['avg_duration']:.2f}s")
        
        # Query types performance
        if perf_data['query_types']:
            st.subheader("Performance by Query Type")
            
            query_types_df = pd.DataFrame([
                {
                    'Query Type': qtype,
                    'Count': stats['count'],
                    'Avg Duration (s)': stats['avg_duration'],
                    'Max Duration (s)': stats['max_duration']
                }
                for qtype, stats in perf_data['query_types'].items()
            ])
            
            st.dataframe(query_types_df, use_container_width=True)
        
        # Slowest queries
        if perf_data['slowest_queries']:
            st.subheader("Slowest Queries")
            
            slowest_df = pd.DataFrame(perf_data['slowest_queries'])
            st.dataframe(slowest_df, use_container_width=True)
    
    with tab3:
        st.subheader("Health Check Results")
        
        health_checks = status['health_checks']
        
        for component, result in health_checks.items():
            status_icon = {"healthy": "✅", "warning": "⚠️", "critical": "❌"}
            
            with st.expander(f"{status_icon.get(result['status'], '❓')} {component.title()}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Status:** {result['status'].title()}")
                    st.write(f"**Message:** {result['message']}")
                with col2:
                    st.write(f"**Response Time:** {result['response_time_ms']:.1f}ms")
                    st.write(f"**Last Check:** {result['timestamp']}")
                
                if result.get('details'):
                    st.json(result['details'])
    
    with tab4:
        st.subheader("Active Alerts")
        
        active_alerts = status['active_alerts']
        
        if not active_alerts:
            st.success("No active alerts")
        else:
            for alert in active_alerts:
                severity_color = {"critical": "🔴", "warning": "🟡", "info": "🔵"}
                
                st.error(f"{severity_color.get(alert['severity'], '⚪')} **{alert['component'].title()}**: {alert['message']}")
                
                if 'value' in alert and 'threshold' in alert:
                    st.write(f"Current: {alert['value']}, Threshold: {alert['threshold']}")
    
    # Performance insights and recommendations
    st.header("🎯 Optimization Recommendations")
    
    try:
        insights = query_optimizer.get_query_performance_insights()
        recommendations = insights.get('optimization_recommendations', [])
        
        if not recommendations:
            st.success("No optimization recommendations at this time")
        else:
            for rec in recommendations:
                priority_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                
                with st.expander(f"{priority_color.get(rec['priority'], '⚪')} {rec['title']}"):
                    st.write(f"**Priority:** {rec['priority'].title()}")
                    st.write(f"**Description:** {rec['description']}")
                    st.write(f"**Recommended Action:** {rec['action']}")
    
    except Exception as e:
        st.error(f"Failed to get recommendations: {sanitize_error_message(e)}")
    
    # Auto-refresh
    if st.button("🔄 Refresh Metrics"):
        st.rerun()
    
    # Auto-refresh every 30 seconds
    import time
    time.sleep(30)
    st.rerun()


def main():
    """Main Streamlit application"""
    
    # Page configuration
    st.set_page_config(
        page_title="AI Home Inspection Dashboard",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🏠 AI-Assisted Home Inspection Dashboard")
    st.caption("Powered by Snowflake Cortex AI")
    
    # Initialize session state
    if 'selected_property' not in st.session_state:
        st.session_state['selected_property'] = None
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 'Properties'
    
    # Navigation
    st.sidebar.title("Navigation")
    pages = ["Properties", "Performance Monitor"] if PERFORMANCE_MONITORING_AVAILABLE else ["Properties"]
    current_page = st.sidebar.radio("Go to", pages, index=pages.index(st.session_state['current_page']))
    st.session_state['current_page'] = current_page
    
    # Get Snowflake connection
    conn = get_snowflake_connection()
    
    # Check if we have a valid connection
    if conn is None:
        show_connection_instructions()
        st.stop()
    
    # Connection successful
    st.success("✅ Connected to Snowflake")
    
    # Route to appropriate page
    if current_page == "Performance Monitor" and PERFORMANCE_MONITORING_AVAILABLE:
        display_performance_monitor()
        return
    
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
    
    # Export functionality in sidebar
    st.sidebar.divider()
    st.sidebar.header("Export")
    
    export_format = st.sidebar.selectbox(
        "Export Format",
        options=["PDF", "CSV"],
        index=0
    )
    
    if st.sidebar.button("Export All Properties"):
        try:
            from src.export import export_pdf, export_csv
            
            # Get all properties (unfiltered)
            all_properties = dashboard.get_property_list()
            property_ids = [p['property_id'] for p in all_properties]
            
            if not property_ids:
                st.sidebar.warning("No properties to export")
            else:
                with st.spinner(f"Generating {export_format} export..."):
                    if export_format == "PDF":
                        # Export first property as PDF (for demo)
                        pdf_bytes = export_pdf(conn, property_ids[0])
                        st.sidebar.download_button(
                            label="Download PDF",
                            data=pdf_bytes,
                            file_name=f"inspection_{property_ids[0]}.pdf",
                            mime="application/pdf"
                        )
                    else:  # CSV
                        csv_bytes = export_csv(conn, property_ids)
                        st.sidebar.download_button(
                            label="Download CSV",
                            data=csv_bytes,
                            file_name="inspections_export.csv",
                            mime="text/csv"
                        )
                
                st.sidebar.success(f"✅ {export_format} export ready!")
        
        except Exception as e:
            error_msg = sanitize_error_message(e)
            st.sidebar.error(f"Export failed: {error_msg}")


if __name__ == "__main__":
    main()
