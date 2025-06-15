"""
Configuration management for FleetPulse MCP Server.

Handles environment variables and configuration validation.
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field


class MCPConfig(BaseSettings):
    """MCP Server configuration from environment variables."""
    
    # Backend connection
    fleetpulse_backend_url: str = Field(
        default="http://localhost:8000",
        env="FLEETPULSE_BACKEND_URL",
        description="URL of the FleetPulse backend API"
    )
    
    # MCP server settings
    mcp_port: int = Field(
        default=8001,
        env="MCP_PORT", 
        description="Port for the MCP server"
    )
    
    # HTTP client settings
    request_timeout: float = Field(
        default=30.0,
        env="REQUEST_TIMEOUT",
        description="Timeout for backend API requests in seconds"
    )
    
    max_retries: int = Field(
        default=3,
        env="MAX_RETRIES",
        description="Maximum number of retry attempts for backend requests"
    )
    
    # OpenTelemetry configuration  
    otel_service_name: str = Field(
        default="fleetpulse-mcp",
        env="OTEL_SERVICE_NAME",
        description="OpenTelemetry service name"
    )
    
    otel_service_version: str = Field(
        default="1.0.0", 
        env="OTEL_SERVICE_VERSION",
        description="OpenTelemetry service version"
    )
    
    otel_environment: str = Field(
        default="development",
        env="OTEL_ENVIRONMENT", 
        description="OpenTelemetry environment"
    )
    
    otel_enable_telemetry: bool = Field(
        default=True,
        env="OTEL_ENABLE_TELEMETRY",
        description="Enable OpenTelemetry instrumentation"
    )
    
    otel_exporter_type: str = Field(
        default="console",
        env="OTEL_EXPORTER_TYPE",
        description="OpenTelemetry exporter type (console, jaeger, otlp)"
    )
    
    otel_exporter_otlp_endpoint: Optional[str] = Field(
        default=None,
        env="OTEL_EXPORTER_OTLP_ENDPOINT",
        description="OTLP exporter endpoint"
    )
    
    otel_exporter_jaeger_endpoint: str = Field(
        default="http://jaeger:14268/api/traces",
        env="OTEL_EXPORTER_JAEGER_ENDPOINT", 
        description="Jaeger exporter endpoint"
    )
    
    otel_trace_sample_rate: float = Field(
        default=1.0,
        env="OTEL_TRACE_SAMPLE_RATE",
        description="OpenTelemetry trace sampling rate"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global configuration instance
config = MCPConfig()


def get_config() -> MCPConfig:
    """Get the current configuration."""
    return config


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