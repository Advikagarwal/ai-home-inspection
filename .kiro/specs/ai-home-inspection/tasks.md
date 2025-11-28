# Implementation Plan

- [x] 1. Set up Snowflake database schema and stages
  - Create properties, rooms, findings, defect_tags, classification_history, and error_log tables
  - Create Snowflake stage for image storage with appropriate permissions
  - Set up database constraints and foreign key relationships
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 10.4_

- [x] 1.1 Write property test for data storage round-trip
  - **Property 1: Data storage round-trip preservation**
  - **Validates: Requirements 1.1**

- [x] 1.2 Write property test for room-property linkage
  - **Property 2: Room-property linkage integrity**
  - **Validates: Requirements 1.2**

- [x] 1.3 Write property test for finding storage
  - **Property 3: Finding storage and retrieval**
  - **Validates: Requirements 1.3, 1.4**

- [x] 2. Implement data ingestion component
  - Create functions for ingesting property metadata with validation
  - Implement room creation with property linkage
  - Build text finding ingestion with room association
  - Implement image upload to Snowflake stage with finding record creation
  - Add input validation and error handling for all ingestion functions
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2.1 Write unit tests for data ingestion edge cases
  - Test missing required fields
  - Test invalid property references
  - Test corrupted image files
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 3. Implement AI classification component for text findings
  - Create SQL queries using SNOWFLAKE.CORTEX.CLASSIFY_TEXT for text classification
  - Implement defect category validation (damp wall, exposed wiring, crack, mold, water leak, none)
  - Build classification result storage with confidence scores and timestamps
  - Add error handling for classification failures with logging
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 10.1_

- [x] 3.1 Write property test for text classification categories
  - **Property 4: Text classification produces valid categories**
  - **Validates: Requirements 2.1, 2.2**

- [x] 3.2 Write property test for classification persistence
  - **Property 5: Classification results are persisted**
  - **Validates: Requirements 2.3, 3.3**

- [x] 3.3 Write property test for classification failure isolation
  - **Property 26: Classification failure isolation**
  - **Validates: Requirements 9.1**

- [ ] 4. Implement AI classification component for image findings
  - Create SQL queries using AI_CLASSIFY with TO_FILE for image classification
  - Implement image defect category validation (crack, water leak, mold, electrical wiring, none)
  - Build multi-tag support for images with multiple defects
  - Add error handling for missing or corrupted images
  - Store classification results with metadata
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 9.2_

- [ ] 4.1 Write property test for image classification categories
  - **Property 6: Image classification produces valid categories**
  - **Validates: Requirements 3.1, 3.2**

- [ ] 4.2 Write property test for multiple tag preservation
  - **Property 7: Multiple tags are preserved**
  - **Validates: Requirements 3.4**

- [ ] 4.3 Write unit tests for image error handling
  - Test corrupted image files
  - Test missing image files
  - _Requirements: 3.5, 9.2_

- [ ] 5. Implement risk scoring engine
  - Create severity weight mapping function (exposed wiring=3, damp wall=3, mold=3, water leak=2, crack=2)
  - Implement room risk score calculation by summing defect severity weights
  - Build property risk score aggregation from room scores
  - Implement risk categorization logic (Low < 5, Medium 5-9, High >= 10)
  - Store calculated scores in properties and rooms tables
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 10.2_

- [ ] 5.1 Write property test for severity weight correctness
  - **Property 8: Severity weights are correctly applied**
  - **Validates: Requirements 4.2**

- [ ] 5.2 Write property test for room risk calculation
  - **Property 9: Room risk score calculation**
  - **Validates: Requirements 4.1, 4.3**

- [ ] 5.3 Write property test for property risk aggregation
  - **Property 10: Property risk score aggregation**
  - **Validates: Requirements 4.4**

- [ ] 5.4 Write property test for risk categorization
  - **Property 11: Risk categorization correctness**
  - **Validates: Requirements 4.5**

- [ ] 5.5 Write property test for risk calculation traceability
  - **Property 29: Risk calculation traceability**
  - **Validates: Requirements 10.2**

- [ ] 5.6 Write unit tests for risk scoring edge cases
  - Test risk calculation with no defects
  - Test boundary values (scores 4, 5, 9, 10)
  - _Requirements: 4.5_

- [ ] 6. Create materialized views for performance optimization
  - Implement room_defect_summary materialized view
  - Implement property_defect_summary materialized view
  - Set up automatic refresh schedules or triggers
  - _Requirements: 4.1, 4.4_

- [ ] 7. Implement summary generation component
  - Build defect aggregation queries to collect counts by type
  - Create summary text formatting function with risk category and defect counts
  - Implement Cortex AI SUMMARIZE integration for natural language generation
  - Add fallback summary generation for AI failures
  - Ensure high-severity defects are prioritized in summaries
  - Store generated summaries in properties table
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 9.4, 10.3_

- [ ] 7.1 Write property test for summary completeness
  - **Property 12: Summary generation completeness**
  - **Validates: Requirements 5.1, 5.2**

- [ ] 7.2 Write property test for high-severity defect prioritization
  - **Property 13: High-severity defects appear in summaries**
  - **Validates: Requirements 5.5**

- [ ] 7.3 Write property test for source data preservation
  - **Property 30: Source data preservation**
  - **Validates: Requirements 10.3**

- [ ] 7.4 Write unit tests for summary edge cases
  - Test summary with no defects
  - Test summary with single defect type
  - Test fallback summary generation
  - _Requirements: 5.4, 9.4_

