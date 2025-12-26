# Inpatient Rotation Seeding Guide

> **Purpose:** Guide for seeding inpatient rotations (FMIT, Night Float, NICU) from Airtable data before running the outpatient solver.

---

## Overview

The schedule generation workflow has two phases:

1. **Phase 1: Inpatient Pre-Assignment** - Seed FMIT, Night Float, NICU rotations from the block schedule
2. **Phase 2: Outpatient Optimization** - Run the CP-SAT solver to fill remaining half-day slots

This guide covers Phase 1.

---

## Data Files

### Location
```
docs/schedules/
├── sanitized_block_schedule.json      # Resident block assignments
├── sanitized_faculty_inpatient_schedule.json  # Faculty FMIT weeks
├── sanitized_residents.json           # Resident metadata
├── sanitized_faculty.json             # Faculty metadata
└── sanitized_rotations.json           # Rotation template definitions
```

### De-Sanitization Required

The repository contains **sanitized** data with PII removed:
- Resident names: `PGY1-01`, `PGY2-03`, etc.
- Faculty names: `FAC-PD`, `FAC-CORE-06`, etc.
- Emails: `redacted@example.com`

**Before seeding, you must de-sanitize locally:**

1. Create a mapping file (not committed):
   ```json
   {
     "PGY1-01": "Actual Resident Name",
     "PGY2-03": "Another Resident Name",
     "FAC-CORE-06": "Faculty Member Name"
   }
   ```

2. Replace sanitized names in the JSON files with real names

3. The seed script matches by **name** to database records

---

## Database Schema

### Key Tables

| Table | Purpose |
|-------|---------|
| `people` | Residents and faculty (name, type, pgy_level) |
| `blocks` | Half-day slots (date, time_of_day, block_number) |
| `rotation_templates` | Rotation types (name, activity_type) |
| `assignments` | Links person + block + rotation |

### Inpatient Templates

```sql
SELECT name, activity_type FROM rotation_templates
WHERE activity_type = 'inpatient';
```

Expected templates:
- `FMIT AM` / `FMIT PM`
- `Night Float AM` / `Night Float PM`
- `NICU`

---

## Seed Script Usage

### Location
```
scripts/seed_inpatient_rotations.py
```

### Prerequisites

1. Docker containers running (`docker compose up -d`)
2. Database has people, blocks, and rotation_templates seeded
3. JSON files de-sanitized with real names

### Commands

```bash
# Dry run - shows what would be created without making changes
python scripts/seed_inpatient_rotations.py --block 10 --dry-run

# Execute seeding
python scripts/seed_inpatient_rotations.py --block 10

# With clearing existing assignments first
python scripts/seed_inpatient_rotations.py --block 10 --clear-first
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SEED_BASE_URL` | `http://localhost:8000` | Backend API URL |
| `SEED_ADMIN_USERNAME` | `admin` | Auth username |
| `SEED_ADMIN_PASSWORD` | `admin123` | Auth password |

---

## Block Schedule Data Structure

### Resident Block Assignments (`block_schedule.json`)

```json
{
  "records": [
    {
      "fields": {
        "blockNumber": ["10"],
        "rotationName": ["Family Medicine Inpatient Team Resident"],
        "Resident": ["Actual Name Here"],
        "residentBlock": "Name - 10"
      }
    }
  ]
}
```

### Faculty FMIT Schedule (`faculty_inpatient_schedule.json`)

```json
{
  "records": [
    {
      "fields": {
        "blockNumber": 10,
        "weekOfBlock": 1,
        "blockWeekInpatientAttending": "Block 10 - Week 1 - Faculty Name",
        "Inpatient Week Start": "2026-03-13",
        "Inpatient Week End": "2026-03-19"
      }
    }
  ]
}
```

---

## Inpatient Rotation Types

The seed script identifies inpatient rotations by these keywords:

| Keyword | Rotation Type |
|---------|---------------|
| `FMIT` | Family Medicine Inpatient Team |
| `Night Float` | Overnight coverage |
| `Inpatient` | General inpatient |
| `NICU` | Neonatal ICU |
| `Neonatal Intensive Care` | NICU variant |
| `Labor and Delivery Night` | L&D night coverage |
| `Pediatrics Night Float` | Peds NF |

### Block 10 Example

| Resident | Rotation | Type |
|----------|----------|------|
| PGY2-06 | Labor and Delivery Night Float | NF |
| PGY1-06 | Pediatrics Night Float Intern | NF |
| PGY3-04 | Night Float + Medical Selective | NF |
| PGY2-03 | Family Medicine Inpatient Team Resident | FMIT |
| PGY3-02 | Family Medicine Inpatient Team Pre-Attending | FMIT |

---

## Full Workflow

### Step 1: Clear Existing Assignments (if regenerating)

