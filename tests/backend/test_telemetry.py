"""
Tests for OpenTelemetry telemetry functionality.

Tests the telemetry configuration, initialization, and basic functionality
without requiring actual telemetry dependencies to be installed.
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from backend.main import app, get_engine, get_session


@pytest.fixture(scope="function")
def temp_db_file():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    yield db_path
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def override_engine(temp_db_file):
    engine = create_engine(f"sqlite:///{temp_db_file}", connect_args={"check_same_thread": False})
    # Create tables for tests
    from backend.main import SQLModel
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def override_get_session(override_engine):
    def _get_session():
        with Session(override_engine) as session:
            yield session
    return _get_session


@pytest.fixture(scope="function")
def client_with_db_override(override_engine, override_get_session):
    # Override dependencies
    app.dependency_overrides[get_engine] = lambda: override_engine
    app.dependency_overrides[get_session] = override_get_session
    
    client = TestClient(app)
    yield client
    
    # Clean up
    app.dependency_overrides.clear()


def test_telemetry_graceful_fallback(client_with_db_override):
    """Test that the application works when telemetry dependencies are not available."""
    
    # Test that the application starts and responds
    response = client_with_db_override.get("/health")
    assert response.status_code == 200
    
    # Check that telemetry status is reported correctly
    health_data = response.json()
    assert "telemetry" in health_data
    
    # Should work regardless of whether telemetry is enabled or not
    assert isinstance(health_data["telemetry"]["enabled"], bool)


def test_health_endpoint_with_telemetry(client_with_db_override):
    """Test that health endpoint includes telemetry information."""
    
    response = client_with_db_override.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify telemetry section exists
    assert "telemetry" in data
    telemetry_info = data["telemetry"]
    
    # Check required telemetry fields
    assert "enabled" in telemetry_info
    assert isinstance(telemetry_info["enabled"], bool)
    
    if telemetry_info["enabled"]:
        # If telemetry is enabled, should have more details
        expected_fields = ["service_name", "service_version", "environment", "exporter_type"]
        for field in expected_fields:
            assert field in telemetry_info
    else:
        # If disabled, should have explanatory note
        assert "note" in telemetry_info


def test_telemetry_environment_configuration():
    """Test that telemetry configuration respects environment variables."""
    
    # Test with telemetry disabled
    with patch.dict(os.environ, {
        'OTEL_ENABLE_TELEMETRY': 'false',
        'OTEL_SERVICE_NAME': 'test-service',
        'OTEL_ENVIRONMENT': 'test'
    }, clear=False):
        
        # Import telemetry after setting env vars
        try:
            from backend.telemetry import get_telemetry_config
            config = get_telemetry_config()
            
            assert config["enable_telemetry"] is False
            assert config["service_name"] == "test-service"
            assert config["environment"] == "test"
        except ImportError:
            # Telemetry module not available, which is fine
            pass


def test_api_endpoints_still_work_with_telemetry(client_with_db_override):
    """Test that API endpoints work correctly with telemetry integration."""
    
    # Test hosts endpoint
    response = client_with_db_override.get("/hosts")
    assert response.status_code == 200
    assert "hosts" in response.json()
    
    # Test health endpoint
    response = client_with_db_override.get("/health")
    assert response.status_code == 200


def test_report_endpoint_with_telemetry(client_with_db_override):
    """Test that the report endpoint works with telemetry integration."""
    
    # Test package update reporting
    test_data = {
        "hostname": "test-host",
        "os": "ubuntu-22.04",
        "update_date": "2024-01-01",
        "updated_packages": [
            {
                "name": "test-package",
                "old_version": "1.0.0",
                "new_version": "1.1.0"
            }
        ]
    }
    
    response = client_with_db_override.post("/report", json=test_data)
    assert response.status_code == 201
    
    result = response.json()
    assert result["status"] == "success"
    assert result["hostname"] == "test-host"


@patch('backend.main.TELEMETRY_ENABLED', True)
def test_telemetry_stub_functions():
    """Test that telemetry stub functions work when telemetry is not available."""
    from backend.main import (
        create_custom_span,
        record_request_metrics,
        record_package_update_metrics,
        record_host_metrics,
        add_baggage
    )
    
    # These should not raise exceptions even if telemetry is not installed
    span = create_custom_span("test_span", {"test": "value"})
    
    # Test span methods
    span.set_attribute("test_key", "test_value")
    span.__enter__()
    span.__exit__(None, None, None)
    
    # Test metric recording functions
    record_request_metrics("GET", "/test", 200, 100.0)
    record_package_update_metrics("test-host", 5)
    record_host_metrics("test-host", "add")
    add_baggage("test_key", "test_value")


def test_health_endpoint_excluded_from_telemetry_metrics(client_with_db_override):
    """Test that health endpoint is excluded from telemetry request metrics."""
    from unittest.mock import patch, MagicMock
    
    # Mock the record_request_metrics function to track calls
    with patch('backend.main.record_request_metrics') as mock_record_metrics:
        # Call health endpoint
        response = client_with_db_override.get("/health")
        assert response.status_code == 200
        
        # Health endpoint should NOT have triggered request metrics recording
        mock_record_metrics.assert_not_called()
        
        # Verify that other endpoints still trigger metrics recording
        # Call hosts endpoint which should trigger metrics
        response = client_with_db_override.get("/hosts")
        assert response.status_code == 200
        
        # This endpoint should have triggered request metrics recording
        mock_record_metrics.assert_called_once()
        call_args = mock_record_metrics.call_args[1]  # Get keyword arguments
        assert call_args["method"] == "GET"
        assert call_args["endpoint"] == "/hosts"
        assert call_args["status_code"] == 200


def test_fastapi_instrumentation_integration():
    """Test that FastAPI instrumentation is properly applied to the app instance."""
    import logging
    from io import StringIO
    from fastapi import FastAPI
    from backend.telemetry import instrument_fastapi_app
    
    # Create a fresh app instance for testing (not the imported one)
    test_app = FastAPI(title="Test App")
    
    # Capture log output to verify instrumentation message
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.INFO)
    
    # Get the telemetry logger and add our handler
    telemetry_logger = logging.getLogger('telemetry')
    original_level = telemetry_logger.level
    telemetry_logger.setLevel(logging.INFO)
    telemetry_logger.addHandler(handler)
    
    try:
        # Call the instrumentation function on the fresh app
        instrument_fastapi_app(test_app)
        
        # Check that the log message was emitted
        log_output = log_capture.getvalue()
        
        # The function should log successful instrumentation
        # If telemetry is disabled, it should handle gracefully without logging
        assert "FastAPI app instrumentation completed" in log_output or log_output == ""
        
    finally:
        # Clean up
        telemetry_logger.removeHandler(handler)
        telemetry_logger.setLevel(original_level)
        handler.close()


def test_docker_compose_telemetry_configuration():
    """Test that docker-compose.yml includes proper telemetry configuration."""
    import yaml
    
    compose_path = os.path.join(os.path.dirname(__file__), '..', '..', 'docker-compose.yml')
    
    with open(compose_path, 'r') as f:
        compose_config = yaml.safe_load(f)
    
    # Check that Jaeger service exists
    assert 'jaeger' in compose_config['services']
    jaeger_service = compose_config['services']['jaeger']
    
    # Verify Jaeger configuration
    assert jaeger_service['image'] == 'jaegertracing/all-in-one:latest'
    assert '16686:16686' in jaeger_service['ports']  # Jaeger UI
    assert '14268:14268' in jaeger_service['ports']  # HTTP collector
    
    # Check that OpenTelemetry Collector service exists
    assert 'otel-collector' in compose_config['services']
    otel_service = compose_config['services']['otel-collector']
    
    # Verify OTEL Collector configuration
    assert 'otel/opentelemetry-collector-contrib' in otel_service['image']
    assert '4317:4317' in otel_service['ports']  # OTLP gRPC
    assert '4318:4318' in otel_service['ports']  # OTLP HTTP
    assert 'jaeger' in otel_service['depends_on']
    
    # Check backend telemetry environment variables
    backend_service = compose_config['services']['backend']
    backend_env = backend_service['environment']
    
    telemetry_env_vars = [
        'OTEL_SERVICE_NAME=fleetpulse-backend',
        'OTEL_SERVICE_VERSION=1.0.0',
        'OTEL_ENABLE_TELEMETRY=${OTEL_ENABLE_TELEMETRY:-true}',
        'OTEL_EXPORTER_TYPE=${OTEL_EXPORTER_TYPE:-jaeger}',
    ]
    
    for env_var in telemetry_env_vars:
        assert env_var in backend_env
    
    # Check that OTLP endpoint is configured
    otlp_endpoint_found = any('OTEL_EXPORTER_OTLP_ENDPOINT' in env for env in backend_env)
    assert otlp_endpoint_found, "OTLP endpoint environment variable not found"
    
    # Check that backend service depends on both Jaeger and OTEL Collector
    assert 'jaeger' in backend_service['depends_on']
    assert 'otel-collector' in backend_service['depends_on']
    
    # Frontend service should exist but have no telemetry environment variables
    frontend_service = compose_config['services']['frontend']
    # Frontend should not have telemetry environment variables since telemetry is backend-only
    assert 'environment' not in frontend_service or frontend_service.get('environment') is None


def test_env_example_telemetry_configuration():
    """Test that .env.example includes telemetry configuration."""
    env_example_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env.example')
    
    with open(env_example_path, 'r') as f:
        env_content = f.read()
    
    # Check for telemetry configuration sections
    telemetry_vars = [
        'OTEL_ENABLE_TELEMETRY',
        'OTEL_ENVIRONMENT',
        'OTEL_EXPORTER_TYPE',
        'OTEL_TRACE_SAMPLE_RATE',
    ]
    
    for var in telemetry_vars:
        assert var in env_content
    
    # Check for telemetry documentation
    assert 'OpenTelemetry Configuration' in env_content
    assert 'jaeger' in env_content.lower()
    assert 'otlp' in env_content.lower()


def test_backend_requirements_telemetry_dependencies():
    """Test that backend requirements.txt includes OpenTelemetry dependencies."""
    requirements_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'backend', 'requirements.txt'
    )
    
    with open(requirements_path, 'r') as f:
        requirements_content = f.read()
    
    # Check for required OpenTelemetry packages
    required_packages = [
        'opentelemetry-api',
        'opentelemetry-sdk',
        'opentelemetry-instrumentation-fastapi',
        'opentelemetry-instrumentation-sqlalchemy',
        'opentelemetry-exporter-jaeger',
        'opentelemetry-exporter-otlp',
    ]
    
    for package in required_packages:
        assert package in requirements_content, f"Missing OpenTelemetry package: {package}"


def test_otel_collector_configuration():
    """Test that otel-collector-config.yaml has proper configuration."""
    import yaml
    
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'otel-collector-config.yaml')
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Check that required sections exist
    assert 'receivers' in config
    assert 'processors' in config
    assert 'exporters' in config
    assert 'service' in config
    
    # Check OTLP receiver configuration
    assert 'otlp' in config['receivers']
    otlp_receiver = config['receivers']['otlp']
    assert 'protocols' in otlp_receiver
    assert 'grpc' in otlp_receiver['protocols']
    assert 'http' in otlp_receiver['protocols']
    
    # Check that Jaeger exporter is configured
    assert 'jaeger' in config['exporters']
    jaeger_exporter = config['exporters']['jaeger']
    assert 'jaeger:14250' in jaeger_exporter['endpoint']
    
    # Check service pipelines
    assert 'pipelines' in config['service']
    pipelines = config['service']['pipelines']
    assert 'traces' in pipelines
    assert 'metrics' in pipelines
    
    # Verify trace pipeline
    trace_pipeline = pipelines['traces']
    assert 'otlp' in trace_pipeline['receivers']
    assert 'jaeger' in trace_pipeline['exporters']


if __name__ == "__main__":
    pytest.main([__file__])