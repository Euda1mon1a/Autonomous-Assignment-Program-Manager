# Troubleshooting

Solutions to common issues with Residency Scheduler.

---

## Installation Issues

### Database Connection Failed

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
    # Ensure database container is running
    docker-compose up -d db

    # Check logs
    docker-compose logs db
    ```

=== "Local"
    ```bash
    # Start PostgreSQL
    sudo systemctl start postgresql

    # Check status
    sudo systemctl status postgresql
    ```

---

### Redis Connection Failed

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
    # or
    sudo systemctl start redis
    ```

---

### Port Already in Use

```
Error: Address already in use: 8000
```

**Solution:**
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

---

### Migration Errors

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

## Runtime Issues

### Authentication Failures

**"Invalid credentials" error:**

1. Verify email and password are correct
2. Check if account is active
3. Try resetting password

**"Token expired" error:**

- Re-login to get new token
- Increase `ACCESS_TOKEN_EXPIRE_MINUTES` in config

---

### Schedule Generation Fails

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

### Slow Performance

**Backend slow:**

```bash
# Check database connections
docker-compose exec db psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL
```

**Frontend slow:**

- Check browser console for errors
- Clear browser cache
- Check network tab for slow requests

---

## Docker Issues

### Container Won't Start

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs <service_name>

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Out of Disk Space

```bash
# Clean unused Docker data
docker system prune -a

# Check disk usage
docker system df
```

---

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid/expired token | Re-login |
| `403 Forbidden` | Insufficient permissions | Check user role |
| `404 Not Found` | Resource doesn't exist | Verify ID/URL |
| `422 Validation Error` | Invalid request data | Check request format |
| `429 Too Many Requests` | Rate limited | Wait and retry |
| `500 Internal Server Error` | Server error | Check backend logs |

---

## Getting Help

If your issue isn't listed here:

1. **Search** [existing issues](https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager/issues)
2. **Check** application logs: `docker-compose logs -f`
3. **Open** a new issue with:
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages and logs
   - Environment details (OS, browser, versions)

---

## Health Checks

Verify system health:

```bash
# Backend health
curl http://localhost:8000/health

# All services status
docker-compose ps

# Database connectivity
docker-compose exec backend python -c "
from app.db.session import engine
with engine.connect() as conn:
    print('Database connected!')
"
```
