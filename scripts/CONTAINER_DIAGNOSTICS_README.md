# Container Staleness Diagnostic Tools

## Overview

Container staleness occurs when Docker containers are running an older version of your application code while the local source files have been updated. This creates a scenario where code changes are visible in the IDE but not reflected in the running container.

**Symptoms:**
- Code changes don't appear in running container
- Tests pass locally but fail in container
- Rebuild reveals code that should already be deployed
- "Works on my machine" scenarios

## Solution: Two Diagnostic Scripts

### 1. diagnose-container-staleness.sh

Detects if a container's code matches your local code by comparing file checksums.

#### Usage

```bash
# Default: checks residency-scheduler-backend container, app/db/session.py file
./scripts/diagnose-container-staleness.sh

# Specify container and file
./scripts/diagnose-container-staleness.sh residency-scheduler-backend app/api/routes/__init__.py

# Check different container
./scripts/diagnose-container-staleness.sh residency-scheduler-backend app/models/block.py
```

#### What It Does

1. **Container Check** - Verifies the container is running
2. **File Existence** - Confirms the file exists in the container
3. **Checksum Comparison** - Compares MD5 hashes of local vs. container files
4. **Status Report** - Clear success/failure output with recommendations

#### Example Output - Success

```
=== Container Staleness Diagnostic ===
Container: residency-scheduler-backend
File: app/db/session.py

--- Container file check ---
-rw-r--r-- 1 appuser appuser 4830 Jan  5 06:36 /app/app/db/session.py
✅ File exists in container

--- Checksum comparison ---
Local:     bb5ed0e762759d93d50e53f088391f50
Container: bb5ed0e762759d93d50e53f088391f50

✅ FILES MATCH - Container is current
```

#### Example Output - Stale

```
=== Container Staleness Diagnostic ===
Container: residency-scheduler-backend
File: app/api/routes/__init__.py

--- Checksum comparison ---
Local:     a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
Container: x9y8z7w6v5u4t3s2r1q0p9o8n7m6l5k4

❌ FILES DIFFER - Container is STALE

Recommended fix:
  docker-compose build --no-cache residency-scheduler-backend && docker-compose up -d residency-scheduler-backend

Or use rebuild script:
  ./scripts/rebuild-containers.sh residency-scheduler-backend
```

---

### 2. rebuild-containers.sh

Completely rebuilds Docker containers from scratch, bypassing all cached layers.

#### Usage

```bash
# Rebuild all containers
./scripts/rebuild-containers.sh

# Rebuild specific service
./scripts/rebuild-containers.sh residency-scheduler-backend

# Rebuild frontend
./scripts/rebuild-containers.sh residency-scheduler-frontend
```

#### What It Does

1. **Stops Services** - Gracefully stops the specified service(s)
2. **Rebuilds Image** - Builds from scratch (--no-cache)
3. **Restarts Services** - Brings services back online
4. **Health Check** - Waits for services to stabilize
5. **Status Report** - Shows final service status

#### Example Output

```
=== Docker Container Rebuild ===

Action: Rebuilding residency-scheduler-backend...

Stopping residency-scheduler-backend...
[+] Running 1/1
 ✔ Container residency-scheduler-backend  Removed

Building residency-scheduler-backend (no cache)...
[+] Building 45.2s
...

Starting residency-scheduler-backend...
[+] Running 2/2
 ✔ Container residency-scheduler-redis    Running
 ✔ Container residency-scheduler-backend   Started

Waiting for health checks to complete...

=== Service Status ===
NAME                                COMMAND             SERVICE   STATUS      PORTS
residency-scheduler-backend         uvicorn app.main:app --reload   backend    Up 5s (healthy)

✅ Rebuild complete

Next steps:
  - Run health checks: docker-compose ps
  - Verify logs: docker-compose logs -f [service_name]
  - Test container code: ./scripts/diagnose-container-staleness.sh
```

---

## Typical Workflow

### Scenario: You make code changes and need to verify they're in the container

```bash
# 1. Make your code changes
# 2. Check if container is stale
./scripts/diagnose-container-staleness.sh residency-scheduler-backend app/api/routes/__init__.py

# 3a. If files match, no action needed
# 3b. If files differ, rebuild
./scripts/rebuild-containers.sh residency-scheduler-backend

# 4. Verify rebuild worked
./scripts/diagnose-container-staleness.sh residency-scheduler-backend app/api/routes/__init__.py
```

### Scenario: Quick full stack rebuild (nuclear option)

```bash
# Rebuild EVERYTHING from scratch
./scripts/rebuild-containers.sh

# Wait for all services to stabilize
sleep 15

# Verify critical components
./scripts/diagnose-container-staleness.sh residency-scheduler-backend app/db/session.py
./scripts/diagnose-container-staleness.sh residency-scheduler-backend app/main.py
```

