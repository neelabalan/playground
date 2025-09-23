package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"regexp"
	"strconv"
	"strings"

	"jenkins_sentinel/internal/config"
	"jenkins_sentinel/internal/jenkins"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

var appConfig *config.Config
var jenkinsClient *jenkins.Client

type JenkinsLogAnalyzerInput struct {
	JobURL string `json:"job_url" jsonschema:"required" jsonschema_description:"Jenkins job URL (e.g., http://jenkins.example.com/job/my-job/123/)"`
}

type JenkinsLogAnalyzerOutput struct {
	Summary    string   `json:"summary" jsonschema_description:"Summary of the analysis"`
	ErrorLines []string `json:"error_lines" jsonschema_description:"Lines containing ERROR or FAILED keywords"`
	LogSnippet string   `json:"log_snippet" jsonschema_description:"First 10 and last 10 lines of the log"`
}

func parseJobURL(jobURL string) (string, int, error) {
	parsedURL, err := url.Parse(jobURL)
	if err != nil {
		return "", 0, fmt.Errorf("invalid URL: %w", err)
	}

	path := strings.Trim(parsedURL.Path, "/")
	parts := strings.Split(path, "/")

	var buildNumber int
	var pipelinePathParts []string

	for i := len(parts) - 1; i >= 0; i-- {
		if num, err := strconv.Atoi(parts[i]); err == nil {
			buildNumber = num
			pipelinePathParts = parts[:i]
			break
		}
	}

	if buildNumber == 0 {
		return "", 0, fmt.Errorf("could not find build number in URL: %s", jobURL)
	}

	pipelinePath := strings.Join(pipelinePathParts, "/")
	return pipelinePath, buildNumber, nil
}

func AnalyzeJenkinsLogs(ctx context.Context, req *mcp.CallToolRequest, input JenkinsLogAnalyzerInput) (*mcp.CallToolResult, JenkinsLogAnalyzerOutput, error) {
	pipelinePath, buildNumber, err := parseJobURL(input.JobURL)
	if err != nil {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				&mcp.TextContent{Text: fmt.Sprintf("error parsing job URL: %v", err)},
			},
		}, JenkinsLogAnalyzerOutput{}, nil
	}

	logContent, err := jenkinsClient.GetConsoleLog(pipelinePath, buildNumber)
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
	configPath := flag.String("config", "config.json", "Path to the configuration file")
	port := flag.String("port", "8081", "Port to run the MCP server on")
	flag.Parse()

	var err error
	appConfig, err = config.LoadConfig(*configPath)
	if err != nil {
		log.Fatalf("error loading config: %v", err)
	}

	log.Printf("loaded config from %s", *configPath)
	log.Printf("jenkins base URL: %s", appConfig.BaseURL)

	jenkinsClient = jenkins.NewClient(appConfig.BaseURL, appConfig.Username, appConfig.Token, appConfig.Password)
	log.Printf("jenkins client initialized with authentication")

	server := mcp.NewServer(&mcp.Implementation{
		Name:    "jenkins-mcp-server",
		Version: "1.0.0",
	}, nil)

	mcp.AddTool(server, &mcp.Tool{
		Name:        "analyze_jenkins_logs",
		Description: "Analyze Jenkins build console logs for errors and failures. Provide a Jenkins job URL and get back error analysis and log snippets. This tool helps identify build failures and troubleshoot Jenkins pipeline issues.",
	}, AnalyzeJenkinsLogs)

	handler := mcp.NewStreamableHTTPHandler(func(req *http.Request) *mcp.Server {
		return server
	}, &mcp.StreamableHTTPOptions{
		Stateless:    true,
		JSONResponse: true,
	})

	mux := http.NewServeMux()
	mux.Handle("/mcp", handler)

	portAddr := ":" + *port
	log.Printf("starting Jenkins MCP server on port %s", portAddr)
	log.Printf("MCP endpoint: http://localhost%s/mcp", portAddr)

	if err := http.ListenAndServe(portAddr, mux); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
