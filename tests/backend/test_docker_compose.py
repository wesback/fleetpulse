"""
Test Docker Compose configuration for port exposure.
"""
import yaml
import os


def test_docker_compose_exposes_backend_port():
    """Test that docker-compose.yml exposes port 8000 for backend API access."""
    docker_compose_path = os.path.join(os.path.dirname(__file__), '..', '..', 'docker-compose.yml')
    
    with open(docker_compose_path, 'r') as f:
        compose_config = yaml.safe_load(f)
    
    # Get the backend service configuration
    backend_service = compose_config['services']['backend']
    ports = backend_service.get('ports', [])
    
    # Check that port 8000 is exposed for backend API
    backend_port_exposed = any('8000:8000' in str(port) for port in ports)
    
    assert backend_port_exposed, (
        "Port 8000 should be exposed for backend API access. "
        f"Current ports: {ports}. "
        "Ansible expects to connect to the backend API on port 8000."
    )


def test_docker_compose_exposes_frontend_port():
    """Test that docker-compose.yml exposes port 8080 for frontend UI access."""
    docker_compose_path = os.path.join(os.path.dirname(__file__), '..', '..', 'docker-compose.yml')
    
    with open(docker_compose_path, 'r') as f:
        compose_config = yaml.safe_load(f)
    
    # Get the frontend service configuration
    frontend_service = compose_config['services']['frontend']
    ports = frontend_service.get('ports', [])
    
    # Check that port 8080 is exposed for frontend UI
    frontend_port_exposed = any('8080:80' in str(port) for port in ports)
    
    assert frontend_port_exposed, (
        "Port 8080 should be exposed for frontend UI access. "
        f"Current ports: {ports}. "
        "Users expect to access the web UI on port 8080."
    )


def test_docker_compose_service_configuration():
    """Test that docker-compose.yml has proper service configuration."""
    docker_compose_path = os.path.join(os.path.dirname(__file__), '..', '..', 'docker-compose.yml')
    
    with open(docker_compose_path, 'r') as f:
        compose_config = yaml.safe_load(f)
    
    # Verify basic service structure
    assert 'services' in compose_config
    assert 'backend' in compose_config['services']
    assert 'frontend' in compose_config['services']
    
    # Test backend service configuration
    backend_service = compose_config['services']['backend']
    assert 'build' in backend_service
    assert 'ports' in backend_service
    assert 'volumes' in backend_service
    assert 'environment' in backend_service
    assert 'container_name' in backend_service
    assert backend_service['container_name'] == 'fleetpulse-backend'
    
    # Test frontend service configuration
    frontend_service = compose_config['services']['frontend']
    assert 'build' in frontend_service
    assert 'ports' in frontend_service
    assert 'depends_on' in frontend_service
    assert 'container_name' in frontend_service
    assert frontend_service['container_name'] == 'fleetpulse-frontend'
    assert 'backend' in frontend_service['depends_on']
    
    # Verify network configuration
    assert 'networks' in compose_config
    assert 'fleetpulse' in compose_config['networks']


def test_docker_compose_dockerfile_references():
    """Test that docker-compose.yml references valid Dockerfile paths."""
    docker_compose_path = os.path.join(os.path.dirname(__file__), '..', '..', 'docker-compose.yml')
    project_root = os.path.join(os.path.dirname(__file__), '..', '..')
    
    with open(docker_compose_path, 'r') as f:
        compose_config = yaml.safe_load(f)
    
    # Test backend dockerfile reference
    backend_service = compose_config['services']['backend']
    backend_dockerfile = backend_service['build']['dockerfile']
    backend_dockerfile_path = os.path.join(project_root, backend_dockerfile)
    
    assert os.path.exists(backend_dockerfile_path), (
        f"Backend Dockerfile not found at {backend_dockerfile_path}. "
        f"Referenced in docker-compose.yml as: {backend_dockerfile}"
    )
    
    # Test frontend dockerfile reference
    frontend_service = compose_config['services']['frontend']
    frontend_dockerfile = frontend_service['build']['dockerfile']
    frontend_dockerfile_path = os.path.join(project_root, frontend_dockerfile)
    
    assert os.path.exists(frontend_dockerfile_path), (
        f"Frontend Dockerfile not found at {frontend_dockerfile_path}. "
        f"Referenced in docker-compose.yml as: {frontend_dockerfile}"
    )


def test_docker_compose_environment_variables():
    """Test that docker-compose.yml has proper environment variable configuration."""
    docker_compose_path = os.path.join(os.path.dirname(__file__), '..', '..', 'docker-compose.yml')
    
    with open(docker_compose_path, 'r') as f:
        compose_config = yaml.safe_load(f)
    
    # Test backend environment variables
    backend_service = compose_config['services']['backend']
    backend_env = backend_service.get('environment', [])
    
    # Convert environment list to dict for easier testing
    env_dict = {}
    for env_var in backend_env:
        if '=' in env_var:
            key, value = env_var.split('=', 1)
            env_dict[key] = value
        else:
            # Environment variable without value (will use system environment)
            env_dict[env_var] = None
    
    # Check for required environment variables
    assert 'FLEETPULSE_DATA_DIR' in env_dict, "FLEETPULSE_DATA_DIR should be set in backend environment"
    assert 'DEPLOYMENT_MODE' in env_dict, "DEPLOYMENT_MODE should be set in backend environment"
    assert 'GUNICORN_WORKERS' in env_dict, "GUNICORN_WORKERS should be set in backend environment"


def test_docker_compose_volume_configuration():
    """Test that docker-compose.yml has proper volume configuration."""
    docker_compose_path = os.path.join(os.path.dirname(__file__), '..', '..', 'docker-compose.yml')
    
    with open(docker_compose_path, 'r') as f:
        compose_config = yaml.safe_load(f)
    
    # Test backend volume configuration
    backend_service = compose_config['services']['backend']
    backend_volumes = backend_service.get('volumes', [])
    
    # Check that data volume is mounted
    data_volume_mounted = any('/data' in str(volume) for volume in backend_volumes)
    assert data_volume_mounted, (
        "Data volume should be mounted at /data in backend service. "
        f"Current volumes: {backend_volumes}"
    )
