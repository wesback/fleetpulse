"""
Test to verify Docker Compose configuration matches expected API access patterns.
"""
import yaml
import os


def test_ansible_backend_api_access():
    """Test that Ansible can access backend API on expected port 8000."""
    docker_compose_path = os.path.join(os.path.dirname(__file__), '..', '..', 'docker-compose.yml')
    
    with open(docker_compose_path, 'r') as f:
        compose_config = yaml.safe_load(f)
    
    # Get the backend service configuration
    backend_service = compose_config['services']['backend']
    ports = backend_service.get('ports', [])
    
    # Check that port 8000 is exposed for backend API access
    # This matches the Ansible playbook expectation: "http://YOUR-BACKEND-IP:8000/report"
    backend_port_exposed = any('8000:8000' in str(port) for port in ports)
    
    assert backend_port_exposed, (
        "Ansible expects backend API to be accessible on port 8000. "
        "The docker-compose.yml should expose '8000:8000' to allow direct API access."
    )


def test_ui_access_still_available():
    """Test that frontend UI access on port 8080 is still available."""
    docker_compose_path = os.path.join(os.path.dirname(__file__), '..', '..', 'docker-compose.yml')
    
    with open(docker_compose_path, 'r') as f:
        compose_config = yaml.safe_load(f)
    
    # Get the frontend service configuration
    frontend_service = compose_config['services']['frontend']
    ports = frontend_service.get('ports', [])
    
    # Check that port 8080 is still exposed for frontend UI (mapping to container port 80)
    # This maintains backward compatibility for users accessing the UI
    ui_port_exposed = any('8080:80' in str(port) for port in ports)
    
    assert ui_port_exposed, (
        "Frontend UI should still be accessible on port 8080 for backward compatibility. "
        "Users expect to access the web UI at http://YOUR-HOST-IP:8080"
    )


def test_both_access_methods_supported():
    """Test that both API and UI access methods are supported simultaneously."""
    docker_compose_path = os.path.join(os.path.dirname(__file__), '..', '..', 'docker-compose.yml')
    
    with open(docker_compose_path, 'r') as f:
        compose_config = yaml.safe_load(f)
    
    # Get the backend and frontend service configurations
    backend_service = compose_config['services']['backend']
    frontend_service = compose_config['services']['frontend']
    backend_ports = backend_service.get('ports', [])
    frontend_ports = frontend_service.get('ports', [])
    
    # Convert to strings for easier checking
    backend_port_strings = [str(port) for port in backend_ports]
    frontend_port_strings = [str(port) for port in frontend_ports]
    
    # Check that both access methods are supported
    backend_api_port = any('8000:8000' in port for port in backend_port_strings)
    ui_port = any('8080:80' in port for port in frontend_port_strings)
    
    assert backend_api_port, "Backend API access on port 8000 must be available for Ansible"
    assert ui_port, "Frontend UI access on port 8080 must be available for users"


def test_sample_docker_compose_consistency():
    """Test that docker-compose.sample.yml has the same port configuration."""
    main_compose_path = os.path.join(os.path.dirname(__file__), '..', '..', 'docker-compose.yml')
    sample_compose_path = os.path.join(os.path.dirname(__file__), '..', '..', 'docker-compose.sample.yml')
    
    with open(main_compose_path, 'r') as f:
        main_config = yaml.safe_load(f)
    
    with open(sample_compose_path, 'r') as f:
        sample_config = yaml.safe_load(f)
    
    # Get port configurations for backend services
    main_backend_ports = main_config['services']['backend']['ports']
    sample_backend_ports = sample_config['services']['backend']['ports']
    
    # Get port configurations for frontend services
    main_frontend_ports = main_config['services']['frontend']['ports']
    sample_frontend_ports = sample_config['services']['frontend']['ports']
    
    # Both should expose port 8000 for backend API
    main_has_backend = any('8000:8000' in str(port) for port in main_backend_ports)
    sample_has_backend = any('8000:8000' in str(port) for port in sample_backend_ports)
    
    assert main_has_backend, "Main docker-compose.yml should expose backend API on port 8000"
    assert sample_has_backend, "Sample docker-compose.yml should expose backend API on port 8000"
    
    # Both should expose port 8080 for UI (mapping to container port 80)
    main_has_ui = any('8080:80' in str(port) for port in main_frontend_ports)
    sample_has_ui = any('8080:80' in str(port) for port in sample_frontend_ports)
    
    assert main_has_ui, "Main docker-compose.yml should expose UI on port 8080"
    assert sample_has_ui, "Sample docker-compose.yml should expose UI on port 8080"
