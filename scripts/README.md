# Scripts

Utility scripts for database seeding, maintenance, and operations.

## Available Scripts

### generate_blocks.py

Generates scheduling blocks (AM/PM half-days) for the academic year. Each day has 2 blocks: one for AM and one for PM.

**Academic Year Structure:**
- 13 blocks × 28 days = 364 days
- Academic year runs July 1 to June 29 (following year)
- Each block is exactly 4 weeks (28 days)

**Usage:**

```bash
# Generate blocks for a single block period
python scripts/generate_blocks.py --start 2026-03-10 --end 2026-04-06 --block-number 10

# Generate full academic year 2025-2026 (July 1, 2025 - June 29, 2026)
python scripts/generate_blocks.py --academic-year 2025

# Dry run to preview what would be created
python scripts/generate_blocks.py --academic-year 2025 --dry-run

# Verbose mode shows each block as it's created
python scripts/generate_blocks.py --academic-year 2025 --verbose
```

**Features:**
- Idempotent: Skips blocks that already exist in database
- Automatically detects weekends (Saturday/Sunday)
- Supports dry-run mode for previewing changes
- Verbose mode for detailed output

**Block Dates (Academic Year 2025-2026):**

| Block | Start Date | End Date |
|-------|------------|----------|
| 1 | Jul 01, 2025 | Jul 28, 2025 |
| 2 | Jul 29, 2025 | Aug 25, 2025 |
| 3 | Aug 26, 2025 | Sep 22, 2025 |
| 4 | Sep 23, 2025 | Oct 20, 2025 |
| 5 | Oct 21, 2025 | Nov 17, 2025 |
| 6 | Nov 18, 2025 | Dec 15, 2025 |
| 7 | Dec 16, 2025 | Jan 12, 2026 |
| 8 | Jan 13, 2026 | Feb 09, 2026 |
| 9 | Feb 10, 2026 | Mar 09, 2026 |
| 10 | Mar 10, 2026 | Apr 06, 2026 |
| 11 | Apr 07, 2026 | May 04, 2026 |
| 12 | May 05, 2026 | Jun 01, 2026 |
| 13 | Jun 02, 2026 | Jun 29, 2026 |

### seed_people.py

Seeds the database with test people (residents and faculty) via the API.

**Usage:**

```bash
# Requires the API to be running
python scripts/seed_people.py
```

Creates:
- 6 PGY-1 residents
- 6 PGY-2 residents
- 6 PGY-3 residents
- 10 faculty members with various roles

## Shell Scripts

### start-celery.sh

Starts Celery worker and/or beat scheduler.

```bash
./scripts/start-celery.sh both    # Start worker + beat
./scripts/start-celery.sh worker  # Worker only
./scripts/start-celery.sh beat    # Scheduler only
```

### backup-db.sh

Creates database backups with configurable retention.

### health-check.sh

Runs system health checks for deployment verification.

### pre-deploy-validate.sh

Validates system state before deployment.

### audit-fix.sh

Fixes npm audit issues in the frontend.

## Running Scripts

Most Python scripts require the backend environment:

```bash
# From project root
cd backend
source venv/bin/activate  # or your virtualenv activation
python ../scripts/script_name.py [args]

# Or with Docker
docker-compose exec backend python /app/scripts/script_name.py [args]
```

## Testing

Tests for scripts are located in `backend/tests/scripts/`:

```bash
cd backend
pytest tests/scripts/ -v
```
