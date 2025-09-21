package logging

import (
	"fmt"
	"io"
	"log/slog"
	"os"
	"strconv"
	"strings"

	"jenkins_sentinel/internal/config"
)

func Setup(config *config.Config) error {
	var writers []io.Writer
	writers = append(writers, os.Stdout)

	if config.LogFile != "" {
		file, err := os.OpenFile(config.LogFile, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
		if err != nil {
			return fmt.Errorf("failed to open log file: %w", err)
		}
		writers = append(writers, file)
	}

	multiWriter := io.MultiWriter(writers...)

	level := slog.LevelInfo
	if isDebugEnabled(config.LoggingLevel) {
		level = slog.LevelDebug
	}

	logger := slog.New(slog.NewTextHandler(multiWriter, &slog.HandlerOptions{
		Level: level,
	}))

	slog.SetDefault(logger)
	return nil
}

func isDebugEnabled(configLevel string) bool {
	if strings.ToLower(configLevel) == "debug" {
		return true
	}

	debugEnv := os.Getenv("DEBUG")
	if debugEnv == "" {
		return false
	}

	debugValue, err := strconv.ParseBool(debugEnv)
	if err != nil {
		return debugEnv == "1"
	}
	return debugValue
}
