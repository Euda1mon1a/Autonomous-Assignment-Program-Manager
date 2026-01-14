# Expansion Service Fixes - Code Analysis & Corrections

**Date:** 2026-01-14
**Author:** Cowork (domain expert)
**Purpose:** Detailed fixes for `block_assignment_expansion_service.py`

---

## Summary

After comparing `Block10_OUTPUT.xlsx` against `Block10_ROSETTA_CORRECT.xlsx`, the expansion service has **5 critical bugs**. The tests in `backend/tests/scheduling/test_expansion_vs_rosetta.py` will FAIL until these are fixed.

---

## Bug #1: KAP Pattern Missing

**Current behavior:** Travis gets `KAP` everywhere
**Expected:** Mon PM=OFF, Tue=OFF/OFF, Wed AM=C, Wed PM=LEC, Thu-Sun=KAP

### Root Cause

The `NIGHT_FLOAT_PATTERNS` dict includes `KAPI-LD` but maps it to `("KAP", "KAP")` for both AM/PM. This misses the complex KAP pattern.

### Fix Location

`block_assignment_expansion_service.py` lines 44-51

### Current Code (line ~50)
```python
NIGHT_FLOAT_PATTERNS: dict[str, tuple[str, str]] = {
    ...
    "KAPI-LD": ("KAP", "KAP"),  # Kapiolani L&D (off-site, both slots)
}
```

### Required Fix

**Remove KAP from NIGHT_FLOAT_PATTERNS** and add a dedicated function:

```python
# Remove this line from NIGHT_FLOAT_PATTERNS:
# "KAPI-LD": ("KAP", "KAP"),

# Add new constants at top of file:
KAPIOLANI_ROTATIONS = frozenset(["KAP", "KAPI-LD", "Kapiolani L and D"])

# Add new method to class:
def _get_kapiolani_assignment(
    self,
    current_date: date,
    time_of_day: str,
    is_last_wed: bool,
) -> str:
    """
    Kapiolani L&D pattern - off-site rotation.

    Pattern:
    - Mon: KAP / OFF (travel back from Kapiolani)
    - Tue: OFF / OFF (recovery day)
    - Wed: C / LEC (continuity clinic + lecture)
    - Thu-Sun: KAP / KAP (on-site at Kapiolani)

    Last Wednesday overrides: LEC / ADV
    """
    dow = current_date.isoweekday()  # 1=Mon, 2=Tue, 3=Wed, ...
    is_am = time_of_day == "AM"

    # Last Wednesday rule takes priority
    if is_last_wed:
        return "LEC" if is_am else "ADV"

    if dow == 1:  # Monday
        return "KAP" if is_am else "OFF"
    elif dow == 2:  # Tuesday
        return "OFF"  # Both AM and PM
    elif dow == 3:  # Wednesday
        return "C" if is_am else "LEC"
    else:  # Thu-Sun (4, 5, 6, 7)
        return "KAP"
```

### Integration Point

In `_expand_single_block_assignment()`, add check BEFORE the AM/PM slot assignment sections (~line 502):

```python
# Check for Kapiolani rotation FIRST
if rotation.abbreviation in KAPIOLANI_ROTATIONS:
    is_last_wed = self._is_last_wednesday_of_block(current_date, end_date)

    # AM slot
    if am_activity:
        kap_code = self._get_kapiolani_assignment(current_date, "AM", is_last_wed)
        kap_template = self._get_absence_template(kap_code) or rotation
        # ... create assignment with kap_template.id

    # PM slot
    if pm_activity:
        kap_code = self._get_kapiolani_assignment(current_date, "PM", is_last_wed)
        kap_template = self._get_absence_template(kap_code) or rotation
        # ... create assignment with kap_template.id

    continue  # Skip default processing
```

---

## Bug #2: LDNF Pattern Wrong

**Current behavior:** Headid gets `L&D` everywhere
**Expected:** Mon-Thu=OFF/LDNF, Fri=C/OFF, Sat-Sun=W/W

### Root Cause

Line 49 has wrong mapping:
```python
"LDNF": ("L&D", "L&D"),  # L&D Night Float works both (24hr coverage)
```

This is **WRONG**. LDNF is Night Float, not 24hr coverage.

### Fix

```python
# Change from:
"LDNF": ("L&D", "L&D"),

# Change to - remove from NIGHT_FLOAT_PATTERNS entirely and add dedicated function:
LDNF_ROTATIONS = frozenset(["LDNF", "L and D night float"])

def _get_ldnf_assignment(
    self,
    current_date: date,
    time_of_day: str,
    is_last_wed: bool,
) -> str:
    """
    L&D Night Float pattern.

    CRITICAL: Friday MORNING clinic (not Wednesday!)

    Pattern:
    - Mon-Thu: OFF / LDNF (sleeping days, working nights)
    - Fri: C / OFF (Friday AM clinic!)
    - Sat-Sun: W / W (weekend off)

    Last Wednesday overrides: LEC / ADV
    """
    dow = current_date.isoweekday()  # 1=Mon, 2=Tue, 3=Wed, 4=Thu, 5=Fri, 6=Sat, 7=Sun
    is_am = time_of_day == "AM"

    # Last Wednesday rule takes priority
    if is_last_wed:
        return "LEC" if is_am else "ADV"

    if dow == 5:  # Friday
        return "C" if is_am else "OFF"  # FRIDAY clinic!
    elif dow in (6, 7):  # Weekend
        return "W"
    else:  # Mon-Thu
        return "OFF" if is_am else "LDNF"
```

