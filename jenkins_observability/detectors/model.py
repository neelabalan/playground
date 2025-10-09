import datetime
import typing

import pydantic


class TimeSeriesPoint(pydantic.BaseModel):
    timestamp: datetime.datetime
    value: float

class MetricTimeSeries(pydantic.BaseModel):
    metric_name: str
    points: list[TimeSeriesPoint]

class DetectorParams(pydantic.BaseModel):
    threshold: float = pydantic.Field(
        default=2.5,
        ge=0.1,
        le=10.0
    )
    min_samples: int = pydantic.Field(
        default=20,
        ge=1,
        le=1000
    )

class DetectionInput(pydantic.BaseModel):
    pipeline_name: str
    time_window_hours: int
    time_series: list[MetricTimeSeries]
    detector_params: dict[str, typing.Any] = pydantic.Field(default_factory=dict)

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

