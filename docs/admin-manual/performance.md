# Performance Tuning Guide

## Overview

This guide provides comprehensive performance optimization strategies for the Residency Scheduler application. It covers database tuning, application optimization, caching strategies, and monitoring.

## Table of Contents

1. [Performance Benchmarks](#performance-benchmarks)
2. [Database Optimization](#database-optimization)
3. [Backend Optimization](#backend-optimization)
4. [Frontend Optimization](#frontend-optimization)
5. [Caching Strategies](#caching-strategies)
6. [Load Balancing](#load-balancing)
7. [Resource Sizing](#resource-sizing)
8. [Monitoring and Profiling](#monitoring-and-profiling)
9. [Troubleshooting Performance Issues](#troubleshooting-performance-issues)

---

## Performance Benchmarks

### Target Response Times

| Operation | Target | Acceptable | Action Threshold |
|-----------|--------|------------|------------------|
| API health check | < 50ms | < 100ms | > 200ms |
| List operations | < 200ms | < 500ms | > 1000ms |
| Single record fetch | < 100ms | < 200ms | > 500ms |
| Schedule generation | < 30s | < 60s | > 120s |
| Report export | < 5s | < 15s | > 30s |
| Page load (frontend) | < 2s | < 3s | > 5s |

### Throughput Targets

| Metric | Target |
|--------|--------|
| Concurrent users | 100+ |
| API requests/second | 500+ |
| Database queries/second | 1000+ |

---

## Database Optimization

### PostgreSQL Configuration

Edit `postgresql.conf` for production:

```ini
# =============================================================================
# Memory Settings
# =============================================================================
# shared_buffers: 25% of available RAM (max 8GB)
shared_buffers = 2GB

# effective_cache_size: 75% of available RAM
effective_cache_size = 6GB

# work_mem: Memory per operation (careful with concurrent connections)
work_mem = 256MB

# maintenance_work_mem: Memory for maintenance operations
maintenance_work_mem = 512MB

# =============================================================================
# Connection Settings
# =============================================================================
max_connections = 100
superuser_reserved_connections = 3

# =============================================================================
# Write-Ahead Log (WAL)
# =============================================================================
wal_buffers = 64MB
checkpoint_completion_target = 0.9
max_wal_size = 4GB
min_wal_size = 1GB

# =============================================================================
# Query Planning
# =============================================================================
# For SSD storage
random_page_cost = 1.1
effective_io_concurrency = 200

# Statistics
default_statistics_target = 100

# =============================================================================
# Parallel Query
# =============================================================================
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_parallel_maintenance_workers = 4
parallel_tuple_cost = 0.01
parallel_setup_cost = 1000.0
```

### Connection Pooling

Use connection pooling for better resource utilization:

```python
# backend/app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,          # Base connections
    max_overflow=20,       # Additional connections
    pool_timeout=30,       # Wait time for connection
    pool_recycle=1800,     # Recycle after 30 minutes
    pool_pre_ping=True,    # Validate connections
)
```

#### PgBouncer (External Pooler)

For high-load scenarios, use PgBouncer:

```ini
# pgbouncer.ini
[databases]
residency_scheduler = host=localhost port=5432 dbname=residency_scheduler

[pgbouncer]
listen_port = 6432
listen_addr = 127.0.0.1
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 500
default_pool_size = 20
min_pool_size = 5
reserve_pool_size = 5
```

### Index Optimization

#### Essential Indexes

```sql
-- People queries
CREATE INDEX idx_people_type ON people(type);
CREATE INDEX idx_people_is_active ON people(is_active);
CREATE INDEX idx_people_pgy_level ON people(pgy_level);

-- Assignment queries
CREATE INDEX idx_assignments_person_id ON assignments(person_id);
CREATE INDEX idx_assignments_block_id ON assignments(block_id);
CREATE INDEX idx_assignments_person_block ON assignments(person_id, block_id);

-- Block queries
CREATE INDEX idx_blocks_date ON blocks(date);
CREATE INDEX idx_blocks_date_shift ON blocks(date, shift_type);

-- Absence queries
CREATE INDEX idx_absences_person_id ON absences(person_id);
CREATE INDEX idx_absences_dates ON absences(start_date, end_date);
CREATE INDEX idx_absences_person_dates ON absences(person_id, start_date, end_date);

-- User queries
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Audit log queries
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
```

#### Index Maintenance

```sql
-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Find unused indexes
SELECT
    schemaname || '.' || relname AS table,
    indexrelname AS index,
    pg_size_pretty(pg_relation_size(i.indexrelid)) AS index_size,
    idx_scan AS times_used
FROM pg_stat_user_indexes ui
JOIN pg_index i ON ui.indexrelid = i.indexrelid
WHERE NOT indisunique AND idx_scan < 50
ORDER BY pg_relation_size(i.indexrelid) DESC;

-- Reindex to fix bloat
REINDEX INDEX idx_assignments_person_id;
```

### Query Optimization

#### Analyze Slow Queries

```sql
-- Enable query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s
SELECT pg_reload_conf();

-- Use EXPLAIN ANALYZE
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT p.name, COUNT(a.id)
FROM people p
JOIN assignments a ON p.id = a.person_id
WHERE p.type = 'resident'
GROUP BY p.id;
```

#### Common Optimizations

```sql
-- Use pagination instead of fetching all records
SELECT * FROM people
ORDER BY id
LIMIT 50 OFFSET 100;

-- Use covering indexes for frequently queried columns
CREATE INDEX idx_people_covering ON people(id, name, email, type)
WHERE is_active = true;

-- Partition large tables by date
CREATE TABLE assignments_2024 PARTITION OF assignments
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

### Database Maintenance

```bash
# Regular maintenance script
#!/bin/bash

# Vacuum and analyze
psql -U scheduler -d residency_scheduler -c "VACUUM ANALYZE;"

# Update statistics
psql -U scheduler -d residency_scheduler -c "ANALYZE VERBOSE;"

# Check table bloat
psql -U scheduler -d residency_scheduler -c "
SELECT
    schemaname,
    relname,
    n_dead_tup,
    n_live_tup,
    round(n_dead_tup * 100.0 / (n_live_tup + n_dead_tup), 2) as dead_percentage
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;
"
```

---

## Backend Optimization

### Gunicorn Configuration

```python
# gunicorn.conf.py

# Workers = (2 x CPU cores) + 1
workers = 9

# Worker class for async support
worker_class = "uvicorn.workers.UvicornWorker"

# Connections per worker
worker_connections = 1000

# Timeout settings
timeout = 120
graceful_timeout = 30
keepalive = 5

# Memory management
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/var/log/residency-scheduler/access.log"
errorlog = "/var/log/residency-scheduler/error.log"
loglevel = "info"
```

### Async Database Operations

```python
# Use async SQLAlchemy for I/O-bound operations
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(
    "postgresql+asyncpg://scheduler:pass@localhost/residency_scheduler",
    pool_size=20,
    max_overflow=30,
)

async def get_people(db: AsyncSession):
    result = await db.execute(select(Person).where(Person.is_active == True))
    return result.scalars().all()
```

### Response Compression

```python
# Enable gzip compression
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000  # Compress responses > 1KB
)
```

### Pagination

```python
# Always paginate list endpoints
from fastapi import Query

@router.get("/people")
async def list_people(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    total = db.query(Person).count()
    people = db.query(Person).offset(skip).limit(limit).all()

    return {
        "items": people,
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

### Background Tasks

```python
# Use background tasks for non-blocking operations
from fastapi import BackgroundTasks

@router.post("/schedule/generate")
async def generate_schedule(
    request: ScheduleRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    schedule_id = create_schedule_record(db)

    # Run generation in background
    background_tasks.add_task(
        run_schedule_generation,
        schedule_id,
        request
    )

    return {"schedule_id": schedule_id, "status": "processing"}
```

---

## Frontend Optimization

### Build Optimization

```javascript
// next.config.js
module.exports = {
  // Enable SWC minification
  swcMinify: true,

  // Optimize images
  images: {
    domains: ['api.your-domain.com'],
    formats: ['image/avif', 'image/webp'],
  },

  // Bundle analyzer
  webpack: (config, { isServer }) => {
    if (process.env.ANALYZE === 'true') {
      const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer')
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: 'static',
          reportFilename: isServer
            ? '../analyze/server.html'
            : './analyze/client.html',
        })
      )
    }
    return config
  },
}
```

### Code Splitting

```typescript
// Use dynamic imports for large components
import dynamic from 'next/dynamic'

const ScheduleCalendar = dynamic(
  () => import('@/components/ScheduleCalendar'),
  {
    loading: () => <LoadingSpinner />,
    ssr: false,
  }
)
```

### React Query Optimization

```typescript
// Optimize data fetching with React Query
import { useQuery, useQueryClient } from '@tanstack/react-query'

// Configure stale time to reduce refetches
export function usePeople() {
  return useQuery({
    queryKey: ['people'],
    queryFn: fetchPeople,
    staleTime: 5 * 60 * 1000,     // Consider fresh for 5 minutes
    cacheTime: 30 * 60 * 1000,    // Keep in cache for 30 minutes
    refetchOnWindowFocus: false,   // Don't refetch on tab focus
  })
}

// Prefetch related data
const queryClient = useQueryClient()

async function prefetchScheduleData(dateRange: DateRange) {
  await queryClient.prefetchQuery({
    queryKey: ['schedule', dateRange],
    queryFn: () => fetchSchedule(dateRange),
  })
}
```

### Bundle Size Optimization

```bash
# Analyze bundle size
npm run build
npx @next/bundle-analyzer

# Tree-shaking - import only what you need
# Bad
import { Calendar, Button, Input, Modal } from 'ui-library'

# Good
import Calendar from 'ui-library/Calendar'
import Button from 'ui-library/Button'
```

---

## Caching Strategies

### Application-Level Caching

#### Redis Cache Implementation

```python
# backend/app/core/cache.py
import redis
import json
from typing import Optional, Any
from datetime import timedelta

class Cache:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    def get(self, key: str) -> Optional[Any]:
        value = self.redis.get(key)
        return json.loads(value) if value else None

    def set(self, key: str, value: Any, ttl: timedelta = timedelta(minutes=5)):
        self.redis.setex(key, ttl, json.dumps(value))

    def delete(self, key: str):
        self.redis.delete(key)

    def delete_pattern(self, pattern: str):
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)

cache = Cache(settings.REDIS_URL)
```

#### Cache Usage

```python
from app.core.cache import cache

@router.get("/people")
async def list_people(db: Session = Depends(get_db)):
    # Try cache first
    cached = cache.get("people:list")
    if cached:
        return cached

    # Fetch from database
    people = db.query(Person).filter(Person.is_active == True).all()
    result = [PersonResponse.from_orm(p) for p in people]

    # Cache result
    cache.set("people:list", result, ttl=timedelta(minutes=5))

    return result

@router.post("/people")
async def create_person(person: PersonCreate, db: Session = Depends(get_db)):
    # Create person...

    # Invalidate cache
    cache.delete("people:list")

    return new_person
```

### HTTP Caching

```python
from fastapi import Response

@router.get("/schedule/{year}/{month}")
async def get_monthly_schedule(
    year: int,
    month: int,
    response: Response,
    db: Session = Depends(get_db)
):
    # Set cache headers
    response.headers["Cache-Control"] = "public, max-age=300"  # 5 minutes
    response.headers["ETag"] = f"{year}-{month}-{hash(schedule)}"

    return schedule
```

### Nginx Caching

```nginx
# Enable proxy caching
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;

server {
    location /api/ {
        proxy_cache api_cache;
        proxy_cache_valid 200 5m;
        proxy_cache_key $scheme$proxy_host$uri$is_args$args;
        proxy_cache_use_stale error timeout updating http_500 http_502;

        add_header X-Cache-Status $upstream_cache_status;

        proxy_pass http://backend;
    }
}
```

---

## Load Balancing

### Nginx Load Balancing

```nginx
upstream backend_servers {
    least_conn;  # Send to server with fewest connections

    server backend1:8000 weight=5;
    server backend2:8000 weight=5;
    server backend3:8000 backup;

    keepalive 32;
}

server {
    location /api/ {
        proxy_pass http://backend_servers;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
}
```

### Docker Swarm Scaling

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    image: residency-scheduler-backend
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
      update_config:
        parallelism: 1
        delay: 10s
```

---

## Resource Sizing

### Sizing Guidelines

| Users | CPU | RAM | Database |
|-------|-----|-----|----------|
| < 50 | 2 cores | 4 GB | Shared |
| 50-200 | 4 cores | 8 GB | 2 cores / 4 GB |
| 200-500 | 8 cores | 16 GB | 4 cores / 8 GB |
| 500+ | 16+ cores | 32+ GB | Dedicated / HA |

### Container Resource Limits

```yaml
# docker-compose.yml
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

  frontend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 256M

  db:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 1G
```

---

## Monitoring and Profiling

### Application Metrics

```python
# backend/app/middleware/metrics.py
import time
from fastapi import Request
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response
```

### Database Monitoring

```sql
-- Current connections
SELECT count(*) FROM pg_stat_activity;

-- Long-running queries
SELECT
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';

-- Table sizes
SELECT
    relname AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
    pg_size_pretty(pg_relation_size(relid)) AS data_size,
    pg_size_pretty(pg_indexes_size(relid)) AS index_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

### Profiling Tools

```bash
# Python profiling
pip install py-spy

# Profile running process
py-spy record -o profile.svg --pid <PID>

# Memory profiling
pip install memory_profiler
python -m memory_profiler app.py
```

---

## Troubleshooting Performance Issues

### Common Issues and Solutions

#### High Database CPU

```sql
-- Find expensive queries
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;

-- Solution: Add missing indexes, optimize queries
```

#### High Memory Usage

```bash
# Check memory usage
docker stats

# Identify memory leaks
# Profile with memory_profiler or py-spy
```

#### Slow API Responses

```bash
# Check response times
curl -w "@curl-format.txt" -s -o /dev/null https://api.example.com/endpoint

# curl-format.txt:
#     time_namelookup:  %{time_namelookup}s\n
#        time_connect:  %{time_connect}s\n
#     time_appconnect:  %{time_appconnect}s\n
#    time_pretransfer:  %{time_pretransfer}s\n
#       time_redirect:  %{time_redirect}s\n
#  time_starttransfer:  %{time_starttransfer}s\n
#                     ----------\n
#          time_total:  %{time_total}s\n
```

#### Connection Pool Exhaustion

```python
# Monitor connection pool
from sqlalchemy import event

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    logger.debug(f"Connection checked out: {id(dbapi_connection)}")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    logger.debug(f"Connection returned: {id(dbapi_connection)}")
```

### Performance Checklist

- [ ] Database indexes optimized
- [ ] Connection pooling configured
- [ ] Query execution plans reviewed
- [ ] API responses paginated
- [ ] Caching implemented
- [ ] Compression enabled
- [ ] Resource limits set
- [ ] Monitoring configured
- [ ] Load testing performed

---

*Last Updated: December 2024*
