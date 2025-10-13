# Implementation Summary: Configurable Backend URL for FleetPulse Frontend

## Problem Statement
The FleetPulse frontend was using a hardcoded API base URL (`const API_BASE = '/api'`), which relied on nginx to proxy requests to the backend. This made it difficult to deploy on Kubernetes and other orchestration platforms where services might need to be addressed directly or through different routing mechanisms.

## Solution Overview
Implemented a runtime configuration system that allows the backend URL to be configured via environment variables at container startup, without requiring a rebuild of the frontend image.

## Implementation Details

### 1. Configuration System
Created a two-layer configuration system:

**Layer 1: Default Configuration (`frontend/public/config.js`)**
```javascript
window.FLEETPULSE_CONFIG = {
  API_BASE_URL: '/api'
};
```
This file is included in the build and provides the default configuration.

**Layer 2: Runtime Configuration Module (`frontend/src/config.js`)**
```javascript
const getConfig = () => {
  const defaultConfig = {
    API_BASE_URL: '/api'
  };
  
  if (window.FLEETPULSE_CONFIG) {
    return {
      ...defaultConfig,
      ...window.FLEETPULSE_CONFIG
    };
  }
  
  return defaultConfig;
};

export const config = getConfig();
```
This module reads the runtime configuration from the window object.

### 2. Dynamic Configuration Generation
Created an entrypoint script (`frontend/docker-entrypoint.sh`) that:
1. Reads the `REACT_APP_BACKEND_URL` environment variable
2. Generates `config.js` at container startup
3. Starts nginx

```bash
BACKEND_URL="${REACT_APP_BACKEND_URL:-/api}"
cat > /usr/share/nginx/html/config.js << EOF
window.FLEETPULSE_CONFIG = {
  API_BASE_URL: '${BACKEND_URL}'
};
EOF
exec nginx -g 'daemon off;'
```

### 3. Frontend Code Updates
Updated all React components to use the configuration:

**Before:**
```javascript
const API_BASE = '/api';
```

**After:**
```javascript
import config from './config';
const API_BASE = config.API_BASE_URL;
```

Files updated:
- `frontend/src/HostsPage.js`
- `frontend/src/StatisticsPage.js`
- `frontend/src/TodayUpdatesPage.js`

### 4. Docker Configuration
Updated `Dockerfile.frontend`:
- Added entrypoint script
- Modified to use `ENTRYPOINT` instead of `CMD`
- Fixed npm install to include devDependencies needed for build

Updated `docker-compose.yml` and `docker-compose.sample.yml`:
- Added `REACT_APP_BACKEND_URL` environment variable
- Provided documentation and examples

### 5. Documentation
Created comprehensive documentation:
- `KUBERNETES_DEPLOYMENT.md`: Complete Kubernetes deployment guide with examples
- Updated `README.md`: Added Kubernetes support section
- Updated `.env.example`: Documented the new configuration option

## Configuration Examples

### Docker Compose (Default - nginx proxy)
```yaml
environment:
  - REACT_APP_BACKEND_URL=/api  # or omit for default
```

### Kubernetes (Internal Service)
```yaml
env:
- name: REACT_APP_BACKEND_URL
  value: http://fleetpulse-backend:8000/api
```

### Kubernetes (With Ingress)
```yaml
env:
- name: REACT_APP_BACKEND_URL
  value: /api  # if both services behind same ingress
```

### External Backend
```yaml
env:
- name: REACT_APP_BACKEND_URL
  value: https://api.example.com/api
```

## Benefits

✅ **Runtime Configuration**: No rebuild required to change backend URL
✅ **Kubernetes Native**: Works seamlessly with Kubernetes services
✅ **Backward Compatible**: Defaults to `/api` for existing deployments
✅ **Environment Agnostic**: Works with Docker, Kubernetes, cloud platforms
✅ **Zero Downtime Changes**: Update backend URL by restarting pods with new env vars

## Testing

All changes have been tested:
- ✅ Frontend builds successfully (`npm run build`)
- ✅ Configuration files are included in build output
- ✅ Configuration logic tested with multiple scenarios
- ✅ Entrypoint script logic validated
- ✅ Default values work correctly
- ✅ Custom values override defaults properly

## Files Changed

| File | Changes |
|------|---------|
| `frontend/src/config.js` | New - Configuration loader |
| `frontend/public/config.js` | New - Default configuration |
| `frontend/public/index.html` | Modified - Load config.js |
| `frontend/docker-entrypoint.sh` | New - Generate config at runtime |
| `frontend/src/HostsPage.js` | Modified - Use config |
| `frontend/src/StatisticsPage.js` | Modified - Use config |
| `frontend/src/TodayUpdatesPage.js` | Modified - Use config |
| `Dockerfile.frontend` | Modified - Use entrypoint script |
| `docker-compose.yml` | Modified - Add env var |
| `docker-compose.sample.yml` | Modified - Add env var |
| `.env.example` | Modified - Document new option |
| `KUBERNETES_DEPLOYMENT.md` | New - Comprehensive K8s guide |
| `README.md` | Modified - Add K8s support section |

## Migration Guide

### For Existing Deployments
No changes required! The default configuration (`/api`) maintains backward compatibility with existing nginx proxy setups.

### For New Kubernetes Deployments
1. Deploy backend service
2. Deploy frontend with `REACT_APP_BACKEND_URL` environment variable pointing to backend service
3. No custom nginx configuration needed

### For External Backend
1. Set `REACT_APP_BACKEND_URL` to external backend URL
2. Ensure CORS is configured on the backend
3. Use HTTPS for production

## Technical Notes

### Why Runtime Configuration?
- Build-time configuration (e.g., using build args) requires rebuilding images for each environment
- Runtime configuration allows the same image to be deployed in different environments
- This is a best practice for cloud-native applications following the 12-factor app methodology

### Why Not Environment Variables in React?
- React's `process.env` variables are embedded at build time
- They cannot be changed at runtime without rebuilding
- Our solution generates configuration at container startup, providing true runtime configuration

### Security Considerations
- The backend URL is visible in the browser (this is acceptable as it's client-side configuration)
- Ensure CORS is properly configured on the backend
- Use HTTPS for external backends
- Consider using Kubernetes secrets for sensitive configuration (though backend URL is typically not sensitive)

## Future Enhancements

Potential future improvements:
- Add configuration for other frontend settings (e.g., feature flags)
- Support multiple backend URLs for different services
- Add configuration validation in the frontend
- Support dynamic reloading of configuration without page refresh

## References

- [12-Factor App: Config](https://12factor.net/config)
- [Kubernetes Configuration Best Practices](https://kubernetes.io/docs/concepts/configuration/)
- [Docker Environment Variables](https://docs.docker.com/compose/environment-variables/)

## Contact

For questions or issues related to this implementation, please refer to:
- [KUBERNETES_DEPLOYMENT.md](./KUBERNETES_DEPLOYMENT.md) for deployment examples
- [README.md](./README.md) for general FleetPulse documentation
- GitHub Issues for bug reports and feature requests
