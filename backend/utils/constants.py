"""Constants used throughout the application."""
import os

# Field length constraints
MAX_HOSTNAME_LENGTH = 255
MAX_PACKAGE_NAME_LENGTH = 255
MAX_VERSION_LENGTH = 100
MAX_OS_LENGTH = 50

# Database configuration
DATA_DIR = os.environ.get("FLEETPULSE_DATA_DIR", "./data")
DB_PATH = os.path.join(DATA_DIR, "updates.db")

# Database type configuration
DATABASE_TYPE = os.environ.get("DATABASE_TYPE", "sqlite").lower()

# PostgreSQL configuration (only used when DATABASE_TYPE=postgresql)
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "fleetpulse")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "fleetpulse")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "fleetpulse")
POSTGRES_SSLMODE = os.environ.get("POSTGRES_SSLMODE", "prefer")

# Constructed DATABASE_URL (can be overridden by environment variable)
if DATABASE_TYPE == "postgresql":
    DATABASE_URL = os.environ.get(
        "DATABASE_URL",
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}?sslmode={POSTGRES_SSLMODE}"
    )
else:
    # SQLite default
    DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")