- [ ] 8. Implement dashboard data access layer
  - Create SQL queries for property list retrieval with risk indicators
  - Build property detail query including rooms, findings, and defect tags
  - Implement room detail query with images and annotations
  - Add filtering logic for risk level
  - Add filtering logic for defect type
  - Implement search functionality across location, identifier, and summary
  - Build multi-filter combination logic
  - Create filter reset functionality
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 8.1 Write property test for dashboard displays all properties
  - **Property 14: Dashboard displays all properties**
  - **Validates: Requirements 6.1**

- [ ] 8.2 Write property test for property list required fields
  - **Property 15: Property list contains required fields**
  - **Validates: Requirements 6.2**

- [ ] 8.3 Write property test for detail view completeness
  - **Property 16: Detail view shows complete data**
  - **Validates: Requirements 6.3**

- [ ] 8.4 Write property test for risk level filtering
  - **Property 17: Risk level filtering correctness**
  - **Validates: Requirements 7.1**

- [ ] 8.5 Write property test for defect type filtering
  - **Property 18: Defect type filtering correctness**
  - **Validates: Requirements 7.2**

- [ ] 8.6 Write property test for search matching
  - **Property 19: Search term matching**
  - **Validates: Requirements 7.3**

- [ ] 8.7 Write property test for multiple filter intersection
  - **Property 20: Multiple filter intersection**
  - **Validates: Requirements 7.4**

- [ ] 8.8 Write property test for filter clearing
  - **Property 21: Filter clearing restores full list**
  - **Validates: Requirements 7.5**

- [ ] 8.9 Write unit tests for filtering edge cases
  - Test filtering with no matching results
  - Test search with partial matches
  - _Requirements: 7.1, 7.2, 7.3_

- [ ] 9. Implement dashboard UI using Streamlit
  - Set up Streamlit application structure with Snowflake connection
  - Create property list view with risk indicators and color coding
  - Build property detail page with rooms, findings, and images
  - Implement room detail display with image annotations
  - Add risk level filter controls
  - Add defect type filter controls
  - Implement search input and functionality
  - Add filter clear button
  - Display plain-language summaries prominently
  - Add error notification display
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.5, 9.5_

- [ ] 9.1 Write property test for error message sanitization
  - **Property 27: Error messages hide sensitive details**
  - **Validates: Requirements 9.5**

- [ ] 10. Implement export component
  - Create PDF export function with property details, images, and annotations
  - Implement CSV export with all property, room, and finding records
  - Add export format validation and support
  - Build download mechanism for generated exports
  - Add error handling for export failures
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 10.1 Write property test for export completeness
  - **Property 22: Export completeness**
  - **Validates: Requirements 8.1**

- [ ] 10.2 Write property test for export format support
  - **Property 23: Export format support**
  - **Validates: Requirements 8.2**

- [ ] 10.3 Write property test for PDF image inclusion
  - **Property 24: PDF export includes images and annotations**
  - **Validates: Requirements 8.3**

- [ ] 10.4 Write property test for CSV record inclusion
  - **Property 25: CSV export includes all records**
  - **Validates: Requirements 8.4**

- [ ] 10.5 Write unit tests for export edge cases
  - Test export with no data
  - Test export with large datasets
  - _Requirements: 8.1_

- [ ] 11. Implement audit and traceability features
  - Add classification timestamp and confidence score recording
  - Implement classification history table population on reclassification
  - Build risk calculation detail storage
  - Add error logging to error_log table for all error types
  - Ensure referential integrity constraints are enforced
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 11.1 Write property test for classification metadata recording
  - **Property 28: Classification metadata is recorded**
  - **Validates: Requirements 10.1**

- [ ] 11.2 Write property test for referential integrity
  - **Property 31: Referential integrity maintenance**
  - **Validates: Requirements 10.4**

- [ ] 11.3 Write property test for classification history preservation
  - **Property 32: Classification history preservation**
  - **Validates: Requirements 10.5**

- [ ] 12. Implement comprehensive error handling
  - Add try-catch blocks for all AI classification calls with logging
  - Implement graceful degradation for missing images
  - Add default value handling for invalid risk calculation data
  - Create fallback mechanisms for summary generation failures
  - Ensure batch processing continues on individual failures
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 12.1 Write unit tests for error handling scenarios
  - Test classification failure handling
  - Test missing image handling
  - Test invalid data in risk calculation
  - Test summary generation fallback
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ] 13. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 14. Create sample data and end-to-end workflow testing
  - Generate sample properties with various defect combinations
  - Create test images with known defect types
  - Run complete workflow: ingest → classify → score → summarize → display
  - Verify dashboard displays correct information
  - Test export functionality with sample data
  - _Requirements: All_

- [ ] 14.1 Write integration tests for end-to-end workflows
  - Test complete inspection workflow
  - Test multi-property dashboard with filtering
  - Test export generation for various scenarios
  - _Requirements: All_

- [ ] 15. Performance optimization and final validation
  - Optimize batch classification queries
  - Verify materialized view refresh performance
  - Test dashboard load time with 100+ properties
  - Validate export generation for large properties
  - Review and optimize Snowflake warehouse sizing
  - _Requirements: All_

- [ ] 15.1 Write performance tests
  - Test batch classification of 1000+ findings
  - Test dashboard load time
  - Test large export generation
  - _Requirements: All_

- [ ] 16. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
