# Docker Local Development - Quick Reference

## Quick Start

```bash
# Start everything
docker-compose -f docker-compose.local.yml up

# Start in background
docker-compose -f docker-compose.local.yml up -d

# Stop everything
docker-compose -f docker-compose.local.yml down
```

## Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | - |
| Backend API | http://localhost:8000 | - |
| API Docs | http://localhost:8000/docs | - |
| PostgreSQL | localhost:5432 | scheduler / local_dev_password |
| Redis | localhost:6379 | local_dev_redis_pass |
| n8n | http://localhost:5679 | admin / local_dev_n8n_password |

## Common Commands

### Service Management

```bash
# View status
docker-compose -f docker-compose.local.yml ps

# View logs (all)
docker-compose -f docker-compose.local.yml logs -f

# View logs (specific service)
docker-compose -f docker-compose.local.yml logs -f backend
docker-compose -f docker-compose.local.yml logs -f frontend

# Restart service
docker-compose -f docker-compose.local.yml restart backend

# Rebuild after dependency changes
docker-compose -f docker-compose.local.yml up --build
```

### Database

```bash
# Connect to PostgreSQL
docker-compose -f docker-compose.local.yml exec db psql -U scheduler -d residency_scheduler

# Run migrations
docker-compose -f docker-compose.local.yml exec backend alembic upgrade head

# Create migration
docker-compose -f docker-compose.local.yml exec backend alembic revision --autogenerate -m "description"

# Reset database (⚠️ deletes all data)
docker-compose -f docker-compose.local.yml down -v
docker-compose -f docker-compose.local.yml up
```

### Redis

```bash
# Connect to Redis
docker-compose -f docker-compose.local.yml exec redis redis-cli -a local_dev_redis_pass

# Common Redis commands:
KEYS *           # List all keys
GET key_name     # Get value
FLUSHALL         # Clear all data
MONITOR          # Watch commands
```

### Backend

```bash
# Run tests
docker-compose -f docker-compose.local.yml exec backend pytest

# Run tests with coverage
docker-compose -f docker-compose.local.yml exec backend pytest --cov=app

# Python shell
docker-compose -f docker-compose.local.yml exec backend python

# Bash shell
docker-compose -f docker-compose.local.yml exec backend bash
```

### Frontend

```bash
# Install package
docker-compose -f docker-compose.local.yml exec frontend npm install package-name

# Run linter
docker-compose -f docker-compose.local.yml exec frontend npm run lint

# Type check
docker-compose -f docker-compose.local.yml exec frontend npm run type-check

# Shell
docker-compose -f docker-compose.local.yml exec frontend sh
```

### Celery

```bash
# View worker logs
docker-compose -f docker-compose.local.yml logs -f celery-worker

# Check worker status
docker-compose -f docker-compose.local.yml exec celery-worker celery -A app.core.celery_app inspect active

# Check scheduled tasks
docker-compose -f docker-compose.local.yml exec celery-worker celery -A app.core.celery_app inspect scheduled

# Purge queue
docker-compose -f docker-compose.local.yml exec celery-worker celery -A app.core.celery_app purge
```

## Troubleshooting

### Service won't start

```bash
# Check logs
docker-compose -f docker-compose.local.yml logs service-name

# Rebuild
docker-compose -f docker-compose.local.yml up --build service-name

# Fresh start
docker-compose -f docker-compose.local.yml down -v
docker-compose -f docker-compose.local.yml up --build
```

### Port already in use

```bash
# Find process using port (Linux/macOS)
lsof -i :8000

# Find process using port (Windows)
netstat -ano | findstr :8000

# Change port in docker-compose.local.yml
# Example: "8001:8000" to use host port 8001
```

### Hot reload not working

```bash
# Restart service
docker-compose -f docker-compose.local.yml restart backend

# Rebuild
docker-compose -f docker-compose.local.yml up --build backend
```

### Out of disk space

```bash
# Check Docker disk usage
docker system df

# Clean up
docker system prune -a
docker volume prune
```

## Environment Variables

File: `.env.local` (already created)

```bash
# View current environment
docker-compose -f docker-compose.local.yml config
```

## File Structure

```
.
├── docker-compose.local.yml       # Local dev Docker Compose
├── .env.local                     # Local environment variables
├── backend/
│   └── Dockerfile.local          # Backend dev Dockerfile
└── frontend/
    └── Dockerfile.local          # Frontend dev Dockerfile
```

## Hot Reload

✅ **Works automatically** - no rebuild needed:
- Python files (`.py`)
- TypeScript/React files (`.tsx`, `.ts`)
- CSS files

⚠️ **Requires rebuild**:
- `requirements.txt` changes
- `package.json` changes
- `.env.local` changes
- Dockerfile changes

## Tips

- **Faster startup**: Comment out n8n in docker-compose.local.yml if not needed
- **Save resources**: Stop unused services with `docker-compose -f docker-compose.local.yml stop service-name`
- **Fresh start**: Use `docker-compose -f docker-compose.local.yml down -v` to delete all data
- **Parallel logs**: Use `docker-compose -f docker-compose.local.yml logs -f backend frontend` to watch multiple services

## Security Reminder

⚠️ **Local development only!** These credentials are NOT secure:
- `DB_PASSWORD=local_dev_password`
- `SECRET_KEY=local_dev_secret_key_...`
- `REDIS_PASSWORD=local_dev_redis_pass`

For production, use `.env` with strong secrets!

## Need More Help?

- Full guide: [DOCKER_LOCAL_SETUP.md](./DOCKER_LOCAL_SETUP.md)
- Project guidelines: [CLAUDE.md](../../CLAUDE.md)
- Main docs: [README.md](../../README.md)
