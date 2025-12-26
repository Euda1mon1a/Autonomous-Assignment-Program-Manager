***REMOVED*** Troubleshooting

Solutions to common issues with Residency Scheduler.

---

***REMOVED******REMOVED*** Installation Issues

***REMOVED******REMOVED******REMOVED*** Database Connection Failed

```
Error: Connection refused to localhost:5432
```

**Causes:**
- PostgreSQL not running
- Wrong connection string
- Firewall blocking port

**Solutions:**

=== "Docker"
    ```bash
    ***REMOVED*** Ensure database container is running
    docker-compose up -d db

    ***REMOVED*** Check logs
    docker-compose logs db
    ```

=== "Local"
    ```bash
    ***REMOVED*** Start PostgreSQL
    sudo systemctl start postgresql

    ***REMOVED*** Check status
    sudo systemctl status postgresql
    ```

---

***REMOVED******REMOVED******REMOVED*** Redis Connection Failed

```
Error: Connection refused to localhost:6379
```

**Solutions:**

=== "Docker"
    ```bash
    docker-compose up -d redis
    ```

=== "Local"
    ```bash
    redis-server
    ***REMOVED*** or
    sudo systemctl start redis
    ```

---

***REMOVED******REMOVED******REMOVED*** Port Already in Use

```
Error: Address already in use: 8000
```

**Solution:**
```bash
***REMOVED*** Find process using port
lsof -i :8000

***REMOVED*** Kill process
kill -9 <PID>
```

---

***REMOVED******REMOVED******REMOVED*** Migration Errors

```
Error: Can't locate revision
```

**Solution:**
```bash
cd backend
alembic downgrade base
alembic upgrade head
```

---

***REMOVED******REMOVED*** Runtime Issues

***REMOVED******REMOVED******REMOVED*** Authentication Failures

**"Invalid credentials" error:**

1. Verify email and password are correct
2. Check if account is active
3. Try resetting password

**"Token expired" error:**

- Re-login to get new token
- Increase `ACCESS_TOKEN_EXPIRE_MINUTES` in config

---

***REMOVED******REMOVED******REMOVED*** Schedule Generation Fails

**"No valid schedule found" error:**

Possible causes:

1. **Insufficient staff**: Not enough people to cover requirements
2. **Constraint conflicts**: Impossible requirements (e.g., everyone on vacation)
3. **Algorithm timeout**: Complex schedule needs more time

**Solutions:**

- Review absence calendar for coverage gaps
- Relax constraint priorities
- Try different algorithm (Greedy vs CP-SAT)
- Increase generation timeout

---

***REMOVED******REMOVED******REMOVED*** Slow Performance

**Backend slow:**

```bash
***REMOVED*** Check database connections
docker-compose exec db psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

***REMOVED*** Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL
```

**Frontend slow:**

- Check browser console for errors
- Clear browser cache
- Check network tab for slow requests

---

***REMOVED******REMOVED*** Docker Issues

***REMOVED******REMOVED******REMOVED*** Container Won't Start

```bash
***REMOVED*** Check container status
docker-compose ps

***REMOVED*** View logs
docker-compose logs <service_name>

***REMOVED*** Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

***REMOVED******REMOVED******REMOVED*** Containers Unhealthy After Database Rebuild

**Symptoms:**
- `celery-beat` shows "unhealthy"
- `mcp-server` is in a restart loop
- Database was rebuilt but containers still fail

**Root Cause:** Containers were built with old environment values baked into image layers. Rebuilding the database doesn't update container images.

***REMOVED******REMOVED******REMOVED******REMOVED*** Diagnosing the Issue

```bash
***REMOVED*** Check container health status
docker compose ps --format "table {{.Name}}\t{{.Status}}"

***REMOVED*** Expected healthy output:
***REMOVED*** NAME                              STATUS
***REMOVED*** residency-scheduler-backend       Up 2 hours (healthy)
***REMOVED*** residency-scheduler-db            Up 2 hours (healthy)
***REMOVED*** residency-scheduler-redis         Up 2 hours (healthy)
***REMOVED*** residency-scheduler-celery-worker Up 2 hours (healthy)
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Issue 1: celery-beat Unhealthy

**Common Causes:**

| Cause | Symptom | Fix |
|-------|---------|-----|
| Stale scheduler file | Beat refuses to start | Delete `celerybeat-schedule` |
| Redis password mismatch | Connection refused | Rebuild with correct `.env` |
| Database schema mismatch | Migration errors in logs | Run migrations |

