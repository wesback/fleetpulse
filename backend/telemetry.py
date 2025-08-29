"""
OpenTelemetry configuration and instrumentation for FleetPulse backend.

This module sets up comprehensive observability including:
- Automatic instrumentation for FastAPI, SQLAlchemy, and HTTP clients
- Custom metrics for business KPIs
- Structured logging with trace correlation
- Resource detection and context propagation
"""

import os
import logging
from typing import Optional

from opentelemetry import trace, metrics, baggage
from opentelemetry.sdk.trace import TracerProvider, Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, DEPLOYMENT_ENVIRONMENT

# Exporters
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Propagators
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.propagators.jaeger import JaegerPropagator
from opentelemetry.propagate import set_global_textmap

# Auto-instrumentation
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Semantic conventions
from opentelemetry.semconv.trace import SpanAttributes

logger = logging.getLogger(__name__)

# Global telemetry objects
tracer: Optional[trace.Tracer] = None
meter: Optional[metrics.Meter] = None

# Custom metrics
request_duration_histogram: Optional[metrics.Histogram] = None
request_counter: Optional[metrics.Counter] = None
error_counter: Optional[metrics.Counter] = None
package_updates_counter: Optional[metrics.Counter] = None
host_counter: Optional[metrics.UpDownCounter] = None


def get_telemetry_config() -> dict:
    """Get telemetry configuration from environment variables."""
    return {
        "service_name": os.getenv("OTEL_SERVICE_NAME", "fleetpulse-backend"),
        "service_version": os.getenv("OTEL_SERVICE_VERSION", "1.0.0"),
        "environment": os.getenv("OTEL_ENVIRONMENT", "development"),
        "jaeger_endpoint": os.getenv("OTEL_EXPORTER_JAEGER_ENDPOINT", "http://jaeger:14268/api/traces"),
        "otlp_endpoint": os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317"),
        "enable_console_exporter": os.getenv("OTEL_ENABLE_CONSOLE_EXPORTER", "false").lower() == "true",
        "trace_sample_rate": float(os.getenv("OTEL_TRACE_SAMPLE_RATE", "1.0")),
        "enable_telemetry": os.getenv("OTEL_ENABLE_TELEMETRY", "true").lower() == "true",
        "exporter_type": os.getenv("OTEL_EXPORTER_TYPE", "jaeger"),  # jaeger, otlp, or console
    }


def setup_resource() -> Resource:
    """Create and configure the OpenTelemetry resource."""
    config = get_telemetry_config()
    
    resource = Resource.create({
        SERVICE_NAME: config["service_name"],
        SERVICE_VERSION: config["service_version"],
        DEPLOYMENT_ENVIRONMENT: config["environment"],
        "service.instance.id": os.getenv("HOSTNAME", "unknown"),
        "service.namespace": "fleetpulse",
    })
    
    return resource


