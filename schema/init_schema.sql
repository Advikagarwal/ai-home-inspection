-- AI-Assisted Home Inspection Workspace - Database Schema
-- This script creates all necessary tables, stages, and constraints

-- Create properties table
CREATE TABLE IF NOT EXISTS properties (
    property_id VARCHAR PRIMARY KEY,
    location VARCHAR NOT NULL,
    inspection_date DATE NOT NULL,
    risk_score INTEGER,
    risk_category VARCHAR,
    summary_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create rooms table with foreign key to properties
CREATE TABLE IF NOT EXISTS rooms (
    room_id VARCHAR PRIMARY KEY,
    property_id VARCHAR NOT NULL,
    room_type VARCHAR NOT NULL,
    room_location VARCHAR,
    risk_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties(property_id)
);

-- Create findings table with foreign key to rooms
CREATE TABLE IF NOT EXISTS findings (
    finding_id VARCHAR PRIMARY KEY,
    room_id VARCHAR NOT NULL,
    finding_type VARCHAR NOT NULL, -- 'text' or 'image'
    note_text TEXT,
    image_filename VARCHAR,
    image_stage_path VARCHAR,
    processing_status VARCHAR DEFAULT 'pending', -- 'pending', 'processed', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);

-- Create defect_tags table with foreign key to findings
CREATE TABLE IF NOT EXISTS defect_tags (
    tag_id VARCHAR PRIMARY KEY,
    finding_id VARCHAR NOT NULL,
    defect_category VARCHAR NOT NULL,
    confidence_score FLOAT,
    severity_weight INTEGER,
    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (finding_id) REFERENCES findings(finding_id)
);

-- Create classification_history table for audit trail
CREATE TABLE IF NOT EXISTS classification_history (
    history_id VARCHAR PRIMARY KEY,
    finding_id VARCHAR NOT NULL,
    defect_category VARCHAR NOT NULL,
    confidence_score FLOAT,
    classification_method VARCHAR, -- 'text_ai', 'image_ai', 'manual'
    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (finding_id) REFERENCES findings(finding_id)
);

-- Create error_log table for centralized error tracking
CREATE TABLE IF NOT EXISTS error_log (
    error_id VARCHAR PRIMARY KEY,
    error_type VARCHAR NOT NULL,
    error_message TEXT NOT NULL,
    entity_type VARCHAR, -- 'property', 'room', 'finding'
    entity_id VARCHAR,
    stack_trace TEXT,
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Snowflake stage for image storage
CREATE STAGE IF NOT EXISTS inspections
    DIRECTORY = (ENABLE = TRUE)
    FILE_FORMAT = (TYPE = 'BINARY');

-- Create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_rooms_property ON rooms(property_id);
CREATE INDEX IF NOT EXISTS idx_findings_room ON findings(room_id);
CREATE INDEX IF NOT EXISTS idx_defect_tags_finding ON defect_tags(finding_id);
CREATE INDEX IF NOT EXISTS idx_classification_history_finding ON classification_history(finding_id);
