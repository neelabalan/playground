-- name: CreateBuild :one
INSERT INTO builds (
    pipeline_name,
    build_number,
    build_start_time,
    build_end_time,
    status,
    building_time_seconds,
    error_log,
    triggered_by,
    blocked_time_seconds,
    buildable_time_seconds,
    waiting_time_seconds
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
) ON CONFLICT (pipeline_name, build_number) 
DO UPDATE SET
    build_start_time = EXCLUDED.build_start_time,
    build_end_time = EXCLUDED.build_end_time,
    status = EXCLUDED.status,
    building_time_seconds = EXCLUDED.building_time_seconds,
    error_log = EXCLUDED.error_log,
    triggered_by = EXCLUDED.triggered_by,
    blocked_time_seconds = EXCLUDED.blocked_time_seconds,
    buildable_time_seconds = EXCLUDED.buildable_time_seconds,
    waiting_time_seconds = EXCLUDED.waiting_time_seconds,
    updated_at = NOW()
RETURNING *;

-- name: GetBuildByID :one
SELECT * FROM builds WHERE id = $1;

-- name: GetBuildsByPipeline :many
SELECT * FROM builds 
WHERE pipeline_name = $1 
ORDER BY build_number DESC 
LIMIT $2;

-- name: GetBuildsByPipelineAndStatus :many
SELECT * FROM builds 
WHERE pipeline_name = $1 AND status = $2 
ORDER BY build_number DESC 
LIMIT $3;

-- name: UpdateBuildStatus :one
UPDATE builds 
SET status = $2, updated_at = NOW() 
WHERE id = $1 
RETURNING *;

-- name: DeleteBuild :exec
DELETE FROM builds WHERE id = $1;

-- name: GetLatestBuilds :many
SELECT * FROM builds 
ORDER BY build_start_time DESC 
LIMIT $1;

-- name: GetBuildsInDateRange :many
SELECT * FROM builds 
WHERE build_start_time >= $1 AND build_start_time <= $2 
ORDER BY build_start_time DESC;

-- name: CreateBuildQueueItem :one
INSERT INTO build_queue (
    job_path,
    build_number,
    last_attempt_at,
    error_message,
    collection_time,
    collection_status
) VALUES (
    $1, $2, $3, $4, $5, $6
) ON CONFLICT (job_path, build_number) 
DO UPDATE SET
    last_attempt_at = EXCLUDED.last_attempt_at,
    collection_time = EXCLUDED.collection_time,
    collection_status = EXCLUDED.collection_status,
    updated_at = NOW()
RETURNING *;

-- name: GetPendingQueueItems :many
SELECT * FROM build_queue 
WHERE collection_status = 'pending' 
ORDER BY collection_time ASC;

-- name: GetQueueItemByJobAndBuild :one
SELECT * FROM build_queue 
WHERE job_path = $1 AND build_number = $2;

-- name: UpdateQueueItemStatus :one
UPDATE build_queue 
SET collection_status = $2, updated_at = NOW() 
WHERE id = $1 
RETURNING *;

-- name: DeleteQueueItem :exec
DELETE FROM build_queue WHERE id = $1;

-- name: GetTimeSeriesForPipeline :many
SELECT 
    build_start_time as timestamp,
    building_time_seconds,
    blocked_time_seconds,
    buildable_time_seconds,
    waiting_time_seconds
FROM builds 
WHERE pipeline_name = $1 
AND build_start_time >= $2 
AND status = 'success'
ORDER BY build_start_time ASC;

