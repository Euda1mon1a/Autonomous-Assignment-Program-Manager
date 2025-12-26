***REMOVED*** Local Development Docker Setup

This guide explains how to use the local development Docker configuration for the Residency Scheduler application.

***REMOVED******REMOVED*** Overview

The local development setup (`docker-compose.local.yml`) is optimized for:

- **No Authentication Required**: Uses standard Docker Hub images (no `dhi.io` login needed)
- **Hot Reload**: Source code changes are immediately reflected without rebuilding
- **Exposed Ports**: All services accessible for debugging and testing
- **Simple Passwords**: Easy-to-remember credentials for local development
- **Full Stack**: Backend, frontend, database, Redis, Celery workers, and n8n

***REMOVED******REMOVED*** Prerequisites

- Docker (20.10 or higher)
- Docker Compose (2.0 or higher)
- 8GB RAM minimum (for all services)
- Ports available: 3000, 5432, 5679, 6379, 8000

***REMOVED******REMOVED*** Quick Start

***REMOVED******REMOVED******REMOVED*** 1. First-Time Setup

The `.env.local` file is already created with development-friendly values:

```bash
***REMOVED*** Verify .env.local exists
cat .env.local
```

***REMOVED******REMOVED******REMOVED*** 2. Start All Services

```bash
***REMOVED*** From the project root directory
docker-compose -f docker-compose.local.yml up --build
```

This will:
- Build Docker images using standard Python and Node images
- Start all services (backend, frontend, database, Redis, Celery, n8n)
- Run database migrations automatically
- Enable hot reload for code changes

***REMOVED******REMOVED******REMOVED*** 3. Access the Application

Once all services are running (look for "Application startup complete" messages):

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | - |
| **Backend API** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **PostgreSQL** | localhost:5432 | User: `scheduler`<br>Password: `local_dev_password`<br>Database: `residency_scheduler` |
| **Redis** | localhost:6379 | Password: `local_dev_redis_pass` |
| **n8n** | http://localhost:5679 | User: `admin`<br>Password: `local_dev_n8n_password` |

***REMOVED******REMOVED******REMOVED*** 4. Verify Everything is Running

```bash
***REMOVED*** Check service status
docker-compose -f docker-compose.local.yml ps

***REMOVED*** View logs (all services)
docker-compose -f docker-compose.local.yml logs -f

***REMOVED*** View logs (specific service)
docker-compose -f docker-compose.local.yml logs -f backend
docker-compose -f docker-compose.local.yml logs -f frontend
docker-compose -f docker-compose.local.yml logs -f celery-worker
```

***REMOVED******REMOVED*** Daily Development Workflow

***REMOVED******REMOVED******REMOVED*** Starting Services

```bash
***REMOVED*** Start all services
docker-compose -f docker-compose.local.yml up

***REMOVED*** Start in background (detached mode)
docker-compose -f docker-compose.local.yml up -d

***REMOVED*** Start specific services only
docker-compose -f docker-compose.local.yml up backend db redis
```

***REMOVED******REMOVED******REMOVED*** Stopping Services

```bash
***REMOVED*** Stop all services (keeps data)
docker-compose -f docker-compose.local.yml down

***REMOVED*** Stop and remove volumes (clean slate)
docker-compose -f docker-compose.local.yml down -v

***REMOVED*** Stop specific service
docker-compose -f docker-compose.local.yml stop backend
```

***REMOVED******REMOVED******REMOVED*** Restarting After Code Changes

**No restart needed for most changes!** The services use hot reload:

- **Backend (Python)**: Changes to `.py` files auto-reload via uvicorn
- **Frontend (Next.js)**: Changes to `.tsx`, `.ts`, `.css` files auto-reload

**Restart required for**:
- Dependency changes (`requirements.txt`, `package.json`)
- Environment variable changes (`.env.local`)
- Docker configuration changes (`docker-compose.local.yml`, `Dockerfile.local`)

```bash
***REMOVED*** Restart after dependency changes
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up --build
```

***REMOVED******REMOVED*** Common Tasks

***REMOVED******REMOVED******REMOVED*** Database Operations

***REMOVED******REMOVED******REMOVED******REMOVED*** Connect to PostgreSQL

