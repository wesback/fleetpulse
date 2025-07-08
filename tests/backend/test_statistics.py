import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import tempfile
import shutil
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from backend.main import app, get_session, get_engine, SQLModel as AppSQLModel
from datetime import date, timedelta

@pytest.fixture(scope="session")
def temp_db_file():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_statistics.db")
    yield db_path
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="session")
def override_engine(temp_db_file):
    engine = create_engine(f"sqlite:///{temp_db_file}", connect_args={"check_same_thread": False})
    return engine

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

def test_statistics_endpoint_empty_database(client_with_db_override):
    """Test statistics endpoint with empty database."""
    response = client_with_db_override.get("/statistics")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total_hosts"] == 0
    assert data["total_updates"] == 0
    assert data["recent_updates"] == 0
    assert data["top_packages"] == []
    assert data["updates_by_os"] == []
    assert data["updates_timeline"] == []
    assert data["host_activity"] == []

def test_statistics_endpoint_with_data(client_with_db_override):
    """Test statistics endpoint with sample data."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)
    old_date = today - timedelta(days=45)  # Outside 30-day window
    
    # Create test data with different hosts, OS, and time periods
    test_data = [
        # Host 1 - Ubuntu (recent)
        {
            "hostname": "host1", "os": "Ubuntu 22.04", "update_date": today.isoformat(),
            "updated_packages": [
                {"name": "nginx", "old_version": "1.0", "new_version": "1.1"},
                {"name": "apache2", "old_version": "2.0", "new_version": "2.1"}
            ]
        },
        # Host 1 - Ubuntu (recent)
        {
            "hostname": "host1", "os": "Ubuntu 22.04", "update_date": yesterday.isoformat(),
            "updated_packages": [
                {"name": "nginx", "old_version": "1.1", "new_version": "1.2"},
                {"name": "mysql", "old_version": "8.0", "new_version": "8.1"}
            ]
        },
        # Host 2 - CentOS (recent)
        {
            "hostname": "host2", "os": "CentOS 7", "update_date": two_days_ago.isoformat(),
            "updated_packages": [
                {"name": "nginx", "old_version": "1.0", "new_version": "1.1"},
                {"name": "redis", "old_version": "6.0", "new_version": "6.2"}
            ]
        },
        # Host 3 - Debian (old - outside 30-day window)
        {
            "hostname": "host3", "os": "Debian 11", "update_date": old_date.isoformat(),
            "updated_packages": [
                {"name": "postgresql", "old_version": "13.0", "new_version": "13.1"}
            ]
        },
        # Host 4 - Ubuntu (recent, most active)
        {
            "hostname": "host4", "os": "Ubuntu 22.04", "update_date": today.isoformat(),
            "updated_packages": [
                {"name": "nginx", "old_version": "1.0", "new_version": "1.1"},
                {"name": "apache2", "old_version": "2.0", "new_version": "2.1"},
                {"name": "mysql", "old_version": "8.0", "new_version": "8.1"},
                {"name": "redis", "old_version": "6.0", "new_version": "6.2"},
                {"name": "nodejs", "old_version": "16.0", "new_version": "18.0"}
            ]
        }
    ]
    
    # Post all test data
    for data in test_data:
        response = client_with_db_override.post("/report", json=data)
        assert response.status_code == 201
    
    # Get statistics
    response = client_with_db_override.get("/statistics")
    assert response.status_code == 200
    
    stats = response.json()
    
    # Verify basic counts
    assert stats["total_hosts"] == 4  # host1, host2, host3, host4
    assert stats["total_updates"] == 11  # Total packages across all reports
    assert stats["recent_updates"] == 10  # All except the old host3 update
    
    # Verify top packages (nginx should be most frequent with 3 updates)
    top_packages = stats["top_packages"]
    assert len(top_packages) > 0
    
    # Find nginx in top packages
    nginx_stats = next((pkg for pkg in top_packages if pkg["name"] == "nginx"), None)
    assert nginx_stats is not None
    assert nginx_stats["count"] == 3  # Updated on host1, host2, host4
    
    # Verify updates by OS
    updates_by_os = stats["updates_by_os"]
    assert len(updates_by_os) == 3  # Ubuntu, CentOS, Debian
    
    # Find Ubuntu stats (should have most updates)
    ubuntu_stats = next((os_stat for os_stat in updates_by_os if "Ubuntu" in os_stat["os"]), None)
    assert ubuntu_stats is not None
    assert ubuntu_stats["count"] == 7  # 2 + 5 from host1 and host4
    
    # Verify timeline has recent dates
    timeline = stats["updates_timeline"]
    assert len(timeline) > 0
    
    # Timeline should only include recent updates (within 30 days)
    timeline_dates = [entry["date"] for entry in timeline]
    assert today.isoformat() in timeline_dates
    assert yesterday.isoformat() in timeline_dates
    assert old_date.isoformat() not in timeline_dates
    
    # Verify host activity
    host_activity = stats["host_activity"]
    assert len(host_activity) == 4  # All hosts
    
    # host4 should be most active with 5 updates
    most_active = host_activity[0]  # Should be ordered by count desc
    assert most_active["hostname"] == "host4"
    assert most_active["count"] == 5
    assert most_active["last_update"] == today.isoformat()

def test_statistics_endpoint_recent_vs_old_data(client_with_db_override):
    """Test that statistics correctly differentiates between recent and old data."""
    today = date.today()
    recent_date = today - timedelta(days=15)  # Within 30 days
    old_date = today - timedelta(days=45)     # Outside 30 days
    
    # Add recent data
    client_with_db_override.post("/report", json={
        "hostname": "recent-host", "os": "Ubuntu", "update_date": recent_date.isoformat(),
        "updated_packages": [{"name": "recent-pkg", "old_version": "1.0", "new_version": "1.1"}]
    })
    
    # Add old data
    client_with_db_override.post("/report", json={
        "hostname": "old-host", "os": "Ubuntu", "update_date": old_date.isoformat(),
        "updated_packages": [{"name": "old-pkg", "old_version": "1.0", "new_version": "1.1"}]
    })
    
    response = client_with_db_override.get("/statistics")
    assert response.status_code == 200
    
    stats = response.json()
    
    # Total should include all data
    assert stats["total_hosts"] == 2
    assert stats["total_updates"] == 2
    
    # Recent should only include data within 30 days
    assert stats["recent_updates"] == 1
    
    # Timeline should only include recent data
    timeline = stats["updates_timeline"]
    timeline_dates = [entry["date"] for entry in timeline]
    assert recent_date.isoformat() in timeline_dates
    assert old_date.isoformat() not in timeline_dates

def test_statistics_endpoint_top_packages_limit(client_with_db_override):
    """Test that top packages are limited to top 10."""
    today = date.today()
    
    # Create 15 different packages to test the limit
    packages = []
    for i in range(15):
        # Create packages with different update frequencies
        # Package 0 will have 15 updates, package 1 will have 14, etc.
        for j in range(15 - i):
            packages.append({
                "name": f"package{i:02d}",
                "old_version": f"1.{j}",
                "new_version": f"1.{j+1}"
            })
    
    # Post all packages
    client_with_db_override.post("/report", json={
        "hostname": "test-host", "os": "Ubuntu", "update_date": today.isoformat(),
        "updated_packages": packages
    })
    
    response = client_with_db_override.get("/statistics")
    assert response.status_code == 200
    
    stats = response.json()
    
    # Should only return top 10 packages
    top_packages = stats["top_packages"]
    assert len(top_packages) == 10
    
    # Should be ordered by count (descending)
    assert top_packages[0]["name"] == "package00"
    assert top_packages[0]["count"] == 15
    assert top_packages[1]["name"] == "package01"
    assert top_packages[1]["count"] == 14
    assert top_packages[9]["name"] == "package09"
    assert top_packages[9]["count"] == 6

def test_statistics_endpoint_host_activity_limit(client_with_db_override):
    """Test that host activity is limited to top 10 hosts."""
    today = date.today()
    
    # Create 15 hosts with different activity levels
    for i in range(15):
        packages = []
        # Host 0 will have 15 updates, host 1 will have 14, etc.
        for j in range(15 - i):
            packages.append({
                "name": f"pkg{j}",
                "old_version": "1.0",
                "new_version": "1.1"
            })
        
        client_with_db_override.post("/report", json={
            "hostname": f"host{i:02d}", "os": "Ubuntu", "update_date": today.isoformat(),
            "updated_packages": packages
        })
    
    response = client_with_db_override.get("/statistics")
    assert response.status_code == 200
    
    stats = response.json()
    
    # Should only return top 10 hosts
    host_activity = stats["host_activity"]
    assert len(host_activity) == 10
    
    # Should be ordered by count (descending)
    assert host_activity[0]["hostname"] == "host00"
    assert host_activity[0]["count"] == 15
    assert host_activity[1]["hostname"] == "host01"
    assert host_activity[1]["count"] == 14
    assert host_activity[9]["hostname"] == "host09"
    assert host_activity[9]["count"] == 6

def test_statistics_endpoint_timeline_data_structure(client_with_db_override):
    """Test that timeline data has correct structure and date formatting."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # Add data for multiple dates
    client_with_db_override.post("/report", json={
        "hostname": "host1", "os": "Ubuntu", "update_date": today.isoformat(),
        "updated_packages": [
            {"name": "pkg1", "old_version": "1.0", "new_version": "1.1"},
            {"name": "pkg2", "old_version": "2.0", "new_version": "2.1"}
        ]
    })
    
    client_with_db_override.post("/report", json={
        "hostname": "host2", "os": "Ubuntu", "update_date": yesterday.isoformat(),
        "updated_packages": [
            {"name": "pkg3", "old_version": "3.0", "new_version": "3.1"}
        ]
    })
    
    response = client_with_db_override.get("/statistics")
    assert response.status_code == 200
    
    stats = response.json()
    timeline = stats["updates_timeline"]
    
    # Should have entries for both dates
    assert len(timeline) == 2
    
    # Verify structure and ordering (should be chronological)
    for entry in timeline:
        assert "date" in entry
        assert "count" in entry
        assert isinstance(entry["count"], int)
        assert entry["count"] > 0
        
        # Verify date format (ISO format)
        from datetime import datetime
        parsed_date = datetime.fromisoformat(entry["date"])
        assert isinstance(parsed_date, datetime)
    
    # Should be ordered chronologically (oldest first)
    dates = [entry["date"] for entry in timeline]
    assert dates == sorted(dates)

