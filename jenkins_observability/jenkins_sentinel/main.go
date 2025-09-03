package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
)

type DatabaseConfig struct {
	Host     string `json:"host"`
	Port     int    `json:"port"`
	User     string `json:"user"`
	Password string `json:"password"`
	DBName   string `json:"dbname"`
}

type Config struct {
	Username        string         `json:"username"`
	Token           string         `json:"token"`
	Pipelines       []string       `json:"pipelines"`
	Database        DatabaseConfig `json:"database"`
	RetryAttempts   int            `json:"retry_attempts"`
	LoggingLevel    string         `json:"logging_level"`
	BackfillEnabled bool           `json:"backfill_enabled"`
}

func loadConfig(filename string) (*Config, error) {
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

func main() {
	config, err := loadConfig("config.json")
	if err != nil {
		log.Fatalf("Error loading config: %v", err)
	}

	fmt.Printf("Loaded config: %+v\n", config)
}
