-- name: CreateBuild :one
INSERT INTO builds (
    pipeline_name,
    build_number,
    build_start_time,
    build_end_time,
    status,
    total_duration,
    steps_successful,
    steps_failed,
    steps_skipped,
    error_log
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
) RETURNING *;

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
) RETURNING *;

-- name: GetPendingQueueItems :many
SELECT * FROM build_queue 
WHERE collection_status = 'pending' 
ORDER BY collection_time ASC;

-- name: UpdateQueueItemStatus :one
UPDATE build_queue 
SET collection_status = $2, updated_at = NOW() 
WHERE id = $1 
RETURNING *;

-- name: DeleteQueueItem :exec
DELETE FROM build_queue WHERE id = $1;
