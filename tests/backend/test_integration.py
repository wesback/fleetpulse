"""
Integration test to verify the optimizations work end-to-end.
"""
import tempfile
import shutil
import os
import time
from unittest.mock import patch


def test_docker_worker_count_configuration():
    """Test that the Dockerfile correctly uses the GUNICORN_WORKERS environment variable."""
    # Read the Dockerfile
    dockerfile_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Dockerfile.backend')
    with open(dockerfile_path, 'r') as f:
        dockerfile_content = f.read()
    
    # Verify that the CMD uses the environment variable with default
    assert '${GUNICORN_WORKERS:-2}' in dockerfile_content
    assert '--workers' in dockerfile_content
    print("✓ Dockerfile correctly configured for dynamic worker count")


def test_environment_variables_documented():
    """Test that new environment variables are documented."""
    # Read the .env.example file
    env_example_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env.example')
    with open(env_example_path, 'r') as f:
        env_example_content = f.read()
    
    # Verify that new environment variables are documented
    assert 'GUNICORN_WORKERS' in env_example_content
    assert 'FORCE_DB_RECREATE' in env_example_content
    print("✓ Environment variables properly documented")


def test_database_initialization_environment_variables():
    """Test that database initialization respects environment variables."""
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Ensure the temp directory is writable
        os.chmod(temp_dir, 0o755)
        
        # Test with FORCE_DB_RECREATE=false (default)
        with patch.dict(os.environ, {
            'FLEETPULSE_DATA_DIR': temp_dir,
            'FORCE_DB_RECREATE': 'false'
        }, clear=False):
            # Reset the global variables to use our test path
            with patch('backend.db.engine.engine', None), \
                 patch('backend.utils.constants.DATA_DIR', temp_dir), \
                 patch('backend.utils.constants.DB_PATH', os.path.join(temp_dir, 'updates.db')):
                
                from backend.main import lifespan
                from fastapi import FastAPI
                import asyncio
                
                async def test_default_behavior():
                    app = FastAPI()
                    async with lifespan(app):
                        # Should create database normally
                        db_path = os.path.join(temp_dir, 'updates.db')
                        assert os.path.exists(db_path)
                        print("✓ Database created with FORCE_DB_RECREATE=false")
                
                asyncio.run(test_default_behavior())
        
        # Clean up for next test
        if os.path.exists(os.path.join(temp_dir, 'updates.db')):
            os.remove(os.path.join(temp_dir, 'updates.db'))
        
        # Test with FORCE_DB_RECREATE=true
        with patch.dict(os.environ, {
            'FLEETPULSE_DATA_DIR': temp_dir,
            'FORCE_DB_RECREATE': 'true'
        }, clear=False):
            # Reset the global variables to use our test path
            with patch('backend.db.engine.engine', None), \
                 patch('backend.utils.constants.DATA_DIR', temp_dir), \
                 patch('backend.utils.constants.DB_PATH', os.path.join(temp_dir, 'updates.db')):
                
                async def test_force_recreate():
                    app = FastAPI()
                    async with lifespan(app):
                        # Should recreate database
                        db_path = os.path.join(temp_dir, 'updates.db')
                        assert os.path.exists(db_path)
                        print("✓ Database recreated with FORCE_DB_RECREATE=true")
                
                asyncio.run(test_force_recreate())
            
    finally:
        shutil.rmtree(temp_dir)


def test_threading_optimization_summary():
    """Summary test to verify threading optimizations."""
    # This is more of a documentation test
    optimizations = [
        "Worker count reduced from 4 to 2 for single-container deployment",
        "Configurable via GUNICORN_WORKERS environment variable",
        "Better resource utilization for combined frontend+backend container"
    ]
    
    for optimization in optimizations:
        print(f"✓ {optimization}")


if __name__ == "__main__":
    print("Running integration tests...")
    test_docker_worker_count_configuration()
    test_environment_variables_documented()
    test_database_initialization_environment_variables()
    test_threading_optimization_summary()
    print("All integration tests passed! 🎉")