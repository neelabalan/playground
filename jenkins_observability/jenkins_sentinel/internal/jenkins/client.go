package jenkins

import (
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"strings"
	"time"
)

const (
	defaultHTTPTimeout = 30 * time.Second
	maxRetryAttempts   = 5
	initialBackoff     = 500 * time.Millisecond
	maxBackoffDelay    = 8 * time.Second
)

type Client struct {
	BaseURL string
	Client  *http.Client
}

type authTransport struct {
	username string
	token    string
	password string
	useToken bool
	base     http.RoundTripper
}

func (t *authTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	if t.useToken {
		req.SetBasicAuth(t.username, t.token)
	} else {
		req.SetBasicAuth(t.username, t.password)
	}
	req.Header.Set("Accept", "application/json")
	return t.base.RoundTrip(req)
}

func NewClient(baseURL, username, token, password string) *Client {
	// Determine authentication method
	useToken := token != ""

	if !useToken {
		slog.Warn("Jenkins API token is empty or missing, falling back to password authentication",
			slog.String("username", username),
			slog.String("recommendation", "Generate an API token in Jenkins (Manage Jenkins > Manage Users > [username] > Configure > API Token) and use it instead of password for better security"))
	} else {
		slog.Info("Using Jenkins API token authentication", slog.String("username", username))
	}

	return &Client{
		BaseURL: strings.TrimSuffix(baseURL, "/"),
		Client: &http.Client{
			Timeout: defaultHTTPTimeout,
			Transport: &authTransport{
				username: username,
				token:    token,
				password: password,
				useToken: useToken,
				base:     http.DefaultTransport,
			},
		},
	}
}

type Build struct {
	Number int    `json:"number"`
	Class  string `json:"_class"`
}

type JobResponse struct {
	AllBuilds []Build `json:"allBuilds"`
}

func (j *Client) GetBuildNumbers(pipelinePath string) ([]int, error) {
	url := fmt.Sprintf("%s/%s/api/json?tree=allBuilds[number]", j.BaseURL, strings.TrimSuffix(pipelinePath, "/"))
	resp, err := j.doWithBackoff(http.MethodGet, url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("jenkins API returned status %d", resp.StatusCode)
	}

	bodyBytes, _ := io.ReadAll(resp.Body)

	slog.Debug("Jenkins API response for build numbers", slog.String("json", string(bodyBytes)))

	var response JobResponse
	if err := json.Unmarshal(bodyBytes, &response); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	numbers := make([]int, len(response.AllBuilds))
	for i, build := range response.AllBuilds {
		numbers[i] = build.Number
	}

	return numbers, nil
}

func (j *Client) GetBuildDetail(pipelinePath string, buildNumber int) (map[string]any, error) {
	url := fmt.Sprintf("%s/%s/%d/api/json", j.BaseURL, strings.TrimSuffix(pipelinePath, "/"), buildNumber)
	resp, err := j.doWithBackoff(http.MethodGet, url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("jenkins API returned status %d for build %d", resp.StatusCode, buildNumber)
	}

	bodyBytes, _ := io.ReadAll(resp.Body)
	slog.Debug("Jenkins API response for build detail", slog.String("json", string(bodyBytes)))

	var buildDetail map[string]any
	if err := json.Unmarshal(bodyBytes, &buildDetail); err != nil {
		return nil, fmt.Errorf("failed to decode build detail: %w", err)
	}

	return buildDetail, nil
}

func (j *Client) GetWorkflowDescribe(pipelinePath string, buildNumber int) (map[string]any, error) {
	url := fmt.Sprintf("%s/%s/%d/wfapi/describe", j.BaseURL, strings.TrimSuffix(pipelinePath, "/"), buildNumber)
	resp, err := j.doWithBackoff(http.MethodGet, url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("jenkins workflow API returned status %d for build %d", resp.StatusCode, buildNumber)
	}

	bodyBytes, _ := io.ReadAll(resp.Body)
	slog.Debug("Jenkins workflow API response", slog.String("json", string(bodyBytes)))

	var workflowDetail map[string]any
	if err := json.Unmarshal(bodyBytes, &workflowDetail); err != nil {
		return nil, fmt.Errorf("failed to decode workflow detail: %w", err)
	}

	return workflowDetail, nil
}

func (j *Client) GetConsoleLog(pipelinePath string, buildNumber int) (string, error) {
	req, _ := http.NewRequest("GET", fmt.Sprintf("%s/%s/%d/consoleText", j.BaseURL, strings.TrimSuffix(pipelinePath, "/"), buildNumber), nil)
	resp, err := j.Client.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to execute console log request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("jenkins console API returned status %d for build %d", resp.StatusCode, buildNumber)
	}

	bodyBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read console log: %w", err)
	}

	return string(bodyBytes), nil
}

func (j *Client) doWithBackoff(method, url string) (*http.Response, error) {
	var lastErr error
	for attempt := 0; attempt < maxRetryAttempts; attempt++ {
		req, err := http.NewRequest(method, url, nil)
		if err != nil {
			return nil, fmt.Errorf("failed to create request: %w", err)
		}

		resp, err := j.Client.Do(req)
		if err == nil && !shouldRetryStatus(resp.StatusCode) {
			return resp, nil
		}

		if err != nil {
			lastErr = err
		} else {
			lastErr = fmt.Errorf("jenkins API returned status %d", resp.StatusCode)
			resp.Body.Close()
		}

		if attempt == maxRetryAttempts-1 {
			break
		}

		backoff := backoffDelay(attempt)
		slog.Warn("retrying Jenkins API request", slog.String("method", method), slog.String("url", url), slog.Int("attempt", attempt+1), slog.Duration("backoff", backoff), slog.Any("error", lastErr))
		time.Sleep(backoff)
	}

	if lastErr == nil {
		lastErr = fmt.Errorf("jenkins API request failed")
	}

	return nil, fmt.Errorf("jenkins API request failed after %d attempts: %w", maxRetryAttempts, lastErr)
}

func shouldRetryStatus(status int) bool {
	return status == http.StatusTooManyRequests || status == http.StatusRequestTimeout || status >= http.StatusInternalServerError
}

func backoffDelay(attempt int) time.Duration {
	delay := initialBackoff << attempt
	if delay > maxBackoffDelay {
		delay = maxBackoffDelay
	}
	return delay
}
