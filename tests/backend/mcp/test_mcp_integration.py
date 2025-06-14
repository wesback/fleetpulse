"""
Integration tests for FleetPulse MCP Server.

These tests verify that the MCP tools work correctly with the actual FastAPI backend.
They assume the FastAPI backend is running on localhost:8000.
"""

import sys
import os
import pytest
import asyncio
import httpx

# Add backend directory to Python path for imports
backend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend")
sys.path.insert(0, backend_dir)

from fleetpulse_mcp.tools.hosts_tool import list_hosts
from fleetpulse_mcp.tools.history_tool import get_host_history
from fleetpulse_mcp.tools.last_updates_tool import get_last_updates
from fleetpulse_mcp.tools.health_tool import check_health
from fleetpulse_mcp.config.settings import config


@pytest.mark.asyncio
class TestMCPIntegration:
    """Integration tests for MCP tools with actual FastAPI backend."""
    
    async def test_backend_is_running(self):
        """Verify the FastAPI backend is running and accessible."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{config.base_url}/health")
                assert response.status_code == 200
        except Exception as e:
            pytest.skip(f"FastAPI backend not available: {e}")
    
    async def test_health_tool_integration(self):
        """Test health tool with actual backend."""
        result = await check_health()
        
        import json
        parsed = json.loads(result)
        
        # Should contain expected fields
        assert "overall_status" in parsed
        assert "http_status" in parsed
        assert "backend_health" in parsed
        assert "timestamp" in parsed
        
        # If backend is healthy, status should be healthy
        if parsed["http_status"] == 200:
            assert parsed["overall_status"] in ["healthy", "degraded"]
    
    async def test_hosts_tool_integration(self):
        """Test hosts tool with actual backend."""
        result = await list_hosts()
        
        # Should return either "No hosts..." or valid JSON
        if result == "No hosts have reported updates yet.":
            # This is valid for empty backend
            assert True
        else:
            import json
            parsed = json.loads(result)
            assert "hosts" in parsed
            assert "total_count" in parsed
            assert "message" in parsed
    
    async def test_last_updates_tool_integration(self):
        """Test last updates tool with actual backend."""
        result = await get_last_updates()
        
        import json
        parsed = json.loads(result)
        
        assert "hosts" in parsed
        assert "total_count" in parsed
        assert "message" in parsed
        
        # If there are hosts, should have summary
        if parsed["total_count"] > 0:
            assert "summary" in parsed
    
    async def test_history_tool_integration_invalid_host(self):
        """Test history tool with non-existent host."""
        with pytest.raises(Exception) as exc_info:
            await get_host_history("non-existent-host-12345")
        
        # The error message may vary depending on backend state
        error_msg = str(exc_info.value)
        assert ("No update history found" in error_msg or 
                "Database session failed" in error_msg or
                "FleetPulse API returned error" in error_msg)
    
    async def test_history_tool_validation(self):
        """Test history tool parameter validation."""
        # Test empty hostname
        with pytest.raises(Exception) as exc_info:
            await get_host_history("")
        assert "Hostname is required" in str(exc_info.value)
        
        # Test invalid limit
        with pytest.raises(Exception) as exc_info:
            await get_host_history("test-host", limit=0)
        assert "Limit must be between 1 and 1000" in str(exc_info.value)
        
        # Test invalid offset
        with pytest.raises(Exception) as exc_info:
            await get_host_history("test-host", offset=-1)
        assert "Offset must be 0 or greater" in str(exc_info.value)
        
        # Test invalid date format
        with pytest.raises(Exception) as exc_info:
            await get_host_history("test-host", date_from="invalid-date")
        assert "YYYY-MM-DD format" in str(exc_info.value)


class TestMCPConfiguration:
    """Test suite for MCP configuration."""
    
    def test_config_validation_valid(self):
        """Test configuration validation with valid settings."""
        assert config.validate() is True
    
    def test_config_base_url(self):
        """Test configuration base URL construction."""
        assert config.base_url == f"http://{config.fastapi_host}:{config.fastapi_port}"
    
    def test_config_defaults(self):
        """Test configuration defaults."""
        assert config.fastapi_host == "localhost"
        assert config.fastapi_port == 8000
        assert config.mcp_server_name == "FleetPulse MCP Server"
        assert config.request_timeout > 0


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])