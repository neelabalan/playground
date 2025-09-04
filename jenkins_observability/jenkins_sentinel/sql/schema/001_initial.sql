-- Schema for Jenkins Sentinel database

CREATE TABLE IF NOT EXISTS builds (
    id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(255) NOT NULL,
    build_number INTEGER NOT NULL CHECK (build_number > 0),
    build_start_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    build_end_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    status VARCHAR(50) NOT NULL DEFAULT 'unknown',
    total_duration FLOAT NOT NULL DEFAULT 0.0,
    steps_successful INTEGER NOT NULL DEFAULT 0,
    steps_failed INTEGER NOT NULL DEFAULT 0,
    steps_skipped INTEGER,
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    error_log TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
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
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_builds_pipeline_build ON builds(pipeline_name, build_number);
CREATE INDEX IF NOT EXISTS idx_builds_status ON builds(status);
CREATE INDEX IF NOT EXISTS idx_builds_build_start_time ON builds(build_start_time);
CREATE INDEX IF NOT EXISTS idx_build_queue_job_path ON build_queue(job_path);
CREATE INDEX IF NOT EXISTS idx_build_queue_collection_status ON build_queue(collection_status);
