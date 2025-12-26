# Local Development Docker Setup

This guide explains how to use the local development Docker configuration for the Residency Scheduler application.

## Overview

The local development setup (`docker-compose.local.yml`) is optimized for:

- **No Authentication Required**: Uses standard Docker Hub images (no `dhi.io` login needed)
- **Hot Reload**: Source code changes are immediately reflected without rebuilding
- **Exposed Ports**: All services accessible for debugging and testing
- **Simple Passwords**: Easy-to-remember credentials for local development
- **Full Stack**: Backend, frontend, database, Redis, Celery workers, and n8n

## Prerequisites

- Docker (20.10 or higher)
- Docker Compose (2.0 or higher)
- 8GB RAM minimum (for all services)
- Ports available: 3000, 5432, 5679, 6379, 8000

## Quick Start

### 1. First-Time Setup

The `.env.local` file is already created with development-friendly values:

```bash
# Verify .env.local exists
cat .env.local
```

### 2. Start All Services

```bash
# From the project root directory
docker-compose -f docker-compose.local.yml up --build
```

This will:
- Build Docker images using standard Python and Node images
- Start all services (backend, frontend, database, Redis, Celery, n8n)
- Run database migrations automatically
- Enable hot reload for code changes

### 3. Access the Application

Once all services are running (look for "Application startup complete" messages):

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | - |
| **Backend API** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **PostgreSQL** | localhost:5432 | User: `scheduler`<br>Password: `local_dev_password`<br>Database: `residency_scheduler` |
| **Redis** | localhost:6379 | Password: `local_dev_redis_pass` |
| **n8n** | http://localhost:5679 | User: `admin`<br>Password: `local_dev_n8n_password` |

### 4. Verify Everything is Running

```bash
# Check service status
docker-compose -f docker-compose.local.yml ps

# View logs (all services)
docker-compose -f docker-compose.local.yml logs -f

# View logs (specific service)
docker-compose -f docker-compose.local.yml logs -f backend
docker-compose -f docker-compose.local.yml logs -f frontend
docker-compose -f docker-compose.local.yml logs -f celery-worker
```

## Daily Development Workflow

### Starting Services

```bash
# Start all services
docker-compose -f docker-compose.local.yml up

# Start in background (detached mode)
docker-compose -f docker-compose.local.yml up -d

# Start specific services only
docker-compose -f docker-compose.local.yml up backend db redis
```

### Stopping Services

```bash
# Stop all services (keeps data)
docker-compose -f docker-compose.local.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker-compose.local.yml down -v

# Stop specific service
docker-compose -f docker-compose.local.yml stop backend
```

### Restarting After Code Changes

**No restart needed for most changes!** The services use hot reload:

- **Backend (Python)**: Changes to `.py` files auto-reload via uvicorn
- **Frontend (Next.js)**: Changes to `.tsx`, `.ts`, `.css` files auto-reload

**Restart required for**:
- Dependency changes (`requirements.txt`, `package.json`)
- Environment variable changes (`.env.local`)
- Docker configuration changes (`docker-compose.local.yml`, `Dockerfile.local`)

```bash
# Restart after dependency changes
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up --build
```

## Common Tasks

### Database Operations

#### Connect to PostgreSQL

```bash
# Using docker exec
docker-compose -f docker-compose.local.yml exec db psql -U scheduler -d residency_scheduler

# Using local PostgreSQL client (if installed)
psql -h localhost -U scheduler -d residency_scheduler
# Password: local_dev_password
```

#### Run Database Migrations

```bash
# Migrations run automatically on backend startup
# To run manually:
docker-compose -f docker-compose.local.yml exec backend alembic upgrade head

# Create new migration
docker-compose -f docker-compose.local.yml exec backend alembic revision --autogenerate -m "Description"

# Rollback one migration
docker-compose -f docker-compose.local.yml exec backend alembic downgrade -1
```

#### Reset Database

```bash
# Stop services and remove database volume
docker-compose -f docker-compose.local.yml down -v

# Start fresh (migrations will run automatically)
docker-compose -f docker-compose.local.yml up
```

### Redis Operations

```bash
# Connect to Redis CLI
docker-compose -f docker-compose.local.yml exec redis redis-cli -a local_dev_redis_pass

# Common Redis commands:
# KEYS *           - List all keys
# GET key_name     - Get value of a key
# FLUSHALL         - Clear all data (use with caution)
# MONITOR          - Watch all Redis commands in real-time
```

### Backend Development

```bash
# View backend logs
docker-compose -f docker-compose.local.yml logs -f backend

# Run tests inside container
docker-compose -f docker-compose.local.yml exec backend pytest

# Run tests with coverage
docker-compose -f docker-compose.local.yml exec backend pytest --cov=app --cov-report=html

# Access backend shell
docker-compose -f docker-compose.local.yml exec backend bash

# Run Python REPL with app context
docker-compose -f docker-compose.local.yml exec backend python
```

### Frontend Development

```bash
# View frontend logs
docker-compose -f docker-compose.local.yml logs -f frontend

# Install new npm package
docker-compose -f docker-compose.local.yml exec frontend npm install package-name

# Run linter
docker-compose -f docker-compose.local.yml exec frontend npm run lint

# Run type checking
docker-compose -f docker-compose.local.yml exec frontend npm run type-check

# Access frontend shell
docker-compose -f docker-compose.local.yml exec frontend sh
```

