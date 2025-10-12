package anomaly

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

type PythonDetector struct {
	name       string
	scriptPath string
}

func NewPythonDetector(scriptPath string) *PythonDetector {
	filename := filepath.Base(scriptPath)
	name := strings.TrimSuffix(filename, ".py")
	return &PythonDetector{
		name:       name,
		scriptPath: scriptPath,
	}
}

func (d *PythonDetector) GetName() string {
	return d.name
}

func (d *PythonDetector) DetectAnomalies(ctx context.Context, input BatchDetectionInput, params map[string]string) (*BatchDetectionOutput, error) {
	startTime := time.Now()

	inputJson, err := json.Marshal(input)
	if err != nil {
		return nil, fmt.Errorf("failed to serialize input for %s: %w", d.name, err)
	}

	args := []string{"run", d.scriptPath}
	for key, value := range params {
		args = append(args, fmt.Sprintf("--%s", key), value)
	}

	cmd := exec.CommandContext(ctx, "uv", args...)
	cmd.Stdin = strings.NewReader(string(inputJson))

	outputBytes, err := cmd.Output()
	if err != nil {
		if exitError, ok := err.(*exec.ExitError); ok {
			return nil, fmt.Errorf("python detector %s failed with stderr: %s", d.name, string(exitError.Stderr))
		}
		return nil, fmt.Errorf("python detector %s execution failed: %w", d.name, err)
	}

	var output BatchDetectionOutput
	if err := json.Unmarshal(outputBytes, &output); err != nil {
		return nil, fmt.Errorf("failed to parse output from %s: %w", d.name, err)
	}

	slog.Info("detector completed",
		slog.String("detector", d.name),
		slog.Duration("duration", time.Since(startTime)))

	return &output, nil
}

type PipelineAnomalyDetectionJob struct {
	PipelineName string
	DetectorName string
	Input        DetectionInput
	Params       map[string]string
}

type PipelineAnomalyDetectionResult struct {
	PipelineName string
	DetectorName string
	Output       *DetectionOutput
	Error        error
}

func RunPipelineDetections(ctx context.Context, registry *DetectorRegistry, jobs []PipelineAnomalyDetectionJob, maxParallel int) []PipelineAnomalyDetectionResult {
	if len(jobs) == 0 {
		return nil
	}

	results := make([]PipelineAnomalyDetectionResult, len(jobs))
	jobChan := make(chan int, len(jobs))
	var wg sync.WaitGroup

	for i := 0; i < maxParallel; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for idx := range jobChan {
				job := jobs[idx]

				detector, err := registry.Get(job.DetectorName)
				if err != nil {
					results[idx] = PipelineAnomalyDetectionResult{
						PipelineName: job.PipelineName,
						DetectorName: job.DetectorName,
						Error:        err,
					}
					slog.Error("detector not found",
						slog.String("pipeline", job.PipelineName),
						slog.String("detector", job.DetectorName))
					continue
				}

				batchInput := BatchDetectionInput{Pipelines: []DetectionInput{job.Input}}
				output, err := detector.DetectAnomalies(ctx, batchInput, job.Params)

				if err != nil {
					results[idx] = PipelineAnomalyDetectionResult{
						PipelineName: job.PipelineName,
						DetectorName: job.DetectorName,
						Error:        err,
					}
					slog.Error("detection failed",
						slog.String("pipeline", job.PipelineName),
						slog.String("detector", job.DetectorName),
						slog.String("error", err.Error()))
					continue
				}

				if len(output.Results) > 0 {
					results[idx] = PipelineAnomalyDetectionResult{
						PipelineName: job.PipelineName,
						DetectorName: job.DetectorName,
						Output:       &output.Results[0],
						Error:        nil,
					}
				}
			}
		}()
	}

	for i := range jobs {
		jobChan <- i
	}
	close(jobChan)

	wg.Wait()
	return results
}
