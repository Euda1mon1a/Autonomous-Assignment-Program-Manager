***REMOVED*** Troubleshooting

This guide covers common issues and their solutions when using Residency Scheduler.

---

***REMOVED******REMOVED*** Quick Diagnostics

***REMOVED******REMOVED******REMOVED*** Health Check Commands

```bash
***REMOVED*** Check all service status (Docker)
docker-compose ps

***REMOVED*** Check backend health
curl http://localhost:8000/health

***REMOVED*** Check detailed health
curl http://localhost:8000/health/ready

***REMOVED*** View backend logs
docker-compose logs -f backend

***REMOVED*** View all logs
docker-compose logs -f
```

***REMOVED******REMOVED******REMOVED*** Common Status Codes

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

***REMOVED******REMOVED*** Installation Issues

***REMOVED******REMOVED******REMOVED*** Docker Won't Start

**Symptom:**
```
ERROR: Couldn't connect to Docker daemon
```

**Solutions:**
1. Ensure Docker is running:
   ```bash
   ***REMOVED*** macOS/Windows: Start Docker Desktop
   ***REMOVED*** Linux:
   sudo systemctl start docker
   ```

2. Check Docker permissions:
   ```bash
   sudo usermod -aG docker $USER
   ***REMOVED*** Log out and back in
   ```

3. Verify Docker version:
   ```bash
   docker --version  ***REMOVED*** Should be 20.10+
   docker-compose --version  ***REMOVED*** Should be 2.0+
   ```

---

***REMOVED******REMOVED******REMOVED*** Database Connection Failed

**Symptom:**
```
Error: Connection refused to localhost:5432
```

**Solutions:**

1. **Check if PostgreSQL is running:**
   ```bash
   ***REMOVED*** Docker
   docker-compose ps db

   ***REMOVED*** Local
   pg_isready -h localhost -p 5432
   ```

2. **Check DATABASE_URL format:**
   ```env
   ***REMOVED*** Correct format
   DATABASE_URL=postgresql://postgres:password@localhost:5432/residency_scheduler

   ***REMOVED*** Common mistakes
   DATABASE_URL=postgres://...  ***REMOVED*** Wrong - use postgresql://
   DATABASE_URL=postgresql://postgres@localhost:5432/db  ***REMOVED*** Missing password
   ```

3. **Verify database exists:**
   ```bash
   psql -U postgres -c "\l" | grep residency

   ***REMOVED*** Create if missing
   createdb residency_scheduler
   ```

4. **Check firewall/network:**
   ```bash
   ***REMOVED*** Test connection
   nc -zv localhost 5432
   ```

---

***REMOVED******REMOVED******REMOVED*** Redis Connection Failed

**Symptom:**
```
Error: Connection refused to localhost:6379
```

**Solutions:**

1. **Start Redis:**
   ```bash
   ***REMOVED*** Docker
   docker-compose up -d redis

   ***REMOVED*** Local
   redis-server
   ```

2. **Test connection:**
   ```bash
   redis-cli ping
   ***REMOVED*** Should return: PONG
   ```

3. **Check REDIS_URL:**
   ```env
   REDIS_URL=redis://localhost:6379/0
   ```

---

***REMOVED******REMOVED******REMOVED*** Migration Errors

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
   ***REMOVED*** Should show single head
   ```

4. **Force current version:**
   ```bash
   alembic stamp head
   ```

---

***REMOVED******REMOVED******REMOVED*** Port Already in Use

**Symptom:**
```
Error: Bind for 0.0.0.0:8000 failed: port is already allocated
```

**Solutions:**

1. **Find process using port:**
   ```bash
   ***REMOVED*** Linux/macOS
   lsof -i :8000

   ***REMOVED*** Windows
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

***REMOVED******REMOVED*** Authentication Issues