```bash
***REMOVED*** Using docker exec
docker-compose -f docker-compose.local.yml exec db psql -U scheduler -d residency_scheduler

***REMOVED*** Using local PostgreSQL client (if installed)
psql -h localhost -U scheduler -d residency_scheduler
***REMOVED*** Password: local_dev_password
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Run Database Migrations

```bash
***REMOVED*** Migrations run automatically on backend startup
***REMOVED*** To run manually:
docker-compose -f docker-compose.local.yml exec backend alembic upgrade head

***REMOVED*** Create new migration
docker-compose -f docker-compose.local.yml exec backend alembic revision --autogenerate -m "Description"

***REMOVED*** Rollback one migration
docker-compose -f docker-compose.local.yml exec backend alembic downgrade -1
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Reset Database

```bash
***REMOVED*** Stop services and remove database volume
docker-compose -f docker-compose.local.yml down -v

***REMOVED*** Start fresh (migrations will run automatically)
docker-compose -f docker-compose.local.yml up
```

***REMOVED******REMOVED******REMOVED*** Redis Operations

```bash
***REMOVED*** Connect to Redis CLI
docker-compose -f docker-compose.local.yml exec redis redis-cli -a local_dev_redis_pass

***REMOVED*** Common Redis commands:
***REMOVED*** KEYS *           - List all keys
***REMOVED*** GET key_name     - Get value of a key
***REMOVED*** FLUSHALL         - Clear all data (use with caution)
***REMOVED*** MONITOR          - Watch all Redis commands in real-time
```

***REMOVED******REMOVED******REMOVED*** Backend Development

```bash
***REMOVED*** View backend logs
docker-compose -f docker-compose.local.yml logs -f backend

***REMOVED*** Run tests inside container
docker-compose -f docker-compose.local.yml exec backend pytest

***REMOVED*** Run tests with coverage
docker-compose -f docker-compose.local.yml exec backend pytest --cov=app --cov-report=html

***REMOVED*** Access backend shell
docker-compose -f docker-compose.local.yml exec backend bash

***REMOVED*** Run Python REPL with app context
docker-compose -f docker-compose.local.yml exec backend python
```

***REMOVED******REMOVED******REMOVED*** Frontend Development

```bash
***REMOVED*** View frontend logs
docker-compose -f docker-compose.local.yml logs -f frontend

***REMOVED*** Install new npm package
docker-compose -f docker-compose.local.yml exec frontend npm install package-name

***REMOVED*** Run linter
docker-compose -f docker-compose.local.yml exec frontend npm run lint

***REMOVED*** Run type checking
docker-compose -f docker-compose.local.yml exec frontend npm run type-check

***REMOVED*** Access frontend shell
docker-compose -f docker-compose.local.yml exec frontend sh
```

***REMOVED******REMOVED******REMOVED*** Celery Operations

```bash
***REMOVED*** View Celery worker logs
docker-compose -f docker-compose.local.yml logs -f celery-worker

***REMOVED*** View Celery beat logs
docker-compose -f docker-compose.local.yml logs -f celery-beat

***REMOVED*** Check Celery worker status
docker-compose -f docker-compose.local.yml exec celery-worker celery -A app.core.celery_app inspect active

***REMOVED*** Purge all tasks from queue
docker-compose -f docker-compose.local.yml exec celery-worker celery -A app.core.celery_app purge
```

***REMOVED******REMOVED*** Debugging

***REMOVED******REMOVED******REMOVED*** Backend Debugging

The backend runs with `DEBUG=true` and verbose logging enabled.

***REMOVED******REMOVED******REMOVED******REMOVED*** View detailed logs:

```bash
docker-compose -f docker-compose.local.yml logs -f backend
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Add breakpoints (pdb):

```python
***REMOVED*** In your Python code
import pdb; pdb.set_trace()
```

Then attach to the container:

```bash
docker attach scheduler-local-backend
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Remote debugging (VS Code / PyCharm):

Port 5678 is exposed for debugpy (if you configure it).

***REMOVED******REMOVED******REMOVED*** Frontend Debugging

```bash
***REMOVED*** View Next.js debug output
docker-compose -f docker-compose.local.yml logs -f frontend

***REMOVED*** Disable Next.js caching (if issues)
docker-compose -f docker-compose.local.yml exec frontend rm -rf .next
docker-compose -f docker-compose.local.yml restart frontend
```

***REMOVED******REMOVED******REMOVED*** Database Debugging

