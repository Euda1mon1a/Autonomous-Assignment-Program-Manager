# Scripts

Utility scripts for database seeding, maintenance, and operations.

## Available Scripts

### generate_blocks.py

Generates scheduling blocks (AM/PM half-days) for the academic year. Each day has 2 blocks: one for AM and one for PM.

**Academic Year Structure:**
- 13 blocks, with the final block extended to reach June 30 (covers 365 days, or 366 in leap years)
- Academic year runs July 1 to June 30 (following year)
- Blocks are 4 weeks (28 days) except the final block, which absorbs the remaining days

**Usage:**

```bash
# Generate blocks for a single block period
python scripts/generate_blocks.py --start 2026-03-12 --end 2026-04-08 --block-number 10

# Generate full academic year 2025-2026 (July 1, 2025 - June 30, 2026)
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
| 13 | Jun 02, 2026 | Jun 30, 2026 |

### check-ai-assistant-usage.py

Checks for mixed AI assistant commits on the current Git branch. Helps prevent conflicts when using multiple AI coding assistants (Claude Code, GitHub Copilot, Codex, etc.) simultaneously.

**Usage:**

```bash
# Basic check
python scripts/check-ai-assistant-usage.py

# Strict mode (exits non-zero if issues found, for CI/hooks)
python scripts/check-ai-assistant-usage.py --strict

# Check more history (default: 20 commits)
python scripts/check-ai-assistant-usage.py --commits 50

# Quiet mode (only show warnings)
python scripts/check-ai-assistant-usage.py --quiet
```

**What It Detects:**
- Interleaved AI commits (e.g., `claude → codex → claude` without human consolidation)
- Multiple AI assistants used on the same branch
- Missing consolidation commits between AI sessions

See [AI Assistant Guardrails](../docs/development/ai-assistant-guardrails.md) for full documentation.

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

## Verification Scripts

### verify_schedule.py

Human-facing schedule verification script. Runs 12 checks against the database and generates visible PASS/FAIL reports.

**Usage:**
```bash
# From backend directory
cd backend
python ../scripts/verify_schedule.py --block 10 --start 2026-03-12 --end 2026-04-08

# Via Docker
docker compose exec backend python ../scripts/verify_schedule.py --block 10

# Without saving report
python ../scripts/verify_schedule.py --block 10 --no-save
```

**Checks Performed:**
1. FMIT faculty pattern (no back-to-back)
2. FMIT mandatory Fri+Sat call
3. Post-FMIT Sunday blocking
4. Night Float headcount = 1
5. FMIT resident headcount (1 per PGY)
6. Call spacing (no back-to-back weeks)
7. PGY-specific clinic days
8. Absence conflicts
9. Weekend coverage
10. ACGME compliance

**Output:** Markdown report saved to `docs/reports/schedule-verification-block{N}-{date}.md`

### verify_constraints.py

Pre-flight verification for scheduling constraints. Ensures constraints are implemented, exported, and registered.

**Usage:**
```bash
python scripts/verify_constraints.py
```

## Excel Tools

### excel/CSVAutoExport.bas

VBA module for Excel that automatically exports worksheets to CSV files when the workbook is saved. This eliminates the manual "Save As CSV" step for clinics using Excel for schedule management.

**Features:**
- Auto-export on save
- UTF-8 encoding for import system compatibility
- Naming convention: `{WorkbookName}_{SheetName}.csv`
- Ctrl+Shift+E manual trigger
- Skips hidden sheets

**Quick Setup:**
1. Open your schedule workbook in Excel
2. Press Alt+F11 to open VBA Editor
3. File > Import File > select `scripts/excel/CSVAutoExport.bas`
4. Copy `scripts/excel/ThisWorkbook_Events.txt` into the ThisWorkbook module
5. Save as .xlsm (macro-enabled)

See `scripts/excel/README.md` for detailed instructions.

### sync_rotation_names.py

Syncs rotation template names in the database with an authoritative CSV file containing medical abbreviation definitions. Compares DB rotation names against CSV full meanings and updates mismatches.

**Usage:**
```bash
# Dry run to see what would change
python scripts/sync_rotation_names.py --csv ~/Desktop/medical_abbreviations.csv --dry-run

# Apply changes
python scripts/sync_rotation_names.py --csv ~/Desktop/medical_abbreviations.csv

# Verbose mode shows all comparisons
python scripts/sync_rotation_names.py --csv ~/Desktop/medical_abbreviations.csv -v
```

**CSV Format Expected:**
```csv
abbreviation,full_meaning,category,description,frequency,percentage,notes
W,Weekend,OFF,,986,20.4,
C,Clinic,Outpatient,,744,15.4,
FMIT,Family Medicine Inpatient Team,inpatient,,202,4.2,
```

**Known Fixes Applied:**
- ICU: "Intensive Care Unit" (removes erroneous "Intern" suffix)
- LAD: "Labor and Delivery" (removes erroneous "Intern" suffix)
- IM-INT: "Internal Medicine Ward Intern" (adds missing "Ward")
- PEDS-W: "Pediatric Ward Intern" (uses singular form from CSV)
- PC: "Post Call" (matches CSV, removes "Recovery")

### import_excel.py

Imports scheduling data (absences, assignments) from Excel/CSV files into the database.

**Usage:**
```bash
# Dry run to preview changes
python scripts/import_excel.py schedule.csv --dry-run

# Import with verbose output
python scripts/import_excel.py absences.xlsx --verbose
```

See docstring in script for supported formats and abbreviations.

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
