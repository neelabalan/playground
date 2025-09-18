package main

type JenkinsTimingMetrics struct {
	WaitingTimeSeconds   float64
	BuildableTimeSeconds float64
	BlockedTimeSeconds   float64
	BuildingTimeSeconds  float64
}

func extractJenkinsTimingMetrics(buildDetail map[string]any) *JenkinsTimingMetrics {
	metrics := &JenkinsTimingMetrics{}

	actions, ok := buildDetail["actions"].([]any)
	if !ok {
		return metrics
	}

	for _, action := range actions {
		actionMap, ok := action.(map[string]any)
		if !ok {
			continue
		}

		if actionMap["_class"] == "jenkins.metrics.impl.TimeInQueueAction" {
			// Only use "Time" fields for total cost accounting (includes subtasks)
			// Convert from milliseconds to seconds
			if waitingTime, ok := actionMap["waitingTimeMillis"].(float64); ok {
				metrics.WaitingTimeSeconds = waitingTime / 1000.0
			}

			if buildableTime, ok := actionMap["buildableTimeMillis"].(float64); ok {
				metrics.BuildableTimeSeconds = buildableTime / 1000.0
			}

			if blockedTime, ok := actionMap["blockedTimeMillis"].(float64); ok {
				metrics.BlockedTimeSeconds = blockedTime / 1000.0
			}

			if executingTime, ok := actionMap["executingTimeMillis"].(float64); ok {
				metrics.BuildingTimeSeconds = executingTime / 1000.0
			}

			break
		}
	}

	return metrics
}
