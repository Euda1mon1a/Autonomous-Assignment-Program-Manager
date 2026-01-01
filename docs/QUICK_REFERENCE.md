# Quick Reference Guide

**Last Updated:** 2025-12-31

Fast reference for common operations in the Residency Scheduler system.

---

## Table of Contents

- [Common Commands](#common-commands)
- [API Endpoints](#api-endpoints)
- [Database Operations](#database-operations)
- [Troubleshooting](#troubleshooting)
- [Configuration](#configuration)

---

## Common Commands

### Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Restart service
docker-compose restart backend

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Schedule Generation

```bash
# Generate schedule via CLI
cd backend
python -m app.cli schedule generate \
  --start 2025-07-01 --end 2025-09-30 \
  --algorithm cp_sat

# Generate via API
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-07-01",
    "end_date": "2025-09-30",
    "algorithm": "cp_sat"
  }'
```

### ACGME Compliance Check

```bash
# CLI
python -m app.cli compliance check --verbose

# API
curl "http://localhost:8000/api/v1/compliance/validate?start_date=2025-07-01&end_date=2025-09-30"
```

### Backup & Restore

```bash
# Backup database
docker-compose exec db pg_dump -U scheduler residency_scheduler > backup.sql

# Restore database
docker-compose exec -T db psql -U scheduler residency_scheduler < backup.sql
```

---

## API Endpoints

### Authentication

```bash
# Login
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}

# Refresh token
POST /api/v1/auth/refresh
{
  "refresh_token": "..."
}
```

### Schedule Management

```bash
# Generate schedule
POST /api/v1/schedule/generate

# Validate schedule
GET /api/v1/compliance/validate?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD

# Export schedule
GET /api/v1/schedule/export?format=excel&start_date=YYYY-MM-DD
```

### People Management

```bash
# List people
GET /api/v1/people?type=resident&active=true

# Create person
POST /api/v1/people
{
  "name": "Doe, John",
  "email": "john@example.com",
  "type": "resident",
  "pgy_level": 2
}

# Update person
PUT /api/v1/people/{id}
{
  "pgy_level": 3
}
```

### Absences

```bash
# Create absence
POST /api/v1/absences
{
  "person_id": "...",
  "type": "vacation",
  "start_date": "2025-07-15",
  "end_date": "2025-07-22"
}

# Approve absence
POST /api/v1/absences/{id}/approve

# List absences
GET /api/v1/absences?start_date=2025-07-01&end_date=2025-07-31
```

### Swaps

```bash
# Execute swap
POST /api/v1/swaps/execute
{
  "source_faculty_id": "...",
  "source_week": "2025-07-08",
  "target_faculty_id": "...",
  "target_week": "2025-07-15",
  "swap_type": "one_to_one"
}

# Validate swap
POST /api/v1/swaps/validate

# Rollback swap
POST /api/v1/swaps/{id}/rollback
```

---

## Database Operations

### Connect to Database

```bash
# Via Docker
docker-compose exec db psql -U scheduler -d residency_scheduler

# Direct connection
psql postgresql://scheduler:password@localhost:5432/residency_scheduler
```

### Common Queries

```sql
-- Count assignments
SELECT COUNT(*) FROM assignments;

-- List residents
SELECT id, name, email, pgy_level
FROM persons
WHERE type = 'RESIDENT' AND active = true;

-- Check compliance violations
SELECT * FROM acgme_violations
WHERE severity = 'CRITICAL'
ORDER BY created_at DESC
LIMIT 10;

-- Get schedule for date range
SELECT p.name, a.date, a.activity_name
FROM assignments a
JOIN persons p ON a.person_id = p.id
WHERE a.date BETWEEN '2025-07-01' AND '2025-07-31'
ORDER BY a.date, p.name;
```

### Migrations

```bash
# Apply migrations
cd backend
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Rollback one migration
alembic downgrade -1

# Check current migration
alembic current
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs backend

# Rebuild
docker-compose up -d --build backend

# Reset everything
docker-compose down -v
docker-compose up -d
```

### Database Connection Failed

```bash
# Check if DB is running
docker-compose ps db

# Test connection
docker-compose exec db pg_isready -U scheduler

# Restart DB
docker-compose restart db
```

### Schedule Generation Timeout

```bash
# Increase timeout
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -d '{"timeout_seconds": 600, ...}'

# Use greedy algorithm (faster)
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -d '{"algorithm": "greedy", ...}'
```

### API Returns 401 Unauthorized

```bash
# Check token expiration
# Access tokens expire after 15 minutes

# Refresh token
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

### High Memory Usage

```bash
# Check container stats
docker stats

# Increase Docker memory limit
# Edit docker-compose.yml:
# backend:
#   mem_limit: 4g

# Restart
docker-compose down
docker-compose up -d
```

---

## Configuration

### Environment Variables

Key `.env` variables:

```bash
# Database
DATABASE_URL=postgresql://scheduler:password@localhost:5432/residency_scheduler

# Security
SECRET_KEY=your-secret-key-here  # Min 32 chars
WEBHOOK_SECRET=your-webhook-secret-here

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
```

### Port Configuration

Default ports:

| Service | Port | Description |
|---------|------|-------------|
| Backend API | 8000 | FastAPI backend |
| Frontend | 3000 | Next.js frontend |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache/Celery |
| MCP Server | 8080 | AI tools (HTTP) |
| Prometheus | 9090 | Metrics |
| Grafana | 3001 | Dashboards |

### Algorithms

| Algorithm | Speed | Quality | Use Case |
|-----------|-------|---------|----------|
| `greedy` | Fast | Good | Quick generation, testing |
| `cp_sat` | Slow | Excellent | Production, optimal schedules |
| `pulp` | Medium | Very Good | Balanced speed/quality |
| `hybrid` | Medium | Excellent | Best of both worlds |

---

## ACGME Compliance Rules

Quick reference for ACGME requirements:

### 80-Hour Rule

- Max 80 hours/week averaged over 4 weeks
- Includes all clinical and educational activities
- Moonlighting counts toward limit

### 1-in-7 Rule

- One 24-hour period off every 7 days
- Averaged over 4 weeks
- Can be averaged over 28-day block

### Supervision Ratios

| PGY Level | Max Residents per Faculty |
|-----------|---------------------------|
| PGY-1 | 2:1 |
| PGY-2/3 | 4:1 |

### Call Frequency

- Max 6 calls per month (block)
- No more than 24 hours + 4 hours continuous
- Min 8 hours between shifts (after 24-hour call)

---

## Useful URLs

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| Metrics | http://localhost:8000/metrics |
| Health Check | http://localhost:8000/health |
| MCP Server | http://localhost:8080/health |

---

## Emergency Procedures

### Abort Running Solver

```bash
# Find active run
curl http://localhost:8000/api/v1/scheduler/runs/active

# Abort specific run
curl -X POST http://localhost:8000/api/v1/scheduler/runs/{run_id}/abort \
  -d '{"reason": "Manual abort", "requested_by": "admin"}'
```

### Restore from Backup

```bash
# 1. Stop services
docker-compose down

# 2. Restore database
docker-compose up -d db
docker-compose exec -T db psql -U scheduler residency_scheduler < backup.sql

# 3. Restart all services
docker-compose up -d
```

### Reset Admin Password

```bash
cd backend
python -m app.cli user reset-password --email admin@example.com
```

---

## Code Examples

### Python API Client

```python
import requests

class SchedulerAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    def generate_schedule(self, start_date, end_date):
        response = requests.post(
            f"{self.base_url}/api/v1/schedule/generate",
            headers=self.headers,
            json={"start_date": start_date, "end_date": end_date}
        )
        return response.json()

    def get_people(self, type="resident"):
        response = requests.get(
            f"{self.base_url}/api/v1/people",
            headers=self.headers,
            params={"type": type}
        )
        return response.json()

# Usage
api = SchedulerAPI("http://localhost:8000", token="your-token")
schedule = api.generate_schedule("2025-07-01", "2025-09-30")
residents = api.get_people(type="resident")
```

### JavaScript/TypeScript API Client

```typescript
class SchedulerAPI {
  private baseUrl: string;
  private token: string;

  constructor(baseUrl: string, token: string) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  async generateSchedule(startDate: string, endDate: string) {
    const response = await fetch(
      `${this.baseUrl}/api/v1/schedule/generate`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ start_date: startDate, end_date: endDate })
      }
    );
    return response.json();
  }

  async getPeople(type: string = 'resident') {
    const response = await fetch(
      `${this.baseUrl}/api/v1/people?type=${type}`,
      {
        headers: {
          'Authorization': `Bearer ${this.token}`
        }
      }
    );
    return response.json();
  }
}

// Usage
const api = new SchedulerAPI('http://localhost:8000', 'your-token');
const schedule = await api.generateSchedule('2025-07-01', '2025-09-30');
const residents = await api.getPeople('resident');
```

---

## See Also

- [Full Documentation](README.md)
- [API Documentation](api/README.md)
- [Installation Guide](guides/installation.md)
- [CLI Reference](operations/cli-reference.md)
- [Troubleshooting](guides/SCHEDULE_GENERATION_RUNBOOK.md#troubleshooting)
- [CLAUDE.md](CLAUDE.md) - AI development guidelines
