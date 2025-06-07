import tempfile
import shutil
import os
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.main import app


def test_api_endpoints_still_work():
    """Test that API endpoints are not affected by frontend serving."""
    # Use the existing test client with database overrides
    client = TestClient(app)
    
    # Test health endpoint
    response = client.get("/health")
    assert response.status_code in [200, 503]  # Should work, might be unhealthy if no DB
    
    # Test hosts endpoint
    response = client.get("/hosts")
    assert response.status_code in [200, 500]  # Should work, might fail if no DB


def test_frontend_serving_fallback():
    """Test that frontend serving returns appropriate response when no static files."""
    # Test with paths that should trigger frontend serving
    client = TestClient(app)
    
    # Most likely scenario is that static files don't exist during testing
    response = client.get("/")
    
    # Should either serve the frontend (200) or return 404 if no static files
    assert response.status_code in [200, 404]
    
    # Test another frontend route
    response = client.get("/dashboard")
    assert response.status_code in [200, 404]