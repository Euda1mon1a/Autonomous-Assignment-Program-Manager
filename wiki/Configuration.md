***REMOVED*** Configuration

This document describes all configuration options for Residency Scheduler.

---

***REMOVED******REMOVED*** Environment Variables

Create a `.env` file in the project root from the template:

```bash
cp .env.example .env
```

---

***REMOVED******REMOVED*** Required Settings

***REMOVED******REMOVED******REMOVED*** Database Configuration

```env
***REMOVED*** PostgreSQL password (required)
DB_PASSWORD=your_secure_password_here

***REMOVED*** Full database connection URL
DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@localhost:5432/residency_scheduler
```

***REMOVED******REMOVED******REMOVED*** Security Settings

```env
***REMOVED*** JWT signing key - REQUIRED (no default in production)
***REMOVED*** Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'
***REMOVED*** Minimum 32 characters, recommended 64+ characters
***REMOVED*** Application will FAIL to start in production if this is empty or uses default
SECRET_KEY=your_64_character_random_secret_key_here

***REMOVED*** Webhook signature verification key - REQUIRED (no default in production)
***REMOVED*** Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'
WEBHOOK_SECRET=your_webhook_secret_key_here

***REMOVED*** Token expiration in minutes (default: 1440 = 24 hours)
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

> **Security Note**: In production mode (`DEBUG=false`), the application validates that `SECRET_KEY` and `WEBHOOK_SECRET` are set and not using default/placeholder values. Startup will fail with a clear error message if validation fails.

***REMOVED******REMOVED******REMOVED*** Frontend Configuration

```env
***REMOVED*** Backend API URL for frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

***REMOVED******REMOVED*** Application Settings

```env
***REMOVED*** Application name
APP_NAME=Residency Scheduler

***REMOVED*** Version string
APP_VERSION=1.0.0

***REMOVED*** Debug mode (set to false in production)
DEBUG=false
```

---

***REMOVED******REMOVED*** Network & CORS

```env
***REMOVED*** Allowed CORS origins (JSON array)
CORS_ORIGINS=["http://localhost:3000", "https://your-domain.com"]

***REMOVED*** Trusted hosts for production (prevents host header attacks)
TRUSTED_HOSTS=["localhost", "your-domain.com"]
```

---

***REMOVED******REMOVED*** Redis & Celery

```env
***REMOVED*** Redis connection URL
REDIS_URL=redis://localhost:6379/0

***REMOVED*** Redis password - REQUIRED for production
***REMOVED*** Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'
REDIS_PASSWORD=your_redis_password_here

***REMOVED*** Celery broker URL (password automatically embedded from REDIS_PASSWORD)
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@localhost:6379/0

***REMOVED*** Celery result backend
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@localhost:6379/0
```

> **Security Note**: Redis now requires password authentication. The application automatically constructs authenticated Redis URLs using `REDIS_PASSWORD`.

---

***REMOVED******REMOVED*** Database Connection Pooling

Fine-tune database connections for your workload:

```env
***REMOVED*** Number of connections to keep in the pool (default: 10)
DB_POOL_SIZE=10

***REMOVED*** Maximum overflow connections above pool_size (default: 20)
DB_POOL_MAX_OVERFLOW=20

***REMOVED*** Seconds to wait for a connection from the pool (default: 30)
DB_POOL_TIMEOUT=30

***REMOVED*** Recycle connections after this many seconds (default: 1800)
DB_POOL_RECYCLE=1800

***REMOVED*** Test connections before using them (default: true)
DB_POOL_PRE_PING=true
```

***REMOVED******REMOVED******REMOVED*** Pool Size Guidelines

| Application Size | `DB_POOL_SIZE` | `DB_POOL_MAX_OVERFLOW` |
|-----------------|----------------|------------------------|
| Small (< 10 users) | 5 | 10 |
| Medium (10-100 users) | 10 | 20 |
| Large (100+ users) | 20 | 40 |

---

***REMOVED******REMOVED*** Resilience Framework

Configure the resilience system thresholds:

```env
***REMOVED*** Defense level thresholds (0.0 - 1.0)
***REMOVED*** GREEN → YELLOW transition (default: 0.70)
RESILIENCE_WARNING_THRESHOLD=0.70

***REMOVED*** YELLOW → ORANGE transition (default: 0.80)
RESILIENCE_MAX_UTILIZATION=0.80

***REMOVED*** ORANGE → RED transition (default: 0.90)
RESILIENCE_CRITICAL_THRESHOLD=0.90

***REMOVED*** RED → BLACK transition (default: 0.95)
RESILIENCE_EMERGENCY_THRESHOLD=0.95
```

***REMOVED******REMOVED******REMOVED*** Automatic Responses

