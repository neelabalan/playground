-- name: CreateAnomalyScore :one
INSERT INTO anomaly_scores (
    pipeline_name,
    build_number,
    metric_name,
    detector_name,
    timestamp,
    value,
    score,
    threshold,
    is_anomaly
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9
)
RETURNING *;

-- name: CreateAnomalyScores :copyfrom
INSERT INTO anomaly_scores (
    pipeline_name,
    build_number,
    metric_name,
    detector_name,
    timestamp,
    value,
    score,
    threshold,
    is_anomaly
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9
);

-- name: GetAnomaliesByPipeline :many
SELECT *
FROM anomaly_scores
WHERE pipeline_name = $1
    AND timestamp >= $2
    AND timestamp <= $3
ORDER BY timestamp DESC;

-- name: GetLatestAnomalyScores :many
SELECT 
    pipeline_name,
    metric_name,
    detector_name,
    MAX(timestamp) as latest_timestamp,
    COUNT(*) FILTER (WHERE is_anomaly = true) as anomaly_count,
    COUNT(*) as total_count
FROM anomaly_scores
WHERE timestamp >= $1
GROUP BY pipeline_name, metric_name, detector_name
ORDER BY latest_timestamp DESC;

-- name: DeleteOldAnomalyScores :exec
DELETE FROM anomaly_scores
WHERE timestamp < $1;

-- name: GetAnomalyScoresByDetector :many
SELECT *
FROM anomaly_scores
WHERE detector_name = $1
    AND timestamp >= $2
    AND timestamp <= $3
ORDER BY timestamp DESC;

-- name: GetBuildDataForAnomaly :many
SELECT 
    a.id,
    a.pipeline_name,
    a.build_number,
    a.metric_name,
    a.detector_name,
    a.timestamp,
    a.value,
    a.score,
    a.threshold,
    a.is_anomaly,
    b.status,
    b.triggered_by,
    b.build_start_time,
    b.build_end_time,
    b.building_time_seconds,
    b.blocked_time_seconds,
    b.buildable_time_seconds,
    b.waiting_time_seconds
FROM anomaly_scores a
LEFT JOIN builds b ON a.pipeline_name = b.pipeline_name 
    AND a.build_number = b.build_number
WHERE a.pipeline_name = $1
    AND a.timestamp >= $2
    AND a.timestamp <= $3
ORDER BY a.timestamp DESC;

-- name: GetAnomaliesByMetric :many
SELECT *
FROM anomaly_scores
WHERE metric_name = $1
    AND is_anomaly = true
    AND timestamp >= $2
    AND timestamp <= $3
ORDER BY score DESC, timestamp DESC;

-- name: GetAnomalyCountByPipeline :many
SELECT 
    pipeline_name,
    metric_name,
    COUNT(*) FILTER (WHERE is_anomaly = true) as anomaly_count,
    COUNT(*) as total_scores,
    AVG(score) as avg_score,
    MAX(score) as max_score
FROM anomaly_scores
WHERE timestamp >= $1
    AND timestamp <= $2
GROUP BY pipeline_name, metric_name
ORDER BY anomaly_count DESC;

-- name: GetRecentAnomaliesForPipeline :many
SELECT *
FROM anomaly_scores
WHERE pipeline_name = $1
    AND is_anomaly = true
    AND timestamp >= $2
ORDER BY timestamp DESC
LIMIT $3;

-- name: GetTimeSeriesForAnomaly :many
SELECT 
    timestamp,
    value,
    score,
    is_anomaly
FROM anomaly_scores
WHERE pipeline_name = $1
    AND metric_name = $2
    AND timestamp >= $3
    AND timestamp <= $4
ORDER BY timestamp ASC;