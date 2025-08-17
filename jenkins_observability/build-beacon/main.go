package main

import (
	"bytes"
	"context"
	"flag"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"reflect"
	"strconv"
	"syscall"
	"time"

	"go.opentelemetry.io/collector/pdata/pcommon"
	"go.opentelemetry.io/collector/pdata/pmetric"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp"
	"go.opentelemetry.io/otel/metric"
	sdkmetric "go.opentelemetry.io/otel/sdk/metric"
	"go.opentelemetry.io/otel/sdk/resource"
	semconv "go.opentelemetry.io/otel/semconv/v1.17.0"
	"go.opentelemetry.io/otel/trace/noop"
)

type Config struct {
	Pipelines    []Pipeline      `json:"pipelines"`
	Worker       int             `json:"worker"`
	DataStore    string          `json:"data_store"`
	SlackChannel string          `json:"slack_channel"`
	Telemetry    TelemetryConfig `json:"telemetry,omitempty"`
}

type Pipeline struct {
	URL       string `json:"url"`
	Frequency int    `json:"frequency"`
}

type TelemetryConfig struct {
	ServiceName     string `json:"service_name"`
	ServiceInstance string `json:"service_instance"`
	OTLPEndpoint    string `json:"otlp_endpoint"`
	OTLPPath        string `json:"otlp_path"`
	ExportInterval  int    `json:"export_interval_seconds"`
}

type OTLPMetricExporter struct {
	endpoint string
	path     string
	provider *sdkmetric.MeterProvider
	gauge    metric.Float64ObservableGauge
}

func NewOTLPMetricExporter(endpoint, path, serviceName, serviceInstance string, exportInterval int) (*OTLPMetricExporter, error) {
	slog.Debug("Creating OTLP metric exporter",
		slog.String("endpoint", endpoint),
		slog.String("path", path),
		slog.String("service_name", serviceName),
		slog.String("service_instance", serviceInstance),
		slog.Int("export_interval", exportInterval))

	ctx := context.Background()

	exporter, err := otlpmetrichttp.New(ctx,
		otlpmetrichttp.WithEndpoint(endpoint),
		otlpmetrichttp.WithURLPath(path),
		otlpmetrichttp.WithInsecure(),
	)
	if err != nil {
		slog.Error("Failed to create OTLP exporter", slog.Any("error", err))
		return nil, fmt.Errorf("failed to create OTLP exporter: %w", err)
	}
	slog.Debug("OTLP exporter created successfully")

	res, err := resource.New(ctx,
		resource.WithAttributes(
			semconv.ServiceName(serviceName),
			attribute.String("service.instance.id", serviceInstance),
		),
	)
	if err != nil {
		slog.Error("Failed to create resource", slog.Any("error", err))
		return nil, fmt.Errorf("failed to create resource: %w", err)
	}
	slog.Debug("OTLP resource created successfully")

	provider := sdkmetric.NewMeterProvider(
		sdkmetric.WithResource(res),
		sdkmetric.WithReader(sdkmetric.NewPeriodicReader(
			exporter,
			sdkmetric.WithInterval(time.Duration(exportInterval)*time.Second),
		)),
	)

	otel.SetMeterProvider(provider)
	otel.SetTracerProvider(noop.NewTracerProvider())

	meter := otel.Meter("github.com/jenkins-build-beacon")

	gauge, err := meter.Float64ObservableGauge(
		"jenkins.build_duration.seconds",
		metric.WithDescription("Jenkins build duration in seconds"),
	)
	if err != nil {
		slog.Error("Failed to create gauge", slog.Any("error", err))
		return nil, fmt.Errorf("failed to create gauge: %w", err)
	}
	slog.Debug("OTLP gauge created successfully")

	slog.Info("OTLP metric exporter initialized successfully",
		slog.String("endpoint", endpoint),
		slog.String("service", serviceName))

	return &OTLPMetricExporter{
		endpoint: endpoint,
		path:     path,
		provider: provider,
		gauge:    gauge,
	}, nil
}

