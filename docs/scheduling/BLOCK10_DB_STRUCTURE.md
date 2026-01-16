# Block 10 Database Structure

> **Source of Truth** for what should exist in the database for Block 10 schedule generation.
>
> **Block 10 Dates:** Thu Mar 12 - Wed Apr 8, 2026
> **Relevant FMIT Scope:** AY Weeks 36-40 (Mar 6 - Apr 9, 2026)

---

## 1. Faculty FMIT Schedule (AY 2025-2026)

**Source:** `Block10_FINAL_PIPELINE.xlsx` sheet "FMIT Attending (2025-2026)"

### Timing Rules (CRITICAL)

| Structure | Pattern | Length | Notes |
|-----------|---------|--------|-------|
| **Academic Block** | Thursday → Wednesday | 28 days | Administrative boundary |
| **FMIT Week** | Friday → Thursday | 7 days | **INDEPENDENT of blocks** |
| **PC Day** | Friday after FMIT ends | 1 day | Recovery day |

**FMIT weeks span block boundaries.** This is by design.

### Full AY Schedule

| AY Wk | Year | FMIT Week (Fri-Thu) | Faculty | Fri Call | Sat Call | Block.Wk |
|------:|------|---------------------|---------|----------|----------|----------|
| 1 | 2025 | Jul 04-10 | FAC-A | Jul 04 | Jul 05 | B1.W1 |
| 2 | 2025 | Jul 11-17 | FAC-B | Jul 11 | Jul 12 | B1.W2 |
| 3 | 2025 | Jul 18-24 | FAC-A | Jul 18 | Jul 19 | B1.W3 |
| 4 | 2025 | Jul 25-31 | FAC-C | Jul 25 | Jul 26 | B1.W4 |
| 5 | 2025 | Aug 01-7 | FAC-D | Aug 01 | Aug 02 | B2.W1 |
| 6 | 2025 | Aug 08-14 | FAC-C | Aug 08 | Aug 09 | B2.W2 |
| 7 | 2025 | Aug 15-21 | FAC-B | Aug 15 | Aug 16 | B2.W3 |
| 8 | 2025 | Aug 22-28 | FAC-E | Aug 22 | Aug 23 | B2.W4 |
| 9 | 2025 | Aug 29-Sep 04 | FAC-A | Aug 29 | Aug 30 | B3.W1 |
| 10 | 2025 | Sep 05-11 | FAC-F | Sep 05 | Sep 06 | B3.W2 |
| 11 | 2025 | Sep 12-18 | FAC-A | Sep 12 | Sep 13 | B3.W3 |
| 12 | 2025 | Sep 19-25 | FAC-G/FAC-F | Sep 19 | Sep 20 | B3.W4 |
| 13 | 2025 | Sep 26-Oct 02 | FAC-A | Sep 26 | Sep 27 | B4.W1 |
| 14 | 2025 | Oct 03-9 | FAC-F | Oct 03 | Oct 04 | B4.W2 |
| 15 | 2025 | Oct 10-16 | FAC-H | Oct 10 | Oct 11 | B4.W3 |
| 16 | 2025 | Oct 17-23 | FAC-D | Oct 17 | Oct 18 | B4.W4 |
| 17 | 2025 | Oct 24-30 | FAC-I | Oct 24 | Oct 25 | B5.W1 |
| 18 | 2025 | Oct 31-Nov 06 | FAC-G | Oct 31 | Nov 01 | B5.W2 |
| 19 | 2025 | Nov 07-13 | FAC-I | Nov 07 | Nov 08 | B5.W3 |
| 20 | 2025 | Nov 14-20 | FAC-J | Nov 14 | Nov 15 | B5.W4 |
| 21 | 2025 | Nov 21-27 | FAC-E | Nov 21 | Nov 22 | B6.W1 |
| 22 | 2025 | Nov 28-Dec 04 | FAC-B | Nov 28 | Nov 29 | B6.W2 |
| 23 | 2025 | Dec 05-11 | FAC-G | Dec 05 | Dec 06 | B6.W3 |
| 24 | 2025 | Dec 12-18 | FAC-B | Dec 12 | Dec 13 | B6.W4 |
| 25 | 2025 | Dec 19-25 | FAC-G | Dec 19 | Dec 20 | B7.W1 |
| 26 | 25→26 | Dec 26-Jan 01 | FAC-I | Dec 26 | Dec 27 | B7.W2 |
| 27 | 2026 | Jan 02-8 | FAC-D | Jan 02 | Jan 03 | B7.W3 |
| 28 | 2026 | Jan 09-15 | FAC-J | Jan 09 | Jan 10 | B7.W4 |
| 29 | 2026 | Jan 16-22 | FAC-E | Jan 16 | Jan 17 | B8.W1 |
| 30 | 2026 | Jan 23-29 | FAC-C | Jan 23 | Jan 24 | B8.W2 |
| 31 | 2026 | Jan 30-Feb 05 | FAC-K | Jan 30 | Jan 31 | B8.W3 |
| 32 | 2026 | Feb 06-12 | FAC-C | Feb 06 | Feb 07 | B8.W4 |
| 33 | 2026 | Feb 13-19 | FAC-J | Feb 13 | Feb 14 | B9.W1 |
| 34 | 2026 | Feb 20-26 | FAC-E | Feb 20 | Feb 21 | B9.W2 |
| 35 | 2026 | Feb 27-Mar 05 | FAC-F | Feb 27 | Feb 28 | B9.W3 |
| **36** | **2026** | **Mar 06-12** | **FAC-C** | **Mar 06** | **Mar 07** | **B9.W4** |
| **37** | **2026** | **Mar 13-19** | **FAC-G** | **Mar 13** | **Mar 14** | **B10.W1** |
| **38** | **2026** | **Mar 20-26** | **FAC-D** | **Mar 20** | **Mar 21** | **B10.W2** |
| **39** | **2026** | **Mar 27-Apr 02** | **FAC-G** | **Mar 27** | **Mar 28** | **B10.W3** |
| **40** | **2026** | **Apr 03-9** | **FAC-I** | **Apr 03** | **Apr 04** | **B10.W4** |
| 41 | 2026 | Apr 10-16 | FAC-E | Apr 10 | Apr 11 | B11.W1 |
| 42 | 2026 | Apr 17-23 | FAC-J | Apr 17 | Apr 18 | B11.W2 |
| 43 | 2026 | Apr 24-30 | FAC-C | Apr 24 | Apr 25 | B11.W3 |
| 44 | 2026 | May 01-7 | FAC-D | May 01 | May 02 | B11.W4 |
| 45 | 2026 | May 08-14 | FAC-F | May 08 | May 09 | B12.W1 |
| 46 | 2026 | May 15-21 | FAC-J | May 15 | May 16 | B12.W2 |
| 47 | 2026 | May 22-28 | FAC-F | May 22 | May 23 | B12.W3 |
| 48 | 2026 | May 29-Jun 04 | FAC-A | May 29 | May 30 | B12.W4 |
| 49 | 2026 | Jun 05-11 | FAC-I | Jun 05 | Jun 06 | B13.W1 |
| 50 | 2026 | Jun 12-18 | FAC-B | Jun 12 | Jun 13 | B13.W2 |
| 51 | 2026 | Jun 19-25 | FAC-I | Jun 19 | Jun 20 | B13.W3 |
| 52 | 2026 | Jun 26-Jul 02 | FAC-B | Jun 26 | Jun 27 | B13.W4 |

