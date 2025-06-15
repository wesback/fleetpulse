"""
Tests for FleetPulse MCP Server
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

# Import MCP server components
from mcp.main import app
from mcp.config import get_config, validate_config
from mcp.tools import get_mcp_tools
from mcp.models import Host, HealthStatus


@pytest.fixture
def client():
    """Create a test client for the MCP server."""
    return TestClient(app)


@pytest.fixture
def mock_backend_client():
    """Mock backend client for testing."""
    mock_client = AsyncMock()
    
    # Mock health check response
    mock_client.health_check.return_value = HealthStatus(
        status="healthy",
        database="connected",
        telemetry={"enabled": False}
    )
    
    # Mock hosts response
    mock_client.list_hosts.return_value = ["test-host-1", "test-host-2"]
    
    # Mock host info response
    from datetime import date
    from mcp.models import BackendHostInfo
    mock_client.get_host_info.return_value = [
        BackendHostInfo(hostname="test-host-1", os="ubuntu-22.04", last_update=date.today()),
        BackendHostInfo(hostname="test-host-2", os="centos-8", last_update=date.today())
    ]
    
    # Mock get_all_updates response
    mock_client.get_all_updates.return_value = [
        {
            "id": 1,
            "hostname": "test-host-1",
            "os": "ubuntu-22.04",
            "update_date": "2024-01-01",
            "name": "nginx",
            "old_version": "1.20.0",
            "new_version": "1.21.0"
        },
        {
            "id": 2,
            "hostname": "test-host-1", 
            "os": "ubuntu-22.04",
            "update_date": "2024-01-01",
            "name": "openssl",
            "old_version": "1.1.1f",
            "new_version": "1.1.1g"
        }
    ]
    
    # Mock get_host_history response
    from mcp.models import BackendPaginatedResponse
    mock_client.get_host_history.return_value = BackendPaginatedResponse(
        items=[
            {
                "id": 1,
                "hostname": "test-host-1",
                "os": "ubuntu-22.04", 
                "update_date": "2024-01-01",
                "name": "nginx",
                "old_version": "1.20.0",
                "new_version": "1.21.0"
            }
        ],
        total=1,
        limit=50,
        offset=0
    )
    
    mock_client.validate_connection.return_value = True
    
    return mock_client


def test_config_validation():
    """Test configuration validation."""
    config = get_config()
    assert config.fleetpulse_backend_url.startswith('http')
    assert 1 <= config.mcp_port <= 65535
    assert config.request_timeout > 0
    assert config.max_retries >= 0
    
    # Test validation function
    validate_config()  # Should not raise


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["service"] == "FleetPulse MCP Server"
    assert "endpoints" in data
    assert "health" in data["endpoints"]


def test_tools_endpoint(client):
    """Test the tools listing endpoint."""
    response = client.get("/tools")
    assert response.status_code == 200
    
    data = response.json()
    assert "tools" in data
    assert len(data["tools"]) > 0
    
    # Check that each tool has required fields
    for tool in data["tools"]:
        assert "name" in tool
        assert "description" in tool
        assert "endpoint" in tool


@patch('mcp.client.get_backend_client')
def test_health_endpoint(mock_get_client, client, mock_backend_client):
    """Test the health check endpoint."""
    mock_get_client.return_value = mock_backend_client
    
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "mcp_server" in data


@patch('mcp.client.get_backend_client')
def test_hosts_endpoint(mock_get_client, client, mock_backend_client):
    """Test the hosts listing endpoint.""" 
    mock_get_client.return_value = mock_backend_client
    
    response = client.get("/hosts")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


@patch('mcp.client.get_backend_client')
def test_host_details_endpoint(mock_get_client, client, mock_backend_client):
    """Test the host details endpoint."""
    mock_get_client.return_value = mock_backend_client
    
    response = client.get("/hosts/test-host-1")
    assert response.status_code == 200
    
    data = response.json()
    assert data["hostname"] == "test-host-1"
    assert "os" in data
    assert "last_update" in data


@patch('mcp.client.get_backend_client')
def test_reports_endpoint(mock_get_client, client, mock_backend_client):
    """Test the reports endpoint."""
    mock_get_client.return_value = mock_backend_client
    
    response = client.get("/reports")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


@patch('mcp.client.get_backend_client')
def test_reports_with_hostname_filter(mock_get_client, client, mock_backend_client):
    """Test the reports endpoint with hostname filter."""
    mock_get_client.return_value = mock_backend_client
    
    response = client.get("/reports?hostname=test-host-1")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


@patch('mcp.client.get_backend_client')
def test_packages_endpoint(mock_get_client, client, mock_backend_client):
    """Test the packages endpoint."""
    mock_get_client.return_value = mock_backend_client
    
    response = client.get("/packages")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


@patch('mcp.client.get_backend_client')
def test_package_details_endpoint(mock_get_client, client, mock_backend_client):
    """Test the package details endpoint."""
    mock_get_client.return_value = mock_backend_client
    
    response = client.get("/packages/nginx")
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "nginx"
    assert "hosts" in data


@patch('mcp.client.get_backend_client')
def test_statistics_endpoint(mock_get_client, client, mock_backend_client):
    """Test the fleet statistics endpoint."""
    mock_get_client.return_value = mock_backend_client
    
    response = client.get("/stats")
    assert response.status_code == 200
    
    data = response.json()
    assert "total_hosts" in data
    assert "total_reports" in data
    assert "total_packages" in data


@patch('mcp.client.get_backend_client')
def test_search_endpoint(mock_get_client, client, mock_backend_client):
    """Test the search endpoint."""
    mock_get_client.return_value = mock_backend_client
    
    response = client.get("/search?q=nginx")
    assert response.status_code == 200
    
    data = response.json()
    assert "query" in data
    assert "results" in data
    assert "total_results" in data


def test_search_endpoint_missing_query(client):
    """Test the search endpoint without query parameter."""
    response = client.get("/search")
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_tools_health_check():
    """Test the MCP tools health check functionality."""
    with patch('mcp.client.get_backend_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.health_check.return_value = HealthStatus(
            status="healthy",
            database="connected", 
            telemetry={"enabled": True}
        )
        mock_get_client.return_value = mock_client
        
        tools = get_mcp_tools()
        result = await tools.health_check()
        
        assert result["status"] == "healthy"
        assert result["mcp_server"]["status"] == "healthy"
        assert result["mcp_server"]["backend_connected"] is True


@pytest.mark.asyncio
async def test_tools_health_check_backend_down():
    """Test the MCP tools health check when backend is down."""
    with patch('mcp.client.get_backend_client') as mock_get_client:
        mock_client = AsyncMock()
        from mcp.client import BackendConnectionError
        mock_client.health_check.side_effect = BackendConnectionError("Connection failed")
        mock_get_client.return_value = mock_client
        
        tools = get_mcp_tools()
        result = await tools.health_check()
        
        assert result["status"] == "unhealthy"
        assert result["mcp_server"]["status"] == "degraded"
        assert result["mcp_server"]["backend_connected"] is False


if __name__ == "__main__":
    pytest.main([__file__])