"""Tests for the natural language chat functionality."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta
from backend.main import app, PackageUpdate
from sqlmodel import Session

# Import fixtures from test_main.py 
from .test_main import (
    temp_db_file, override_engine, override_get_session, 
    set_dependency_overrides, client_with_db_override, setup_database_for_each_test
)


@pytest.fixture
def client_with_sample_data(override_engine):
    """Create a test client with sample data for chat testing."""
    # Create sample data
    with Session(override_engine) as session:
        updates = [
            PackageUpdate(
                hostname="web-01",
                os="Ubuntu 20.04",
                update_date=date.today() - timedelta(days=2),
                name="nginx",
                old_version="1.18.0",
                new_version="1.20.1"
            ),
            PackageUpdate(
                hostname="web-01",
                os="Ubuntu 20.04",
                update_date=date.today() - timedelta(days=2),
                name="python3",
                old_version="3.8.5",
                new_version="3.8.10"
            ),
            PackageUpdate(
                hostname="db-01",
                os="CentOS 7",
                update_date=date.today() - timedelta(days=5),
                name="mysql-server",
                old_version="5.7.32",
                new_version="5.7.35"
            ),
            PackageUpdate(
                hostname="app-01",
                os="Ubuntu 22.04",
                update_date=date.today() - timedelta(days=10),
                name="nodejs",
                old_version="14.17.0",
                new_version="16.14.0"
            ),
        ]
        
        for update in updates:
            session.add(update)
        session.commit()
    
    return TestClient(app)


def test_chat_empty_question(client_with_db_override):
    """Test chat endpoint with empty question."""
    response = client_with_db_override.post("/chat", json={"question": ""})
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]


def test_chat_too_long_question(client_with_db_override):
    """Test chat endpoint with too long question."""
    long_question = "a" * 501
    response = client_with_db_override.post("/chat", json={"question": long_question})
    assert response.status_code == 400
    assert "too long" in response.json()["detail"]


def test_chat_help_response(client_with_db_override):
    """Test chat endpoint returns help for unknown questions."""
    response = client_with_db_override.post("/chat", json={"question": "random question"})
    assert response.status_code == 200
    data = response.json()
    assert data["query_type"] == "help"
    assert "I can help you" in data["answer"]


def test_chat_which_hosts_updated(client_with_sample_data):
    """Test 'which hosts' type queries."""
    response = client_with_sample_data.post("/chat", json={"question": "Which hosts had python updated last week?"})
    assert response.status_code == 200
    data = response.json()
    assert data["query_type"] == "hosts_updated"
    assert "web-01" in data["answer"]
    assert isinstance(data["data"], list)


def test_chat_what_packages_on_host(client_with_sample_data):
    """Test 'what packages' type queries."""
    response = client_with_sample_data.post("/chat", json={"question": "What packages were updated on web-01?"})
    assert response.status_code == 200
    data = response.json()
    assert data["query_type"] == "packages_on_host"
    assert "nginx" in data["answer"] or "python3" in data["answer"]
    assert isinstance(data["data"], list)


def test_chat_show_os_hosts(client_with_sample_data):
    """Test 'show me hosts' type queries."""
    response = client_with_sample_data.post("/chat", json={"question": "Show me Ubuntu hosts"})
    assert response.status_code == 200
    data = response.json()
    assert data["query_type"] == "os_hosts"
    assert "Ubuntu" in data["answer"]
    assert isinstance(data["data"], list)


def test_chat_count_hosts(client_with_sample_data):
    """Test 'how many hosts' type queries."""
    response = client_with_sample_data.post("/chat", json={"question": "How many hosts do we have?"})
    assert response.status_code == 200
    data = response.json()
    assert data["query_type"] == "count_hosts"
    assert "host(s) total" in data["answer"]


def test_chat_stale_hosts(client_with_sample_data):
    """Test 'haven't been updated' type queries."""
    response = client_with_sample_data.post("/chat", json={"question": "Which hosts haven't been updated in 7 days?"})
    assert response.status_code == 200
    data = response.json()
    assert data["query_type"] == "stale_hosts"
    # app-01 should be in stale hosts since it was updated 10 days ago
    assert isinstance(data["data"], list)


def test_chat_packages_clarification(client_with_db_override):
    """Test packages query without hostname returns clarification."""
    response = client_with_db_override.post("/chat", json={"question": "What packages were updated?"})
    assert response.status_code == 200
    data = response.json()
    assert data["query_type"] == "clarification"
    assert "specify which host" in data["answer"]