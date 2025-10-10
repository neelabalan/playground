package anomaly

import (
	"context"
	"time"
)

type AnomalyDetector interface {
	GetName() string

	DetectAnomalies(ctx context.Context, input BatchDetectionInput) (*BatchDetectionOutput, error)
}

type DetectionInput struct {
	PipelineName    string             `json:"pipeline_name"`
	TimeWindowHours int                `json:"time_window_hours"`
	Metrics         []string           `json:"metrics"`
	TimeSeries      []MetricTimeSeries `json:"time_series"`
}

type BatchDetectionInput struct {
	Pipelines []DetectionInput `json:"pipelines"`
}

type BatchDetectionOutput struct {
	Results []DetectionOutput `json:"results"`
}

type TimeSeriesPoint struct {
	Timestamp time.Time `json:"timestamp"`
	Value     float64   `json:"value"`
}

type MetricTimeSeries struct {
	MetricName string            `json:"metric_name"`
	Points     []TimeSeriesPoint `json:"points"`
}

type DetectionOutput struct {
	Anomalies []AnomalyResult   `json:"anomalies"`
	Metadata  DetectionMetadata `json:"metadata"`
}

type AnomalyResult struct {
	Timestamp  time.Time `json:"timestamp"`
	MetricName string    `json:"metric_name"`
	Score      float64   `json:"score"`
	Threshold  float64   `json:"threshold"`
	IsAnomaly  bool      `json:"is_anomaly"`
	Value      float64   `json:"value"`
}

type DetectionMetadata struct {
	// DetectorName    string `json:"detector_name"`
	ProcessedPoints int   `json:"processed_points"`
	ExecutionTimeMs int64 `json:"execution_time_ms"`
}
