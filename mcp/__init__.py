"""
FleetPulse MCP Server Package

A Model Context Protocol (MCP) server that provides read-only access to FleetPulse
backend data for AI assistants.
"""

__version__ = "1.0.0"
__author__ = "FleetPulse Team"
__description__ = "MCP server for FleetPulse fleet management system"

from .main import app
from .config import get_config
from .tools import get_mcp_tools
from .client import get_backend_client

__all__ = [
    "app",
    "get_config", 
    "get_mcp_tools",
    "get_backend_client"
]