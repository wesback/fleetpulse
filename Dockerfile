# Multi-stage Dockerfile to build frontend and backend in a single container
# Stage 1: Build the React frontend
FROM node:24-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

# Stage 2: Build the Python backend with frontend assets
FROM python:3.13-slim AS backend

# Build arguments for user configuration
ARG USER_ID=1000
ARG GROUP_ID=1000

# Set environment variables for Python best practices
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./

# Copy built frontend assets from the previous stage
COPY --from=frontend-build /app/frontend/build ./static

# Create data directory with proper permissions
RUN mkdir -p /data && chmod 755 /data

# Create a non-root user with configurable UID/GID for better volume compatibility
RUN groupadd -g ${GROUP_ID} appuser && \
    useradd -u ${USER_ID} -g ${GROUP_ID} -M -s /bin/bash appuser && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /data
USER appuser

# Expose port 8000 for the combined service
EXPOSE 8000

# Use gunicorn with uvicorn workers for production
# Default to 2 workers for single-container deployment, configurable via GUNICORN_WORKERS
CMD ["sh", "-c", "gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-2}"]

# Add a healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl --fail http://localhost:8000/health || exit 1
