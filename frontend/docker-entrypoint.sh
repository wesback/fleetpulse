#!/bin/sh
set -e

# Generate config.js with runtime configuration
# This allows the backend URL to be configured via environment variables
# without rebuilding the frontend

# Default to /api for backward compatibility (nginx proxy mode)
BACKEND_URL="${REACT_APP_BACKEND_URL:-/api}"

echo "Generating frontend configuration..."
echo "Backend URL: ${BACKEND_URL}"

cat > /usr/share/nginx/html/config.js << EOF
// Runtime configuration - generated at container startup
// This file is loaded before the React app initializes
window.FLEETPULSE_CONFIG = {
  API_BASE_URL: '${BACKEND_URL}'
};
EOF

echo "Configuration generated successfully"

# Start nginx
exec nginx -g 'daemon off;'
