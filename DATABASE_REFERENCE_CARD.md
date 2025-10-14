# PostgreSQL Support - Quick Reference Card

## Configuration Cheat Sheet

### SQLite (Default)
```bash
# No configuration needed!
docker compose up -d
```

### PostgreSQL
```bash
# .env file
DATABASE_TYPE=postgresql
POSTGRES_HOST=postgres
POSTGRES_PASSWORD=your-password

# Deploy
docker compose -f docker-compose.postgres.yml up -d
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_TYPE` | `sqlite` | Database type: `sqlite` or `postgresql` |
| `DATABASE_URL` | (auto) | Override with direct connection string |
| `FLEETPULSE_DATA_DIR` | `./data` | SQLite data directory |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `fleetpulse` | PostgreSQL database name |
| `POSTGRES_USER` | `fleetpulse` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `fleetpulse` | PostgreSQL password (CHANGE!) |
| `POSTGRES_SSLMODE` | `prefer` | SSL mode: disable, prefer, require |
| `DB_POOL_SIZE` | `5` | PostgreSQL connection pool size |
| `DB_MAX_OVERFLOW` | `10` | PostgreSQL max overflow connections |

## Quick Commands

### Check Database Type
```bash
curl http://localhost:8000/health | jq '.database.type'
```

### Docker Compose Logs
```bash
# Backend logs
docker compose logs -f backend

# PostgreSQL logs
docker compose -f docker-compose.postgres.yml logs -f postgres
```

### Kubernetes Logs
```bash
# Backend logs
kubectl logs -f -l app=fleetpulse-backend -n fleetpulse

# PostgreSQL logs
kubectl logs -f -l app=fleetpulse-postgres -n fleetpulse
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't connect to PostgreSQL | Check `POSTGRES_HOST` and ensure PostgreSQL is running |
| Permission denied (SQLite) | Run `chmod 755 ./data` |
| Wrong database type | Check environment variables and restart |
| PostgreSQL password error | Verify `POSTGRES_PASSWORD` matches |

## Common Use Cases

### Development
```bash
# SQLite - fastest setup
docker compose up -d
```

### Production (Docker)
```bash
# PostgreSQL with secure password
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)" >> .env
docker compose -f docker-compose.postgres.yml up -d
```

### Production (Kubernetes)
```bash
# 1. Update password in k3s-postgres.yaml
# 2. Deploy
kubectl apply -f k3s-postgres.yaml
kubectl apply -f k3s-deployment.yaml
```

## Decision Matrix

| Criteria | SQLite | PostgreSQL |
|----------|--------|------------|
| Setup complexity | ⭐ Simple | ⭐⭐⭐ Moderate |
| Single node | ✅ Excellent | ✅ Good |
| High availability | ❌ No | ✅ Yes |
| Concurrent writes | ⚠️ Limited | ✅ Excellent |
| Production ready | ✅ Yes (< 100 hosts) | ✅ Yes (any scale) |
| Backup complexity | ⭐ Simple file | ⭐⭐ Requires tools |

## File Locations

### Configuration Files
- `.env` - Environment variables
- `.env.example` - Configuration examples
- `docker-compose.yml` - Default Docker Compose (SQLite)
- `docker-compose.postgres.yml` - PostgreSQL Docker Compose
- `k3s-deployment.yaml` - Kubernetes deployment
- `k3s-postgres.yaml` - PostgreSQL StatefulSet

### Documentation
- `README.md` - Main documentation
- `DATABASE_QUICKSTART.md` - Quick start guide
- `DATABASE_CONFIGURATION.md` - Complete guide
- `IMPLEMENTATION_SUMMARY_POSTGRESQL.md` - Implementation details

### Code
- `backend/utils/constants.py` - Database configuration
- `backend/db/engine.py` - Database engine
- `backend/routers/health.py` - Health endpoint

### Tests
- `tests/backend/test_database_config.py` - Unit tests
- `test_database_integration.sh` - Integration tests

## Connection String Examples

### SQLite
```
sqlite:///./data/updates.db
```

### PostgreSQL
```
postgresql://user:password@host:5432/database
postgresql://user:password@host:5432/database?sslmode=require
```

## Health Check Response

### SQLite
```json
{
  "status": "healthy",
  "database": {
    "type": "sqlite",
    "status": "connected"
  },
  "telemetry": {...}
}
```

### PostgreSQL
```json
{
  "status": "healthy",
  "database": {
    "type": "postgresql",
    "status": "connected"
  },
  "telemetry": {...}
}
```

## Support

📖 Documentation: [DATABASE_CONFIGURATION.md](DATABASE_CONFIGURATION.md)
🚀 Quick Start: [DATABASE_QUICKSTART.md](DATABASE_QUICKSTART.md)
🐛 Issues: https://github.com/wesback/fleetpulse/issues
