#!/usr/bin/env python3
# /// script
# dependencies = [
#     "pydantic>=2.0.0"
# ]
# ///

import argparse
import json
import math
import sys
import time

import _models


class ZScoreDetector:
    def calculate_mean(self, values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    def calculate_std_dev(self, values: list[float], mean: float) -> float:
        if len(values) <= 1:
            return 0.0
        return math.sqrt(sum((x-mean) ** 2 for x in values) / (len(values) - 1))

    def detect_anomalies_for_pipeline(
        self,
        pipeline_data: _models.DetectionInput,
        threshold: float,
        min_samples: int
    ) -> _models.DetectionOutput:
        start_time = time.time()
        anomalies = []
        total_points = 0

        for time_series in pipeline_data.time_series:
            values = [point.value for point in time_series.points]
            total_points += len(values)

            if len(values) < min_samples:
                continue

            mean = self.calculate_mean(values)
            std_dev = self.calculate_std_dev(values, mean)

            if std_dev == 0:
                continue

            for point in time_series.points:
                z_score = abs((point.value - mean) / std_dev)
                is_anomaly = z_score > threshold

                if is_anomaly:
                    anomalies.append(_models.AnomalyResult(
                        timestamp=point.timestamp,
                        metric_name=time_series.metric_name,
                        score=z_score,
                        threshold=threshold,
                        is_anomaly=is_anomaly,
                        value=point.value,
                        build_number=point.build_number
                    ))

        execution_time_ms = int((time.time() - start_time) * 1000)

        return _models.DetectionOutput(
            anomalies=anomalies,
            metadata=_models.DetectionMetadata(
                detector_name="zscore",
                processed_points=total_points,
                execution_time_ms=execution_time_ms
            )
        )

def main():
    parser = argparse.ArgumentParser(description="Z-Score anomaly detector")
    parser.add_argument('--threshold', type=float, required=True)
    parser.add_argument('--min-samples', type=int, required=True)
    args = parser.parse_args()

    input_data = json.load(sys.stdin)
    batch_input = _models.BatchDetectionInput(**input_data)

    detector = ZScoreDetector()
    results = []

    for pipeline_data in batch_input.pipelines:
        output = detector.detect_anomalies_for_pipeline(
            pipeline_data,
            args.threshold,
            args.min_samples
        )
        results.append(output)

    batch_output = _models.BatchDetectionOutput(results=results)
    print(batch_output.model_dump_json())

if __name__ == "__main__":
    main()






