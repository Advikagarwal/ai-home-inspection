# Streamlit + Snowflake Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              Streamlit Dashboard (Port 8501)                    │ │
│  │                  (src/dashboard_app.py)                         │ │
│  │                                                                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │ │
│  │  │ Property List│  │   Filtering  │  │    Export    │         │ │
│  │  │     View     │  │   & Search   │  │  (PDF/CSV)   │         │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘         │ │
│  │                                                                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │ │
│  │  │   Property   │  │     Room     │  │    Error     │         │ │
│  │  │   Details    │  │   Details    │  │ Sanitization │         │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘         │ │
│  └────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DATA ACCESS LAYER                               │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              Dashboard Data Access                              │ │
│  │              (src/dashboard_data.py)                            │ │
│  │                                                                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │ │
│  │  │get_property_ │  │get_property_ │  │ get_room_    │         │ │
│  │  │    list()    │  │  details()   │  │  details()   │         │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘         │ │
│  │                                                                  │ │
│  │  • Risk level filtering                                         │ │
│  │  • Defect type filtering                                        │ │
│  │  • Search functionality                                         │ │
│  │  • Multi-filter support                                         │ │
│  └────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CONNECTION MANAGEMENT                             │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              Snowflake Connection Handler                       │ │
│  │                                                                  │ │
│  │  1. Try Streamlit native connection (st.connection)            │ │
│  │  2. Fall back to snowflake-connector-python                    │ │
│  │  3. Check Streamlit secrets (.streamlit/secrets.toml)          │ │
│  │  4. Check environment variables                                │ │
│  │  5. Display setup instructions if not configured               │ │
│  └────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SNOWFLAKE DATABASE                              │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                        Data Tables                              │ │
│  │                                                                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │ │
│  │  │  Properties  │  │    Rooms     │  │   Findings   │         │ │
│  │  │              │  │              │  │              │         │ │
│  │  │ • property_id│  │ • room_id    │  │ • finding_id │         │ │
│  │  │ • location   │  │ • property_id│  │ • room_id    │         │ │
│  │  │ • risk_score │  │ • room_type  │  │ • note_text  │         │ │
│  │  │ • risk_cat   │  │ • risk_score │  │ • image_path │         │ │
│  │  │ • summary    │  │              │  │              │         │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘         │ │
│  │                                                                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │ │
│  │  │ Defect Tags  │  │Classification│  │  Error Log   │         │ │
│  │  │              │  │   History    │  │              │         │ │
│  │  │ • tag_id     │  │ • history_id │  │ • error_id   │         │ │
│  │  │ • finding_id │  │ • finding_id │  │ • error_type │         │ │
│  │  │ • defect_cat │  │ • defect_cat │  │ • message    │         │ │
│  │  │ • confidence │  │ • timestamp  │  │ • timestamp  │         │ │
│  │  │ • severity   │  │              │  │              │         │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Snowflake Cortex AI                          │ │
│  │                                                                  │ │
│  │  • CLASSIFY_TEXT: Text defect classification                   │ │
│  │  • AI_CLASSIFY: Image defect detection                         │ │
│  │  • SUMMARIZE: Natural language summary generation              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Snowflake Stage                              │ │
│  │                                                                  │ │
│  │  • Image storage                                                │ │
│  │  • Binary file format                                           │ │
│  │  • Directory enabled                                            │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Property List View
```
User → Streamlit UI → dashboard_data.get_property_list()
                    → SQL Query with filters
                    → Snowflake Database
                    → Properties + Defect Tags (if filtered)
                    → Format results
                    → Display in UI
```

### 2. Property Details View
```
User clicks "View Details"
    → Streamlit UI → dashboard_data.get_property_details(property_id)
                  → Query property info
                  → Query all rooms
                  → For each room:
                      → Query findings
                      → For each finding:
                          → Query defect tags
                  → Build hierarchical structure
                  → Display in UI
```

### 3. Filtering
```
User applies filter
    → Streamlit UI → Build filter dictionary
                  → dashboard_data.get_property_list(filters)
                  → Dynamic SQL query construction
                  → Add WHERE clauses
                  → Add JOINs if needed
                  → Execute query
                  → Return filtered results
```

### 4. Export
```
User clicks "Export"
    → Streamlit UI → Get property IDs
                  → Call export function (PDF or CSV)
                  → Query all data
                  → Format for export
                  → Generate file
                  → Provide download button
```

## Connection Flow

