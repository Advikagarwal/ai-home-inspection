# Requirements Document

## Introduction

The AI-Assisted Home Inspection Workspace is a system designed to automatically analyze home inspection data (text notes and images) to identify construction defects, assess risk levels, and generate human-readable reports. This AI-for-Good application helps home buyers, tenants, and regulators identify unsafe housing conditions early by leveraging Snowflake's Cortex AI capabilities to tag defects, compute risk scores, and produce actionable summaries.

## Glossary

- **System**: The AI-Assisted Home Inspection Workspace
- **Property**: A residential building or unit being inspected
- **Room**: A distinct space within a Property (e.g., kitchen, bedroom)
- **Finding**: A recorded defect observation consisting of text notes and/or images
- **Defect Tag**: A classification label applied to a Finding (e.g., "crack", "damp wall", "exposed wiring")
- **Risk Score**: A numerical or categorical assessment of safety risk for a Room or Property
- **Snowflake Stage**: A cloud storage location in Snowflake for storing inspection images
- **Cortex AI**: Snowflake's built-in AI/ML functions for classification and summarization
- **Inspector**: A user who conducts property inspections and uploads data
- **Stakeholder**: A user who reviews inspection results (buyer, tenant, regulator)

## Requirements

### Requirement 1

**User Story:** As an inspector, I want to upload inspection data including property details, room information, text notes, and images, so that the system can analyze defects automatically.

#### Acceptance Criteria

1. WHEN an inspector provides property metadata THEN the System SHALL store the property record with unique identifier, location, and inspection date
2. WHEN an inspector provides room information for a Property THEN the System SHALL create room records linked to that Property with room type and location details
3. WHEN an inspector uploads text notes describing defects THEN the System SHALL store each note as a Finding linked to the corresponding Room
4. WHEN an inspector uploads inspection images THEN the System SHALL store each image file in a Snowflake Stage and create a Finding record with the file reference
5. WHERE images include metadata THEN the System SHALL preserve the metadata associations with the corresponding Room and Property

### Requirement 2

**User Story:** As a stakeholder, I want the system to automatically classify text notes into defect categories, so that I can quickly understand what issues were documented without reading all notes manually.

#### Acceptance Criteria

1. WHEN the System processes a text Finding THEN the System SHALL apply Cortex AI text classification to assign a Defect Tag from predefined categories
2. THE System SHALL support defect categories including "damp wall", "exposed wiring", "crack", "mold", "water leak", and "none"
3. WHEN text classification completes THEN the System SHALL store the assigned Defect Tag with the Finding record
4. WHEN a text Finding contains ambiguous content THEN the System SHALL assign the most probable Defect Tag based on classification confidence

### Requirement 3

**User Story:** As a stakeholder, I want the system to automatically analyze inspection images and detect visible defects, so that visual evidence of problems is systematically identified.

#### Acceptance Criteria

1. WHEN the System processes an image Finding THEN the System SHALL apply Cortex AI image classification to detect defects visible in the image
2. THE System SHALL classify images using categories including "crack", "water leak", "mold", "electrical wiring", and "none"
3. WHEN image classification completes THEN the System SHALL store the detected Defect Tags with the image Finding record
4. WHEN an image contains multiple defect types THEN the System SHALL record all detected Defect Tags for that image
5. WHEN an image file is corrupted or unreadable THEN the System SHALL handle the error gracefully and log the failure without blocking other processing

### Requirement 4

**User Story:** As a stakeholder, I want the system to calculate a risk score for each room and property based on detected defects, so that I can prioritize which properties require immediate attention.

#### Acceptance Criteria

1. WHEN the System aggregates Findings for a Room THEN the System SHALL compute a numerical risk score based on defect severity weights
2. THE System SHALL assign severity weights where "exposed wiring" equals 3, "damp wall" equals 3, "mold" equals 3, "water leak" equals 2, and "crack" equals 2
3. WHEN computing a Room risk score THEN the System SHALL sum the severity weights of all Defect Tags found in that Room
4. WHEN the System aggregates Room scores for a Property THEN the System SHALL compute a Property risk score as the sum of all Room scores
5. WHEN a Property risk score is computed THEN the System SHALL categorize it as "Low" (score less than 5), "Medium" (score 5 to 9), or "High" (score 10 or greater)

