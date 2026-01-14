# Expansion Service Bugs - Block10_OUTPUT vs ROSETTA

**Date:** 2026-01-14
**Comparison:** `Block10_OUTPUT.xlsx` vs `docs/scheduling/Block10_ROSETTA_CORRECT.xlsx`

---

## Summary

The expansion service is **stamping rotation codes without applying scheduling rules**.

### What's Working ✅
- Wed PM = LEC for FMC, PROC (non-exempt rotations)

### What's Broken ❌
1. **KAP pattern** not applied
2. **LDNF pattern** not applied
3. **Intern Wed AM continuity** not applied
4. **Last Wednesday (LEC/ADV)** not fully applied
5. **Mid-block transitions** not applied

---

## Bug #1: Kapiolani (KAP) Pattern Not Applied

**Resident:** Travis, Colin (Row 22 in OUTPUT)
**Rotation:** KAP (Kapiolani L&D)

| Column | Day | Expected | Actual | Status |
|--------|-----|----------|--------|--------|
| 15 | Mon PM | OFF | KAP | ❌ |
| 16 | Tue AM | OFF | KAP | ❌ |
| 17 | Tue PM | OFF | KAP | ❌ |
| 18 | Wed AM | C | KAP | ❌ |
| 19 | Wed PM | LEC | KAP | ❌ |
| 60 | Last Wed AM | LEC | KAP | ❌ |
| 61 | Last Wed PM | ADV | KAP | ❌ |

**Rule:** Kapiolani is off-site. Pattern should be:
- Mon: KAP / OFF (travel back)
- Tue: OFF / OFF (recovery)
- Wed: C / LEC (continuity clinic + lecture)
- Thu-Sun: KAP / KAP

**Fix needed in expansion service:**
```python
def get_kapiolani_assignment(day_of_week, is_am, is_last_wed):
    if is_last_wed:
        return "LEC" if is_am else "ADV"
    if day_of_week == 0:  # Monday
        return "KAP" if is_am else "OFF"
    elif day_of_week == 1:  # Tuesday
        return "OFF"
    elif day_of_week == 2:  # Wednesday
        return "C" if is_am else "LEC"
    else:
        return "KAP"
```

---

## Bug #2: LDNF Pattern Not Applied

**Resident:** Headid, Ronald (Row 17 in OUTPUT)
**Rotation:** L&D Night Float

| Column | Day | Expected | Actual | Status |
|--------|-----|----------|--------|--------|
| 6 | Thu AM | OFF | L&D | ❌ |
| 7 | Thu PM | LDNF | L&D | ❌ |
| 8 | Fri AM | **C** | L&D | ❌ |
| 18 | Wed AM | OFF | L&D | ❌ |
| 60 | Last Wed AM | LEC | L&D | ❌ |
| 61 | Last Wed PM | ADV | L&D | ❌ |

**CRITICAL:** LDNF gets **Friday AM clinic**, NOT Wednesday AM!

**Rule:** L&D Night Float pattern:
- Mon-Thu: OFF / LDNF (sleeping days, working nights)
- Fri: **C** / OFF (Friday morning clinic!)
- Sat-Sun: W / W (weekend off)

**Fix needed:**
```python
def get_ldnf_assignment(day_of_week, is_am, is_last_wed):
    if is_last_wed:
        return "LEC" if is_am else "ADV"
    if day_of_week == 4:  # Friday
        return "C" if is_am else "OFF"
    elif day_of_week in (5, 6):  # Weekend
        return "W"
    else:  # Mon-Thu
        return "OFF" if is_am else "LDNF"
```

---

## Bug #3: Intern Wednesday AM Continuity Not Applied

**Affected residents:** All PGY-1 interns (except NF/LDNF/KAP)

| Resident | Rotation | Col 18 Expected | Col 18 Actual | Status |
|----------|----------|-----------------|---------------|--------|
| Sloss, Meleighe | PROC | C | PR | ❌ |
| Monsivais, Joshua | IM | C | IM | ❌ |
| Wilhelm, Clara | Peds Ward | C | PedW | ❌ |
| Sawyer, Tessa | FMC | C | C | ✅ |

**Rule:** PGY-1 interns get continuity clinic (C) on Wednesday AM.

**Exceptions:**
- NF, PedNF, LDNF (night float - no Wed AM clinic)
- KAP (has own pattern with Wed AM = C)
- FMIT (inpatient coverage)

**Fix needed:**
```python
INTERN_WED_AM_EXEMPT = {'NF', 'PedNF', 'LDNF', 'FMIT', 'TDY', 'Hilo'}

def get_intern_wed_am(rotation, pgy_level, is_last_wed):
    if is_last_wed:
        return "LEC"  # Last Wed AM = LEC for all
    if pgy_level == 1 and rotation not in INTERN_WED_AM_EXEMPT:
        return "C"
    return None  # Use rotation default
```

---

## Bug #4: Last Wednesday Not Fully Applied

**Rule:** ALL residents get LEC/ADV on last Wednesday (Apr 8), cols 60-61.

| Resident | Col 60 Expected | Col 60 Actual | Col 61 Expected | Col 61 Actual |
|----------|-----------------|---------------|-----------------|---------------|
| Travis | LEC | KAP | ADV | KAP |
| Headid | LEC | L&D | ADV | L&D |
| Sloss | LEC | PR | ADV | LEC |
| Sawyer | LEC | C | ADV | LEC |

**Fix needed:**
```python
LAST_WED_AM_COL = 60
LAST_WED_PM_COL = 61

def apply_last_wednesday(col):
    if col == LAST_WED_AM_COL:
        return "LEC"
    if col == LAST_WED_PM_COL:
        return "ADV"
    return None
```

This should be checked **first** (highest priority) before any rotation-specific logic.

---

## Bug #5: Mid-Block Transitions Not Applied

**Affected residents:**
- You, Jae: NEURO → NF at col 28
- Wilhelm, Clara: Peds Ward → Peds NF at col 28
- Byrnes, Katherine: Peds NF → Peds Ward at col 28

**Rule:** At column 28 (Mar 23), switch to second rotation pattern.

| Resident | Col 28 Expected | Col 28 Actual | Col 29 Expected | Col 29 Actual |
|----------|-----------------|---------------|-----------------|---------------|
| You, Jae | OFF | NEURO? | NF | NEURO? |
| Wilhelm | OFF | PedW? | PedNF | PedW? |

**Fix needed:**
```python
MID_BLOCK_COL = 28

def get_active_rotation(col, rotation1, rotation2):
    if rotation2 and col >= MID_BLOCK_COL:
        return rotation2
    return rotation1
```

---

## Test File

Run the tests to verify fixes:

```bash
pytest tests/test_rosetta_comparison.py -v
```

Tests are in: `tests/test_rosetta_comparison.py`

---

## Priority Order for Fixes

1. **Last Wednesday** (highest priority - overrides everything)
2. **Wednesday PM = LEC** (already partially working)
3. **Rotation-specific patterns** (KAP, LDNF, NF)
4. **Intern Wed AM continuity** (PGY-1 only)
5. **Mid-block transitions** (col 28+)
6. **Default rotation pattern** (lowest priority)

The expansion service should apply rules in this order, with earlier rules overriding later ones.