---

## Key Files to Monitor

These are commonly-changed files that frequently cause staleness issues:

### Backend Core
- `app/db/session.py` - Database session management
- `app/main.py` - Application entry point
- `app/api/routes/__init__.py` - API route initialization
- `app/core/config.py` - Configuration

### API Routes
- `app/api/routes/auth.py` - Authentication endpoints
- `app/api/routes/schedules.py` - Schedule endpoints
- `app/api/routes/swaps.py` - Swap endpoints

### Scheduling Engine
- `app/scheduling/engine.py` - Core scheduler
- `app/scheduling/acgme_validator.py` - Compliance validator
- `app/models/*.py` - Database models (after migrations)

### Pro Tips

1. **Quick Check After PR Merge**
   ```bash
   ./scripts/diagnose-container-staleness.sh residency-scheduler-backend app/api/routes/__init__.py
   ```

2. **Before Running Tests**
   ```bash
   ./scripts/diagnose-container-staleness.sh && echo "Safe to test" || ./scripts/rebuild-containers.sh
   ```

3. **Regular CI/CD Integration**
   ```bash
   # In your CI pipeline before running tests
   ./scripts/rebuild-containers.sh residency-scheduler-backend
   ./scripts/diagnose-container-staleness.sh residency-scheduler-backend app/db/session.py
   ```

4. **Monitor Multiple Files**
   ```bash
   # Create a check script
   for file in app/db/session.py app/main.py app/api/routes/__init__.py; do
       ./scripts/diagnose-container-staleness.sh residency-scheduler-backend "$file" || exit 1
   done
   ```

---

## Troubleshooting

### "Container is not running"

```bash
# Start the container
docker-compose up -d residency-scheduler-backend

# Try diagnostic again
./scripts/diagnose-container-staleness.sh
```

### "FILE NOT FOUND IN CONTAINER"

The file doesn't exist in the container image. Possible causes:
- File was added after container was built
- Wrong file path specified
- Container image is very stale

**Fix:**
```bash
./scripts/rebuild-containers.sh residency-scheduler-backend
./scripts/diagnose-container-staleness.sh residency-scheduler-backend app/path/to/file.py
```

### "Could not read container file hash"

Docker exec failed. The container might be hung or unhealthy.

**Fix:**
```bash
# Check container status
docker-compose ps residency-scheduler-backend

# Restart if unhealthy
docker-compose restart residency-scheduler-backend

# Try again
./scripts/diagnose-container-staleness.sh
```

---

## Prevention Strategies

### 1. Always Rebuild After Git Merge

```bash
# After pulling from main
git pull origin main
./scripts/rebuild-containers.sh residency-scheduler-backend
```

### 2. Pre-Test Health Check

```bash
# Before running tests
./scripts/diagnose-container-staleness.sh residency-scheduler-backend app/db/session.py || {
    echo "Container is stale, rebuilding..."
    ./scripts/rebuild-containers.sh residency-scheduler-backend
}
pytest backend/tests
```

### 3. Regular Full Stack Validation

```bash
# Weekly validation
./scripts/rebuild-containers.sh
docker-compose ps
./scripts/diagnose-container-staleness.sh residency-scheduler-backend app/main.py
```

---

## Technical Details

### How the Diagnostic Works

The script uses MD5 checksums to compare files:

1. **Local checksum** - `md5sum backend/$FILE_PATH`
2. **Container checksum** - `docker exec $CONTAINER md5sum /app/$FILE_PATH`
3. **Comparison** - If hashes match, files are identical

This is fast, reliable, and doesn't require filesystem mounts or special Docker configurations.

### Why Full Rebuild with --no-cache?

Docker's layer caching can cause stale code to persist:

- **With cache** - Old layers might be reused even if source changed
- **With --no-cache** - All layers are rebuilt from source files

For development:
```bash
docker-compose build --no-cache SERVICE_NAME
```

For production CI/CD:
```bash
# Standard build (uses cache for speed)
docker-compose build SERVICE_NAME
```

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Rebuild containers
  run: ./scripts/rebuild-containers.sh

- name: Verify code freshness
  run: |
    ./scripts/diagnose-container-staleness.sh residency-scheduler-backend app/db/session.py
    ./scripts/diagnose-container-staleness.sh residency-scheduler-backend app/main.py

- name: Run tests
  run: docker-compose exec -T residency-scheduler-backend pytest
```

---

## Questions?

- Check container logs: `docker-compose logs -f residency-scheduler-backend`
- Verify Docker running: `docker ps`
- Check docker-compose: `docker-compose config`
