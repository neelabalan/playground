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
			Timeout: 30 * time.Second,
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
	req, _ := http.NewRequest("GET", fmt.Sprintf("%s/%s/api/json?tree=allBuilds[number]", j.BaseURL, strings.TrimSuffix(pipelinePath, "/")), nil)

	resp, err := j.Client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
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
	req, _ := http.NewRequest("GET", fmt.Sprintf("%s/%s/%d/api/json", j.BaseURL, strings.TrimSuffix(pipelinePath, "/"), buildNumber), nil)
	resp, err := j.Client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
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
	req, _ := http.NewRequest("GET", fmt.Sprintf("%s/%s/%d/wfapi/describe", j.BaseURL, strings.TrimSuffix(pipelinePath, "/"), buildNumber), nil)
	resp, err := j.Client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to execute workflow request: %w", err)
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
