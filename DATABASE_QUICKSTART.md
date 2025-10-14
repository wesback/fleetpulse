# Quick Start: PostgreSQL vs SQLite

This guide helps you choose the right database for your FleetPulse deployment.

## TL;DR - Which Database Should I Use?

### Use SQLite (Default) if:
- ✅ Single-node deployment
- ✅ Development or testing
- ✅ Small to medium fleet (< 100 hosts)
- ✅ Want zero configuration
- ✅ Local development

**No configuration needed - just run:**
```bash
docker compose up -d
```

### Use PostgreSQL if:
- ✅ Production environment
- ✅ High availability required
- ✅ Large fleet (> 100 hosts)
- ✅ Multiple backend replicas
- ✅ Enterprise deployment

**Quick setup:**
```bash
docker compose -f docker-compose.postgres.yml up -d
```

## Quick Configuration Examples

### SQLite (Default)
```bash
# .env file - or just use defaults
DATABASE_TYPE=sqlite
FLEETPULSE_DATA_PATH=./data
```

### PostgreSQL (Docker Compose)
```bash
# .env file
DATABASE_TYPE=postgresql
POSTGRES_HOST=postgres
POSTGRES_PASSWORD=your-secure-password
```

### PostgreSQL (Kubernetes)
```bash
# Deploy PostgreSQL
kubectl apply -f k3s-postgres.yaml

# Update backend in k3s-deployment.yaml:
# - Set DATABASE_TYPE=postgresql
# - Uncomment PostgreSQL configuration

# Deploy application
kubectl apply -f k3s-deployment.yaml
```

## Environment Variables Reference

### SQLite
```bash
DATABASE_TYPE=sqlite              # Default
FLEETPULSE_DATA_DIR=./data       # Default
```

### PostgreSQL
```bash
DATABASE_TYPE=postgresql
POSTGRES_HOST=localhost           # Default
POSTGRES_PORT=5432               # Default
POSTGRES_DB=fleetpulse           # Default
POSTGRES_USER=fleetpulse         # Default
POSTGRES_PASSWORD=fleetpulse     # Change this!
POSTGRES_SSLMODE=prefer          # Default
```

### Advanced
```bash
# Direct connection string (overrides individual params)
DATABASE_URL=postgresql://user:pass@host:5432/db

# PostgreSQL connection pool
DB_POOL_SIZE=5                   # Default
DB_MAX_OVERFLOW=10               # Default
```

## Verification

Check which database is active:
```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "database": {
    "type": "sqlite",  // or "postgresql"
    "status": "connected"
  }
}
```

## Need More Details?

📖 See [DATABASE_CONFIGURATION.md](DATABASE_CONFIGURATION.md) for:
- Detailed configuration options
- Migration guides
- Troubleshooting
- Security best practices
- Performance tuning

## Common Use Cases

### Development
```bash
# SQLite - fastest setup
docker compose up -d
```

### Staging
```bash
# PostgreSQL for production-like environment
docker compose -f docker-compose.postgres.yml up -d
```

### Production (Docker)
```bash
# PostgreSQL with custom password
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)" >> .env
docker compose -f docker-compose.postgres.yml up -d
```

### Production (Kubernetes)
```bash
# 1. Update PostgreSQL password in k3s-postgres.yaml
# 2. Deploy PostgreSQL
kubectl apply -f k3s-postgres.yaml

# 3. Update backend configuration in k3s-deployment.yaml
# 4. Deploy application
kubectl apply -f k3s-deployment.yaml
```

## Switching Databases

### From SQLite to PostgreSQL

**Docker Compose:**
```bash
# Stop current deployment
docker compose down

# Start with PostgreSQL
docker compose -f docker-compose.postgres.yml up -d
```

**Kubernetes:**
```bash
# Deploy PostgreSQL
kubectl apply -f k3s-postgres.yaml

# Update backend deployment
# Edit k3s-deployment.yaml to set DATABASE_TYPE=postgresql
kubectl apply -f k3s-deployment.yaml
```

### From PostgreSQL to SQLite

**Docker Compose:**
```bash
# Stop current deployment
docker compose -f docker-compose.postgres.yml down

# Start with SQLite
docker compose up -d
```

**Kubernetes:**
```bash
# Update backend deployment
# Edit k3s-deployment.yaml to set DATABASE_TYPE=sqlite
kubectl apply -f k3s-deployment.yaml

# Optionally remove PostgreSQL
kubectl delete -f k3s-postgres.yaml
```

## Troubleshooting Quick Fixes

### Can't connect to database
```bash
# Check backend logs
docker compose logs backend
# or
kubectl logs -l app=fleetpulse-backend -n fleetpulse
```

### PostgreSQL not ready
```bash
# Check PostgreSQL status
docker compose ps postgres
# or
kubectl get pods -l app=fleetpulse-postgres -n fleetpulse

# Check PostgreSQL logs
docker compose logs postgres
# or
kubectl logs -l app=fleetpulse-postgres -n fleetpulse
```

### Permission denied (SQLite)
```bash
# Fix directory permissions
chmod 755 ./data
```

### Wrong database type
```bash
# Check health endpoint
curl http://localhost:8000/health | jq '.database.type'
```
