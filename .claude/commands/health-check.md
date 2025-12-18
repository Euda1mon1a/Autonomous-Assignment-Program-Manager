<!--
Check system health endpoints and service status.
Validates that all components are running correctly.
-->

Perform comprehensive system health checks:

1. Check if the backend server is running
2. Test health endpoints
3. Verify database connectivity
4. Check Redis/Celery status
5. Review FMIT health metrics

Execute these health checks:

```bash
cd /home/user/Autonomous-Assignment-Program-Manager

# Check if containers are running (if using Docker)
docker-compose ps

# Test main health endpoint
curl -X GET "http://localhost:8000/health" -H "accept: application/json" || echo "Backend not running"

# Test FMIT health endpoint
curl -X GET "http://localhost:8000/api/v1/fmit/health" -H "accept: application/json" || echo "FMIT health endpoint unavailable"

# Test FMIT detailed status
curl -X GET "http://localhost:8000/api/v1/fmit/status" -H "accept: application/json" || echo "FMIT status endpoint unavailable"

# Test FMIT metrics
curl -X GET "http://localhost:8000/api/v1/fmit/metrics" -H "accept: application/json" || echo "FMIT metrics endpoint unavailable"

# Check database connectivity
cd backend
python -c "from app.db.session import engine; engine.connect(); print('Database connection: OK')" || echo "Database connection: FAILED"

# Check Celery worker status (if running)
celery -A app.core.celery_app inspect ping || echo "Celery workers not responding"

# Check Redis connectivity
redis-cli ping || echo "Redis not responding"
```

Report on system health:

## Service Status
- Backend API: Running/Stopped
- Database: Connected/Disconnected
- Redis: Available/Unavailable
- Celery Workers: Active/Inactive

## FMIT Health Metrics
From the `/api/v1/fmit/health` endpoint:
- Overall Status: healthy/degraded/critical
- Total Swaps This Month: [number]
- Pending Swap Requests: [number]
- Active Conflict Alerts: [number]
- Coverage Percentage: [percentage]%
- Issues: [list any issues]
- Recommendations: [list recommendations]

## Critical Alerts
- Number of critical ACGME violations
- Coverage gaps in next 7 days
- Pending swaps requiring immediate attention
- System circuit breaker status

## Performance Indicators
- Database query response time
- API endpoint response time
- Background task queue length
- Memory and CPU usage (if available)

If any component is unhealthy:
1. Provide detailed error messages
2. Suggest troubleshooting steps
3. Check logs for recent errors
4. Recommend immediate actions

To start services if needed:
```bash
# Start all services with Docker Compose
docker-compose up -d

# Or start backend directly
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
