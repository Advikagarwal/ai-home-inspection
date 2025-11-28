# AI-Assisted Home Inspection Workspace

An AI-powered system for automatically analyzing home inspection data to identify construction defects, assess risk levels, and generate human-readable reports. This AI-for-Good application helps home buyers, tenants, and regulators identify unsafe housing conditions early.

## Overview

This system leverages Snowflake's Cortex AI capabilities to:
- **Automatically tag defects** in text notes and images using AI/ML
- **Calculate risk scores** for rooms and properties based on defect severity
- **Generate plain-language summaries** for easy understanding
- **Provide an interactive dashboard** for viewing and filtering inspection results

## Features

- 🤖 AI-powered defect classification for text and images
- 📊 Risk scoring with Low/Medium/High categorization
- 📝 Natural language summary generation
- 🎯 Interactive dashboard with filtering and search
- 📄 Export capabilities (PDF and CSV)
- 🔍 Comprehensive audit trails and traceability

## Technology Stack

- **Database**: Snowflake
- **AI/ML**: Snowflake Cortex AI (CLASSIFY_TEXT, AI_CLASSIFY, SUMMARIZE)
- **Backend**: Python with Snowflake Connector
- **UI**: Streamlit (recommended)
- **Testing**: pytest, Hypothesis (property-based testing)

## Project Structure

```
.
├── .kiro/specs/ai-home-inspection/  # Specification documents
│   ├── requirements.md               # User stories and acceptance criteria
│   ├── design.md                     # Architecture and design
│   └── tasks.md                      # Implementation task list
├── schema/                           # Database schema
│   └── init_schema.sql              # Table and stage definitions
├── src/                              # Source code
│   ├── data_ingestion.py            # Data ingestion component
│   └── ai_classification.py         # AI classification component
├── tests/                            # Test suite
│   ├── conftest.py                  # Test configuration
│   ├── test_data_storage.py         # Property-based tests
│   └── test_text_classification.py  # Classification tests
└── requirements.txt                  # Python dependencies
```

## Getting Started

### Prerequisites

- Snowflake account with Cortex AI enabled
- Python 3.8+
- pip or conda for package management

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-home-inspection
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure Snowflake connection:
```bash
# Set up your Snowflake credentials
export SNOWFLAKE_ACCOUNT=<your-account>
export SNOWFLAKE_USER=<your-user>
export SNOWFLAKE_PASSWORD=<your-password>
export SNOWFLAKE_WAREHOUSE=<your-warehouse>
export SNOWFLAKE_DATABASE=<your-database>
export SNOWFLAKE_SCHEMA=<your-schema>
```

4. Initialize the database schema:
```bash
# Run the schema initialization script
snowsql -f schema/init_schema.sql
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run property-based tests only
pytest -k "property"
```

## Implementation Status

This project follows a spec-driven development approach. See `.kiro/specs/ai-home-inspection/tasks.md` for the complete implementation plan and current progress.

## AI for Good Impact

This solution empowers stakeholders to catch safety issues early:
- **Saves time**: AI-automated tagging reduces manual inspection review time
- **Improves accuracy**: AI can spot defects that casual review might miss
- **Increases accessibility**: Plain-language summaries make findings understandable to non-experts
- **Promotes safety**: Early detection helps families avoid unsafe homes and enables proactive enforcement

## Documentation

- [Requirements](/.kiro/specs/ai-home-inspection/requirements.md) - User stories and acceptance criteria
- [Design](/.kiro/specs/ai-home-inspection/design.md) - Architecture and technical design
- [Tasks](/.kiro/specs/ai-home-inspection/tasks.md) - Implementation plan

## Contributing

This project uses property-based testing to ensure correctness. When contributing:
1. Follow the task list in `tasks.md`
2. Write property-based tests for universal properties
3. Write unit tests for specific examples and edge cases
4. Ensure all tests pass before submitting

## License

[Add your license here]

## Contact

For questions or support, please contact [your contact information].
