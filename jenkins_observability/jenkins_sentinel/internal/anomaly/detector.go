package anomaly

import (
	"context"
	"fmt"
	"path/filepath"
	"time"
)

type PythonDetector struct {
	name       string
	scriptPath string
}

func NewPythonDetector(name string) *PythonDetector {
	// should be received from config. Not hardcoded path
	scriptPath := filepath.Join("scripts", "detectors", fmt.Sprintf("%s.py", name))
	return &PythonDetector{
		name:       name,
		scriptPath: scriptPath,
	}
}

func (d *PythonDetector) GetName() string {
	return d.name
}

func (d *PythonDetector) DetectAnomalies(ctx context.Context, input DetectionInput) (*DetectionOutput, error) {
	startTime := time.Now()
}
