#!/bin/bash

# Script to run backend Python tests using pytest

# Navigate to the project root if the script is not already there
# This ensures that pytest can find the backend and tests directories correctly.
# If your script is already in the project root, this cd command won't have an adverse effect.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")" # Assumes this script is in a 'scripts' or similar subdir

# If the script is in the project root, adjust PROJECT_ROOT accordingly
if [ -f "$SCRIPT_DIR/backend/main.py" ]; then 
    PROJECT_ROOT="$SCRIPT_DIR"
elif [ -f "$PROJECT_ROOT/backend/main.py" ]; then
    echo "Running from project root or scripts subdirectory."
else
    echo "Error: Could not determine project root. Make sure backend/main.py exists."
    echo "SCRIPT_DIR: $SCRIPT_DIR"
    echo "PROJECT_ROOT: $PROJECT_ROOT"
    exit 1
fi

cd "$PROJECT_ROOT"

# Check if virtual environment exists and activate it
# Adjust the path to your virtual environment if it's different (e.g., venv, .venv, etc.)
ACTIVATE_VENV=false
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
    ACTIVATE_VENV=true
elif [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
    ACTIVATE_VENV=true
else
    echo "Warning: No virtual environment (.venv or venv) found."
    echo "Attempting to create one and install dependencies."
    python3 -m venv .venv
    if [ $? -eq 0 ]; then
        echo "Virtual environment .venv created."
        source .venv/bin/activate
        ACTIVATE_VENV=true
    else
        echo "Error: Failed to create virtual environment. Please create one manually."
        exit 1
    fi
fi

# Install/update dependencies if requirements.txt exists and venv was activated
if [ "$ACTIVATE_VENV" = true ] && [ -f "backend/requirements.txt" ]; then
    echo "Installing/updating dependencies from backend/requirements.txt..."
    pip install -r backend/requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies from backend/requirements.txt."
        # Deactivate if we activated it
        if [ "$ACTIVATE_VENV" = true ] && [ -n "$VIRTUAL_ENV" ]; then
            deactivate
        fi
        exit 1
    fi
elif [ ! -f "backend/requirements.txt" ]; then
    echo "Warning: backend/requirements.txt not found. Skipping dependency installation."
fi

# Install MCP dependencies if mcp/requirements.txt exists and venv was activated
if [ "$ACTIVATE_VENV" = true ] && [ -f "mcp/requirements.txt" ]; then
    echo "Installing/updating dependencies from mcp/requirements.txt..."
    pip install -r mcp/requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies from mcp/requirements.txt."
        # Deactivate if we activated it
        if [ "$ACTIVATE_VENV" = true ] && [ -n "$VIRTUAL_ENV" ]; then
            deactivate
        fi
        exit 1
    fi
elif [ ! -f "mcp/requirements.txt" ]; then
    echo "Warning: mcp/requirements.txt not found. Skipping MCP dependency installation."
fi

# Set PYTHONPATH to include the project root
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Run backend tests
echo "Running backend tests..."
pytest -v tests/backend/

# Run MCP tests
echo "Running MCP tests..."
pytest -v tests/mcp/

# Run frontend tests
cd frontend
npm install
npm test -- --watchAll=false --passWithNoTests
cd ..

# Deactivate virtual environment if it was activated by this script
if [ "$ACTIVATE_VENV" = true ] && [ -n "$VIRTUAL_ENV" ]; then
    echo "Deactivating virtual environment..."
    deactivate
fi

echo "Test run complete."
