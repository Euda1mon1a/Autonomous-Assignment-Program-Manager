***REMOVED*** Celery Quick Reference Card

***REMOVED******REMOVED*** Quick Start

***REMOVED******REMOVED******REMOVED*** Starting Services (Docker)
```bash
docker compose up -d celery-worker celery-beat redis
```

***REMOVED******REMOVED******REMOVED*** Starting Services (Local Development)
```bash
***REMOVED*** Terminal 1: Redis
redis-server

***REMOVED*** Terminal 2: Celery
cd backend
../scripts/start-celery.sh both
```

***REMOVED******REMOVED******REMOVED*** Verify Configuration
```bash
cd backend
python verify_celery.py
```

***REMOVED******REMOVED*** Common Commands

***REMOVED******REMOVED******REMOVED*** Check Worker Status
```bash
cd backend
celery -A app.core.celery_app inspect active
```

***REMOVED******REMOVED******REMOVED*** Check Scheduled Tasks
```bash
cd backend
celery -A app.core.celery_app inspect scheduled
```

***REMOVED******REMOVED******REMOVED*** List Registered Tasks
```bash
cd backend
celery -A app.core.celery_app inspect registered
```

***REMOVED******REMOVED******REMOVED*** Check Beat Schedule
```bash
cd backend
celery -A app.core.celery_app inspect scheduled
```

***REMOVED******REMOVED******REMOVED*** Purge All Tasks
```bash
cd backend
celery -A app.core.celery_app purge
```

***REMOVED******REMOVED******REMOVED*** Stop Workers
```bash
cd backend
celery -A app.core.celery_app control shutdown
```

***REMOVED******REMOVED*** Task Queues

- **default**: General purpose tasks
- **resilience**: Health checks, contingency analysis, forecasting
- **notifications**: Email and webhook delivery

***REMOVED******REMOVED*** Periodic Tasks Schedule

| Task | Frequency | Queue | Purpose |
|------|-----------|-------|---------|
| `periodic_health_check` | Every 15 min | resilience | Monitor system health |
| `run_contingency_analysis` | Daily 2 AM | resilience | N-1/N-2 analysis |
| `precompute_fallback_schedules` | Sunday 3 AM | resilience | Pre-generate crisis schedules |
| `generate_utilization_forecast` | Daily 6 AM | resilience | Predict capacity issues |

***REMOVED******REMOVED*** Manual Task Execution

***REMOVED******REMOVED******REMOVED*** Python
```python
from app.resilience.tasks import periodic_health_check

***REMOVED*** Execute immediately
result = periodic_health_check.delay()

***REMOVED*** Execute with delay
result = periodic_health_check.apply_async(countdown=60)

***REMOVED*** Get result
print(result.get(timeout=10))
```

***REMOVED******REMOVED******REMOVED*** Celery CLI
```bash
cd backend
celery -A app.core.celery_app call app.resilience.tasks.periodic_health_check
```

***REMOVED******REMOVED*** Monitoring

***REMOVED******REMOVED******REMOVED*** Health Check
```bash
./scripts/health-check.sh --docker --verbose
```

***REMOVED******REMOVED******REMOVED*** View Logs (Docker)
```bash
docker compose logs -f celery-worker
docker compose logs -f celery-beat
```

***REMOVED******REMOVED******REMOVED*** Worker Stats
```bash
cd backend
celery -A app.core.celery_app inspect stats
```

***REMOVED******REMOVED*** Debugging

***REMOVED******REMOVED******REMOVED*** Enable Debug Logging
```bash
***REMOVED*** In .env
CELERY_LOG_LEVEL=debug
```

***REMOVED******REMOVED******REMOVED*** Check Task Failures
```bash
cd backend
celery -A app.core.celery_app events
```

***REMOVED******REMOVED******REMOVED*** Test Redis Connection
```bash
redis-cli ping
***REMOVED*** Should return: PONG
```

***REMOVED******REMOVED******REMOVED*** Test Task Registration
```bash
cd backend
python -c "from app.core.celery_app import celery_app; print(list(celery_app.tasks.keys()))"
```

***REMOVED******REMOVED*** Environment Variables

```bash
***REMOVED*** Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

***REMOVED*** Worker Configuration
CELERY_WORKER_CONCURRENCY=4
CELERY_LOG_LEVEL=info
CELERY_QUEUES=default,resilience,notifications
CELERY_MAX_TASKS_PER_CHILD=1000
```

***REMOVED******REMOVED*** Production Tips

1. **Scale Workers**: Increase `CELERY_WORKER_CONCURRENCY` based on CPU cores
2. **Separate Workers**: Run dedicated workers for each queue
   ```bash
   celery -A app.core.celery_app worker -Q resilience --concurrency=2
   celery -A app.core.celery_app worker -Q notifications --concurrency=8
   ```
3. **Monitor Memory**: Set `--max-tasks-per-child=1000` to prevent memory leaks
4. **Use Flower**: Add web UI for monitoring
   ```bash
   pip install flower
   celery -A app.core.celery_app flower
   ***REMOVED*** Visit http://localhost:5555
   ```
5. **Configure Alerts**: Set `RESILIENCE_ALERT_RECIPIENTS` in environment

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Workers Not Starting
- Check Redis is running: `redis-cli ping`
- Check configuration: `python verify_celery.py`
- Check logs: `docker compose logs celery-worker`

***REMOVED******REMOVED******REMOVED*** Tasks Not Executing
- Verify worker is running: `celery -A app.core.celery_app inspect active`
- Check task is registered: `celery -A app.core.celery_app inspect registered`
- Check queue routing: Tasks route to specific queues

***REMOVED******REMOVED******REMOVED*** Beat Schedule Not Running
- Verify beat is running: `docker compose ps celery-beat`
- Check schedule: `celery -A app.core.celery_app inspect scheduled`
- Check logs: `docker compose logs celery-beat`

***REMOVED******REMOVED******REMOVED*** Redis Connection Errors
- Verify Redis URL: `echo $REDIS_URL`
- Test connection: `redis-cli -u $REDIS_URL ping`
- Check firewall/network settings

***REMOVED******REMOVED*** Architecture

```
┌─────────────────┐
│  FastAPI App    │
│  (app/main.py)  │
└────────┬────────┘
         │ imports
         ▼
┌─────────────────┐         ┌──────────────┐
│  Celery App     │◄────────┤  Redis       │
│  (celery_app)   │ broker  │  (message    │
└────────┬────────┘         │   broker)    │
         │                  └──────────────┘
         │ includes
         ▼
┌─────────────────┐
│  Task Modules   │
│  - resilience/  │
│  - notifications│
└─────────────────┘
         │
         ▼
┌─────────────────┐         ┌──────────────┐
│  Workers        │         │  Beat        │
│  (execute tasks)│         │  (scheduler) │
└─────────────────┘         └──────────────┘
```

***REMOVED******REMOVED*** Files Reference

| File | Purpose |
|------|---------|
| `backend/app/core/celery_app.py` | Celery configuration |
| `backend/app/resilience/tasks.py` | Resilience monitoring tasks |
| `backend/app/notifications/tasks.py` | Notification tasks |
| `docker-compose.yml` | Docker service definitions |
| `scripts/start-celery.sh` | Startup script |
| `scripts/health-check.sh` | Health monitoring |
| `backend/verify_celery.py` | Configuration verification |

***REMOVED******REMOVED*** Support

For detailed documentation, see:
- `CELERY_SETUP_SUMMARY.md` - Complete configuration details
- `ARCHITECTURE.md` - System architecture
- `docs/RESILIENCE_FRAMEWORK.md` - Resilience framework documentation
