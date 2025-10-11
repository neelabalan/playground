import datetime

import pydantic


class TimeSeriesPoint(pydantic.BaseModel):
    timestamp: datetime.datetime
    value: float

class MetricTimeSeries(pydantic.BaseModel):
    metric_name: str
    points: list[TimeSeriesPoint]

class DetectionInput(pydantic.BaseModel):
    pipeline_name: str
    time_window_hours: int
    time_series: list[MetricTimeSeries]

class BatchDetectionInput(pydantic.BaseModel):
    pipelines: list[DetectionInput]

class AnomalyResult(pydantic.BaseModel):
    timestamp: datetime.datetime
    metric_name: str
    score: float
    threshold: float
    is_anomaly: bool
    value: float

class DetectionMetadata(pydantic.BaseModel):
    detector_name: str
    processed_points: int
    exeuction_time_ms: int

class DetectionOutput(pydantic.BaseModel):
    anomalies: list[AnomalyResult]
    metadata: DetectionMetadata

class BatchDetectionOutput(pydantic.BaseModel):
    results: list[DetectionOutput]

