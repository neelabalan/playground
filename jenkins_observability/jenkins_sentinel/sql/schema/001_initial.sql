-- Schema for Jenkins Sentinel database

CREATE TABLE IF NOT EXISTS builds (
    id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(255) NOT NULL,
    build_number INTEGER NOT NULL CHECK (build_number > 0),
    build_start_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    build_end_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    status VARCHAR(50) NOT NULL DEFAULT 'unknown',
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    error_log TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    triggered_by VARCHAR(255) DEFAULT NULL,
    building_time_seconds FLOAT DEFAULT NULL,
    blocked_time_seconds FLOAT DEFAULT NULL,
    buildable_time_seconds FLOAT DEFAULT NULL,
    waiting_time_seconds FLOAT DEFAULT NULL,
    CONSTRAINT unique_pipeline_build UNIQUE (pipeline_name, build_number)
);

CREATE TABLE IF NOT EXISTS build_queue (
    id SERIAL PRIMARY KEY,
    job_path VARCHAR(255) NOT NULL,
    build_number INTEGER NOT NULL CHECK (build_number > 0),
    last_attempt_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    error_message TEXT,
    collection_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    collection_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_queue_item UNIQUE (job_path, build_number)
);

-- Column comments for documentation
COMMENT ON COLUMN builds.triggered_by IS 'Username or ID of who/what triggered the build';
COMMENT ON COLUMN builds.building_time_seconds IS 'Actual build execution time in seconds including subtasks (from executingTimeMillis)';
COMMENT ON COLUMN builds.blocked_time_seconds IS 'Time in seconds blocked waiting for resources including subtasks';
COMMENT ON COLUMN builds.buildable_time_seconds IS 'Time in seconds buildable but waiting for executor including subtasks';
COMMENT ON COLUMN builds.waiting_time_seconds IS 'Time in seconds in waiting state including subtasks';

-- Indexes for performance on common queries
CREATE INDEX IF NOT EXISTS idx_builds_pipeline_building_time ON builds(pipeline_name, building_time_seconds);
CREATE INDEX IF NOT EXISTS idx_builds_pipeline_build_start ON builds(pipeline_name, build_start_time);
