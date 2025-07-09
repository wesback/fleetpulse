"""Test for the modular structure of the FastAPI backend."""
import pytest
from backend.main import app
from backend.models.database import PackageUpdate
from backend.models.schemas import UpdateIn, HostInfo, StatisticsResponse
from backend.db.engine import get_engine
from backend.db.session import get_session
from backend.utils.validation import validate_hostname, validate_package_name
from backend.utils.constants import MAX_HOSTNAME_LENGTH, DATA_DIR


def test_modular_imports():
    """Test that all modular components can be imported correctly."""
    # Test that main app is available
    assert app is not None
    assert app.title == "FleetPulse API"
    
    # Test that database models are available
    assert PackageUpdate is not None
    
    # Test that schemas are available
    assert UpdateIn is not None
    assert HostInfo is not None
    assert StatisticsResponse is not None
    
    # Test that database functions are available
    assert get_engine is not None
    assert get_session is not None
    
    # Test that utilities are available
    assert validate_hostname is not None
    assert validate_package_name is not None
    assert MAX_HOSTNAME_LENGTH == 255
    assert DATA_DIR is not None


def test_validation_functions():
    """Test that validation functions work correctly."""
    # Test hostname validation
    assert validate_hostname("test-host") == True
    assert validate_hostname("test.example.com") == True
    assert validate_hostname("") == False
    assert validate_hostname("host with spaces") == False
    
    # Test package name validation
    assert validate_package_name("test-package") == True
    assert validate_package_name("package.name") == True
    assert validate_package_name("package:version") == True
    assert validate_package_name("") == False


def test_router_endpoints_exist():
    """Test that all expected endpoints are available in the app."""
    routes = [route.path for route in app.routes]
    
    # Check that all expected endpoints exist
    expected_endpoints = ["/report", "/hosts", "/health", "/statistics", "/last-updates"]
    
    for endpoint in expected_endpoints:
        assert endpoint in routes, f"Endpoint {endpoint} not found in routes"


def test_app_structure():
    """Test that the app has the expected middleware and configuration."""
    # Test that middleware is present (CORS middleware gets wrapped in a Middleware class)
    assert len(app.user_middleware) > 0
    
    # Test that the app has the expected title and description
    assert app.title == "FleetPulse API"
    assert "tracking package updates" in app.description.lower()
    assert app.version == "1.0.0"