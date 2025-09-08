## Thesis

Tracking per-job build duration in Jenkins like a time-series data provides a uniquely valuable and granular level of pipeline observability, enabling effective anomaly detection and a comprehensive understanding of pipeline health beyond traditional system metrics. 

## A Technical Review

This document reviews the technical journey of implementing Jenkins pipeline observability, analyzing the evolution from OpenTelemetry-based metrics to a PostgreSQL-based solution for build duration monitoring. The analysis validates the architectural decisions made and provides recommendations for future implementation.

### First approach: OpenTelemetry (OTel) Plugin for Jenkins

> Outcome: Limited success, Too much transformation required to get the build duration per job data from traces.

- The Jenkins OpenTelemetry plugin is primarily designed for high-level pipeline observability and distributed tracing. While it provides valuable insights into pipeline execution flows, it lacks specific support for retrieving detailed build duration metrics for individual Jenkins jobs. The plugin focuses on:
    - Overall pipeline health metrics
    - Distributed tracing across pipeline stages
    - Security and access monitoring
    - General system performance indicators
- Requires multiple config changes at trace side to store traces for more than half hour and this shouldn't need compaction to run every few hours.
    - Maybe this is configurable.

### Second approach: Attempted to combine Jenkins Metrics plugin with custom OpenTelemetry instrumentation

> Outcome: Failed due to fundamental data model mismatch

- Use the Jenkins Metrics plugin to generate build-duration metrics, then export to OTel.
- Why it didn't work:
    - I tried to use a gauge (e.g., build_duration{job="jobX", build="123"}), but gauges aggregate over time (e.g., Prometheus averages the latest value, not storing individual points).
    - The misconception was that build duration as treated as a metric, but rather an event, a single data point per build. Metrics represent aggregated state, not raw event data. Logs are more suitable (For example: `event_emitter`)
- Metrics (gauges, histograms) are stateful—they represent the current state (e.g., "last build duration") or aggregated values (e.g., "95th percentile of all builds").

### Third approach: Storing Raw Build Events in PostgreSQL

> Outcome: Successful - meets all requirements for granular build duration tracking

- This solution succeeds because it aligns with the correct data archetype:
    - Simplicity
    - Each build becomes a discrete record with all associated metadata
    - SQL enables complex queries across multiple dimensions (job, pipeline, time range, build number)
    - Proper indexing supports efficient queries across large datasets
- Use a custom script to write each build’s duration as a row into PostgreSQL (with columns: build_id, job_name, duration_seconds, timestamp).
- Visualize in Grafana using PostgreSQL as a data source

## Jenkins Sentinel

### Flow

```mermaid
flowchart TD
    %% ── 1. Daemon start  ─────────────────────
    A[Daemon starts] --> B["Read config"]
    B --> B1["Initialize DB connection pool"]
    B1 --> B2["Health check; Jenkins API"]
    B2 --> B3{"Jenkins accessible"}
    B3 --> |No| B4["Log error & <br> retry with backoff"]
    B4 --> B2
    B3 --> |Yes| C["Check for pipeline <br> metadata in DB"]
    C --> D["Iterate through pipelines"]
    D --> E{"Data exists?"}
    E --> |No| F["Create fresh data in DB"]
    F --> H["Backfill mode"]
    E --> |Yes| G["Get last build <br> number for pipeline"]
    G --> I1{"API call successful?"}
    I1 --> |No| I2["Handle API error <br> (rate limit/timeout)"]
    I2 --> I3["Add to retry queue"]
    I3 --> R
    I1 --> K["Compute missing build numbers"]
    K --> L{"Missing builds found?"}
    L -->|Yes| M["Fetch details for <br> missing builds"]
    L -->|No| N["Log 'No new/missing builds' & continue"]
    
    M --> M1{"Fetch successful?"}
    M1 --> |No| M2["Add failed builds <br> to build queue"]
    M1 --> |Yes| O["Upsert builds into <br> build_durations"]
    M2 --> P["Update pipeline state"]
    P --> P1
    P1 --> P2["Process retry queue"]
    P2 --> R{"More jobs to process?"}
    N --> R
    
    P --> R
    R --> |Yes| D
    R --> |NO| Q["Sleep for X hour(s)"]
    
    Q --> A

    %% Error handling branch
    style B4 fill:#8f1500
    style I2 fill:#8f1500
    style M2 fill:#8f1500
```

