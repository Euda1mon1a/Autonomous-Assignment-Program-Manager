# Academic Calendar Architecture: The Foundational Gap

> **Created:** 2025-12-25
> **Origin:** Recovered insight from crashed IDE session
> **Status:** DESIGN DOCUMENT - Pending implementation by local Claude Code
> **Priority:** CRITICAL - Supersedes Block 10 work

---

## The Core Insight

**Academic calendar != Gregorian calendar**

The scheduling system has a fundamental architectural conflict:

| System | Calendar Type | Structure |
|--------|---------------|-----------|
| Frontend | Gregorian | 12 months, 28-31 days each |
| User mental model | Gregorian | "March schedule", "April schedule" |
| Backend scheduler | Academic blocks | 13 blocks × 28 days |
| FMIT faculty | Neither | Friday-Thursday weeks |

This causes **every block boundary to be a potential failure point**.

---

## The Problem Visualized

```
GREGORIAN (What users see):
│ Jan │ Feb │ Mar │ Apr │ May │ Jun │ Jul │ Aug │ Sep │ Oct │ Nov │ Dec │
│ 31  │ 28  │ 31  │ 30  │ 31  │ 30  │ 31  │ 31  │ 30  │ 31  │ 30  │ 31  │

ACADEMIC BLOCKS (What the scheduler uses):
│ B1  │ B2  │ B3  │ B4  │ B5  │ B6  │ B7  │ B8  │ B9  │ B10 │ B11 │ B12 │B13│
│ 28  │ 28  │ 28  │ 28  │ 28  │ 28  │ 28  │ 28  │ 28  │ 28  │ 28  │ 28  │28 │
└─Jul 1                                                          Jun 30─┘

FMIT WEEKS (Faculty exception):
│ Fri─Thu │ Fri─Thu │ Fri─Thu │ ... │ (52 weeks, independent of both)
```

### Block Boundary Conflicts

| Block | Academic Dates | Gregorian Months Crossed |
|-------|---------------|-------------------------|
| Block 2 | Jul 29 - Aug 25 | July AND August |
| Block 3 | Aug 26 - Sep 22 | August AND September |
| Block 10 | Mar 10 - Apr 6 | March AND April |
| Block 13 | Jun 3 - Jun 30 | June (partial) |

---

## The Missing Model: ResidentBlockRotation

### Current State

```
Assignment → Block (date + AM/PM)
          → RotationTemplate
          → Person

Problem: No way to say "Resident X is on Rotation Y for Block 10"
```

### Required State

```
ResidentBlockRotation → Person (resident)
                      → RotationTemplate
                      → block_number (1-13)
                      → academic_year ("2025-2026")
                      → block_half (1 or 2, for NF/NICU)

Assignment → ResidentBlockRotation (optional FK)
          → Block (specific half-day)
          → activity details
```

---

## Schema Design

### New Model: ResidentBlockRotation

```python
class ResidentBlockRotation(Base):
    """Links a resident to a rotation for a specific block."""

    __tablename__ = "resident_block_rotations"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Core relationship
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"))
    rotation_template_id: Mapped[int] = mapped_column(ForeignKey("rotation_templates.id"))

    # Academic calendar position
    block_number: Mapped[int] = mapped_column()  # 1-13
    academic_year: Mapped[str] = mapped_column(String(9))  # "2025-2026"

    # For half-block rotations (NF, NICU)
    block_half: Mapped[Optional[int]] = mapped_column(nullable=True)  # 1 or 2

    # Metadata
    assigned_by: Mapped[str] = mapped_column(String(50))  # "scheduler", "manual", "swap"
    assigned_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    person: Mapped["Person"] = relationship(back_populates="block_rotations")
    rotation_template: Mapped["RotationTemplate"] = relationship()
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="block_rotation")

    __table_args__ = (
        UniqueConstraint(
            "person_id", "block_number", "academic_year", "block_half",
            name="uq_person_block_year_half"
        ),
        CheckConstraint("block_number >= 1 AND block_number <= 13", name="ck_block_number"),
        CheckConstraint("block_half IS NULL OR block_half IN (1, 2)", name="ck_block_half"),
    )
```