func (e *OTLPMetricExporter) RecordJenkinsBuild(ctx context.Context, build JenkinsBuild) error {
	slog.Debug("Recording Jenkins build metrics",
		slog.String("pipeline", build.PipelineName),
		slog.Int("build_number", build.BuildNumber),
		slog.String("status", build.Status),
		slog.Float64("duration", build.DurationSeconds))

	metricData := pmetric.NewMetrics()
	resourceMetrics := metricData.ResourceMetrics().AppendEmpty()

	resourceMetrics.Resource().Attributes().PutStr("service.name", "jenkins-build-beacon")
	resourceMetrics.Resource().Attributes().PutStr("service.instance.id", "simulator")

	scopeMetrics := resourceMetrics.ScopeMetrics().AppendEmpty()
	scopeMetrics.Scope().SetName("github.com/jenkins-build-beacon")

	commonLabels := func(dataPoint pmetric.NumberDataPoint) {
		dataPoint.Attributes().PutStr("pipeline_name", build.PipelineName)
		dataPoint.Attributes().PutStr("status", build.Status)
		dataPoint.Attributes().PutInt("build_number", int64(build.BuildNumber))
		dataPoint.Attributes().PutStr("url", build.URL)
		dataPoint.SetTimestamp(pcommon.NewTimestampFromTime(build.Timestamp))
	}

	durationMetric := scopeMetrics.Metrics().AppendEmpty()
	durationMetric.SetName("jenkins_build_duration_seconds")
	durationMetric.SetDescription("Jenkins build duration in seconds")

	durationGauge := durationMetric.SetEmptyGauge()
	durationDataPoint := durationGauge.DataPoints().AppendEmpty()
	durationDataPoint.SetDoubleValue(build.DurationSeconds)
	commonLabels(durationDataPoint)

	slog.Debug("Sending metrics to OTLP endpoint",
		slog.String("endpoint", e.endpoint),
		slog.Int("metrics_count", 2))

	if err := e.SendMetrics(ctx, metricData); err != nil {
		slog.Error("Failed to send Jenkins build metrics",
			slog.String("pipeline", build.PipelineName),
			slog.Int("build_number", build.BuildNumber),
			slog.Any("error", err))
		return err
	}

	slog.Debug("Successfully sent Jenkins build metrics",
		slog.String("pipeline", build.PipelineName),
		slog.Int("build_number", build.BuildNumber))

	return nil
}

func (e *OTLPMetricExporter) SendMetrics(ctx context.Context, metrics pmetric.Metrics) error {
	slog.Debug("Marshaling metrics for OTLP transmission")

	marshaler := &pmetric.ProtoMarshaler{}
	data, err := marshaler.MarshalMetrics(metrics)
	if err != nil {
		slog.Error("Failed to marshal metrics", slog.Any("error", err))
		return fmt.Errorf("failed to marshal metrics: %w", err)
	}

	url := fmt.Sprintf("http://%s%s", e.endpoint, e.path)
	slog.Debug("Sending HTTP request to OTLP endpoint",
		slog.String("url", url),
		slog.Int("payload_size", len(data)))

	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(data))
	if err != nil {
		slog.Error("Failed to create HTTP request", slog.Any("error", err))
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/x-protobuf")

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		slog.Error("Failed to send HTTP request",
			slog.String("url", url),
			slog.Any("error", err))
		return fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		slog.Error("OTLP endpoint returned error",
			slog.Int("status_code", resp.StatusCode),
			slog.String("response_body", string(body)),
			slog.String("url", url))
		return fmt.Errorf("server returned status %d: %s", resp.StatusCode, string(body))
	}

	slog.Debug("Successfully sent metrics to OTLP endpoint",
		slog.String("url", url),
		slog.Int("status_code", resp.StatusCode))

	return nil
}

