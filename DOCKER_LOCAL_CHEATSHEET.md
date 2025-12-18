***REMOVED*** Docker Local Development - Quick Reference

***REMOVED******REMOVED*** Quick Start

```bash
***REMOVED*** Start everything
docker-compose -f docker-compose.local.yml up

***REMOVED*** Start in background
docker-compose -f docker-compose.local.yml up -d

***REMOVED*** Stop everything
docker-compose -f docker-compose.local.yml down
```

***REMOVED******REMOVED*** Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | - |
| Backend API | http://localhost:8000 | - |
| API Docs | http://localhost:8000/docs | - |
| PostgreSQL | localhost:5432 | scheduler / local_dev_password |
| Redis | localhost:6379 | local_dev_redis_pass |
| n8n | http://localhost:5679 | admin / local_dev_n8n_password |

***REMOVED******REMOVED*** Common Commands

***REMOVED******REMOVED******REMOVED*** Service Management

```bash
***REMOVED*** View status
docker-compose -f docker-compose.local.yml ps

***REMOVED*** View logs (all)
docker-compose -f docker-compose.local.yml logs -f

***REMOVED*** View logs (specific service)
docker-compose -f docker-compose.local.yml logs -f backend
docker-compose -f docker-compose.local.yml logs -f frontend

***REMOVED*** Restart service
docker-compose -f docker-compose.local.yml restart backend

***REMOVED*** Rebuild after dependency changes
docker-compose -f docker-compose.local.yml up --build
```

***REMOVED******REMOVED******REMOVED*** Database

```bash
***REMOVED*** Connect to PostgreSQL
docker-compose -f docker-compose.local.yml exec db psql -U scheduler -d residency_scheduler

***REMOVED*** Run migrations
docker-compose -f docker-compose.local.yml exec backend alembic upgrade head

***REMOVED*** Create migration
docker-compose -f docker-compose.local.yml exec backend alembic revision --autogenerate -m "description"

***REMOVED*** Reset database (⚠️ deletes all data)
docker-compose -f docker-compose.local.yml down -v
docker-compose -f docker-compose.local.yml up
```

***REMOVED******REMOVED******REMOVED*** Redis

```bash
***REMOVED*** Connect to Redis
docker-compose -f docker-compose.local.yml exec redis redis-cli -a local_dev_redis_pass

***REMOVED*** Common Redis commands:
KEYS *           ***REMOVED*** List all keys
GET key_name     ***REMOVED*** Get value
FLUSHALL         ***REMOVED*** Clear all data
MONITOR          ***REMOVED*** Watch commands
```

***REMOVED******REMOVED******REMOVED*** Backend

```bash
***REMOVED*** Run tests
docker-compose -f docker-compose.local.yml exec backend pytest

***REMOVED*** Run tests with coverage
docker-compose -f docker-compose.local.yml exec backend pytest --cov=app

***REMOVED*** Python shell
docker-compose -f docker-compose.local.yml exec backend python

***REMOVED*** Bash shell
docker-compose -f docker-compose.local.yml exec backend bash
```

***REMOVED******REMOVED******REMOVED*** Frontend

```bash
***REMOVED*** Install package
docker-compose -f docker-compose.local.yml exec frontend npm install package-name

***REMOVED*** Run linter
docker-compose -f docker-compose.local.yml exec frontend npm run lint

***REMOVED*** Type check
docker-compose -f docker-compose.local.yml exec frontend npm run type-check

***REMOVED*** Shell
docker-compose -f docker-compose.local.yml exec frontend sh
```

***REMOVED******REMOVED******REMOVED*** Celery

```bash
***REMOVED*** View worker logs
docker-compose -f docker-compose.local.yml logs -f celery-worker

***REMOVED*** Check worker status
docker-compose -f docker-compose.local.yml exec celery-worker celery -A app.core.celery_app inspect active

***REMOVED*** Check scheduled tasks
docker-compose -f docker-compose.local.yml exec celery-worker celery -A app.core.celery_app inspect scheduled

***REMOVED*** Purge queue
docker-compose -f docker-compose.local.yml exec celery-worker celery -A app.core.celery_app purge
```

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Service won't start

```bash
***REMOVED*** Check logs
docker-compose -f docker-compose.local.yml logs service-name

***REMOVED*** Rebuild
docker-compose -f docker-compose.local.yml up --build service-name

***REMOVED*** Fresh start
docker-compose -f docker-compose.local.yml down -v
docker-compose -f docker-compose.local.yml up --build
```

***REMOVED******REMOVED******REMOVED*** Port already in use

```bash
***REMOVED*** Find process using port (Linux/macOS)
lsof -i :8000

***REMOVED*** Find process using port (Windows)
netstat -ano | findstr :8000

***REMOVED*** Change port in docker-compose.local.yml
***REMOVED*** Example: "8001:8000" to use host port 8001
```

***REMOVED******REMOVED******REMOVED*** Hot reload not working

```bash
***REMOVED*** Restart service
docker-compose -f docker-compose.local.yml restart backend

***REMOVED*** Rebuild
docker-compose -f docker-compose.local.yml up --build backend
```

***REMOVED******REMOVED******REMOVED*** Out of disk space

```bash
***REMOVED*** Check Docker disk usage
docker system df

***REMOVED*** Clean up
docker system prune -a
docker volume prune
```

***REMOVED******REMOVED*** Environment Variables

File: `.env.local` (already created)

```bash
***REMOVED*** View current environment
docker-compose -f docker-compose.local.yml config
```

***REMOVED******REMOVED*** File Structure

```
.
├── docker-compose.local.yml       ***REMOVED*** Local dev Docker Compose
├── .env.local                     ***REMOVED*** Local environment variables
├── backend/
│   └── Dockerfile.local          ***REMOVED*** Backend dev Dockerfile
└── frontend/
    └── Dockerfile.local          ***REMOVED*** Frontend dev Dockerfile
```

***REMOVED******REMOVED*** Hot Reload

✅ **Works automatically** - no rebuild needed:
- Python files (`.py`)
- TypeScript/React files (`.tsx`, `.ts`)
- CSS files

⚠️ **Requires rebuild**:
- `requirements.txt` changes
- `package.json` changes
- `.env.local` changes
- Dockerfile changes

***REMOVED******REMOVED*** Tips

- **Faster startup**: Comment out n8n in docker-compose.local.yml if not needed
- **Save resources**: Stop unused services with `docker-compose -f docker-compose.local.yml stop service-name`
- **Fresh start**: Use `docker-compose -f docker-compose.local.yml down -v` to delete all data
- **Parallel logs**: Use `docker-compose -f docker-compose.local.yml logs -f backend frontend` to watch multiple services

***REMOVED******REMOVED*** Security Reminder

⚠️ **Local development only!** These credentials are NOT secure:
- `DB_PASSWORD=local_dev_password`
- `SECRET_KEY=local_dev_secret_key_...`
- `REDIS_PASSWORD=local_dev_redis_pass`

For production, use `.env` with strong secrets!

***REMOVED******REMOVED*** Need More Help?

- Full guide: [DOCKER_LOCAL_SETUP.md](./DOCKER_LOCAL_SETUP.md)
- Project guidelines: [CLAUDE.md](./CLAUDE.md)
- Main docs: [README.md](./README.md)