### Enhanced RotationTemplate

```python
class CalendarMode(str, Enum):
    """How a rotation's time boundaries are calculated."""
    ACADEMIC_BLOCK = "academic_block"    # Standard 28-day blocks
    BLOCK_HALF = "block_half"            # 14-day halves (NF, NICU)
    FMIT_WEEK = "fmit_week"              # Friday-Thursday weeks
    GREGORIAN_MONTH = "gregorian_month"  # For reporting/admin only
    DAILY = "daily"                      # Individual day assignments

# Add to RotationTemplate model:
class RotationTemplate(Base):
    # Existing fields...

    # NEW FIELDS
    calendar_mode: Mapped[str] = mapped_column(
        String(20),
        default=CalendarMode.ACADEMIC_BLOCK
    )
    is_block_half_rotation: Mapped[bool] = mapped_column(default=False)
    is_solver_eligible: Mapped[bool] = mapped_column(default=True)
    week_structure: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )  # "FRIDAY_THURSDAY" for FMIT
```

---

## FMIT Calendar Exception Explained

FMIT (Family Medicine Inpatient Team) faculty operate on a **different calendar**:

| Aspect | Residents | FMIT Faculty |
|--------|-----------|--------------|
| Week structure | Mon-Sun | **Fri-Thu** |
| Rotation unit | 28-day blocks | 7-day weeks |
| Block alignment | Aligned | **Independent** |

### Current Hardcoding (fmit.py:45-67)

```python
def get_fmit_week_dates(any_date: date) -> tuple[date, date]:
    """FMIT weeks run Friday-Thursday, NOT Monday-Sunday"""
    day_of_week = any_date.weekday()
    if day_of_week >= 4:  # Fri, Sat, Sun
        days_since_friday = day_of_week - 4
    else:  # Mon, Tue, Wed, Thu
        days_since_friday = day_of_week + 3
    friday = any_date - timedelta(days=days_since_friday)
    thursday = friday + timedelta(days=6)
    return friday, thursday
```

### Proposed: Data-Driven Calendar Mode

Instead of hardcoding, the `calendar_mode` field tells the system:
- `FMIT_WEEK`: Use Friday-Thursday boundaries
- `ACADEMIC_BLOCK`: Use 28-day block boundaries
- `BLOCK_HALF`: Use 14-day half-block boundaries

---

## Hardcoding Locations to Refactor

All of these become unnecessary with proper data model:

| Location | Hardcoding | Replace With |
|----------|------------|--------------|
| `engine.py:109` | `preserve_fmit=True` | Query `is_solver_eligible=False` |
| `engine.py:858` | `_load_fmit_assignments()` | Query `ResidentBlockRotation` |
| `fmit.py:289,447,650` | `"FMIT" in name.upper()` | `calendar_mode == "fmit_week"` |
| `inpatient.py:70` | `"night" in name_lower` | `is_block_half_rotation=True` |
| `engine.py:956` | `activity_type == "clinic"` | `is_solver_eligible=True` |

---

## Two-Phase Schedule Generation

### Current (One Phase)
```
Solver → assigns half-day slots → done
```

### Required (Two Phases)

```
Phase 1: ROTATION ASSIGNMENT
══════════════════════════════
For each resident, for each block:
  → Assign to a rotation (creates ResidentBlockRotation)
  → Respects 28-day block boundaries
  → Handles block-half rotations (NF, NICU)
  → Maps FMIT weeks to blocks

Phase 2: SLOT ASSIGNMENT
══════════════════════════════
Given the rotation assignment:
  → Fill half-day activities
  → FM Clinic: 4 half-days
  → Specialty: 5 half-days
  → Academics: 1 half-day (Wed AM)
```

