"""
Configuration settings for FleetPulse MCP Server.

This module manages configuration for the MCP server, including
FastAPI backend connection settings and MCP server configuration.
"""

import os
from typing import Optional


class MCPConfig:
    """Configuration class for FleetPulse MCP Server."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # FastAPI backend configuration
        self.fastapi_host = os.environ.get("FLEETPULSE_API_HOST", "localhost")
        self.fastapi_port = int(os.environ.get("FLEETPULSE_API_PORT", "8000"))
        self.fastapi_base_url = f"http://{self.fastapi_host}:{self.fastapi_port}"
        
        # MCP server configuration
        self.mcp_server_name = os.environ.get("MCP_SERVER_NAME", "FleetPulse MCP Server")
        self.mcp_server_version = os.environ.get("MCP_SERVER_VERSION", "1.0.0")
        
        # Request timeout configuration
        self.request_timeout = float(os.environ.get("MCP_REQUEST_TIMEOUT", "30.0"))
        
        # Enable debug logging
        self.debug = os.environ.get("MCP_DEBUG", "false").lower() == "true"
    
    @property
    def base_url(self) -> str:
        """Get the FastAPI base URL."""
        return self.fastapi_base_url
    
    def validate(self) -> bool:
        """Validate configuration settings."""
        if not self.fastapi_host:
            return False
        if not (1 <= self.fastapi_port <= 65535):
            return False
        if self.request_timeout <= 0:
            return False
        return True


# Global configuration instance
config = MCPConfig()