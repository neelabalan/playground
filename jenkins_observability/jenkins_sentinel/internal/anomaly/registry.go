package anomaly

import (
	"fmt"
	"log/slog"
	"os"
	"path/filepath"
	"strings"
)

type DetectorRegistry struct {
	detectors map[string]AnomalyDetector
}

func NewDetectorRegistry(detectorDir string) (*DetectorRegistry, error) {
	registry := &DetectorRegistry{
		detectors: make(map[string]AnomalyDetector),
	}

	if err := registry.discoverAndRegister(detectorDir); err != nil {
		return nil, err
	}

	return registry, nil
}

func (r *DetectorRegistry) Get(name string) (AnomalyDetector, error) {
	detector, exists := r.detectors[name]
	if !exists {
		return nil, fmt.Errorf("detector %s not found", name)
	}

	return detector, nil
}

func (r *DetectorRegistry) List() []string {
	names := make([]string, 0, len(r.detectors))
	for name := range r.detectors {
		names = append(names, name)
	}
	return names
}

func (r *DetectorRegistry) discoverAndRegister(detectorDir string) error {
	if detectorDir == "" {
		return fmt.Errorf("detector directory not specified")
	}

	if _, err := os.Stat(detectorDir); os.IsNotExist(err) {
		return fmt.Errorf("detector directory does not exist: %s", detectorDir)
	}

	slog.Info("discovering anomaly detectors", slog.String("directory", detectorDir))

	entries, err := os.ReadDir(detectorDir)
	if err != nil {
		return fmt.Errorf("failed to read detector directory: %w", err)
	}

	discoveredCount := 0
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}

		if !strings.HasSuffix(entry.Name(), ".py") {
			continue
		}

		if strings.HasPrefix(entry.Name(), "_") || strings.HasPrefix(entry.Name(), ".") {
			slog.Debug("skipping file", slog.String("file", entry.Name()))
			continue
		}

		scriptPath := filepath.Join(detectorDir, entry.Name())
		detector := NewPythonDetector(scriptPath)
		name := detector.GetName()

		if _, exists := r.detectors[name]; exists {
			slog.Warn("detector already registered, skipping",
				slog.String("name", name),
				slog.String("file", entry.Name()))
			continue
		}

		r.detectors[name] = detector
		slog.Info("registered anomaly detector", slog.String("name", name))
		discoveredCount++
	}

	slog.Info("detector discovery complete",
		slog.Int("discovered", discoveredCount),
		slog.Int("total", len(r.detectors)))

	return nil
}
