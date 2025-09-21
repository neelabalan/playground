package main

import (
	"context"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"regexp"
	"strings"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

type JenkinsLogAnalyzerInput struct {
	JobURL string `json:"job_url" jsonschema:"required,description=Jenkins job URL (e.g., http://jenkins.example.com/job/my-job/123/)"`
}

type JenkinsLogAnalyzerOutput struct {
	Summary    string   `json:"summary" jsonschema:"description=Summary of the analysis"`
	ErrorLines []string `json:"error_lines" jsonschema:"description=Lines containing ERROR or FAILED keywords"`
	LogSnippet string   `json:"log_snippet" jsonschema:"description=First 10 and last 10 lines of the log"`
}

func AnalyzeJenkinsLogs(ctx context.Context, req *mcp.CallToolRequest, input JenkinsLogAnalyzerInput) (*mcp.CallToolResult, JenkinsLogAnalyzerOutput, error) {
	consoleURL := strings.TrimSuffix(input.JobURL, "/") + "/consoleText"

	logContent, err := downloadJenkinsLog(consoleURL)
	if err != nil {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				&mcp.TextContent{Text: fmt.Sprintf("error downloading log: %v", err)},
			},
		}, JenkinsLogAnalyzerOutput{}, nil
	}

	analysis := analyzeLog(logContent)

	return &mcp.CallToolResult{
		Content: []mcp.Content{
			&mcp.TextContent{Text: fmt.Sprintf("jenkins log analysis complete\n\nsummary: %s\n\nfound %d error lines\n\nlog snippet:\n%s",
				analysis.Summary, len(analysis.ErrorLines), analysis.LogSnippet)},
		},
	}, analysis, nil
}

func downloadJenkinsLog(consoleURL string) (string, error) {
	resp, err := http.Get(consoleURL)
	if err != nil {
		return "", fmt.Errorf("failed to fetch log: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("HTTP %d: %s", resp.StatusCode, resp.Status)
	}

	tmpDir := "/tmp"
	if _, err := os.Stat(tmpDir); os.IsNotExist(err) {
		tmpDir = "."
	}

	tempFile, err := os.CreateTemp(tmpDir, "jenkins_log_*.txt")
	if err != nil {
		return "", fmt.Errorf("failed to create temp file: %w", err)
	}
	defer func() {
		tempFile.Close()
		os.Remove(tempFile.Name())
	}()

	_, err = io.Copy(tempFile, resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to write log to temp file: %w", err)
	}

	tempFile.Seek(0, 0)
	content, err := io.ReadAll(tempFile)
	if err != nil {
		return "", fmt.Errorf("failed to read temp file: %w", err)
	}

	return string(content), nil
}

func analyzeLog(content string) JenkinsLogAnalyzerOutput {
	lines := strings.Split(content, "\n")

	errorPattern := regexp.MustCompile(`(?i)(error|failed|failure|exception|fatal|abort)`)
	var errorLines []string

	for i, line := range lines {
		if errorPattern.MatchString(line) && strings.TrimSpace(line) != "" {
			errorLines = append(errorLines, fmt.Sprintf("line %d: %s", i+1, strings.TrimSpace(line)))
		}
	}

	var snippetLines []string
	snippetLines = append(snippetLines, "=== FIRST 10 LINES ===")
	for i := 0; i < 10 && i < len(lines); i++ {
		if strings.TrimSpace(lines[i]) != "" {
			snippetLines = append(snippetLines, fmt.Sprintf("%d: %s", i+1, lines[i]))
		}
	}

	snippetLines = append(snippetLines, "", "=== LAST 10 LINES ===")
	start := len(lines) - 10
	if start < 0 {
		start = 0
	}
	for i := start; i < len(lines); i++ {
		if strings.TrimSpace(lines[i]) != "" {
			snippetLines = append(snippetLines, fmt.Sprintf("%d: %s", i+1, lines[i]))
		}
	}

	summary := fmt.Sprintf("analyzed %d lines. found %d lines with error keywords.", len(lines), len(errorLines))
	if len(errorLines) > 0 {
		summary += " build likely failed."
	} else {
		summary += " no obvious errors detected."
	}

	return JenkinsLogAnalyzerOutput{
		Summary:    summary,
		ErrorLines: errorLines,
		LogSnippet: strings.Join(snippetLines, "\n"),
	}
}

func main() {
	server := mcp.NewServer(&mcp.Implementation{
		Name:    "jenkins-log-analyzer",
		Version: "1.0.0",
	}, nil)

	mcp.AddTool(server, &mcp.Tool{
		Name:        "analyze_jenkins_logs",
		Description: "Analyze Jenkins build logs for errors and failures. Provide a Jenkins job URL and get back error analysis and log snippets.",
	}, AnalyzeJenkinsLogs)

	if err := server.Run(context.Background(), &mcp.StdioTransport{}); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
