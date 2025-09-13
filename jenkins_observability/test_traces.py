#!/usr/bin/env python3
# /// script
# dependencies = [
#     "opentelemetry-api==1.28.2",
#     "opentelemetry-sdk==1.28.2",
#     "opentelemetry-exporter-otlp==1.28.2"
# ]
# ///

import time

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

trace.set_tracer_provider(TracerProvider())
exporter = OTLPSpanExporter(endpoint='http://localhost:4318/v1/traces', headers={}, timeout=30.0)
span_processor = BatchSpanProcessor(exporter)
trace.get_tracer_provider().add_span_processor(span_processor)
tracer = trace.get_tracer('test-jenkins-traces')

print('creating test trace...')

with tracer.start_as_current_span('test-span') as span:
    span.set_attribute('service.name', 'jenkins-observability')
    span.set_attribute('test.attribute', 'test-value')
    span.set_attribute('jenkins.job', 'test-job')
    print('test span created')
    time.sleep(0.1)

print('forcing flush...')
result = span_processor.force_flush(timeout_millis=5000)
print(f'flush result: {result}')

print('test completed')
