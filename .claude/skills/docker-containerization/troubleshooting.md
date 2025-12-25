***REMOVED*** Docker Troubleshooting Reference

Common issues and solutions for Docker development and production.

***REMOVED******REMOVED*** Build Failures

***REMOVED******REMOVED******REMOVED*** "COPY failed: file not found"

**Cause:** File path doesn't exist or is in `.dockerignore`

**Solution:**
```bash
***REMOVED*** Check if file exists
ls -la path/to/file

***REMOVED*** Check .dockerignore
cat .dockerignore | grep filename

***REMOVED*** Build with verbose output
docker build --progress=plain .
```

***REMOVED******REMOVED******REMOVED*** "No space left on device"

**Cause:** Docker storage full

**Solution:**
```bash
***REMOVED*** Check Docker disk usage
docker system df

***REMOVED*** Clean up everything unused
docker system prune -af --volumes

***REMOVED*** Clean up old build cache
docker builder prune -af
```

***REMOVED******REMOVED******REMOVED*** "pip install fails" / Dependency conflicts

**Cause:** Missing system packages for compiled dependencies

**Solution:**
```dockerfile
***REMOVED*** Add build dependencies in builder stage
FROM python:3.12-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*
```

***REMOVED******REMOVED******REMOVED*** "npm ERR! ERESOLVE" in frontend build

**Cause:** Dependency version conflicts

**Solution:**
```dockerfile
***REMOVED*** Use --legacy-peer-deps or fix package.json
RUN npm ci --legacy-peer-deps
***REMOVED*** OR
RUN npm install --force
```

***REMOVED******REMOVED*** Container Startup Issues

***REMOVED******REMOVED******REMOVED*** Container exits immediately (exit code 0)

**Cause:** No foreground process

**Solution:**
```dockerfile
***REMOVED*** Use foreground process
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
***REMOVED*** NOT
CMD ["uvicorn", "app.main:app", "&"]
```

***REMOVED******REMOVED******REMOVED*** Container exits with code 1

**Cause:** Application error at startup

**Diagnosis:**
```bash
***REMOVED*** View logs
docker compose logs backend

***REMOVED*** Run interactively
docker compose run --rm backend bash
python -c "from app.main import app; print('OK')"
```

**Common causes:**
- Missing environment variables
- Database not ready
- Invalid configuration

***REMOVED******REMOVED******REMOVED*** Container exits with code 137 (OOM Killed)

**Cause:** Out of memory

**Solution:**
```yaml
***REMOVED*** Increase memory limits
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G
```

```bash
***REMOVED*** Check for OOM in system logs
dmesg | grep -i "killed process"
```

***REMOVED******REMOVED******REMOVED*** "Connection refused" to database

**Cause:** Database not ready when app starts

**Solution:**
```yaml
***REMOVED*** Use health checks with depends_on condition
services:
  backend:
    depends_on:
      db:
        condition: service_healthy

  db:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U scheduler"]
      interval: 5s
      timeout: 5s
      retries: 10
```

***REMOVED******REMOVED*** Networking Issues

***REMOVED******REMOVED******REMOVED*** Container can't reach another container

**Cause:** Different networks or wrong hostname

**Diagnosis:**
```bash
***REMOVED*** Check networks
docker network ls
docker network inspect <network>

***REMOVED*** Test connectivity from container
docker compose exec backend ping db
docker compose exec backend curl -v http://db:5432
```

**Solution:**
```yaml
***REMOVED*** Ensure both on same network
services:
  backend:
    networks:
      - app-network
  db:
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

***REMOVED******REMOVED******REMOVED*** "Port already in use"

**Cause:** Another process using the port

**Solution:**
```bash
***REMOVED*** Find what's using the port
lsof -i :8000
***REMOVED*** OR
netstat -tulpn | grep 8000

***REMOVED*** Kill the process or use different port
docker compose down  ***REMOVED*** May have orphaned containers
docker ps -a | grep 8000
```

***REMOVED******REMOVED******REMOVED*** DNS resolution fails inside container

**Cause:** DNS configuration issues

**Solution:**
```yaml
***REMOVED*** Specify DNS servers
services:
  backend:
    dns:
      - 8.8.8.8
      - 8.8.4.4
```

***REMOVED******REMOVED*** Volume/Mount Issues

***REMOVED******REMOVED******REMOVED*** "Permission denied" on mounted files

**Cause:** UID/GID mismatch between host and container

**Solution:**
```dockerfile
***REMOVED*** Match host user's UID
ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID appgroup && useradd -u $UID -g appgroup appuser
USER appuser
```

```yaml
***REMOVED*** Or run container as host user
services:
  backend:
    user: "${UID}:${GID}"
```

***REMOVED******REMOVED******REMOVED*** Changes not reflected in mounted volume

**Cause:** Cached filesystem or delegated mount

**Solution (macOS):**
```yaml
volumes:
  - ./backend:/app:cached  ***REMOVED*** Read-heavy
  ***REMOVED*** OR
  - ./backend:/app:delegated  ***REMOVED*** Write-heavy (host sees changes later)
```

**Solution (Force sync):**
```bash
***REMOVED*** Touch a file to trigger sync
touch backend/app/main.py
```

***REMOVED******REMOVED******REMOVED*** Volume data persists after down

**Cause:** Named volumes are not removed by `down`

**Solution:**
```bash
***REMOVED*** Remove volumes too
docker compose down -v

