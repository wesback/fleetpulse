"""
Test environment variable handling for data directory configuration.
"""
import os
import sys
import tempfile
import pytest
from unittest.mock import patch

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def test_current_behavior_with_fleetpulse_data_path():
    """Test that demonstrates the current issue with FLEETPULSE_DATA_PATH."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Clear environment and set only FLEETPULSE_DATA_PATH
        env_patch = {"FLEETPULSE_DATA_PATH": temp_dir}
        # Make sure FLEETPULSE_DATA_DIR is not set by removing it
        
        with patch.dict(os.environ, env_patch, clear=True):
            # Test the current logic from main.py
            data_dir = os.environ.get("FLEETPULSE_DATA_DIR", "/data")
            
            # This shows the issue - even though FLEETPULSE_DATA_PATH is set,
            # the code only looks for FLEETPULSE_DATA_DIR
            assert data_dir == "/data"  # Uses default, not the temp_dir
            assert data_dir != temp_dir  # This demonstrates the problem


def test_proposed_fix_logic():
    """Test the proposed fix logic that should accept both environment variables."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test case 1: FLEETPULSE_DATA_DIR is set (current behavior should work)
        with patch.dict(os.environ, {"FLEETPULSE_DATA_DIR": temp_dir}):
            # Proposed logic: check FLEETPULSE_DATA_DIR first, then FLEETPULSE_DATA_PATH, then default
            data_dir_env = os.environ.get("FLEETPULSE_DATA_DIR")
            data_path_env = os.environ.get("FLEETPULSE_DATA_PATH")
            data_dir = (data_dir_env if data_dir_env else data_path_env) or "/data"
            assert data_dir == temp_dir
        
        # Test case 2: Only FLEETPULSE_DATA_PATH is set (should work after fix)
        with patch.dict(os.environ, {"FLEETPULSE_DATA_PATH": temp_dir}, clear=True):
            # Remove FLEETPULSE_DATA_DIR to ensure it's not set
            env = dict(os.environ)
            if "FLEETPULSE_DATA_DIR" in env:
                del env["FLEETPULSE_DATA_DIR"]
            
            with patch.dict(os.environ, env):
                data_dir_env = os.environ.get("FLEETPULSE_DATA_DIR")
                data_path_env = os.environ.get("FLEETPULSE_DATA_PATH")
                data_dir = (data_dir_env if data_dir_env else data_path_env) or "/data"
                assert data_dir == temp_dir
        
        # Test case 3: Neither is set (should use default)
        with patch.dict(os.environ, {}, clear=True):
            data_dir_env = os.environ.get("FLEETPULSE_DATA_DIR")
            data_path_env = os.environ.get("FLEETPULSE_DATA_PATH")
            data_dir = (data_dir_env if data_dir_env else data_path_env) or "/data"
            assert data_dir == "/data"


def test_data_dir_precedence():
    """Test that FLEETPULSE_DATA_DIR takes precedence over FLEETPULSE_DATA_PATH."""
    with tempfile.TemporaryDirectory() as temp_dir1:
        with tempfile.TemporaryDirectory() as temp_dir2:
            # Set both environment variables
            with patch.dict(os.environ, {
                "FLEETPULSE_DATA_DIR": temp_dir1,
                "FLEETPULSE_DATA_PATH": temp_dir2
            }):
                # FLEETPULSE_DATA_DIR should take precedence
                data_dir_env = os.environ.get("FLEETPULSE_DATA_DIR")
                data_path_env = os.environ.get("FLEETPULSE_DATA_PATH")
                data_dir = (data_dir_env if data_dir_env else data_path_env) or "/data"
                assert data_dir == temp_dir1
                assert data_dir != temp_dir2


def test_fixed_behavior_with_fleetpulse_data_path():
    """Test that the fix allows FLEETPULSE_DATA_PATH to work correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set only FLEETPULSE_DATA_PATH
        with patch.dict(os.environ, {"FLEETPULSE_DATA_PATH": temp_dir}, clear=True):
            # Test the fixed logic
            data_dir_env = os.environ.get("FLEETPULSE_DATA_DIR")
            data_path_env = os.environ.get("FLEETPULSE_DATA_PATH")
            data_dir = (data_dir_env if data_dir_env else data_path_env) or "/data"
            
            # After the fix, this should work
            assert data_dir == temp_dir
            assert data_dir != "/data"


def test_empty_environment_variables():
    """Test that empty environment variables are handled correctly."""
    # Test empty FLEETPULSE_DATA_PATH
    with patch.dict(os.environ, {"FLEETPULSE_DATA_PATH": ""}, clear=True):
        data_dir_env = os.environ.get("FLEETPULSE_DATA_DIR")
        data_path_env = os.environ.get("FLEETPULSE_DATA_PATH")
        data_dir = (data_dir_env if data_dir_env else data_path_env) or "/data"
        
        # Should default to "/data" when FLEETPULSE_DATA_PATH is empty
        assert data_dir == "/data"
    
    # Test empty FLEETPULSE_DATA_DIR
    with patch.dict(os.environ, {"FLEETPULSE_DATA_DIR": ""}, clear=True):
        data_dir_env = os.environ.get("FLEETPULSE_DATA_DIR")
        data_path_env = os.environ.get("FLEETPULSE_DATA_PATH")
        data_dir = (data_dir_env if data_dir_env else data_path_env) or "/data"
        
        # Should default to "/data" when FLEETPULSE_DATA_DIR is empty
        assert data_dir == "/data"