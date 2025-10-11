package config

import (
	"encoding/json"
	"fmt"
	"os"
)

type DatabaseConfig struct {
	Host     string `json:"host"`
	Port     int    `json:"port"`
	User     string `json:"user"`
	Password string `json:"password"`
	DBName   string `json:"dbname"`
}

type AnomalyProcessingConfig struct {
	MaxParallel       int    `json:"max_parallel"`
	BatchSize         int    `json:"batch_size"`
	DetectorDirectory string `json:"detector_directory"`
}

type AnomalyDetectionConfig struct {
	Name            string         `json:"name,omitempty"`
	Params          map[string]any `json:"params,omitempty"`
	TimeWindowHours int            `json:"time_window_hours,omitempty"`
	Metrics         []string       `json:"metrics,omitempty"`
}

type PipelineConfig struct {
	URL              string                  `json:"url"`
	AnomalyDetection *AnomalyDetectionConfig `json:"anomaly_detection,omitempty"`
}

type Config struct {
	Username          string                  `json:"username"`
	Token             string                  `json:"token,omitempty"`
	Password          string                  `json:"password,omitempty"`
	BaseURL           string                  `json:"base_url"`
	AnomalyProcessing AnomalyProcessingConfig `json:"anomaly_processing"`
	Pipelines         []PipelineConfig        `json:"pipelines"`
	Database          DatabaseConfig          `json:"database"`
	RetryAttempts     int                     `json:"retry_attempts"`
	LoggingLevel      string                  `json:"logging_level"`
	LogFile           string                  `json:"log_file,omitempty"`
	BackfillEnabled   bool                    `json:"backfill_enabled"`
}

func LoadConfig(filename string) (*Config, error) {
	file, err := os.Open(filename)
	if err != nil {
		return nil, fmt.Errorf("failed to open config file: %w", err)
	}
	defer file.Close()

	var config Config
	decoder := json.NewDecoder(file)
	if err := decoder.Decode(&config); err != nil {
		return nil, fmt.Errorf("failed to decode config JSON: %w", err)
	}

	return &config, nil
}
