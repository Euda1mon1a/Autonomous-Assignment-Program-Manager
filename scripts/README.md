***REMOVED*** Scripts

Utility scripts for the Residency Scheduler application.

***REMOVED******REMOVED*** Available Scripts

***REMOVED******REMOVED******REMOVED*** Data Import/Export

| Script | Description |
|--------|-------------|
| **import_excel.py** | Import absences and schedules from Excel files |
| **seed_people.py** | Seed the database with test people data |

***REMOVED******REMOVED******REMOVED*** System Operations

| Script | Description |
|--------|-------------|
| **backup-db.sh** | Database backup utility |
| **health-check.sh** | System health check |
| **start-celery.sh** | Start Celery worker and beat scheduler |
| **pre-deploy-validate.sh** | Pre-deployment validation checks |
| **audit-fix.sh** | Fix npm audit issues |

---

***REMOVED******REMOVED*** import_excel.py

Import leave/absences and pre-assigned rotations from Excel files.

***REMOVED******REMOVED******REMOVED*** Usage

```bash
***REMOVED*** Validate without making changes
python scripts/import_excel.py schedule.xlsx --dry-run

***REMOVED*** Import with verbose logging
python scripts/import_excel.py absences.xlsx --verbose

***REMOVED*** Use custom database
python scripts/import_excel.py data.xlsx --database-url "postgresql://..."
```

***REMOVED******REMOVED******REMOVED*** Options

- `--dry-run` - Parse and validate without creating records
- `--verbose, -v` - Enable detailed logging
- `--database-url` - Database connection string (defaults to DATABASE_URL)

***REMOVED******REMOVED******REMOVED*** Supported Formats

**Absence sheets** with columns:
- Person/Name, Type (VAC/SICK/DEP/etc.), Start Date, End Date, Notes

**Schedule sheets** (legacy format):
- AM/PM columns per day, person names in column E

***REMOVED******REMOVED******REMOVED*** Absence Type Abbreviations

| Abbreviation | Type |
|--------------|------|
| VAC | Vacation |
| SICK | Sick Leave |
| MED | Medical |
| CONF | Conference |
| DEP | Deployment |
| TDY | Temporary Duty |
| FEM | Family Emergency |
| PER | Personal |
| BER | Bereavement |
| MAT/PAT | Maternity/Paternity |

See [User Guide - Importing Data](../docs/user-guide/imports.md) for complete documentation.

---

***REMOVED******REMOVED*** seed_people.py

Seed the database with test residents and faculty for development.

***REMOVED******REMOVED******REMOVED*** Usage

```bash
***REMOVED*** Requires backend server running
python scripts/seed_people.py
```

Creates:
- 6 PGY-1 Residents
- 6 PGY-2 Residents
- 6 PGY-3 Residents
- 10 Faculty members with various roles

---

***REMOVED******REMOVED*** start-celery.sh

Start Celery background task workers.

***REMOVED******REMOVED******REMOVED*** Usage

```bash
***REMOVED*** Start both worker and beat scheduler
./scripts/start-celery.sh both

***REMOVED*** Start worker only
./scripts/start-celery.sh worker

***REMOVED*** Start beat scheduler only
./scripts/start-celery.sh beat
```

---

***REMOVED******REMOVED*** backup-db.sh

Create database backups.

***REMOVED******REMOVED******REMOVED*** Usage

```bash
./scripts/backup-db.sh
```

Creates timestamped backup in `backups/` directory.

---

***REMOVED******REMOVED*** health-check.sh

Run system health checks.

***REMOVED******REMOVED******REMOVED*** Usage

```bash
./scripts/health-check.sh
```

Checks:
- Database connectivity
- Redis connectivity
- API health endpoints
- Celery worker status

---

***REMOVED******REMOVED*** pre-deploy-validate.sh

Validate the system before deployment.

***REMOVED******REMOVED******REMOVED*** Usage

```bash
./scripts/pre-deploy-validate.sh
```

Validates:
- Environment variables
- Database migrations
- Static assets
- Configuration

---

***REMOVED******REMOVED*** Prerequisites

Most Python scripts require:

1. **Backend virtual environment activated**:
   ```bash
   cd backend
   source venv/bin/activate
   ```

2. **Dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Database running and accessible**

Shell scripts may require:
- Docker running (for containerized services)
- PostgreSQL client tools (`pg_dump`, `psql`)
- Redis CLI (`redis-cli`)
