# Session: Custom Rotation Colors & Mid-Block Rotation Splits

**Date:** 2025-12-26
**Branch:** `claude/block0-engine-fix-commands`
**Status:** Complete - Ready for PR

---

## Overview

This session accomplished two major features:
1. **Custom Rotation Colors** - Database-driven color customization for schedule grid cells
2. **Mid-Block Rotation Splits** - Split combined rotations (NF+X) into proper half-block assignments

---

## Feature 1: Custom Rotation Colors

### Problem
Rotation templates displayed with hardcoded colors based on activity type (clinic=blue, inpatient=purple, etc.). Users wanted custom colors per rotation for better visual distinction.

### Solution
Added `font_color` and `background_color` columns to the `rotation_templates` table, with frontend rendering via inline styles.

### Implementation

#### Backend Changes

**`backend/app/models/rotation_template.py`**
```python
# Added columns
font_color = Column(String(50))      # Tailwind color class for text
background_color = Column(String(50)) # Tailwind color class for background
```

**`backend/app/schemas/rotation_template.py`**
```python
# Added to Pydantic schemas
font_color: str | None = None
background_color: str | None = None
```

#### Frontend Changes

**`frontend/src/types/api.ts`**
```typescript
export interface RotationTemplate {
  // ... existing fields
  font_color: string | null;
  background_color: string | null;
}
```

