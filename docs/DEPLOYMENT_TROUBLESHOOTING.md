# Deployment Troubleshooting Guide

> **Last Updated:** 2025-12-21 (Session 14)
> **Purpose:** Document recurring deployment issues and their solutions

---

## Table of Contents

1. [Docker Build Issues](#docker-build-issues)
2. [Redis Connection Issues](#redis-connection-issues)
3. [SQLAlchemy/ORM Issues](#sqlalchemyorm-issues)
4. [Authentication Issues](#authentication-issues)
5. [Rate Limiting Issues](#rate-limiting-issues)
6. [GraphQL Issues](#graphql-issues)
7. [Database Seeding](#database-seeding)
8. [Quick Recovery Steps](#quick-recovery-steps)

---

## Docker Build Issues

### Problem: Cached Layer Prevents Dependency Installation

**Symptom:**
```
ImportError: failed to find libmagic. Check your installation
```

**Cause:** Docker layer caching doesn't detect changes to `apt-get install` commands when the base image layer is cached.

**Solution:**
```bash
# Full clean rebuild
docker-compose -f docker-compose.local.yml down
docker rmi autonomous-assignment-program-manager-backend 2>/dev/null || true
docker builder prune -af
docker-compose -f docker-compose.local.yml up -d --build
```

**Files Involved:**
- `backend/Dockerfile.local` (development)
- `backend/Dockerfile` (production)

**Note:** `docker-compose.local.yml` uses `Dockerfile.local`, not `Dockerfile`. Ensure dependencies are added to the correct file.

---

## Redis Connection Issues

### Problem: Double Password in Redis URL

**Symptom:**
```
AuthenticationError: ...
# Or rate limiting middleware crashes
```

**Cause:** When both `REDIS_URL` and `REDIS_PASSWORD` are set in environment, and `REDIS_URL` already contains the password, the `redis_url_with_password` property doubles it:

```
Expected: redis://:password@redis:6379/0
Actual:   redis://:password@:password@redis:6379/0
```

**Solution:** Fixed in `backend/app/core/config.py`:

```python
@property
def redis_url_with_password(self) -> str:
    # Check if password is already in the URL
    if "@" in self.REDIS_URL and self.REDIS_URL.startswith("redis://:"):
        return self.REDIS_URL  # Already has password
    if self.REDIS_PASSWORD:
        return self.REDIS_URL.replace("redis://", f"redis://:{self.REDIS_PASSWORD}@")
    return self.REDIS_URL
```

**Files Involved:**
- `backend/app/core/config.py`
- `docker-compose.local.yml` (environment variables)

---

## SQLAlchemy/ORM Issues

### Problem: Ambiguous Foreign Keys Error

**Symptom:**
```
AmbiguousForeignKeysError: Could not determine join condition between parent/child
tables on relationship APIKey.owner - there are multiple foreign key paths linking
the tables. Specify the 'foreign_keys' argument.
```

**Cause:** Model has multiple `ForeignKey` columns pointing to the same table without explicit `foreign_keys` specification.

**Example in `APIKey` model:**
```python
owner_id = Column(GUID(), ForeignKey("users.id"))
revoked_by_id = Column(GUID(), ForeignKey("users.id"))  # Second FK to users
owner = relationship("User", backref="api_keys")  # Ambiguous!
```

**Solution:**
```python
owner = relationship("User", foreign_keys=[owner_id], backref="api_keys")
```

**Files Involved:**
- `backend/app/models/gateway_auth.py`

### Problem: Reserved Column Name "metadata"

**Symptom:**
```
InvalidRequestError: Attribute name 'metadata' is reserved
```

**Cause:** SQLAlchemy reserves `metadata` as a class attribute.

**Solution:** Rename columns to descriptive alternatives:
- `metadata` → `config_data`, `json_data`, `settings_json`, etc.

---

## Authentication Issues

### Problem: Admin User Not Created

**Symptom:**
```
Login failed: {"detail": "Invalid credentials"}
```

**Cause:** Database migrations create the schema but don't seed the admin user.

**Solution:**
1. Check if admin exists:
   ```bash
   docker exec scheduler-local-db psql -U scheduler -d residency_scheduler -c \
     "SELECT username FROM users WHERE username = 'admin';"
   ```

2. Admin should be created via migration or initial seed. If missing, check:
   - `backend/alembic/versions/` for user creation migration
   - Initial data seeders

**Default Admin Credentials (Development Only):**
- Username: `admin`
- Password: `AdminPassword123!`

### Problem: JWT Token Validation Fails

**Symptom:**
```
{"detail": "Could not validate credentials"}
```

**Causes:**
1. Token expired (15-minute default)
2. SECRET_KEY changed between token issuance and validation
3. Token blacklisted

**Solution:** Re-authenticate to get fresh tokens.

---

## Rate Limiting Issues

### Problem: Invalid Rate Limiting Strategy

**Symptom:**
```
ConfigurationError: Invalid rate limiting strategy fixed-window-elastic-expiry
```

**Cause:** SlowAPI only supports certain strategies.

**Valid Strategies:**
- `fixed-window`
- `moving-window`

**Solution:** In `backend/app/core/slowapi_limiter.py`:
```python
limiter = Limiter(
    ...
    strategy="fixed-window",  # Not "fixed-window-elastic-expiry"
)
```

---

## GraphQL Issues

### Problem: Enum Not Recognized

**Symptom:**
```
ObjectIsNotAnEnumError: AssignmentRole is not an enum
```

**Cause:** Strawberry GraphQL requires enums to inherit from both `str` and `Enum`.

**Wrong:**
```python
@strawberry.enum
class AssignmentRole(str):  # Missing Enum inheritance
    PRIMARY = "primary"
```

**Correct:**
```python
from enum import Enum

@strawberry.enum
class AssignmentRole(str, Enum):  # Must have both!
    PRIMARY = "primary"
```

**Files Affected:**
- `backend/app/graphql/types/assignment.py`
- `backend/app/graphql/types/person.py`
- `backend/app/graphql/types/schedule.py`

---

## Database Seeding

### Problem: Scripts Not Mounted in Container

**Symptom:**
```
python3: can't open file '/app/scripts/seed_people.py': [Errno 2] No such file or directory
```

**Cause:** The `scripts/` directory is not volume-mounted in `docker-compose.local.yml`.

**Solutions:**

1. **Run from host with requests:**
   ```bash
   python3 scripts/seed_people.py  # Requires requests module
   ```

2. **Pipe script to container:**
   ```bash
   cat scripts/seed_people.py | docker exec -i scheduler-local-backend python3
   ```

3. **Inline execution:**
   ```bash
   docker exec scheduler-local-backend python3 -c "
   import sys
   sys.path.insert(0, '/app')
   from app.db.session import SessionLocal
   # ... seeding code
   "
   ```

### Problem: Duplicate Key Constraint

**Symptom:**
```
IntegrityError: duplicate key value violates unique constraint "people_email_key"
```

**Cause:** Running seed script multiple times without cleanup.

**Solution:** Seeders should be idempotent - check for existing records before inserting.

---

## Quick Recovery Steps

### Full Stack Restart

```bash
# Stop everything
docker-compose -f docker-compose.local.yml down

# Clean slate (optional - removes volumes)
docker-compose -f docker-compose.local.yml down -v

# Fresh rebuild
docker builder prune -af
docker-compose -f docker-compose.local.yml up -d --build

# Wait for startup
sleep 15

# Verify
curl http://localhost:8000/health
```

### Database Reset

```bash
# Drop and recreate database
docker exec scheduler-local-db psql -U scheduler -c "DROP DATABASE residency_scheduler;"
docker exec scheduler-local-db psql -U scheduler -c "CREATE DATABASE residency_scheduler;"

# Run migrations
docker exec scheduler-local-backend alembic upgrade head
```

### Check Container Health

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
docker logs scheduler-local-backend --tail 50
docker logs scheduler-local-redis --tail 20
```

---

## Checklist for New Deployments

- [ ] Secret keys generated and set (not defaults)
- [ ] Redis password configured correctly
- [ ] Database migrations run (`alembic upgrade head`)
- [ ] Admin user exists
- [ ] Health endpoint responds: `curl http://localhost:8000/health`
- [ ] Can login: POST to `/api/v1/auth/login/json`
- [ ] People seeded (28 test records)
- [ ] Rotation templates seeded (8 templates)
- [ ] Blocks generated for target period

---

## Frontend Issues

### Problem: Login Flashes and Resets

**Symptom:** Login form submits, page briefly flashes, then resets to login form.

**Cause:** `NEXT_PUBLIC_API_URL` missing `/api` suffix. Frontend sends requests to wrong path.

**Wrong:**
```yaml
# docker-compose.local.yml
NEXT_PUBLIC_API_URL: http://localhost:8000  # Missing /api!
```

**Correct:**
```yaml
NEXT_PUBLIC_API_URL: http://localhost:8000/api  # Include /api
```

**How it breaks:**
1. Frontend api.ts builds URL: `NEXT_PUBLIC_API_URL + '/auth/login'`
2. Without `/api`: `http://localhost:8000/auth/login` (wrong path)
3. With `/api`: `http://localhost:8000/api/auth/login` (redirects to `/api/v1/auth/login`)

**Fix Applied:**
- `docker-compose.local.yml` line 219: Added `/api` suffix
- `frontend/src/components/LoginForm.tsx`: Added descriptive error messages

### Problem: Demo Credentials Wrong

**Symptom:** Login fails with credentials shown on login page.

**Cause:** Login page showed outdated demo credentials.

**Actual Credentials:**
- Username: `admin`
- Password: `AdminPassword123!`

---

## Related Documentation

- `docs/CLAUDE_DEPLOYMENT_HANDOFF.md` - Known deployment blockers
- `docs/security/DATA_SECURITY_POLICY.md` - PII handling
- `CLAUDE.md` - Project guidelines

---

*This document should be updated as new deployment issues are discovered.*
