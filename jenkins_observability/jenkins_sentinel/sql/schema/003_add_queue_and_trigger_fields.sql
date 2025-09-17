-- Add queue wait time and trigger information to builds table

ALTER TABLE builds 
ADD COLUMN queue_wait_time FLOAT DEFAULT NULL,
ADD COLUMN triggered_by VARCHAR(255) DEFAULT NULL;

-- Add comments for documentation
COMMENT ON COLUMN builds.queue_wait_time IS 'Time in seconds the build waited in queue before execution';
COMMENT ON COLUMN builds.triggered_by IS 'Username or ID of who/what triggered the build';