### Requirement 5

**User Story:** As a stakeholder, I want the system to generate plain-language summaries of inspection results, so that I can understand the key findings without technical expertise.

#### Acceptance Criteria

1. WHEN the System completes defect analysis for a Property THEN the System SHALL generate a human-readable summary text
2. WHEN generating a summary THEN the System SHALL include the risk category, count of affected rooms, and primary defect types
3. WHEN generating a summary THEN the System SHALL use Cortex AI summarization functions to produce concise natural language output
4. WHEN a Property has no significant defects THEN the System SHALL generate a summary indicating low risk with no major issues found
5. WHEN a Property has multiple defect types THEN the System SHALL prioritize the most severe defects in the summary text

### Requirement 6

**User Story:** As a stakeholder, I want to view an interactive dashboard showing all properties with their risk indicators, so that I can quickly identify which properties need review.

#### Acceptance Criteria

1. WHEN a stakeholder accesses the dashboard THEN the System SHALL display a list of all Properties with their risk categories and scores
2. WHEN displaying the property list THEN the System SHALL show each Property's identifier, location, inspection date, risk category, and risk score
3. WHEN a stakeholder selects a Property from the list THEN the System SHALL display detailed information including all Rooms, Findings, and Defect Tags
4. WHEN displaying Property details THEN the System SHALL show the plain-language summary prominently
5. WHEN displaying Room details THEN the System SHALL show all associated images with their detected Defect Tags as overlays or captions

### Requirement 7

**User Story:** As a stakeholder, I want to filter and search properties by defect type or risk level, so that I can focus on specific types of issues or high-priority cases.

#### Acceptance Criteria

1. WHEN a stakeholder applies a risk level filter THEN the System SHALL display only Properties matching the selected risk category
2. WHEN a stakeholder applies a defect type filter THEN the System SHALL display only Properties containing at least one Finding with the specified Defect Tag
3. WHEN a stakeholder enters a search term THEN the System SHALL return Properties matching the term in location, identifier, or summary text
4. WHEN multiple filters are applied THEN the System SHALL display Properties satisfying all filter conditions
5. WHEN a stakeholder clears filters THEN the System SHALL restore the full unfiltered property list

### Requirement 8

**User Story:** As a stakeholder, I want to export inspection reports and data, so that I can share findings with other parties or maintain records outside the system.

#### Acceptance Criteria

1. WHEN a stakeholder requests a Property report export THEN the System SHALL generate a document containing all Property details, Room information, Defect Tags, risk scores, and summary text
2. WHEN exporting data THEN the System SHALL support common formats including PDF and CSV
3. WHEN exporting a PDF report THEN the System SHALL include inspection images with visible Defect Tag annotations
4. WHEN exporting CSV data THEN the System SHALL include all Property, Room, and Finding records with their associated classifications
5. WHEN an export completes THEN the System SHALL provide a download link or file to the stakeholder

### Requirement 9

**User Story:** As a system administrator, I want the system to handle errors gracefully during AI processing, so that individual failures do not prevent the analysis of other inspection data.

#### Acceptance Criteria

1. WHEN Cortex AI classification fails for a Finding THEN the System SHALL log the error with details and continue processing other Findings
2. WHEN an image file cannot be accessed from the Snowflake Stage THEN the System SHALL record the failure and mark the Finding as unprocessed
3. WHEN risk score calculation encounters invalid data THEN the System SHALL use default values or skip the invalid record and log a warning
4. WHEN summary generation fails THEN the System SHALL provide a basic fallback summary using the raw aggregated data
5. WHEN the System encounters errors THEN the System SHALL display error notifications to users without exposing sensitive system details

### Requirement 10

**User Story:** As a developer, I want the system to maintain data integrity and traceability, so that all AI-generated classifications and scores can be audited and verified.

#### Acceptance Criteria

1. WHEN the System assigns a Defect Tag THEN the System SHALL record the classification timestamp and confidence score
2. WHEN the System computes a risk score THEN the System SHALL store the calculation details including individual defect contributions
3. WHEN the System generates a summary THEN the System SHALL preserve the source data used to create the summary
4. THE System SHALL maintain referential integrity between Properties, Rooms, and Findings at all times
5. WHEN a Finding is updated or reclassified THEN the System SHALL preserve the history of previous classifications for audit purposes
