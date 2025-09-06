package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log/slog"
	"os"
	"strings"
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
	BaseURL         string         `json:"base_url"`
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

func convertJenkinsResult(result string) string {
	switch strings.ToUpper(result) {
	case "SUCCESS":
		return BuildStatusSuccess
	case "FAILURE":
		return BuildStatusFailure
	case "ABORTED":
		return BuildStatusAborted
	case "UNSTABLE":
		return BuildStatusUnstable
	case "NOT_BUILT":
		return BuildStatusNotBuilt
	default:
		return "unknown"
	}
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

func processPipeline(ctx context.Context, queries *db.Queries, jenkins *JenkinsClient, pipelinePath string) error {
	slog.Info("processing pipeline", slog.String("pipeline", pipelinePath))

	buildNumbers, err := jenkins.GetBuildNumbers(pipelinePath)
	if err != nil {
		return fmt.Errorf("failed to get build numbers for %s: %w", pipelinePath, err)
	}

	slog.Info("found builds in Jenkins", slog.String("pipeline", pipelinePath), slog.Int("count", len(buildNumbers)))

	pipelineName := extractPipelineName(pipelinePath)

	existingBuilds, err := queries.GetBuildsByPipeline(ctx, db.GetBuildsByPipelineParams{
		PipelineName: pipelineName,
		Limit:        10000,
	})
	if err != nil {
		return fmt.Errorf("failed to get existing builds: %w", err)
	}

	existingBuildNumbers := make(map[int]bool)
	for _, build := range existingBuilds {
		existingBuildNumbers[int(build.BuildNumber)] = true
	}

	missingCount := 0
	for _, buildNumber := range buildNumbers {
		if !existingBuildNumbers[buildNumber] {
			queueItem, err := queries.CreateBuildQueueItem(ctx, db.CreateBuildQueueItemParams{
				JobPath:          pipelinePath,
				BuildNumber:      int32(buildNumber),
				LastAttemptAt:    pgtype.Timestamptz{Time: time.Now(), Valid: true},
				ErrorMessage:     pgtype.Text{Valid: false},
				CollectionTime:   pgtype.Timestamptz{Time: time.Now(), Valid: true},
				CollectionStatus: CollectionStatusPending,
			})
			if err != nil {
				slog.Error("failed to queue build",
					slog.String("pipeline", pipelinePath),
					slog.Int("build", buildNumber),
					slog.Any("error", err))
				continue
			}

			slog.Debug("queued build for processing",
				slog.String("pipeline", pipelinePath),
				slog.Int("build", buildNumber),
				slog.Int("queue_id", int(queueItem.ID)))
			missingCount++
		}
	}

	slog.Info("queued missing builds",
		slog.String("pipeline", pipelineName),
		slog.Int("missing", missingCount),
		slog.Int("existing", len(existingBuilds)))

	return nil
}

func processQueuedBuilds(ctx context.Context, queries *db.Queries, jenkins *JenkinsClient) error {
	pendingItems, err := queries.GetPendingQueueItems(ctx)
	if err != nil {
		return fmt.Errorf("failed to get pending queue items: %w", err)
	}

	if len(pendingItems) == 0 {
		slog.Info("no pending builds in queue")
		return nil
	}

	slog.Info("processing queued builds", slog.Int("count", len(pendingItems)))

	for _, item := range pendingItems {
		err := processBuildFromQueue(ctx, queries, jenkins, item)
		if err != nil {
			slog.Error("failed to process build from queue",
				slog.String("job_path", item.JobPath),
				slog.Int("build_number", int(item.BuildNumber)),
				slog.Any("error", err))

			_, updateErr := queries.UpdateQueueItemStatus(ctx, db.UpdateQueueItemStatusParams{
				ID:               item.ID,
				CollectionStatus: CollectionStatusError,
			})
			if updateErr != nil {
				slog.Error("failed to update queue item status", slog.Any("error", updateErr))
			}
			continue
		}

		err = queries.DeleteQueueItem(ctx, item.ID)
		if err != nil {
			slog.Error("failed to delete processed queue item", slog.Any("error", err))
		}
	}

	return nil
}

func processBuildFromQueue(ctx context.Context, queries *db.Queries, jenkins *JenkinsClient, queueItem db.BuildQueue) error {
	buildDetail, err := jenkins.GetBuildDetail(queueItem.JobPath, int(queueItem.BuildNumber))
	if err != nil {
		return fmt.Errorf("failed to get build detail: %w", err)
	}

	if buildDetail["building"].(bool) {
		slog.Info("build still running, skipping",
			slog.String("job_path", queueItem.JobPath),
			slog.Int("build_number", int(queueItem.BuildNumber)))
		return nil
	}

	pipelineName := extractPipelineName(queueItem.JobPath)

	buildStartTime := time.Unix(int64(buildDetail["timestamp"].(float64))/1000, 0)
	buildEndTime := buildStartTime.Add(time.Duration(buildDetail["duration"].(float64)) * time.Millisecond)

	_, err = queries.CreateBuild(ctx, db.CreateBuildParams{
		PipelineName:    pipelineName,
		BuildNumber:     queueItem.BuildNumber,
		BuildStartTime:  pgtype.Timestamptz{Time: buildStartTime, Valid: true},
		BuildEndTime:    pgtype.Timestamptz{Time: buildEndTime, Valid: true},
		Status:          convertJenkinsResult(buildDetail["result"].(string)),
		TotalDuration:   buildDetail["duration"].(float64) / 1000.0,
		StepsSuccessful: 0, // TODO: Extract from Jenkins data if available
		StepsFailed:     0, // TODO: Extract from Jenkins data if available
		StepsSkipped:    pgtype.Int4{Valid: false},
		ErrorLog:        pgtype.Text{Valid: false},
	})

	if err != nil {
		return fmt.Errorf("failed to create build record: %w", err)
	}

	slog.Info("processed build",
		slog.String("pipeline", pipelineName),
		slog.Int("build_number", int(queueItem.BuildNumber)),
		slog.String("status", convertJenkinsResult(buildDetail["result"].(string))))

	return nil
}

func extractPipelineName(jobPath string) string {
	cleaned := strings.TrimSuffix(jobPath, "/")
	cleaned = strings.TrimPrefix(cleaned, "job/")
	return cleaned
}

func main() {
	configPath := flag.String("config", "config.json", "Path to the configuration file")
	flag.Parse()

	config, err := loadConfig(*configPath)
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

	// Run database migrations
	if err := RunMigrations(ctx, conn, "sql/schema"); err != nil {
		slog.Error("failed to run migrations", slog.Any("error", err))
		os.Exit(1)
	}

	slog.Info("database schema initialized successfully")

	jenkins := NewJenkinsClient(config.BaseURL, config.Username, config.Token)

	for _, pipelinePath := range config.Pipelines {
		err := processPipeline(ctx, queries, jenkins, pipelinePath)
		if err != nil {
			slog.Error("failed to process pipeline",
				slog.String("pipeline", pipelinePath),
				slog.Any("error", err))
			continue
		}
	}

	err = processQueuedBuilds(ctx, queries, jenkins)
	if err != nil {
		slog.Error("failed to process queued builds", slog.Any("error", err))
	}

	slog.Info("jenkins sentinel completed successfully")
}
