package main

import (
	"context"
	"flag"
	"fmt"
	"log/slog"
	"os"
	"strings"
	"time"

	"jenkins_sentinel/internal/anomaly"
	"jenkins_sentinel/internal/config"
	"jenkins_sentinel/internal/db"
	"jenkins_sentinel/internal/jenkins"
	"jenkins_sentinel/internal/logging"
	"jenkins_sentinel/internal/metrics"
	"jenkins_sentinel/internal/migrations"

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

func processPipeline(ctx context.Context, queries *db.Queries, jenkinsClient *jenkins.Client, pipelinePath string) error {
	slog.Info("processing pipeline", slog.String("pipeline", pipelinePath))

	buildNumbers, err := jenkinsClient.GetBuildNumbers(pipelinePath)
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

func processQueuedBuilds(ctx context.Context, queries *db.Queries, jenkinsClient *jenkins.Client) error {
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
		err := processBuildFromQueue(ctx, queries, jenkinsClient, item)
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

func processBuildFromQueue(ctx context.Context, queries *db.Queries, jenkinsClient *jenkins.Client, queueItem db.BuildQueue) error {
	buildDetail, err := jenkinsClient.GetBuildDetail(queueItem.JobPath, int(queueItem.BuildNumber))
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

	timingMetrics := metrics.ExtractJenkinsTimingMetrics(buildDetail)
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

func buildTimeSeriesData(ctx context.Context, queries *db.Queries, pipelineName string, metricName string, startTime, endTime time.Time) (anomaly.MetricTimeSeries, error) {
	rows, err := queries.GetMetricTimeSeries(ctx, db.GetMetricTimeSeriesParams{
		PipelineName:     pipelineName,
		BuildStartTime:   pgtype.Timestamptz{Time: startTime, Valid: true},
		BuildStartTime_2: pgtype.Timestamptz{Time: endTime, Valid: true},
		MetricName:       metricName,
	})
	if err != nil {
		return anomaly.MetricTimeSeries{}, fmt.Errorf("failed to fetch metric time series: %w", err)
	}

	points := make([]anomaly.TimeSeriesPoint, 0, len(rows))

	for _, row := range rows {
		if row.MetricValue != nil {
			if value, ok := row.MetricValue.(float64); ok {
				points = append(points, anomaly.TimeSeriesPoint{
					Timestamp:   row.BuildStartTime.Time,
					Value:       value,
					BuildNumber: row.BuildNumber,
				})
			}
		}
	}

	return anomaly.MetricTimeSeries{
		MetricName: metricName,
		Points:     points,
	}, nil
}

func buildPipelineAnomalyDetectionJob(ctx context.Context, queries *db.Queries, pipelineCfg *config.PipelineConfig) (*anomaly.PipelineAnomalyDetectionJob, error) {
	if pipelineCfg.AnomalyDetection == nil || pipelineCfg.AnomalyDetection.Name == "" {
		return nil, nil
	}

	pipelineName := extractPipelineName(pipelineCfg.URL)
	timeWindow := time.Duration(pipelineCfg.AnomalyDetection.TimeWindowHours) * time.Hour
	startTime := time.Now().Add(-timeWindow)
	endTime := time.Now()

	slog.Info("preparing anomaly detection",
		slog.String("pipeline", pipelineName),
		slog.String("detector", pipelineCfg.AnomalyDetection.Name),
		slog.Int("time_window_hours", pipelineCfg.AnomalyDetection.TimeWindowHours))

	var timeSeries []anomaly.MetricTimeSeries

	for _, metricName := range pipelineCfg.AnomalyDetection.Metrics {
		ts, err := buildTimeSeriesData(ctx, queries, pipelineName, metricName, startTime, endTime)
		if err != nil {
			slog.Error("failed to build time series",
				slog.String("pipeline", pipelineName),
				slog.String("metric", metricName),
				slog.Any("error", err))
			continue
		}

		if len(ts.Points) > 0 {
			timeSeries = append(timeSeries, ts)
		}
	}

	if len(timeSeries) == 0 {
		slog.Warn("no time series data available for anomaly detection",
			slog.String("pipeline", pipelineName))
		return nil, nil
	}

	detectionInput := anomaly.DetectionInput{
		PipelineName:    pipelineName,
		TimeWindowHours: pipelineCfg.AnomalyDetection.TimeWindowHours,
		Metrics:         pipelineCfg.AnomalyDetection.Metrics,
		TimeSeries:      timeSeries,
	}

	var params map[string]string
	if pipelineCfg.AnomalyDetection.Params != nil {
		params = make(map[string]string)
		for key, value := range pipelineCfg.AnomalyDetection.Params {
			params[key] = fmt.Sprintf("%v", value)
		}
	}

	return &anomaly.PipelineAnomalyDetectionJob{
		PipelineName: pipelineName,
		DetectorName: pipelineCfg.AnomalyDetection.Name,
		Input:        detectionInput,
		Params:       params,
	}, nil
}

func processAnomalyDetection(ctx context.Context, queries *db.Queries, registry *anomaly.DetectorRegistry, cfg *config.Config) error {
	slog.Info("starting anomaly detection processing")

	var detectionJobs []anomaly.PipelineAnomalyDetectionJob

	for _, pipelineCfg := range cfg.Pipelines {
		job, err := buildPipelineAnomalyDetectionJob(ctx, queries, &pipelineCfg)
		if err != nil {
			slog.Error("failed to build anomaly detection job",
				slog.String("pipeline", pipelineCfg.URL),
				slog.Any("error", err))
			continue
		}

		if job != nil {
			detectionJobs = append(detectionJobs, *job)
		}
	}

	if len(detectionJobs) == 0 {
		slog.Info("no anomaly detection jobs to process")
		return nil
	}

	slog.Info("running anomaly detection", slog.Int("job_count", len(detectionJobs)))

	results := anomaly.RunPipelineDetections(ctx, registry, detectionJobs, cfg.AnomalyProcessing.MaxParallel)

	for _, result := range results {
		if result.Error != nil {
			slog.Error("anomaly detection failed",
				slog.String("pipeline", result.PipelineName),
				slog.String("detector", result.DetectorName),
				slog.Any("error", result.Error))
			continue
		}

		if result.Output == nil {
			continue
		}

		pipelineName := result.PipelineName

		for _, anomalyResult := range result.Output.Anomalies {
			_, err := queries.CreateAnomalyScore(ctx, db.CreateAnomalyScoreParams{
				PipelineName: pipelineName,
				BuildNumber:  pgtype.Int4{Int32: anomalyResult.BuildNumber, Valid: true},
				MetricName:   anomalyResult.MetricName,
				DetectorName: result.DetectorName,
				Timestamp:    pgtype.Timestamptz{Time: anomalyResult.Timestamp, Valid: true},
				Value:        anomalyResult.Value,
				Score:        anomalyResult.Score,
				Threshold:    anomalyResult.Threshold,
				IsAnomaly:    anomalyResult.IsAnomaly,
			})

			if err != nil {
				slog.Error("failed to store anomaly score",
					slog.String("pipeline", pipelineName),
					slog.String("metric", anomalyResult.MetricName),
					slog.Any("error", err))
			}
		}

		slog.Info("stored anomaly detection results",
			slog.String("pipeline", result.PipelineName),
			slog.String("detector", result.DetectorName),
			slog.Int("anomalies_found", len(result.Output.Anomalies)),
			slog.Int("points_processed", result.Output.Metadata.ProcessedPoints))
	}

	return nil
}

func main() {
	configPath := flag.String("config", "config.json", "Path to the configuration file")
	flag.Parse()

	config, err := config.LoadConfig(*configPath)
	if err != nil {
		slog.Error("error loading config", slog.Any("error", err))
		os.Exit(1)
	}

	if err := logging.Setup(config); err != nil {
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
	if err := migrations.Run(ctx, conn, "sql/schema"); err != nil {
		slog.Error("failed to run migrations", slog.Any("error", err))
		os.Exit(1)
	}

	slog.Info("database schema initialized successfully")

	jenkinsClient := jenkins.NewClient(config.BaseURL, config.Username, config.Token, config.Password)

	for _, pipeline := range config.Pipelines {
		err := processPipeline(ctx, queries, jenkinsClient, pipeline.URL)
		if err != nil {
			slog.Error("failed to process pipeline",
				slog.String("pipeline", pipeline.URL),
				slog.Any("error", err))
			continue
		}
	}

	err = processQueuedBuilds(ctx, queries, jenkinsClient)
	if err != nil {
		slog.Error("failed to process queued builds", slog.Any("error", err))
	}

	detectorDir := config.AnomalyProcessing.DetectorDirectory

	detectorRegistry, err := anomaly.NewDetectorRegistry(detectorDir)
	if err != nil {
		slog.Error("failed to initialize anomaly detector registry", slog.Any("error", err))
	} else {
		slog.Info("anomaly detectors loaded", slog.Any("detectors", detectorRegistry.List()))

		err = processAnomalyDetection(ctx, queries, detectorRegistry, config)
		if err != nil {
			slog.Error("failed to process anomaly detection", slog.Any("error", err))
		}
	}

	slog.Info("jenkins sentinel completed successfully")
}
