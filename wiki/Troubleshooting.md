# Troubleshooting

This guide covers common issues and their solutions when using Residency Scheduler.

---

## Quick Diagnostics

### Health Check Commands

```bash
# Check all service status (Docker)
docker-compose ps

# Check backend health
curl http://localhost:8000/health

# Check detailed health
curl http://localhost:8000/health/ready

# View backend logs
docker-compose logs -f backend

# View all logs
docker-compose logs -f
```

### Common Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | None needed |
| 400 | Bad request | Check request data |
| 401 | Unauthorized | Login or refresh token |
| 403 | Forbidden | Check permissions |
| 404 | Not found | Verify resource exists |
| 422 | Validation error | Check field formats |
| 500 | Server error | Check backend logs |

---

## Installation Issues

### Docker Won't Start

**Symptom:**
```
ERROR: Couldn't connect to Docker daemon
```

**Solutions:**
1. Ensure Docker is running:
   ```bash
   # macOS/Windows: Start Docker Desktop
   # Linux:
   sudo systemctl start docker
   ```

2. Check Docker permissions:
   ```bash
   sudo usermod -aG docker $USER
   # Log out and back in
   ```

3. Verify Docker version:
   ```bash
   docker --version  # Should be 20.10+
   docker-compose --version  # Should be 2.0+
   ```

---

### Database Connection Failed

**Symptom:**
```
Error: Connection refused to localhost:5432
```

**Solutions:**

1. **Check if PostgreSQL is running:**
   ```bash
   # Docker
   docker-compose ps db

   # Local
   pg_isready -h localhost -p 5432
   ```

2. **Check DATABASE_URL format:**
   ```env
   # Correct format
   DATABASE_URL=postgresql://postgres:password@localhost:5432/residency_scheduler

   # Common mistakes
   DATABASE_URL=postgres://...  # Wrong - use postgresql://
   DATABASE_URL=postgresql://postgres@localhost:5432/db  # Missing password
   ```

3. **Verify database exists:**
   ```bash
   psql -U postgres -c "\l" | grep residency

   # Create if missing
   createdb residency_scheduler
   ```

4. **Check firewall/network:**
   ```bash
   # Test connection
   nc -zv localhost 5432
   ```

---

### Redis Connection Failed

**Symptom:**
```
Error: Connection refused to localhost:6379
```

**Solutions:**

1. **Start Redis:**
   ```bash
   # Docker
   docker-compose up -d redis

   # Local
   redis-server
   ```

2. **Test connection:**
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

3. **Check REDIS_URL:**
   ```env
   REDIS_URL=redis://localhost:6379/0
   ```

---

### Migration Errors

**Symptom:**
```
alembic.util.exc.CommandError: Can't locate revision
```

**Solutions:**

1. **Reset migrations:**
   ```bash
   cd backend
   alembic downgrade base
   alembic upgrade head
   ```

2. **Verify alembic.ini:**
   ```ini
   [alembic]
   script_location = alembic
   sqlalchemy.url = postgresql://...
   ```

3. **Check for conflicts:**
   ```bash
   alembic heads
   # Should show single head
   ```

4. **Force current version:**
   ```bash
   alembic stamp head
   ```

---

### Port Already in Use

**Symptom:**
```
Error: Bind for 0.0.0.0:8000 failed: port is already allocated
```

**Solutions:**

1. **Find process using port:**
   ```bash
   # Linux/macOS
   lsof -i :8000

   # Windows
   netstat -ano | findstr :8000
   ```

2. **Kill the process:**
   ```bash
   kill -9 <PID>
   ```

3. **Or use different port:**
   ```bash
   uvicorn app.main:app --port 8001
   ```

---

## Authentication Issues

### Login Failed

**Symptom:**
```
401 Unauthorized - Invalid credentials
```

**Solutions:**

1. **Verify credentials:**
   - Check email/password spelling
   - Ensure account exists
   - Check account is active

2. **Reset password (if needed):**
   ```bash
   # Via CLI
   cd backend
   python -m app.cli.reset_password user@example.com
   ```

3. **Check user in database:**
   ```sql
   SELECT email, is_active FROM users WHERE email = 'user@example.com';
   ```

---

### Token Expired

**Symptom:**
```
401 Unauthorized - Token has expired
```

**Solutions:**

1. **Login again** to get new token

