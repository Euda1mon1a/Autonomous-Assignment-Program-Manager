---
name: schedule-verification
description: Human verification checklist for generated schedules. Use when reviewing Block 10 or any generated schedule to ensure it makes operational sense. Covers FMIT, call, Night Float, clinic days, and absence handling.
---

# Schedule Verification Skill

Systematic checklist for human verification of generated schedules. Ensures the schedule makes operational sense before deployment.

## MANDATORY: Generate Visible Report

**CRITICAL:** Every time this skill runs, you MUST:

1. **Print a header** with block number and date range
2. **Run each check** and print PASS/FAIL for each item
3. **Show actual data** - not just "checked", but the values found
4. **Generate summary table** at the end with all results
5. **Save report** to `docs/reports/schedule-verification-{block}-{date}.md`

```
╔══════════════════════════════════════════════════════════════════╗
║  SCHEDULE VERIFICATION REPORT                                    ║
║  Block: 10  |  Date Range: 2026-03-10 to 2026-04-06              ║
║  Generated: 2025-12-26                                           ║
╠══════════════════════════════════════════════════════════════════╣
║  CHECK                                    │ STATUS │ DETAILS     ║
╠═══════════════════════════════════════════╪════════╪═════════════╣
║  FMIT faculty rotation pattern            │ ✅ PASS │ No b2b     ║
║  FMIT mandatory Fri+Sat call              │ ✅ PASS │ 4/4 weeks  ║
║  Post-FMIT Sunday blocking                │ ✅ PASS │ 0 conflicts║
║  Night Float headcount = 1                │ ❌ FAIL │ Found 3    ║
║  ...                                      │        │             ║
╚══════════════════════════════════════════════════════════════════╝
```

**DO NOT** silently run checks. Every check must produce visible output.

## When This Skill Activates

- After schedule generation completes
- Before deploying a new schedule to production
- When reviewing Block 10 or any academic block schedule
- When a human asks "does this schedule make sense?"
- After constraint changes to verify behavior

---

## Verification Checklist

### 1. Faculty FMIT Schedule

| Check | What to Verify | How to Check |
|-------|----------------|--------------|
| [ ] FMIT rotation pattern | No faculty has back-to-back FMIT weeks | Query: faculty with FMIT in consecutive weeks |
| [ ] FMIT mandatory call | FMIT faculty has Fri+Sat call during their week | Check call assignments for FMIT weeks |
| [ ] Post-FMIT Sunday block | No Sunday call within 3 days of FMIT end | Check Sunday call vs FMIT end dates |
| [ ] FMIT coverage | Every week has FMIT faculty assigned | No gaps in FMIT weekly coverage |

**Expected Pattern (Block 10 example):**
```
Week 1: FAC-CORE-01 (FMIT) → Fri/Sat call → Sun blocked
Week 2: FAC-CORE-02 (FMIT) → Fri/Sat call → Sun blocked
Week 3: FAC-CORE-01 (FMIT) → Fri/Sat call → Sun blocked
Week 4: FAC-CORE-03 (FMIT) → Fri/Sat call → Sun blocked
```

### 2. Resident Inpatient Assignments

| Check | What to Verify | Expected |
|-------|----------------|----------|
| [ ] FMIT headcount | 1 resident per PGY level on FMIT | 3 total per block |
| [ ] Night Float headcount | Exactly 1 resident on NF at a time | Never 0, never 2+ |
| [ ] NICU coverage | NICU resident has Friday PM clinic | Always |
| [ ] Post-Call | Thursday after NF ends is Post-Call | No assignments that day |

**PGY-Specific Clinic Days (FMIT residents):**
| PGY Level | Required Clinic Day |
|-----------|---------------------|
| PGY-1 | Wednesday AM |
| PGY-2 | Tuesday PM |
| PGY-3 | Monday PM |

### 3. Call Schedule Equity