***REMOVED******REMOVED******REMOVED*** Login Failed

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
   ***REMOVED*** Via CLI
   cd backend
   python -m app.cli.reset_password user@example.com
   ```

3. **Check user in database:**
   ```sql
   SELECT email, is_active FROM users WHERE email = 'user@example.com';
   ```

---

***REMOVED******REMOVED******REMOVED*** Token Expired

**Symptom:**
```
401 Unauthorized - Token has expired
```

**Solutions:**

1. **Login again** to get new token

2. **Increase token lifetime (if appropriate):**
   ```env
   ACCESS_TOKEN_EXPIRE_MINUTES=2880  ***REMOVED*** 48 hours
   ```

3. **Check server time sync:**
   ```bash
   date
   ***REMOVED*** Ensure correct timezone
   ```

---

***REMOVED******REMOVED******REMOVED*** CORS Errors

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

***REMOVED******REMOVED*** Schedule Generation Issues

***REMOVED******REMOVED******REMOVED*** Generation Takes Too Long

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
   SCHEDULE_GENERATION_TIMEOUT=600  ***REMOVED*** 10 minutes
   ```

4. **Check Celery workers:**
   ```bash
   docker-compose logs celery-worker
   ***REMOVED*** Ensure workers are running and processing
   ```

---

***REMOVED******REMOVED******REMOVED*** Compliance Violations After Generation

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

***REMOVED******REMOVED******REMOVED*** "No Valid Schedule Found"

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

***REMOVED******REMOVED*** Celery/Background Task Issues

***REMOVED******REMOVED******REMOVED*** Tasks Not Running

**Symptom:**
Scheduled tasks don't execute.

**Solutions:**

1. **Check Celery worker:**
   ```bash
   docker-compose logs celery-worker

   ***REMOVED*** Verify worker is running
   celery -A app.core.celery_app inspect active
   ```

2. **Check Celery beat:**
   ```bash
   docker-compose logs celery-beat

   ***REMOVED*** Verify beat is scheduling
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

***REMOVED******REMOVED******REMOVED*** Tasks Stuck in Queue

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

***REMOVED******REMOVED*** Frontend Issues

***REMOVED******REMOVED******REMOVED*** Page Won't Load

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

***REMOVED******REMOVED******REMOVED*** Data Not Updating

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

***REMOVED******REMOVED******REMOVED*** Calendar Not Showing Events

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

***REMOVED******REMOVED*** Performance Issues

***REMOVED******REMOVED******REMOVED*** Slow API Responses

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

***REMOVED******REMOVED******REMOVED*** High Memory Usage

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

***REMOVED******REMOVED*** Data Issues

***REMOVED******REMOVED******REMOVED*** Missing Data After Migration

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
   ***REMOVED*** If using Docker
   docker-compose exec db pg_restore -U postgres -d residency_scheduler backup.dump
   ```

3. **Check if data exists:**
   ```sql
   SELECT COUNT(*) FROM people;
   SELECT COUNT(*) FROM assignments;
   ```

---

***REMOVED******REMOVED******REMOVED*** Import Failed

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

***REMOVED******REMOVED******REMOVED*** Export Not Working

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

***REMOVED******REMOVED*** Getting More Help

***REMOVED******REMOVED******REMOVED*** Collect Debug Information

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

***REMOVED******REMOVED******REMOVED*** Log Locations

| Component | Location |
|-----------|----------|
| Backend | `docker-compose logs backend` |
| Frontend | Browser console (F12) |
| Database | `docker-compose logs db` |
| Redis | `docker-compose logs redis` |
| Celery | `docker-compose logs celery-worker` |

***REMOVED******REMOVED******REMOVED*** Support Channels

1. **Documentation** - Check this wiki
2. **GitHub Issues** - Search existing issues first
3. **New Issue** - Create with debug information
4. **Team Chat** - For internal teams

---

***REMOVED******REMOVED*** Related Documentation

- [Getting Started](Getting-Started) - Installation guide
- [Configuration](Configuration) - Environment setup
- [Architecture](Architecture) - System design
- [Development](Development) - Contributing guide