def setup_tracing():
    """Set up OpenTelemetry tracing with appropriate exporters."""
    global tracer
    
    config = get_telemetry_config()
    
    if not config["enable_telemetry"]:
        logger.info("Telemetry disabled via configuration")
        return
    
    # Create resource
    resource = setup_resource()
    
    # Set up tracer provider with sampling
    sampling_rate = config["trace_sample_rate"]
    sampler = TraceIdRatioBased(sampling_rate)
    
    trace.set_tracer_provider(TracerProvider(
        resource=resource,
        sampler=sampler
    ))
    
    # Configure exporter based on type
    exporter_type = config["exporter_type"]
    
    if exporter_type == "jaeger":
        exporter = JaegerExporter(
            agent_host_name=os.getenv("JAEGER_AGENT_HOST", "jaeger"),
            agent_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
        )
    elif exporter_type == "otlp":
        exporter = OTLPSpanExporter(
            endpoint=config["otlp_endpoint"],
            insecure=True,
        )
    else:
        # Console exporter for development
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter
        exporter = ConsoleSpanExporter()
    
    # Add span processor
    span_processor = BatchSpanProcessor(exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    # Set up propagators for context propagation
    from opentelemetry.propagate import set_global_textmap
    
    # Use B3 propagator for now - more compatible
    set_global_textmap(B3MultiFormat())
    
    # Get tracer
    tracer = trace.get_tracer(__name__)
    
    logger.info(f"Tracing configured with {exporter_type} exporter (sampling rate: {sampling_rate})")


def setup_metrics():
    """Set up OpenTelemetry metrics with appropriate exporters."""
    global meter, request_duration_histogram, request_counter, error_counter
    global package_updates_counter, host_counter
    
    config = get_telemetry_config()
    
    if not config["enable_telemetry"]:
        return
    
    # Create resource
    resource = setup_resource()
    
    # Configure metric exporter
    exporter_type = config["exporter_type"]
    
    if exporter_type == "otlp":
        metric_exporter = OTLPMetricExporter(
            endpoint=config["otlp_endpoint"],
            insecure=True,
        )
    else:
        # Console exporter for development
        from opentelemetry.sdk.metrics.export import ConsoleMetricExporter
        metric_exporter = ConsoleMetricExporter()
    
    # Set up metric reader
    metric_reader = PeriodicExportingMetricReader(
        exporter=metric_exporter,
        export_interval_millis=30000,  # Export every 30 seconds
    )
    
    # Set up meter provider
    metrics.set_meter_provider(MeterProvider(
        resource=resource,
        metric_readers=[metric_reader]
    ))
    
    # Get meter
    meter = metrics.get_meter(__name__)
    
    # Create custom metrics
    request_duration_histogram = meter.create_histogram(
        name="http_request_duration_ms",
        description="Duration of HTTP requests in milliseconds",
        unit="ms",
    )
    
    request_counter = meter.create_counter(
        name="http_requests_total",
        description="Total number of HTTP requests",
    )
    
    error_counter = meter.create_counter(
        name="http_errors_total", 
        description="Total number of HTTP errors",
    )
    
    package_updates_counter = meter.create_counter(
        name="package_updates_total",
        description="Total number of package updates reported",
    )
    
    host_counter = meter.create_up_down_counter(
        name="active_hosts_total",
        description="Number of active hosts reporting updates",
    )
    
    logger.info(f"Metrics configured with {exporter_type} exporter")


def setup_auto_instrumentation():
    """Set up automatic instrumentation for frameworks and libraries (except FastAPI)."""
    config = get_telemetry_config()
    
    if not config["enable_telemetry"]:
        return
    
    # Note: FastAPI instrumentation is handled separately in instrument_fastapi_app()
    # to ensure proper app instance is used
    
    try:
        # Instrument SQLAlchemy - this must be done BEFORE creating engine instances
        SQLAlchemyInstrumentor().instrument()
        logger.info("SQLAlchemy instrumentation configured")
        
        # Instrument HTTP clients
        HTTPXClientInstrumentor().instrument()
        RequestsInstrumentor().instrument()
        logger.info("HTTP client instrumentation configured")
        
        logger.info("Auto-instrumentation configured (except FastAPI)")
        
    except Exception as e:
        logger.error(f"Failed to configure auto-instrumentation: {e}")
        # Continue without auto-instrumentation


def instrument_database_engine(engine):
    """Explicitly instrument a database engine for tracing."""
    config = get_telemetry_config()
    
    if not config["enable_telemetry"]:
        return
    
    try:
        # Additional explicit instrumentation for the engine
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        instrumentor = SQLAlchemyInstrumentor()
        
        # Check if already instrumented
        if not instrumentor.is_instrumented_by_opentelemetry:
            instrumentor.instrument_engine(engine)
            logger.info("Database engine explicitly instrumented for tracing")
        else:
            logger.info("Database engine already instrumented")
            
    except Exception as e:
        logger.error(f"Failed to instrument database engine: {e}")


def instrument_fastapi_app(app):
    """Instrument the specific FastAPI app instance for tracing."""
    config = get_telemetry_config()
    
    if not config["enable_telemetry"]:
        return
    
    # Instrument the specific FastAPI app instance
    FastAPIInstrumentor.instrument_app(app)
    
    logger.info("FastAPI app instrumentation completed")


def setup_logging():
    """Configure structured logging with trace correlation."""
    config = get_telemetry_config()
    
    if not config["enable_telemetry"]:
        return
    
    # Configure logging format to include trace information
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - '
        'trace_id=%(otelTraceID)s span_id=%(otelSpanID)s - '
        '%(message)s'
    )
    
    # Add trace context to logs
    class TraceContextFilter(logging.Filter):
        def filter(self, record):
            span = trace.get_current_span()
            if span != trace.INVALID_SPAN:
                span_context = span.get_span_context()
                record.otelTraceID = format(span_context.trace_id, '032x')
                record.otelSpanID = format(span_context.span_id, '016x')
            else:
                record.otelTraceID = '0' * 32
                record.otelSpanID = '0' * 16
            return True
    
    # Apply to root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(TraceContextFilter())
        handler.setFormatter(formatter)
    
    logger.info("Structured logging with trace correlation configured")


