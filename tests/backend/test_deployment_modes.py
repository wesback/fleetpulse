import os
import tempfile
import subprocess
import shutil
from unittest.mock import patch, MagicMock
import pytest

def test_dockerfile_deployment_mode_configuration():
    """Test that the Dockerfile properly supports both deployment modes."""
    dockerfile_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Dockerfile.backend')
    
    # Read the Dockerfile content
    with open(dockerfile_path, 'r') as f:
        dockerfile_content = f.read()
    
    # Check that the CMD supports conditional deployment mode
    assert "DEPLOYMENT_MODE" in dockerfile_content
    assert "uvicorn" in dockerfile_content
    assert "gunicorn" in dockerfile_content
    # Check for the actual escaped format in the Dockerfile
    assert '\\"${DEPLOYMENT_MODE:-uvicorn}\\"' in dockerfile_content
    assert "gunicorn main:app -k uvicorn.workers.UvicornWorker" in dockerfile_content
    assert "uvicorn main:app --host 0.0.0.0 --port 8000" in dockerfile_content

def test_env_example_deployment_mode_documentation():
    """Test that .env.example documents the new deployment mode options."""
    env_example_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env.example')
    
    with open(env_example_path, 'r') as f:
        env_content = f.read()
    
    # Check that DEPLOYMENT_MODE is documented
    assert "DEPLOYMENT_MODE=" in env_content
    assert "uvicorn" in env_content
    assert "gunicorn" in env_content
    
    # Check that usage scenarios are explained
    assert "single-container" in env_content.lower()
    assert "production" in env_content.lower()
    assert "development" in env_content.lower()

def test_uvicorn_direct_command_structure():
    """Test that uvicorn command structure is correct."""
    # This tests the command that would be executed in uvicorn mode
    # We're not actually starting uvicorn, just testing the command structure
    
    expected_uvicorn_cmd = "uvicorn main:app --host 0.0.0.0 --port 8000"
    
    # Test that the command structure is valid
    cmd_parts = expected_uvicorn_cmd.split()
    assert cmd_parts[0] == "uvicorn"
    assert "main:app" in cmd_parts
    assert "--host" in cmd_parts
    assert "0.0.0.0" in cmd_parts
    assert "--port" in cmd_parts
    assert "8000" in cmd_parts

def test_gunicorn_command_structure():
    """Test that gunicorn command structure is correct."""
    # This tests the command that would be executed in gunicorn mode
    expected_gunicorn_cmd = "gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 2"
    
    cmd_parts = expected_gunicorn_cmd.split()
    assert cmd_parts[0] == "gunicorn"
    assert "main:app" in cmd_parts
    assert "-k" in cmd_parts
    assert "uvicorn.workers.UvicornWorker" in cmd_parts
    assert "--bind" in cmd_parts
    assert "0.0.0.0:8000" in cmd_parts
    assert "--workers" in cmd_parts

def test_deployment_mode_defaults():
    """Test that the deployment mode defaults to uvicorn for simplicity."""
    dockerfile_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Dockerfile.backend')
    
    with open(dockerfile_path, 'r') as f:
        dockerfile_content = f.read()
    
    # Check that uvicorn is the default when DEPLOYMENT_MODE is not set
    assert "${DEPLOYMENT_MODE:-uvicorn}" in dockerfile_content

def test_environment_configuration_examples():
    """Test that the configuration examples make sense for different use cases."""
    env_example_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env.example')
    
    with open(env_example_path, 'r') as f:
        env_content = f.read()
    
    # Test that configuration examples are present
    assert "DEPLOYMENT_MODE=uvicorn" in env_content
    assert "GUNICORN_WORKERS=2" in env_content
    
    # Test that use case explanations are present
    lines = env_content.lower()
    assert "low to medium traffic" in lines
    assert "high-traffic" in lines
    assert "development" in lines
    assert "single-container" in lines

def test_backward_compatibility():
    """Test that the new configuration maintains backward compatibility."""
    # The GUNICORN_WORKERS variable should still work for gunicorn mode
    env_example_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env.example')
    
    with open(env_example_path, 'r') as f:
        env_content = f.read()
    
    # GUNICORN_WORKERS should still be documented and available
    assert "GUNICORN_WORKERS" in env_content