"""
Configuration management for FleetPulse MCP Server.

Handles environment variables and configuration validation.
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class MCPConfig:
    """MCP Server configuration from environment variables."""
    
    # Backend connection
    fleetpulse_backend_url: str = "http://localhost:8000"
    
    # MCP server settings
    mcp_port: int = 8001
    
    # HTTP client settings
    request_timeout: float = 30.0
    max_retries: int = 3
    
    # OpenTelemetry configuration  
    otel_service_name: str = "fleetpulse-mcp"
    otel_service_version: str = "1.0.0"
    otel_environment: str = "development"
    otel_enable_telemetry: bool = True
    otel_exporter_type: str = "console"
    otel_exporter_otlp_endpoint: Optional[str] = None
    otel_exporter_jaeger_endpoint: str = "http://jaeger:14268/api/traces"
    otel_trace_sample_rate: float = 1.0

    def __post_init__(self):
        """Load values from environment variables."""
        self.fleetpulse_backend_url = os.getenv("FLEETPULSE_BACKEND_URL", self.fleetpulse_backend_url)
        self.mcp_port = int(os.getenv("MCP_PORT", str(self.mcp_port)))
        self.request_timeout = float(os.getenv("REQUEST_TIMEOUT", str(self.request_timeout)))
        self.max_retries = int(os.getenv("MAX_RETRIES", str(self.max_retries)))
        
        self.otel_service_name = os.getenv("OTEL_SERVICE_NAME", self.otel_service_name)
        self.otel_service_version = os.getenv("OTEL_SERVICE_VERSION", self.otel_service_version)
        self.otel_environment = os.getenv("OTEL_ENVIRONMENT", self.otel_environment)
        self.otel_enable_telemetry = os.getenv("OTEL_ENABLE_TELEMETRY", "true").lower() == "true"
        self.otel_exporter_type = os.getenv("OTEL_EXPORTER_TYPE", self.otel_exporter_type)
        self.otel_exporter_otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", self.otel_exporter_otlp_endpoint)
        self.otel_exporter_jaeger_endpoint = os.getenv("OTEL_EXPORTER_JAEGER_ENDPOINT", self.otel_exporter_jaeger_endpoint)
        self.otel_trace_sample_rate = float(os.getenv("OTEL_TRACE_SAMPLE_RATE", str(self.otel_trace_sample_rate)))


# Global configuration instance
_config: Optional[MCPConfig] = None


def get_config() -> MCPConfig:
    """Get the current configuration."""
    global _config
    if _config is None:
        _config = MCPConfig()
    return _config


def validate_config() -> None:
    """Validate configuration on startup."""
    cfg = get_config()
    
    # Validate backend URL format
    if not cfg.fleetpulse_backend_url.startswith(('http://', 'https://')):
        raise ValueError(f"Invalid backend URL format: {cfg.fleetpulse_backend_url}")
    
    # Validate port range
    if not (1 <= cfg.mcp_port <= 65535):
        raise ValueError(f"Invalid port number: {cfg.mcp_port}")
    
    # Validate timeout
    if cfg.request_timeout <= 0:
        raise ValueError(f"Invalid request timeout: {cfg.request_timeout}")
    
    # Validate retry count
    if cfg.max_retries < 0:
        raise ValueError(f"Invalid max retries: {cfg.max_retries}")
    
    # Validate exporter type
    valid_exporters = {"console", "jaeger", "otlp"}
    if cfg.otel_exporter_type not in valid_exporters:
        raise ValueError(f"Invalid exporter type: {cfg.otel_exporter_type}. Must be one of {valid_exporters}")
    
    # Validate sample rate
    if not (0.0 <= cfg.otel_trace_sample_rate <= 1.0):
        raise ValueError(f"Invalid trace sample rate: {cfg.otel_trace_sample_rate}. Must be between 0.0 and 1.0")