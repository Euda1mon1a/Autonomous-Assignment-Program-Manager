# Production Docker Configuration

Production-ready Docker setup for Residency Scheduler with security hardening, health checks, and resource limits.

## Directory Structure

```
.docker/
├── backend.Dockerfile      # Multi-stage backend build
├── frontend.Dockerfile     # Multi-stage frontend build with nginx
├── docker-compose.prod.yml # Production orchestration
├── .env.prod.example       # Environment template
├── nginx/
│   ├── nginx.conf          # Main nginx configuration
│   └── default.conf        # Server block configuration
└── README.md               # This file
```

## Quick Start

### 1. Create Environment File

```bash
cp .docker/.env.prod.example .docker/.env
```

### 2. Generate Secrets

```bash
# Create secrets directory
mkdir -p .docker/secrets

# Generate database password
openssl rand -base64 32 > .docker/secrets/db_password.txt

# Generate JWT secret key
python -c "import secrets; print(secrets.token_urlsafe(64))" > .docker/secrets/secret_key.txt

# Set proper permissions
chmod 600 .docker/secrets/*.txt
```

### 3. Create Data Directories

```bash
sudo mkdir -p /var/lib/residency-scheduler/{postgres,redis}
sudo chown -R 1001:1001 /var/lib/residency-scheduler
```

### 4. Build and Deploy

```bash
# Build images
docker-compose -f .docker/docker-compose.prod.yml build

# Start services
docker-compose -f .docker/docker-compose.prod.yml up -d

# View logs
docker-compose -f .docker/docker-compose.prod.yml logs -f
```

## Security Features

### Container Hardening
- Non-root users in all containers
- Read-only root filesystems
- No new privileges security option
- Minimal base images (Alpine/slim)
- Multi-stage builds to reduce attack surface

### Network Security
- Internal backend network (no external access)
- Frontend network for public access
- Rate limiting on API endpoints
- Strict CORS configuration

### Secrets Management
- Docker secrets for sensitive data
- No secrets in environment variables
- File-based secret injection

## Health Checks

All services include health checks:

| Service | Endpoint | Interval |
|---------|----------|----------|
| PostgreSQL | pg_isready | 10s |
| Redis | redis-cli ping | 10s |
| Backend | /health | 30s |
| Celery | celery inspect | 30s |
| Frontend | /health | 30s |

## Resource Limits

| Service | CPU Limit | Memory Limit | CPU Reserved | Memory Reserved |
|---------|-----------|--------------|--------------|-----------------|
| PostgreSQL | 2 cores | 2GB | 0.5 cores | 512MB |
| Redis | 0.5 cores | 512MB | 0.1 cores | 128MB |
| Backend | 4 cores | 4GB | 1 core | 1GB |
| Celery | 2 cores | 2GB | 0.5 cores | 512MB |
| Frontend | 1 core | 512MB | 0.25 cores | 128MB |

## Scaling

### Horizontal Scaling (Backend)

```bash
docker-compose -f .docker/docker-compose.prod.yml up -d --scale backend=3
```

### Celery Workers

```bash
docker-compose -f .docker/docker-compose.prod.yml up -d --scale celery-worker=4
```

## Monitoring

### Prometheus Metrics

Backend exposes metrics at `/metrics` (internal only).

### Log Aggregation

All containers use JSON file logging with rotation:
- Max size: 10MB
- Max files: 5

Access logs:
```bash
docker-compose -f .docker/docker-compose.prod.yml logs -f backend
```

### Container Status

```bash
docker-compose -f .docker/docker-compose.prod.yml ps
```

## Backup and Recovery

### Database Backup

```bash
docker-compose -f .docker/docker-compose.prod.yml exec db \
  pg_dump -U scheduler residency_scheduler > backup.sql
```

### Database Restore

```bash
docker-compose -f .docker/docker-compose.prod.yml exec -T db \
  psql -U scheduler residency_scheduler < backup.sql
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f .docker/docker-compose.prod.yml logs <service>

# Check health status
docker inspect --format='{{.State.Health.Status}}' <container>
```

### Database Connection Issues

```bash
# Verify database is healthy
docker-compose -f .docker/docker-compose.prod.yml exec db pg_isready

# Check connection from backend
docker-compose -f .docker/docker-compose.prod.yml exec backend \
  python -c "from app.database import engine; engine.connect(); print('OK')"
```

### Permission Issues

Ensure data directories have correct ownership:
```bash
sudo chown -R 1001:1001 /var/lib/residency-scheduler
```

## Updating

### Rolling Update

```bash
# Pull latest images
docker-compose -f .docker/docker-compose.prod.yml pull

# Recreate containers with zero downtime
docker-compose -f .docker/docker-compose.prod.yml up -d --no-deps --build backend
docker-compose -f .docker/docker-compose.prod.yml up -d --no-deps --build frontend
```

### Full Update

```bash
# Stop all services
docker-compose -f .docker/docker-compose.prod.yml down

# Rebuild and restart
docker-compose -f .docker/docker-compose.prod.yml up -d --build
```
