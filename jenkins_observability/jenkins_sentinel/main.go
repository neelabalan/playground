package main

import (
	"context"
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

func extractTriggeredBy(buildDetail map[string]any) *string {
	actions, ok := buildDetail["actions"].([]any)
	if !ok {
		return nil
	}

	for _, action := range actions {
		actionMap, ok := action.(map[string]any)
		if !ok {
			continue
		}

		if actionMap["_class"] == "hudson.model.CauseAction" {
			causes, ok := actionMap["causes"].([]any)
			if !ok || len(causes) == 0 {
				continue
			}

			cause, ok := causes[0].(map[string]any)
			if !ok {
				continue
			}

			if userName, ok := cause["userName"].(string); ok && userName != "" {
				return &userName
			}
			if userID, ok := cause["userId"].(string); ok && userID != "" {
				return &userID
			}
		}
	}
	return nil
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

	timingMetrics := extractJenkinsTimingMetrics(buildDetail)
	triggeredBy := extractTriggeredBy(buildDetail)

	var triggeredByField pgtype.Text
	if triggeredBy != nil {
		triggeredByField = pgtype.Text{String: *triggeredBy, Valid: true}
	}

	var buildingTimeField pgtype.Float8
	if timingMetrics.BuildingTimeSeconds > 0 {
		buildingTimeField = pgtype.Float8{Float64: timingMetrics.BuildingTimeSeconds, Valid: true}
	}

	var blockedTimeField pgtype.Float8
	if timingMetrics.BlockedTimeSeconds > 0 {
		blockedTimeField = pgtype.Float8{Float64: timingMetrics.BlockedTimeSeconds, Valid: true}
	}

	var buildableTimeField pgtype.Float8
	if timingMetrics.BuildableTimeSeconds > 0 {
		buildableTimeField = pgtype.Float8{Float64: timingMetrics.BuildableTimeSeconds, Valid: true}
	}

	var waitingTimeField pgtype.Float8
	if timingMetrics.WaitingTimeSeconds > 0 {
		waitingTimeField = pgtype.Float8{Float64: timingMetrics.WaitingTimeSeconds, Valid: true}
	}

	_, err = queries.CreateBuild(ctx, db.CreateBuildParams{
		PipelineName:         pipelineName,
		BuildNumber:          queueItem.BuildNumber,
		BuildStartTime:       pgtype.Timestamptz{Time: buildStartTime, Valid: true},
		BuildEndTime:         pgtype.Timestamptz{Time: buildEndTime, Valid: true},
		Status:               convertJenkinsResult(buildDetail["result"].(string)),
		BuildingTimeSeconds:  buildingTimeField,
		ErrorLog:             pgtype.Text{Valid: false},
		TriggeredBy:          triggeredByField,
		BlockedTimeSeconds:   blockedTimeField,
		BuildableTimeSeconds: buildableTimeField,
		WaitingTimeSeconds:   waitingTimeField,
	})

	if err != nil {
		return fmt.Errorf("failed to create build record: %w", err)
	}

	logAttrs := []any{
		slog.String("pipeline", pipelineName),
		slog.Int("build_number", int(queueItem.BuildNumber)),
		slog.String("status", convertJenkinsResult(buildDetail["result"].(string))),
		slog.Float64("building_time_seconds", timingMetrics.BuildingTimeSeconds),
		slog.Float64("waiting_time_seconds", timingMetrics.WaitingTimeSeconds),
		slog.Float64("buildable_time_seconds", timingMetrics.BuildableTimeSeconds),
		slog.Float64("blocked_time_seconds", timingMetrics.BlockedTimeSeconds),
	}

	if triggeredBy != nil {
		logAttrs = append(logAttrs, slog.String("triggered_by", *triggeredBy))
	}

	slog.Info("processed build with timing metrics", logAttrs...)

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

	if err := setupLogger(config); err != nil {
		slog.Error("failed to setup logger", slog.Any("error", err))
		os.Exit(1)
	}

	slog.Info("jenkins sentinel started", slog.String("config_path", *configPath))

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

	jenkins := NewJenkinsClient(config.BaseURL, config.Username, config.Token, config.Password)

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
