# Residency Scheduling Domain Model

## Core Concepts

### Rotation vs Activity vs Absence

**Rotation** = Multi-week block assignment (28 days = 4 weeks)
- Examples: Neurology Elective, FMIT Inpatient, PGY-1 Clinic
- Stored in `rotation_templates` table
- Residents are assigned to rotations via `block_assignments`
- A rotation CONTAINS multiple activities within its 56 half-day slots

**Activity** = Slot-level event that fills half-day slots
- Examples: FM Clinic AM, Specialty PM, LEC Wednesday PM
- Stored in `activities` table
- Activities are the building blocks within weekly patterns
- Some activities are PROTECTED (locked) - solver cannot move them
- Some are solver-fillable based on requirements

**Absence** = Time away from program (exception to normal schedule)
- Examples: Vacation, Deployment, TDY, Medical Leave
- Stored in `absences` table
- Counts toward 28-day away-from-program limit per academic year
- NOT the same as "day off" (which is ACGME-protected rest)

### Key Distinction
- Day Off (`off` activity, `time_off` category) = ACGME-protected rest, does NOT count toward away limit
- Absence = Away from program, DOES count toward 28-day extension threshold

---

## Weekly Pattern Structure

### Grid Layout
```
         | Sun | Mon | Tue | Wed | Thu | Fri | Sat |
    AM   |  0  |  1  |  2  |  3  |  4  |  5  |  6  |
    PM   |  0  |  1  |  2  |  3  |  4  |  5  |  6  |
```

- 7 days x 2 time periods = 14 slots per week
- 4 weeks per block = 56 total half-day slots per rotation

### Week-Specific Patterns
- `week_number = NULL` → Same pattern all 4 weeks
- `week_number = 1,2,3,4` → Week-specific patterns
- Example: LEC Wednesday PM weeks 1-3, Advising PM week 4

### Protected Slots
- `is_protected = true` → Solver cannot modify
- Typical protected: Wednesday PM Lecture (LEC)
- Solver fills remaining slots based on requirements

---

## Activity Categories

| Category | Examples | Supervision | Clinical Hours |
|----------|----------|-------------|----------------|
| clinical | FM Clinic, Specialty, Inpatient, Call | Yes | Yes |
| educational | Lecture (LEC), Conference | No | No |
| time_off | Day Off, Recovery | No | No |
| administrative | Admin duties | No | No |

---

## Half-Day Requirements (Soft Constraints)

### Standard Block Distribution (10 half-days/week target)
- FM Clinic: 4 half-days (40%)
- Specialty: 5 half-days (50%)
- Academics/LEC: 1 half-day (10%, protected)
- Elective: 0 (buffer)

### Soft Constraint Fields
```python
RotationActivityRequirement:
  min_halfdays      # Hard floor
  max_halfdays      # Hard ceiling
  target_halfdays   # Preferred (soft optimization)
  priority          # 0-100 (higher = more important)
  prefer_full_days  # AM+PM together for same activity
  preferred_days    # [1,2,3,4,5] for Mon-Fri
  avoid_days        # [0,6] for weekends
  applicable_weeks  # [1,2,3] or null for all
```

### Priority Levels
- 0-30: Low (nice to have)
- 31-60: Medium (should satisfy)
- 61-90: High (strong preference)
- 91-100: Critical (near-hard constraint, e.g., protected LEC)

---

## ACGME Compliance Considerations

### Work Hour Limits
- 80 hours/week averaged over 4 weeks
- 1 day off per 7 days (protected)
- 24+4 hour shifts max (24 duty + 4 transition)

### Supervision Requirements
- PGY-1: Direct supervision required
- PGY-2+: May have indirect supervision
- `supervision_required` and `max_supervision_ratio` on rotation templates

### Away From Program
- 28-day limit per academic year
- Exceeding requires training extension
- Tracked via `is_away_from_program` on absences

---

## Template Categories

| Category | Activity Types | Away Tracking |
|----------|----------------|---------------|
| rotation | clinic, inpatient, procedure | No |
| time_off | off, recovery | No |
| absence | absence | Yes (counts toward 28 days) |
| educational | conference, lecture | No |

---

## Scheduling Workflow

1. **Block Assignment** - Assign resident to rotation for 28-day block
2. **Weekly Pattern** - Define 14-slot grid with activities
3. **Activity Requirements** - Set half-day distribution (FM 4, Specialty 5, etc.)
4. **Protected Slots** - Lock mandatory activities (LEC Wednesday)
5. **Solver Fills** - Optimizer fills remaining slots per requirements
6. **Swaps/Overrides** - Manual adjustments for edge cases

---

## Database Schema Summary

```
rotation_templates (Rotations)
  ├── weekly_patterns (7x2 grid per week)
  │     └── activity_id → activities
  ├── activity_requirements (soft constraints)
  │     └── activity_id → activities
  └── block_assignments (resident assignments)

activities (Slot-level events)
  - FM Clinic, Specialty, LEC, OFF, etc.
  - is_protected for locked slots

absences (Time away)
  - is_away_from_program for 28-day tracking
```

---

## Common Patterns

### Outpatient Rotation (e.g., Neurology Elective)
- Weekends: OFF (includes_weekend_work = false)
- Wednesday PM: LEC (protected)
- Mon-Fri: Mix of FM Clinic (4) + Specialty (5)

### Inpatient Rotation (e.g., FMIT)
- Weekends: Working (includes_weekend_work = true)
- 24/7 coverage requirement
- leave_eligible = false

### Night Float
- Nights only (special scheduling)
- Weekend work required
- Recovery days after shift sequence
