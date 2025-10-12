-- Anomaly detection results for time-series metrics
CREATE TABLE IF NOT EXISTS anomaly_scores (
    id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(255) NOT NULL,
    build_number INTEGER,
    metric_name VARCHAR(100) NOT NULL,
    detector_name VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    value FLOAT NOT NULL,
    score FLOAT NOT NULL,
    threshold FLOAT NOT NULL,
    is_anomaly BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_anomaly_build FOREIGN KEY (pipeline_name, build_number) 
        REFERENCES builds(pipeline_name, build_number) ON DELETE CASCADE
);

-- Indexes for Grafana queries
CREATE INDEX IF NOT EXISTS idx_anomaly_pipeline_timestamp ON anomaly_scores(pipeline_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_anomaly_metric_timestamp ON anomaly_scores(metric_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_anomaly_is_anomaly ON anomaly_scores(is_anomaly, timestamp DESC) WHERE is_anomaly = true;
CREATE INDEX IF NOT EXISTS idx_anomaly_detector ON anomaly_scores(detector_name, timestamp DESC);

-- Comments for documentation
COMMENT ON TABLE anomaly_scores IS 'Stores anomaly detection results for pipeline metrics';
COMMENT ON COLUMN anomaly_scores.build_number IS 'Links to specific build, NULL for aggregated metrics';
COMMENT ON COLUMN anomaly_scores.value IS 'Original metric value that was analyzed';
COMMENT ON COLUMN anomaly_scores.score IS 'Anomaly score from detector (e.g., z-score, isolation score)';
COMMENT ON COLUMN anomaly_scores.threshold IS 'Threshold used for this detection';
COMMENT ON COLUMN anomaly_scores.is_anomaly IS 'Whether this point was flagged as anomalous';