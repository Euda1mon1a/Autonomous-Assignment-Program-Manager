# Scheduling System Understanding

> **Last Updated:** 2025-12-31
> **Status:** Documenting as we learn
> **Block 10:** IMMINENT - must be produced in next 1-2 days (test case)

---

## Block 10 Status

| Metric | Value |
|--------|-------|
| **Date Range** | 2026-03-12 → 2026-04-08 |
| **Duration** | 28 days |
| **Half-Day Slots** | 56 (AM/PM) |
| **Assignments** | 992 (in baseline backup) |
| **Origin** | Test case created by team |
| **Purpose** | Validate scheduling before production |

### 28-Day Bug
- **Frontend was:** Calculating dates with hardcoded +28 day math
- **Should be:** Reading actual dates from DB via blocks API
- **Fix applied:** `useBlockRanges` hook now fetches real block dates
- **DB is correct:** Dates are right in database

---

## Core Principles

1. **Call is FACULTY ONLY** (residents = v2 future)
2. **Call is SEPARATE from block assignments** - different table, different logic
3. **Equity-based distribution** among eligible faculty

---

## Call Types

| Type | Days | Coverage |
|------|------|----------|
| `overnight` | Sun-Thurs | Weeknight overnight |
| `weekend` | Fri-Sat | Covered by FMIT (see below) |
| `backup` | Any | Secondary coverage |

---

## Sun-Thurs Call Rules

### Eligibility
- **Eligible:** All faculty EXCEPT FMIT attending
- **NOT Eligible:**
  - FMIT attending (already providing continuous coverage)
  - Faculty on leave
  - Faculty on TDY
  - Faculty absent for ANY reason

### Equity
- Call distributed equitably among eligible faculty
- Tracked via `sunday_call_count` and `weekday_call_count` in `people` table

### Post-Call (Next Day)
```
Sun-Thurs Overnight Call
         ↓
Next Day AM: PCAT (Post-Call Attending)
Next Day PM: DO (Direct Observation)
```

- **PCAT:** Supervise resident clinic while post-call (lighter duty)
- **DO:** Direct Observation of resident encounters (educational)
- **PCAT/DO do NOT exist on weekends**

---

## Friday-Sunday Coverage (FMIT)

### FMIT Attending Schedule
```
Friday 0800 (or AM start) → Sunday 1200 (noon)
        CONTINUOUS COVERAGE
```

- FMIT attending covers the entire weekend
- This is why FMIT is not eligible for Sun-Thurs call
- FMIT handles Friday and Saturday "call" implicitly

### FMIT Implications
- No separate weekend call assignment needed for FMIT week
- FMIT attending already present for weekend coverage
- Tracked via `fmit_weeks_count` in `people` table

---

## Night Float (Residents)

### NF Post-Call Rule
When Night Float rotation ENDS (at block-half boundary):
```
NF ends at block-half transition
         ↓
Next day = PC (Post-Call) - FULL DAY (AM + PM)
```

### Block-Half Transitions
| NF Assignment | PC Day |
|---------------|--------|
| Half 1 (Days 1-14) | Day 15 (first day of Half 2) |
| Half 2 (Days 15-28) | Day 1 of next block |

### Why This Matters
- **PC gives NF resident their day off**
- PC is CRITICAL priority - trumps any other rotation
- This is mandatory recovery time after night shifts

---

## Constraint Files

| File | Purpose |
|------|---------|
| `constraints/post_call.py` | PCAT/DO after Sun-Thurs call |
| `constraints/night_float_post_call.py` | PC day after NF ends |
| `constraints/call_coverage.py` | Call coverage requirements |
| `constraints/call_equity.py` | Fair distribution |
| `constraints/overnight_call.py` | Overnight call rules |
| `validators/call_validator.py` | Call validation |
| `fair_call_optimizer.py` | Equity optimization |

---

## Database Tables

### call_assignments
```sql
call_assignments {
  id         UUID PK
  date       DATE        -- specific date
  person_id  UUID FK     -- faculty member
  call_type  VARCHAR     -- 'overnight', 'weekend', 'backup'
  is_weekend BOOLEAN
  is_holiday BOOLEAN
  created_at TIMESTAMP
}

CONSTRAINT: unique_call_per_day (date, person_id, call_type)
```

### people (call tracking columns)
```sql
sunday_call_count    INT  -- equity tracking
weekday_call_count   INT  -- equity tracking
fmit_weeks_count     INT  -- FMIT week tracking
```

---

## Activity Types Reference

| Abbrev | Name | Who | When | Priority |
|--------|------|-----|------|----------|
| **PCAT** | Post-Call Attending | Faculty | AM after overnight | HIGH |
| **DO** | Direct Observation | Faculty | PM after overnight | HIGH |
| **PC** | Post-Call | Resident | Full day after NF ends | CRITICAL |
| **NF** | Night Float | Resident | Night coverage rotation | - |
| **FMIT** | Faculty Member In Training | Faculty | Week-long including weekend | - |

---

## FMIT Distribution

### Target Allocation
| Role | FMIT Weeks/Year |
|------|-----------------|
| Regular Faculty | **6 weeks** |
| Dept Chief | **1-2 weeks** |

### Distribution Rules
- Can be any time, anywhere in the academic year
- Not clustered - spread throughout year
- Tracked via `fmit_weeks_count` in `people` table

### Current State (AY 2025-26)
- **Faculty have already selected their weeks**
- Manual/preference-based assignment

### Future State (Goal)
1. System generates FMIT assignments (equity-based)
2. Faculty can trade/swap to get preferred weeks
3. Swap system validates and executes trades

### Holiday FMIT
- **TBD** - not sure if holidays included in FMIT week
- Goal: Eventually make holiday FMIT equitable too
- Holiday call equity also a future consideration

### FMIT Week Structure (Reminder)
```
Friday AM → Sunday 1200 (continuous coverage)
  - Covers weekend call implicitly
  - FMIT attending NOT eligible for Sun-Thurs call that week
```

---

## Credentials & Procedures

### Core Concept
- **Credentials = procedure-specific faculty qualifications**
- Faculty are NOT interchangeable - different credentials
- Scheduler must match credentialed faculty to procedure slots

### Credential-Restricted Clinic Types

| Clinic Type | Restriction |
|-------------|-------------|
| **Vasectomy Procedure** | Only credentialed faculty |
| **Vasectomy Counseling** | Only credentialed faculty |
| **Sports Medicine** | Only Sports Med faculty (+ their rotating residents) |
| **IUD procedures** | Only credentialed faculty |
| (Other procedures) | Based on `procedure_credentials` table |

### Database Tables
- `procedures` - List of procedures
- `procedure_credentials` - Which faculty have which credentials
- `certification_types` - Types of certifications

### Scheduling Implication
When assigning faculty to procedure clinics:
1. Check `procedure_credentials` for eligibility
2. Only schedule credentialed faculty
3. Sports Med is special case (faculty specialty, not just credential)

---

## Open Questions

1. ~~How does FMIT week assignment work?~~ → Documented above
2. What happens if no faculty eligible for call on a given night?
3. Backup call - when/how assigned?
4. ~~Holiday call/FMIT rules?~~ → TBD, future equity goal

---

## Files to Reference

- `docs/architecture/FACULTY_SCHEDULING_SPECIFICATION.md` (referenced in constraints)
- `backend/app/scheduling/constraints/fmit.py`

---

*This document updated live during ORCHESTRATOR session 2025-12-31*