**Bold = Block 10 scope (AY Weeks 36-40)**

---

## 2. Database Tables

### Order of Operations (Preload vs Solver)

**Phase 1: PRELOAD** (locked before solver runs)
1. Absences (LV, HOL, DEP, TDY)
2. **FMIT** - `inpatient_preloads` table
3. **FMIT Fri/Sat call** - `call_assignments` table (auto-assigned with FMIT)
4. C-I, Night Float, aSM, Conferences, Protected time

**Phase 2: SOLVER** (computed)
1. Sun-Thu call (min-gap decay) → `call_assignments`
2. Outpatient assignments
3. Faculty AT/C assignments
4. Admin time (GME/DFM)

---

## 3. Table: `inpatient_preloads`

**Purpose:** Faculty FMIT week assignments (foundational preload)

### Block 10 Correct Data

| person_id | rotation_type | start_date | end_date | fmit_week_number | notes |
|-----------|---------------|------------|----------|------------------|-------|
| (FAC-C UUID) | FMIT | 2026-03-06 | 2026-03-12 | 4 | Block 9 Week 4 (spans into Block 10) |
| (FAC-G UUID) | FMIT | 2026-03-13 | 2026-03-19 | 1 | Block 10 Week 1 |
| (FAC-D UUID) | FMIT | 2026-03-20 | 2026-03-26 | 2 | Block 10 Week 2 |
| (FAC-G UUID) | FMIT | 2026-03-27 | 2026-04-02 | 3 | Block 10 Week 3 |
| (FAC-I UUID) | FMIT | 2026-04-03 | 2026-04-09 | 4 | Block 10 Week 4 (spans into Block 11) |

