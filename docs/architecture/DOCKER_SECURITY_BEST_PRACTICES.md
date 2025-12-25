# Docker Security Best Practices

> **Last Updated:** 2025-12-25
> **Status:** Implemented and verified

This document describes the Docker security measures and best practices implemented in the Residency Scheduler project.

---

## Overview

The Docker setup has been reviewed and implements industry best practices for container security, including:

- Multi-stage builds for minimal attack surface
- Non-root users in all containers
- Health checks on all services
- Automated vulnerability scanning in CI/CD
- Proper secrets management
- Resource limits in production

---

## Security Measures by Container

### Backend (`backend/Dockerfile`)

| Practice | Implementation | Status |
|----------|----------------|--------|
| Multi-stage build | `builder` → `runtime` stages | Implemented |
| Minimal base image | `python:3.12-slim` | Implemented |
| Non-root user | `appuser` (UID 1001) | Implemented |
| No shell entrypoint | `docker-entrypoint.sh` with `exec` | Implemented |
| Health check | Python urllib (no curl needed) | Implemented |
| No cache bloat | `pip install --no-cache-dir` | Implemented |
| Signal handling | `exec uvicorn` for proper PID 1 | Implemented |

**Entrypoint Pattern:**

The backend uses an entrypoint script that runs migrations and then `exec`s uvicorn:

```bash
#!/bin/sh
set -e
echo "Running database migrations..."
alembic upgrade head
echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
```

Using `exec` ensures uvicorn becomes PID 1 and receives signals directly (SIGTERM for graceful shutdown), preventing zombie processes.

### Frontend (`frontend/Dockerfile`)

| Practice | Implementation | Status |
|----------|----------------|--------|
| Multi-stage build | `builder` → `runtime` stages | Implemented |
| Minimal runtime | Next.js standalone output | Implemented |
| Non-root user | `nextjs` (UID 1001) | Implemented |
| Health check | Node.js HTTP module | Implemented |
| Telemetry disabled | `NEXT_TELEMETRY_DISABLED=1` | Implemented |

### MCP Server (`mcp-server/Dockerfile`)

| Practice | Implementation | Status |
|----------|----------------|--------|
| Multi-stage build | `builder` → `runtime` stages | Implemented |
| Non-root user | `mcp` (UID 1000) | Implemented |
| Security options | `no-new-privileges:true` | Implemented |
| Resource limits | CPU/memory in compose | Implemented |
| Health check | Python import verification | Implemented |

### Nginx (`nginx/Dockerfile`)

| Practice | Implementation | Status |
|----------|----------------|--------|
| Alpine base | `nginx:1.27-alpine` | Implemented |
| Proper permissions | `nginx` user ownership | Implemented |
| Health check | `nginx -t` config test | Implemented |

---

## Docker Compose Security

### Base Configuration (`docker-compose.yml`)

- **Health checks** on all services with appropriate intervals
- **Dependency ordering** with `depends_on: condition: service_healthy`
- **Network isolation** via dedicated `app-network`
- **Named volumes** for data persistence

### Production Configuration (`docker-compose.prod.yml`)

| Feature | Implementation |
|---------|----------------|
| Resource limits | CPU and memory limits on all services |
| Logging rotation | `max-size`, `max-file`, `compress` |
| Redis hardening | Password, timeout, keepalive settings |
| Network segmentation | Dedicated subnet (172.28.0.0/16) |

Example resource limits:
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '1.0'
      memory: 1G
```

---

## CI/CD Security Scanning

Security scanning is automated via `.github/workflows/security.yml`:

### Vulnerability Scanning

| Tool | Scope | Trigger |
|------|-------|---------|
| **Trivy** | Container images, filesystem | Push, PR, weekly |
| **Safety** | Python dependencies | Push, PR |
| **pip-audit** | Python CVEs | Push, PR |
| **npm audit** | Node.js dependencies | Push, PR |
| **Docker Scout** | Container CVEs | Push |

### Static Analysis

| Tool | Language | Trigger |
|------|----------|---------|
| **CodeQL** | Python, TypeScript | Push, PR |
| **Semgrep** | All (security rules) | Push, PR |
| **Bandit** | Python security | Push, PR |
| **Gitleaks** | Secret detection | Push, PR |

### Container Image Scanning

```yaml
# Builds and scans both backend and frontend images
docker-scan:
  strategy:
    matrix:
      context: ['backend', 'frontend']
  steps:
    - name: Build Docker image for scanning
      uses: docker/build-push-action@v6
    - name: Run Trivy container scan
      uses: aquasecurity/trivy-action@master
```

---

## Secrets Management

### Development Environment

- Environment variables with defaults for local dev
- Example: `${REDIS_PASSWORD:-dev_only_password}`
- `.env` file for local overrides (gitignored)

### Production Environment

- No defaults - fails if secrets not set
- Example: `${REDIS_PASSWORD}` (no fallback)
- Secrets injected at deployment time

### Application-Level Validation

The application refuses to start if critical secrets are:
- Empty
- Less than 32 characters
- Using known default values

```python
# From backend/app/core/config.py
if len(settings.SECRET_KEY) < 32:
    raise ValueError("SECRET_KEY must be at least 32 characters")
```

---

## Logging Configuration

Production logging uses structured JSON with rotation:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "20m"
    max-file: "5"
    compress: "true"
```

| Service | Max Size | Max Files |
|---------|----------|-----------|
| Backend | 20m | 5 |
| Celery Worker | 15m | 5 |
| Redis | 5m | 3 |
| Nginx | 20m | 5 |

---

## What We Don't Implement (and Why)

| Practice | Status | Rationale |
|----------|--------|-----------|
| Image signing (Cosign) | Not implemented | Adds operational overhead; only critical for public registries |
| Multi-arch builds | Not implemented | No ARM64 deployment target currently |
| BuildKit cache mounts | Not implemented | Marginal benefit for this project size |
| tini init process | Not implemented | Entrypoint script with `exec` achieves same goal |

---

## Verification Commands

### Check non-root users

```bash
# Backend
docker compose exec backend whoami
# Expected: appuser

# Frontend
docker compose exec frontend whoami
# Expected: nextjs

# MCP Server
docker compose exec mcp-server whoami
# Expected: mcp
```

### Check health status

```bash
docker compose ps --format "table {{.Name}}\t{{.Status}}"
```

### Run vulnerability scan locally

```bash
# Using Trivy
trivy image residency-scheduler-backend:latest
trivy image residency-scheduler-frontend:latest

# Using Docker Scout
docker scout cves residency-scheduler-backend:latest
```

---

## Related Documentation

- [DOCKER_WORKAROUNDS.md](../development/DOCKER_WORKAROUNDS.md) - Troubleshooting build failures
- [DOCKER_GORDON_RESEARCH.md](../planning/DOCKER_GORDON_RESEARCH.md) - Docker AI Assistant evaluation
- [Gordon Evaluation Findings](../planning/research/GORDON_EVALUATION_RESULTS.md) - Review accuracy assessment
- [Security Workflow](.github/workflows/security.yml) - CI/CD security scanning
