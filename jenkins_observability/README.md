## Thesis

Tracking per-job build duration in Jenkins like a time-series data provides a uniquely valuable and granular level of pipeline observability, enabling effective anomaly detection and a comprehensive understanding of pipeline health beyond traditional system metrics. 

## A Technical Review

This document reviews the technical journey of implementing Jenkins pipeline observability, analyzing the evolution from OpenTelemetry-based metrics to a PostgreSQL-based solution for build duration monitoring. The analysis validates the architectural decisions made and provides recommendations for future implementation.

1. Initial Approach: OpenTelemetry (OTel) Plugin for Jenkins
    - Outcome: Limited success, Too much transformation required to get the build duration per job data from traces.
    - The Jenkins OpenTelemetry plugin is primarily designed for high-level pipeline observability and distributed tracing. While it provides valuable insights into pipeline execution flows, it lacks specific support for retrieving detailed build duration metrics for individual Jenkins jobs. The plugin focuses on:
        - Overall pipeline health metrics
        - Distributed tracing across pipeline stages
        - Security and access monitoring
        - General system performance indicators
    - Requires multiple config changes at trace side to store traces for more than half hour and this shouldn't need compaction to run every few hours.
        - Maybe this is configurable.
2. Secondary Attempt: Attempted to combine Jenkins Metrics plugin with custom OpenTelemetry instrumentation
    - Outcome: Failed due to fundamental data model mismatch
    - Use the Jenkins Metrics plugin to generate build-duration metrics, then export to OTel.
    - Why it didn't work:
        - I tried to use a gauge (e.g., build_duration{job="jobX", build="123"}), but gauges aggregate over time (e.g., Prometheus averages the latest value, not storing individual points).
        - The misconception was that build duration as treated as a metric, but rather an event, a single data point per build. Metrics represent aggregated state, not raw event data. Logs are more suitable (For example: `event_emitter`)
    - Metrics (gauges, histograms) are stateful—they represent the current state (e.g., "last build duration") or aggregated values (e.g., "95th percentile of all builds").
3. Third attempt: Storing Raw Build Events in PostgreSQL
    - Outcome: Successful - meets all requirements for granular build duration tracking
    - This solution succeeds because it aligns with the correct data archetype:
        - Simplicity
        - Each build becomes a discrete record with all associated metadata
        - SQL enables complex queries across multiple dimensions (job, pipeline, time range, build number)
        - Proper indexing supports efficient queries across large datasets
    - Use a custom script to write each build’s duration as a row into PostgreSQL (with columns: build_id, job_name, duration_seconds, timestamp).
    - Visualize in Grafana using PostgreSQL as a data source

## Future considerations

- For data retention implement automated cleanup policies for historical build data
- Consider time-series specific PostgreSQL extensions (TimescaleDB)
- Hybrid approach of using Tempo for traces and Postgres for events.

## Troublehsoot

`org.jenkinsci.plugins.durabletask.BourneShellScript.LAUNCH_DIAGNOSTICS=true` for diagnostics.
Can be executed in Jenkins's script console.

## References

- https://github.com/jenkinsci/opentelemetry-plugin/issues/1159
- https://opentelemetry.io/docs/concepts/signals/metrics/
    - "Unlike request tracing, which is intended to capture request lifecycles and provide context to the individual pieces of a request, metrics are intended to provide statistical information in aggregate."
    - Gauge: Measures a current value at the time it is read. An example would be the fuel gauge in a vehicle. Gauges are synchronous.
    - Histogram: A client-side aggregation of values, such as request latencies. A histogram is a good choice if you are interested in value statistics. For example: How many requests take fewer than 1s?