---

## Migration Plan

### Step 1: Add New Fields to RotationTemplate

```bash
alembic revision --autogenerate -m "Add calendar_mode and is_solver_eligible to RotationTemplate"
```

Fields to add:
- `calendar_mode` (String, default "academic_block")
- `is_solver_eligible` (Boolean, default True)
- `week_structure` (String, nullable)

Complete existing migration `9d38e1388001` for `is_block_half_rotation`.

### Step 2: Create ResidentBlockRotation Model

```bash
alembic revision --autogenerate -m "Add ResidentBlockRotation model"
```

### Step 3: Add FK to Assignment (Optional)

```bash
alembic revision --autogenerate -m "Add resident_block_rotation_id to Assignment"
```

### Step 4: Seed calendar_mode Values

```python
# In seed script or migration
ROTATION_CALENDAR_MODES = {
    "FMIT": ("fmit_week", False, "FRIDAY_THURSDAY"),
    "Night Float": ("block_half", False, None),
    "NF": ("block_half", False, None),
    "NICU": ("block_half", False, None),
    # All others default to ("academic_block", True, None)
}
```

### Step 5: Refactor Engine

Replace `preserve_fmit` pattern with:
```python
# Load block rotations, not individual assignments
block_rotations = ResidentBlockRotation.query.filter_by(
    block_number=target_block,
    academic_year=academic_year
)

for br in block_rotations:
    if br.rotation_template.is_solver_eligible:
        solver.add_to_optimization(br)
    else:
        # Skip - these are pre-assigned
        pass
```

---

## Verification Queries

After implementation, local Claude Code should verify:

```sql
-- 1. All rotation templates have calendar_mode
SELECT name, calendar_mode, is_solver_eligible
FROM rotation_templates
ORDER BY calendar_mode;

-- 2. ResidentBlockRotation populated for target block
SELECT
    p.name as resident,
    rt.abbreviation as rotation,
    rbr.block_number,
    rbr.block_half
FROM resident_block_rotations rbr
JOIN people p ON rbr.person_id = p.id
JOIN rotation_templates rt ON rbr.rotation_template_id = rt.id
WHERE rbr.block_number = 10 AND rbr.academic_year = '2025-2026';

-- 3. No hardcoded FMIT string checks remain
-- (grep codebase, not SQL)
```

---

## Why This Supersedes Block 10

Every time we fix Block 10 without this foundation:
1. The fix works for Block 10
2. Block 11 breaks (same boundary issues)
3. Or Block 9-10 transition breaks
4. Or FMIT week crossing block boundary breaks

**13 block boundaries × N rotation types × calendar exceptions = combinatorial edge cases**

Fix the model, and edge cases collapse into data.

---

## For Local Claude Code

### Before Starting
1. Read this entire document
2. Explore existing models: `backend/app/models/`
3. Check existing migration: `9d38e1388001`
4. Understand `AcademicBlockService`

### Execution Order
1. Complete `is_block_half_rotation` field on model
2. Add `calendar_mode`, `is_solver_eligible`, `week_structure`
3. Create `ResidentBlockRotation` model
4. Add FK to `Assignment` (optional, can defer)
5. Create seed data for calendar modes
6. Write tests for block rotation queries
7. Refactor engine to use new model

### Safety
- DO NOT modify existing columns
- ADD new fields/tables only
- Run against copy of production DB first
- Use `alembic downgrade -1` to test rollback

---

## Related Documents

- [Block 10 Postmortem](../development/POSTMORTEM_BLOCK10_SESSION.md)
- [Schedule Verification Template](../development/SCHEDULE_VERIFICATION_TEMPLATE.md)
- [Solver Algorithm](SOLVER_ALGORITHM.md)

---

*This document captures the insight from the crashed IDE session. It is the authoritative spec for local Claude Code to implement.*
