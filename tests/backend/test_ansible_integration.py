"""
Test to verify Docker Compose configuration matches expected API access patterns.
"""
import yaml


def test_ansible_backend_api_access():
    """Test that Ansible can access backend API on expected port 8000."""
    docker_compose_path = "/home/runner/work/fleetpulse/fleetpulse/docker-compose.yml"
    
    with open(docker_compose_path, 'r') as f:
        compose_config = yaml.safe_load(f)
    
    # Get the fleetpulse service configuration
    fleetpulse_service = compose_config['services']['fleetpulse']
    ports = fleetpulse_service.get('ports', [])
    
    # Check that port 8000 is exposed for backend API access
    # This matches the Ansible playbook expectation: "http://YOUR-BACKEND-IP:8000/report"
    backend_port_exposed = any('8000:8000' in str(port) for port in ports)
    
    assert backend_port_exposed, (
        "Ansible expects backend API to be accessible on port 8000. "
        "The docker-compose.yml should expose '8000:8000' to allow direct API access."
    )


def test_ui_access_still_available():
    """Test that frontend UI access on port 8080 is still available."""
    docker_compose_path = "/home/runner/work/fleetpulse/fleetpulse/docker-compose.yml"
    
    with open(docker_compose_path, 'r') as f:
        compose_config = yaml.safe_load(f)
    
    # Get the fleetpulse service configuration
    fleetpulse_service = compose_config['services']['fleetpulse']
    ports = fleetpulse_service.get('ports', [])
    
    # Check that port 8080 is still exposed for frontend UI
    # This maintains backward compatibility for users accessing the UI
    ui_port_exposed = any('8080:8000' in str(port) for port in ports)
    
    assert ui_port_exposed, (
        "Frontend UI should still be accessible on port 8080 for backward compatibility. "
        "Users expect to access the web UI at http://YOUR-HOST-IP:8080"
    )


def test_both_access_methods_supported():
    """Test that both API and UI access methods are supported simultaneously."""
    docker_compose_path = "/home/runner/work/fleetpulse/fleetpulse/docker-compose.yml"
    
    with open(docker_compose_path, 'r') as f:
        compose_config = yaml.safe_load(f)
    
    # Get the fleetpulse service configuration
    fleetpulse_service = compose_config['services']['fleetpulse']
    ports = fleetpulse_service.get('ports', [])
    
    # Convert to strings for easier checking
    port_strings = [str(port) for port in ports]
    
    # Check that both access methods are supported
    backend_api_port = any('8000:8000' in port for port in port_strings)
    ui_port = any('8080:8000' in port for port in port_strings)
    
    assert backend_api_port, "Backend API access on port 8000 must be available for Ansible"
    assert ui_port, "Frontend UI access on port 8080 must be available for users"
    
    # Verify we have exactly 2 port mappings (no duplicates or conflicts)
    assert len(ports) == 2, f"Expected exactly 2 port mappings, got {len(ports)}: {ports}"


def test_sample_docker_compose_consistency():
    """Test that docker-compose.sample.yml has the same port configuration."""
    main_compose_path = "/home/runner/work/fleetpulse/fleetpulse/docker-compose.yml"
    sample_compose_path = "/home/runner/work/fleetpulse/fleetpulse/docker-compose.sample.yml"
    
    with open(main_compose_path, 'r') as f:
        main_config = yaml.safe_load(f)
    
    with open(sample_compose_path, 'r') as f:
        sample_config = yaml.safe_load(f)
    
    # Get port configurations
    main_ports = main_config['services']['fleetpulse']['ports']
    sample_ports = sample_config['services']['fleetpulse']['ports']
    
    # Both should expose port 8000 for backend API
    main_has_backend = any('8000:8000' in str(port) for port in main_ports)
    sample_has_backend = any('8000:8000' in str(port) for port in sample_ports)
    
    assert main_has_backend, "Main docker-compose.yml should expose backend API on port 8000"
    assert sample_has_backend, "Sample docker-compose.yml should expose backend API on port 8000"
    
    # Both should expose port 8080 for UI
    main_has_ui = any('8080:8000' in str(port) for port in main_ports)
    sample_has_ui = any('8080:8000' in str(port) for port in sample_ports)
    
    assert main_has_ui, "Main docker-compose.yml should expose UI on port 8080"
    assert sample_has_ui, "Sample docker-compose.yml should expose UI on port 8080"