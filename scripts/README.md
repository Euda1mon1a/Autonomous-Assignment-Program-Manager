# Scripts

Utility scripts for the Residency Scheduler application.

## Available Scripts

### Data Import/Export

| Script | Description |
|--------|-------------|
| **import_excel.py** | Import absences and schedules from Excel files |
| **seed_people.py** | Seed the database with test people data |

### System Operations

| Script | Description |
|--------|-------------|
| **backup-db.sh** | Database backup utility |
| **health-check.sh** | System health check |
| **start-celery.sh** | Start Celery worker and beat scheduler |
| **pre-deploy-validate.sh** | Pre-deployment validation checks |
| **audit-fix.sh** | Fix npm audit issues |

---

## import_excel.py

Import leave/absences and pre-assigned rotations from Excel files.

### Usage

```bash
# Validate without making changes
python scripts/import_excel.py schedule.xlsx --dry-run

# Import with verbose logging
python scripts/import_excel.py absences.xlsx --verbose

# Use custom database
python scripts/import_excel.py data.xlsx --database-url "postgresql://..."
```

### Options

- `--dry-run` - Parse and validate without creating records
- `--verbose, -v` - Enable detailed logging
- `--database-url` - Database connection string (defaults to DATABASE_URL)

### Supported Formats

**Absence sheets** with columns:
- Person/Name, Type (VAC/SICK/DEP/etc.), Start Date, End Date, Notes

**Schedule sheets** (legacy format):
- AM/PM columns per day, person names in column E

### Absence Type Abbreviations

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

## seed_people.py

Seed the database with test residents and faculty for development.

### Usage

```bash
# Requires backend server running
python scripts/seed_people.py
```

Creates:
- 6 PGY-1 Residents
- 6 PGY-2 Residents
- 6 PGY-3 Residents
- 10 Faculty members with various roles

---

## start-celery.sh

Start Celery background task workers.

### Usage

```bash
# Start both worker and beat scheduler
./scripts/start-celery.sh both

# Start worker only
./scripts/start-celery.sh worker

# Start beat scheduler only
./scripts/start-celery.sh beat
```

---

## backup-db.sh

Create database backups.

### Usage

```bash
./scripts/backup-db.sh
```

Creates timestamped backup in `backups/` directory.

---

## health-check.sh

Run system health checks.

### Usage

```bash
./scripts/health-check.sh
```

Checks:
- Database connectivity
- Redis connectivity
- API health endpoints
- Celery worker status

---

## pre-deploy-validate.sh

Validate the system before deployment.

### Usage

```bash
./scripts/pre-deploy-validate.sh
```

Validates:
- Environment variables
- Database migrations
- Static assets
- Configuration

---

## Prerequisites

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
