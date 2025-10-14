# Database Configuration Guide

FleetPulse supports both SQLite and PostgreSQL databases with seamless switching between them via environment variables.

## Table of Contents
- [Quick Start](#quick-start)
- [Database Types](#database-types)
- [Configuration](#configuration)
- [Docker Compose Setup](#docker-compose-setup)
- [Kubernetes/K3s Setup](#kubernetesk3s-setup)
- [Migration Guide](#migration-guide)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Using SQLite (Default)
No configuration needed! FleetPulse uses SQLite by default:

```bash
docker compose up -d
```

### Using PostgreSQL
Use the PostgreSQL-specific compose file:

```bash
docker compose -f docker-compose.postgres.yml up -d
```

Or configure environment variables in `.env`:

```bash
DATABASE_TYPE=postgresql
POSTGRES_HOST=postgres
POSTGRES_PASSWORD=your-secure-password
```

## Database Types

### SQLite
- **Best for**: Single-node deployments, development, small to medium workloads
- **Pros**: Zero configuration, file-based, no separate database server needed
- **Cons**: Limited concurrent write performance, not suitable for distributed deployments
- **Default**: Yes

### PostgreSQL
- **Best for**: Production deployments, high availability, distributed systems
- **Pros**: Excellent concurrent performance, ACID compliant, industry standard
- **Cons**: Requires separate database server, more complex setup
- **Default**: No

## Configuration

### Environment Variables

#### Database Type Selection
```bash
# Choose database type: "sqlite" or "postgresql"
DATABASE_TYPE=sqlite  # Default
```

#### SQLite Configuration
```bash
# Data directory for SQLite database file
FLEETPULSE_DATA_DIR=./data  # Default
```

#### PostgreSQL Configuration
```bash
# PostgreSQL connection parameters
POSTGRES_HOST=localhost      # Default
POSTGRES_PORT=5432          # Default
POSTGRES_DB=fleetpulse      # Default
POSTGRES_USER=fleetpulse    # Default
POSTGRES_PASSWORD=fleetpulse # Default (CHANGE IN PRODUCTION!)
POSTGRES_SSLMODE=prefer     # Default (options: disable, allow, prefer, require, verify-ca, verify-full)
```

#### Advanced: Direct Database URL
Override all individual parameters with a single connection string:

```bash
# For SQLite
DATABASE_URL=sqlite:///path/to/database.db

# For PostgreSQL
DATABASE_URL=postgresql://user:password@host:port/dbname?sslmode=prefer
```

#### Connection Pool Settings (PostgreSQL only)
```bash
DB_POOL_SIZE=5        # Default: 5 connections
DB_MAX_OVERFLOW=10    # Default: 10 overflow connections
```

## Docker Compose Setup

### Option 1: SQLite (Default)
The default `docker-compose.yml` uses SQLite:

```bash
docker compose up -d
```

### Option 2: PostgreSQL (Recommended Method)
Use the provided PostgreSQL configuration:

```bash
# Using the PostgreSQL-specific compose file
docker compose -f docker-compose.postgres.yml up -d

# Or with both default and postgres config
docker compose -f docker-compose.yml -f docker-compose.postgres.yml up -d
```

### Option 3: Enable PostgreSQL in Default Compose File
Edit `docker-compose.yml` and uncomment the PostgreSQL service and related configuration:

```yaml
# 1. Uncomment the postgres service section
services:
  postgres:
    image: postgres:16-alpine
    container_name: fleetpulse-postgres
    environment:
      - POSTGRES_DB=fleetpulse
      - POSTGRES_USER=fleetpulse
      - POSTGRES_PASSWORD=fleetpulse  # CHANGE IN PRODUCTION!
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - fleetpulse
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U fleetpulse"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    environment:
      # 2. Change DATABASE_TYPE
      - DATABASE_TYPE=postgresql
      # 3. Uncomment PostgreSQL configuration
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=fleetpulse
      - POSTGRES_USER=fleetpulse
      - POSTGRES_PASSWORD=fleetpulse
    depends_on:
      # 4. Uncomment postgres dependency
      - postgres

# 5. Uncomment volumes section
volumes:
  postgres-data:
```

### Environment File Configuration
Create a `.env` file with your database configuration:

```bash
# For SQLite (default)
DATABASE_TYPE=sqlite
FLEETPULSE_DATA_PATH=./data

# For PostgreSQL
DATABASE_TYPE=postgresql
POSTGRES_HOST=postgres
POSTGRES_DB=fleetpulse
POSTGRES_USER=fleetpulse
POSTGRES_PASSWORD=your-secure-password
```

## Kubernetes/K3s Setup

### Using SQLite (Default)
Deploy the standard manifests:

```bash
kubectl apply -f k3s-deployment.yaml
```

### Using PostgreSQL

#### Step 1: Deploy PostgreSQL
First, deploy the PostgreSQL StatefulSet:

```bash
kubectl apply -f k3s-postgres.yaml
```

This creates:
- PostgreSQL StatefulSet with persistent storage
- PostgreSQL Service
- ConfigMap with connection details
- Secret with credentials (⚠️ Update password in production!)
- PersistentVolumeClaim for data

#### Step 2: Update Backend Configuration
Edit `k3s-deployment.yaml` and update the backend deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fleetpulse-backend
  namespace: fleetpulse
spec:
  template:
    spec:
      containers:
      - name: backend
        env:
        # Change DATABASE_TYPE
        - name: DATABASE_TYPE
          value: postgresql
        # Uncomment PostgreSQL configuration
        - name: POSTGRES_HOST
          valueFrom:
            configMapKeyRef:
              name: fleetpulse-postgres-config
              key: POSTGRES_HOST
        - name: POSTGRES_PORT
          valueFrom:
            configMapKeyRef:
              name: fleetpulse-postgres-config
              key: POSTGRES_PORT
        - name: POSTGRES_DB
          valueFrom:
            secretKeyRef:
              name: fleetpulse-postgres-secret
              key: POSTGRES_DB
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: fleetpulse-postgres-secret
              key: POSTGRES_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: fleetpulse-postgres-secret
              key: POSTGRES_PASSWORD
        # Comment out FLEETPULSE_DATA_DIR (not needed for PostgreSQL)
        # - name: FLEETPULSE_DATA_DIR
        #   value: /data
```

#### Step 3: Deploy Updated Backend
```bash
kubectl apply -f k3s-deployment.yaml
```

#### Production Security Best Practices
Update the PostgreSQL password before deployment:

```bash
# Create a secure password
kubectl create secret generic fleetpulse-postgres-secret \
  --from-literal=POSTGRES_DB=fleetpulse \
  --from-literal=POSTGRES_USER=fleetpulse \
  --from-literal=POSTGRES_PASSWORD=$(openssl rand -base64 32) \
  -n fleetpulse --dry-run=client -o yaml | kubectl apply -f -
```

### External PostgreSQL Database
To use an external PostgreSQL instance (e.g., AWS RDS, Azure Database, Google Cloud SQL):

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fleetpulse-postgres-config
  namespace: fleetpulse
data:
  POSTGRES_HOST: your-external-db-host.region.rds.amazonaws.com
  POSTGRES_PORT: "5432"
---
apiVersion: v1
kind: Secret
metadata:
  name: fleetpulse-postgres-secret
  namespace: fleetpulse
type: Opaque
stringData:
  POSTGRES_DB: fleetpulse
  POSTGRES_USER: fleetpulse_user
  POSTGRES_PASSWORD: your-secure-password
```

## Migration Guide

### Migrating from SQLite to PostgreSQL

#### For Docker Compose

1. **Export SQLite data** (if you have existing data):
   ```bash
   docker compose exec backend sqlite3 /data/updates.db .dump > backup.sql
   ```

2. **Stop the application**:
   ```bash
   docker compose down
   ```

3. **Switch to PostgreSQL**:
   ```bash
   docker compose -f docker-compose.postgres.yml up -d
   ```

4. **Import data** (if needed):
   ```bash
   # This requires manual conversion as SQLite and PostgreSQL SQL dialects differ
   # For production migrations, consider using a migration tool
   ```

#### For Kubernetes

1. **Create PostgreSQL deployment**:
   ```bash
   kubectl apply -f k3s-postgres.yaml
   ```

2. **Wait for PostgreSQL to be ready**:
   ```bash
   kubectl wait --for=condition=ready pod -l app=fleetpulse-postgres -n fleetpulse --timeout=120s
   ```

3. **Update backend configuration** (see Kubernetes setup above)

4. **Deploy updated backend**:
   ```bash
   kubectl apply -f k3s-deployment.yaml
   ```

### Data Migration Tools
For production migrations with existing data, consider:
- **pg_loader**: Migrates SQLite to PostgreSQL
- **Alembic**: Database migration framework (future enhancement)
- Manual SQL conversion and import

## Troubleshooting

### Connection Issues

#### SQLite
**Problem**: "Cannot write to database directory"
```bash
# Solution: Check directory permissions
ls -la ./data
chmod 755 ./data
```

**Problem**: "Database locked"
```bash
# Solution: Ensure only one process accesses SQLite
# Consider switching to PostgreSQL for concurrent access
```

#### PostgreSQL
**Problem**: "could not translate host name to address"
```bash
# Solution: Check POSTGRES_HOST is correct
echo $POSTGRES_HOST
# For Docker Compose: should be "postgres"
# For Kubernetes: should be "fleetpulse-postgres"
```

**Problem**: "password authentication failed"
```bash
# Solution: Verify credentials
docker compose exec postgres psql -U fleetpulse -d fleetpulse
# Or check Kubernetes secret:
kubectl get secret fleetpulse-postgres-secret -n fleetpulse -o yaml
```

**Problem**: "Connection refused"
```bash
# Solution: Check if PostgreSQL is running
docker compose ps postgres
# Or for Kubernetes:
kubectl get pods -n fleetpulse -l app=fleetpulse-postgres
```

### Health Check
Verify database connection:

```bash
# Check health endpoint
curl http://localhost:8000/health

# Should return:
{
  "status": "healthy",
  "database": {
    "type": "sqlite",  # or "postgresql"
    "status": "connected"
  },
  "telemetry": {...}
}
```

### Enable SQL Debugging
Set environment variable for detailed SQL logging:

```yaml
environment:
  - SQLALCHEMY_ECHO=true
```

### Check Database Logs

#### Docker Compose
```bash
# Backend logs
docker compose logs -f backend

# PostgreSQL logs
docker compose logs -f postgres
```

#### Kubernetes
```bash
# Backend logs
kubectl logs -f -l app=fleetpulse-backend -n fleetpulse

# PostgreSQL logs
kubectl logs -f -l app=fleetpulse-postgres -n fleetpulse
```

## Performance Tuning

### SQLite
```bash
# Increase cache size for better read performance
# SQLite automatically optimized by SQLAlchemy
```

### PostgreSQL
```bash
# Adjust connection pool
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# For high-traffic deployments, scale backend replicas
# Kubernetes:
kubectl scale deployment fleetpulse-backend --replicas=5 -n fleetpulse
```

## Security Best Practices

1. **Always change default passwords** in production
2. **Use SSL/TLS** for PostgreSQL connections:
   ```bash
   POSTGRES_SSLMODE=require
   ```
3. **Restrict PostgreSQL network access**:
   - Docker: Use internal networks only
   - Kubernetes: Use Network Policies
4. **Use secrets management**:
   - Kubernetes Secrets
   - External secret managers (AWS Secrets Manager, HashiCorp Vault)
5. **Regular backups**:
   - SQLite: Copy database file
   - PostgreSQL: Use pg_dump or continuous archiving

## Support

For issues or questions:
- GitHub Issues: https://github.com/wesback/fleetpulse/issues
- Documentation: https://github.com/wesback/fleetpulse
