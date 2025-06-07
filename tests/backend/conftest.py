#!/usr/bin/python3
# tests/backend/conftest.py
import pytest
import os
import tempfile
import shutil

@pytest.fixture(scope="session", autouse=True)
def set_test_environment():
    """Configures the test environment before any tests run."""
    temp_dir = tempfile.mkdtemp()
    original_env_var = os.environ.get("FLEETPULSE_DATA_DIR")
    os.environ["FLEETPULSE_DATA_DIR"] = temp_dir
    # print(f"[conftest.py] FLEETPULSE_DATA_DIR set to {temp_dir}") # For debugging

    yield  # Allows the test session to run

    # Teardown: Clean up after the entire test session
    if original_env_var is None:
        if "FLEETPULSE_DATA_DIR" in os.environ:
            del os.environ["FLEETPULSE_DATA_DIR"]
    else:
        os.environ["FLEETPULSE_DATA_DIR"] = original_env_var
    shutil.rmtree(temp_dir)
    # print(f"[conftest.py] Cleaned up FLEETPULSE_DATA_DIR {temp_dir}") # For debugging
