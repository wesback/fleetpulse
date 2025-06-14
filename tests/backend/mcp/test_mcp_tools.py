"""
Tests for FleetPulse MCP Server functionality.

These tests verify that the MCP tools correctly interact with the FastAPI backend
and return properly formatted responses.
"""

import sys
import os
import pytest
import asyncio
import httpx
from unittest.mock import patch, AsyncMock

# Add backend directory to Python path for imports
backend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend")
sys.path.insert(0, backend_dir)

from fleetpulse_mcp.tools.hosts_tool import list_hosts
from fleetpulse_mcp.tools.history_tool import get_host_history
from fleetpulse_mcp.tools.last_updates_tool import get_last_updates
from fleetpulse_mcp.tools.health_tool import check_health
from fleetpulse_mcp.config.settings import config


class TestMCPTools:
    """Test suite for MCP tools."""
    
    @pytest.mark.asyncio
    async def test_health_tool_success(self):
        """Test health tool with successful response."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.reason_phrase = "OK"
        mock_response.json.return_value = {
            "status": "healthy",
            "database": "connected"
        }
        mock_response.raise_for_status.return_value = None
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await check_health()
            
            # Verify result is JSON and contains expected fields
            import json
            parsed = json.loads(result)
            assert parsed["overall_status"] == "healthy"
            assert parsed["http_status"] == 200
            assert "timestamp" in parsed
    
    @pytest.mark.asyncio
    async def test_health_tool_unhealthy(self):
        """Test health tool with unhealthy response."""
        mock_response = AsyncMock()
        mock_response.status_code = 503
        mock_response.reason_phrase = "Service Unavailable"
        mock_response.json.return_value = {
            "status": "unhealthy",
            "database": "disconnected"
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await check_health()
            
            # Should return structured error, not raise exception
            import json
            parsed = json.loads(result)
            assert parsed["overall_status"] == "unhealthy"
            assert parsed["http_status"] == 503
    
    @pytest.mark.asyncio
    async def test_hosts_tool_success(self):
        """Test hosts tool with successful response."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "hosts": ["server-01", "server-02"]
        }
        mock_response.raise_for_status.return_value = None
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await list_hosts()
            
            import json
            parsed = json.loads(result)
            assert "hosts" in parsed
            assert parsed["total_count"] == 2
            assert "server-01" in parsed["hosts"]
    
    @pytest.mark.asyncio
    async def test_hosts_tool_no_hosts(self):
        """Test hosts tool with no hosts."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"hosts": []}
        mock_response.raise_for_status.return_value = None
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await list_hosts()
            
            assert result == "No hosts have reported updates yet."
    
    @pytest.mark.asyncio
    async def test_history_tool_success(self):
        """Test history tool with successful response."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "hostname": "test-host",
                    "name": "nginx",
                    "old_version": "1.18.0",
                    "new_version": "1.20.1",
                    "update_date": "2025-06-14"
                }
            ],
            "total": 1,
            "limit": 50,
            "offset": 0
        }
        mock_response.raise_for_status.return_value = None
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await get_host_history("test-host")
            
            import json
            parsed = json.loads(result)
            assert parsed["hostname"] == "test-host"
            assert "update_history" in parsed
            assert "pagination" in parsed
            assert len(parsed["update_history"]) == 1
    
    @pytest.mark.asyncio
    async def test_history_tool_with_filters(self):
        """Test history tool with filters."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [],
            "total": 0,
            "limit": 10,
            "offset": 0
        }
        mock_response.raise_for_status.return_value = None
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await get_host_history(
                hostname="test-host",
                date_from="2025-06-01",
                date_to="2025-06-14",
                os="ubuntu",
                package="nginx",
                limit=10,
                offset=5
            )
            
            import json
            parsed = json.loads(result)
            assert parsed["filters_applied"]["date_from"] == "2025-06-01"
            assert parsed["filters_applied"]["os"] == "ubuntu"
            assert parsed["filters_applied"]["package"] == "nginx"
    
    @pytest.mark.asyncio
    async def test_history_tool_invalid_hostname(self):
        """Test history tool with invalid hostname."""
        with pytest.raises(Exception) as exc_info:
            await get_host_history("")
        
        assert "hostname is required" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_history_tool_invalid_limit(self):
        """Test history tool with invalid limit."""
        with pytest.raises(Exception) as exc_info:
            await get_host_history("test-host", limit=0)
        
        assert "Limit must be between 1 and 1000" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_last_updates_tool_success(self):
        """Test last updates tool with successful response."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "hostname": "server-01",
                "os": "ubuntu",
                "last_update": "2025-06-14"
            },
            {
                "hostname": "server-02", 
                "os": "centos",
                "last_update": "2025-06-13"
            }
        ]
        mock_response.raise_for_status.return_value = None
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await get_last_updates()
            
            import json
            parsed = json.loads(result)
            assert parsed["total_count"] == 2
            assert "summary" in parsed
            assert parsed["summary"]["most_recent_update"] == "2025-06-14"
    
    @pytest.mark.asyncio
    async def test_tools_timeout_handling(self):
        """Test that tools handle timeouts gracefully."""
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.TimeoutException("Request timed out")
            
            # Health tool should return structured error for timeouts
            result = await check_health()
            import json
            parsed = json.loads(result)
            assert parsed["overall_status"] == "timeout"
            
            # Other tools should raise exceptions for timeouts
            with pytest.raises(Exception) as exc_info:
                await list_hosts()
            assert "timed out" in str(exc_info.value)


class TestMCPConfiguration:
    """Test suite for MCP configuration."""
    
    def test_config_validation_valid(self):
        """Test configuration validation with valid settings."""
        assert config.validate() is True
    
    def test_config_base_url(self):
        """Test configuration base URL construction."""
        assert config.base_url == f"http://{config.fastapi_host}:{config.fastapi_port}"
    
    @patch.dict('os.environ', {'FLEETPULSE_API_HOST': 'api.example.com'})
    def test_config_from_env(self):
        """Test configuration loading from environment variables."""
        from fleetpulse_mcp.config.settings import MCPConfig
        test_config = MCPConfig()
        assert test_config.fastapi_host == 'api.example.com'