***REMOVED*** Container Security Reference

Security hardening patterns for Docker containers in healthcare/military environments.

***REMOVED******REMOVED*** Security Checklist

***REMOVED******REMOVED******REMOVED*** Dockerfile Security

| Check | Pattern | Priority |
|-------|---------|----------|
| Non-root user | `USER appuser` | CRITICAL |
| Minimal base image | `python:3.12-slim` or `alpine` | HIGH |
| No secrets in build | Use runtime secrets | CRITICAL |
| Pinned versions | `FROM python:3.12.1-slim` | HIGH |
| Read-only filesystem | `read_only: true` | MEDIUM |
| No privilege escalation | `no-new-privileges:true` | HIGH |

***REMOVED******REMOVED******REMOVED*** Docker Compose Security

```yaml
services:
  backend:
    ***REMOVED*** Run as non-root user
    user: "1000:1000"

    ***REMOVED*** Prevent privilege escalation
    security_opt:
      - no-new-privileges:true

    ***REMOVED*** Read-only root filesystem
    read_only: true

    ***REMOVED*** Limit writeable areas
    tmpfs:
      - /tmp
      - /var/run

    ***REMOVED*** Resource limits (prevent DoS)
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 1G

    ***REMOVED*** Drop all capabilities, add only needed ones
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  ***REMOVED*** Only if binding to ports < 1024
```

***REMOVED******REMOVED*** Secrets Management

***REMOVED******REMOVED******REMOVED*** NEVER Do This

```yaml
***REMOVED*** VULNERABLE: Secrets in environment
services:
  backend:
    environment:
      DATABASE_PASSWORD: super_secret_password  ***REMOVED*** VISIBLE in `docker inspect`
      SECRET_KEY: my_secret_key
```

***REMOVED******REMOVED******REMOVED*** Do This Instead

```yaml
***REMOVED*** SECURE: Use Docker secrets
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
    external: true  ***REMOVED*** Created with: docker secret create db_password ./password.txt
  secret_key:
    external: true
```

***REMOVED******REMOVED******REMOVED*** Reading Secrets in Application

```python
***REMOVED*** app/core/config.py
import os
from pathlib import Path

def get_secret(name: str, env_var: str) -> str:
    """Read secret from file (Docker secrets) or environment variable."""
    ***REMOVED*** Try Docker secrets first
    secret_file = os.environ.get(f"{env_var}_FILE")
    if secret_file:
        secret_path = Path(secret_file)
        if secret_path.exists():
            return secret_path.read_text().strip()

    ***REMOVED*** Fall back to environment variable
    value = os.environ.get(env_var)
    if not value:
        raise ValueError(f"Secret {name} not found in file or environment")
    return value

***REMOVED*** Usage
DATABASE_PASSWORD = get_secret("database password", "DATABASE_PASSWORD")
SECRET_KEY = get_secret("secret key", "SECRET_KEY")
```

***REMOVED******REMOVED*** Network Security

***REMOVED******REMOVED******REMOVED*** Internal Networks

```yaml
***REMOVED*** Production: Backend services not exposed to internet
networks:
  frontend-network:
    driver: bridge  ***REMOVED*** Accessible from host

  backend-network:
    driver: bridge
    internal: true  ***REMOVED*** NO external access

services:
  frontend:
    networks:
      - frontend-network
      - backend-network  ***REMOVED*** Can reach backend

  backend:
    networks:
      - backend-network  ***REMOVED*** Only reachable internally

  db:
    networks:
      - backend-network  ***REMOVED*** Never exposed externally
```

***REMOVED******REMOVED******REMOVED*** Restricting Container Network Access

```yaml
***REMOVED*** Container that should not reach the internet
services:
  backend:
    network_mode: none  ***REMOVED*** Complete isolation
    ***REMOVED*** OR
    networks:
      - internal-only

networks:
  internal-only:
    internal: true
```

***REMOVED******REMOVED*** Image Vulnerability Scanning

***REMOVED******REMOVED******REMOVED*** Trivy (Recommended)

```bash
***REMOVED*** Scan image for vulnerabilities
trivy image ghcr.io/org/backend:latest

***REMOVED*** Scan with severity filter
trivy image --severity CRITICAL,HIGH ghcr.io/org/backend:latest

***REMOVED*** Scan Dockerfile (IaC scanning)
trivy config ./Dockerfile

***REMOVED*** Scan as part of CI
trivy image --exit-code 1 --severity CRITICAL ghcr.io/org/backend:latest
```

***REMOVED******REMOVED******REMOVED*** Docker Scout

```bash
***REMOVED*** Analyze image
docker scout cves ghcr.io/org/backend:latest

***REMOVED*** Quick recommendations
docker scout recommendations ghcr.io/org/backend:latest
```

***REMOVED******REMOVED******REMOVED*** Hadolint (Dockerfile Linting)