func (e *OTLPMetricExporter) Shutdown(ctx context.Context) error {
	slog.Info("Shutting down OTLP metric exporter")

	if e.provider != nil {
		if err := e.provider.Shutdown(ctx); err != nil {
			slog.Error("Failed to shutdown metric provider", slog.Any("error", err))
			return err
		}
		slog.Debug("Metric provider shutdown successfully")
	}

	slog.Info("OTLP metric exporter shutdown completed")
	return nil
}

func ProcessBackfill(ctx context.Context, exporter *OTLPMetricExporter, serviceName, serviceInstance string) error {
	slog.Info("Starting metrics backfill", "days", 3)

	base := time.Now().Add(-time.Duration(3) * 24 * time.Hour)

	for i := range 10 {
		customTimestamp := base.Add(time.Duration(i) * time.Minute)

		metricData := pmetric.NewMetrics()
		resourceMetrics := metricData.ResourceMetrics().AppendEmpty()

		resourceMetrics.Resource().Attributes().PutStr("service.name", serviceName)
		resourceMetrics.Resource().Attributes().PutStr("service.instance.id", serviceInstance)

		scopeMetrics := resourceMetrics.ScopeMetrics().AppendEmpty()
		scopeMetrics.Scope().SetName("github.com/jenkins-build-beacon")

		metric := scopeMetrics.Metrics().AppendEmpty()
		metric.SetName("jenkins_builds_backfilled")
		metric.SetDescription("Backfilled Jenkins build metrics")

		sum := metric.SetEmptySum()
		sum.SetAggregationTemporality(pmetric.AggregationTemporalityCumulative)
		sum.SetIsMonotonic(true)

		dataPoint := sum.DataPoints().AppendEmpty()
		dataPoint.SetIntValue(int64(i + 1))
		dataPoint.SetTimestamp(pcommon.NewTimestampFromTime(customTimestamp))
		dataPoint.Attributes().PutStr("pipeline", "historical")
		dataPoint.Attributes().PutStr("status", "success")
		dataPoint.Attributes().PutInt("sequence", int64(i))

		err := exporter.SendMetrics(ctx, metricData)
		if err != nil {
			slog.Error("Failed to send backfilled metric", "error", err, "sequence", i+1)
		} else {
			slog.Debug("Sent backfilled metric", "sequence", i+1, "timestamp", customTimestamp)
		}

		time.Sleep(100 * time.Millisecond)
	}

	slog.Info("Finished metrics backfill")
	return nil
}

func generateServiceInstanceID() string {
	return "jenkins-beacon-" + time.Now().Format("20060102-150405")
}

func waitForShutdown() <-chan struct{} {
	shutdown := make(chan struct{})
	go func() {
		sigint := make(chan os.Signal, 1)
		signal.Notify(sigint, syscall.SIGINT, syscall.SIGTERM)
		<-sigint
		close(shutdown)
	}()
	return shutdown
}

type JenkinsBuild struct {
	BuildNumber     int
	PipelineName    string
	URL             string
	Status          string
	DurationSeconds float64
	Timestamp       time.Time
}

type JenkinsBuildSimulator struct {
	pipelines []string
	baseURL   string
}

func NewJenkinsBuildSimulator(numPipelines int) *JenkinsBuildSimulator {
	pipelines := []string{
		"frontend-build", "backend-api", "data-pipeline", "ml-training",
		"mobile-app", "integration-tests", "security-scan", "deployment",
		"microservice-auth", "microservice-payment", "microservice-inventory",
		"ui-components", "database-migration", "docker-build", "k8s-deploy",
	}

	if numPipelines < len(pipelines) {
		pipelines = pipelines[:numPipelines]
	}

	return &JenkinsBuildSimulator{
		pipelines: pipelines,
		baseURL:   "https://jenkins.company.com/job",
	}
}

