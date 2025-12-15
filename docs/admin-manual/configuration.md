# System Configuration Guide

## Overview

This guide covers all configuration options for the Residency Scheduler application, including environment variables, application settings, and runtime configuration.

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [Backend Configuration](#backend-configuration)
3. [Frontend Configuration](#frontend-configuration)
4. [Database Configuration](#database-configuration)
5. [Docker Configuration](#docker-configuration)
6. [CORS Configuration](#cors-configuration)
7. [Logging Configuration](#logging-configuration)
8. [ACGME Settings](#acgme-settings)
9. [Scheduling Engine Settings](#scheduling-engine-settings)

---

## Environment Variables

### Overview

The application uses environment variables for configuration, which can be set via:

1. `.env` file in the project root
2. System environment variables
3. Docker Compose environment section
4. Container orchestration secrets

### Primary Configuration File

Create `.env` from the provided template:

```bash
cp .env.example .env
```

### Complete Environment Variable Reference

#### Database Configuration

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `DB_PASSWORD` | Yes | - | PostgreSQL password |
| `DATABASE_URL` | No | Constructed | Full database connection URL |

```bash
# Simple configuration
DB_PASSWORD=your_secure_database_password

# Or full URL (overrides DB_PASSWORD)
DATABASE_URL=postgresql://scheduler:password@localhost:5432/residency_scheduler
```

**Database URL Format:**
```
postgresql://[user]:[password]@[host]:[port]/[database]
```

#### Security Configuration

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `SECRET_KEY` | Yes | - | JWT signing key (min 64 chars) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | 1440 | Token expiration (minutes) |

```bash
# Generate secure key
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Example configuration
SECRET_KEY=your_64_character_minimum_secret_key_for_jwt_signing_here
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

#### Application Configuration

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `DEBUG` | No | false | Enable debug mode |
| `APP_NAME` | No | Residency Scheduler | Application name |
| `APP_VERSION` | No | 1.0.0 | Application version |

```bash
# Production
DEBUG=false

# Development
DEBUG=true
```

#### CORS Configuration

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `CORS_ORIGINS` | No | ["http://localhost:3000"] | Allowed origins (JSON array) |

```bash
# Single origin
CORS_ORIGINS=["https://scheduler.hospital.org"]

# Multiple origins
CORS_ORIGINS=["https://scheduler.hospital.org","https://admin.hospital.org"]

# Development (allow localhost)
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

#### Frontend Configuration

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | http://localhost:8000 | Backend API URL |

```bash
# Production
NEXT_PUBLIC_API_URL=https://api.scheduler.hospital.org

# Development
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Environment-Specific Configurations

#### Production `.env`

```bash
# =============================================================================
# Production Configuration
# =============================================================================

# Database
DB_PASSWORD=<strong-randomly-generated-password>

# Security (CRITICAL: Use unique values)
SECRET_KEY=<64-char-cryptographically-secure-random-string>
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Application
DEBUG=false

# CORS
CORS_ORIGINS=["https://scheduler.hospital.org"]

# Frontend
NEXT_PUBLIC_API_URL=https://api.scheduler.hospital.org
```

#### Development `.env`

```bash
# =============================================================================
# Development Configuration
# =============================================================================

# Database
DB_PASSWORD=devpassword123

# Security
SECRET_KEY=dev-secret-key-not-for-production-use-only-in-development
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Application
DEBUG=true

# CORS
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Backend Configuration

### Configuration File Location

`backend/app/core/config.py`

### Settings Class

```python
class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Residency Scheduler"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://scheduler:scheduler@localhost:5432/residency_scheduler"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True
```

### Extending Configuration

To add new settings:

1. Add the variable to the `Settings` class
2. Set default value (optional)
3. Add to `.env.example`
4. Document in this guide

```python
# Example: Adding a new setting
class Settings(BaseSettings):
    # ... existing settings ...

    # New setting
    MAX_UPLOAD_SIZE_MB: int = 10
    ENABLE_NOTIFICATIONS: bool = True
```

---

## Frontend Configuration

### Configuration Files

| File | Purpose | Git Tracked |
|------|---------|:-----------:|
| `.env` | Default values | Yes |
| `.env.local` | Local overrides | No |
| `.env.production` | Production values | No |

### Next.js Environment Variables

Variables prefixed with `NEXT_PUBLIC_` are available in the browser:

```bash
# Available in browser JavaScript
NEXT_PUBLIC_API_URL=https://api.example.com

# Server-side only (not exposed to browser)
API_SECRET_KEY=server-only-secret
```

### Runtime Configuration

For values that need to change at runtime, use the API or a configuration endpoint:

```typescript
// frontend/src/lib/config.ts
export const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  appName: process.env.NEXT_PUBLIC_APP_NAME || 'Residency Scheduler',
}
```

---

## Database Configuration

### PostgreSQL Settings

#### Connection Pool Settings

In `backend/app/db/session.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,           # Base number of connections
    max_overflow=10,       # Additional connections when pool is full
    pool_timeout=30,       # Seconds to wait for connection
    pool_recycle=1800,     # Recycle connections after 30 minutes
    pool_pre_ping=True,    # Verify connections before use
)
```

#### PostgreSQL Tuning

For production, tune PostgreSQL in `postgresql.conf`:

```ini
# Memory Settings
shared_buffers = 2GB                    # 25% of available RAM
effective_cache_size = 6GB              # 75% of available RAM
work_mem = 256MB                        # Per-operation memory
maintenance_work_mem = 512MB            # Maintenance operations

# Connection Settings
max_connections = 100                   # Maximum concurrent connections
listen_addresses = 'localhost'          # Security: bind to localhost only

# Write Performance
wal_buffers = 64MB
checkpoint_completion_target = 0.9

# Query Planning
random_page_cost = 1.1                  # For SSD storage
effective_io_concurrency = 200          # For SSD storage
```

---

## Docker Configuration

### Docker Compose Configuration

#### Production (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: scheduler
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: residency_scheduler
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U scheduler"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://scheduler:${DB_PASSWORD}@db:5432/residency_scheduler
      SECRET_KEY: ${SECRET_KEY}
      DEBUG: "false"
      CORS_ORIGINS: ${CORS_ORIGINS}
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    restart: unless-stopped
    depends_on:
      - backend
    environment:
      NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL}
    ports:
      - "3000:3000"

volumes:
  postgres_data:
```

#### Development (`docker-compose.dev.yml`)

```yaml
version: '3.8'

services:
  db:
    ports:
      - "5432:5432"  # Expose database for local tools

  backend:
    volumes:
      - ./backend:/app  # Mount source for hot reload
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    environment:
      DEBUG: "true"

  frontend:
    volumes:
      - ./frontend:/app
      - /app/node_modules  # Don't override node_modules
    command: npm run dev
```

### Resource Limits

For production, set resource limits:

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
```

---

## CORS Configuration

### Understanding CORS

Cross-Origin Resource Sharing (CORS) controls which domains can make API requests.

### Configuration Options

```bash
# Single origin (most secure)
CORS_ORIGINS=["https://scheduler.hospital.org"]

# Multiple origins
CORS_ORIGINS=["https://scheduler.hospital.org","https://mobile.hospital.org"]

# Allow all origins (NOT RECOMMENDED for production)
CORS_ORIGINS=["*"]
```

### Backend CORS Implementation

In `backend/app/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],  # For file downloads
)
```

---

## Logging Configuration

### Backend Logging

#### Log Levels

| Level | Use Case |
|-------|----------|
| DEBUG | Detailed diagnostic information |
| INFO | General operational information |
| WARNING | Unexpected situations that aren't errors |
| ERROR | Errors that need attention |
| CRITICAL | System failures |

#### Configuration

Create `backend/logging_config.py`:

```python
import logging
import sys

def setup_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/var/log/residency-scheduler/app.log'),
        ]
    )

    # Reduce noise from third-party libraries
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('uvicorn').setLevel(logging.INFO)
```

### Structured Logging (Production)

For production, consider JSON logging:

```python
import json
import logging

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_record)
```

---

## ACGME Settings

### Compliance Configuration

The scheduling engine enforces ACGME rules. Configure thresholds:

```python
# backend/app/scheduling/config.py

ACGME_SETTINGS = {
    # Maximum weekly hours (averaged over 4 weeks)
    "max_weekly_hours": 80,

    # Averaging period for weekly hours
    "averaging_period_weeks": 4,

    # Minimum day off per week
    "days_off_per_week": 1,

    # Day off checking period
    "day_off_period_days": 7,

    # Maximum continuous duty hours
    "max_continuous_duty_hours": 24,

    # Maximum consecutive night shifts
    "max_consecutive_nights": 6,

    # Supervision ratios by PGY level
    "supervision_ratios": {
        "PGY1": 2,   # 1 faculty per 2 PGY-1 residents
        "PGY2": 4,   # 1 faculty per 4 PGY-2 residents
        "PGY3": 4,   # 1 faculty per 4 PGY-3 residents
    },

    # Violation severity levels
    "violation_severity": {
        "max_weekly_hours": "CRITICAL",
        "day_off": "HIGH",
        "continuous_duty": "CRITICAL",
        "supervision": "HIGH",
    }
}
```

### Override Configuration

For emergency situations, compliance overrides can be enabled:

```python
OVERRIDE_SETTINGS = {
    # Allow overrides (requires justification)
    "allow_overrides": True,

    # Roles that can approve overrides
    "override_approvers": ["admin", "coordinator"],

    # Require written justification
    "require_justification": True,

    # Log all overrides to audit trail
    "audit_overrides": True,
}
```

---

## Scheduling Engine Settings

### Algorithm Configuration

```python
# backend/app/scheduling/config.py

SCHEDULING_SETTINGS = {
    # Algorithm selection
    "algorithm": "greedy_constraint_satisfaction",

    # Maximum iterations for optimization
    "max_iterations": 10000,

    # Timeout in seconds
    "timeout_seconds": 300,

    # Priority weights for optimization
    "weights": {
        "coverage": 1.0,      # Fill all required slots
        "fairness": 0.8,      # Balance workload
        "preferences": 0.5,   # Honor preferences
        "continuity": 0.3,    # Keep assignments together
    },

    # Block configuration
    "blocks_per_day": 2,  # AM and PM blocks
    "days_per_year": 365,

    # Capacity limits
    "max_residents_per_block": 10,
    "max_faculty_per_block": 5,
}
```

### Rotation Template Defaults

```python
ROTATION_DEFAULTS = {
    # Default rotation duration
    "default_duration_weeks": 4,

    # Minimum notice for schedule changes
    "minimum_notice_days": 14,

    # Academic year boundaries
    "academic_year_start_month": 7,  # July
    "academic_year_start_day": 1,
}
```

---

## Configuration Best Practices

### Security

1. **Never commit secrets:** Add `.env` to `.gitignore`
2. **Use strong keys:** Generate cryptographically secure keys
3. **Rotate credentials:** Change passwords and keys periodically
4. **Limit exposure:** Use environment-specific configurations

### Performance

1. **Connection pooling:** Configure appropriate pool sizes
2. **Caching:** Enable query caching where appropriate
3. **Resource limits:** Set Docker resource constraints

### Maintainability

1. **Document changes:** Update this guide when adding settings
2. **Use defaults:** Provide sensible defaults for optional settings
3. **Validate early:** Check configuration on startup
4. **Environment parity:** Keep dev/staging/prod configs similar

---

## Configuration Checklist

Before deployment, verify:

- [ ] `SECRET_KEY` is unique and secure
- [ ] `DB_PASSWORD` is strong and unique
- [ ] `DEBUG` is `false` in production
- [ ] `CORS_ORIGINS` is properly restricted
- [ ] Database connection pool is configured
- [ ] Logging is configured for production
- [ ] Resource limits are set
- [ ] SSL/TLS is enabled
- [ ] ACGME settings match your requirements

---

*Last Updated: December 2024*
