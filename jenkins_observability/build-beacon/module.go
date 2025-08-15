package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"bytes"
	"io"
	"net/http"
	"os"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/prometheus"
	"go.opentelemetry.io/otel/metric"
	sdkmetric "go.opentelemetry.io/otel/sdk/metric"
	"go.opentelemetry.io/otel/sdk/resource"

	gogoproto "github.com/gogo/protobuf/proto"
	"github.com/golang/snappy"
	prompb "github.com/prometheus/prometheus/prompb"
)

func setup() {
	fmt.Println("Starting OpenTelemetry Prometheus Example")

	res, err := resource.New(
		context.Background(),
		resource.WithAttributes(
			attribute.String("service.name", "otel-prometheus-example"),
		),
	)
	if err != nil {
		log.Fatalf("failed to create resource: %v", err)
	}

	exporter, err := prometheus.New()
	if err != nil {
		log.Fatalf("failed to create prometheus exporter: %v", err)
	}

	meterProvider := sdkmetric.NewMeterProvider(
		sdkmetric.WithResource(res),
		sdkmetric.WithReader(exporter),
	)
	otel.SetMeterProvider(meterProvider)
	meter := otel.GetMeterProvider().Meter("example-meter")

	workDuration, err := meter.Float64Histogram(
		"example_work_duration_ms",
	)
	if err != nil {
		log.Fatalf("failed to create histogram: %v", err)
	}

	ctx := context.Background()
	for i := range 100 {
		doWork(ctx, workDuration, i)
		time.Sleep(time.Second)
	}

	if err := meterProvider.Shutdown(ctx); err != nil {
		log.Printf("Error shutting down meter provider: %v", err)
	}
}
func doWork(ctx context.Context, hist metric.Float64Histogram, workID int) {
	duration := time.Millisecond * time.Duration(100+workID*10)
	metricValue := float64(duration.Milliseconds())
	hist.Record(ctx, metricValue, metric.WithAttributes(attribute.Int("work.id", workID)))
	fmt.Printf("example_work_duration_ms = %f (workID=%d)\n", metricValue, workID)
}

func publish() {
	endpoint := os.Getenv("REMOTE_WRITE_URL")
	if endpoint == "" {
		endpoint = "http://localhost:9090/api/v1/write"
	}

	client := &http.Client{Timeout: 10 * time.Second}

	// build a sample WriteRequest with a few time series
	wr := &prompb.WriteRequest{}
	// now := time.Now().Unix() * 1000 // milliseconds
	base := time.Now().Add(-50*24*time.Hour).Unix() * 1000 // ms, 50 days back

	for i := range 100 {
		ts := prompb.TimeSeries{
			Labels: []prompb.Label{
				{Name: "__name__", Value: "remote_test_metric"},
				{Name: "instance", Value: "remote-writer-1"},
				{Name: "series", Value: fmt.Sprintf("%d", i)},
			},
			Samples: []prompb.Sample{
				{Value: float64(100 + i), Timestamp: int64(base + int64(i*1000))},
			},
		}
		wr.Timeseries = append(wr.Timeseries, ts)
	}

	data, err := gogoproto.Marshal(wr)
	if err != nil {
		panic(err)
	}

	// compress with snappy as Prometheus expects
	compressed := snappy.Encode(nil, data)

	req, err := http.NewRequestWithContext(context.Background(), "POST", endpoint, bytes.NewReader(compressed))
	if err != nil {
		panic(err)
	}
	req.Header.Set("Content-Encoding", "snappy")
	req.Header.Set("Content-Type", "application/x-protobuf")

	resp, err := client.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	fmt.Printf("status=%s body=%s\n", resp.Status, string(body))
}
