# Getting Started with Residency Scheduler

Quick start guide for new users and developers.

---

## For End Users (Program Coordinators)

### First Time Setup

1. **Access the application**: Navigate to `http://localhost:3000`
2. **Login**: Use credentials provided by admin
3. **View dashboard**: See current schedules and compliance status

### Common Tasks

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

## For Developers

### Quick Start

```bash
# 1. Clone repository
git clone <repository-url>
cd Autonomous-Assignment-Program-Manager

# 2. Start services
docker-compose up -d

# 3. Access applications
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Frontend: http://localhost:3000

# 4. Run tests
cd backend && pytest
cd frontend && npm test
```

### Development Workflow

1. **Create feature branch**: `git checkout -b feature/my-feature`
2. **Make changes**: Follow [CLAUDE.md](CLAUDE.md) guidelines
3. **Run tests**: Ensure all tests pass
4. **Create PR**: Push to GitHub and open pull request
5. **Wait for review**: Address feedback
6. **Merge**: After approval

### Key Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Development guidelines |
| `docker-compose.yml` | Service configuration |
| `backend/app/main.py` | FastAPI application entry |
| `frontend/src/pages/` | Next.js pages |

---

## For Administrators

### Initial System Setup

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your settings

# 2. Generate secrets
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# 3. Start services
docker-compose up -d

# 4. Create admin user
cd backend
python -m app.cli user create \
  --email admin@example.com \
  --role ADMIN \
  --first-name Admin \
  --last-name User

# 5. Seed initial data
python -m app.cli data seed --type all
```

### Backup Strategy

```bash
# Daily backups
0 2 * * * cd /path/to/app && docker-compose exec -T db pg_dump -U scheduler residency_scheduler > backup_$(date +\%Y\%m\%d).sql

# Weekly backup rotation
# Keep last 4 weeks
```

---

## Next Steps

- **Users**: Read [User Workflows](guides/user-workflows.md)
- **Developers**: Read [Development Guide](CLAUDE.md)
- **Admins**: Read [Admin Manual](admin-manual/)

---

## Common Questions

**Q: How do I reset my password?**
A: Contact your administrator or use CLI: `python -m app.cli user reset-password --email your@email.com`

**Q: Why is schedule generation slow?**
A: CP-SAT algorithm is thorough but slow. Try `greedy` algorithm for faster results.

**Q: How do I approve leave requests?**
A: Go to "Absences" → "Pending Requests" → Click "Approve"

**Q: Can I export schedules to Excel?**
A: Yes! Go to "Schedules" → "Export" → Select "Excel" format

---

## See Also

- [Quick Reference](QUICK_REFERENCE.md)
- [Full Documentation](README.md)
- [API Documentation](api/README.md)
- [Troubleshooting](guides/SCHEDULE_GENERATION_RUNBOOK.md#troubleshooting)