**`frontend/src/components/schedule/ScheduleCell.tsx`**
- Added Tailwind-to-hex color mapping for inline styles
- Falls back to activity-type colors when custom colors not set
- Uses inline `style` prop instead of dynamic Tailwind classes (Tailwind can't detect dynamic classes at build time)

```typescript
const tailwindToHex: Record<string, string> = {
  'black': '#000000',
  'white': '#ffffff',
  'sky-500': '#0ea5e9',
  'red-500': '#ef4444',
  'green-500': '#22c55e',
  // ... more colors
}

// Usage in component
if (assignment.fontColor && assignment.backgroundColor) {
  return {
    colorClass: 'border',
    customStyle: {
      color: tailwindToHex[assignment.fontColor] || assignment.fontColor,
      backgroundColor: tailwindToHex[assignment.backgroundColor] || assignment.backgroundColor,
    }
  }
}
```

### Database Update
Colors were applied via direct SQL update from user's revised CSV:
```sql
UPDATE rotation_templates
SET font_color = 'black', background_color = 'sky-500'
WHERE abbreviation = 'C';
-- (similar for other templates)
```

---

## Feature 2: Mid-Block Rotation Splits

### Problem
Combined rotations like "NF+DERM" (Night Float + Dermatology) switch halfway through a block. These were imported as a single template, but the scheduler needs:
1. Separate assignments for each half
2. Post-Call (PC) recovery on day 15 (mid-block transition)

### Solution
Created `split_combined_rotations.py` script to split combined assignments into proper half-block assignments.

### Naming Convention = Order
| Template Name | Days 1-14 | Days 16-28 |
|---------------|-----------|------------|
| `NF+DERM` | Night Float | Dermatology |
| `NF+FMIT` | Night Float | FMIT |
| `NF+CARD` | Night Float | Cardiology |
| `DERM+NF` | Dermatology | Night Float |

### Split Pattern
```
Original: Combined template for all 28 days
After:    NF (days 1-14) → PC (day 15) → Second rotation (days 16-28)
```

### Implementation

**`split_combined_rotations.py`**
```python
COMBINED_TEMPLATES = {
    "38d35ac5-...": ("Night Float", "Dermatology"),  # NF-DERM
    "6dd781d5-...": ("Night Float", "FMIT"),          # NF-I
    "691ad20d-...": ("Night Float", "Cardiology"),    # NF+
}

# For each combined assignment:
# 1. Delete combined assignments
# 2. Create NF assignments for days 1-14
# 3. Create PC assignments for day 15
# 4. Create second rotation assignments for days 16-28
```

### Execution Results
```
=== Summary ===
Deleted: 664 combined assignments
Created: 664 split assignments
```

### Affected Residents (Blocks 10-13)

| Resident | Block | Days 1-14 | Day 15 | Days 16-28 |
|----------|-------|-----------|--------|------------|
| Gigon | 11 | NF | PC | DERM |
| Headid | 11 | NF | PC | DERM |
| Monsivais | 11 | NF | PC | FMIT |
| Sloss | 11 | NF | PC | FMIT |
| Wilhelm | 12 | NF | PC | FMIT |
| Byrnes | 12 | NF | PC | FMIT |
| Thomas | 12 | NF | PC | CARD |
| Maher | 12 | NF | PC | DERM |
| Travis | 13 | NF | PC | FMIT |
| Sawyer | 13 | NF | PC | FMIT |
| Sloss | 13 | NF | PC | DERM |
| Cook | 13 | NF | PC | DERM |

### Post-Call Constraint Enforcement
The existing `NightFloatPostCallConstraint` now correctly triggers:
- NF ends on day 14 → PC required on day 15 (mid-block)
- NF ends on day 28 → PC required on next block day 1

---

## Prerequisites Created

For the split script to work, standalone rotation templates were created:
```sql
-- Dermatology (standalone)
INSERT INTO rotation_templates (id, name, abbreviation, activity_type, ...)
VALUES ('49071d43-...', 'Dermatology', 'DERM', 'elective', ...);

-- Cardiology (standalone)
INSERT INTO rotation_templates (id, name, abbreviation, activity_type, ...)
VALUES ('3fabd4e7-...', 'Cardiology', 'CARD', 'elective', ...);
```

---

## Verification

### Color Verification
```bash
# Check rotation templates have colors
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/rotation-templates" | \
  jq '.items[] | {name, abbreviation, font_color, background_color}'
```

### Split Verification
```bash
# Check Gigon's Block 11 assignments
docker exec -i residency-scheduler-backend python3 -c "
import psycopg2
conn = psycopg2.connect('...')
cur = conn.cursor()
cur.execute('''
    SELECT b.date, b.time_of_day, rt.abbreviation
    FROM assignments a
    JOIN blocks b ON a.block_id = b.id
    JOIN people p ON a.person_id = p.id
    JOIN rotation_templates rt ON a.rotation_template_id = rt.id
    WHERE p.name = 'Alaine Gigon' AND b.block_number = 11
    ORDER BY b.date
''')
for r in cur.fetchall():
    print(f'{r[0]} {r[1]}: {r[2]}')
"
# Expected: NF for days 1-14, PC for day 15, DERM for days 16-28
```

---

## Files Changed

### Modified
- `backend/app/models/rotation_template.py` - Added color columns
- `backend/app/schemas/rotation_template.py` - Added color fields to schemas
- `frontend/src/types/api.ts` - Added TypeScript color fields
- `frontend/src/components/schedule/ScheduleGrid.tsx` - Pass colors to cells
- `frontend/src/components/schedule/ScheduleCell.tsx` - Render with inline styles

### Created
- `split_combined_rotations.py` - One-time migration script (already executed)

### Migrations
- `backend/alembic/versions/e46cd3bee350_merge_block0_and_main_heads.py` - Merge migration heads

---

## Notes

1. **Tailwind Dynamic Classes**: Tailwind CSS purges unused classes at build time. Dynamic class names like `bg-${color}` don't work. Solution: use inline styles with hex values.

2. **Database Password**: Found in container env: `5XcUhOacvejEwBWW9M8BpSjlkrhzAxtt`

3. **Split Script Location**: Keep `split_combined_rotations.py` in repo root as a utility for future similar migrations.

4. **Faculty Outpatient**: Not addressed this session. Requires Airtable Primary Duties data integration (future work).

---

## Related Files
- `docs/schedules/sanitized_primary_duties.json` - Airtable Primary Duties export
- `docs/schedules/sanitized_faculty_clinic_templates.json` - Faculty clinic template mappings
- `.claude/plans/sunny-launching-river.md` - Planning document
