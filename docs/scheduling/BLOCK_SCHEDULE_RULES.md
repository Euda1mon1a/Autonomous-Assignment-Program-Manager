# Block Schedule Rules - Definitive Reference

**Version:** 1.0
**Last Updated:** 2026-01-14
**Source:** Transcript analysis, PD feedback, AY 25-26 scheduling sessions
**Purpose:** RAG-indexable reference for expansion service and schedule validation

---

## Overview

This document defines the rules for expanding block assignments into daily half-day schedules. The expansion service reads rotation assignments and must apply these patterns to generate correct Excel output.

**Key Principle:** Rotations define WHERE a resident works, but patterns define WHAT appears in each cell.

---

## Column Reference (Block 10: Mar 12 - Apr 8, 2026)

```
Col  6-7:   Thu Mar 12 (AM/PM) - Block start
Col  8-9:   Fri Mar 13
Col 10-11:  Sat Mar 14
Col 12-13:  Sun Mar 15
Col 14-15:  Mon Mar 16
Col 16-17:  Tue Mar 17
Col 18-19:  Wed Mar 18 ← FIRST LEC DAY (col 19 = PM)
Col 20-21:  Thu Mar 19
Col 22-23:  Fri Mar 20
Col 24-25:  Sat Mar 21
Col 26-27:  Sun Mar 22
Col 28-29:  Mon Mar 23 ← MID-BLOCK TRANSITION POINT
Col 30-31:  Tue Mar 24
Col 32-33:  Wed Mar 25 ← SECOND LEC DAY (col 33 = PM)
Col 34-35:  Thu Mar 26
Col 36-37:  Fri Mar 27
Col 38-39:  Sat Mar 28
Col 40-41:  Sun Mar 29
Col 42-43:  Mon Mar 30
Col 44-45:  Tue Mar 31
Col 46-47:  Wed Apr 1 ← THIRD LEC DAY (col 47 = PM)
Col 48-49:  Thu Apr 2
Col 50-51:  Fri Apr 3
Col 52-53:  Sat Apr 4
Col 54-55:  Sun Apr 5
Col 56-57:  Mon Apr 6
Col 58-59:  Tue Apr 7
Col 60-61:  Wed Apr 8 ← LAST WEDNESDAY (special rules!)
```

### Key Column Sets

```python
# Wednesday PM columns (LEC)
LEC_COLS = {19, 33, 47, 61}

# Wednesday AM columns (intern continuity)
WED_AM_COLS = {18, 32, 46, 60}

# Weekend columns (Sat/Sun)
WEEKEND_COLS = {10, 11, 12, 13, 24, 25, 26, 27, 38, 39, 40, 41, 52, 53, 54, 55}

# Monday PM columns (HLC eligible)
MONDAY_PM_COLS = {15, 29, 43, 57}

# Thursday PM columns (CLC on weeks 2 and 4)
THURSDAY_PM_COLS = {7, 21, 35, 49}  # Week 1, 2, 3, 4
CLC_COLS = {21, 49}  # 2nd and 4th Thursday only

# Mid-block transition starts at col 28
MID_BLOCK_COL = 28

# Last Wednesday
LAST_WED_AM = 60
LAST_WED_PM = 61
```

---

## Universal Rules (Apply to ALL Residents)

### Rule 1: Wednesday PM = LEC

**ALL residents** get LEC on Wednesday PM, EXCEPT those on exempt rotations.

```python
LEC_EXEMPT_ROTATIONS = {
    'NF', 'NF-PM', 'NF-ENDO',      # Night float (working nights)
    'NEURO-NF',                     # NEURO transitioning to NF
    'PedNF', 'PNF',                 # Peds night float
    'LDNF',                         # L&D night float
    'Hilo', 'TDY',                  # Off-island (not present)
    'FMIT', 'FMIT 2',               # Inpatient (24/7 coverage)
}

def get_wed_pm(rotation: str) -> str:
    if rotation in LEC_EXEMPT_ROTATIONS:
        return None  # Keep rotation pattern
    return 'LEC'
```

