# Gordon AI Evaluation Results - Docker Performance Optimization

> **Document Type:** Research & Recommendations
> **Created:** 2025-12-19
> **Purpose:** Gordon AI-guided Docker optimization for Residency Scheduler
> **Scope:** Performance optimization (image size, build time, resource usage)
> **Stack:** FastAPI + Next.js + Celery + PostgreSQL + Redis

---

## Executive Summary

This document provides a structured approach to evaluating and optimizing Docker containers for the Residency Scheduler application using Gordon AI. The recommendations focus on **performance optimization** including image size reduction, build time improvement, resource efficiency, and production best practices.

**Current State:**
- Backend: Multi-stage Dockerfile with DHI (Docker Hardened Images)
- Frontend: Multi-stage Dockerfile with DHI, Next.js standalone output
- Infrastructure: PostgreSQL, Redis, Celery (worker + beat), n8n
- Deployment: docker-compose.yml + docker-compose.prod.yml

**Expected Outcomes:**
- 20-40% reduction in image sizes
- 30-50% faster CI/CD build times
- 15-25% reduction in memory usage
- Improved caching strategies
- Optimized resource limits

---

## Table of Contents

1. [Performance & Image Size](#1-performance--image-size)
2. [Resource Optimization](#2-resource-optimization)
3. [Best Practices](#3-best-practices)
4. [Implementation Roadmap](#4-implementation-roadmap)
5. [Measurement & Validation](#5-measurement--validation)

---

## 1. Performance & Image Size

### 1.1 Frontend Docker Image Size Reduction

**Gordon AI Question:**
```
Analyze frontend/Dockerfile for size optimization opportunities.
We're using Next.js 14 with standalone output and Node.js 22 DHI base images.
What can be optimized to reduce the final image size?
```

**Expected Optimization Opportunities:**

1. **Next.js Output Optimization**
   - Current: Using standalone output (already good)
   - Opportunity: Verify `.next/standalone` excludes dev dependencies
   - Expected Impact: 5-10% reduction if dev deps are leaking

2. **Node_modules Pruning**
   - Current: `npm ci --legacy-peer-deps` in builder
   - Opportunity: Production-only dependencies in runtime stage
   - Expected Impact: 15-25% reduction by removing build-only packages

3. **Static Asset Compression**
   - Current: Copying `.next/static` as-is
   - Opportunity: Pre-compress static assets (gzip/brotli)
   - Expected Impact: 10-20% reduction in static asset size

4. **Base Image Selection**
   - Current: `dhi.io/node:22` (distroless-style)
   - Opportunity: Compare with `node:22-alpine` or pure distroless
   - Expected Impact: 20-30% reduction if switching to alpine (trade-off with security)

**Specific Recommendations:**

```dockerfile
# RECOMMENDATION 1: Explicitly verify standalone output
# Add to next.config.js:
output: 'standalone',
experimental: {
  outputFileTracingRoot: path.join(__dirname, '../../'),
}

# RECOMMENDATION 2: Add compression for static assets
FROM builder AS compressor
RUN find .next/static -type f \( -name '*.js' -o -name '*.css' -o -name '*.html' \) \
    -exec gzip -9 -k {} \; \
    -exec brotli -9 -k {} \;

# RECOMMENDATION 3: Verify package.json doesn't include devDependencies in production
# Add .dockerignore:
node_modules
.next
.git
*.md
tests
__tests__
.env.local
.env.development

# RECOMMENDATION 4: Use npm prune in builder stage
RUN npm ci --omit=dev --legacy-peer-deps && \
    npm cache clean --force && \
    npm prune --production
```

**Estimated Impact:**
- Image size reduction: **25-35%** (from ~400MB to ~260-300MB)
- Build time improvement: **10-15%** with better caching
- Runtime memory: **5-10% reduction** from fewer loaded modules

---

### 1.2 Backend Docker Image Size Reduction

**Gordon AI Question:**
```
Analyze backend/Dockerfile for size optimization opportunities.
We're using Python 3.12 with FastAPI, SQLAlchemy, ortools, psycopg2, and Celery.
Using DHI base images with multi-stage builds. What can be optimized?
```

**Expected Optimization Opportunities:**

1. **Python Package Size**
   - Current: Installing all requirements.txt in venv
   - Opportunity: Strip debug symbols, remove .pyc files, wheel caching
   - Expected Impact: 10-20% reduction

2. **System Dependencies**
   - Current: Installing `libpq5` runtime dependency
   - Opportunity: Verify no unnecessary shared libraries
   - Expected Impact: 5-10% reduction

3. **Pip Installation Optimization**
   - Current: `pip install --no-cache-dir`
   - Opportunity: Use pip wheel caching in builder, multi-layer installs
   - Expected Impact: 20-30% faster builds (not size, but CI time)

4. **Python Bytecode Optimization**
   - Current: `PYTHONDONTWRITEBYTECODE=1` (disables .pyc)
   - Opportunity: Actually want compiled .pyc for faster startup
   - Expected Impact: 2-3s faster container startup

**Specific Recommendations:**

```dockerfile
# RECOMMENDATION 1: Split requirements.txt by dependency groups
# Create requirements-base.txt (core deps) and requirements-heavy.txt (ortools, ML libs)
# This enables better layer caching

# requirements-base.txt (changes rarely)
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
pydantic==2.5.3

# requirements-heavy.txt (changes very rarely)
ortools>=9.8
pandas>=2.0.0

# requirements-app.txt (changes frequently)
# Your custom packages here

# RECOMMENDATION 2: Optimize pip install
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements-base.txt && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements-heavy.txt && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements-app.txt

# RECOMMENDATION 3: Strip unnecessary files from site-packages
RUN find /opt/venv -type d -name "tests" -exec rm -rf {} + && \
    find /opt/venv -type d -name "__pycache__" -exec rm -rf {} + && \
    find /opt/venv -type f -name "*.pyc" -delete && \
    find /opt/venv -type f -name "*.pyo" -delete && \
    find /opt/venv -name "*.dist-info" -exec sh -c 'rm -rf "$1"/{RECORD,INSTALLER,direct_url.json}' _ {} \;

# RECOMMENDATION 4: Enable bytecode compilation for runtime
ENV PYTHONDONTWRITEBYTECODE=0
RUN python -m compileall -b /opt/venv/lib/python3.12/site-packages && \
    find /opt/venv -name "*.py" -type f -delete

# RECOMMENDATION 5: Add .dockerignore
__pycache__
*.py[cod]
*$py.class
*.so
.Python
.git
.pytest_cache
.coverage
htmlcov/
tests/
docs/
*.md
.env
.venv
venv/
alembic/versions/*.pyc
```

**Estimated Impact:**
- Image size reduction: **20-30%** (from ~500MB to ~350-400MB)
- Build time improvement: **30-40%** with split requirements caching
- Container startup: **2-4s faster** with precompiled bytecode
- CI/CD time: **3-5 minutes saved** on incremental builds

---

### 1.3 Multi-Stage Build Optimization for Faster CI

**Gordon AI Question:**
```
Analyze our CI/CD build times. We're using GitHub Actions with multi-stage Docker builds.
How can we optimize build caching and layer reuse to minimize CI build times?
Focus on BuildKit features and cache mount strategies.
```

**Expected Optimization Opportunities:**

1. **BuildKit Cache Mounts**
   - Current: Not using cache mounts
   - Opportunity: `--mount=type=cache` for pip, npm
   - Expected Impact: 40-60% faster builds on cache hit

2. **Layer Ordering**
   - Current: Good (dependencies before code)
   - Opportunity: Further split by change frequency
   - Expected Impact: 10-20% better cache hit rate

3. **Parallel Stage Builds**
   - Current: Sequential builds (backend, then frontend)
   - Opportunity: Build both in parallel in CI
   - Expected Impact: 30-40% faster total CI time

4. **Registry Caching**
   - Current: No explicit registry cache
   - Opportunity: Use GitHub Container Registry for layer caching
   - Expected Impact: 50-70% faster builds in CI

**Specific Recommendations:**

```dockerfile
# RECOMMENDATION 1: Enable BuildKit cache mounts (backend)
# syntax=docker/dockerfile:1.4

FROM dhi.io/python:3.12-dev AS builder
WORKDIR /app

# Use cache mount for pip downloads
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m venv /opt/venv && \
    /opt/venv/bin/pip install -r requirements.txt

# RECOMMENDATION 2: Enable BuildKit cache mounts (frontend)
# syntax=docker/dockerfile:1.4

FROM dhi.io/node:22-dev AS builder
WORKDIR /app

# Use cache mount for npm
RUN --mount=type=cache,target=/root/.npm \
    --mount=type=bind,source=package.json,target=package.json \
    --mount=type=bind,source=package-lock.json,target=package-lock.json \
    npm ci --legacy-peer-deps

# RECOMMENDATION 3: GitHub Actions workflow optimization
# .github/workflows/docker-build.yml
name: Docker Build Optimized

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
        with:
          driver-opts: |
            image=moby/buildkit:master
            network=host

      - name: Cache Docker layers
        uses: actions/cache@v4
        with:
          path: /tmp/.buildx-cache
          key: ${{ runner.os }}-buildx-${{ github.sha }}
          restore-keys: |
            ${{ runner.os }}-buildx-

      - name: Build Backend
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          file: ./backend/Dockerfile
          cache-from: type=local,src=/tmp/.buildx-cache
          cache-to: type=local,dest=/tmp/.buildx-cache-new,mode=max
          build-args: |
            BUILDKIT_INLINE_CACHE=1

      - name: Build Frontend (parallel)
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          file: ./frontend/Dockerfile
          cache-from: type=local,src=/tmp/.buildx-cache
          cache-to: type=local,dest=/tmp/.buildx-cache-new,mode=max
          build-args: |
            BUILDKIT_INLINE_CACHE=1

# RECOMMENDATION 4: docker-compose build optimization
# docker-compose.yml (add to services)
build:
  context: ./backend
  dockerfile: Dockerfile
  cache_from:
    - residency-scheduler-backend:latest
  args:
    BUILDKIT_INLINE_CACHE: 1
environment:
  DOCKER_BUILDKIT: 1
  COMPOSE_DOCKER_CLI_BUILD: 1
```

**Estimated Impact:**
- First build time: No change (~10-15 minutes)
- Cached build time: **60-75% reduction** (~3-5 minutes)
- Incremental build: **70-80% reduction** (~2-3 minutes)
- Parallel builds: **30-40% total CI time reduction**

---

### 1.4 BuildKit Features for Better Caching

**Gordon AI Question:**
```
What specific BuildKit features should we leverage for our FastAPI + Next.js stack?
We need better caching for pip wheels, npm packages, and layer reuse.
Show me advanced BuildKit syntax for our use case.
```

**Expected Optimization Opportunities:**

1. **Secret Mounting**
   - Current: Build-time environment variables
   - Opportunity: `--mount=type=secret` for tokens
   - Expected Impact: Security improvement, no layer bloat

2. **SSH Agent Forwarding**
   - Current: Not needed (public packages)
   - Opportunity: Future-proof for private repos
   - Expected Impact: Enables private package pulls without creds in layers

3. **Bind Mounts**
   - Current: COPY for all files
   - Opportunity: Read-only bind mounts for config files
   - Expected Impact: Faster builds, no unnecessary file copies

4. **Cache Invalidation Control**
   - Current: Timestamp-based invalidation
   - Opportunity: Content-hash based with `--mount=type=bind`
   - Expected Impact: 20-30% better cache hit rate

**Specific Recommendations:**

```dockerfile
# RECOMMENDATION 1: Advanced BuildKit syntax (backend)
# syntax=docker/dockerfile:1.4

FROM dhi.io/python:3.12-dev AS builder

WORKDIR /app

# Use bind mount for requirements (doesn't create layer)
# Use cache mount for pip (persists between builds)
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# If using private PyPI repo (future)
RUN --mount=type=secret,id=pip_token,env=PIP_INDEX_URL \
    --mount=type=cache,target=/root/.cache/pip \
    /opt/venv/bin/pip install private-package

# RECOMMENDATION 2: Advanced BuildKit syntax (frontend)
# syntax=docker/dockerfile:1.4

FROM dhi.io/node:22-dev AS builder

WORKDIR /app

# Bind mount for package files, cache mount for npm
RUN --mount=type=cache,target=/root/.npm,sharing=locked \
    --mount=type=bind,source=package.json,target=package.json \
    --mount=type=bind,source=package-lock.json,target=package-lock.json \
    npm ci --legacy-peer-deps && npm cache clean --force

# Copy source only after dependencies (better caching)
COPY . .

# Use cache for Next.js build cache
RUN --mount=type=cache,target=/app/.next/cache \
    npm run build

# RECOMMENDATION 3: BuildKit build command
# Use in CI/CD and local development
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

docker build \
  --secret id=pip_token,src=$HOME/.pip/token \
  --cache-from=type=registry,ref=ghcr.io/yourorg/scheduler-backend:latest \
  --cache-to=type=inline \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  -t residency-scheduler-backend:latest \
  ./backend

# RECOMMENDATION 4: docker-compose with BuildKit features
version: '3.8'
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      cache_from:
        - type=registry,ref=ghcr.io/yourorg/scheduler-backend:cache
      secrets:
        - pip_token
      args:
        BUILDKIT_INLINE_CACHE: 1

secrets:
  pip_token:
    file: ./.secrets/pip_token
```

**Estimated Impact:**
- Build security: **100% improvement** (no secrets in layers)
- Cache efficiency: **25-35% better hit rate**
- Build time (cache hit): **40-50% faster**
- Layer size: **10-15% reduction** (fewer unnecessary copies)

---

### 1.5 Unnecessary Layers in Dockerfiles

**Gordon AI Question:**
```
Analyze our Dockerfiles for unnecessary layers and layer bloat.
What RUN commands should be combined? Are we creating wasteful intermediate layers?
Focus on layer count reduction and squashing opportunities.
```

**Expected Optimization Opportunities:**

1. **RUN Command Consolidation**
   - Current: Multiple RUN commands for apt-get
   - Opportunity: Combine related operations
   - Expected Impact: 20-30% fewer layers

2. **COPY Optimization**
   - Current: Multiple COPY commands
   - Opportunity: Single COPY with .dockerignore
   - Expected Impact: 10-15% fewer layers

3. **Layer Size Distribution**
   - Current: Unknown without analysis
   - Opportunity: Identify large layers, split/optimize
   - Expected Impact: 15-25% size reduction in largest layers

4. **Squashing Consideration**
   - Current: No squashing
   - Opportunity: Squash final runtime stage
   - Expected Impact: 10-20% final image size reduction (trade-off with caching)

**Specific Recommendations:**

```dockerfile
# CURRENT BACKEND (HAS OPPORTUNITIES)
RUN apt-get update && apt-get install -y --no-install-recommends gcc
RUN apt-get install -y libpq-dev
RUN rm -rf /var/lib/apt/lists/*

# RECOMMENDATION 1: Consolidate RUN commands
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# CURRENT FRONTEND (GOOD, BUT CAN IMPROVE)
COPY package.json package-lock.json* ./
RUN npm ci --legacy-peer-deps && npm cache clean --force
COPY . .

# RECOMMENDATION 2: Optimize COPY with specific paths
COPY package*.json ./
COPY src/ ./src/
COPY public/ ./public/
COPY next.config.js tsconfig.json ./
# Everything else excluded by .dockerignore

# RECOMMENDATION 3: Backend layer analysis targets
# Run: docker history residency-scheduler-backend:latest --human
# Expected large layers to optimize:
# - pip install ortools (100-200MB)
# - pip install pandas/numpy (50-100MB)
# - COPY application code (20-50MB)

# RECOMMENDATION 4: Split heavy dependencies
# For ortools and data science packages, create base image
FROM dhi.io/python:3.12 AS base-ml
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir \
        ortools>=9.8 \
        pandas>=2.0.0 \
        numpy>=1.24.0
# Tag this as: residency-scheduler-base-ml:latest
# Update monthly, not on every build

FROM base-ml AS builder
# Now build time is 5-7 minutes instead of 12-15 minutes
```

**Layer Analysis Commands:**

```bash
# Analyze current layer sizes
docker history residency-scheduler-backend:latest --human --no-trunc
docker history residency-scheduler-frontend:latest --human --no-trunc

# Identify large files in images
docker run --rm residency-scheduler-backend:latest \
  find / -type f -size +10M -exec ls -lh {} \; 2>/dev/null

# Compare image sizes
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep residency

# Dive tool for interactive analysis
dive residency-scheduler-backend:latest
```

**Estimated Impact:**
- Layer count reduction: **30-40% fewer layers**
- Image size reduction: **15-25%** from consolidation
- Build time: **20-30% faster** with better caching
- Registry bandwidth: **25-35% reduction** in push/pull size

---

## 2. Resource Optimization

### 2.1 Resource Limits for FastAPI + Celery + PostgreSQL

**Gordon AI Question:**
```
Review our docker-compose.prod.yml resource limits.
Are the CPU and memory limits appropriate for:
- FastAPI (4 Uvicorn workers)
- Celery Worker (8 concurrency)
- Celery Beat (scheduler)
- PostgreSQL 15
- Redis 7

Current load: 50-100 concurrent users, 2000 schedule assignments/day.
```

**Current Configuration Analysis:**

| Service | CPU Limit | Memory Limit | Reservation | Assessment |
|---------|-----------|--------------|-------------|------------|
| PostgreSQL | 2.0 | 2G | 1.0 / 1G | **APPROPRIATE** |
| Redis | 1.0 | 768M | 0.5 / 512M | **OVER-PROVISIONED** |
| Backend | 2.0 | 2G | 1.0 / 1G | **APPROPRIATE** |
| Celery Worker | 4.0 | 3G | 2.0 / 2G | **SLIGHTLY HIGH** |
| Celery Beat | 0.5 | 512M | 0.25 / 256M | **APPROPRIATE** |
| Frontend | 1.0 | 1G | 0.5 / 512M | **APPROPRIATE** |

**Expected Optimization Opportunities:**

1. **Redis Right-Sizing**
   - Current: 768M limit, 512M maxmemory config
   - Opportunity: Reduce to 384M limit with 256M maxmemory
   - Expected Impact: 50% reduction (384MB freed for other services)

2. **Celery Worker Optimization**
   - Current: 4 CPU, 3G memory, 8 concurrency, 2 replicas
   - Opportunity: Reduce to 2 CPU, 2G memory with better worker config
   - Expected Impact: 33% reduction (2GB freed)

3. **Connection Pool Tuning**
   - Current: Default connection pools
   - Opportunity: Tune pool sizes to match worker count
   - Expected Impact: 20-30% reduction in idle connections

4. **Monitoring and Auto-Scaling**
   - Current: Fixed resource limits
   - Opportunity: Add Prometheus metrics for right-sizing
   - Expected Impact: Data-driven optimization (10-20% overall reduction)

**Specific Recommendations:**

```yaml
# RECOMMENDATION 1: Optimized Redis Configuration
services:
  redis:
    command: >
      redis-server
      --appendonly yes
      --appendfsync everysec
      --maxmemory 256mb              # REDUCED from 512mb
      --maxmemory-policy allkeys-lru
      --save 900 1 300 10 60 10000   # ADD: persistence tuning
      --requirepass ${REDIS_PASSWORD}
      --tcp-backlog 511
      --timeout 300
      --tcp-keepalive 60
      --maxclients 1000              # ADD: connection limit
    deploy:
      resources:
        limits:
          cpus: '0.5'                # REDUCED from 1.0
          memory: 384M               # REDUCED from 768M
        reservations:
          cpus: '0.25'               # REDUCED from 0.5
          memory: 256M               # REDUCED from 512M

# RECOMMENDATION 2: Optimized Celery Worker Configuration
services:
  celery-worker:
    environment:
      CELERY_WORKER_CONCURRENCY: "4"  # REDUCED from 8
      CELERY_WORKER_PREFETCH_MULTIPLIER: "2"  # INCREASED from 1
      CELERY_WORKER_MAX_TASKS_PER_CHILD: "500"  # REDUCED from 1000
      CELERY_POOL: "prefork"          # ADD: explicit pool type
      CELERYD_MAX_MEMORY_PER_CHILD: "400000"  # ADD: 400MB per child limit
    deploy:
      resources:
        limits:
          cpus: '2.0'                # REDUCED from 4.0
          memory: 2G                 # REDUCED from 3G
        reservations:
          cpus: '1.0'                # REDUCED from 2.0
          memory: 1G                 # REDUCED from 2G
      replicas: 2                    # KEEP: good for redundancy
    command: >
      celery -A app.core.celery_app worker
      --loglevel=info
      -Q default,resilience,notifications
      --concurrency=4                 # MATCH environment variable
      --max-tasks-per-child=500
      --max-memory-per-child=400000
      --time-limit=600
      --soft-time-limit=540
      --without-gossip                # ADD: reduce network chatter
      --without-mingle                # ADD: faster startup

# RECOMMENDATION 3: PostgreSQL Connection Pool Tuning
services:
  db:
    command: >
      postgres
      -c max_connections=100          # ADD: limit connections
      -c shared_buffers=512MB         # ADD: 25% of memory
      -c effective_cache_size=1536MB  # ADD: 75% of memory
      -c maintenance_work_mem=128MB   # ADD: maintenance operations
      -c work_mem=5MB                 # ADD: per-query memory
      -c wal_buffers=16MB             # ADD: write-ahead log
      -c random_page_cost=1.1         # ADD: SSD optimization
      -c effective_io_concurrency=200 # ADD: SSD optimization
    deploy:
      resources:
        limits:
          cpus: '2.0'                # KEEP: appropriate for workload
          memory: 2G                 # KEEP: appropriate for workload
        reservations:
          cpus: '1.0'
          memory: 1G

# RECOMMENDATION 4: Backend Connection Pool Configuration
# Add to backend/app/db/session.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,              # Base pool size (matches Uvicorn workers * 2.5)
    max_overflow=20,           # Additional connections on burst
    pool_pre_ping=True,        # Verify connections before use
    pool_recycle=3600,         # Recycle connections after 1 hour
    echo=False,                # Disable SQL logging in production
    connect_args={
        "server_settings": {
            "application_name": "residency_scheduler_backend",
            "jit": "off"       # Disable JIT for faster simple queries
        }
    }
)
```

**Resource Calculation Guide:**

```python
# Backend (FastAPI) Resources
# Formula: (workers * avg_memory_per_worker) + base_overhead
workers = 4  # Uvicorn workers
memory_per_worker = 150  # MB (FastAPI + SQLAlchemy + your app)
base_overhead = 200  # MB (Python interpreter, imports)
total_memory = (workers * memory_per_worker) + base_overhead
# Result: ~800MB, rounded to 1GB with headroom

# Celery Worker Resources
# Formula: (concurrency * avg_memory_per_task) + base_overhead
concurrency = 4  # Worker processes
memory_per_task = 100  # MB (task execution)
base_overhead = 200  # MB (Celery + imports)
max_memory = (concurrency * memory_per_task) + base_overhead + (concurrency * 300)
# Result: ~1.6GB, rounded to 2GB with headroom

# PostgreSQL Resources
# Formula: shared_buffers + work_mem * max_connections + overhead
shared_buffers = 512  # MB (25% of total)
work_mem = 5  # MB per connection
max_connections = 100
overhead = 200  # MB (OS, caching)
total_memory = shared_buffers + (work_mem * max_connections / 10) + overhead
# Result: ~1.2GB, rounded to 2GB with headroom

# Redis Resources
# Formula: maxmemory + overhead + persistence
maxmemory = 256  # MB (configured limit)
overhead = 64  # MB (Redis overhead)
persistence = 64  # MB (RDB/AOF buffers)
total_memory = maxmemory + overhead + persistence
# Result: ~384MB
```

**Estimated Impact:**
- Redis: **Save 384MB** (50% reduction)
- Celery Worker: **Save 2GB total** (33% reduction, 1GB per replica)
- Total Memory Savings: **~2.4GB** across all services
- Cost Savings: **$20-40/month** on cloud infrastructure
- Performance: **No degradation** at current load (50-100 concurrent users)

---

### 2.2 Redis Memory Optimization

**Gordon AI Question:**
```
How should we optimize Redis for our use case?
Using Redis for: Celery broker/backend, rate limiting, session caching.
Current config: 256MB maxmemory, allkeys-lru eviction.
Are there better configurations for a scheduling application?
```

**Expected Optimization Opportunities:**

1. **Eviction Policy Tuning**
   - Current: `allkeys-lru` (evict any key, least recently used)
   - Opportunity: Split by database number with different policies
   - Expected Impact: 20-30% better cache hit rate

2. **Persistence Strategy**
   - Current: AOF everysec (disk writes every second)
   - Opportunity: Tune for durability vs performance
   - Expected Impact: 40-50% faster writes (if relaxed)

3. **Memory Usage Analysis**
   - Current: Unknown memory distribution
   - Opportunity: Analyze by key pattern
   - Expected Impact: 15-25% memory reduction by removing waste

4. **Connection Optimization**
   - Current: Default connection settings
   - Opportunity: Tune timeouts and keepalives
   - Expected Impact: 30-40% fewer idle connections

**Specific Recommendations:**

```yaml
# RECOMMENDATION 1: Multi-Database Strategy with Separate Policies
services:
  redis:
    command: >
      redis-server
      # Database 0: Celery (no eviction, must not lose tasks)
      # Database 1: Rate limiting (volatile-ttl, auto-expire)
      # Database 2: Session caching (allkeys-lru, can evict)
      --databases 8
      --maxmemory 256mb
      --maxmemory-policy noeviction          # DEFAULT: don't evict (Celery safety)
      --appendonly yes
      --appendfsync everysec                 # Balance durability/performance
      --auto-aof-rewrite-percentage 100      # Rewrite AOF when 100% larger
      --auto-aof-rewrite-min-size 64mb       # Minimum size to trigger rewrite
      --save 900 1 300 10 60 10000          # RDB snapshots (backup)
      --requirepass ${REDIS_PASSWORD}
      --tcp-backlog 511
      --timeout 300                          # Close idle connections after 5min
      --tcp-keepalive 60                     # Keepalive packets every 60s
      --maxclients 1000                      # Connection limit
      --slowlog-log-slower-than 10000        # Log queries >10ms
      --slowlog-max-len 128                  # Keep last 128 slow queries
      --latency-monitor-threshold 100        # Monitor latency >100ms
      --notify-keyspace-events Ex            # Enable expiration events

# RECOMMENDATION 2: Update Application Redis Configuration
# backend/app/core/config.py

class Settings(BaseSettings):
    # Celery: Database 0 (no eviction, critical)
    CELERY_BROKER_URL: str = "redis://:password@redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://:password@redis:6379/0"

    # Rate Limiting: Database 1 (TTL-based eviction)
    RATE_LIMIT_REDIS_DB: int = 1
    RATE_LIMIT_REDIS_URL: str = "redis://:password@redis:6379/1"

    # Session/Cache: Database 2 (LRU eviction)
    CACHE_REDIS_DB: int = 2
    CACHE_REDIS_URL: str = "redis://:password@redis:6379/2"

    # Connection pool settings
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_HEALTH_CHECK_INTERVAL: int = 30

# RECOMMENDATION 3: Redis Client Optimization
# backend/app/core/redis_client.py

from redis.asyncio import ConnectionPool, Redis
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff

# Celery Redis (DB 0) - strict durability
celery_pool = ConnectionPool.from_url(
    settings.CELERY_BROKER_URL,
    max_connections=50,
    socket_timeout=5,
    socket_connect_timeout=5,
    socket_keepalive=True,
    socket_keepalive_options={
        1: 1,  # TCP_KEEPIDLE
        2: 1,  # TCP_KEEPINTVL
        3: 3,  # TCP_KEEPCNT
    },
    retry=Retry(ExponentialBackoff(), 3),
    health_check_interval=30,
    decode_responses=False,  # Celery needs bytes
)

# Cache Redis (DB 2) - performance optimized
cache_pool = ConnectionPool.from_url(
    settings.CACHE_REDIS_URL,
    max_connections=30,
    socket_timeout=2,  # Faster timeout for cache
    socket_connect_timeout=2,
    socket_keepalive=True,
    retry=Retry(ExponentialBackoff(), 1),  # Fewer retries for cache
    health_check_interval=30,
    decode_responses=True,  # Easier string handling
)

celery_redis = Redis(connection_pool=celery_pool)
cache_redis = Redis(connection_pool=cache_pool)

# RECOMMENDATION 4: Memory Analysis Script
# scripts/redis-memory-analysis.sh

#!/bin/bash
# Analyze Redis memory usage by pattern

docker-compose exec redis redis-cli -a "$REDIS_PASSWORD" <<EOF
INFO memory
MEMORY STATS
MEMORY DOCTOR

# Analyze by key pattern
EVAL "
local keys = redis.call('KEYS', ARGV[1])
local total = 0
for i=1,#keys do
  local mem = redis.call('MEMORY', 'USAGE', keys[i])
  total = total + (mem or 0)
end
return total
" 0 "celery-task-meta-*"

# Show largest keys
MEMORY USAGE "celery-task-meta-*" SAMPLES 5
EOF

# Expected output interpretation:
# - celery-task-meta-*: 50-100MB (task results, can set shorter TTL)
# - rate_limit:*: 10-20MB (short TTL, OK)
# - schedule:cache:*: 30-50MB (schedule data, good)
```

**Redis Eviction Policy Guide:**

| Use Case | Database | Eviction Policy | Rationale |
|----------|----------|-----------------|-----------|
| Celery Tasks | 0 | `noeviction` | Never lose pending tasks |
| Task Results | 0 | `noeviction` + short TTL | Expire old results automatically |
| Rate Limiting | 1 | `volatile-ttl` | Evict based on TTL, always has TTL |
| Session Cache | 2 | `allkeys-lru` | Can evict any key, recreatable |
| Schedule Cache | 2 | `allkeys-lru` | Can evict, DB is source of truth |

**Memory Optimization Checklist:**

```bash
# 1. Set reasonable TTLs on Celery task results
# backend/app/core/celery_config.py
result_expires = 3600  # 1 hour (default: 1 day)

# 2. Clean up old keys periodically
EVAL "return redis.call('DEL', unpack(redis.call('KEYS', 'celery-task-meta-*')))" 0

# 3. Monitor memory usage
watch -n 5 'docker-compose exec redis redis-cli -a "$REDIS_PASSWORD" INFO memory'

# 4. Track eviction stats
docker-compose exec redis redis-cli -a "$REDIS_PASSWORD" INFO stats | grep evicted

# Expected: evicted_keys should be 0 for DB 0, low for DB 1/2
```

**Estimated Impact:**
- Memory usage: **20-30% more efficient** (better allocation)
- Cache hit rate: **15-25% improvement** (smarter eviction)
- Latency: **10-20% reduction** (optimized persistence)
- Connection overhead: **30-40% fewer idle connections**
- Task reliability: **100% improvement** (no task eviction)

---

### 2.3 Health Check Interval Optimization

**Gordon AI Question:**
```
Analyze our health check configurations across all services.
Are the intervals appropriate? Are we over-checking or under-checking?
Focus on balancing fast failure detection with resource overhead.
```

**Current Health Check Analysis:**

| Service | Interval | Timeout | Retries | Start Period | Assessment |
|---------|----------|---------|---------|--------------|------------|
| PostgreSQL | 10s | 5s | 5 | 10s | **TOO FREQUENT** |
| Redis | 10s | 5s | 5 | 5s | **TOO FREQUENT** |
| Backend | 30s | 10s | 3 | 40s | **GOOD** |
| Celery Worker | 30s | 10s | 3 | 30s | **GOOD** |
| Frontend | 30s | 10s | 3 | 40s | **GOOD** |
| Nginx | 30s | 10s | 3 | N/A | **GOOD** |

**Expected Optimization Opportunities:**

1. **Database Health Check Frequency**
   - Current: Every 10 seconds
   - Opportunity: Reduce to 30 seconds (databases rarely fail suddenly)
   - Expected Impact: 66% reduction in health check overhead

2. **Redis Health Check Frequency**
   - Current: Every 10 seconds
   - Opportunity: Reduce to 20-30 seconds
   - Expected Impact: 50-66% reduction in overhead

3. **Health Check Commands**
   - Current: Using `pg_isready`, `redis-cli ping`
   - Opportunity: These are already lightweight (OK)
   - Expected Impact: No change needed

4. **Startup Period Tuning**
   - Current: PostgreSQL 10s (probably too short)
   - Opportunity: Increase to 30s to avoid false failures
   - Expected Impact: Fewer false-positive failures on startup

**Specific Recommendations:**

```yaml
# RECOMMENDATION 1: Optimized Database Health Checks
services:
  db:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U scheduler -d residency_scheduler"]
      interval: 30s          # INCREASED from 10s (stable service)
      timeout: 5s            # KEEP: reasonable for DB query
      retries: 3             # REDUCED from 5 (fail faster)
      start_period: 30s      # INCREASED from 10s (allow startup time)

  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 20s          # INCREASED from 10s (stable service)
      timeout: 3s            # REDUCED from 5s (ping is instant)
      retries: 3             # REDUCED from 5 (fail faster)
      start_period: 10s      # KEEP: Redis starts fast

# RECOMMENDATION 2: Enhanced Application Health Checks
services:
  backend:
    healthcheck:
      # Add custom health endpoint that checks DB + Redis
      test: ["CMD-SHELL", "curl -f http://localhost:8000/health/ready || exit 1"]
      interval: 30s          # KEEP: good balance
      timeout: 10s           # KEEP: allows DB query
      retries: 3             # KEEP: appropriate
      start_period: 40s      # KEEP: allows migrations

  celery-worker:
    healthcheck:
      test: ["CMD-SHELL", "celery -A app.core.celery_app inspect ping -d celery@$$HOSTNAME -t 5"]
      interval: 60s          # INCREASED from 30s (workers rarely fail)
      timeout: 10s           # KEEP: allows Celery response
      retries: 3             # KEEP: appropriate
      start_period: 30s      # KEEP: allows worker initialization

  celery-beat:
    # ADD: Health check for beat scheduler
    healthcheck:
      test: ["CMD-SHELL", "celery -A app.core.celery_app inspect scheduled | grep -q 'empty' || exit 0"]
      interval: 120s         # LONG: beat rarely fails, less critical
      timeout: 10s
      retries: 2
      start_period: 30s

  frontend:
    healthcheck:
      # Use Node built-in HTTP check (no curl in distroless)
      test: ["CMD-SHELL", "node -e \"require('http').get('http://localhost:3000/api/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))\""]
      interval: 30s          # KEEP: good balance
      timeout: 10s           # KEEP: allows Next.js response
      retries: 3             # KEEP: appropriate
      start_period: 40s      # KEEP: allows build

# RECOMMENDATION 3: Add Comprehensive Health Endpoints
# backend/app/api/routes/health.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.redis_client import cache_redis
import time

router = APIRouter()

@router.get("/health")
async def health():
    """Liveness probe - is the service running?"""
    return {"status": "ok"}

@router.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    """Readiness probe - is the service ready to handle requests?"""
    health_status = {
        "status": "ok",
        "checks": {},
        "timestamp": time.time()
    }

    # Check database
    try:
        await db.execute("SELECT 1")
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = f"error: {str(e)}"

    # Check Redis
    try:
        await cache_redis.ping()
        health_status["checks"]["redis"] = "ok"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["redis"] = f"error: {str(e)}"

    status_code = status.HTTP_200_OK if health_status["status"] == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
    return health_status, status_code

@router.get("/health/startup")
async def startup():
    """Startup probe - has the service finished initialization?"""
    # Check if migrations complete, configs loaded, etc.
    return {"status": "ready"}

# RECOMMENDATION 4: Frontend Health Endpoint
# frontend/pages/api/health.ts

export default async function handler(req, res) {
  // Simple liveness check
  if (req.url === '/api/health') {
    return res.status(200).json({ status: 'ok' });
  }

  // Readiness check - verify backend connectivity
  if (req.url === '/api/health/ready') {
    try {
      const backendResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/health`,
        { signal: AbortSignal.timeout(5000) }
      );

      if (backendResponse.ok) {
        return res.status(200).json({
          status: 'ok',
          backend: 'connected'
        });
      } else {
        return res.status(503).json({
          status: 'degraded',
          backend: 'unavailable'
        });
      }
    } catch (error) {
      return res.status(503).json({
        status: 'degraded',
        backend: 'error'
      });
    }
  }
}
```

**Health Check Overhead Analysis:**

```bash
# Calculate health check overhead

# Current (PostgreSQL + Redis):
# (2 services) * (6 checks/minute) * (5ms avg execution) * (60 min) = 3600 checks/hour
# Overhead: ~18 seconds of check execution per hour

# Optimized (PostgreSQL + Redis):
# PostgreSQL: (1 service) * (2 checks/minute) * (5ms) * (60 min) = 600 checks/hour
# Redis: (1 service) * (3 checks/minute) * (2ms) * (60 min) = 360 checks/hour
# Overhead: ~4.8 seconds of check execution per hour
# Reduction: 73% fewer checks

# Failure Detection Comparison:
# Current: Detect failure in 10s + (5 retries * 5s) = 35s worst case
# Optimized: Detect failure in 30s + (3 retries * 5s) = 45s worst case
# Trade-off: 10s slower detection, but services rarely fail suddenly
```

**Health Check Best Practices:**

| Service Type | Liveness Interval | Readiness Interval | Rationale |
|--------------|-------------------|-------------------|-----------|
| Database | 30-60s | 30s | Rarely fails, expensive to check often |
| Cache (Redis) | 20-30s | 20s | Fast checks, but rarely fails |
| Application | 15-30s | 30s | Can fail, but HTTP check is cheap |
| Worker | 60-120s | 60s | Asynchronous, less time-sensitive |
| Scheduler | 120-300s | 120s | Very stable, low criticality |

**Estimated Impact:**
- Health check overhead: **70-75% reduction** (3600 → 900 checks/hour)
- CPU usage: **5-10% reduction** on database services
- Network overhead: **60-70% reduction** in health check traffic
- False positive failures: **50% reduction** (better start periods)
- Failure detection time: **+10s** (acceptable trade-off)

---

## 3. Best Practices

### 3.1 Production Best Practices for docker-compose.prod.yml

**Gordon AI Question:**
```
Review our docker-compose.prod.yml for production best practices.
Are we following Docker production recommendations for:
- Security (non-root users, read-only filesystems)
- Reliability (restart policies, health checks)
- Observability (logging, metrics)
- Resource management
What are we missing?
```

**Expected Optimization Opportunities:**

1. **Security Hardening**
   - Current: Backend/frontend run as non-root (good)
   - Opportunity: Read-only filesystems, capability dropping
   - Expected Impact: 80% attack surface reduction

2. **Logging Strategy**
   - Current: JSON file driver with rotation (good)
   - Opportunity: Centralized logging, structured logs
   - Expected Impact: 60% easier troubleshooting

3. **Secrets Management**
   - Current: Environment variables from .env
   - Opportunity: Docker secrets, external secret managers
   - Expected Impact: 90% security improvement for credentials

4. **Network Segmentation**
   - Current: Single bridge network
   - Opportunity: Separate frontend/backend/data networks
   - Expected Impact: 50% reduced blast radius

**Specific Recommendations:**

```yaml
# RECOMMENDATION 1: Security Hardening
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    security_opt:
      - no-new-privileges:true        # ADD: prevent privilege escalation
    cap_drop:
      - ALL                            # ADD: drop all capabilities
    cap_add:
      - NET_BIND_SERVICE              # ADD: only allow binding to ports
    read_only: true                    # ADD: read-only root filesystem
    tmpfs:
      - /tmp                           # ADD: writable tmp
      - /app/.cache                    # ADD: writable cache
    volumes:
      - backend_logs:/app/logs        # ADD: persistent logs
    environment:
      LOG_LEVEL: "info"
      PYTHONDONTWRITEBYTECODE: "1"
      PYTHONUNBUFFERED: "1"
    networks:
      - frontend-network              # ADD: separate networks
      - backend-network
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
          pids: 100                    # ADD: limit process count
        reservations:
          cpus: '1.0'
          memory: 1G

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: always
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp
      - /app/.next/cache              # Next.js cache
    networks:
      - frontend-network              # Only frontend network
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
          pids: 50
        reservations:
          cpus: '0.5'
          memory: 512M

  db:
    image: postgres:15-alpine
    restart: always
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - DAC_OVERRIDE
      - SETGID
      - SETUID
      - FOWNER                        # Postgres needs these
    read_only: false                  # Postgres needs writable FS
    networks:
      - backend-network               # Only backend network
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups/postgres:/backups:ro  # READ-ONLY backup mount
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
          pids: 200                   # Postgres connection limit
        reservations:
          cpus: '1.0'
          memory: 1G

# RECOMMENDATION 2: Secrets Management
secrets:
  db_password:
    file: ./secrets/db_password.txt
  redis_password:
    file: ./secrets/redis_password.txt
  secret_key:
    file: ./secrets/secret_key.txt

services:
  backend:
    secrets:
      - db_password
      - redis_password
      - secret_key
    environment:
      DATABASE_URL_FILE: /run/secrets/db_password  # Use _FILE suffix
      REDIS_PASSWORD_FILE: /run/secrets/redis_password
      SECRET_KEY_FILE: /run/secrets/secret_key

# Update backend code to read from _FILE variables
# backend/app/core/config.py

class Settings(BaseSettings):
    @property
    def DATABASE_URL(self) -> str:
        if hasattr(self, 'DATABASE_URL_FILE'):
            with open(self.DATABASE_URL_FILE) as f:
                return f.read().strip()
        return os.getenv('DATABASE_URL')

# RECOMMENDATION 3: Network Segmentation
networks:
  frontend-network:
    driver: bridge
    internal: false                   # Internet-facing
    ipam:
      config:
        - subnet: 172.28.1.0/24

  backend-network:
    driver: bridge
    internal: true                    # Internal only
    ipam:
      config:
        - subnet: 172.28.2.0/24

  data-network:
    driver: bridge
    internal: true                    # Database access only
    ipam:
      config:
        - subnet: 172.28.3.0/24

services:
  frontend:
    networks:
      - frontend-network              # Public + backend API
      - backend-network

  backend:
    networks:
      - backend-network               # Frontend + data
      - data-network

  db:
    networks:
      - data-network                  # Backend only

  redis:
    networks:
      - data-network                  # Backend + Celery only

# RECOMMENDATION 4: Structured Logging & Observability
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "20m"
        max-file: "5"
        compress: "true"
        labels: "service,environment"  # ADD: labels
        tag: "{{.Name}}/{{.ID}}"      # ADD: container tagging
    labels:
      com.example.service: "backend"
      com.example.environment: "production"
      com.example.version: "${VERSION:-latest}"
    environment:
      LOG_LEVEL: "info"
      LOG_FORMAT: "json"               # ADD: structured logging
      LOG_OUTPUT: "stdout"             # ADD: container-friendly

# Add Prometheus metrics
  prometheus:
    image: prom/prometheus:latest
    container_name: residency-scheduler-prometheus
    restart: always
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    networks:
      - backend-network
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  grafana:
    image: grafana/grafana:latest
    container_name: residency-scheduler-grafana
    restart: always
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
      GF_INSTALL_PLUGINS: "grafana-clock-panel,grafana-simple-json-datasource"
    networks:
      - backend-network
    depends_on:
      - prometheus
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M

volumes:
  prometheus_data:
  grafana_data:
  backend_logs:

# RECOMMENDATION 5: Backup and Disaster Recovery
services:
  backup:
    image: postgres:15-alpine
    container_name: residency-scheduler-backup
    restart: "no"  # Run manually or via cron
    networks:
      - data-network
    volumes:
      - ./backups:/backups
      - ./scripts/backup.sh:/backup.sh:ro
    environment:
      BACKUP_RETENTION_DAYS: "30"
    entrypoint: ["/backup.sh"]
    depends_on:
      - db

# scripts/backup.sh
#!/bin/bash
set -e

BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Dump database
PGPASSWORD="$DB_PASSWORD" pg_dump \
  -h db \
  -U scheduler \
  -d residency_scheduler \
  --no-owner \
  --no-acl \
  | gzip > "$BACKUP_FILE"

# Delete old backups
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +$BACKUP_RETENTION_DAYS -delete

echo "Backup completed: $BACKUP_FILE"
```

**Production Checklist:**

- [ ] **Security**
  - [ ] Non-root users (✓ Already done)
  - [ ] Read-only filesystems where possible
  - [ ] Capability dropping
  - [ ] No new privileges
  - [ ] Docker secrets for credentials
  - [ ] Network segmentation
  - [ ] TLS/SSL certificates configured
  - [ ] Firewall rules configured

- [ ] **Reliability**
  - [ ] Restart policies set to `always`
  - [ ] Health checks configured
  - [ ] Startup probes for slow-starting services
  - [ ] Resource limits set
  - [ ] Resource reservations set
  - [ ] Graceful shutdown handlers
  - [ ] Database connection pooling

- [ ] **Observability**
  - [ ] Structured logging (JSON)
  - [ ] Log rotation configured
  - [ ] Centralized logging (optional: ELK/Loki)
  - [ ] Prometheus metrics exposed
  - [ ] Grafana dashboards configured
  - [ ] Alerting rules defined
  - [ ] Distributed tracing (optional: Jaeger)

- [ ] **Data Management**
  - [ ] Persistent volumes configured
  - [ ] Backup strategy implemented
  - [ ] Backup retention policy defined
  - [ ] Database migration strategy
  - [ ] Data encryption at rest
  - [ ] Data encryption in transit

- [ ] **Performance**
  - [ ] Resource limits tuned
  - [ ] Connection pools optimized
  - [ ] Caching strategy implemented
  - [ ] CDN for static assets (if applicable)
  - [ ] Database indexes optimized
  - [ ] Query performance monitored

**Estimated Impact:**
- Security posture: **80% improvement** (defense in depth)
- Incident response time: **60% faster** (better observability)
- Downtime prevention: **40% reduction** (health checks + monitoring)
- Recovery time: **70% faster** (automated backups)
- Compliance: **100% improvement** (audit logs, encryption)

---

### 3.2 Logging Configuration Recommendations

**Gordon AI Question:**
```
Review our logging configuration across all services.
Are we logging too much? Too little? Are log formats consistent?
Should we implement centralized logging for a production deployment?
```

**Current Logging Analysis:**

| Service | Driver | Max Size | Max Files | Compression | Assessment |
|---------|--------|----------|-----------|-------------|------------|
| PostgreSQL | json-file | 10m | 5 | ✓ | **TOO VERBOSE** |
| Redis | json-file | 5m | 3 | ✓ | **GOOD** |
| Backend | json-file | 20m | 5 | ✓ | **GOOD** |
| Celery Worker | json-file | 15m | 5 | ✓ | **GOOD** |
| Celery Beat | json-file | 5m | 3 | ✓ | **GOOD** |
| Frontend | json-file | 10m | 3 | ✓ | **GOOD** |
| Nginx | json-file | 20m | 5 | ✓ | **GOOD** |

**Expected Optimization Opportunities:**

1. **Structured Logging**
   - Current: Plain text logs (Python logging, Next.js console)
   - Opportunity: JSON structured logs for all services
   - Expected Impact: 300% improvement in log searchability

2. **Log Levels**
   - Current: INFO level in production (verbose)
   - Opportunity: WARNING for most, INFO for critical services
   - Expected Impact: 60-70% reduction in log volume

3. **Log Aggregation**
   - Current: Per-container JSON files
   - Opportunity: Centralized logging (Loki, ELK, or CloudWatch)
   - Expected Impact: 80% easier troubleshooting

4. **Sensitive Data Redaction**
   - Current: Unknown if PHI is being logged
   - Opportunity: Automatic redaction of sensitive fields
   - Expected Impact: 100% compliance improvement

**Specific Recommendations:**

```yaml
# RECOMMENDATION 1: Centralized Logging with Loki (Lightweight)
version: '3.8'

services:
  # Loki - Log Aggregation
  loki:
    image: grafana/loki:latest
    container_name: residency-scheduler-loki
    restart: always
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki
      - ./loki/loki-config.yml:/etc/loki/local-config.yaml:ro
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - backend-network
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M

  # Promtail - Log Shipper
  promtail:
    image: grafana/promtail:latest
    container_name: residency-scheduler-promtail
    restart: always
    volumes:
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock
      - ./promtail/promtail-config.yml:/etc/promtail/config.yml:ro
    command: -config.file=/etc/promtail/config.yml
    networks:
      - backend-network
    depends_on:
      - loki

  # Update existing services to use Loki driver
  backend:
    logging:
      driver: loki
      options:
        loki-url: "http://loki:3100/loki/api/v1/push"
        loki-retries: "5"
        loki-batch-size: "400"
        loki-external-labels: "service=backend,environment=production"
        max-size: "20m"  # Fallback to local logs
        max-file: "3"
        compress: "true"

volumes:
  loki_data:

# RECOMMENDATION 2: Structured Logging Configuration
# backend/app/core/logging_config.py

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger

class HealthCheckFilter(logging.Filter):
    """Filter out noisy health check logs"""
    def filter(self, record):
        return '/health' not in record.getMessage()

class SensitiveDataFilter(logging.Filter):
    """Redact sensitive data from logs"""
    SENSITIVE_FIELDS = [
        'password', 'ssn', 'social_security', 'credit_card',
        'api_key', 'secret', 'token', 'auth'
    ]

    def filter(self, record):
        if hasattr(record, 'msg') and isinstance(record.msg, dict):
            record.msg = self._redact_dict(record.msg)
        return True

    def _redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively redact sensitive fields"""
        redacted = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                redacted[key] = '***REDACTED***'
            elif isinstance(value, dict):
                redacted[key] = self._redact_dict(value)
            else:
                redacted[key] = value
        return redacted

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional context"""
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()

        # Add log level
        log_record['level'] = record.levelname

        # Add logger name
        log_record['logger'] = record.name

        # Add file and line number
        log_record['file'] = f"{record.filename}:{record.lineno}"

        # Add function name
        log_record['function'] = record.funcName

        # Add service metadata
        log_record['service'] = 'residency-scheduler-backend'
        log_record['environment'] = 'production'

def setup_logging(log_level: str = "INFO"):
    """Configure structured logging for the application"""

    # Create formatter
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(logger)s %(file)s %(function)s %(message)s'
    )

    # Console handler (stdout for containers)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(HealthCheckFilter())
    console_handler.addFilter(SensitiveDataFilter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('celery').setLevel(logging.INFO)

    return root_logger

# Usage in app/main.py
from app.core.logging_config import setup_logging
setup_logging(log_level=os.getenv('LOG_LEVEL', 'INFO'))

# RECOMMENDATION 3: Frontend Structured Logging
# frontend/lib/logger.ts

interface LogContext {
  service: string;
  environment: string;
  timestamp: string;
  level: string;
  message: string;
  [key: string]: any;
}

class StructuredLogger {
  private service = 'residency-scheduler-frontend';
  private environment = process.env.NODE_ENV || 'development';

  private log(level: string, message: string, context?: Record<string, any>) {
    const logEntry: LogContext = {
      service: this.service,
      environment: this.environment,
      timestamp: new Date().toISOString(),
      level,
      message,
      ...this.redactSensitiveData(context || {}),
    };

    // In production, send to logging service
    if (this.environment === 'production') {
      console.log(JSON.stringify(logEntry));
      // Optional: Send to backend logging endpoint
      // fetch('/api/logs', { method: 'POST', body: JSON.stringify(logEntry) });
    } else {
      // Pretty print in development
      console[level.toLowerCase()](message, context);
    }
  }

  private redactSensitiveData(data: Record<string, any>): Record<string, any> {
    const sensitiveFields = ['password', 'token', 'apiKey', 'secret'];
    const redacted = { ...data };

    for (const field of sensitiveFields) {
      if (field in redacted) {
        redacted[field] = '***REDACTED***';
      }
    }

    return redacted;
  }

  info(message: string, context?: Record<string, any>) {
    this.log('INFO', message, context);
  }

  warn(message: string, context?: Record<string, any>) {
    this.log('WARN', message, context);
  }

  error(message: string, context?: Record<string, any>) {
    this.log('ERROR', message, context);
  }

  debug(message: string, context?: Record<string, any>) {
    if (this.environment !== 'production') {
      this.log('DEBUG', message, context);
    }
  }
}

export const logger = new StructuredLogger();

// Usage
import { logger } from '@/lib/logger';

logger.info('Schedule generated', {
  scheduleId: '123',
  duration: 450,
  assignmentCount: 730
});

logger.error('Failed to fetch schedule', {
  error: error.message,
  scheduleId: '123'
});

# RECOMMENDATION 4: Loki Configuration
# loki/loki-config.yml

auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
  chunk_idle_period: 5m
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb:
    directory: /loki/index

  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h  # 7 days
  ingestion_rate_mb: 10
  ingestion_burst_size_mb: 20

chunk_store_config:
  max_look_back_period: 720h  # 30 days

table_manager:
  retention_deletes_enabled: true
  retention_period: 720h  # 30 days

# RECOMMENDATION 5: Promtail Configuration
# promtail/promtail-config.yml

server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'stream'
      - source_labels: ['__meta_docker_container_label_com_docker_compose_service']
        target_label: 'service'
    pipeline_stages:
      # Parse JSON logs
      - json:
          expressions:
            timestamp: timestamp
            level: level
            message: message
            service: service
      # Extract log level
      - labels:
          level:
          service:
      # Add timestamp
      - timestamp:
          source: timestamp
          format: RFC3339Nano
```

**Log Level Guidelines:**

| Service | Development | Production | Rationale |
|---------|-------------|------------|-----------|
| Backend | DEBUG | INFO | Detailed API logs helpful |
| Celery Worker | INFO | WARNING | Only log important events |
| Celery Beat | INFO | WARNING | Scheduled tasks log once |
| PostgreSQL | INFO | WARNING | Reduce query logging |
| Redis | NOTICE | WARNING | Minimal logging needed |
| Frontend | DEBUG | ERROR | Client logs less critical |
| Nginx | INFO | WARN | Access logs externalized |

**Log Retention Strategy:**

```yaml
# Per-service retention based on importance
backend:
  local_retention: 7 days    # Docker JSON files
  loki_retention: 30 days    # Centralized logs
  archive_retention: 1 year  # Compliance (S3/backup)

database:
  local_retention: 14 days   # Query logs
  loki_retention: 30 days
  archive_retention: 1 year

security:
  local_retention: 30 days   # Auth, access logs
  loki_retention: 90 days
  archive_retention: 7 years # Compliance requirement
```

**Estimated Impact:**
- Log volume reduction: **60-70%** (smarter log levels)
- Troubleshooting time: **70% faster** (centralized, structured logs)
- Storage costs: **40-50% reduction** (better retention policies)
- Compliance: **100% improvement** (sensitive data redaction)
- Searchability: **300% improvement** (JSON + Loki)

---

### 3.3 Common Issues with Celery + Redis + PostgreSQL

**Gordon AI Question:**
```
What are the most common issues when running Celery + Redis + PostgreSQL in Docker?
How should we configure:
- Celery worker concurrency
- Redis connection pooling
- PostgreSQL connection limits
- Task timeouts and retries
What monitoring should we implement?
```

**Expected Common Issues:**

1. **Connection Pool Exhaustion**
   - Symptom: "Too many connections" errors
   - Cause: Each Celery worker opens DB connections
   - Expected Impact: 100% service disruption

2. **Redis Memory Eviction**
   - Symptom: Tasks disappearing from queue
   - Cause: Redis hitting maxmemory with wrong eviction policy
   - Expected Impact: Lost background tasks

3. **Zombie Tasks**
   - Symptom: Tasks stuck in "started" state
   - Cause: Worker crash without cleanup
   - Expected Impact: 20-30% resource waste

4. **Slow Task Accumulation**
   - Symptom: Queue backlog growing over time
   - Cause: Task processing slower than task production
   - Expected Impact: Degraded user experience

**Specific Recommendations:**

```python
# RECOMMENDATION 1: Optimal Celery Configuration
# backend/app/core/celery_config.py

from celery import Celery
from kombu import Queue, Exchange

# Calculate optimal settings
# Formula: (workers * replicas * concurrency) * connections_per_worker <= postgres max_connections
# Example: (1 backend + 2 worker replicas) * 4 concurrency * 2 connections = 24 connections
# Reserve 20 for FastAPI, 30 for maintenance = 74 total (under 100 limit)

celery_app = Celery('residency_scheduler')

celery_app.conf.update(
    # Broker settings
    broker_url='redis://:password@redis:6379/0',
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    broker_pool_limit=10,  # Connection pool to Redis

    # Result backend settings
    result_backend='redis://:password@redis:6379/0',
    result_expires=3600,  # 1 hour (reduced from default 24h)
    result_backend_transport_options={
        'master_name': 'mymaster',  # For Redis Sentinel
        'retry_on_timeout': True,
        'socket_timeout': 5,
        'socket_connect_timeout': 5,
    },

    # Worker settings
    worker_prefetch_multiplier=2,  # Fetch 2 tasks per worker at a time
    worker_max_tasks_per_child=500,  # Restart after 500 tasks (prevent memory leaks)
    worker_max_memory_per_child=400_000,  # 400MB limit per child (KB)
    worker_disable_rate_limits=False,
    worker_send_task_events=True,  # Enable monitoring

    # Task settings
    task_acks_late=True,  # Acknowledge after task completion (safer)
    task_reject_on_worker_lost=True,  # Requeue if worker crashes
    task_track_started=True,  # Track task state
    task_time_limit=600,  # 10 minutes hard limit
    task_soft_time_limit=540,  # 9 minutes soft limit
    task_default_retry_delay=60,  # 1 minute between retries
    task_max_retries=3,

    # Queue configuration
    task_queues=(
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('resilience', Exchange('resilience'), routing_key='resilience', priority=5),
        Queue('notifications', Exchange('notifications'), routing_key='notifications', priority=3),
    ),
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',

    # Serialization
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='America/New_York',
    enable_utc=True,

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,

    # Beat scheduler settings
    beat_schedule={
        'resilience-health-check': {
            'task': 'app.resilience.tasks.check_resilience_health',
            'schedule': 900.0,  # Every 15 minutes
            'options': {'queue': 'resilience', 'priority': 5}
        },
        'n1-n2-analysis': {
            'task': 'app.resilience.tasks.run_n1_n2_contingency',
            'schedule': 86400.0,  # Every 24 hours
            'options': {'queue': 'resilience', 'priority': 5}
        },
    },
)

# RECOMMENDATION 2: Database Connection Pool for Celery
# backend/app/db/celery_session.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Celery-specific engine with smaller pool
# Formula: concurrency * 1.5 = 4 * 1.5 = 6 connections per worker
# 2 workers * 6 = 12 connections total for Celery

celery_engine = create_async_engine(
    DATABASE_URL,
    pool_size=6,  # Smaller than FastAPI pool
    max_overflow=4,  # Limited overflow
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
    connect_args={
        "server_settings": {
            "application_name": "residency_scheduler_celery",
            "jit": "off"
        },
        "command_timeout": 60,  # 60 second query timeout
    }
)

async_session = sessionmaker(
    celery_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

async def get_celery_db():
    """Get database session for Celery tasks"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# RECOMMENDATION 3: Task Implementation Best Practices
# backend/app/resilience/tasks.py

from celery import Task
from app.core.celery_app import celery_app
from app.db.celery_session import get_celery_db

class DatabaseTask(Task):
    """Base task class with database session management"""
    _db = None

    def after_return(self, *args, **kwargs):
        """Close DB connection after task completes"""
        if self._db is not None:
            self._db.close()

@celery_app.task(
    base=DatabaseTask,
    bind=True,
    name='app.resilience.tasks.check_resilience_health',
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    reject_on_worker_lost=True,
    time_limit=300,  # 5 minutes
    soft_time_limit=270,  # 4.5 minutes
)
async def check_resilience_health(self):
    """Check system resilience health"""
    from app.resilience.framework import ResilienceFramework

    try:
        async for db in get_celery_db():
            framework = ResilienceFramework(db)
            health_data = await framework.check_health()

            # Log results
            self.update_state(
                state='SUCCESS',
                meta={'health_level': health_data['level']}
            )

            return health_data

    except SoftTimeLimitExceeded:
        # Handle soft timeout gracefully
        logger.warning('Task approaching time limit, wrapping up')
        raise

    except Exception as exc:
        # Retry with exponential backoff
        logger.error(f'Resilience health check failed: {exc}')
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

# RECOMMENDATION 4: Connection Monitoring
# backend/app/api/routes/monitoring.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.celery_app import celery_app
from app.core.redis_client import celery_redis

router = APIRouter()

@router.get("/monitoring/connections")
async def check_connections(db: AsyncSession = Depends(get_db)):
    """Monitor database and Redis connections"""

    # PostgreSQL connections
    pg_result = await db.execute("""
        SELECT
            count(*) as total_connections,
            count(*) FILTER (WHERE state = 'active') as active_connections,
            count(*) FILTER (WHERE state = 'idle') as idle_connections,
            count(*) FILTER (WHERE application_name LIKE 'residency_scheduler%') as app_connections
        FROM pg_stat_activity
    """)
    pg_stats = pg_result.fetchone()

    # Redis connections
    redis_info = await celery_redis.info('clients')
    redis_connections = redis_info.get('connected_clients', 0)

    # Celery worker status
    celery_inspect = celery_app.control.inspect()
    active_workers = celery_inspect.active()

    # Celery queue lengths
    queue_lengths = {}
    for queue in ['default', 'resilience', 'notifications']:
        queue_length = await celery_redis.llen(f'celery:queue:{queue}')
        queue_lengths[queue] = queue_length

    return {
        'postgres': {
            'total': pg_stats[0],
            'active': pg_stats[1],
            'idle': pg_stats[2],
            'app': pg_stats[3],
            'max': 100,  # From postgresql.conf
            'utilization': f"{(pg_stats[0] / 100) * 100:.1f}%"
        },
        'redis': {
            'connections': redis_connections,
            'max': 1000,  # From redis.conf
            'utilization': f"{(redis_connections / 1000) * 100:.1f}%"
        },
        'celery': {
            'workers': len(active_workers) if active_workers else 0,
            'queues': queue_lengths,
            'total_queued': sum(queue_lengths.values())
        }
    }

@router.get("/monitoring/celery/tasks")
async def celery_task_status():
    """Get Celery task statistics"""
    inspect = celery_app.control.inspect()

    return {
        'active': inspect.active(),
        'scheduled': inspect.scheduled(),
        'reserved': inspect.reserved(),
        'stats': inspect.stats(),
    }

# RECOMMENDATION 5: Alerting Configuration
# prometheus/alert-rules.yml

groups:
  - name: celery_alerts
    interval: 30s
    rules:
      # Alert if queue is backing up
      - alert: CeleryQueueBacklog
        expr: celery_queue_length > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Celery queue {{ $labels.queue }} has {{ $value }} tasks"
          description: "Queue backlog may indicate slow task processing"

      # Alert if no workers are running
      - alert: CeleryNoWorkers
        expr: celery_workers_total == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "No Celery workers are running"
          description: "Background task processing is stopped"

      # Alert if many tasks are failing
      - alert: CeleryHighFailureRate
        expr: rate(celery_task_failed_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High Celery task failure rate"
          description: "{{ $value }} tasks failing per second"

  - name: database_alerts
    interval: 30s
    rules:
      # Alert if connection pool is exhausted
      - alert: PostgreSQLConnectionPoolExhaustion
        expr: pg_stat_activity_count > 90
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL connection pool near exhaustion"
          description: "{{ $value }} connections out of 100 max"

      # Alert if idle connections are high
      - alert: PostgreSQLHighIdleConnections
        expr: pg_stat_activity_idle_count > 30
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High number of idle PostgreSQL connections"
          description: "{{ $value }} idle connections may indicate connection leak"

  - name: redis_alerts
    interval: 30s
    rules:
      # Alert if Redis memory is high
      - alert: RedisMemoryHigh
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redis memory usage at {{ $value }}%"
          description: "May start evicting keys or refusing writes"

      # Alert if evictions are happening
      - alert: RedisEvictingKeys
        expr: rate(redis_evicted_keys_total[5m]) > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redis is evicting keys"
          description: "{{ $value }} keys evicted per second - may indicate undersized maxmemory"
```

**Common Issues Troubleshooting Guide:**

```bash
# ISSUE 1: "Too many connections" on PostgreSQL
# Diagnosis:
docker-compose exec db psql -U scheduler -d residency_scheduler -c \
  "SELECT count(*), application_name, state FROM pg_stat_activity GROUP BY application_name, state;"

# Solution: Reduce pool_size in backend/celery or increase max_connections
# In docker-compose.prod.yml:
postgres -c max_connections=150  # Increase from 100

# ISSUE 2: Tasks stuck in "started" state
# Diagnosis:
docker-compose exec redis redis-cli -a "$REDIS_PASSWORD" KEYS "celery-task-meta-*"

# Solution: Enable task_acks_late and task_reject_on_worker_lost
# Already in RECOMMENDATION 1 above

# ISSUE 3: Redis memory eviction
# Diagnosis:
docker-compose exec redis redis-cli -a "$REDIS_PASSWORD" INFO stats | grep evicted

# Solution: Use noeviction policy for Celery DB (database 0)
# Already in RECOMMENDATION 1 of Section 2.2

# ISSUE 4: Slow task processing
# Diagnosis:
docker-compose exec celery-worker celery -A app.core.celery_app inspect stats

# Solution: Increase worker concurrency or add more worker replicas
# In docker-compose.prod.yml:
deploy:
  replicas: 3  # Add one more worker

# ISSUE 5: Connection leaks
# Diagnosis:
docker-compose exec db psql -U scheduler -d residency_scheduler -c \
  "SELECT application_name, state, state_change FROM pg_stat_activity WHERE state = 'idle in transaction';"

# Solution: Enable pool_pre_ping and pool_recycle
# Already in RECOMMENDATION 2 above
```

**Estimated Impact:**
- Connection pool errors: **95% reduction** (proper sizing)
- Lost tasks: **99% reduction** (acks_late + reject_on_worker_lost)
- Memory issues: **80% reduction** (proper Redis configuration)
- Task backlog: **60% improvement** (better concurrency tuning)
- Monitoring visibility: **300% improvement** (comprehensive metrics)

---

## 4. Implementation Roadmap

### Phase 1: Quick Wins (Week 1)

**Priority: HIGH | Effort: LOW | Impact: MEDIUM**

- [ ] Add `.dockerignore` files (frontend & backend)
- [ ] Enable BuildKit cache mounts in Dockerfiles
- [ ] Optimize health check intervals (reduce DB/Redis frequency)
- [ ] Add structured logging configuration
- [ ] Implement sensitive data redaction in logs

**Expected Impact:**
- Build time: 30-40% faster
- Image size: 10-15% reduction
- Health check overhead: 70% reduction

---

### Phase 2: Image Optimization (Week 2)

**Priority: HIGH | Effort: MEDIUM | Impact: HIGH**

- [ ] Split requirements.txt by change frequency (backend)
- [ ] Optimize npm dependency installation (frontend)
- [ ] Implement multi-database Redis strategy
- [ ] Add connection pool monitoring endpoints
- [ ] Configure Celery with optimal settings

**Expected Impact:**
- Backend image: 20-30% smaller
- Frontend image: 25-35% smaller
- Build cache hit rate: 50% improvement
- Resource usage: 15-20% reduction

---

### Phase 3: Production Hardening (Week 3)

**Priority: MEDIUM | Effort: HIGH | Impact: HIGH**

- [ ] Implement Docker secrets management
- [ ] Add network segmentation (frontend/backend/data)
- [ ] Enable read-only filesystems where possible
- [ ] Configure capability dropping (security)
- [ ] Set up centralized logging (Loki)

**Expected Impact:**
- Security posture: 80% improvement
- Troubleshooting time: 70% faster
- Compliance: 100% improvement

---

### Phase 4: Observability (Week 4)

**Priority: MEDIUM | Effort: MEDIUM | Impact: MEDIUM**

- [ ] Deploy Prometheus for metrics
- [ ] Configure Grafana dashboards
- [ ] Set up alerting rules (Celery, DB, Redis)
- [ ] Implement connection monitoring
- [ ] Add backup and disaster recovery

**Expected Impact:**
- Incident detection: 90% faster
- Downtime prevention: 40% reduction
- Recovery time: 70% faster

---

## 5. Measurement & Validation

### Baseline Metrics (Measure Before Optimization)

```bash
# Image sizes
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep residency

# Build times
time docker-compose build backend
time docker-compose build frontend

# Resource usage (run for 5 minutes)
docker stats --no-stream > baseline_stats.txt

# Health check frequency
docker inspect residency-scheduler-db | jq '.[0].Config.Healthcheck'

# Connection counts
docker-compose exec db psql -U scheduler -d residency_scheduler -c \
  "SELECT count(*) FROM pg_stat_activity;"
```

**Expected Baseline:**
- Backend image: ~500MB
- Frontend image: ~400MB
- Backend build time: ~12-15 minutes (no cache)
- Frontend build time: ~8-10 minutes (no cache)
- Total memory usage: ~8-10GB
- Health checks: ~3600/hour (all services)
- Database connections: 30-50

---

### Post-Optimization Targets

| Metric | Baseline | Target | Stretch Goal |
|--------|----------|--------|--------------|
| Backend image size | 500MB | 350MB | 300MB |
| Frontend image size | 400MB | 280MB | 250MB |
| Backend build (no cache) | 12-15 min | 10-12 min | 8-10 min |
| Backend build (cache) | 8-10 min | 3-5 min | 2-3 min |
| Frontend build (no cache) | 8-10 min | 6-8 min | 5-6 min |
| Frontend build (cache) | 5-6 min | 2-3 min | 1-2 min |
| Total memory usage | 8-10GB | 6-7GB | 5-6GB |
| Health checks/hour | 3600 | 1000 | 800 |
| Log volume/day | 5GB | 2GB | 1.5GB |
| Connection pool usage | 70% | 50% | 40% |

---

### Validation Scripts

```bash
#!/bin/bash
# scripts/validate-optimization.sh

echo "=== Docker Image Size Comparison ==="
echo "Backend:"
docker history residency-scheduler-backend:latest --human | head -n 10
echo ""
echo "Frontend:"
docker history residency-scheduler-frontend:latest --human | head -n 10

echo ""
echo "=== Build Time Test (with cache) ==="
time docker-compose build backend
time docker-compose build frontend

echo ""
echo "=== Resource Usage Test ==="
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

echo ""
echo "=== Connection Pool Status ==="
docker-compose exec db psql -U scheduler -d residency_scheduler -c \
  "SELECT count(*) as total,
          count(*) FILTER (WHERE state = 'active') as active,
          count(*) FILTER (WHERE state = 'idle') as idle
   FROM pg_stat_activity;"

echo ""
echo "=== Health Check Configuration ==="
for service in db redis backend celery-worker frontend; do
  echo "Service: $service"
  docker inspect residency-scheduler-$service | jq '.[0].Config.Healthcheck.Interval'
done

echo ""
echo "=== Log Volume (last 24 hours) ==="
du -sh /var/lib/docker/containers/*/*-json.log | sort -h | tail -n 10
```

---

## Conclusion

This Gordon AI evaluation provides a comprehensive roadmap for optimizing the Residency Scheduler Docker deployment. The recommendations focus on:

1. **Performance**: 30-50% build time reduction, 20-35% image size reduction
2. **Resource Efficiency**: 15-25% memory reduction, 70% fewer health checks
3. **Production Readiness**: Enhanced security, observability, and reliability
4. **Best Practices**: Structured logging, connection pooling, monitoring

**Estimated Total Impact:**
- **Cost Savings**: $50-100/month on cloud infrastructure
- **Developer Productivity**: 2-3 hours/week saved on builds and debugging
- **Incident Response**: 70% faster troubleshooting
- **System Reliability**: 40% reduction in downtime

**Next Steps:**
1. Run baseline measurements
2. Implement Phase 1 (Quick Wins) first
3. Measure improvements after each phase
4. Adjust targets based on actual results
5. Document learnings for future optimization

---

**Document Version:** 1.1
**Last Updated:** 2025-12-25
**Maintained By:** Infrastructure Team
**Review Schedule:** Quarterly

---

## Addendum: Security Best Practices Review (2025-12-25)

### Review Summary

An external review of Docker security best practices was conducted on 2025-12-25. The initial analysis made several claims about missing best practices that were subsequently verified against the actual codebase.

### Claims Verified as INCORRECT

| Claim | Reality |
|-------|---------|
| "No vulnerability scanning" | `.github/workflows/security.yml` has Trivy scanning (filesystem + container images) |
| "No logging configuration" | `docker-compose.prod.yml` has comprehensive JSON logging with rotation |
| "Resource limits only in prod" | This is intentional - dev shouldn't have limits interfering with debugging |

### Claims Verified as VALID

| Issue | Resolution |
|-------|------------|
| Frontend missing non-root user | Fixed: Added `nextjs` user (UID 1001) |
| Backend uses `sh -c` entrypoint | Fixed: Added `docker-entrypoint.sh` with `exec` for proper signal handling |

### Implemented Improvements

**Commit:** `cd03310` on branch `claude/review-docker-setup-7HRSC`

1. **Frontend Dockerfile**: Added non-root user
   ```dockerfile
   RUN adduser --disabled-password --gecos '' --uid 1001 nextjs \
       && chown -R nextjs:nextjs /app
   USER nextjs
   ```

2. **Backend Dockerfile**: Added entrypoint script
   ```dockerfile
   COPY docker-entrypoint.sh /usr/local/bin/
   RUN chmod +x /usr/local/bin/docker-entrypoint.sh
   ENTRYPOINT ["docker-entrypoint.sh"]
   ```

3. **Backend docker-entrypoint.sh**: Proper signal handling
   ```bash
   #!/bin/sh
   set -e
   alembic upgrade head
   exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
   ```

### What Was Already Implemented

The following practices were already in place (contrary to initial claims):

- Multi-stage builds on all custom images
- Non-root users on backend, MCP server, and nginx
- Health checks on all services
- `no-new-privileges` security option on MCP server
- Resource limits and reservations in production
- Network isolation with dedicated `app-network`
- Automated vulnerability scanning (Trivy, Safety, npm audit, Bandit, CodeQL, Semgrep)
- Structured logging configuration in production compose
- Secret validation (app refuses to start with weak secrets)

### Recommendations Not Implemented (with Rationale)

| Practice | Status | Rationale |
|----------|--------|-----------|
| Image signing (Cosign) | Not implemented | Adds operational overhead; only critical for public registries |
| Multi-arch builds | Not implemented | No ARM64 deployment target currently |
| BuildKit cache mounts | Not implemented | Marginal benefit for this project size |
| tini init process | Not implemented | Entrypoint script with `exec` achieves same goal |

### Lessons Learned

1. **Verify claims against actual codebase** before accepting recommendations
2. **Check CI/CD workflows** - security scanning may already be in place
3. **Look for all compose file variants** - features may be in prod overlay
4. **Understand design decisions** - some "missing" practices are intentional

### Related Documentation

- [DOCKER_SECURITY_BEST_PRACTICES.md](../../architecture/DOCKER_SECURITY_BEST_PRACTICES.md) - Comprehensive security documentation
- [security.yml](../../../.github/workflows/security.yml) - CI/CD security scanning workflow
