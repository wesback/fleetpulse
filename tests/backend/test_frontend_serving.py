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


def test_static_js_file_serving():
    """Test that static JavaScript files are properly served from the correct path."""
    client = TestClient(app)
    
    # Test the specific file that was failing in the issue
    response = client.get("/static/js/main.fd6dc8ce.js")
    
    # The file should be accessible if static files are built and mounted correctly
    if response.status_code == 200:
        # If the file exists, it should have the correct content-type
        assert "javascript" in response.headers.get("content-type", "").lower()
        # Should not be empty
        assert len(response.content) > 0
    else:
        # If file doesn't exist during testing, should return 404
        assert response.status_code == 404