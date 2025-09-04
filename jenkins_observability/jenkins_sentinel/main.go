package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"os"
	"time"

	"jenkins_sentinel/internal/db"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
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

const (
	BuildStatusSuccess  = "success"
	BuildStatusFailure  = "failure"
	BuildStatusAborted  = "aborted"
	BuildStatusUnstable = "unstable"
	BuildStatusNotBuilt = "not_built"
)

const (
	CollectionStatusComplete = "complete"
	CollectionStatusPartial  = "partial"
	CollectionStatusError    = "error"
	CollectionStatusPending  = "pending"
)

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
		slog.Error("error loading config", slog.Any("error", err))
		os.Exit(1)
	}

	slog.Info("loaded config", slog.Any("config", config))

	conn, err := pgx.Connect(context.Background(), fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=disable",
		config.Database.Host, config.Database.Port, config.Database.User, config.Database.Password, config.Database.DBName))
	if err != nil {
		slog.Error("failed connecting to postgres", slog.Any("error", err))
		os.Exit(1)
	}
	defer conn.Close(context.Background())

	queries := db.New(conn)

	slog.Info("successfully connected to PostgreSQL database")

	ctx := context.Background()

	createdBuild, err := queries.CreateBuild(ctx, db.CreateBuildParams{
		PipelineName:    "test-pipeline",
		BuildNumber:     1,
		BuildStartTime:  pgtype.Timestamptz{Time: time.Now().Add(-time.Hour), Valid: true},
		BuildEndTime:    pgtype.Timestamptz{Time: time.Now(), Valid: true},
		Status:          BuildStatusSuccess,
		TotalDuration:   3600.0,
		StepsSuccessful: 5,
		StepsFailed:     0,
		StepsSkipped:    pgtype.Int4{Int32: 0, Valid: true},
		ErrorLog:        pgtype.Text{String: "", Valid: false},
	})
	if err != nil {
		slog.Error("failed creating build", slog.Any("error", err))
		os.Exit(1)
	}

	slog.Info("created build", slog.Any("build", createdBuild))

	builds, err := queries.GetBuildsByPipeline(ctx, db.GetBuildsByPipelineParams{
		PipelineName: "test-pipeline",
		Limit:        10,
	})
	if err != nil {
		slog.Error("failed querying builds", slog.Any("error", err))
		os.Exit(1)
	}

	slog.Info("found builds", slog.Int("count", len(builds)))
}
