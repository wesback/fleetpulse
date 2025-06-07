import tempfile
import shutil
import pytest
import os
import asyncio
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, inspect, text
from sqlmodel import SQLModel
from backend.main import lifespan, PackageUpdate, get_engine, DATA_DIR, DB_PATH
from fastapi import FastAPI


@pytest.mark.asyncio
async def test_database_initialization_new_database():
    """Test that database is created properly when it doesn't exist."""
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Mock the environment variables and paths
        with patch.dict(os.environ, {"FLEETPULSE_DATA_DIR": temp_dir}):
            with patch('backend.main.DATA_DIR', temp_dir):
                with patch('backend.main.DB_PATH', os.path.join(temp_dir, "test.db")):
                    with patch('backend.main.engine', None):
                        # Create a test app
                        app = FastAPI()
                        
                        # Mock logger to capture log messages
                        with patch('backend.main.logger') as mock_logger:
                            # Run the lifespan startup
                            async with lifespan(app):
                                # Verify that the database file was created
                                assert os.path.exists(os.path.join(temp_dir, "test.db"))
                                
                                # Verify that proper log messages were called
                                mock_logger.info.assert_any_call("New database - creating tables...")
                                mock_logger.info.assert_any_call("Database tables created successfully")
                            
    finally:
        shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_database_initialization_existing_database():
    """Test that existing database tables are not recreated."""
    temp_dir = tempfile.mkdtemp()
    
    try:
        db_path = os.path.join(temp_dir, "test.db")
        
        # First, create a database with tables
        engine = create_engine(f"sqlite:///{db_path}")
        SQLModel.metadata.create_all(engine)
        
        # Now test that the lifespan doesn't recreate tables
        with patch.dict(os.environ, {"FLEETPULSE_DATA_DIR": temp_dir}):
            with patch('backend.main.DATA_DIR', temp_dir):
                with patch('backend.main.DB_PATH', db_path):
                    with patch('backend.main.engine', None):
                        app = FastAPI()
                        
                        with patch('backend.main.logger') as mock_logger:
                            async with lifespan(app):
                                # Verify that it detected existing tables
                                mock_logger.info.assert_any_call("Database tables already exist - skipping creation")
                            
    finally:
        shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_database_initialization_force_recreate():
    """Test that FORCE_DB_RECREATE environment variable works."""
    temp_dir = tempfile.mkdtemp()
    
    try:
        db_path = os.path.join(temp_dir, "test.db")
        
        # First, create a database with tables
        engine = create_engine(f"sqlite:///{db_path}")
        SQLModel.metadata.create_all(engine)
        
        # Now test force recreation
        with patch.dict(os.environ, {
            "FLEETPULSE_DATA_DIR": temp_dir,
            "FORCE_DB_RECREATE": "true"
        }):
            with patch('backend.main.DATA_DIR', temp_dir):
                with patch('backend.main.DB_PATH', db_path):
                    with patch('backend.main.engine', None):
                        app = FastAPI()
                        
                        with patch('backend.main.logger') as mock_logger:
                            async with lifespan(app):
                                # Verify that it forced recreation
                                mock_logger.info.assert_any_call("Force recreation enabled - dropping and recreating all tables...")
                                mock_logger.info.assert_any_call("Database tables recreated successfully")
                            
    finally:
        shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_database_initialization_missing_tables():
    """Test that missing tables are created when database exists but tables are missing."""
    temp_dir = tempfile.mkdtemp()
    
    try:
        db_path = os.path.join(temp_dir, "test.db")
        
        # Create an empty database file (simulating a database without our tables)
        with open(db_path, 'w') as f:
            f.write("")  # Empty file
        
        # Create engine and add some random table (not our model)
        engine = create_engine(f"sqlite:///{db_path}")
        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE some_other_table (id INTEGER PRIMARY KEY)"))
            conn.commit()
        
        with patch.dict(os.environ, {"FLEETPULSE_DATA_DIR": temp_dir}):
            with patch('backend.main.DATA_DIR', temp_dir):
                with patch('backend.main.DB_PATH', db_path):
                    with patch('backend.main.engine', None):
                        app = FastAPI()
                        
                        with patch('backend.main.logger') as mock_logger:
                            async with lifespan(app):
                                # Verify that it detected missing tables and created them
                                mock_logger.info.assert_any_call("Database exists but tables missing - creating tables...")
                                mock_logger.info.assert_any_call("Database tables created successfully")
                            
    finally:
        shutil.rmtree(temp_dir)