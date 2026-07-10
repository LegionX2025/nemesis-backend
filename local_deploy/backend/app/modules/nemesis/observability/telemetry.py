# nemesis/observability/telemetry.py

import logging
import sys
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from prometheus_client import start_http_server, Counter, Histogram

class TelemetryManager:
    def __init__(self, service_name: str = "nemesis_core"):
        self.service_name = service_name
        self._setup_logging()
        self._setup_tracing()
        self._setup_metrics()

    def _setup_logging(self):
        # Structured JSON logging could be added here for ELK/Datadog
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(trace_id)s] - %(message)s'
        )
        
        class TraceIdFilter(logging.Filter):
            def filter(self, record):
                span = trace.get_current_span()
                record.trace_id = span.get_span_context().trace_id if span.is_recording() else 0
                # Format to 32 char hex
                if record.trace_id != 0:
                    record.trace_id = f"{record.trace_id:032x}"
                else:
                    record.trace_id = "0" * 32
                return True

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        handler.addFilter(TraceIdFilter())

        self.logger = logging.getLogger(self.service_name)
        self.logger.setLevel(logging.INFO)
        # Prevent duplicate logs if handler already exists
        if not self.logger.handlers:
            self.logger.addHandler(handler)

    def _setup_tracing(self):
        provider = TracerProvider()
        processor = BatchSpanProcessor(ConsoleSpanExporter()) # Replace with OTLP Exporter in prod
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        self.tracer = trace.get_tracer(self.service_name)

    def _setup_metrics(self):
        # OpenTelemetry Metrics
        reader = PeriodicExportingMetricReader(ConsoleMetricExporter()) # Replace with OTLP
        provider = MeterProvider(metric_readers=[reader])
        metrics.set_meter_provider(provider)
        self.meter = metrics.get_meter(self.service_name)
        
        # Prometheus Metrics (Exposed on port 8001 by default if started)
        self.prom_tx_processed = Counter('nemesis_transactions_processed_total', 'Total transactions processed by the engine')
        self.prom_trace_duration = Histogram('nemesis_trace_duration_seconds', 'Time spent tracing an entity')
        self.prom_api_calls = Counter('nemesis_api_calls_total', 'Total API calls made', ['chain', 'status'])

    def start_prometheus_server(self, port: int = 8001):
        try:
            start_http_server(port)
            self.logger.info(f"Prometheus metrics server started on port {port}")
        except Exception as e:
            self.logger.error(f"Failed to start Prometheus server: {e}")

    def get_logger(self):
        return self.logger

    def get_tracer(self):
        return self.tracer

# Global instance
telemetry = TelemetryManager()
logger = telemetry.get_logger()
tracer = telemetry.get_tracer()
