package anomaly

import (
	"context"
	"encoding/json"
	"fmt"
	"os/exec"
	"path/filepath"
	"strings"
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

func (d *PythonDetector) DetectAnomalies(ctx context.Context, input BatchDetectionInput) (*BatchDetectionOutput, error) {
	startTime := time.Now()

	inputJson, err := json.Marshal(input)
	if err != nil {
		return nil, fmt.Errorf("failed to serialize input for %s: %w", d.name, err)
	}

	cmd := exec.CommandContext(ctx, "uv", "run", d.scriptPath)
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
	executionTime := time.Since(startTime).Milliseconds()
	fmt.Printf("execution time: %dms", executionTime)

	return &output, nil
}