2. **Increase token lifetime (if appropriate):**
   ```env
   ACCESS_TOKEN_EXPIRE_MINUTES=2880  # 48 hours
   ```

3. **Check server time sync:**
   ```bash
   date
   # Ensure correct timezone
   ```

---

### CORS Errors

**Symptom:**
```
Access to fetch at 'http://localhost:8000/api/...' from origin
'http://localhost:3000' has been blocked by CORS policy
```

**Solutions:**

1. **Add origin to CORS_ORIGINS:**
   ```env
   CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
   ```

2. **Restart backend after change:**
   ```bash
   docker-compose restart backend
   ```

3. **Check for typos in origin URL**

---

## Schedule Generation Issues

### Generation Takes Too Long

**Symptom:**
Schedule generation hangs or times out.

**Solutions:**

1. **Reduce date range:**
   - Generate month-by-month instead of full year

2. **Use faster algorithm:**
   ```json
   {
     "algorithm": "greedy"  // Instead of "hybrid" or "cp-sat"
   }
   ```

3. **Increase timeout:**
   ```env
   SCHEDULE_GENERATION_TIMEOUT=600  # 10 minutes
   ```

4. **Check Celery workers:**
   ```bash
   docker-compose logs celery-worker
   # Ensure workers are running and processing
   ```

---

### Compliance Violations After Generation

**Symptom:**
Generated schedule has ACGME violations.

**Solutions:**

1. **Review constraint configuration:**
   - Check supervision ratios
   - Verify absence entries
   - Review template capacity limits

2. **Ensure adequate staffing:**
   - More violations often = understaffing
   - Add residents or faculty if needed

3. **Adjust priority weights:**
   - Increase compliance weight
   - Decrease preference weight

4. **Manual adjustments:**
   - Edit specific assignments
   - Use swap system for fine-tuning

---

### "No Valid Schedule Found"

**Symptom:**
```
Error: Could not generate valid schedule - constraints unsatisfiable
```

**Solutions:**

1. **Check for impossible constraints:**
   - Too many absences in same period
   - Required coverage exceeds available staff
   - Conflicting requirements

2. **Review absence calendar:**
   - Check for overlapping absences
   - Verify absence dates are correct

3. **Increase flexibility:**
   - Allow overtime
   - Reduce minimum requirements temporarily

4. **Try different algorithm:**
   ```json
   {
     "algorithm": "greedy",
     "allow_violations": true
   }
   ```

---

## Celery/Background Task Issues

### Tasks Not Running

**Symptom:**
Scheduled tasks don't execute.

**Solutions:**

1. **Check Celery worker:**
   ```bash
   docker-compose logs celery-worker

   # Verify worker is running
   celery -A app.core.celery_app inspect active
   ```

2. **Check Celery beat:**
   ```bash
   docker-compose logs celery-beat

   # Verify beat is scheduling
   ```

3. **Verify Redis connection:**
   ```bash
   redis-cli ping
   ```

4. **Restart Celery services:**
   ```bash
   docker-compose restart celery-worker celery-beat
   ```

---

### Tasks Stuck in Queue

**Symptom:**
Tasks show as pending but never complete.

**Solutions:**

1. **Check worker capacity:**
   ```bash
   celery -A app.core.celery_app inspect stats
   ```

2. **Clear stuck tasks:**
   ```bash
   celery -A app.core.celery_app purge
   ```

3. **Increase worker concurrency:**
   ```yaml
   celery-worker:
     command: celery -A app.core.celery_app worker --concurrency=4
   ```

4. **Check for errors in task:**
   ```bash
   celery -A app.core.celery_app inspect reserved
   ```

---

## Frontend Issues

### Page Won't Load

**Symptom:**
Blank page or loading spinner indefinitely.

**Solutions:**

1. **Check browser console:**
   - Press F12 → Console tab
   - Look for JavaScript errors

2. **Verify API URL:**
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Clear browser cache:**
   - Hard refresh: Ctrl+Shift+R (Cmd+Shift+R on Mac)
   - Clear cookies and cache

4. **Check backend is running:**
   ```bash
   curl http://localhost:8000/health
   ```

---

### Data Not Updating

**Symptom:**
Changes don't appear until page refresh.

**Solutions:**

1. **Check React Query cache:**
   - Data is cached for performance
   - Wait for stale time to expire
   - Or force refresh in component

