"""
Centralized telemetry utilities for FleetPulse backend.

This module provides a consistent interface for telemetry operations across all
router modules, with graceful fallbacks when telemetry dependencies are not available.
"""
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Try to import telemetry functions with graceful fallback
try:
    from telemetry import (
        create_custom_span,
        record_package_update_metrics,
        record_host_metrics,
        add_baggage,
        get_tracer,
        get_meter,
    )
    TELEMETRY_ENABLED = True
    logger.info("Telemetry enabled - all telemetry functions available")
except ImportError as e:
    logger.warning(f"Telemetry dependencies not available: {e}")
    TELEMETRY_ENABLED = False
    
    # Create stub functions that do nothing
    def create_custom_span(name: str, attributes: Optional[dict] = None):
        """Stub span context manager."""
        class DummySpan:
            def __enter__(self): 
                return self
            def __exit__(self, *args): 
                pass
            def set_attribute(self, key: str, value: Any): 
                pass
        return DummySpan()
    
    def record_package_update_metrics(*args, **kwargs): 
        """Stub package update metrics function."""
        pass
    
    def record_host_metrics(*args, **kwargs): 
        """Stub host metrics function."""
        pass
    
    def add_baggage(*args, **kwargs): 
        """Stub baggage function."""
        pass
    
    def get_tracer(*args, **kwargs): 
        """Stub tracer function."""
        return None
        
    def get_meter(*args, **kwargs):
        """Stub meter function."""
        return None


# Provide a global tracer stub for patching in tests
class DummyTracer:
    def start_as_current_span(self, name, *args, **kwargs):
        class DummySpan:
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def set_attribute(self, k, v): pass
        return DummySpan()

tracer = DummyTracer()


def is_telemetry_enabled() -> bool:
    """Check if telemetry is enabled and available."""
    return TELEMETRY_ENABLED


def create_business_span(operation_name: str, **attributes):
    """
    Create a custom span for business operations with standardized attributes.
    
    Args:
        operation_name: Name of the business operation
        **attributes: Additional attributes to add to the span
    """
    return create_custom_span(f"business.{operation_name}", attributes)


def record_host_query_metrics(operation: str, hostname: Optional[str] = None, result_count: Optional[int] = None):
    """
    Record metrics for host query operations.
    
    Args:
        operation: Type of host operation (list_hosts, host_history, last_updates)
        hostname: Optional hostname for specific host operations
        result_count: Optional count of results returned
    """
    if not TELEMETRY_ENABLED:
        return
        
    # Add operation-specific baggage
    add_baggage("host.operation", operation)
    if hostname:
        add_baggage("host.hostname", hostname)
    if result_count is not None:
        add_baggage("host.result_count", str(result_count))