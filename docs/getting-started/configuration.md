# Configuration

Complete reference for all configuration options.

---

## Environment Variables

### Application Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application display name | `Residency Scheduler` |
| `APP_VERSION` | Application version | `1.0.0` |
| `DEBUG` | Enable debug mode | `false` |

### Database Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | Full PostgreSQL connection URL | Yes |
| `DB_PASSWORD` | Database password | Yes |
| `DB_POOL_SIZE` | Connection pool size | `10` |
| `DB_MAX_OVERFLOW` | Max overflow connections | `20` |

!!! warning "Production Security"
    Always use strong, unique passwords in production. Generate with:
    ```bash
    openssl rand -base64 32
    ```

### Security Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | JWT signing key (64+ chars) | Yes |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | `1440` |
| `CORS_ORIGINS` | Allowed origins (JSON array) | `["http://localhost:3000"]` |
| `TRUSTED_HOSTS` | Allowed host headers | `[]` |

### Redis & Celery

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery message broker | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery result storage | `redis://localhost:6379/0` |

### Frontend Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

---

## Resilience Framework Settings

The resilience framework monitors system health and prevents overload.

| Variable | Description | Default |
|----------|-------------|---------|
| `RESILIENCE_UTILIZATION_WARNING` | Warning threshold | `0.75` |
| `RESILIENCE_UTILIZATION_CRITICAL` | Critical threshold | `0.85` |
| `RESILIENCE_UTILIZATION_EMERGENCY` | Emergency threshold | `0.95` |
| `CONTINGENCY_CHECK_INTERVAL_HOURS` | Analysis frequency | `4` |
| `MAX_CONTINGENCY_SCENARIOS` | Scenarios to analyze | `100` |

---

## Rate Limiting

| Variable | Description | Default |
|----------|-------------|---------|
| `RATE_LIMIT_LOGIN_ATTEMPTS` | Login attempts per window | `5` |
| `RATE_LIMIT_LOGIN_WINDOW` | Window duration (seconds) | `60` |
| `RATE_LIMIT_REGISTER_ATTEMPTS` | Register attempts per window | `3` |
| `RATE_LIMIT_REGISTER_WINDOW` | Window duration (seconds) | `60` |

---

## Sample Configuration

### Development

```env title=".env"
# Application
DEBUG=true
APP_NAME=Residency Scheduler (Dev)

# Database
DATABASE_URL=postgresql://postgres:devpass@localhost:5432/residency_scheduler

# Security
SECRET_KEY=dev-secret-key-not-for-production-use-only-for-development
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CORS (allow all localhost)
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# Redis
REDIS_URL=redis://localhost:6379/0

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Production

```env title=".env.prod"
# Application
DEBUG=false
APP_NAME=Residency Scheduler

# Database
DATABASE_URL=postgresql://prod_user:${DB_PASSWORD}@db.example.com:5432/residency_prod

# Security (generate with: openssl rand -hex 32)
SECRET_KEY=your-production-secret-key-64-characters-minimum-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440
TRUSTED_HOSTS=["scheduler.example.com"]

# CORS
CORS_ORIGINS=["https://scheduler.example.com"]

# Redis
REDIS_URL=redis://:${REDIS_PASSWORD}@redis.example.com:6379/0

# Frontend
NEXT_PUBLIC_API_URL=https://api.scheduler.example.com
```

---

## Docker Compose Override

For environment-specific configurations:

```yaml title="docker-compose.override.yml"
version: "3.8"

services:
  backend:
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    volumes:
      - ./backend:/app  # Hot reload

  frontend:
    environment:
      - NODE_ENV=development
    volumes:
      - ./frontend:/app
      - /app/node_modules
```

---

## Configuration Validation

Check your configuration:

```bash
# Backend health check
curl http://localhost:8000/health

# Expected response
{"status": "healthy"}
```

See [Troubleshooting](../troubleshooting.md) if health checks fail.