2. **Invalidate cache manually:**
   - Use browser DevTools → Application → Clear site data

3. **Check for mutation errors:**
   - Look in Network tab for failed requests

---

### Calendar Not Showing Events

**Symptom:**
Calendar view is empty despite having assignments.

**Solutions:**

1. **Check date range:**
   - Ensure viewing correct month/year
   - Check if assignments exist in that range

2. **Verify API response:**
   - Check Network tab for `/api/assignments` call
   - Ensure data is returned

3. **Check user permissions:**
   - Some views filter by user role
   - Admin sees all, faculty sees own

---

## Performance Issues

### Slow API Responses

**Symptom:**
API requests take several seconds.

**Solutions:**

1. **Check database performance:**
   ```sql
   -- Find slow queries
   SELECT query, mean_exec_time
   FROM pg_stat_statements
   ORDER BY mean_exec_time DESC
   LIMIT 10;
   ```

2. **Add indexes:**
   ```sql
   CREATE INDEX idx_assignments_person ON assignments(person_id);
   CREATE INDEX idx_assignments_date ON assignments(date);
   ```

3. **Increase connection pool:**
   ```env
   DB_POOL_SIZE=20
   DB_POOL_MAX_OVERFLOW=40
   ```

4. **Enable caching:**
   - Ensure Redis is configured
   - Check cache headers in responses

---

### High Memory Usage

**Symptom:**
Backend using excessive memory.

**Solutions:**

1. **Check for memory leaks:**
   ```bash
   docker stats
   ```

2. **Reduce worker processes:**
   ```yaml
   backend:
     deploy:
       resources:
         limits:
           memory: 2G
   ```

3. **Optimize queries:**
   - Use pagination
   - Avoid loading all records

4. **Restart services periodically:**
   ```bash
   docker-compose restart backend
   ```

---

## Data Issues

### Missing Data After Migration

**Symptom:**
Data disappeared after database migration.

**Solutions:**

1. **Check migration logs:**
   ```bash
   alembic history
   alembic current
   ```

2. **Restore from backup:**
   ```bash
   # If using Docker
   docker-compose exec db pg_restore -U postgres -d residency_scheduler backup.dump
   ```

3. **Check if data exists:**
   ```sql
   SELECT COUNT(*) FROM people;
   SELECT COUNT(*) FROM assignments;
   ```

---

### Import Failed

**Symptom:**
Excel import shows errors.

**Solutions:**

1. **Verify file format:**
   - Must be .xlsx (not .xls)
   - Download and use provided template

2. **Check required columns:**
   - All required fields must have values
   - Column headers must match exactly

3. **Validate data types:**
   - Dates in correct format (YYYY-MM-DD)
   - Numbers without formatting
   - No special characters

4. **Check file size:**
   - Maximum typically 10MB
   - Split large imports

---

### Export Not Working

**Symptom:**
Excel/ICS export fails or produces empty file.

**Solutions:**

1. **Check data exists:**
   - Verify date range has assignments
   - Check filter settings

2. **Check browser downloads:**
   - Pop-up blocker may prevent download
   - Check Downloads folder

3. **Try different browser:**
   - Some browsers handle downloads differently

4. **Check backend logs:**
   ```bash
   docker-compose logs backend | grep export
   ```

---

## Getting More Help

### Collect Debug Information

When reporting issues, include:

1. **Error messages** (full text, including stack traces)
2. **Steps to reproduce**
3. **Environment info:**
   ```bash
   docker --version
   docker-compose --version
   python --version
   node --version
   ```
4. **Configuration** (sanitize secrets)
5. **Log excerpts:**
   ```bash
   docker-compose logs --tail=100 backend > backend.log
   ```

### Log Locations

| Component | Location |
|-----------|----------|
| Backend | `docker-compose logs backend` |
| Frontend | Browser console (F12) |
| Database | `docker-compose logs db` |
| Redis | `docker-compose logs redis` |
| Celery | `docker-compose logs celery-worker` |

### Support Channels

1. **Documentation** - Check this wiki
2. **GitHub Issues** - Search existing issues first
3. **New Issue** - Create with debug information
4. **Team Chat** - For internal teams

---

## Related Documentation

- [Getting Started](Getting-Started) - Installation guide
- [Configuration](Configuration) - Environment setup
- [Architecture](Architecture) - System design
- [Development](Development) - Contributing guide
