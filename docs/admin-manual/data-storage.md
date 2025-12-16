# Data Storage and Persistence

## Overview

This guide explains where application data is physically stored in different deployment scenarios. Understanding data storage locations is critical for backup planning, disaster recovery, and infrastructure management.

## Table of Contents

1. [Storage Architecture](#storage-architecture)
2. [Local Development (macOS/Linux)](#local-development-macoslinux)
3. [Production Docker Deployment](#production-docker-deployment)
4. [Manual Installation](#manual-installation)
5. [Data Persistence Layers](#data-persistence-layers)
6. [Inspecting Data Locations](#inspecting-data-locations)
7. [Storage Best Practices](#storage-best-practices)

---

## Storage Architecture

The application uses multiple storage layers for different purposes:

| Layer | Technology | Persistence | Purpose |
|-------|------------|-------------|---------|
| **Primary Database** | PostgreSQL | Durable | All application data |
| **Task Queue** | Redis | Semi-durable | Background job queue |
| **Result Cache** | Redis | Temporary (1hr) | Task results |
| **In-Memory Cache** | Python `ScheduleCache` | Session only | Hot data caching |

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        APPLICATION                               │
├─────────────────────────────────────────────────────────────────┤
│  In-Memory Cache (ScheduleCache)                                │
│  └── 1000 entries, 1-hour TTL, lost on restart                  │
├─────────────────────────────────────────────────────────────────┤
│  Redis Cache                                                     │
│  └── Task results expire after 1 hour                           │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL Database                                             │
│  └── All persistent data (users, schedules, resilience state)   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Local Development (macOS/Linux)

When running with Docker Compose for development:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Where Data Is Stored

| Data | Storage Location | Description |
|------|------------------|-------------|
| **PostgreSQL** | Docker named volume `postgres_data` | Inside Docker's virtual machine |
| **Redis** | In-memory only | No persistence in dev mode |
| **Application Code** | `./backend`, `./frontend` | Mounted from your local filesystem |

### Docker Volume Location

**On macOS (Docker Desktop):**
```
~/Library/Containers/com.docker.docker/Data/vms/0/data/docker/volumes/
```

**On Linux:**
```
/var/lib/docker/volumes/
```

### Key Points

- **Data persists across container restarts** (as long as you don't delete the volume)
- **Data is lost if you run `docker volume rm postgres_data`**
- **Redis data is NOT persisted** in development mode
- **Code changes are live** due to volume mounts

### Inspecting Docker Volumes

```bash
# List all volumes
docker volume ls

# Inspect postgres volume
docker volume inspect postgres_data

# View volume size
docker system df -v | grep postgres_data
```

### Backing Up Local Development Data

```bash
# Backup PostgreSQL data
docker run --rm \
  -v postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar cvf /backup/db-backup.tar /data

# Restore PostgreSQL data
docker run --rm \
  -v postgres_data:/data \
  -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xvf /backup/db-backup.tar --strip 1"
```

---

## Production Docker Deployment

When running the production Docker configuration:

```bash
docker-compose -f .docker/docker-compose.prod.yml up -d
```

### Where Data Is Stored

| Data | Storage Location | Description |
|------|------------------|-------------|
| **PostgreSQL** | `${DATA_DIR}/postgres` | Host filesystem bind mount |
| **Redis** | `${DATA_DIR}/redis` | Host filesystem bind mount |

**Default DATA_DIR:** `/var/lib/residency-scheduler`

### Configuration (from `docker-compose.prod.yml`)

```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${DATA_DIR:-/var/lib/residency-scheduler}/postgres

  redis_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${DATA_DIR:-/var/lib/residency-scheduler}/redis
```

### Production Storage Locations

```
/var/lib/residency-scheduler/
├── postgres/           # PostgreSQL data files
│   ├── base/           # Database files
│   ├── global/         # Cluster-wide tables
│   ├── pg_wal/         # Write-ahead logs
│   └── ...
└── redis/              # Redis persistence
    └── appendonly.aof  # Append-only file
```

### Key Points

- **Data persists on the host filesystem** (survives container rebuilds)
- **Redis uses AOF persistence** for durability
- **Bind mounts allow direct filesystem access** for backups
- **Storage is decoupled from containers**

### Customizing Storage Location

Set the `DATA_DIR` environment variable:

```bash
# In .env or shell
export DATA_DIR=/mnt/data/residency-scheduler

# Create directories
sudo mkdir -p ${DATA_DIR}/postgres ${DATA_DIR}/redis
sudo chown -R 999:999 ${DATA_DIR}/postgres  # postgres user
sudo chown -R 999:999 ${DATA_DIR}/redis     # redis user
```

---

## Manual Installation

For non-Docker deployments:

### Where Data Is Stored

| Data | Storage Location |
|------|------------------|
| **PostgreSQL** | `/var/lib/postgresql/15/main` |
| **Redis** | `/var/lib/redis` |
| **Application** | `/opt/residency-scheduler` |
| **Logs** | `/var/log/residency-scheduler` |

### PostgreSQL Data Directory

```bash
# Check PostgreSQL data directory
sudo -u postgres psql -c "SHOW data_directory;"
# Output: /var/lib/postgresql/15/main
```

### Redis Data Directory

```bash
# Check Redis configuration
cat /etc/redis/redis.conf | grep "^dir"
# Output: dir /var/lib/redis
```

---

## Data Persistence Layers

### What Persists Between Sessions

The following data survives application restarts:

#### Tier 1 - Critical State (PostgreSQL)

| Table | Purpose |
|-------|---------|
| `resilience_health_checks` | System health snapshots |
| `resilience_events` | State change audit log |
| `sacrifice_decisions` | Load shedding decisions |
| `fallback_activations` | Fallback schedule activations |
| `vulnerability_records` | N-1/N-2 analysis results |

#### Tier 2 - Strategic State (PostgreSQL)

| Table | Purpose |
|-------|---------|
| `feedback_loop_states` | Homeostasis deviation tracking |
| `allostasis_records` | Cumulative stress tracking |
| `scheduling_zones` | Service zone definitions |
| `equilibrium_shifts` | System equilibrium transitions |

#### Tier 3 - Cognitive State (PostgreSQL)

| Table | Purpose |
|-------|---------|
| `cognitive_sessions` | User work session history |
| `preference_trails` | Faculty scheduling preferences |
| `faculty_centrality` | Hub/critical faculty scores |

### What Is Temporary

| Data | Location | Lifetime |
|------|----------|----------|
| In-memory cache | Python `ScheduleCache` | Until restart |
| LRU cached values | Python `@lru_cache` | Until restart |
| Redis task results | Redis | 1 hour TTL |

---

## Inspecting Data Locations

### Docker Environment

```bash
# Check where Docker stores volumes
docker info | grep "Docker Root Dir"

# List volumes with size
docker system df -v

# Inspect specific volume
docker volume inspect residency-scheduler_postgres_data

# Access PostgreSQL container
docker compose exec db psql -U scheduler -d residency_scheduler

# Check database size
docker compose exec db psql -U scheduler -d residency_scheduler \
  -c "SELECT pg_size_pretty(pg_database_size('residency_scheduler'));"
```

### Production Environment

```bash
# Check disk usage
du -sh /var/lib/residency-scheduler/*

# Check PostgreSQL data size
sudo du -sh /var/lib/postgresql/15/main

# List database tables and sizes
psql -U scheduler -d residency_scheduler -c "
  SELECT
    schemaname || '.' || tablename AS table,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) AS size
  FROM pg_tables
  WHERE schemaname = 'public'
  ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC
  LIMIT 20;
"
```

---

## Storage Best Practices

### Development

1. **Regularly backup your Docker volume** if you have important test data
2. **Use `docker-compose down` (not `docker-compose down -v`)** to preserve data
3. **Consider named volumes over bind mounts** for database storage

### Production

1. **Use dedicated storage** for database volumes (SSD recommended)
2. **Set up automated backups** to external storage (see [Backup & Restore](./backup-restore.md))
3. **Monitor disk usage** with alerts at 80% capacity
4. **Use RAID or replicated storage** for critical data
5. **Store secrets separately** from application data

### Storage Sizing Guidelines

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| PostgreSQL | 10 GB | 50 GB |
| Redis | 1 GB | 2 GB |
| Logs | 5 GB | 20 GB |
| Backups | 3x DB size | 5x DB size |

### Monitoring Commands

```bash
# Monitor disk usage
watch -n 60 'df -h /var/lib/residency-scheduler'

# Alert if over 80%
USAGE=$(df /var/lib/residency-scheduler | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$USAGE" -gt 80 ]; then
  echo "WARNING: Disk usage at ${USAGE}%"
fi
```

---

## Summary

| Deployment Mode | PostgreSQL Location | Survives Restart | Survives `docker-compose down -v` |
|-----------------|---------------------|------------------|-----------------------------------|
| **Local Dev (Docker)** | Docker volume | Yes | No |
| **Production (Docker)** | Host filesystem | Yes | Yes |
| **Manual Install** | `/var/lib/postgresql` | Yes | N/A |

**Key Takeaway:** In all deployment modes, PostgreSQL is the source of truth for persistent data. Ensure you have proper backup procedures in place regardless of deployment method.

---

*Last Updated: December 2024*
