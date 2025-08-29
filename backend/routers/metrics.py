"""Routes for Prometheus metrics exposition."""
import logging
import os
from fastapi import APIRouter, Response

from backend.metrics.prometheus import generate_prometheus_metrics

logger = logging.getLogger(__name__)

# Get metrics path from environment, default to /metrics
METRICS_PATH = os.environ.get("METRICS_PATH", "/metrics")

router = APIRouter()


@router.get(METRICS_PATH)
def get_metrics():
    """
    Prometheus-compatible metrics endpoint.
    
    Returns metrics in Prometheus exposition format with proper content type.
    Configurable via METRICS_PATH environment variable (default: /metrics).
    """
    try:
        metrics_content = generate_prometheus_metrics()
        
        # Return with proper Prometheus content type
        return Response(
            content=metrics_content,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
        
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        # Return error response in Prometheus format
        error_content = (
            "# HELP fleetpulse_metrics_endpoint_errors_total Metrics endpoint errors\n"
            "# TYPE fleetpulse_metrics_endpoint_errors_total counter\n"
            "fleetpulse_metrics_endpoint_errors_total 1\n"
        )
        return Response(
            content=error_content,
            media_type="text/plain; version=0.0.4; charset=utf-8",
            status_code=500
        )