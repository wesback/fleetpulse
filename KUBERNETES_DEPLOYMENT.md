# FleetPulse Kubernetes Deployment Guide

This guide explains how to deploy FleetPulse on Kubernetes with configurable backend URLs.

## Overview

FleetPulse now supports configurable backend URLs, making it seamless to deploy on Kubernetes where services are addressed differently than in Docker Compose.

## Key Features

- **Runtime Configuration**: Backend URL is configured at container startup, not build time
- **No Rebuild Required**: Change backend URL by setting environment variables
- **Kubernetes Native**: Works seamlessly with Kubernetes services and ingress
- **Backward Compatible**: Defaults to `/api` for nginx proxy mode

## Configuration

### Environment Variables

#### Frontend Container

| Variable | Default | Description |
|----------|---------|-------------|
| `REACT_APP_BACKEND_URL` | `/api` | Backend API base URL |

**Examples:**
- Docker Compose with nginx proxy: `/api` (default)
- Kubernetes internal service: `http://fleetpulse-backend:8000/api`
- External backend: `https://api.example.com/api`
- Kubernetes with ingress: `/api` (if both services behind same ingress)

## Kubernetes Deployment Examples

### Example 1: Internal Services (Recommended)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: fleetpulse-backend
spec:
  selector:
    app: fleetpulse-backend
  ports:
    - port: 8000
      targetPort: 8000
---
apiVersion: v1
kind: Service
metadata:
  name: fleetpulse-frontend
spec:
  selector:
    app: fleetpulse-frontend
  ports:
    - port: 80
      targetPort: 80
  type: LoadBalancer
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fleetpulse-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: fleetpulse-backend
  template:
    metadata:
      labels:
        app: fleetpulse-backend
    spec:
      containers:
      - name: backend
        image: wesback/fleetpulse-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: FLEETPULSE_DATA_DIR
          value: /data
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: fleetpulse-data-pvc
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fleetpulse-frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: fleetpulse-frontend
  template:
    metadata:
      labels:
        app: fleetpulse-frontend
    spec:
      containers:
      - name: frontend
        image: wesback/fleetpulse-frontend:latest
        ports:
        - containerPort: 80
        env:
        # Configure frontend to use backend service
        - name: REACT_APP_BACKEND_URL
          value: http://fleetpulse-backend:8000/api
```

### Example 2: With Ingress (Single Domain)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fleetpulse-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2
spec:
  rules:
  - host: fleetpulse.example.com
    http:
      paths:
      - path: /api(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: fleetpulse-backend
            port:
              number: 8000
      - path: /()(.*)
        pathType: Prefix
        backend:
          service:
            name: fleetpulse-frontend
            port:
              number: 80
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fleetpulse-frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: fleetpulse-frontend
  template:
    metadata:
      labels:
        app: fleetpulse-frontend
    spec:
      containers:
      - name: frontend
        image: wesback/fleetpulse-frontend:latest
        ports:
        - containerPort: 80
        env:
        # Use relative path since both are behind same ingress
        - name: REACT_APP_BACKEND_URL
          value: /api
```

### Example 3: Separate Domains

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fleetpulse-backend-ingress
spec:
  rules:
  - host: api.fleetpulse.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: fleetpulse-backend
            port:
              number: 8000
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fleetpulse-frontend-ingress
spec:
  rules:
  - host: fleetpulse.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: fleetpulse-frontend
            port:
              number: 80
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fleetpulse-frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: fleetpulse-frontend
  template:
    metadata:
      labels:
        app: fleetpulse-frontend
    spec:
      containers:
      - name: frontend
        image: wesback/fleetpulse-frontend:latest
        ports:
        - containerPort: 80
        env:
        # Use full backend domain
        - name: REACT_APP_BACKEND_URL
          value: https://api.fleetpulse.example.com/api
```

## Helm Chart Example

```yaml
# values.yaml
backend:
  replicaCount: 2
  image:
    repository: wesback/fleetpulse-backend
    tag: latest
  service:
    type: ClusterIP
    port: 8000

frontend:
  replicaCount: 2
  image:
    repository: wesback/fleetpulse-frontend
    tag: latest
  service:
    type: LoadBalancer
    port: 80
  config:
    # Backend URL configuration
    backendUrl: http://{{ .Release.Name }}-backend:8000/api

ingress:
  enabled: true
  className: nginx
  host: fleetpulse.example.com
```

## Docker Compose (for comparison)

```yaml
services:
  backend:
    image: wesback/fleetpulse-backend:latest
    ports:
      - "8000:8000"
    
  frontend:
    image: wesback/fleetpulse-frontend:latest
    ports:
      - "8080:80"
    environment:
      # Use nginx proxy (default)
      - REACT_APP_BACKEND_URL=/api
      # Or direct connection
      # - REACT_APP_BACKEND_URL=http://backend:8000/api
```

## ConfigMap Approach (Alternative)

You can also use ConfigMaps to manage the configuration:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fleetpulse-frontend-config
data:
  REACT_APP_BACKEND_URL: "http://fleetpulse-backend:8000/api"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fleetpulse-frontend
spec:
  template:
    spec:
      containers:
      - name: frontend
        image: wesback/fleetpulse-frontend:latest
        envFrom:
        - configMapRef:
            name: fleetpulse-frontend-config
```

## Verification

After deployment, verify the configuration:

```bash
# Check frontend pod logs
kubectl logs -l app=fleetpulse-frontend

# You should see:
# Generating frontend configuration...
# Backend URL: http://fleetpulse-backend:8000/api
# Configuration generated successfully

# Exec into frontend pod to verify
kubectl exec -it deployment/fleetpulse-frontend -- cat /usr/share/nginx/html/config.js

# You should see:
# window.FLEETPULSE_CONFIG = {
#   API_BASE_URL: 'http://fleetpulse-backend:8000/api'
# };
```

## Troubleshooting

### Frontend can't connect to backend

1. **Check backend URL configuration:**
   ```bash
   kubectl get deployment fleetpulse-frontend -o yaml | grep REACT_APP_BACKEND_URL
   ```

2. **Verify backend service is accessible:**
   ```bash
   kubectl exec -it deployment/fleetpulse-frontend -- curl http://fleetpulse-backend:8000/health
   ```

3. **Check frontend config.js:**
   ```bash
   kubectl exec -it deployment/fleetpulse-frontend -- cat /usr/share/nginx/html/config.js
   ```

### CORS Issues

If the backend URL is external, ensure CORS is configured on the backend:

```yaml
# Backend deployment
env:
- name: ALLOWED_ORIGINS
  value: https://fleetpulse.example.com
```

## Migration from Previous Versions

If you're upgrading from a version without configurable backend URLs:

1. **No code changes needed** - defaults to `/api` (backward compatible)
2. **To use direct backend access**, add environment variable:
   ```yaml
   env:
   - name: REACT_APP_BACKEND_URL
     value: http://fleetpulse-backend:8000/api
   ```
3. **Rebuild images if using custom builds** - pull latest images for pre-built deployments

## Best Practices

1. **Use internal service names** when possible (e.g., `http://fleetpulse-backend:8000/api`)
2. **Use ConfigMaps** for environment-specific configuration
3. **Use Secrets** for sensitive configuration (API keys, tokens)
4. **Enable CORS** only for specific origins in production
5. **Use HTTPS** with proper TLS certificates for external access
6. **Implement health checks** and readiness probes
7. **Set resource limits** for pods
8. **Use persistent volumes** for backend data storage

## Additional Resources

- [FleetPulse Docker Documentation](./DOCKER_DEPLOYMENT.md)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kubernetes Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)
