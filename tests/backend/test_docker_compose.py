"""
Test Docker Compose configuration for port exposure.
"""
import yaml
import os


def test_docker_compose_exposes_backend_port():
    """Test that docker-compose.yml exposes port 8000 for backend API access."""
    docker_compose_path = "/home/runner/work/fleetpulse/fleetpulse/docker-compose.yml"
    
    with open(docker_compose_path, 'r') as f:
        compose_config = yaml.safe_load(f)
    
    # Get the fleetpulse service configuration
    fleetpulse_service = compose_config['services']['fleetpulse']
    ports = fleetpulse_service.get('ports', [])
    
    # Check that port 8000 is exposed for backend API
    backend_port_exposed = any('8000:8000' in str(port) for port in ports)
    
    assert backend_port_exposed, (
        "Port 8000 should be exposed for backend API access. "
        f"Current ports: {ports}. "
        "Ansible expects to connect to the backend API on port 8000."
    )


def test_docker_compose_exposes_frontend_port():
    """Test that docker-compose.yml exposes port 8080 for frontend UI access."""
    docker_compose_path = "/home/runner/work/fleetpulse/fleetpulse/docker-compose.yml"
    
    with open(docker_compose_path, 'r') as f:
        compose_config = yaml.safe_load(f)
    
    # Get the fleetpulse service configuration
    fleetpulse_service = compose_config['services']['fleetpulse']
    ports = fleetpulse_service.get('ports', [])
    
    # Check that port 8080 is exposed for frontend UI
    frontend_port_exposed = any('8080:8080' in str(port) for port in ports)
    
    assert frontend_port_exposed, (
        "Port 8080 should be exposed for frontend UI access. "
        f"Current ports: {ports}. "
        "Users expect to access the web UI on port 8080."
    )


def test_docker_compose_service_configuration():
    """Test that docker-compose.yml has proper service configuration."""
    docker_compose_path = "/home/runner/work/fleetpulse/fleetpulse/docker-compose.yml"
    
    with open(docker_compose_path, 'r') as f:
        compose_config = yaml.safe_load(f)
    
    # Verify basic service structure
    assert 'services' in compose_config
    assert 'fleetpulse' in compose_config['services']
    
    fleetpulse_service = compose_config['services']['fleetpulse']
    
    # Verify essential configuration
    assert 'build' in fleetpulse_service
    assert 'ports' in fleetpulse_service
    assert 'volumes' in fleetpulse_service
    assert 'environment' in fleetpulse_service
