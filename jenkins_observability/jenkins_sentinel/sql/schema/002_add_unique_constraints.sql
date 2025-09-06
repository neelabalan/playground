-- Add unique constraint for builds table to prevent duplicate (pipeline_name, build_number) pairs
ALTER TABLE builds ADD CONSTRAINT unique_pipeline_build 
UNIQUE (pipeline_name, build_number);

-- Add unique constraint for build_queue table to prevent duplicate queue items
ALTER TABLE build_queue ADD CONSTRAINT unique_queue_item 
UNIQUE (job_path, build_number);