func (s *JenkinsBuildSimulator) GenerateBuild() JenkinsBuild {
	pipeline := s.pipelines[time.Now().UnixNano()%int64(len(s.pipelines))]
	buildNumber := int(time.Now().Unix()%10000) + 1

	// realistic status distribution: 70% success, 20% failed, 10% aborted
	statusRand := time.Now().UnixNano() % 100
	var status string
	var baseDuration float64

	switch {
	case statusRand < 70:
		status = "success"
		baseDuration = 120 + float64(time.Now().UnixNano()%300)
	case statusRand < 90:
		status = "failed"
		baseDuration = 60 + float64(time.Now().UnixNano()%180)
	default:
		status = "aborted"
		baseDuration = 30 + float64(time.Now().UnixNano()%90)
	}

	return JenkinsBuild{
		BuildNumber:     buildNumber,
		PipelineName:    pipeline,
		URL:             fmt.Sprintf("%s/%s/%d/", s.baseURL, pipeline, buildNumber),
		Status:          status,
		DurationSeconds: baseDuration,
		Timestamp:       time.Now(),
	}
}

type CmdArgs struct {
	Config    string `arg:"config" default:"" description:"The configuration file where pipelines are listed to collect data"`
	Simulate  bool   `arg:"simulate" default:"false" description:"Enable Jenkins build simulation mode"`
	Interval  int    `arg:"interval" default:"30" description:"Simulation interval in seconds"`
	Pipelines int    `arg:"pipelines" default:"5" description:"Number of pipelines to simulate"`
}

func createFlagArgs(args any) any {
	t := reflect.TypeOf(args)
	commandLineArgs := reflect.New(t).Elem()

	for i := 0; i < t.NumField(); i++ {
		field := t.Field(i)
		cmdTag := field.Tag.Get("arg")
		defaultTag := field.Tag.Get("default")
		description := field.Tag.Get("description")

		switch field.Type.Name() {
		case "string":
			flag.StringVar(commandLineArgs.Field(i).Addr().Interface().(*string), cmdTag, defaultTag, description)
		case "int":
			val, err := strconv.Atoi(defaultTag)
			if err != nil {
				slog.Error("Check the default tag for ", slog.Any("type", field))
			}
			flag.IntVar(commandLineArgs.Field(i).Addr().Interface().(*int), cmdTag, val, description)
		case "bool":
			val, err := strconv.ParseBool(defaultTag)
			if err != nil {
				slog.Error("Check the default tag for ", slog.Any("type", field))
			}
			flag.BoolVar(commandLineArgs.Field(i).Addr().Interface().(*bool), cmdTag, val, description)
		default:
			slog.Warn("Cannot parse at ", slog.Any("type", field))
		}
	}
	flag.Parse()
	return commandLineArgs.Interface()

}