### Celery Operations

```bash
# View Celery worker logs
docker-compose -f docker-compose.local.yml logs -f celery-worker

# View Celery beat logs
docker-compose -f docker-compose.local.yml logs -f celery-beat

# Check Celery worker status
docker-compose -f docker-compose.local.yml exec celery-worker celery -A app.core.celery_app inspect active

# Purge all tasks from queue
docker-compose -f docker-compose.local.yml exec celery-worker celery -A app.core.celery_app purge
```

## Debugging

### Backend Debugging

The backend runs with `DEBUG=true` and verbose logging enabled.

#### View detailed logs:

```bash
docker-compose -f docker-compose.local.yml logs -f backend
```

#### Add breakpoints (pdb):

```python
# In your Python code
import pdb; pdb.set_trace()
```

Then attach to the container:

```bash
docker attach scheduler-local-backend
```

#### Remote debugging (VS Code / PyCharm):

Port 5678 is exposed for debugpy (if you configure it).

### Frontend Debugging

```bash
# View Next.js debug output
docker-compose -f docker-compose.local.yml logs -f frontend

# Disable Next.js caching (if issues)
docker-compose -f docker-compose.local.yml exec frontend rm -rf .next
docker-compose -f docker-compose.local.yml restart frontend
```

### Database Debugging

```bash
# Check active connections
docker-compose -f docker-compose.local.yml exec db psql -U scheduler -d residency_scheduler -c "SELECT * FROM pg_stat_activity;"

# View table structure
docker-compose -f docker-compose.local.yml exec db psql -U scheduler -d residency_scheduler -c "\d persons"

# Check recent migrations
docker-compose -f docker-compose.local.yml exec db psql -U scheduler -d residency_scheduler -c "SELECT * FROM alembic_version;"
```

## Troubleshooting

### Port Already in Use

```bash
# Find what's using the port (example for port 8000)
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or change the port in docker-compose.local.yml
```

### Services Not Starting

```bash
# Check Docker daemon is running
docker info

# View full error logs
docker-compose -f docker-compose.local.yml up

# Check for resource issues
docker system df
docker system prune  # Clean up unused resources
```

### Database Connection Issues

```bash
# Verify database is healthy
docker-compose -f docker-compose.local.yml ps db

# Check database logs
docker-compose -f docker-compose.local.yml logs db

# Recreate database
docker-compose -f docker-compose.local.yml down -v
docker-compose -f docker-compose.local.yml up db
```

### Hot Reload Not Working

```bash
# Verify volume mounts are correct
docker-compose -f docker-compose.local.yml config

# Restart the service
docker-compose -f docker-compose.local.yml restart backend

# Rebuild if needed
docker-compose -f docker-compose.local.yml up --build backend
```

### Celery Tasks Not Running

```bash
# Check worker is running
docker-compose -f docker-compose.local.yml ps celery-worker

# Check worker can ping
docker-compose -f docker-compose.local.yml exec celery-worker celery -A app.core.celery_app inspect ping

# Check Redis connection
docker-compose -f docker-compose.local.yml exec celery-worker celery -A app.core.celery_app inspect stats
```

## Performance Tips

### Speed Up Builds

```bash
# Use Docker build cache
docker-compose -f docker-compose.local.yml build --parallel

# Clean build cache if stale
docker builder prune
```

### Reduce Resource Usage

Edit `docker-compose.local.yml` to:
- Disable n8n if not needed (comment out the service)
- Reduce Redis maxmemory: `--maxmemory 128mb`
- Run fewer Celery workers

### Monitor Resource Usage

```bash
# View resource usage
docker stats

# View specific service
docker stats scheduler-local-backend
```

## Differences from Production

| Aspect | Local Development | Production |
|--------|-------------------|------------|
| **Images** | `python:3.12-slim`, `node:22-alpine` | `dhi.io/python:3.12`, `dhi.io/node:22` |
| **Security** | Simple passwords, exposed ports | Strong secrets, minimal exposure |
| **Build** | Single-stage | Multi-stage distroless |
| **User** | Root (easier volume permissions) | Non-root user |
| **Logging** | DEBUG level, verbose | INFO/WARNING level |
| **Hot Reload** | Enabled | Disabled |
| **Volume Mounts** | Source code mounted | No source mounts |
| **Health Checks** | Basic | Production-grade |

## Switching to Production Configuration

When ready for production:

```bash
# Use the production docker-compose.yml
docker-compose up --build

# Or with environment-specific overrides
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```

Make sure to:
1. Use `.env` with strong secrets (not `.env.local`)
2. Set `DEBUG=false`
3. Use proper CORS origins
4. Enable rate limiting
5. Use HTTPS
6. Review security settings

## Getting Help

- **Backend Issues**: Check `backend/README.md` and `docs/development/`
- **Frontend Issues**: Check `frontend/README.md`
- **Docker Issues**: Run `docker-compose -f docker-compose.local.yml config` to validate
- **Database Issues**: Check `docs/admin-manual/database.md`

## Additional Resources

- [CLAUDE.md](../../CLAUDE.md) - Project development guidelines
- [README.md](../../README.md) - Main project documentation
- [docs/](../) - Comprehensive documentation
- [.env.example](../../.env.example) - Production environment template

---

**Happy Coding!** 🚀

The local development environment is designed to make your development experience smooth and productive. If you encounter issues not covered here, please update this documentation.
