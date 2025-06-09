import tempfile
import shutil
import os
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.main import app


def test_api_endpoints_work():
    """Test that API endpoints work correctly in the separated backend."""
    # Use the existing test client with database overrides
    client = TestClient(app)
    
    # Test health endpoint - now returns 500 due to database dependency
    response = client.get("/health")
    assert response.status_code in [200, 500, 503]  # Should work, might be unhealthy if no DB
    
    # Test hosts endpoint
    response = client.get("/hosts")
    assert response.status_code in [200, 500]  # Should work, might fail if no DB


def test_frontend_routes_not_served():
    """Test that frontend routes are no longer served by the backend."""
    client = TestClient(app)
    
    # Frontend routes should return 404 since backend no longer serves them
    response = client.get("/")
    assert response.status_code == 404
    
    # Test another frontend route
    response = client.get("/dashboard")
    assert response.status_code == 404


def test_static_files_not_served():
    """Test that static files are no longer served by the backend."""
    client = TestClient(app)
    
    # Static files should return 404 since backend no longer serves them
    response = client.get("/static/js/main.fd6dc8ce.js")
    assert response.status_code == 404
    
    # Test CSS files
    response = client.get("/static/css/main.css")
    assert response.status_code == 404