# FleetPulse Service DNS Reference

## Docker Compose vs Kubernetes

### How DNS Works

**Docker Compose:**
- Services communicate using simple service names defined in `docker-compose.yml`
- Docker's embedded DNS server (127.0.0.11) resolves service names
- All services on the same network can reach each other
- Example: `backend`, `jaeger`, `otel-collector`

**Kubernetes (K3s):**
- Services communicate using Kubernetes DNS
- DNS format: `<service-name>.<namespace>.svc.cluster.local`
- CoreDNS (usually at 10.43.0.10 in K3s) resolves service names
- Short names work within the same namespace
- FQDNs work across namespaces

### Service Endpoints

| Service | Docker Compose | Kubernetes Short Name | Kubernetes FQDN |
|---------|---------------|----------------------|-----------------|
| Backend API | `http://backend:8000` | `http://fleetpulse-backend:8000` | `http://fleetpulse-backend.fleetpulse.svc.cluster.local:8000` |
| Frontend | `http://frontend:80` | `http://fleetpulse-frontend:80` | `http://fleetpulse-frontend.fleetpulse.svc.cluster.local:80` |
| Jaeger Collector | `http://jaeger:14268/api/traces` | `http://fleetpulse-jaeger:14268/api/traces` | `http://fleetpulse-jaeger.fleetpulse.svc.cluster.local:14268/api/traces` |
| Jaeger Agent | `jaeger:6831` | `fleetpulse-jaeger:6831` | `fleetpulse-jaeger.fleetpulse.svc.cluster.local:6831` |
| Jaeger UI | `http://jaeger:16686` | `http://fleetpulse-jaeger:16686` | `http://fleetpulse-jaeger.fleetpulse.svc.cluster.local:16686` |
| OTEL Collector (gRPC) | `http://otel-collector:4317` | `http://fleetpulse-otel-collector:4317` | `http://fleetpulse-otel-collector.fleetpulse.svc.cluster.local:4317` |
| OTEL Collector (HTTP) | `http://otel-collector:4318` | `http://fleetpulse-otel-collector:4318` | `http://fleetpulse-otel-collector.fleetpulse.svc.cluster.local:4318` |
| MCP Server | `http://mcp:8001` | `http://fleetpulse-mcp:8001` | `http://fleetpulse-mcp.fleetpulse.svc.cluster.local:8001` |

### Environment Variables

#### Docker Compose (docker-compose.yml)

```yaml
environment:
  # Backend service references
  - OTEL_EXPORTER_JAEGER_ENDPOINT=http://jaeger:14268/api/traces
  - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
  - JAEGER_AGENT_HOST=jaeger
  - JAEGER_AGENT_PORT=6831
  
  # Frontend to Backend
  - REACT_APP_BACKEND_URL=/api  # Uses nginx proxy
```

#### Kubernetes (k3s-deployment.yaml)

```yaml
environment:
  # Backend service references (using FQDNs)
  - OTEL_EXPORTER_JAEGER_ENDPOINT=http://fleetpulse-jaeger.fleetpulse.svc.cluster.local:14268/api/traces
  - OTEL_EXPORTER_OTLP_ENDPOINT=http://fleetpulse-otel-collector.fleetpulse.svc.cluster.local:4317
  - JAEGER_AGENT_HOST=fleetpulse-jaeger.fleetpulse.svc.cluster.local
  - JAEGER_AGENT_PORT=6831
  
  # Frontend to Backend (direct service access, no proxy needed)
  - REACT_APP_BACKEND_URL=http://fleetpulse-backend:8000/api
```

### Backend Code Defaults

The backend code (`backend/telemetry.py`) has these defaults:

```python
"jaeger_endpoint": os.getenv("OTEL_EXPORTER_JAEGER_ENDPOINT", "http://jaeger:14268/api/traces"),
"otlp_endpoint": os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317"),
```

**These defaults work for Docker Compose but NOT for Kubernetes!** You must override them with environment variables in your K3s deployment.

## Why FQDNs in Kubernetes?

### Short Names (Same Namespace)
```yaml
value: http://fleetpulse-backend:8000/api
```
✅ Works within the same namespace (`fleetpulse`)  
✅ Simpler and easier to read  
⚠️ Can be ambiguous if DNS search paths change  

### Fully Qualified Domain Names (FQDNs)
```yaml
value: http://fleetpulse-backend.fleetpulse.svc.cluster.local:8000/api
```
✅ Works across namespaces  
✅ Explicit and unambiguous  
✅ Portable across clusters  
✅ Recommended for production  
⚠️ Longer and more verbose  

## Best Practices

1. **Same namespace, user-facing**: Use short names (e.g., frontend → backend)
   ```yaml
   - name: REACT_APP_BACKEND_URL
     value: http://fleetpulse-backend:8000/api
   ```

2. **Same namespace, telemetry/infrastructure**: Use FQDNs for clarity
   ```yaml
   - name: OTEL_EXPORTER_JAEGER_ENDPOINT
     value: http://fleetpulse-jaeger.fleetpulse.svc.cluster.local:14268/api/traces
   ```

3. **Cross-namespace**: Always use FQDNs
   ```yaml
   - name: DATABASE_URL
     value: postgresql://db.database-namespace.svc.cluster.local:5432/mydb
   ```

4. **External services**: Use external URLs
   ```yaml
   - name: EXTERNAL_API_URL
     value: https://api.example.com
   ```

## Troubleshooting DNS

### Test DNS Resolution

```bash
# From a pod
kubectl exec -n fleetpulse -it <pod-name> -- nslookup fleetpulse-backend

# Expected output:
# Server:    10.43.0.10
# Address 1: 10.43.0.10 kube-dns.kube-system.svc.cluster.local
# 
# Name:      fleetpulse-backend
# Address 1: 10.43.XXX.XXX fleetpulse-backend.fleetpulse.svc.cluster.local
```

### Check DNS Configuration

```bash
# View CoreDNS config
kubectl get configmap -n kube-system coredns -o yaml

# Check CoreDNS pods
kubectl get pods -n kube-system -l k8s-app=kube-dns
```

### Common DNS Issues

1. **Service not found**: Service doesn't exist or wrong namespace
   ```bash
   kubectl get svc -n fleetpulse
   ```

2. **No endpoints**: Service exists but no pods backing it
   ```bash
   kubectl get endpoints -n fleetpulse fleetpulse-backend
   ```

3. **Wrong port**: Service port vs container port mismatch
   ```bash
   kubectl describe svc -n fleetpulse fleetpulse-backend
   ```

## Summary

- **Docker Compose**: Simple names work because of Docker's embedded DNS
- **Kubernetes**: Use service names (short or FQDN) because of CoreDNS
- **The deployment uses FQDNs for telemetry endpoints** to be explicit and portable
- **Frontend uses short name** for backend because both are in the same namespace
- **Always override default values** in backend code when deploying to Kubernetes
