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
