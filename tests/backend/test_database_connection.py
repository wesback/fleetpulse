import tempfile
import shutil
import pytest
import os
from sqlalchemy import text
from backend.main import get_engine


def test_database_engine_creation():
    """Test that the database engine can be created without SQLAlchemy compatibility issues."""
    # Set up a temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Set environment variable to use test directory
        original_data_dir = os.environ.get("FLEETPULSE_DATA_DIR")
        os.environ["FLEETPULSE_DATA_DIR"] = temp_dir
        
        # Reset the global engine and update the paths to force re-creation
        import backend.main
        original_engine = backend.main.engine
        original_data_dir_module = backend.main.DATA_DIR
        original_db_path_module = backend.main.DB_PATH
        
        backend.main.engine = None
        backend.main.DATA_DIR = temp_dir
        backend.main.DB_PATH = os.path.join(temp_dir, "updates.db")
        
        # This should work without throwing SQLAlchemy compatibility errors
        engine = get_engine()
        assert engine is not None
        
        # Test that we can actually connect and execute SQL
        with engine.connect() as conn:
            # This should not raise "Not an executable object" error
            result = conn.execute(text("SELECT 1"))
            assert result is not None
            
    finally:
        # Restore original state
        if original_data_dir is not None:
            os.environ["FLEETPULSE_DATA_DIR"] = original_data_dir
        else:
            os.environ.pop("FLEETPULSE_DATA_DIR", None)
        backend.main.engine = original_engine
        backend.main.DATA_DIR = original_data_dir_module
        backend.main.DB_PATH = original_db_path_module
        
        # Clean up
        shutil.rmtree(temp_dir)