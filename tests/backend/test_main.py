import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import tempfile
import shutil
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, select
from backend.main import app, get_session, get_engine, SQLModel as AppSQLModel, PackageUpdate
from datetime import date, timedelta

@pytest.fixture(scope="session")
def temp_db_file():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    yield db_path
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="session")
def override_engine(temp_db_file):
    engine = create_engine(f"sqlite:///{temp_db_file}", connect_args={"check_same_thread": False})
    return engine

# Generator function for FastAPI dependency override
@pytest.fixture(scope="session")
def override_get_session(override_engine):
    def _get_session():
        with Session(override_engine) as session:
            yield session
    return _get_session

@pytest.fixture(scope="session", autouse=True)
def set_dependency_overrides(override_engine, override_get_session):
    app.dependency_overrides[get_engine] = lambda: override_engine
    app.dependency_overrides[get_session] = override_get_session
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def client_with_db_override():
    client = TestClient(app)
    yield client

@pytest.fixture(scope="function", autouse=True)
def setup_database_for_each_test(override_engine):
    AppSQLModel.metadata.drop_all(override_engine)
    AppSQLModel.metadata.create_all(override_engine)
    yield
    AppSQLModel.metadata.drop_all(override_engine)

def test_report_update_success(client_with_db_override, override_engine):
    test_date = date.today()
    response = client_with_db_override.post(
        "/report",
        json={
            "hostname": "test-host-1",
            "os": "ubuntu-22.04",
            "update_date": test_date.isoformat(),
            "updated_packages": [
                {"name": "nginx", "old_version": "1.20.0", "new_version": "1.21.0"},
                {"name": "openssl", "old_version": "1.1.1f", "new_version": "1.1.1g"},
            ],
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "success"

    # Assertions against the database should use the override_engine
    with Session(override_engine) as session:
        updates = session.exec(select(PackageUpdate)).all()
        assert len(updates) == 2
        assert updates[0].hostname == "test-host-1"
        assert updates[0].name == "nginx"
        assert updates[1].name == "openssl"
        assert updates[0].update_date == test_date

def test_list_hosts_no_hosts(client_with_db_override):
    response = client_with_db_override.get("/hosts")
    assert response.status_code == 200
    assert response.json() == {"hosts": []}

def test_list_hosts_one_host(client_with_db_override):
    client_with_db_override.post("/report", json={"hostname": "host-a", "os": "centos", "update_date": date.today().isoformat(), "updated_packages": [{"name": "vim", "old_version": "1", "new_version": "2"}]})
    response = client_with_db_override.get("/hosts")
    assert response.status_code == 200
    assert response.json() == {"hosts": ["host-a"]}

def test_list_hosts_multiple_hosts(client_with_db_override):
    client_with_db_override.post("/report", json={"hostname": "host-b", "os": "debian", "update_date": date.today().isoformat(), "updated_packages": [{"name": "git", "old_version": "2", "new_version": "3"}]})
    client_with_db_override.post("/report", json={"hostname": "host-c", "os": "fedora", "update_date": date.today().isoformat(), "updated_packages": [{"name": "curl", "old_version": "7", "new_version": "8"}]})
    client_with_db_override.post("/report", json={"hostname": "host-b", "os": "debian", "update_date": date.today().isoformat(), "updated_packages": [{"name": "nano", "old_version": "1", "new_version": "2"}]}) # Same host again
    response = client_with_db_override.get("/hosts")
    assert response.status_code == 200
    hosts_list = response.json()["hosts"]
    assert len(hosts_list) == 2 # Should be unique
    assert "host-b" in hosts_list
    assert "host-c" in hosts_list

def test_host_history_not_found(client_with_db_override):
    response = client_with_db_override.get("/history/non-existent-host")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data or "detail" in data

def test_host_history_found(client_with_db_override):
    today = date.today()
    client_with_db_override.post("/report", json={"hostname": "history-host", "os": "arch", "update_date": today.isoformat(), "updated_packages": [{"name": "pkg1", "old_version": "1", "new_version": "2"}]})
    client_with_db_override.post("/report", json={"hostname": "history-host", "os": "arch", "update_date": (today - timedelta(days=1)).isoformat(), "updated_packages": [{"name": "pkg2", "old_version": "3", "new_version": "4"}]})
    
    response = client_with_db_override.get("/history/history-host")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 2
    # Check if dates are correctly parsed and present (order might not be guaranteed by default select)
    dates_in_history = {item['update_date'] for item in history}
    assert today.isoformat() in dates_in_history
    assert (today - timedelta(days=1)).isoformat() in dates_in_history
    hostnames_in_history = {item['hostname'] for item in history}
    assert "history-host" in hostnames_in_history

def test_last_updates_no_data(client_with_db_override):
    response = client_with_db_override.get("/last-updates")
    assert response.status_code == 200
    assert response.json() == []

def test_last_updates_with_data(client_with_db_override):
    today = date.today()
    yesterday = today - timedelta(days=1)
    client_with_db_override.post("/report", json={"hostname": "host1", "os": "os1", "update_date": today.isoformat(), "updated_packages": [{"name": "p1", "old_version": "v1", "new_version": "v2"}]})
    client_with_db_override.post("/report", json={"hostname": "host2", "os": "os2", "update_date": yesterday.isoformat(), "updated_packages": [{"name": "p2", "old_version": "v1", "new_version": "v2"}]})
    client_with_db_override.post("/report", json={"hostname": "host1", "os": "os1", "update_date": yesterday.isoformat(), "updated_packages": [{"name": "p3", "old_version": "v1", "new_version": "v2"}]}) # Older update for host1

    response = client_with_db_override.get("/last-updates")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    host1_data = next((item for item in data if item["hostname"] == "host1"), None)
    host2_data = next((item for item in data if item["hostname"] == "host2"), None)

    assert host1_data is not None
    assert host1_data["os"] == "os1"
    assert host1_data["last_update"] == today.isoformat() # Should be the latest

    assert host2_data is not None
    assert host2_data["os"] == "os2"
    assert host2_data["last_update"] == yesterday.isoformat()

def test_host_history_with_date_filters(client_with_db_override):
    """Test date filtering functionality."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)
    
    # Create test data with different dates
    client_with_db_override.post("/report", json={
        "hostname": "filter-host", "os": "ubuntu", "update_date": today.isoformat(),
        "updated_packages": [{"name": "pkg1", "old_version": "1.0", "new_version": "1.1"}]
    })
    client_with_db_override.post("/report", json={
        "hostname": "filter-host", "os": "ubuntu", "update_date": yesterday.isoformat(),
        "updated_packages": [{"name": "pkg2", "old_version": "2.0", "new_version": "2.1"}]
    })
    client_with_db_override.post("/report", json={
        "hostname": "filter-host", "os": "ubuntu", "update_date": two_days_ago.isoformat(),
        "updated_packages": [{"name": "pkg3", "old_version": "3.0", "new_version": "3.1"}]
    })
    
    # Test date_from filter
    response = client_with_db_override.get(f"/history/filter-host?date_from={yesterday.isoformat()}")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 2  # Today and yesterday
    dates = [item['update_date'] for item in history]
    assert today.isoformat() in dates
    assert yesterday.isoformat() in dates
    assert two_days_ago.isoformat() not in dates
    
    # Test date_to filter
    response = client_with_db_override.get(f"/history/filter-host?date_to={yesterday.isoformat()}")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 2  # Yesterday and two days ago
    dates = [item['update_date'] for item in history]
    assert yesterday.isoformat() in dates
    assert two_days_ago.isoformat() in dates
    assert today.isoformat() not in dates
    
    # Test date range filter
    response = client_with_db_override.get(f"/history/filter-host?date_from={yesterday.isoformat()}&date_to={today.isoformat()}")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 2  # Today and yesterday
    dates = [item['update_date'] for item in history]
    assert today.isoformat() in dates
    assert yesterday.isoformat() in dates
    assert two_days_ago.isoformat() not in dates

def test_host_history_with_os_filter(client_with_db_override):
    """Test OS filtering functionality."""
    today = date.today()
    
    # Create test data with different OS
    client_with_db_override.post("/report", json={
        "hostname": "os-filter-host", "os": "ubuntu-20.04", "update_date": today.isoformat(),
        "updated_packages": [{"name": "pkg1", "old_version": "1.0", "new_version": "1.1"}]
    })
    client_with_db_override.post("/report", json={
        "hostname": "os-filter-host", "os": "centos-8", "update_date": today.isoformat(),
        "updated_packages": [{"name": "pkg2", "old_version": "2.0", "new_version": "2.1"}]
    })
    client_with_db_override.post("/report", json={
        "hostname": "os-filter-host", "os": "ubuntu-20.04", "update_date": today.isoformat(),
        "updated_packages": [{"name": "pkg3", "old_version": "3.0", "new_version": "3.1"}]
    })
    
    # Test OS filter
    response = client_with_db_override.get("/history/os-filter-host?os=ubuntu-20.04")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 2  # Two ubuntu packages
    for item in history:
        assert item['os'] == 'ubuntu-20.04'
    
    response = client_with_db_override.get("/history/os-filter-host?os=centos-8")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 1  # One centos package
    assert history[0]['os'] == 'centos-8'

def test_host_history_with_package_filter(client_with_db_override):
    """Test package name filtering functionality."""
    today = date.today()
    
    # Create test data with different package names
    client_with_db_override.post("/report", json={
        "hostname": "pkg-filter-host", "os": "ubuntu", "update_date": today.isoformat(),
        "updated_packages": [
            {"name": "nginx", "old_version": "1.0", "new_version": "1.1"},
            {"name": "apache2", "old_version": "2.0", "new_version": "2.1"},
            {"name": "nginx-common", "old_version": "1.0", "new_version": "1.1"}
        ]
    })
    
    # Test exact package name filter
    response = client_with_db_override.get("/history/pkg-filter-host?package=nginx")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 2  # nginx and nginx-common (partial match)
    package_names = [item['name'] for item in history]
    assert 'nginx' in package_names
    assert 'nginx-common' in package_names
    assert 'apache2' not in package_names
    
    # Test partial package name filter
    response = client_with_db_override.get("/history/pkg-filter-host?package=apa")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 1  # apache2
    assert history[0]['name'] == 'apache2'

def test_host_history_with_combined_filters(client_with_db_override):
    """Test combining multiple filters."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # Create test data with various combinations
    client_with_db_override.post("/report", json={
        "hostname": "combo-host", "os": "ubuntu", "update_date": today.isoformat(),
        "updated_packages": [{"name": "nginx", "old_version": "1.0", "new_version": "1.1"}]
    })
    client_with_db_override.post("/report", json={
        "hostname": "combo-host", "os": "centos", "update_date": today.isoformat(),
        "updated_packages": [{"name": "nginx", "old_version": "1.0", "new_version": "1.1"}]
    })
    client_with_db_override.post("/report", json={
        "hostname": "combo-host", "os": "ubuntu", "update_date": yesterday.isoformat(),
        "updated_packages": [{"name": "apache", "old_version": "2.0", "new_version": "2.1"}]
    })
    
    # Test combining OS and package filters
    response = client_with_db_override.get("/history/combo-host?os=ubuntu&package=nginx")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 1
    assert history[0]['os'] == 'ubuntu'
    assert history[0]['name'] == 'nginx'
    
    # Test combining date and OS filters
    response = client_with_db_override.get(f"/history/combo-host?date_from={today.isoformat()}&os=ubuntu")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 1
    assert history[0]['os'] == 'ubuntu'
    assert history[0]['update_date'] == today.isoformat()

def test_host_history_filter_validation(client_with_db_override):
    """Test filter parameter validation."""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    # Create test data
    client_with_db_override.post("/report", json={
        "hostname": "valid-host", "os": "ubuntu", "update_date": today.isoformat(),
        "updated_packages": [{"name": "pkg", "old_version": "1.0", "new_version": "1.1"}]
    })
    
    # Test invalid date range (date_from > date_to)
    response = client_with_db_override.get(f"/history/valid-host?date_from={tomorrow.isoformat()}&date_to={today.isoformat()}")
    assert response.status_code == 400
    error_msg = response.json().get('error') or response.json().get('detail')
    assert "date_from cannot be after date_to" in error_msg
    
    # Test invalid OS format
    response = client_with_db_override.get("/history/valid-host?os=invalid$os")
    assert response.status_code == 400
    error_msg = response.json().get('error') or response.json().get('detail')
    assert "Invalid OS format" in error_msg
    
    # Test invalid package name
    response = client_with_db_override.get("/history/valid-host?package=invalid$package")
    assert response.status_code == 400
    error_msg = response.json().get('error') or response.json().get('detail')
    assert "Invalid package name format" in error_msg

def test_host_history_no_results_with_filters(client_with_db_override):
    """Test that 404 is returned when filters yield no results."""
    today = date.today()
    
    # Create test data
    client_with_db_override.post("/report", json={
        "hostname": "no-results-host", "os": "ubuntu", "update_date": today.isoformat(),
        "updated_packages": [{"name": "nginx", "old_version": "1.0", "new_version": "1.1"}]
    })
    
    # Test filter that should yield no results
    response = client_with_db_override.get("/history/no-results-host?package=nonexistent")
    assert response.status_code == 404
    error_msg = response.json().get('error') or response.json().get('detail')
    assert "No update history found" in error_msg