### Validation Query

```sql
SELECT p.name, ip.rotation_type, ip.start_date, ip.end_date, ip.fmit_week_number, ip.notes
FROM inpatient_preloads ip
JOIN people p ON ip.person_id = p.id
WHERE ip.start_date <= '2026-04-09' AND ip.end_date >= '2026-03-06'
ORDER BY ip.start_date;
```

**Expected:** 5 rows matching above

---

## 4. Table: `call_assignments`

**Purpose:** Overnight call assignments (both preloaded FMIT call and solver-assigned Sun-Thu call)

### Block 10 FMIT Fri/Sat Call (PRELOADED)

| date | person_id | call_type | is_weekend | source |
|------|-----------|-----------|------------|--------|
| 2026-03-06 (Fri) | FAC-C | overnight | true | FMIT preload |
| 2026-03-07 (Sat) | FAC-C | overnight | true | FMIT preload |
| 2026-03-13 (Fri) | FAC-G | overnight | true | FMIT preload |
| 2026-03-14 (Sat) | FAC-G | overnight | true | FMIT preload |
| 2026-03-20 (Fri) | FAC-D | overnight | true | FMIT preload |
| 2026-03-21 (Sat) | FAC-D | overnight | true | FMIT preload |
| 2026-03-27 (Fri) | FAC-G | overnight | true | FMIT preload |
| 2026-03-28 (Sat) | FAC-G | overnight | true | FMIT preload |
| 2026-04-03 (Fri) | FAC-I | overnight | true | FMIT preload |
| 2026-04-04 (Sat) | FAC-I | overnight | true | FMIT preload |

### Block 10 Sun-Thu Call (SOLVER OUTPUT)

Sun-Thu call is assigned by the solver with these constraints:
- **FMIT faculty CANNOT take Sun-Thu call during their FMIT week**
- Min-gap decay algorithm for equity
- Must not conflict with absences

| Date Range | DOW | Constraint |
|------------|-----|------------|
| Mar 08-12 (Sun-Thu) | 0-4 | FAC-C blocked (on FMIT) |
| Mar 15-19 (Sun-Thu) | 0-4 | FAC-G blocked (on FMIT) |
| Mar 22-26 (Sun-Thu) | 0-4 | FAC-D blocked (on FMIT) |
| Mar 29-Apr 02 (Sun-Thu) | 0-4 | FAC-G blocked (on FMIT) |
| Apr 05-09 (Sun-Thu) | 0-4 | FAC-I blocked (on FMIT) |

