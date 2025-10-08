package anomaly

import "time"

type DetectionInput struct {
	PipelineName    string                 `json:"pipeline_name"`
	TimeWindowHours int                    `json:"time_window_hours"`
	Metrics         []string               `json:"metrics"`
	BuildData       []BuildDataPoint       `json:build_data`
	DetectorParams  map[string]interface{} `json:"params,omitempty"`
}

type BuildDataPoint struct {
	Timestamp time.Time `json:"timestamp"`
}