def initialize_telemetry():
    """Initialize all OpenTelemetry components."""
    try:
        setup_tracing()
        setup_metrics()
        setup_auto_instrumentation()
        setup_logging()
        logger.info("OpenTelemetry initialization completed successfully")
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")
        # Don't fail application startup if telemetry fails
        pass


def get_tracer() -> trace.Tracer:
    """Get the configured tracer instance."""
    global tracer
    if tracer is None:
        tracer = trace.get_tracer(__name__)
    return tracer


def get_meter() -> metrics.Meter:
    """Get the configured meter instance.""" 
    global meter
    if meter is None:
        meter = metrics.get_meter(__name__)
    return meter


def create_custom_span(name: str, attributes: Optional[dict] = None):
    """Create a custom span with optional attributes."""
    tracer = get_tracer()
    span = tracer.start_span(name)
    
    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)
    
    return span


def record_request_metrics(method: str, endpoint: str, status_code: int, duration_ms: float):
    """Record HTTP request metrics."""
    if request_counter and request_duration_histogram:
        labels = {
            "method": method,
            "endpoint": endpoint,
            "status_code": str(status_code),
        }
        
        request_counter.add(1, labels)
        request_duration_histogram.record(duration_ms, labels)
        
        # Record errors
        if status_code >= 400 and error_counter:
            error_labels = {
                "method": method,
                "endpoint": endpoint,
                "status_code": str(status_code),
            }
            error_counter.add(1, error_labels)
    
    # Also record in Prometheus format
    try:
        from backend.metrics.prometheus import record_prometheus_http_metrics
        record_prometheus_http_metrics(method, endpoint, status_code, duration_ms)
    except ImportError:
        # Prometheus metrics not available
        pass
    except Exception as e:
        logger.error(f"Failed to record Prometheus HTTP metrics: {e}")


def record_package_update_metrics(hostname: str, package_count: int):
    """Record package update business metrics."""
    if package_updates_counter:
        labels = {
            "hostname": hostname,
        }
        package_updates_counter.add(package_count, labels)
    
    # Also record in Prometheus format
    try:
        from backend.metrics.prometheus import record_prometheus_package_update
        record_prometheus_package_update(hostname, package_count)
    except ImportError:
        # Prometheus metrics not available
        pass
    except Exception as e:
        logger.error(f"Failed to record Prometheus package update metrics: {e}")


def record_host_metrics(hostname: str, operation: str = "add"):
    """Record host-related metrics."""
    if host_counter:
        labels = {
            "hostname": hostname,
        }
        value = 1 if operation == "add" else -1
        host_counter.add(value, labels)


def add_baggage(key: str, value: str):
    """Add baggage for context propagation."""
    baggage.set_baggage(key, value)


def get_baggage(key: str) -> Optional[str]:
    """Get baggage value."""
    return baggage.get_baggage(key)


def shutdown_telemetry():
    """Gracefully shutdown telemetry providers."""
    try:
        # Shutdown tracer provider
        tracer_provider = trace.get_tracer_provider()
        if hasattr(tracer_provider, 'shutdown'):
            tracer_provider.shutdown()
        
        # Shutdown meter provider
        meter_provider = metrics.get_meter_provider()
        if hasattr(meter_provider, 'shutdown'):
            meter_provider.shutdown()
        
        logger.info("Telemetry shutdown completed")
    except Exception as e:
        logger.error(f"Error during telemetry shutdown: {e}")