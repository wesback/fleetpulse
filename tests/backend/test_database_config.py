"""Test database configuration and engine creation."""
import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_sqlite_default_configuration():
    """Test that SQLite is the default database configuration."""
    # Clear any existing environment variables
    for key in ['DATABASE_TYPE', 'DATABASE_URL', 'POSTGRES_HOST']:
        os.environ.pop(key, None)
    
    # Re-import constants to get fresh values
    import importlib
    from backend.utils import constants
    importlib.reload(constants)
    
    assert constants.DATABASE_TYPE == "sqlite"
    assert "sqlite:///" in constants.DATABASE_URL


def test_postgresql_configuration():
    """Test PostgreSQL configuration via environment variables."""
    # Set PostgreSQL environment variables
    os.environ['DATABASE_TYPE'] = 'postgresql'
    os.environ['POSTGRES_HOST'] = 'testhost'
    os.environ['POSTGRES_PORT'] = '5433'
    os.environ['POSTGRES_DB'] = 'testdb'
    os.environ['POSTGRES_USER'] = 'testuser'
    os.environ['POSTGRES_PASSWORD'] = 'testpass'
    
    # Re-import constants to get fresh values
    import importlib
    from backend.utils import constants
    importlib.reload(constants)
    
    assert constants.DATABASE_TYPE == "postgresql"
    assert constants.POSTGRES_HOST == "testhost"
    assert constants.POSTGRES_PORT == "5433"
    assert constants.POSTGRES_DB == "testdb"
    assert constants.POSTGRES_USER == "testuser"
    assert constants.POSTGRES_PASSWORD == "testpass"
    assert "postgresql://" in constants.DATABASE_URL
    assert "testhost:5433" in constants.DATABASE_URL
    assert "testdb" in constants.DATABASE_URL
    
    # Clean up
    for key in ['DATABASE_TYPE', 'POSTGRES_HOST', 'POSTGRES_PORT', 
                'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']:
        os.environ.pop(key, None)


def test_database_url_override():
    """Test that DATABASE_URL can override individual parameters."""
    custom_url = "postgresql://customuser:custompass@customhost:9999/customdb"
    os.environ['DATABASE_TYPE'] = 'postgresql'
    os.environ['DATABASE_URL'] = custom_url
    
    # Re-import constants to get fresh values
    import importlib
    from backend.utils import constants
    importlib.reload(constants)
    
    assert constants.DATABASE_URL == custom_url
    
    # Clean up
    os.environ.pop('DATABASE_TYPE', None)
    os.environ.pop('DATABASE_URL', None)


def test_sqlite_engine_creation():
    """Test that SQLite engine can be created successfully."""
    # Clear environment
    for key in ['DATABASE_TYPE', 'DATABASE_URL']:
        os.environ.pop(key, None)
    
    # Create a temporary directory for the database
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['FLEETPULSE_DATA_DIR'] = tmpdir
        
        # Re-import to get fresh values
        import importlib
        from backend.utils import constants
        from backend.db import engine as engine_module
        importlib.reload(constants)
        
        # Reset the global engine
        engine_module.engine = None
        
        # Create engine
        from backend.db.engine import get_engine
        engine = get_engine()
        
        assert engine is not None
        assert "sqlite:///" in str(engine.url)
        
        # Test connection
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            assert result == 1
        
        # Clean up
        engine_module.engine = None
        os.environ.pop('FLEETPULSE_DATA_DIR', None)


def test_backward_compatibility():
    """Test that existing SQLite behavior is maintained."""
    # This test ensures that without any configuration,
    # the system works exactly as before
    
    # Clear all database-related environment variables
    for key in list(os.environ.keys()):
        if any(x in key for x in ['DATABASE', 'POSTGRES', 'DB_']):
            os.environ.pop(key, None)
    
    # Re-import constants
    import importlib
    from backend.utils import constants
    importlib.reload(constants)
    
    # Verify default behavior
    assert constants.DATABASE_TYPE == "sqlite"
    assert constants.DB_PATH == os.path.join(constants.DATA_DIR, "updates.db")
    assert "sqlite:///" in constants.DATABASE_URL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