### Data model

- build_queue
    - id
    - job_path
    - build_number
    - last_attempt_at
    - error_message
    - collection_time (TIMESTAMP WITH TIME ZONE): When this build's data was captured/collected by the daemon.
    - collection_status (ENUM: 'complete', 'partial', 'error', 'pending'): 'Partial' for builds collected mid-run; 'pending' for known but uncollected builds during backfill.

- build_table (This stores the per-build metrics. Primary key: (pipeline_name, build_number) for uniqueness)
    - pipeline_name (VARCHAR(255), part of PK): Unique identifier for the Jenkins pipeline/job.
    - build_number (INTEGER, part of PK): Sequential build ID from Jenkins.
    - build_start_time (TIMESTAMP WITH TIME ZONE): When the build began (from Jenkins API).
    - build_end_time (TIMESTAMP WITH TIME ZONE): When the build completed/aborted.
    - status (ENUM: 'success', 'failure', 'aborted', 'unstable', 'not_built', etc.): Matches Jenkins statuses.
    - total_duration (INTERVAL or DOUBLE PRECISION in seconds): Build runtime. Use INTERVAL for human-readable queries, or seconds for easy math/ML.
    - steps_successful (INTEGER): Count of successful steps/stages.
    - steps_failed (INTEGER): Count of failed steps/stages. (Consider adding steps_total = steps_successful + steps_failed for completeness.)
    - steps_skipped (INTEGER, optional addition): If your pipelines have conditional steps, this could track skipped ones for deeper analysis.
    - last_updated (TIMESTAMP WITH TIME ZONE): When this record was last modified (auto-updated via trigger). Useful for auditing changes.
    - error_log (TEXT): Any errors from Jenkins API during collection (e.g., "API timeout"). Null if successful.

### Development and Enhancement Plan

- System handles Jenkins restarts and downtime by remembering last processed build ID and resuming when online
- Collector crashes are handled through state table that prevents data duplication on restart
- Backfilling utility resyncs data when state table gets corrupted or missing
- Jenkins API rate limiting is handled with exponential backoff and retry mechanisms
- Automated cleanup policies manage data retention for historical build data
- Code abstraction layer mitigates impact of Jenkins API changes
- TimescaleDB migration provides automatic partitioning and improved query performance for time-series data
- Hybrid approach uses Tempo for traces and Postgres for events
- Parallel build data collection improves performance with worker threads
- Tracing integrations explore Jenkins Metrics API for generating traces stored in Tempo
- Step level data collection captures successful, failed, and duration metrics for individual stages
- Anomaly detection system identifies optimal algorithms through data collection and simulation
- TimescaleDB migration strategy includes parallel deployment and zero-downtime cutover
- Data lifecycle management automates archival to object storage with parquet format
- Dashboard optimization provides dynamic time ranges and context-aware drill-down capabilities
- LLM powered failure analysis offers triggered root cause analysis with chat integration
- Natural language queries enable questions like "why did the payment-service build #13 fail"
- Multi-jenkins support provides unified dashboard across different environments
- Performance comparison capabilities across multiple Jenkins instances
  
### Business impact
- Developer productivity increased through faster problem identification, reduced MTTR (Mean time to resolution) for build failures, elimination of debugging guesswork, and decreased context switching overhead
- Overall pipeline success rate improvement through proactive anomaly detection
- Infrastructure cost optimization through identification of resource-intensive pipelines
- Reduced deployment cycle time by predicting and preventing pipeline bottlenecks
- Accelerated onboarding of new team members through comprehensive build history visibility

## Troublehsoot

`org.jenkinsci.plugins.durabletask.BourneShellScript.LAUNCH_DIAGNOSTICS=true` for diagnostics.
Can be executed in Jenkins's script console.

## References

- https://github.com/jenkinsci/opentelemetry-plugin/issues/1159
- https://opentelemetry.io/docs/concepts/signals/metrics/
    - "Unlike request tracing, which is intended to capture request lifecycles and provide context to the individual pieces of a request, metrics are intended to provide statistical information in aggregate."
    - Gauge: Measures a current value at the time it is read. An example would be the fuel gauge in a vehicle. Gauges are synchronous.
    - Histogram: A client-side aggregation of values, such as request latencies. A histogram is a good choice if you are interested in value statistics. For example: How many requests take fewer than 1s?