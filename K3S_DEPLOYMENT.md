# FleetPulse K3s Deployment Guide

## Overview

This guide covers deploying FleetPulse on Kubernetes (K3s). The key differences from Docker Compose are:

- **Service DNS**: Use FQDNs instead of simple hostnames
- **No Nginx proxy needed**: Frontend talks directly to backend service
- **Storage**: Need to configure proper PersistentVolumes
- **Networking**: Uses Kubernetes Services and optional Ingress

## Docker Compose vs Kubernetes Service Names

| Component | Docker Compose | Kubernetes (K3s) |
|-----------|---------------|------------------|
| Backend | `backend:8000` | `fleetpulse-backend:8000` or `fleetpulse-backend.fleetpulse.svc.cluster.local:8000` |
| Frontend | `frontend:80` | `fleetpulse-frontend:80` |
| Jaeger | `jaeger:14268` | `fleetpulse-jaeger.fleetpulse.svc.cluster.local:14268` |
| OTEL Collector | `otel-collector:4317` | `fleetpulse-otel-collector.fleetpulse.svc.cluster.local:4317` |
| MCP | `mcp:8001` | `fleetpulse-mcp:8001` |

**Format:** `<service-name>.<namespace>.svc.cluster.local:<port>`

## Quick Start

### 1. Apply the Kubernetes manifests

```bash
kubectl apply -f k3s-deployment.yaml
```

### 2. Check deployment status

```bash
# Check all resources
kubectl get all -n fleetpulse

# Check pods
kubectl get pods -n fleetpulse

# Check services
kubectl get svc -n fleetpulse
```

### 3. Access the application

```bash
# Get the LoadBalancer IP/Port
kubectl get svc fleetpulse-frontend -n fleetpulse

# If using NodePort or you want to port-forward:
kubectl port-forward -n fleetpulse svc/fleetpulse-frontend 8080:80
```

Then access: http://localhost:8080

## Important Notes for K3s

### DNS Resolution

**The Nginx proxy is NOT needed in K3s!** The frontend is configured to talk directly to the backend service using:

```yaml
env:
- name: REACT_APP_BACKEND_URL
  value: http://fleetpulse-backend:8000/api
```

This works because:
- Both pods are in the same namespace
- Kubernetes DNS automatically resolves service names
- No need for runtime DNS resolution in Nginx

### Service Names and DNS

In Kubernetes, services can be accessed using different DNS formats:

1. **Short name** (same namespace): `fleetpulse-backend` ✅
2. **FQDN** (explicit): `fleetpulse-backend.fleetpulse.svc.cluster.local` ✅
3. **Cross-namespace**: `service-name.namespace.svc.cluster.local` ✅

The deployment uses **FQDNs** for Jaeger and OTEL Collector to ensure compatibility:

```yaml
# Backend environment variables
- name: OTEL_EXPORTER_JAEGER_ENDPOINT
  value: http://fleetpulse-jaeger.fleetpulse.svc.cluster.local:14268/api/traces
- name: JAEGER_AGENT_HOST
  value: fleetpulse-jaeger.fleetpulse.svc.cluster.local
```

**Why FQDNs?**
- More explicit and portable
- Works across namespaces
- Avoids DNS search path issues
- Matches Kubernetes best practices

**Note:** In the same namespace, short names like `fleetpulse-backend` work fine, but FQDNs are more explicit and recommended for telemetry endpoints.

### Storage

The deployment uses a `ReadWriteMany` PersistentVolumeClaim. K3s defaults to `local-path` storage which only supports `ReadWriteOnce`. You have two options:

**Option 1: Single replica backend (ReadWriteOnce)**
```bash
# Edit k3s-deployment.yaml and change:
# 1. PVC accessModes to ReadWriteOnce
# 2. Backend replicas to 1
```

**Option 2: Use NFS or other RWX storage**
```bash
# Install NFS provisioner or use another storage class that supports RWX
```

### Service Types