### Validation Query (FMIT Fri/Sat)

```sql
SELECT ca.date, EXTRACT(DOW FROM ca.date) as dow, p.name, ca.call_type
FROM call_assignments ca
JOIN people p ON ca.person_id = p.id
WHERE ca.date >= '2026-03-06' AND ca.date <= '2026-04-09'
  AND EXTRACT(DOW FROM ca.date) IN (5, 6)  -- Friday=5, Saturday=6
ORDER BY ca.date;
```

**Expected:** 10 rows matching FMIT faculty

### Validation Query (No FMIT Conflicts)

```sql
-- Should return 0 rows (no FMIT faculty on Sun-Thu call during their FMIT week)
SELECT ca.date, p.name as on_call, ip.start_date as fmit_start, ip.end_date as fmit_end
FROM call_assignments ca
JOIN people p ON ca.person_id = p.id
JOIN inpatient_preloads ip ON ip.person_id = ca.person_id
WHERE ca.date BETWEEN ip.start_date AND ip.end_date
  AND EXTRACT(DOW FROM ca.date) NOT IN (5, 6);  -- Not Fri/Sat
```

**Expected:** 0 rows

---

## 5. Table: `absences`

**Purpose:** Faculty/resident unavailability (vacation, TDY, deployment, etc.)

### Block 10 Faculty Absences

| person | start_date | end_date | absence_type | notes |
|--------|------------|----------|--------------|-------|
| FAC-A | 2026-03-09 | 2026-03-14 | TDY | USAFP conference |
| FAC-F | 2025-12-01 | 2026-06-30 | OTHER | Extended leave (Dec-Jun) |
| FAC-J | 2026-02-21 | 2026-06-30 | DEPLOYED | Deployment |
| FAC-C | 2026-03-06 | 2026-03-12 | VACATION | (Also on FMIT this week) |
| FAC-C | 2026-03-23 | 2026-03-27 | VACATION | |
| FAC-C | 2026-03-30 | 2026-03-30 | VACATION | Single day |
| FAC-K | 2026-03-06 | 2026-03-14 | VACATION | Vacation + USAFP |
| FAC-G | 2026-04-05 | 2026-04-07 | VACATION | |
| FAC-D | 2026-03-09 | 2026-03-14 | TDY | USAFP/TDY |

### Block 10 Resident Absences

| person | start_date | end_date | absence_type | notes |
|--------|------------|----------|--------------|-------|
| RES-1 | 2026-03-25 | 2026-04-03 | VACATION | C4 |
| RES-2 | 2026-04-03 | 2026-04-08 | VACATION | |
| RES-3 | 2026-03-14 | 2026-03-20 | VACATION | |
| RES-4 | 2026-03-21 | 2026-03-23 | VACATION | |
| RES-5 | 2026-04-04 | 2026-04-07 | VACATION | |
| RES-6 | 2026-03-22 | 2026-03-28 | VACATION | |
| RES-6 | 2026-04-06 | 2026-04-08 | VACATION | |

### Validation Query

```sql
SELECT p.name, a.start_date, a.end_date, a.absence_type
FROM absences a
JOIN people p ON a.person_id = p.id
WHERE a.start_date <= '2026-04-08' AND a.end_date >= '2026-03-12'
ORDER BY p.type, p.name, a.start_date;
```

### Call/Absence Conflict Check

```sql
-- Should return 0 rows (no one on call during their absence)
SELECT ca.date, p.name, a.absence_type, a.start_date, a.end_date
FROM call_assignments ca
JOIN people p ON ca.person_id = p.id
JOIN absences a ON a.person_id = ca.person_id
  AND ca.date BETWEEN a.start_date AND a.end_date
WHERE ca.date BETWEEN '2026-03-12' AND '2026-04-08';
```

**Expected:** 0 rows

---

## 6. Table: `half_day_assignments`

