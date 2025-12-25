# Container Security Reference

Security hardening patterns for Docker containers in healthcare/military environments.

## Security Checklist

### Dockerfile Security

| Check | Pattern | Priority |
|-------|---------|----------|
| Non-root user | `USER appuser` | CRITICAL |
| Minimal base image | `python:3.12-slim` or `alpine` | HIGH |
| No secrets in build | Use runtime secrets | CRITICAL |
| Pinned versions | `FROM python:3.12.1-slim` | HIGH |
| Read-only filesystem | `read_only: true` | MEDIUM |
| No privilege escalation | `no-new-privileges:true` | HIGH |

### Docker Compose Security

```yaml
services:
  backend:
    # Run as non-root user
    user: "1000:1000"

    # Prevent privilege escalation
    security_opt:
      - no-new-privileges:true

    # Read-only root filesystem
    read_only: true

    # Limit writeable areas
    tmpfs:
      - /tmp
      - /var/run

    # Resource limits (prevent DoS)
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 1G

    # Drop all capabilities, add only needed ones
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Only if binding to ports < 1024
```

## Secrets Management

### NEVER Do This

```yaml
# VULNERABLE: Secrets in environment
services:
  backend:
    environment:
      DATABASE_PASSWORD: super_secret_password  # VISIBLE in `docker inspect`
      SECRET_KEY: my_secret_key
```

### Do This Instead

```yaml
# SECURE: Use Docker secrets
services:
  backend:
    secrets:
      - db_password
      - secret_key
    environment:
      DATABASE_PASSWORD_FILE: /run/secrets/db_password
      SECRET_KEY_FILE: /run/secrets/secret_key

secrets:
  db_password:
    external: true  # Created with: docker secret create db_password ./password.txt
  secret_key:
    external: true
```

### Reading Secrets in Application

```python
# app/core/config.py
import os
from pathlib import Path

def get_secret(name: str, env_var: str) -> str:
    """Read secret from file (Docker secrets) or environment variable."""
    # Try Docker secrets first
    secret_file = os.environ.get(f"{env_var}_FILE")
    if secret_file:
        secret_path = Path(secret_file)
        if secret_path.exists():
            return secret_path.read_text().strip()

    # Fall back to environment variable
    value = os.environ.get(env_var)
    if not value:
        raise ValueError(f"Secret {name} not found in file or environment")
    return value

# Usage
DATABASE_PASSWORD = get_secret("database password", "DATABASE_PASSWORD")
SECRET_KEY = get_secret("secret key", "SECRET_KEY")
```

## Network Security

### Internal Networks

```yaml
# Production: Backend services not exposed to internet
networks:
  frontend-network:
    driver: bridge  # Accessible from host

  backend-network:
    driver: bridge
    internal: true  # NO external access

services:
  frontend:
    networks:
      - frontend-network
      - backend-network  # Can reach backend

  backend:
    networks:
      - backend-network  # Only reachable internally

  db:
    networks:
      - backend-network  # Never exposed externally
```

### Restricting Container Network Access

```yaml
# Container that should not reach the internet
services:
  backend:
    network_mode: none  # Complete isolation
    # OR
    networks:
      - internal-only

networks:
  internal-only:
    internal: true
```

## Image Vulnerability Scanning

### Trivy (Recommended)

```bash
# Scan image for vulnerabilities
trivy image ghcr.io/org/backend:latest

# Scan with severity filter
trivy image --severity CRITICAL,HIGH ghcr.io/org/backend:latest

# Scan Dockerfile (IaC scanning)
trivy config ./Dockerfile

# Scan as part of CI
trivy image --exit-code 1 --severity CRITICAL ghcr.io/org/backend:latest
```

### Docker Scout

```bash
# Analyze image
docker scout cves ghcr.io/org/backend:latest

# Quick recommendations
docker scout recommendations ghcr.io/org/backend:latest
```