```
Dashboard starts
    ↓
Try st.connection("snowflake")
    ↓
Success? → Use connection
    ↓
Fail → Try snowflake.connector.connect()
    ↓
Check .streamlit/secrets.toml
    ↓
Found? → Use credentials
    ↓
Not found → Check environment variables
    ↓
Found? → Use credentials
    ↓
Not found → Display setup instructions
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SECURITY LAYERS                                 │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Layer 1: Error Sanitization                                   │ │
│  │  • Remove passwords, connection strings, API keys              │ │
│  │  • Remove file paths and system details                        │ │
│  │  • Generic error messages for users                            │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Layer 2: Secrets Management                                   │ │
│  │  • Credentials in .streamlit/secrets.toml (gitignored)         │ │
│  │  • Environment variables support                               │ │
│  │  • No hardcoded credentials                                    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Layer 3: Encrypted Connections                                │ │
│  │  • All Snowflake connections use TLS/SSL                       │ │
│  │  • Secure authentication                                       │ │
│  │  • SSO support available                                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Layer 4: Input Validation                                     │ │
│  │  • All user inputs validated                                   │ │
│  │  • SQL injection prevention                                    │ │
│  │  • Parameterized queries                                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Deployment Architecture

### Local Development
```
Developer Machine
    ↓
Python Virtual Environment
    ↓
Streamlit Server (localhost:8501)
    ↓
Snowflake Cloud (via internet)
```

### Streamlit Community Cloud
```
GitHub Repository
    ↓
Streamlit Cloud (automatic deployment)
    ↓
Streamlit Server (public URL)
    ↓
Snowflake Cloud (via internet)
```

### Snowflake Native App
```
Snowflake Account
    ↓
Streamlit in Snowflake (native)
    ↓
Same Snowflake Account (no external connection)
```

### Docker Container
```
Docker Host
    ↓
Container (Python + Streamlit)
    ↓
Exposed Port 8501
    ↓
Snowflake Cloud (via internet)
```

### Cloud Platform (AWS/Azure/GCP)
```
Cloud Container Service
    ↓
Load Balancer
    ↓
Container Instances (auto-scaling)
    ↓
Snowflake Cloud (via internet)
```

## Component Interaction

```
┌──────────────┐
│     User     │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│                    Streamlit UI                           │
│  • Property list with filters                            │
│  • Property details view                                 │
│  • Export functionality                                  │
└──────┬───────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│              Dashboard Data Layer                         │
│  • get_property_list(filters)                            │
│  • get_property_details(property_id)                     │
│  • get_room_details(room_id)                             │
└──────┬───────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│           Snowflake Connection                            │
│  • Connection management                                 │
│  • Query execution                                       │
│  • Result formatting                                     │
└──────┬───────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│              Snowflake Database                           │
│  • Tables (properties, rooms, findings, tags)            │
│  • Cortex AI functions                                   │
│  • Stage (images)                                        │
└──────────────────────────────────────────────────────────┘
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Layer                        │
│  • Streamlit 1.28+                                      │
│  • Python 3.8+                                          │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  Connection Layer                        │
│  • snowflake-connector-python 3.0+                      │
│  • Streamlit Snowflake connector                        │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   Database Layer                         │
│  • Snowflake Cloud Data Platform                        │
│  • Snowflake Cortex AI                                  │
└─────────────────────────────────────────────────────────┘
```

## File Structure

```
.
├── src/
│   ├── dashboard_app.py          # Main Streamlit application
│   ├── dashboard_data.py         # Data access layer
│   ├── data_ingestion.py         # Data ingestion
│   ├── ai_classification.py      # AI classification
│   ├── risk_scoring.py           # Risk scoring
│   ├── summary_generation.py     # Summary generation
│   └── export.py                 # Export functionality
│
├── .streamlit/
│   ├── secrets.toml.example      # Connection template
│   └── config.toml               # Streamlit configuration
│
├── tests/
│   ├── test_streamlit_integration.py  # Dashboard tests
│   └── ...                       # Other tests
│
├── schema/
│   └── init_schema.sql           # Database schema
│
├── docs/
│   ├── STREAMLIT_README.md       # Quick start
│   ├── STREAMLIT_DEPLOYMENT.md   # Deployment guide
│   └── STREAMLIT_ARCHITECTURE.md # This file
│
├── run_dashboard.sh              # Linux/Mac launcher
├── run_dashboard.bat             # Windows launcher
├── requirements.txt              # Python dependencies
└── README.md                     # Main documentation
```

## Performance Considerations

### Query Optimization
- Use materialized views for aggregations
- Index on frequently filtered columns
- Batch operations where possible

### Caching
- Streamlit automatically caches query results
- Use `@st.cache_data` for expensive operations
- Cache property lists and summaries

### Scalability
- Snowflake auto-scales compute resources
- Use appropriate warehouse sizes
- Implement pagination for large datasets

### Network
- Minimize round trips to database
- Fetch related data in single queries
- Use connection pooling

## Monitoring & Observability

### Application Metrics
- Dashboard load time
- Query execution time
- Error rates
- User activity

### Snowflake Metrics
- Query history
- Warehouse utilization
- Credit consumption
- Data transfer

### Logging
- Application logs (Streamlit)
- Database logs (Snowflake)
- Error logs (centralized)
- Audit logs (compliance)

---

**For implementation details, see:**
- `STREAMLIT_README.md` - Quick start
- `STREAMLIT_DEPLOYMENT.md` - Deployment
- `IMPLEMENTATION_SUMMARY.md` - Summary