---

## Bug #3: Intern Continuity Only for KAP

**Current behavior:** Only Travis (KAP) gets Wed AM = C
**Expected:** ALL PGY-1 interns get C on Wed AM (except exempt rotations)

### Root Cause

The `_should_apply_intern_continuity()` method exists but the **rotation abbreviations don't match**.

Looking at line 323:
```python
if rotation.abbreviation in INTERN_CONTINUITY_EXEMPT:
    return False
```

The `INTERN_CONTINUITY_EXEMPT` set (line 68-70) contains:
```python
INTERN_CONTINUITY_EXEMPT = frozenset([
    "NF", "PNF", "LDNF", "FMIT", "TDY", "HILO", "KAPI-LD", "PedNF", "Peds NF",
])
```

But the rotation templates in the database use different abbreviations like:
- `PROC`, `PR-AM` for Procedures
- `IM-INT` for Internal Medicine
- `PEDS-W` for Peds Ward

**These are NOT in the exempt list, so they SHOULD get C on Wed AM.**

### Fix

The check at line 520-527 is correct, but the clinic template lookup may be failing.

Check that `CLINIC_TEMPLATE_ABBREV = "C"` matches a rotation template in the database with `abbreviation = "C"`.

Debug with:
```python
clinic_template = self._get_absence_template(CLINIC_TEMPLATE_ABBREV)
if clinic_template:
    logger.info(f"Found clinic template: {clinic_template.id}")
else:
    logger.error(f"MISSING clinic template for abbrev '{CLINIC_TEMPLATE_ABBREV}'")
```

If no template found, the code falls through to default rotation.

---

## Bug #4: Last Wednesday Not Fully Applied

**Current behavior:** Some residents have rotation codes on Last Wed
**Expected:** ALL residents have LEC/ADV on Apr 8

### Root Cause

The `_get_absence_template()` method returns `None` if template not found, and the code silently falls through:

```python
# Line 513-516
if self._is_last_wednesday_of_block(current_date, end_date):
    lec_template = self._get_absence_template("LEC")
    if lec_template:  # <-- If None, falls through!
        am_template_id = lec_template.id
```

### Fix

Add error logging and ensure templates exist:

```python
if self._is_last_wednesday_of_block(current_date, end_date):
    lec_template = self._get_absence_template("LEC")
    if lec_template:
        am_template_id = lec_template.id
    else:
        logger.error("CRITICAL: Missing 'LEC' rotation template for Last Wednesday!")
        # Still force LEC somehow - maybe create inline
```

Also ensure `_preload_absence_templates()` includes both `"LEC"` and `"LEC-PM"`:

```python
# Line 231 - Add "LEC" if missing
"LEC-PM",  # Protected lecture time (Wednesday PM)
"LEC",  # Last Wednesday AM (all residents attend)  <- Ensure this exists!
```

---

## Bug #5: Mid-Block Transitions Not Visible in Output

**Current behavior:** Unknown if transitions apply (You, Wilhelm, Byrnes)
**Expected:** Pattern changes at day 14 (Mar 23)

### Root Cause

The `_get_active_rotation()` method (line 247-263) looks correct:

```python
def _get_active_rotation(
    self,
    block_assignment: BlockAssignment,
    day_index: int,
) -> RotationTemplate | None:
    if (
        block_assignment.secondary_rotation_template_id
        and day_index >= MID_BLOCK_DAY
    ):
        return block_assignment.secondary_rotation_template
    return block_assignment.rotation_template
```

But need to verify:
1. `MID_BLOCK_DAY = 14` is correct
2. `secondary_rotation_template_id` is populated for transitioning residents
3. The relationships are properly loaded (line 165-166)

### Debug

Add logging:
```python
rotation = self._get_active_rotation(block_assignment, day_index)
if day_index == 14 and block_assignment.secondary_rotation_template_id:
    logger.info(
        f"MID-BLOCK TRANSITION for {block_assignment.resident_id}: "
        f"day {day_index}, switching to {rotation.abbreviation if rotation else 'None'}"
    )
```

---

## Required Database Templates

Ensure these rotation templates exist with these exact abbreviations:

| Abbreviation | Name | Template Category |
|--------------|------|-------------------|
| `C` | Clinic | rotation |
| `LEC` | Lecture (Last Wed AM) | educational |
| `LEC-PM` | Lecture (Wed PM) | educational |
| `ADV` | Advising | educational |
| `OFF` | Day Off | time_off |
| `OFF-AM` | Day Off AM | time_off |
| `W` | Weekend | time_off |
| `W-AM` | Weekend AM | time_off |
| `W-PM` | Weekend PM | time_off |
| `KAP` | Kapiolani | rotation |
| `LDNF` | L&D Night Float | rotation |
| `NF` | Night Float | rotation |
| `PedNF` | Peds Night Float | rotation |

---

## Test Commands

After fixes, run:

```bash
# From backend directory
cd backend

# Run ROSETTA comparison tests
pytest tests/scheduling/test_expansion_vs_rosetta.py -v

# Expected: All tests should PASS
```

Current state: ~24 tests failing due to the above bugs.

---

## Priority Order for Fixes

1. **Database templates** - Ensure all required templates exist
2. **Last Wednesday** - Highest priority override
3. **LDNF pattern** - Fix the Friday clinic rule
4. **KAP pattern** - Add dedicated function
5. **Intern continuity** - Debug template lookup
6. **Mid-block transitions** - Verify data and logic
