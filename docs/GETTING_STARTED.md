***REMOVED*** Getting Started with Residency Scheduler

Quick start guide for new users and developers.

---

***REMOVED******REMOVED*** For End Users (Program Coordinators)

***REMOVED******REMOVED******REMOVED*** First Time Setup

1. **Access the application**: Navigate to `http://localhost:3000`
2. **Login**: Use credentials provided by admin
3. **View dashboard**: See current schedules and compliance status

***REMOVED******REMOVED******REMOVED*** Common Tasks

**View Current Schedule:**
1. Click "Schedules" in navigation
2. Select date range
3. View assignments by person or by date

**Request Time Off:**
1. Go to "Absences" → "Request Leave"
2. Select dates and type (vacation, sick, etc.)
3. Submit for approval

**Request Schedule Swap:**
1. Go to "Swaps" → "Request Swap"
2. Select week to give away
3. Choose swap type (one-to-one or absorb)
4. System will suggest compatible faculty

---

***REMOVED******REMOVED*** For Developers

***REMOVED******REMOVED******REMOVED*** Quick Start

```bash
***REMOVED*** 1. Clone repository
git clone <repository-url>
cd Autonomous-Assignment-Program-Manager

***REMOVED*** 2. Start services
docker-compose up -d

***REMOVED*** 3. Access applications
***REMOVED*** Backend API: http://localhost:8000
***REMOVED*** API Docs: http://localhost:8000/docs
***REMOVED*** Frontend: http://localhost:3000

***REMOVED*** 4. Run tests
cd backend && pytest
cd frontend && npm test
```

***REMOVED******REMOVED******REMOVED*** Development Workflow

1. **Create feature branch**: `git checkout -b feature/my-feature`
2. **Make changes**: Follow [CLAUDE.md](CLAUDE.md) guidelines
3. **Run tests**: Ensure all tests pass
4. **Create PR**: Push to GitHub and open pull request
5. **Wait for review**: Address feedback
6. **Merge**: After approval

***REMOVED******REMOVED******REMOVED*** Key Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Development guidelines |
| `docker-compose.yml` | Service configuration |
| `backend/app/main.py` | FastAPI application entry |
| `frontend/src/pages/` | Next.js pages |

---

***REMOVED******REMOVED*** For Administrators

***REMOVED******REMOVED******REMOVED*** Initial System Setup

```bash
***REMOVED*** 1. Configure environment
cp .env.example .env
***REMOVED*** Edit .env with your settings

***REMOVED*** 2. Generate secrets
python -c 'import secrets; print(secrets.token_urlsafe(32))'

***REMOVED*** 3. Start services
docker-compose up -d

***REMOVED*** 4. Create admin user
cd backend
python -m app.cli user create \
  --email admin@example.com \
  --role ADMIN \
  --first-name Admin \
  --last-name User

***REMOVED*** 5. Seed initial data
python -m app.cli data seed --type all
```

***REMOVED******REMOVED******REMOVED*** Backup Strategy

```bash
***REMOVED*** Daily backups
0 2 * * * cd /path/to/app && docker-compose exec -T db pg_dump -U scheduler residency_scheduler > backup_$(date +\%Y\%m\%d).sql

***REMOVED*** Weekly backup rotation
***REMOVED*** Keep last 4 weeks
```

---

***REMOVED******REMOVED*** Next Steps

- **Users**: Read [User Workflows](guides/user-workflows.md)
- **Developers**: Read [Development Guide](CLAUDE.md)
- **Admins**: Read [Admin Manual](admin-manual/)

---

***REMOVED******REMOVED*** Common Questions

**Q: How do I reset my password?**
A: Contact your administrator or use CLI: `python -m app.cli user reset-password --email your@email.com`

**Q: Why is schedule generation slow?**
A: CP-SAT algorithm is thorough but slow. Try `greedy` algorithm for faster results.

**Q: How do I approve leave requests?**
A: Go to "Absences" → "Pending Requests" → Click "Approve"

**Q: Can I export schedules to Excel?**
A: Yes! Go to "Schedules" → "Export" → Select "Excel" format

---

***REMOVED******REMOVED*** See Also

- [Quick Reference](QUICK_REFERENCE.md)
- [Full Documentation](README.md)
- [API Documentation](api/README.md)
- [Troubleshooting](guides/SCHEDULE_GENERATION_RUNBOOK.md***REMOVED***troubleshooting)
