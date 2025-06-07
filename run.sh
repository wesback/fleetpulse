#!/bin/bash

# FleetPulse startup script
# Automatically sets USER_ID and GROUP_ID to match the current user
# This ensures proper file permissions for Docker volume mounts

# Get current user's UID and GID
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)

# Ensure data directory exists with proper permissions
mkdir -p ./data

echo "Starting FleetPulse with USER_ID=$USER_ID and GROUP_ID=$GROUP_ID"

# Check if we need to rebuild (if args changed)
if [ "$1" = "--rebuild" ] || [ "$1" = "-r" ]; then
    echo "Rebuilding container..."
    docker-compose build --no-cache
fi

# Start the application
docker-compose up "$@"
