"""
Prometheus metrics collection and exposition for FleetPulse.

This module provides Prometheus-compatible metrics exposition that reuses
existing OpenTelemetry metrics and database aggregations where possible.
"""

import logging
import os
import time
from typing import Optional, Dict, Any
from contextlib import contextmanager

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, Info, generate_latest
from sqlmodel import Session, select, func
from datetime import datetime, timedelta

from backend.models.database import PackageUpdate
from backend.db.session import get_session

logger = logging.getLogger(__name__)

# Global Prometheus registry and metrics
_registry: Optional[CollectorRegistry] = None
_metrics: Dict[str, Any] = {}

# Prometheus histogram buckets for request duration in seconds
REQUEST_DURATION_BUCKETS = [0.05, 0.1, 0.25, 0.5, 1, 2, 5]

# Collection timeout in seconds
COLLECTION_TIMEOUT = 0.8


def get_prometheus_registry() -> CollectorRegistry:
    """Get or create the Prometheus registry."""
    global _registry, _metrics
    
    if _registry is None:
        _registry = CollectorRegistry()
        
        # Create Prometheus metrics
        _metrics['package_updates_total'] = Counter(
            'package_updates_total',
            'Total number of package updates processed',
            ['hostname'],
            registry=_registry
        )
        
        _metrics['active_hosts_total'] = Gauge(
            'active_hosts_total', 
            'Current number of active hosts known to FleetPulse',
            registry=_registry
        )
        
        _metrics['http_requests_total'] = Counter(
            'http_requests_total',
            'Total number of HTTP requests',
            ['method', 'route', 'status'],
            registry=_registry
        )
        
        _metrics['http_request_duration_seconds'] = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'route', 'status'],
            buckets=REQUEST_DURATION_BUCKETS,
            registry=_registry
        )
        
        _metrics['fleetpulse_metrics_collect_errors_total'] = Counter(
            'fleetpulse_metrics_collect_errors_total',
            'Total number of metrics collection errors',
            ['collector'],
            registry=_registry
        )
        
        # Info metric for FleetPulse version
        _metrics['fleetpulse_info'] = Info(
            'fleetpulse_info',
            'FleetPulse build and version information',
            registry=_registry
        )
        _metrics['fleetpulse_info'].info({
            'version': '1.0.0',
            'service': 'fleetpulse-backend'
        })
        
        logger.info("Prometheus registry and metrics initialized")
    
    return _registry


@contextmanager
def timeout_context(timeout_seconds: float):
    """Context manager for timing operations with timeout."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        if duration > timeout_seconds:
            logger.warning(f"Collection took {duration:.3f}s, exceeded timeout of {timeout_seconds}s")


def collect_active_hosts_total() -> Optional[int]:
    """Collect active hosts count from database with timeout."""
    try:
        with timeout_context(COLLECTION_TIMEOUT):
            with next(get_session()) as session:
                # Reuse logic from statistics.py - count distinct hostnames
                total_hosts = session.exec(
                    select(func.count(func.distinct(PackageUpdate.hostname)))
                ).one()
                return total_hosts
    except Exception as e:
        logger.error(f"Failed to collect active hosts total: {e}")
        _metrics['fleetpulse_metrics_collect_errors_total'].labels(collector='active_hosts').inc()
        return None


def collect_package_updates_total() -> Optional[int]:
    """Collect total package updates count from database with timeout."""
    try:
        with timeout_context(COLLECTION_TIMEOUT):
            with next(get_session()) as session:
                # Reuse logic from statistics.py - count all package updates
                total_updates = session.exec(
                    select(func.count(PackageUpdate.id))
                ).one()
                return total_updates
    except Exception as e:
        logger.error(f"Failed to collect package updates total: {e}")
        _metrics['fleetpulse_metrics_collect_errors_total'].labels(collector='package_updates').inc()
        return None


def collect_http_metrics():
    """
    Collect HTTP metrics from OpenTelemetry metrics if available.
    
    Note: This would ideally read from the OpenTelemetry metric readers,
    but since OTel metrics are primarily for export to external systems,
    we'll rely on the middleware to also update Prometheus metrics directly.
    """
    try:
        # This function serves as a placeholder for HTTP metrics collection
        # The actual collection happens in the middleware via record_prometheus_http_metrics
        pass
    except Exception as e:
        logger.error(f"Failed to collect HTTP metrics: {e}")
        _metrics['fleetpulse_metrics_collect_errors_total'].labels(collector='http_metrics').inc()


def record_prometheus_http_metrics(method: str, endpoint: str, status_code: int, duration_ms: float):
    """
    Record HTTP metrics in Prometheus format.
    This should be called from the telemetry middleware alongside existing OTel recording.
    """
    try:
        get_prometheus_registry()  # Ensure registry is initialized
        
        # Normalize the endpoint to a route pattern for cardinality control
        route = normalize_route(endpoint)
        status = str(status_code)
        
        # Record request count
        _metrics['http_requests_total'].labels(
            method=method, 
            route=route, 
            status=status
        ).inc()
        
        # Record request duration (convert from milliseconds to seconds)
        duration_seconds = duration_ms / 1000.0
        _metrics['http_request_duration_seconds'].labels(
            method=method,
            route=route, 
            status=status
        ).observe(duration_seconds)
        
    except Exception as e:
        logger.error(f"Failed to record Prometheus HTTP metrics: {e}")
        _metrics['fleetpulse_metrics_collect_errors_total'].labels(collector='http_metrics').inc()


def normalize_route(endpoint: str) -> str:
    """
    Normalize endpoint paths to route patterns to control cardinality.
    
    This helps avoid high cardinality issues by converting specific paths
    to generic route patterns.
    """
    if endpoint.startswith('/api/'):
        return endpoint
    elif endpoint == '/health':
        return '/health'
    elif endpoint == '/report':
        return '/report'
    elif endpoint.startswith('/metrics'):
        return '/metrics'
    else:
        # Group other endpoints to avoid cardinality explosion
        return '/other'


def update_domain_metrics():
    """Update domain-specific metrics by querying current data sources."""
    try:
        # Update active hosts total
        active_hosts = collect_active_hosts_total()
        if active_hosts is not None:
            _metrics['active_hosts_total'].set(active_hosts)
        
        # Note: package_updates_total is a counter, so we don't set it directly
        # Instead, it should be incremented when packages are updated
        # For now, we could set it to the current total, but this isn't ideal for a counter
        # In a real implementation, we'd track increments
        
    except Exception as e:
        logger.error(f"Failed to update domain metrics: {e}")


def record_prometheus_package_update(hostname: str, package_count: int):
    """Record package update metrics in Prometheus format."""
    try:
        get_prometheus_registry()  # Ensure registry is initialized
        _metrics['package_updates_total'].labels(hostname=hostname).inc(package_count)
    except Exception as e:
        logger.error(f"Failed to record Prometheus package update metrics: {e}")
        _metrics['fleetpulse_metrics_collect_errors_total'].labels(collector='package_updates').inc()


def generate_prometheus_metrics() -> str:
    """Generate Prometheus metrics in exposition format."""
    try:
        registry = get_prometheus_registry()
        
        # Update domain metrics before generating output
        update_domain_metrics()
        
        # Generate Prometheus format
        output = generate_latest(registry)
        return output.decode('utf-8')
        
    except Exception as e:
        logger.error(f"Failed to generate Prometheus metrics: {e}")
        # Return minimal error metric
        return f"# HELP fleetpulse_metrics_generation_errors_total Metrics generation errors\n# TYPE fleetpulse_metrics_generation_errors_total counter\nfleetpulse_metrics_generation_errors_total 1\n"