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