| Check | What to Verify | Acceptable Range |
|-------|----------------|------------------|
| [ ] Sunday call distribution | Evenly distributed across faculty | Max variance: 1-2 |
| [ ] Weekday call distribution | Mon-Thu evenly distributed | Max variance: 2-3 |
| [ ] Call spacing | No back-to-back call weeks | Same faculty not in adjacent weeks |
| [ ] PD/APD Tuesday | Program Directors avoid Tuesday call | Preference, not hard |

### 4. Absence Handling

| Check | What to Verify | Expected |
|-------|----------------|----------|
| [ ] Leave respected | No assignments during approved leave | 0 conflicts |
| [ ] TDY respected | No assignments during TDY | 0 conflicts |
| [ ] Weekend assignments | Weekend blocks show appropriate coverage | Inpatient only |
| [ ] Holiday handling | Federal holidays have inpatient coverage | FMIT defaults |

### 5. Coverage Metrics

| Metric | Target | Warning | Violation |
|--------|--------|---------|-----------|
| Overall coverage | > 80% | 70-80% | < 70% |
| Weekday coverage | > 95% | 85-95% | < 85% |
| Weekend coverage | > 50% | 30-50% | < 30% |
| ACGME violations | 0 | 1-2 | > 2 |

---

## Spot Check Protocol

For any generated schedule, spot check **at least 3 people** of each type:

### Faculty Spot Check
1. Pick random faculty member
2. View their entire month
3. Verify:
   - FMIT weeks are not consecutive
   - Call weeks are spaced
   - Post-FMIT recovery days exist
   - No assignments during absences

### Resident Spot Check
1. Pick one resident from each PGY level
2. View their entire month
3. Verify:
   - Clinic days match PGY requirements
   - Night Float followed by Post-Call
   - No double-booking (AM+PM same day = OK, but not 2 rotations same slot)
   - Absences respected

---

## Query Templates

### Check FMIT Faculty Schedule
```sql
SELECT p.last_name, b.date, rt.name
FROM assignments a
JOIN blocks b ON a.block_id = b.id
JOIN people p ON a.person_id = p.id
JOIN rotation_templates rt ON a.rotation_template_id = rt.id
WHERE p.type = 'faculty'
  AND rt.activity_type = 'inpatient'
  AND b.date BETWEEN '2026-03-10' AND '2026-04-06'
ORDER BY p.last_name, b.date;
```

### Check Night Float Headcount
```sql
SELECT b.date, b.time_of_day, COUNT(*) as nf_count
FROM assignments a
JOIN blocks b ON a.block_id = b.id
JOIN rotation_templates rt ON a.rotation_template_id = rt.id
WHERE rt.name LIKE '%Night Float%'
  AND b.date BETWEEN '2026-03-10' AND '2026-04-06'
GROUP BY b.date, b.time_of_day
HAVING COUNT(*) != 1;
```

### Check for Absence Conflicts
```sql
SELECT p.last_name, b.date, rt.name as rotation, 'CONFLICT' as status
FROM assignments a
JOIN blocks b ON a.block_id = b.id
JOIN people p ON a.person_id = p.id
JOIN rotation_templates rt ON a.rotation_template_id = rt.id
WHERE EXISTS (
  SELECT 1 FROM absences ab
  WHERE ab.person_id = p.id
    AND b.date BETWEEN ab.start_date AND ab.end_date
)
AND rt.activity_type != 'absence';
```

---

## Red Flags (Stop and Investigate)

| Red Flag | Possible Cause | Action |
|----------|----------------|--------|
| 0% weekend coverage | Inpatient rotations not loading | Check `preserve_resident_inpatient` |
| All residents on Night Float | Missing headcount constraint | Check `ResidentInpatientHeadcountConstraint` |
| Faculty with 3+ FMIT weeks | Constraint not registered | Check `ConstraintManager.create_default()` |
| Assignments during leave | Absence preservation failing | Check `preserve_absence` |
| Back-to-back call weeks | CallSpacingConstraint weight too low | Increase weight from 8.0 |

---

## Sign-Off

After verification, update this section:

```
Schedule Verified: [ ] Yes  [ ] No
Block: ___
Verified By: ___
Date: ___
Issues Found: ___
Resolution: ___
```