```bash
docker compose exec db psql -U scheduler -d residency_scheduler \
  -c "DELETE FROM assignments WHERE block_id IN (
        SELECT id FROM blocks WHERE block_number = 10
      );"
```

### Step 2: Verify Database State

```bash
# Check people exist
docker compose exec db psql -U scheduler -d residency_scheduler \
  -c "SELECT name, type, pgy_level FROM people LIMIT 10;"

# Check blocks exist for target block
docker compose exec db psql -U scheduler -d residency_scheduler \
  -c "SELECT COUNT(*) FROM blocks WHERE block_number = 10;"
# Expected: 56 (28 days × 2 AM/PM)

# Check inpatient templates exist
docker compose exec db psql -U scheduler -d residency_scheduler \
  -c "SELECT name FROM rotation_templates WHERE activity_type = 'inpatient';"
```

### Step 3: De-Sanitize JSON Files

Replace sanitized names with real names in:
- `docs/schedules/sanitized_block_schedule.json`
- `docs/schedules/sanitized_faculty_inpatient_schedule.json`

Or create de-sanitized copies without the `sanitized_` prefix.

### Step 4: Run Seed Script

```bash
# From project root
cd /path/to/Autonomous-Assignment-Program-Manager

# Dry run first
python scripts/seed_inpatient_rotations.py --block 10 --dry-run

# If output looks correct, run for real
python scripts/seed_inpatient_rotations.py --block 10
```

### Step 5: Verify Inpatient Assignments

```bash
docker compose exec db psql -U scheduler -d residency_scheduler -c "
SELECT p.name, rt.name as rotation, rt.activity_type
FROM assignments a
JOIN people p ON a.person_id = p.id
JOIN rotation_templates rt ON a.rotation_template_id = rt.id
JOIN blocks b ON a.block_id = b.id
WHERE b.block_number = 10 AND rt.activity_type = 'inpatient'
GROUP BY p.name, rt.name, rt.activity_type;"
```

### Step 6: Run Outpatient Solver

```bash
# Get auth token
TOKEN=$(curl -s http://localhost:8000/api/v1/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Generate schedule (preserves inpatient, optimizes outpatient)
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Idempotency-Key: block10-full-$(date +%Y%m%d-%H%M%S)" \
  -d '{
    "start_date": "2026-03-12",
    "end_date": "2026-04-08",
    "algorithm": "cp_sat",
    "pgy_levels": [1, 2, 3],
    "timeout_seconds": 300
  }' | python3 -m json.tool
```

### Step 7: Validate Final Schedule

```bash
# Check total assignments
docker compose exec db psql -U scheduler -d residency_scheduler -c "
SELECT rt.activity_type, COUNT(*) as count
FROM assignments a
JOIN rotation_templates rt ON a.rotation_template_id = rt.id
JOIN blocks b ON a.block_id = b.id
WHERE b.block_number = 10
GROUP BY rt.activity_type;"

# Run ACGME validation
curl -s "http://localhost:8000/api/v1/schedule/validate?start_date=2026-03-12&end_date=2026-04-08" \
  | python3 -m json.tool
```

---

## Troubleshooting

### "Person not found" Errors

The name in your JSON doesn't match the database. Check:
```bash
docker compose exec db psql -U scheduler -d residency_scheduler \
  -c "SELECT name FROM people WHERE name ILIKE '%partial_name%';"
```

### "No template for rotation" Errors

The rotation name from Airtable doesn't map to a database template. The script tries to map:
- `*FMIT*` → `FMIT AM` / `FMIT PM`
- `*Night Float*` → `Night Float AM` / `Night Float PM`
- `*NICU*` → `NICU`

Check available templates:
```bash
docker compose exec db psql -U scheduler -d residency_scheduler \
  -c "SELECT name, activity_type FROM rotation_templates;"
```

### Duplicate Key Errors

Assignments already exist. Clear first:
```bash
docker compose exec db psql -U scheduler -d residency_scheduler \
  -c "DELETE FROM assignments WHERE block_id IN (
        SELECT id FROM blocks WHERE block_number = 10
      );"
```

---

## API Endpoints Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/auth/login/json` | POST | Get auth token |
| `/api/v1/people` | GET | List all people |
| `/api/v1/rotation-templates` | GET | List rotation templates |
| `/api/v1/blocks` | GET | List blocks (supports `block_number` filter) |
| `/api/v1/assignments` | POST | Create assignment |
| `/api/v1/schedule/generate` | POST | Run solver |
| `/api/v1/schedule/validate` | GET | Validate ACGME compliance |

---

## Related Files

- `scripts/seed_inpatient_rotations.py` - The seeding script
- `scripts/seed_people.py` - Seeds people from JSON
- `scripts/seed_templates.py` - Seeds rotation templates
- `backend/app/scheduling/engine.py` - Schedule generation engine
- `docs/guides/SCHEDULE_GENERATION_RUNBOOK.md` - Full generation workflow

---

*Last updated: 2025-12-26*
