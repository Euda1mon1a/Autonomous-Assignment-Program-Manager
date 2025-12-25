# Docker Troubleshooting Reference

Common issues and solutions for Docker development and production.

## Build Failures

### "COPY failed: file not found"

**Cause:** File path doesn't exist or is in `.dockerignore`

**Solution:**
```bash
# Check if file exists
ls -la path/to/file

# Check .dockerignore
cat .dockerignore | grep filename

# Build with verbose output
docker build --progress=plain .
```

### "No space left on device"

**Cause:** Docker storage full

**Solution:**
```bash
# Check Docker disk usage
docker system df

# Clean up everything unused
docker system prune -af --volumes

# Clean up old build cache
docker builder prune -af
```

### "pip install fails" / Dependency conflicts

**Cause:** Missing system packages for compiled dependencies

**Solution:**
```dockerfile
# Add build dependencies in builder stage
FROM python:3.12-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*
```

### "npm ERR! ERESOLVE" in frontend build

**Cause:** Dependency version conflicts

**Solution:**
```dockerfile
# Use --legacy-peer-deps or fix package.json
RUN npm ci --legacy-peer-deps
# OR
RUN npm install --force
```

## Container Startup Issues

### Container exits immediately (exit code 0)

**Cause:** No foreground process

**Solution:**
```dockerfile
# Use foreground process
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
# NOT
CMD ["uvicorn", "app.main:app", "&"]
```

### Container exits with code 1

**Cause:** Application error at startup

**Diagnosis:**
```bash
# View logs
docker compose logs backend

# Run interactively
docker compose run --rm backend bash
python -c "from app.main import app; print('OK')"
```

**Common causes:**
- Missing environment variables
- Database not ready
- Invalid configuration

### Container exits with code 137 (OOM Killed)

**Cause:** Out of memory

**Solution:**
```yaml
# Increase memory limits
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G
```

```bash
# Check for OOM in system logs
dmesg | grep -i "killed process"
```

### "Connection refused" to database

**Cause:** Database not ready when app starts

**Solution:**
```yaml
# Use health checks with depends_on condition
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

## Networking Issues

### Container can't reach another container

**Cause:** Different networks or wrong hostname

**Diagnosis:**
```bash
# Check networks
docker network ls
docker network inspect <network>

# Test connectivity from container
docker compose exec backend ping db
docker compose exec backend curl -v http://db:5432
```

**Solution:**
```yaml
# Ensure both on same network
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

### "Port already in use"

**Cause:** Another process using the port

**Solution:**
```bash
# Find what's using the port
lsof -i :8000
# OR
netstat -tulpn | grep 8000

# Kill the process or use different port
docker compose down  # May have orphaned containers
docker ps -a | grep 8000
```

### DNS resolution fails inside container

**Cause:** DNS configuration issues

**Solution:**
```yaml
# Specify DNS servers
services:
  backend:
    dns:
      - 8.8.8.8
      - 8.8.4.4
```

## Volume/Mount Issues

### "Permission denied" on mounted files

**Cause:** UID/GID mismatch between host and container

**Solution:**
```dockerfile
# Match host user's UID
ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID appgroup && useradd -u $UID -g appgroup appuser
USER appuser
```

```yaml
# Or run container as host user
services:
  backend:
    user: "${UID}:${GID}"
```

### Changes not reflected in mounted volume

**Cause:** Cached filesystem or delegated mount

**Solution (macOS):**
```yaml
volumes:
  - ./backend:/app:cached  # Read-heavy
  # OR
  - ./backend:/app:delegated  # Write-heavy (host sees changes later)
```

**Solution (Force sync):**
```bash
# Touch a file to trigger sync
touch backend/app/main.py
```

### Volume data persists after down

**Cause:** Named volumes are not removed by `down`

**Solution:**
```bash
# Remove volumes too
docker compose down -v

# Or remove specific volume
docker volume rm project_postgres_data
```

## Performance Issues

### Slow builds

**Solution 1: Fix layer ordering**
```dockerfile
# Dependencies before code (cached if requirements don't change)
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .  # Only this invalidates on code changes
```

**Solution 2: Use BuildKit cache mounts**
```dockerfile
# syntax=docker/dockerfile:1.4
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

**Solution 3: Enable BuildKit**
```bash
export DOCKER_BUILDKIT=1
docker build .
```

### Slow container startup

**Diagnosis:**
```bash
# Profile startup
time docker compose up backend
docker compose logs --timestamps backend | head -50
```

**Solutions:**
- Reduce dependencies
- Use lazy imports in Python
- Warm up connections in background

### High memory usage

**Diagnosis:**
```bash
docker stats
docker compose exec backend ps aux --sort=-%mem | head
```

**Solutions:**
```yaml
# Set limits
deploy:
  resources:
    limits:
      memory: 2G
```

## Health Check Failures

### Container "unhealthy" status

**Diagnosis:**
```bash
# View health check output
docker inspect --format='{{json .State.Health}}' container_id

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' container_id
```

**Common fixes:**
```yaml
# Increase start period for slow apps
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  start_period: 60s  # Give app time to start
  retries: 5
```

### curl not found in health check

**Solution:**
```dockerfile
# Install curl in runtime stage
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

## Development Workflow Issues

### Hot reload not working

**Cause:** Volume mount not configured or file watcher issues

**Solution:**
```yaml
# Ensure volume mount
volumes:
  - ./backend/app:/app/app:delegated

# Ensure reload flag
command: uvicorn app.main:app --host 0.0.0.0 --reload
```

**For Next.js:**
```yaml
volumes:
  - ./frontend/src:/app/src:delegated
  - ./frontend/public:/app/public:delegated
```

### Tests fail in container but pass locally

**Cause:** Different environment (Python version, OS, dependencies)

**Solution:**
```bash
# Always run tests in container
docker compose exec backend pytest

# Or use same image for CI
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm backend pytest
```

## Debugging Commands Reference

```bash
# === Container Status ===
docker compose ps                          # Service status
docker compose top                         # Running processes
docker stats                               # Resource usage

# === Logs ===
docker compose logs -f service             # Follow logs
docker compose logs --tail=100 service     # Last 100 lines
docker compose logs --since=1h service     # Last hour

# === Exec Into Container ===
docker compose exec backend bash           # Interactive shell
docker compose exec backend python         # Python REPL
docker compose exec db psql -U scheduler   # Database CLI

# === Network ===
docker network ls                          # List networks
docker network inspect network_name        # Network details

# === Volumes ===
docker volume ls                           # List volumes
docker volume inspect volume_name          # Volume details

# === Clean Up ===
docker compose down                        # Stop and remove
docker compose down -v                     # Include volumes
docker compose down --remove-orphans       # Remove orphaned containers
docker system prune -af                    # Remove all unused

# === Build ===
docker compose build --no-cache            # Fresh build
docker compose build --progress=plain      # Verbose output
docker compose build --pull                # Update base images
```

## Emergency Recovery

### Container keeps restarting

```bash
# Stop restart loop
docker compose stop service

# Start manually for debugging
docker compose run --rm service bash

# Check last logs before crash
docker compose logs --tail=200 service
```

### Database volume corrupted

```bash
# 1. Stop everything
docker compose down

# 2. Backup volume (if possible)
docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# 3. Remove and recreate
docker volume rm project_postgres_data
docker compose up -d db

# 4. Restore from application backup
docker compose exec backend python scripts/restore_backup.py
```

### Complete reset

```bash
# Nuclear option - removes EVERYTHING
docker compose down -v --remove-orphans
docker system prune -af --volumes
docker compose up -d --build
```