```env
***REMOVED*** Automatically activate defense protocols (default: true)
RESILIENCE_AUTO_ACTIVATE_DEFENSE=true

***REMOVED*** Automatically switch to fallback schedules (default: false)
RESILIENCE_AUTO_ACTIVATE_FALLBACK=false

***REMOVED*** Automatically shed load when overutilized (default: false)
RESILIENCE_AUTO_SHED_LOAD=false
```

***REMOVED******REMOVED******REMOVED*** Health Check Intervals

```env
***REMOVED*** How often to run health checks in minutes (default: 15)
RESILIENCE_HEALTH_CHECK_INTERVAL_MINUTES=15

***REMOVED*** How often to run contingency analysis in hours (default: 24)
RESILIENCE_CONTINGENCY_ANALYSIS_INTERVAL_HOURS=24
```

***REMOVED******REMOVED******REMOVED*** Alerting

```env
***REMOVED*** Email recipients for resilience alerts (comma-separated)
RESILIENCE_ALERT_RECIPIENTS=admin@example.com,coordinator@example.com

***REMOVED*** Slack channel for alerts (if using n8n integration)
RESILIENCE_SLACK_CHANNEL=***REMOVED***residency-alerts
```

---

***REMOVED******REMOVED*** ACGME Compliance Settings

These are typically configured in the database but can have defaults:

```env
***REMOVED*** Maximum weekly hours (averaged over 4 weeks)
ACGME_MAX_WEEKLY_HOURS=80

***REMOVED*** Maximum continuous duty hours
ACGME_MAX_CONTINUOUS_HOURS=24

***REMOVED*** Required days off per week
ACGME_DAYS_OFF_PER_WEEK=1

***REMOVED*** Supervision ratios (faculty:residents)
ACGME_SUPERVISION_PGY1=0.5    ***REMOVED*** 1:2 ratio
ACGME_SUPERVISION_PGY2_3=0.25  ***REMOVED*** 1:4 ratio
```

---

***REMOVED******REMOVED*** Email Configuration

```env
***REMOVED*** SMTP server settings
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=notifications@example.com
SMTP_PASSWORD=your_smtp_password
SMTP_FROM_EMAIL=noreply@example.com
SMTP_FROM_NAME=Residency Scheduler

***REMOVED*** Use TLS (default: true)
SMTP_TLS=true
```

---

***REMOVED******REMOVED*** Logging

```env
***REMOVED*** Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

***REMOVED*** Log format: json or text
LOG_FORMAT=json

***REMOVED*** Log file path (optional, uses stdout if not set)
LOG_FILE=/var/log/residency-scheduler/app.log
```

---

***REMOVED******REMOVED*** Monitoring (Sentry)

```env
***REMOVED*** Sentry DSN for error tracking (optional)
SENTRY_DSN=https://key@sentry.io/project

***REMOVED*** Environment name for Sentry
SENTRY_ENVIRONMENT=production

***REMOVED*** Sample rate for performance monitoring (0.0 - 1.0)
SENTRY_TRACES_SAMPLE_RATE=0.1
```

---

***REMOVED******REMOVED*** Docker Configuration

***REMOVED******REMOVED******REMOVED*** Docker Compose Environment

For Docker deployments, set variables in `docker-compose.yml` or use an `.env` file:

```yaml
services:
  backend:
    environment:
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/residency_scheduler
      - SECRET_KEY=${SECRET_KEY}
      - REDIS_URL=redis://redis:6379/0
```

***REMOVED******REMOVED******REMOVED*** Production Docker Settings

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

***REMOVED******REMOVED*** Configuration Files

***REMOVED******REMOVED******REMOVED*** Backend Configuration

Located at `backend/app/core/config.py`:

```python
class Settings(BaseSettings):
    ***REMOVED*** All settings are loaded from environment variables
    ***REMOVED*** with defaults defined in the class

    APP_NAME: str = "Residency Scheduler"
    DEBUG: bool = False
    SECRET_KEY: str  ***REMOVED*** Required, no default

    class Config:
        env_file = ".env"
```

***REMOVED******REMOVED******REMOVED*** Frontend Configuration

Located at `frontend/next.config.js`:

```javascript
module.exports = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
  // Additional Next.js configuration
}
```

---

***REMOVED******REMOVED*** Configuration by Environment

***REMOVED******REMOVED******REMOVED*** Development

```env
DEBUG=true
LOG_LEVEL=DEBUG
CORS_ORIGINS=["http://localhost:3000"]
DATABASE_URL=postgresql://postgres:devpassword@localhost:5432/residency_dev
```

***REMOVED******REMOVED******REMOVED*** Staging

```env
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=["https://staging.your-domain.com"]
DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/residency_staging
SENTRY_ENVIRONMENT=staging
```