### Rule 2: Last Wednesday Special (Col 60-61)

**Final Wednesday of block has different rules:**

| Slot | Code | Notes |
|------|------|-------|
| AM (col 60) | LEC | Lecture - NOT clinic |
| PM (col 61) | ADV | Advising |

**Common Error:** Scheduling morning clinic on last Wednesday. This is WRONG.

```python
def is_last_wednesday(col: int) -> bool:
    return col in {60, 61}

def get_last_wed_assignment(col: int) -> str:
    if col == 60:
        return 'LEC'  # AM
    elif col == 61:
        return 'ADV'  # PM
```

---

## Intern Rules (PGY-1 Only)

### Rule 3: Wednesday AM Continuity Clinic

**PGY-1 interns** get continuity clinic (C) on Wednesday AM, EXCEPT those on exempt rotations.

```python
CONTINUITY_EXEMPT_ROTATIONS = {
    'NF', 'NF-PM', 'NF-ENDO',      # Night float
    'NEURO-NF',                     # Mid-block to NF
    'PedNF', 'PNF',                 # Peds night float
    'LDNF',                         # L&D night float
    'Hilo', 'TDY',                  # Off-island
    'KAP', 'Kapiolani L and D',     # Off-site (has own Wed AM rule!)
    'OB', 'OB-CL',                  # OB rotation
    'FMIT', 'FMIT 2',               # Inpatient
}

def get_intern_wed_am(rotation: str, block_number: int) -> str:
    """Get Wednesday AM assignment for PGY-1 intern."""
    if rotation in CONTINUITY_EXEMPT_ROTATIONS:
        return None  # Use rotation-specific pattern instead

    # Continuity clinic code based on experience level
    if block_number <= 6:
        return 'C60'  # 60-min appointments (new intern)
    elif block_number <= 13:
        return 'C40'  # 40-min appointments (experienced)
    else:
        return 'C'    # Standard
```

**Note:** Kapiolani is NOT exempt - it has its OWN Wed AM clinic rule (see below).

### Rule 4: Intern Clinic Caps

| Level | Clinic Half-Days/Week | Notes |
|-------|----------------------|-------|
| PGY-1 | 1 (ideally) | Protected for learning |

### Rule 5: Intern Flex Time

PGY-1 requires **2 half-days FLX** per week.

---

## Rotation-Specific Patterns

### Standard Rotation Patterns

```python
# (AM_code, PM_code) - DEFAULT patterns
# Special days (Wed AM/PM, Last Wed) override these
ROTATION_PATTERNS = {
    # Clinic-based rotations
    'FMC':        ('C', 'C'),       # Family Medicine Clinic
    'PROC':       ('PR', 'C'),      # Procedures AM, Clinic PM
    'SM':         ('SM', 'C'),      # Sports Med AM, Clinic PM
    'POCUS':      ('US', 'C'),      # Ultrasound AM, Clinic PM
    'Gyn Clinic': ('GYN', 'C'),     # Gyn AM, Clinic PM
    'Surg Exp':   ('SURG', 'C'),    # Surgery AM, Clinic PM

    # Ward rotations (24/7)
    'IM':         ('IM', 'IM'),     # Internal Medicine ward
    'Peds Ward':  ('PedW', 'PedW'), # Peds inpatient
    'FMIT':       ('FMIT', 'FMIT'), # FM Inpatient Team
    'FMIT 2':     ('FMIT', 'FMIT'), # FM Inpatient Team 2

    # Night float patterns
    'NF':         ('OFF', 'NF'),    # FM Night Float
    'PedNF':      ('OFF', 'PedNF'), # Peds Night Float
    'Peds NF':    ('OFF', 'PedNF'), # Peds Night Float (alt name)

    # Electives
    'NEURO':      ('NEURO', 'C'),   # Neurology + Clinic
    'ENDO':       ('ENDO', 'C'),    # Endocrine + Clinic
    'Derm':       ('DERM', 'C'),    # Dermatology + Clinic
    'VA':         ('VA', 'VA'),     # VA rotation

    # Off-site
    'Hilo':       ('TDY', 'TDY'),   # Off-island TDY
}
```