***REMOVED*** Or remove specific volume
docker volume rm project_postgres_data
```

***REMOVED******REMOVED*** Performance Issues

***REMOVED******REMOVED******REMOVED*** Slow builds

**Solution 1: Fix layer ordering**
```dockerfile
***REMOVED*** Dependencies before code (cached if requirements don't change)
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .  ***REMOVED*** Only this invalidates on code changes
```

**Solution 2: Use BuildKit cache mounts**
```dockerfile
***REMOVED*** syntax=docker/dockerfile:1.4
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

**Solution 3: Enable BuildKit**
```bash
export DOCKER_BUILDKIT=1
docker build .
```

***REMOVED******REMOVED******REMOVED*** Slow container startup

**Diagnosis:**
```bash
***REMOVED*** Profile startup
time docker compose up backend
docker compose logs --timestamps backend | head -50
```

**Solutions:**
- Reduce dependencies
- Use lazy imports in Python
- Warm up connections in background

***REMOVED******REMOVED******REMOVED*** High memory usage

**Diagnosis:**
```bash
docker stats
docker compose exec backend ps aux --sort=-%mem | head
```

**Solutions:**
```yaml
***REMOVED*** Set limits
deploy:
  resources:
    limits:
      memory: 2G
```

***REMOVED******REMOVED*** Health Check Failures

***REMOVED******REMOVED******REMOVED*** Container "unhealthy" status

**Diagnosis:**
```bash
***REMOVED*** View health check output
docker inspect --format='{{json .State.Health}}' container_id

***REMOVED*** View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' container_id
```

**Common fixes:**
```yaml
***REMOVED*** Increase start period for slow apps
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  start_period: 60s  ***REMOVED*** Give app time to start
  retries: 5
```

***REMOVED******REMOVED******REMOVED*** curl not found in health check

**Solution:**
```dockerfile
***REMOVED*** Install curl in runtime stage
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
```

**Or use wget (often pre-installed):**
```yaml
healthcheck:
  test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8000/health"]
```

**Or use Python for Python containers:**
```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
```

***REMOVED******REMOVED*** Development Workflow Issues

***REMOVED******REMOVED******REMOVED*** Hot reload not working

**Cause:** Volume mount not configured or file watcher issues

**Solution:**
```yaml
***REMOVED*** Ensure volume mount
volumes:
  - ./backend/app:/app/app:delegated

***REMOVED*** Ensure reload flag
command: uvicorn app.main:app --host 0.0.0.0 --reload
```

**For Next.js:**
```yaml
volumes:
  - ./frontend/src:/app/src:delegated
  - ./frontend/public:/app/public:delegated
```

***REMOVED******REMOVED******REMOVED*** Tests fail in container but pass locally

**Cause:** Different environment (Python version, OS, dependencies)

**Solution:**
```bash
***REMOVED*** Always run tests in container
docker compose exec backend pytest

***REMOVED*** Or use same image for CI
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm backend pytest
```

***REMOVED******REMOVED*** Debugging Commands Reference

```bash
***REMOVED*** === Container Status ===
docker compose ps                          ***REMOVED*** Service status
docker compose top                         ***REMOVED*** Running processes
docker stats                               ***REMOVED*** Resource usage

***REMOVED*** === Logs ===
docker compose logs -f service             ***REMOVED*** Follow logs
docker compose logs --tail=100 service     ***REMOVED*** Last 100 lines
docker compose logs --since=1h service     ***REMOVED*** Last hour

***REMOVED*** === Exec Into Container ===
docker compose exec backend bash           ***REMOVED*** Interactive shell
docker compose exec backend python         ***REMOVED*** Python REPL
docker compose exec db psql -U scheduler   ***REMOVED*** Database CLI

***REMOVED*** === Network ===
docker network ls                          ***REMOVED*** List networks
docker network inspect network_name        ***REMOVED*** Network details

***REMOVED*** === Volumes ===
docker volume ls                           ***REMOVED*** List volumes
docker volume inspect volume_name          ***REMOVED*** Volume details

***REMOVED*** === Clean Up ===
docker compose down                        ***REMOVED*** Stop and remove
docker compose down -v                     ***REMOVED*** Include volumes
docker compose down --remove-orphans       ***REMOVED*** Remove orphaned containers
docker system prune -af                    ***REMOVED*** Remove all unused

***REMOVED*** === Build ===
docker compose build --no-cache            ***REMOVED*** Fresh build
docker compose build --progress=plain      ***REMOVED*** Verbose output
docker compose build --pull                ***REMOVED*** Update base images
```

***REMOVED******REMOVED*** Emergency Recovery

***REMOVED******REMOVED******REMOVED*** Container keeps restarting

```bash
***REMOVED*** Stop restart loop
docker compose stop service

***REMOVED*** Start manually for debugging
docker compose run --rm service bash

***REMOVED*** Check last logs before crash
docker compose logs --tail=200 service
```

***REMOVED******REMOVED******REMOVED*** Database volume corrupted

```bash
***REMOVED*** 1. Stop everything
docker compose down

***REMOVED*** 2. Backup volume (if possible)
docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

***REMOVED*** 3. Remove and recreate
docker volume rm project_postgres_data
docker compose up -d db

***REMOVED*** 4. Restore from application backup
docker compose exec backend python scripts/restore_backup.py
```

***REMOVED******REMOVED******REMOVED*** Complete reset

```bash
***REMOVED*** Nuclear option - removes EVERYTHING
docker compose down -v --remove-orphans
docker system prune -af --volumes
docker compose up -d --build
```