```bash
***REMOVED*** Lint Dockerfile for security issues
docker run --rm -i hadolint/hadolint < Dockerfile

***REMOVED*** Common security rules:
***REMOVED*** DL3002 - Last USER should not be root
***REMOVED*** DL3003 - Use WORKDIR to switch directories
***REMOVED*** DL3006 - Always tag the version of an image explicitly
***REMOVED*** DL3008 - Pin versions in apt get install
***REMOVED*** DL3009 - Delete apt-get lists after installing
```

***REMOVED******REMOVED*** HIPAA Considerations for Containers

***REMOVED******REMOVED******REMOVED*** PHI Data Handling

1. **Never mount PHI data directly** - Use encrypted volumes
2. **Audit logging** - All container access logged
3. **Encryption at rest** - Database volumes must be encrypted
4. **Network encryption** - TLS between all services

***REMOVED******REMOVED******REMOVED*** Volume Encryption

```yaml
***REMOVED*** Use encrypted driver for sensitive data
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: 'none'
      o: 'bind'
      device: '/encrypted/postgres'  ***REMOVED*** Host path on encrypted filesystem
```

***REMOVED******REMOVED******REMOVED*** Audit Logging

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

***REMOVED******REMOVED*** Common Security Vulnerabilities

***REMOVED******REMOVED******REMOVED*** 1. Exposed Docker Socket

```yaml
***REMOVED*** VULNERABLE: Gives container full host control
volumes:
  - /var/run/docker.sock:/var/run/docker.sock

***REMOVED*** AVOID unless absolutely necessary (e.g., CI runners)
```

***REMOVED******REMOVED******REMOVED*** 2. Privileged Mode

```yaml
***REMOVED*** VULNERABLE: Container has full host privileges
privileged: true

***REMOVED*** NEVER use in production
```

***REMOVED******REMOVED******REMOVED*** 3. Host Network Mode

```yaml
***REMOVED*** RISKY: Container shares host network
network_mode: host

***REMOVED*** Only use for specific debugging scenarios
```

***REMOVED******REMOVED******REMOVED*** 4. Writable Sensitive Mounts

```yaml
***REMOVED*** VULNERABLE: Container can modify host files
volumes:
  - /etc:/etc

***REMOVED*** If mounting host files, use read-only
volumes:
  - /etc/localtime:/etc/localtime:ro
```

***REMOVED******REMOVED*** Security Hardened Dockerfile Template

```dockerfile
***REMOVED*** syntax=docker/dockerfile:1.4

***REMOVED*** Stage 1: Build
FROM python:3.12-slim AS builder

***REMOVED*** Security: Don't run apt as interactive
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

***REMOVED*** Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

***REMOVED*** Create and use virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

***REMOVED*** Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

***REMOVED*** Stage 2: Runtime
FROM python:3.12-slim AS runtime

***REMOVED*** Security: Metadata
LABEL org.opencontainers.image.title="Backend API"
LABEL org.opencontainers.image.vendor="Residency Scheduler"
LABEL org.opencontainers.image.licenses="Proprietary"

***REMOVED*** Security: Don't run as root
RUN groupadd -r -g 1001 appgroup \
    && useradd -r -u 1001 -g appgroup appuser

***REMOVED*** Runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /var/cache/apt/archives/*

WORKDIR /app

***REMOVED*** Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

***REMOVED*** Copy application code
COPY --chown=appuser:appgroup app/ ./app/

***REMOVED*** Security: Switch to non-root user
USER appuser

***REMOVED*** Security: Don't store Python bytecode
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

***REMOVED*** Health check for orchestrator
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

***REMOVED*** Security: Use exec form to prevent shell injection
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

***REMOVED******REMOVED*** Compliance Verification Script

```bash
***REMOVED***!/bin/bash
***REMOVED*** check-container-security.sh

IMAGE=$1

echo "=== Container Security Check: $IMAGE ==="

***REMOVED*** Check if running as root
echo -n "Non-root user: "
USER=$(docker run --rm --entrypoint whoami $IMAGE 2>/dev/null)
if [ "$USER" != "root" ]; then
    echo "PASS ($USER)"
else
    echo "FAIL (running as root)"
fi

***REMOVED*** Check for secrets in environment
echo -n "No hardcoded secrets: "
SECRETS=$(docker inspect $IMAGE | grep -iE "(password|secret|key).*=.*[a-zA-Z0-9]" | wc -l)
if [ "$SECRETS" -eq 0 ]; then
    echo "PASS"
else
    echo "WARNING (found $SECRETS potential secrets)"
fi

***REMOVED*** Check image size
echo -n "Image size: "
SIZE=$(docker image inspect $IMAGE --format='{{.Size}}' | numfmt --to=iec)
echo "$SIZE"

***REMOVED*** Run Trivy scan
echo "=== Vulnerability Scan ==="
trivy image --severity HIGH,CRITICAL $IMAGE

echo "=== Security Check Complete ==="
```