**Fix:**

```bash
***REMOVED*** Clear stale scheduler file
docker compose exec celery-beat rm -f /app/celerybeat-schedule

***REMOVED*** Restart
docker compose restart celery-beat

***REMOVED*** Check logs
docker compose logs --tail=20 celery-beat
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Issue 2: mcp-server Restart Loop

**Root Cause:** The MCP server is configured to run in **stdio mode** by default, but inside a Docker container with no interactive input, it exits immediately.

**Fix Options:**

```bash
***REMOVED*** Option A: Run in HTTP mode (add to docker-compose.yml under mcp-server)
command: ["--host", "0.0.0.0", "--port", "8080"]

***REMOVED*** Option B: Just stop it if not needed for schedule generation
docker compose stop mcp-server
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Issue 3: Environment Variable Mismatch

**Symptoms:**
- Containers start but can't connect to Redis/DB
- "Authentication failed" in logs
- Worked before database rebuild

**Diagnosis:**

```bash
***REMOVED*** Check what env vars Docker Compose sees
docker compose config | grep -A5 "environment:"

***REMOVED*** Verify .env file exists and has required vars
cat .env | grep -E '^(DB_PASSWORD|REDIS_PASSWORD|SECRET_KEY)=' | wc -l
***REMOVED*** Should output: 3
```

**Fix - Full Rebuild with Fresh Environment:**

```bash
***REMOVED*** 1. Stop everything and remove volumes
docker compose down -v

***REMOVED*** 2. Verify .env has correct values
cat .env | head -20

***REMOVED*** 3. Rebuild ALL containers (clears cached layers)
docker compose build --no-cache

***REMOVED*** 4. Start fresh
docker compose up -d

***REMOVED*** 5. Verify health
docker compose ps
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Required Environment Variables

| Variable | Purpose | Validation |
|----------|---------|------------|
| `DB_PASSWORD` | PostgreSQL password | Must match in all containers |
| `REDIS_PASSWORD` | Redis authentication | Must match in all containers |
| `SECRET_KEY` | JWT signing | Min 32 characters |

**Generate new secrets if needed:**

```bash
***REMOVED*** Generate secure values
python -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(64)}')"
python -c "import secrets; print(f'REDIS_PASSWORD={secrets.token_urlsafe(32)}')"
python -c "import secrets; print(f'DB_PASSWORD={secrets.token_urlsafe(32)}')"
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Complete Recovery Procedure

When containers are persistently unhealthy after DB changes:

```bash
***REMOVED*** 1. Full teardown (preserves .env)
docker compose down -v
docker system prune -f

***REMOVED*** 2. Verify .env is correct
cat .env

***REMOVED*** 3. Rebuild from scratch
docker compose build --no-cache

***REMOVED*** 4. Start services
docker compose up -d

***REMOVED*** 5. Wait for health checks (30-60 seconds)
sleep 60

***REMOVED*** 6. Verify all healthy
docker compose ps

***REMOVED*** 7. Run database migrations
docker compose exec backend alembic upgrade head

***REMOVED*** 8. Final health check
curl -s http://localhost:8000/api/v1/health/ready | python -m json.tool
```

---

***REMOVED******REMOVED******REMOVED*** Out of Disk Space

```bash
***REMOVED*** Clean unused Docker data
docker system prune -a

***REMOVED*** Check disk usage
docker system df
```

---

***REMOVED******REMOVED*** Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid/expired token | Re-login |
| `403 Forbidden` | Insufficient permissions | Check user role |
| `404 Not Found` | Resource doesn't exist | Verify ID/URL |
| `422 Validation Error` | Invalid request data | Check request format |
| `429 Too Many Requests` | Rate limited | Wait and retry |
| `500 Internal Server Error` | Server error | Check backend logs |

---

***REMOVED******REMOVED*** Getting Help

If your issue isn't listed here:

1. **Search** [existing issues](https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager/issues)
2. **Check** application logs: `docker-compose logs -f`
3. **Open** a new issue with:
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages and logs
   - Environment details (OS, browser, versions)

---

***REMOVED******REMOVED*** Health Checks

Verify system health:

```bash
***REMOVED*** Backend health
curl http://localhost:8000/health

***REMOVED*** All services status
docker-compose ps

***REMOVED*** Database connectivity
docker-compose exec backend python -c "
from app.db.session import engine
with engine.connect() as conn:
    print('Database connected!')
"
```