### Hadolint (Dockerfile Linting)

```bash
# Lint Dockerfile for security issues
docker run --rm -i hadolint/hadolint < Dockerfile

# Common security rules:
# DL3002 - Last USER should not be root
# DL3003 - Use WORKDIR to switch directories
# DL3006 - Always tag the version of an image explicitly
# DL3008 - Pin versions in apt get install
# DL3009 - Delete apt-get lists after installing
```

## HIPAA Considerations for Containers

### PHI Data Handling

1. **Never mount PHI data directly** - Use encrypted volumes
2. **Audit logging** - All container access logged
3. **Encryption at rest** - Database volumes must be encrypted
4. **Network encryption** - TLS between all services

### Volume Encryption

```yaml
# Use encrypted driver for sensitive data
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: 'none'
      o: 'bind'
      device: '/encrypted/postgres'  # Host path on encrypted filesystem
```

### Audit Logging

```yaml
services:
  backend:
    logging:
      driver: json-file
      options:
        max-size: "100m"
        max-file: "10"
        labels: "service,environment"
    labels:
      service: "backend"
      environment: "production"
      compliance: "hipaa"
```

## Common Security Vulnerabilities

### 1. Exposed Docker Socket

```yaml
# VULNERABLE: Gives container full host control
volumes:
  - /var/run/docker.sock:/var/run/docker.sock

# AVOID unless absolutely necessary (e.g., CI runners)
```

### 2. Privileged Mode

```yaml
# VULNERABLE: Container has full host privileges
privileged: true

# NEVER use in production
```

### 3. Host Network Mode

```yaml
# RISKY: Container shares host network
network_mode: host

# Only use for specific debugging scenarios
```

### 4. Writable Sensitive Mounts

```yaml
# VULNERABLE: Container can modify host files
volumes:
  - /etc:/etc

# If mounting host files, use read-only
volumes:
  - /etc/localtime:/etc/localtime:ro
```

## Security Hardened Dockerfile Template

```dockerfile
# syntax=docker/dockerfile:1.4

# Stage 1: Build
FROM python:3.12-slim AS builder

# Security: Don't run apt as interactive
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and use virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

# Security: Metadata
LABEL org.opencontainers.image.title="Backend API"
LABEL org.opencontainers.image.vendor="Residency Scheduler"
LABEL org.opencontainers.image.licenses="Proprietary"

# Security: Don't run as root
RUN groupadd -r -g 1001 appgroup \
    && useradd -r -u 1001 -g appgroup appuser

# Runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /var/cache/apt/archives/*

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appgroup app/ ./app/

# Security: Switch to non-root user
USER appuser

# Security: Don't store Python bytecode
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Health check for orchestrator
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Security: Use exec form to prevent shell injection
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Compliance Verification Script

```bash
#!/bin/bash
# check-container-security.sh

IMAGE=$1

echo "=== Container Security Check: $IMAGE ==="

# Check if running as root
echo -n "Non-root user: "
USER=$(docker run --rm --entrypoint whoami $IMAGE 2>/dev/null)
if [ "$USER" != "root" ]; then
    echo "PASS ($USER)"
else
    echo "FAIL (running as root)"
fi

# Check for secrets in environment
echo -n "No hardcoded secrets: "
SECRETS=$(docker inspect $IMAGE | grep -iE "(password|secret|key).*=.*[a-zA-Z0-9]" | wc -l)
if [ "$SECRETS" -eq 0 ]; then
    echo "PASS"
else
    echo "WARNING (found $SECRETS potential secrets)"
fi

# Check image size
echo -n "Image size: "
SIZE=$(docker image inspect $IMAGE --format='{{.Size}}' | numfmt --to=iec)
echo "$SIZE"

# Run Trivy scan
echo "=== Vulnerability Scan ==="
trivy image --severity HIGH,CRITICAL $IMAGE

echo "=== Security Check Complete ==="
```
