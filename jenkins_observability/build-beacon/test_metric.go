package main

import (
	"bytes"
	"context"
	"fmt"
	"net/http"
	"time"

	"go.opentelemetry.io/collector/pdata/pcommon"
	"go.opentelemetry.io/collector/pdata/pmetric"
	"go.opentelemetry.io/collector/pdata/pmetric/pmetricotlp"
)

func TestJenkinsBuilds(ctx context.Context) error {
	// Hardcoded test data - 5 builds
	buildData := []struct {
		buildNumber int
		duration    float64
	}{
		{101, 245.5},
		{102, 189.2},
		{103, 98.7},
		{104, 312.1},
		{105, 156.8},
	}

	for _, build := range buildData {
		metricData := pmetric.NewMetrics()
		resourceMetrics := metricData.ResourceMetrics().AppendEmpty()
		resourceMetrics.Resource().Attributes().PutStr("service.name", "jenkins-build-beacon")

		scopeMetrics := resourceMetrics.ScopeMetrics().AppendEmpty()
		scopeMetrics.Scope().SetName("github.com/jenkins-build-beacon")

		// Create the build duration metric
		durationMetric := scopeMetrics.Metrics().AppendEmpty()
		durationMetric.SetName("jenkins_build_duration_seconds")
		durationMetric.SetDescription("Jenkins build duration in seconds")

		durationGauge := durationMetric.SetEmptyGauge()
		durationDataPoint := durationGauge.DataPoints().AppendEmpty()
		durationDataPoint.SetDoubleValue(build.duration)

		// Add labels/attributes
		durationDataPoint.Attributes().PutStr("pipeline_name", "test-pipeline")
		durationDataPoint.Attributes().PutStr("job", "test-job")
		durationDataPoint.Attributes().PutStr("build_number", fmt.Sprintf("%d", build.buildNumber))
		durationDataPoint.SetTimestamp(pcommon.NewTimestampFromTime(time.Now()))

		// Send this build's metrics
		fmt.Printf("Sending build %d with duration %.1f seconds\n", build.buildNumber, build.duration)

		if err := sendMetrics(ctx, metricData, "localhost:4318"); err != nil {
			return fmt.Errorf("failed to send metrics for build %d: %w", build.buildNumber, err)
		}

		// Add small delay between sends to simulate real builds
		time.Sleep(100 * time.Millisecond)
	}

	return nil
}

func sendMetrics(ctx context.Context, metrics pmetric.Metrics, endpoint string) error {
	// Create OTLP request
	req := pmetricotlp.NewExportRequestFromMetrics(metrics)

	// Marshal to protobuf
	data, err := req.MarshalProto()
	if err != nil {
		return fmt.Errorf("failed to marshal metrics: %w", err)
	}

	// Send HTTP request
	url := fmt.Sprintf("http://%s/v1/metrics", endpoint)
	httpReq, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(data))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/x-protobuf")

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(httpReq)
	if err != nil {
		return fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("received non-200 status: %d", resp.StatusCode)
	}

	return nil
}
