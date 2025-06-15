"""
OpenTelemetry instrumentation for FleetPulse MCP Server.

Provides comprehensive observability with tracing and metrics.
"""

import os
import logging
from typing import Optional
from contextlib import contextmanager

from opentelemetry import trace, metrics, baggage
from opentelemetry.sdk.trace import TracerProvider, Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, DEPLOYMENT_ENVIRONMENT

# Exporters
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Instrumentation
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

# Propagators
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.propagate import set_global_textmap

from .config import get_config


logger = logging.getLogger(__name__)

# Global telemetry components
tracer = None
meter = None


def setup_resource() -> Resource:
    """Create and configure the OpenTelemetry resource."""
    config = get_config()
    
    resource = Resource.create({
        SERVICE_NAME: config.otel_service_name,
        SERVICE_VERSION: config.otel_service_version,
        DEPLOYMENT_ENVIRONMENT: config.otel_environment,
        "service.instance.id": os.getenv("HOSTNAME", "unknown"),
        "service.namespace": "fleetpulse",
        "service.component": "mcp-server",
    })
    
    return resource


def setup_tracing():
    """Set up OpenTelemetry tracing with appropriate exporters."""
    config = get_config()
    resource = setup_resource()
    
    # Create tracer provider
    trace.set_tracer_provider(TracerProvider(
        resource=resource,
        sampler=trace.TraceIdRatioBased(config.otel_trace_sample_rate)
    ))
    
    # Choose exporter based on configuration
    exporter_type = config.otel_exporter_type.lower()
    
    if exporter_type == "jaeger":
        exporter = JaegerExporter(
            agent_host_name=config.otel_exporter_jaeger_endpoint.split("://")[1].split(":")[0],
            agent_port=14268,
            collector_endpoint=config.otel_exporter_jaeger_endpoint,
        )
    elif exporter_type == "otlp":
        endpoint = config.otel_exporter_otlp_endpoint or "http://localhost:4317"
        exporter = OTLPSpanExporter(endpoint=endpoint)
    else:  # console
        exporter = ConsoleSpanExporter()
    
    # Add span processor
    span_processor = BatchSpanProcessor(exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    # Set up propagators
    set_global_textmap(B3MultiFormat())
    
    logger.info(f"Tracing configured with {exporter_type} exporter")


def setup_metrics():
    """Set up OpenTelemetry metrics with appropriate exporters."""
    config = get_config()
    resource = setup_resource()
    
    # Choose exporter based on configuration
    exporter_type = config.otel_exporter_type.lower()
    
    if exporter_type == "otlp":
        endpoint = config.otel_exporter_otlp_endpoint or "http://localhost:4317"
        metric_exporter = OTLPMetricExporter(endpoint=endpoint)
    else:  # console or jaeger (fallback to console for metrics)
        metric_exporter = ConsoleMetricExporter()
    
    # Create metric reader
    metric_reader = PeriodicExportingMetricReader(
        exporter=metric_exporter,
        export_interval_millis=5000  # Export every 5 seconds
    )
    
    # Set up meter provider
    metrics.set_meter_provider(MeterProvider(
        resource=resource,
        metric_readers=[metric_reader]
    ))
    
    logger.info(f"Metrics configured with {exporter_type} exporter")


def initialize_telemetry():
    """Initialize OpenTelemetry with all instrumentation."""
    global tracer, meter
    
    config = get_config()
    
    if not config.otel_enable_telemetry:
        logger.info("OpenTelemetry is disabled")
        return
    
    try:
        # Set up tracing and metrics
        setup_tracing()
        setup_metrics()
        
        # Get tracer and meter instances
        tracer = trace.get_tracer(__name__)
        meter = metrics.get_meter(__name__)
        
        # Auto-instrument HTTP clients
        HTTPXClientInstrumentor().instrument()
        
        logger.info("OpenTelemetry initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")
        # Continue without telemetry
        tracer = None
        meter = None


def instrument_fastapi_app(app):
    """Instrument FastAPI application."""
    if tracer is not None:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumentation applied")


def shutdown_telemetry():
    """Shutdown OpenTelemetry components."""
    logger.info("Shutting down OpenTelemetry...")
    
    # Shutdown tracer provider
    if hasattr(trace.get_tracer_provider(), 'shutdown'):
        trace.get_tracer_provider().shutdown()
    
    # Shutdown meter provider  
    if hasattr(metrics.get_meter_provider(), 'shutdown'):
        metrics.get_meter_provider().shutdown()


@contextmanager
def create_custom_span(name: str, attributes: Optional[dict] = None):
    """Create a custom span with optional attributes."""
    if tracer is None:
        # Return a dummy context manager if telemetry is disabled
        class DummySpan:
            def set_attribute(self, key, value): pass
            def set_status(self, status): pass
            def record_exception(self, exception): pass
        
        yield DummySpan()
        return
    
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        yield span


def create_metrics():
    """Create custom metrics for the MCP server."""
    if meter is None:
        return {}
    
    try:
        return {
            "mcp_requests_total": meter.create_counter(
                name="mcp_requests_total",
                description="Total number of MCP requests",
                unit="1"
            ),
            "mcp_request_duration": meter.create_histogram(
                name="mcp_request_duration_seconds",
                description="MCP request duration",
                unit="s"
            ),
            "backend_api_requests_total": meter.create_counter(
                name="backend_api_requests_total", 
                description="Total number of backend API requests",
                unit="1"
            ),
            "backend_api_duration": meter.create_histogram(
                name="backend_api_duration_seconds",
                description="Backend API request duration",
                unit="s"
            ),
            "mcp_active_connections": meter.create_up_down_counter(
                name="mcp_active_connections",
                description="Current active HTTP connections",
                unit="1"
            ),
        }
    except Exception as e:
        logger.error(f"Failed to create metrics: {e}")
        return {}


def record_mcp_request_metrics(endpoint: str, status_code: int, duration_seconds: float):
    """Record metrics for MCP requests."""
    if meter is None:
        return
    
    try:
        metrics_dict = create_metrics()
        
        # Record request count
        if "mcp_requests_total" in metrics_dict:
            metrics_dict["mcp_requests_total"].add(
                1, 
                attributes={"endpoint": endpoint, "status_code": str(status_code)}
            )
        
        # Record request duration
        if "mcp_request_duration" in metrics_dict:
            metrics_dict["mcp_request_duration"].record(
                duration_seconds,
                attributes={"endpoint": endpoint}
            )
            
    except Exception as e:
        logger.error(f"Failed to record MCP request metrics: {e}")


def record_backend_api_metrics(endpoint: str, status_code: int, duration_seconds: float):
    """Record metrics for backend API requests."""
    if meter is None:
        return
    
    try:
        metrics_dict = create_metrics()
        
        # Record request count
        if "backend_api_requests_total" in metrics_dict:
            metrics_dict["backend_api_requests_total"].add(
                1,
                attributes={"backend_endpoint": endpoint, "status_code": str(status_code)}
            )
        
        # Record request duration
        if "backend_api_duration" in metrics_dict:
            metrics_dict["backend_api_duration"].record(
                duration_seconds,
                attributes={"backend_endpoint": endpoint}
            )
            
    except Exception as e:
        logger.error(f"Failed to record backend API metrics: {e}")


def add_baggage(key: str, value: str):
    """Add baggage to the current context."""
    try:
        baggage.set_baggage(key, value)
    except Exception as e:
        logger.error(f"Failed to add baggage: {e}")


def get_tracer():
    """Get the current tracer instance."""
    return tracer