---

## Special Rotation Schedules

### Kapiolani L&D (Intern - PGY-1)

**Off-site rotation at Kapiolani Medical Center.**

| Day | AM | PM |
|-----|----|----|
| Mon | KAP | **OFF** |
| Tue | **OFF** | **OFF** |
| Wed | **C** | LEC |
| Thu | KAP | KAP |
| Fri | KAP | KAP |
| Sat | KAP | KAP |
| Sun | KAP | KAP |

```python
def get_kapiolani_assignment(day_of_week: int, is_am: bool) -> str:
    """
    day_of_week: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
    """
    if day_of_week == 0:  # Monday
        return 'KAP' if is_am else 'OFF'
    elif day_of_week == 1:  # Tuesday
        return 'OFF'  # Both AM and PM
    elif day_of_week == 2:  # Wednesday
        return 'C' if is_am else 'LEC'  # Continuity clinic AM!
    else:  # Thu-Sun
        return 'KAP'
```

**Key Points:**
- Wednesday AM is **C** (continuity), NOT KAP
- Mon PM through Tue is OFF (recovery)
- Thu-Sun = 4 shifts at Kapiolani

---

### L&D Night Float (R2 - PGY-2)

**TAMC Labor & Delivery night shift rotation.**

| Day | AM | PM |
|-----|----|----|
| Mon | OFF | LDNF |
| Tue | OFF | LDNF |
| Wed | OFF | LDNF |
| Thu | OFF | LDNF |
| Fri | **C** | OFF |
| Sat | W | W |
| Sun | W | W |

```python
def get_ldnf_assignment(day_of_week: int, is_am: bool) -> str:
    """L&D Night Float pattern for R2."""
    if day_of_week == 4:  # Friday
        return 'C' if is_am else 'OFF'  # Friday MORNING clinic!
    elif day_of_week in (5, 6):  # Weekend
        return 'W'
    else:  # Mon-Thu
        return 'OFF' if is_am else 'LDNF'
```

**CRITICAL:** Friday **morning** clinic, NOT Wednesday! This is different from all other rotations.

---

### FM Night Float (NF)

**Night float timing was CORRECTED per transcript:**

| Component | Value |
|-----------|-------|
| Starts | Thursday |
| Ends | Wednesday (following week) |
| Post-call | Thursday after |
| Oncoming clinic | Thursday PM = C-N |

```python
def get_nf_assignment(day_of_block: int, is_am: bool, is_oncoming_week: bool) -> str:
    """
    FM Night Float pattern.
    day_of_block: 0 = first day of NF assignment
    """
    # Oncoming Thursday PM = C-N
    if day_of_block == 0 and not is_am:
        return 'C-N'  # Oncoming clinic

    # During NF: OFF mornings, NF afternoons/nights
    return 'OFF' if is_am else 'NF'
```

**C-N Code:** Used Thursday PM when oncoming to night float. Marcy uses this as cue to drop C30s.

---

### Hilo / Okinawa TDY (Off-Island)

**Pre-departure (Week 1):**
- Thu (col 6-7): C / C
- Fri (col 8-9): C / C
- Weekend: Travel

**During Hilo/Okinawa (Weeks 2-4):**
- All slots: TDY

**Return (Week 4):**
- 4th Tuesday (col 44-45): C / C (return clinic)

```python
def get_hilo_assignment(col: int, block_start_col: int = 6) -> str:
    """Hilo/Okinawa TDY pattern."""
    # First Thu/Fri = clinic before leaving
    if col in {6, 7, 8, 9}:
        return 'C'

    # Return Tuesday (4th Tuesday)
    if col in {44, 45}:
        return 'C'

    # Everything else = TDY (off-island)
    return 'TDY'
```

---

### Peds Ward / Peds NF Mid-Block Transition

Some residents switch rotations mid-block at column 28:

| Resident | First Half (col 6-27) | Second Half (col 28-61) |
|----------|----------------------|------------------------|
| Resident A | Peds Ward | Peds NF |
| Resident B | Peds NF | Peds Ward |

```python
def get_rotation_for_column(
    col: int,
    primary_rotation: str,
    secondary_rotation: str = None
) -> str:
    """Get active rotation based on column position."""
    MID_BLOCK_COL = 28

    if secondary_rotation and col >= MID_BLOCK_COL:
        return secondary_rotation
    return primary_rotation
```

---

### NEURO → NF Mid-Block Transition

Example (PGY-3): NEURO first half, then NF second half:

| Period | Pattern |
|--------|---------|
| Col 6-27 (NEURO) | NEURO / C (AM/PM) |
| Col 28+ (NF) | OFF / NF (AM/PM) |

---

## Senior Resident Rules (PGY-2/3)

### Wednesday AM by Rotation

Senior residents do NOT get automatic continuity clinic. Their Wed AM depends on rotation:

| Rotation | Wed AM Code |
|----------|------------|
| FMC (R3) | ADM |
| FMC (R2) | FLX |
| Procedures | SIM |
| Sports Med | aSM |
| Other | Per rotation pattern |

### Clinic Caps

| Level | Clinic Half-Days/Week |
|-------|----------------------|
| PGY-2 | 2-3 (max 3) |
| PGY-3 | 3-4 |

**R2 on Sports Med:** Maximum **3** clinics (not 4).

### Flex Time

| Level | FLX Half-Days/Week |
|-------|-------------------|
| PGY-2 | 1 |
| PGY-3 (FMC) | At least 1 |

---

## Special Clinics

### HLC (Houseless Clinic)

| Attribute | Value |
|-----------|-------|
| Day | Monday PM |
| Eligible | R2 and R3 only |
| Frequency | Every Monday |
| Staffing | One resident per slot |

```python
MONDAY_PM_COLS = {15, 29, 43, 57}

def should_assign_hlc(col: int, pgy_level: int) -> bool:
    return col in MONDAY_PM_COLS and pgy_level >= 2
```

### CLC (Continuity Learning Curriculum)

| Attribute | Value |
|-----------|-------|
| Day | Thursday PM |
| Weeks | 2nd and 4th (NOT back-to-back) |
| NOT on | 1st Thursday (beginning of block issues) |

```python
# Week 2 = col 21, Week 4 = col 49
CLC_COLS = {21, 49}

def should_assign_clc(col: int) -> bool:
    return col in CLC_COLS
```

---

## IM Rotation Exception

**Special Rule for Internal Medicine:**

The final Wednesday of IM rotation gets **Tuesday PM** clinic instead.

**Reason:** Preserves 4 weeks of continuity (otherwise only 3 weeks due to "inverted day" logic where Thursday starts new scheduling week).

```python
def apply_im_last_week_exception(resident, last_tue_pm_col: int):
    """
    IM residents get Tue PM clinic instead of Wed.
    Last Wed still follows Last Wednesday rules (LEC/ADV).
    """
    # Move clinic to Tue PM
    set_assignment(resident, last_tue_pm_col, 'C')

    # Last Wed = LEC/ADV per Rule 2
    set_assignment(resident, LAST_WED_AM, 'LEC')
    set_assignment(resident, LAST_WED_PM, 'ADV')
```

---

## Weekend Handling

### Weekend Columns

Weekends use 'W' code for residents with weekend off:

```python
WEEKEND_COLS = {
    10, 11,   # Sat Mar 14
    12, 13,   # Sun Mar 15
    24, 25,   # Sat Mar 21
    26, 27,   # Sun Mar 22
    38, 39,   # Sat Mar 28
    40, 41,   # Sun Mar 29
    52, 53,   # Sat Apr 4
    54, 55,   # Sun Apr 5
}

def is_weekend(col: int) -> bool:
    return col in WEEKEND_COLS
```

### Rotations That Work Weekends

These rotations do NOT get 'W' on weekends:

```python
WORKS_WEEKENDS = {
    'FMIT', 'FMIT 2',     # Inpatient coverage
    'Peds Ward', 'PedW',   # Peds inpatient
    'IM',                  # Internal medicine ward
    'NF', 'PedNF', 'LDNF', # Night float
    'KAP',                 # Kapiolani L&D
    'Hilo', 'TDY',         # Off-island
}
```

---

## Pre-Blocked Codes (Never Overwrite)

These codes indicate protected time and should NEVER be overwritten:

```python
PREBLOCKED_CODES = {
    'W',       # Weekend off
    'LV',      # Leave
    'LEC',     # Lecture (Wed PM)
    'ADV',     # Advising (Last Wed PM)
    'USAFP',   # Conference
    'DEP',     # Deployed
    'DO',      # Day off (post-call PM)
    'PCAT',    # Post-call (AM)
    'PC',      # Post-call (general)
    'MedsTo',  # MedsTo orientation
    'Orient',  # Orientation
}
```

---

## Validation Checklist

After expansion, verify:

- [ ] All Wednesday PM slots show LEC (except exempt rotations)
- [ ] All PGY-1 Wednesday AM slots show C/C40/C60 (except exempt rotations)
- [ ] Kapiolani intern has: Mon AM=KAP, Mon PM=OFF, Tue=OFF/OFF, Wed AM=C
- [ ] L&D NF (R2) has: Fri AM=C, Mon-Thu AM=OFF, Mon-Thu PM=LDNF
- [ ] Mid-block transitions occur at column 28
- [ ] Last Wednesday shows AM=LEC, PM=ADV
- [ ] IM residents have Tuesday PM clinic in final week
- [ ] Weekend columns show W for non-24/7 rotations
- [ ] Pre-blocked codes not overwritten
- [ ] Night float starts Thursday, ends Wednesday
- [ ] C-N used for oncoming night float (Thursday PM)

---

## Complete Pattern Application Function

```python
def get_assignment(
    rotation: str,
    col: int,
    pgy_level: int,
    block_number: int,
    secondary_rotation: str = None
) -> str:
    """
    Get the correct assignment for a resident at a specific column.

    Priority order:
    1. Pre-blocked (return None to skip)
    2. Last Wednesday rules
    3. Wednesday PM LEC
    4. Rotation-specific patterns (Kapiolani, LDNF, etc.)
    5. Wednesday AM intern continuity
    6. Weekend handling
    7. Mid-block transition
    8. Default rotation pattern
    """
    is_am = (col % 2 == 0)

    # Determine active rotation (mid-block transition)
    active_rotation = rotation
    if secondary_rotation and col >= MID_BLOCK_COL:
        active_rotation = secondary_rotation

    # 1. Last Wednesday (col 60-61)
    if col == LAST_WED_AM:
        return 'LEC'
    if col == LAST_WED_PM:
        return 'ADV'

    # 2. Wednesday PM = LEC (except exempt)
    if col in LEC_COLS and active_rotation not in LEC_EXEMPT_ROTATIONS:
        return 'LEC'

    # 3. Rotation-specific patterns
    if active_rotation in ('KAP', 'Kapiolani L and D'):
        return get_kapiolani_assignment(col_to_dow(col), is_am)

    if active_rotation in ('LDNF', 'L and D night float'):
        return get_ldnf_assignment(col_to_dow(col), is_am)

    if active_rotation == 'Hilo':
        return get_hilo_assignment(col)

    # 4. Wednesday AM intern continuity
    if col in WED_AM_COLS and pgy_level == 1:
        continuity = get_intern_wed_am(active_rotation, block_number)
        if continuity:
            return continuity

    # 5. Weekend handling
    if is_weekend(col) and active_rotation not in WORKS_WEEKENDS:
        return 'W'

    # 6. Default rotation pattern
    pattern = ROTATION_PATTERNS.get(active_rotation, (active_rotation, active_rotation))
    return pattern[0] if is_am else pattern[1]
```

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-14 | Initial version from transcript analysis and SKILL.md refinement |
