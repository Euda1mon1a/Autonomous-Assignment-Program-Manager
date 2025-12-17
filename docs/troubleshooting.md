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