func main() {
	logDebugMode := os.Getenv("DEBUG")
	if logDebugMode == "TRUE" || logDebugMode == "1" {
		slog.SetLogLoggerLevel(slog.LevelDebug)
	} else {
		slog.SetLogLoggerLevel(slog.LevelInfo)
	}

	slog.Debug("Starting Jenkins Build Beacon")
	slog.Info("Jenkins Build Beacon initializing...")

	args := createFlagArgs(CmdArgs{}).(CmdArgs)
	slog.Debug("Parsed command line arguments",
		slog.String("config", args.Config),
		slog.Bool("simulate", args.Simulate),
		slog.Int("interval", args.Interval),
		slog.Int("pipelines", args.Pipelines))

	ctx := context.Background()
	TestJenkinsBuilds(ctx)

	// configPath := args.Config
	// if configPath == "" {
	// 	configPath = "config.json"
	// }
	// slog.Debug("Using config file", slog.String("path", configPath))

	// file, err := os.Open(configPath)
	// if err != nil {
	// 	slog.Error("Failed to open config file", slog.String("path", configPath), slog.Any("error", err))
	// 	os.Exit(1)
	// }
	// defer file.Close()

	// var config Config
	// decoder := json.NewDecoder(file)
	// if err := decoder.Decode(&config); err != nil {
	// 	slog.Error("Failed to decode config file", slog.Any("error", err))
	// 	os.Exit(1)
	// }
	// slog.Debug("Successfully loaded configuration from file")

	// if config.Telemetry.ServiceName == "" {
	// 	// default config
	// 	config.Telemetry = TelemetryConfig{
	// 		ServiceName:     "jenkins-build-beacon",
	// 		ServiceInstance: generateServiceInstanceID(),
	// 		OTLPEndpoint:    "localhost:9090",
	// 		OTLPPath:        "/api/v1/otlp/v1/metrics",
	// 		ExportInterval:  15,
	// 	}
	// 	slog.Debug("Using default telemetry configuration")
	// } else {
	// 	slog.Debug("Using telemetry configuration from file",
	// 		slog.String("service_name", config.Telemetry.ServiceName),
	// 		slog.String("endpoint", config.Telemetry.OTLPEndpoint))
	// }

	// slog.Info("Loaded config", slog.Any("pipelines", len(config.Pipelines)),
	// 	slog.Int("workers", config.Worker),
	// 	slog.String("service_instance", config.Telemetry.ServiceInstance),
	// )

	// ctx := context.Background()

	// metricExporter, err := NewOTLPMetricExporter(
	// 	config.Telemetry.OTLPEndpoint,
	// 	config.Telemetry.OTLPPath,
	// 	config.Telemetry.ServiceName,
	// 	config.Telemetry.ServiceInstance,
	// 	config.Telemetry.ExportInterval,
	// )
	// if err != nil {
	// 	slog.Error("Failed to create metric exporter", slog.Any("error", err))
	// 	os.Exit(1)
	// }
	// defer metricExporter.Shutdown(ctx)

	// if args.Simulate {
	// 	slog.Info("Starting Jenkins build simulation mode",
	// 		slog.Int("pipelines", args.Pipelines),
	// 		slog.Int("interval_seconds", args.Interval))

	// 	simulator := NewJenkinsBuildSimulator(args.Pipelines)
	// 	ticker := time.NewTicker(time.Duration(args.Interval) * time.Second)
	// 	defer ticker.Stop()

	// 	for {
	// 		select {
	// 		case <-ticker.C:
	// 			build := simulator.GenerateBuild()

	// 			slog.Info("Simulating Jenkins build",
	// 				slog.String("pipeline", build.PipelineName),
	// 				slog.Int("build_number", build.BuildNumber),
	// 				slog.String("status", build.Status),
	// 				slog.Float64("duration_seconds", build.DurationSeconds))

	// 			if err := metricExporter.RecordJenkinsBuild(ctx, build); err != nil {
	// 				slog.Error("Failed to send build metrics", slog.Any("error", err))
	// 			}

	// 		case <-waitForShutdown():
	// 			slog.Info("Shutdown signal received, stopping simulation...")
	// 			return
	// 		}
	// 	}
	// } else {
	// 	// Pipeline monitoring mode - just stay idle and monitor
	// 	slog.Info("Starting pipeline monitoring mode (idle - no metrics sent)")
	// 	slog.Debug("Configured pipelines", slog.Any("pipelines", config.Pipelines))

	// 	ticker := time.NewTicker(60 * time.Second) // Check every minute
	// 	defer ticker.Stop()

	// 	for {
	// 		select {
	// 		case <-ticker.C:
	// 			slog.Debug("Pipeline monitoring heartbeat",
	// 				slog.Int("configured_pipelines", len(config.Pipelines)),
	// 				slog.String("mode", "idle_monitoring"))

	// 			// Just log that we're monitoring, don't send metrics
	// 			for i, pipeline := range config.Pipelines {
	// 				slog.Debug("Monitoring pipeline",
	// 					slog.Int("index", i+1),
	// 					slog.String("url", pipeline.URL),
	// 					slog.Int("frequency", pipeline.Frequency))
	// 			}

	// 		case <-waitForShutdown():
	// 			slog.Info("Shutdown signal received, stopping pipeline monitoring...")
	// 			return
	// 		}
	// 	}
	// }
}