def test_statistics_endpoint_edge_cases(client_with_db_override):
    """Test statistics endpoint with edge cases."""
    today = date.today()
    
    # Test with single host, single package
    client_with_db_override.post("/report", json={
        "hostname": "single-host", "os": "Ubuntu", "update_date": today.isoformat(),
        "updated_packages": [{"name": "single-pkg", "old_version": "1.0", "new_version": "1.1"}]
    })
    
    response = client_with_db_override.get("/statistics")
    assert response.status_code == 200
    
    stats = response.json()
    assert stats["total_hosts"] == 1
    assert stats["total_updates"] == 1
    assert stats["recent_updates"] == 1
    assert len(stats["top_packages"]) == 1
    assert stats["top_packages"][0]["name"] == "single-pkg"
    assert stats["top_packages"][0]["count"] == 1

def test_statistics_endpoint_data_consistency(client_with_db_override):
    """Test that statistics data is consistent across different metrics."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # Add diverse test data
    test_reports = [
        {
            "hostname": "web-server", "os": "Ubuntu 22.04", "update_date": today.isoformat(),
            "updated_packages": [
                {"name": "nginx", "old_version": "1.20", "new_version": "1.21"},
                {"name": "openssl", "old_version": "1.1.1", "new_version": "1.1.2"}
            ]
        },
        {
            "hostname": "db-server", "os": "CentOS 8", "update_date": yesterday.isoformat(),
            "updated_packages": [
                {"name": "postgresql", "old_version": "13.0", "new_version": "13.1"},
                {"name": "openssl", "old_version": "1.1.1", "new_version": "1.1.2"}
            ]
        }
    ]
    
    for report in test_reports:
        response = client_with_db_override.post("/report", json=report)
        assert response.status_code == 201
    
    response = client_with_db_override.get("/statistics")
    assert response.status_code == 200
    
    stats = response.json()
    
    # Verify data consistency
    assert stats["total_hosts"] == 2
    assert stats["total_updates"] == 4
    assert stats["recent_updates"] == 4  # All updates are within 30 days
    
    # Verify OS distribution sums to total updates
    os_total = sum(os_stat["count"] for os_stat in stats["updates_by_os"])
    assert os_total == stats["total_updates"]
    
    # Verify host activity sums to total updates
    host_total = sum(host_stat["count"] for host_stat in stats["host_activity"])
    assert host_total == stats["total_updates"]
    
    # Verify timeline sums to recent updates
    timeline_total = sum(entry["count"] for entry in stats["updates_timeline"])
    assert timeline_total == stats["recent_updates"]

def test_statistics_endpoint_error_handling(client_with_db_override):
    """Test statistics endpoint error handling and response structure."""
    # Test with empty database - should not error
    response = client_with_db_override.get("/statistics")
    assert response.status_code == 200
    
    # Verify response structure is always present
    stats = response.json()
    required_fields = [
        "total_hosts", "total_updates", "recent_updates",
        "top_packages", "updates_by_os", "updates_timeline", "host_activity"
    ]
    
    for field in required_fields:
        assert field in stats
        
    # Verify numeric fields are integers
    assert isinstance(stats["total_hosts"], int)
    assert isinstance(stats["total_updates"], int)
    assert isinstance(stats["recent_updates"], int)
    
    # Verify array fields are lists
    assert isinstance(stats["top_packages"], list)
    assert isinstance(stats["updates_by_os"], list)
    assert isinstance(stats["updates_timeline"], list)
    assert isinstance(stats["host_activity"], list)

def test_statistics_endpoint_date_boundary_conditions(client_with_db_override):
    """Test statistics endpoint with edge cases around 30-day boundary."""
    today = date.today()
    exactly_30_days_ago = today - timedelta(days=30)
    exactly_31_days_ago = today - timedelta(days=31)
    
    # Add data exactly at 30-day boundary
    client_with_db_override.post("/report", json={
        "hostname": "boundary-host", "os": "Ubuntu", "update_date": exactly_30_days_ago.isoformat(),
        "updated_packages": [{"name": "boundary-pkg", "old_version": "1.0", "new_version": "1.1"}]
    })
    
    # Add data outside 30-day boundary
    client_with_db_override.post("/report", json={
        "hostname": "old-host", "os": "Ubuntu", "update_date": exactly_31_days_ago.isoformat(),
        "updated_packages": [{"name": "old-pkg", "old_version": "1.0", "new_version": "1.1"}]
    })
    
    response = client_with_db_override.get("/statistics")
    assert response.status_code == 200
    
    stats = response.json()
    
    # Total should include all data
    assert stats["total_hosts"] == 2
    assert stats["total_updates"] == 2
    
    # Recent should include data from exactly 30 days ago (>=)
    assert stats["recent_updates"] == 1
    
    # Timeline should include the 30-day boundary data
    timeline = stats["updates_timeline"]
    timeline_dates = [entry["date"] for entry in timeline]
    assert exactly_30_days_ago.isoformat() in timeline_dates
    assert exactly_31_days_ago.isoformat() not in timeline_dates