- **Frontend**: `LoadBalancer` - K3s will expose this with a NodePort by default
- **Backend, Jaeger, MCP**: `ClusterIP` - Internal only

To expose Jaeger UI:
```bash
kubectl port-forward -n fleetpulse svc/fleetpulse-jaeger 16686:16686
```

## Troubleshooting

### Check pod logs

```bash
# Backend logs
kubectl logs -n fleetpulse -l app=fleetpulse-backend --tail=50

# Frontend logs
kubectl logs -n fleetpulse -l app=fleetpulse-frontend --tail=50
```

### DNS issues

If you still see DNS resolution errors in the frontend nginx:

1. Check if backend service is running:
```bash
kubectl get svc -n fleetpulse fleetpulse-backend
kubectl get endpoints -n fleetpulse fleetpulse-backend
```

2. Test DNS from frontend pod:
```bash
kubectl exec -n fleetpulse -it <frontend-pod-name> -- nslookup fleetpulse-backend
```

3. Verify the environment variable:
```bash
kubectl exec -n fleetpulse -it <frontend-pod-name> -- env | grep REACT_APP_BACKEND_URL
```

### Backend not resolving

The original error was because Nginx in the frontend tried to resolve "backend" at startup. The solution:

1. **Primary fix**: Use `REACT_APP_BACKEND_URL=http://fleetpulse-backend:8000/api` to bypass Nginx proxy entirely
2. **Secondary fix**: Updated nginx.conf to use runtime DNS resolution with K3s DNS (10.43.0.10)

### Jaeger/OTEL Collector not connecting

If telemetry is not working:

1. **Verify Jaeger is running**:
```bash
kubectl get pods -n fleetpulse -l app=fleetpulse-jaeger
kubectl logs -n fleetpulse -l app=fleetpulse-jaeger
```

2. **Test connectivity from backend pod**:
```bash
# Get backend pod name
kubectl get pods -n fleetpulse -l app=fleetpulse-backend

# Test DNS resolution
kubectl exec -n fleetpulse -it <backend-pod-name> -- nslookup fleetpulse-jaeger.fleetpulse.svc.cluster.local

# Test HTTP connectivity
kubectl exec -n fleetpulse -it <backend-pod-name> -- curl -v http://fleetpulse-jaeger.fleetpulse.svc.cluster.local:14268/api/traces
```

3. **Check environment variables**:
```bash
kubectl exec -n fleetpulse -it <backend-pod-name> -- env | grep -E "OTEL|JAEGER"
```

4. **Verify service endpoints**:
```bash
kubectl get endpoints -n fleetpulse fleetpulse-jaeger
kubectl get endpoints -n fleetpulse fleetpulse-otel-collector
```

## Configuration Options

### Using Ingress (Recommended for Production)

If you want to expose both frontend and backend through a single domain:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fleetpulse-ingress
  namespace: fleetpulse
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: web
spec:
  rules:
  - host: fleetpulse.local  # Change to your domain
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: fleetpulse-backend
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: fleetpulse-frontend
            port:
              number: 80
```

Then update frontend to use relative path:
```yaml
- name: REACT_APP_BACKEND_URL
  value: /api
```

### Environment-specific Configuration

For different environments, you can use Kustomize or Helm:

```bash
# Development
kubectl apply -f k3s-deployment.yaml

# Production with ingress
kubectl apply -f k3s-deployment.yaml
kubectl apply -f k3s-ingress.yaml
```

## Scaling

```bash
# Scale backend
kubectl scale deployment -n fleetpulse fleetpulse-backend --replicas=3

# Scale frontend
kubectl scale deployment -n fleetpulse fleetpulse-frontend --replicas=3
```

## Cleanup

```bash
kubectl delete namespace fleetpulse
```

## Next Steps

1. Configure your data source (mount actual fleet data)
2. Set up ingress for production access
3. Configure persistent storage properly
4. Set up monitoring and alerts
5. Configure backup for the PVC