```bash
***REMOVED*** Check active connections
docker-compose -f docker-compose.local.yml exec db psql -U scheduler -d residency_scheduler -c "SELECT * FROM pg_stat_activity;"

***REMOVED*** View table structure
docker-compose -f docker-compose.local.yml exec db psql -U scheduler -d residency_scheduler -c "\d persons"

***REMOVED*** Check recent migrations
docker-compose -f docker-compose.local.yml exec db psql -U scheduler -d residency_scheduler -c "SELECT * FROM alembic_version;"
```

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Port Already in Use

```bash
***REMOVED*** Find what's using the port (example for port 8000)
lsof -i :8000  ***REMOVED*** macOS/Linux
netstat -ano | findstr :8000  ***REMOVED*** Windows

***REMOVED*** Kill the process or change the port in docker-compose.local.yml
```

***REMOVED******REMOVED******REMOVED*** Services Not Starting

```bash
***REMOVED*** Check Docker daemon is running
docker info

***REMOVED*** View full error logs
docker-compose -f docker-compose.local.yml up

***REMOVED*** Check for resource issues
docker system df
docker system prune  ***REMOVED*** Clean up unused resources
```

***REMOVED******REMOVED******REMOVED*** Database Connection Issues

```bash
***REMOVED*** Verify database is healthy
docker-compose -f docker-compose.local.yml ps db

***REMOVED*** Check database logs
docker-compose -f docker-compose.local.yml logs db

***REMOVED*** Recreate database
docker-compose -f docker-compose.local.yml down -v
docker-compose -f docker-compose.local.yml up db
```

***REMOVED******REMOVED******REMOVED*** Hot Reload Not Working

```bash
***REMOVED*** Verify volume mounts are correct
docker-compose -f docker-compose.local.yml config

***REMOVED*** Restart the service
docker-compose -f docker-compose.local.yml restart backend

***REMOVED*** Rebuild if needed
docker-compose -f docker-compose.local.yml up --build backend
```

***REMOVED******REMOVED******REMOVED*** Celery Tasks Not Running

```bash
***REMOVED*** Check worker is running
docker-compose -f docker-compose.local.yml ps celery-worker

***REMOVED*** Check worker can ping
docker-compose -f docker-compose.local.yml exec celery-worker celery -A app.core.celery_app inspect ping

***REMOVED*** Check Redis connection
docker-compose -f docker-compose.local.yml exec celery-worker celery -A app.core.celery_app inspect stats
```

***REMOVED******REMOVED*** Performance Tips

***REMOVED******REMOVED******REMOVED*** Speed Up Builds

```bash
***REMOVED*** Use Docker build cache
docker-compose -f docker-compose.local.yml build --parallel

***REMOVED*** Clean build cache if stale
docker builder prune
```

***REMOVED******REMOVED******REMOVED*** Reduce Resource Usage

Edit `docker-compose.local.yml` to:
- Disable n8n if not needed (comment out the service)
- Reduce Redis maxmemory: `--maxmemory 128mb`
- Run fewer Celery workers

***REMOVED******REMOVED******REMOVED*** Monitor Resource Usage

```bash
***REMOVED*** View resource usage
docker stats

***REMOVED*** View specific service
docker stats scheduler-local-backend
```

***REMOVED******REMOVED*** Differences from Production

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

***REMOVED******REMOVED*** Switching to Production Configuration

When ready for production:

```bash
***REMOVED*** Use the production docker-compose.yml
docker-compose up --build

***REMOVED*** Or with environment-specific overrides
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```

Make sure to:
1. Use `.env` with strong secrets (not `.env.local`)
2. Set `DEBUG=false`
3. Use proper CORS origins
4. Enable rate limiting
5. Use HTTPS
6. Review security settings

***REMOVED******REMOVED*** Getting Help

- **Backend Issues**: Check `backend/README.md` and `docs/development/`
- **Frontend Issues**: Check `frontend/README.md`
- **Docker Issues**: Run `docker-compose -f docker-compose.local.yml config` to validate
- **Database Issues**: Check `docs/admin-manual/database.md`

***REMOVED******REMOVED*** Additional Resources

- [CLAUDE.md](../../CLAUDE.md) - Project development guidelines
- [README.md](../../README.md) - Main project documentation
- [docs/](../) - Comprehensive documentation
- [.env.example](../../.env.example) - Production environment template

---

**Happy Coding!** 🚀

The local development environment is designed to make your development experience smooth and productive. If you encounter issues not covered here, please update this documentation.