**Purpose:** Granular half-day slot assignments (AM/PM)

**Status:** Empty for Block 10 (preload expansion not yet run)

This table is populated by the preload expansion service after FMIT and other preloads are in place.

### Source Priority

| Priority | Source | Description |
|----------|--------|-------------|
| 1 | `preload` | FMIT, call, absences - NEVER overwritten |
| 2 | `manual` | Explicit human override |
| 3 | `solver` | Computed by CP-SAT |
| 4 | `template` | Default from WeeklyPattern |

---

## 7. Table: `people`

**Purpose:** Faculty and resident roster

### Faculty UUIDs (Block 10 FMIT relevant)

```sql
SELECT id, name FROM people
WHERE type = 'faculty'
  AND name ILIKE ANY(ARRAY['%FAC-C%', '%FAC-G%', '%FAC-D%', '%FAC-I%']);
```

| UUID | Name |
|------|------|
| 1571ad88-2632-4c98-ad98-3d50ee8a3f83 | FAC-C |
| 1c4d3de2-4ae1-4229-a108-e734e10d45cf | FAC-G |
| 27dd09bd-426c-4930-a8ea-c8e1bf40c192 | FAC-D |
| (lookup) | FAC-I |

### Adjunct Faculty (Special Rules)

| Name | clinic_min | clinic_max | Notes |
|------|------------|------------|-------|
| ADJ-1 | 0 | 0 | FMIT/Call only |
| ADJ-2 | 0 | 0 | FMIT/Call only |

These faculty:
- CAN be assigned FMIT weeks
- CAN take overnight call
- Should NOT have regular C/AT/GME assignments
- "None/None" in export is CORRECT

---

## 8. Validation Checklist

Run these queries to verify Block 10 DB state:

### 1. FMIT Preloads (should be 5 rows)
```sql
SELECT COUNT(*) FROM inpatient_preloads
WHERE start_date <= '2026-04-09' AND end_date >= '2026-03-06';
```

### 2. FMIT Fri/Sat Call (should be 10 rows)
```sql
SELECT COUNT(*) FROM call_assignments
WHERE date >= '2026-03-06' AND date <= '2026-04-09'
  AND EXTRACT(DOW FROM date) IN (5, 6);
```

### 3. No FMIT/Sun-Thu Conflicts (should be 0 rows)
```sql
SELECT COUNT(*) FROM call_assignments ca
JOIN inpatient_preloads ip ON ip.person_id = ca.person_id
WHERE ca.date BETWEEN ip.start_date AND ip.end_date
  AND EXTRACT(DOW FROM ca.date) NOT IN (5, 6);
```

### 4. No Call/Absence Conflicts (should be 0 rows)
```sql
SELECT COUNT(*) FROM call_assignments ca
JOIN absences a ON a.person_id = ca.person_id
  AND ca.date BETWEEN a.start_date AND a.end_date
WHERE ca.date BETWEEN '2026-03-12' AND '2026-04-08';
```

---

## 9. Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| FMIT faculty on Sun-Thu call | Solver didn't respect constraint | Delete conflicting call, re-run solver |
| Call during absence | Absence loaded after call | Delete conflicting call, assign replacement |
| Wrong FMIT dates | Block vs FMIT week confusion | FMIT is Fri-Thu, blocks are Thu-Wed |
| Missing Fri/Sat call | FMIT call not preloaded | Insert from FMIT schedule |

---

## 10. Key Files

| File | Purpose |
|------|---------|
| `backend/app/models/inpatient_preload.py` | InpatientPreload model |
| `backend/app/services/block_schedule_export_service.py` | Export pipeline |
| `backend/app/scheduling/constraints/fmit.py` | FMIT constraints |
| `Block10_FINAL_PIPELINE.xlsx` | Current working schedule |
| `.claude/skills/tamc-excel-scheduling/SKILL.md` | Scheduling rules |

---

*Last updated: 2026-01-15*
