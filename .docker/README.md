***REMOVED*** Production Docker Configuration

Production-ready Docker setup for Residency Scheduler with security hardening, health checks, and resource limits.

***REMOVED******REMOVED*** Directory Structure

```
.docker/
├── backend.Dockerfile      ***REMOVED*** Multi-stage backend build
├── frontend.Dockerfile     ***REMOVED*** Multi-stage frontend build with nginx
├── docker-compose.prod.yml ***REMOVED*** Production orchestration
├── .env.prod.example       ***REMOVED*** Environment template
├── nginx/
│   ├── nginx.conf          ***REMOVED*** Main nginx configuration
│   └── default.conf        ***REMOVED*** Server block configuration
└── README.md               ***REMOVED*** This file
```

***REMOVED******REMOVED*** Quick Start

***REMOVED******REMOVED******REMOVED*** 1. Create Environment File

```bash
cp .docker/.env.prod.example .docker/.env
```

***REMOVED******REMOVED******REMOVED*** 2. Generate Secrets

```bash
***REMOVED*** Create secrets directory
mkdir -p .docker/secrets

***REMOVED*** Generate database password
openssl rand -base64 32 > .docker/secrets/db_password.txt

***REMOVED*** Generate JWT secret key
python -c "import secrets; print(secrets.token_urlsafe(64))" > .docker/secrets/secret_key.txt

***REMOVED*** Set proper permissions
chmod 600 .docker/secrets/*.txt
```

***REMOVED******REMOVED******REMOVED*** 3. Create Data Directories

```bash
sudo mkdir -p /var/lib/residency-scheduler/{postgres,redis}
sudo chown -R 1001:1001 /var/lib/residency-scheduler
```

***REMOVED******REMOVED******REMOVED*** 4. Build and Deploy

```bash
***REMOVED*** Build images
docker-compose -f .docker/docker-compose.prod.yml build

***REMOVED*** Start services
docker-compose -f .docker/docker-compose.prod.yml up -d

***REMOVED*** View logs
docker-compose -f .docker/docker-compose.prod.yml logs -f
```

***REMOVED******REMOVED*** Security Features

***REMOVED******REMOVED******REMOVED*** Container Hardening
- Non-root users in all containers
- Read-only root filesystems
- No new privileges security option
- Minimal base images (Alpine/slim)
- Multi-stage builds to reduce attack surface

***REMOVED******REMOVED******REMOVED*** Network Security
- Internal backend network (no external access)
- Frontend network for public access
- Rate limiting on API endpoints
- Strict CORS configuration

***REMOVED******REMOVED******REMOVED*** Secrets Management
- Docker secrets for sensitive data
- No secrets in environment variables
- File-based secret injection

***REMOVED******REMOVED*** Health Checks

All services include health checks:

| Service | Endpoint | Interval |
|---------|----------|----------|
| PostgreSQL | pg_isready | 10s |
| Redis | redis-cli ping | 10s |
| Backend | /health | 30s |
| Celery | celery inspect | 30s |
| Frontend | /health | 30s |

***REMOVED******REMOVED*** Resource Limits

| Service | CPU Limit | Memory Limit | CPU Reserved | Memory Reserved |
|---------|-----------|--------------|--------------|-----------------|
| PostgreSQL | 2 cores | 2GB | 0.5 cores | 512MB |
| Redis | 0.5 cores | 512MB | 0.1 cores | 128MB |
| Backend | 4 cores | 4GB | 1 core | 1GB |
| Celery | 2 cores | 2GB | 0.5 cores | 512MB |
| Frontend | 1 core | 512MB | 0.25 cores | 128MB |

***REMOVED******REMOVED*** Scaling

***REMOVED******REMOVED******REMOVED*** Horizontal Scaling (Backend)

```bash
docker-compose -f .docker/docker-compose.prod.yml up -d --scale backend=3
```

***REMOVED******REMOVED******REMOVED*** Celery Workers

```bash
docker-compose -f .docker/docker-compose.prod.yml up -d --scale celery-worker=4
```

***REMOVED******REMOVED*** Monitoring

***REMOVED******REMOVED******REMOVED*** Prometheus Metrics

Backend exposes metrics at `/metrics` (internal only).

***REMOVED******REMOVED******REMOVED*** Log Aggregation

All containers use JSON file logging with rotation:
- Max size: 10MB
- Max files: 5

Access logs:
```bash
docker-compose -f .docker/docker-compose.prod.yml logs -f backend
```

***REMOVED******REMOVED******REMOVED*** Container Status

```bash
docker-compose -f .docker/docker-compose.prod.yml ps
```

***REMOVED******REMOVED*** Backup and Recovery

***REMOVED******REMOVED******REMOVED*** Database Backup

```bash
docker-compose -f .docker/docker-compose.prod.yml exec db \
  pg_dump -U scheduler residency_scheduler > backup.sql
```

***REMOVED******REMOVED******REMOVED*** Database Restore

```bash
docker-compose -f .docker/docker-compose.prod.yml exec -T db \
  psql -U scheduler residency_scheduler < backup.sql
```

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Container Won't Start

```bash
***REMOVED*** Check logs
docker-compose -f .docker/docker-compose.prod.yml logs <service>

***REMOVED*** Check health status
docker inspect --format='{{.State.Health.Status}}' <container>
```

***REMOVED******REMOVED******REMOVED*** Database Connection Issues

```bash
***REMOVED*** Verify database is healthy
docker-compose -f .docker/docker-compose.prod.yml exec db pg_isready

***REMOVED*** Check connection from backend
docker-compose -f .docker/docker-compose.prod.yml exec backend \
  python -c "from app.database import engine; engine.connect(); print('OK')"
```

***REMOVED******REMOVED******REMOVED*** Permission Issues

Ensure data directories have correct ownership:
```bash
sudo chown -R 1001:1001 /var/lib/residency-scheduler
```

***REMOVED******REMOVED*** Updating

***REMOVED******REMOVED******REMOVED*** Rolling Update

```bash
***REMOVED*** Pull latest images
docker-compose -f .docker/docker-compose.prod.yml pull

***REMOVED*** Recreate containers with zero downtime
docker-compose -f .docker/docker-compose.prod.yml up -d --no-deps --build backend
docker-compose -f .docker/docker-compose.prod.yml up -d --no-deps --build frontend
```

***REMOVED******REMOVED******REMOVED*** Full Update

```bash
***REMOVED*** Stop all services
docker-compose -f .docker/docker-compose.prod.yml down

***REMOVED*** Rebuild and restart
docker-compose -f .docker/docker-compose.prod.yml up -d --build
```