***REMOVED******REMOVED******REMOVED*** Production

```env
DEBUG=false
LOG_LEVEL=WARNING
CORS_ORIGINS=["https://your-domain.com"]
TRUSTED_HOSTS=["your-domain.com"]
DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/residency_prod
SENTRY_ENVIRONMENT=production
DB_POOL_SIZE=20
DB_POOL_MAX_OVERFLOW=40
```

---

***REMOVED******REMOVED*** Nginx Configuration

For production deployments with Nginx:

```nginx
***REMOVED*** nginx/nginx.conf

upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:3000;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;

    ***REMOVED*** Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    location /api {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

***REMOVED******REMOVED*** Monitoring Services

```env
***REMOVED*** N8N workflow automation password - REQUIRED (no default)
N8N_PASSWORD=your_secure_n8n_password

***REMOVED*** Grafana admin password - REQUIRED (no default)
GRAFANA_ADMIN_PASSWORD=your_secure_grafana_password
```

> **Security Note**: Default passwords for N8N and Grafana have been removed. These services will fail to start without explicit password configuration.

---

***REMOVED******REMOVED*** Secrets Management

***REMOVED******REMOVED******REMOVED*** Best Practices

1. **Never commit secrets** to version control
2. **Use environment variables** for all sensitive data
3. **Rotate secrets regularly**, especially `SECRET_KEY`
4. **Use different secrets** for each environment
5. **Never use default/placeholder secrets** in production

***REMOVED******REMOVED******REMOVED*** Required Secrets (No Defaults Allowed)

| Secret | Purpose | Generation Command |
|--------|---------|-------------------|
| `SECRET_KEY` | JWT token signing | `python -c 'import secrets; print(secrets.token_urlsafe(32))'` |
| `WEBHOOK_SECRET` | Webhook HMAC verification | `python -c 'import secrets; print(secrets.token_urlsafe(32))'` |
| `REDIS_PASSWORD` | Redis authentication | `python -c 'import secrets; print(secrets.token_urlsafe(32))'` |
| `N8N_PASSWORD` | N8N admin access | `python -c 'import secrets; print(secrets.token_urlsafe(16))'` |
| `GRAFANA_ADMIN_PASSWORD` | Grafana admin access | `python -c 'import secrets; print(secrets.token_urlsafe(16))'` |
| `DB_PASSWORD` | Database authentication | `openssl rand -base64 24` |

***REMOVED******REMOVED******REMOVED*** Generating Secrets

```bash
***REMOVED*** Generate a secure SECRET_KEY (64 characters)
python -c 'import secrets; print(secrets.token_urlsafe(32))'

***REMOVED*** Alternative using openssl
openssl rand -hex 32

***REMOVED*** Generate a database password
openssl rand -base64 24
```

***REMOVED******REMOVED******REMOVED*** Using Docker Secrets (Swarm)

```yaml
services:
  backend:
    secrets:
      - db_password
      - secret_key

secrets:
  db_password:
    external: true
  secret_key:
    external: true
```

---

***REMOVED******REMOVED*** Validation

***REMOVED******REMOVED******REMOVED*** Check Configuration

```bash
***REMOVED*** Backend - validate settings
cd backend
python -c "from app.core.config import settings; print(settings)"

***REMOVED*** Check database connection
python -c "from app.db.session import engine; engine.connect()"

***REMOVED*** Check Redis connection
python -c "import redis; r = redis.from_url('redis://localhost:6379'); r.ping()"
```

***REMOVED******REMOVED******REMOVED*** Health Endpoints

```bash
***REMOVED*** Basic health check
curl http://localhost:8000/health

***REMOVED*** Detailed health check
curl http://localhost:8000/health/ready
```

---

***REMOVED******REMOVED*** Troubleshooting Configuration

***REMOVED******REMOVED******REMOVED*** Common Issues

**Database connection failed:**
```
Error: Connection refused to localhost:5432
```
- Check `DATABASE_URL` is correct
- Ensure PostgreSQL is running
- Verify network connectivity in Docker

**Invalid SECRET_KEY:**
```
Error: SECRET_KEY must be at least 32 characters
```
- Generate a new key: `openssl rand -hex 32`
- Ensure no quotes around the value in `.env`

**CORS errors:**
```
Access-Control-Allow-Origin missing
```
- Add your frontend URL to `CORS_ORIGINS`
- Ensure it's a valid JSON array

**Redis connection failed:**
```
Error: Connection refused to localhost:6379
```
- Check Redis is running
- Verify `REDIS_URL` is correct

---

***REMOVED******REMOVED*** Related Documentation

- [Getting Started](Getting-Started) - Installation guide
- [Architecture](Architecture) - System design
- [Development](Development) - Contributing guide
