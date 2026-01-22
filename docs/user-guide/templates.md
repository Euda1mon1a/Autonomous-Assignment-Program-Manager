# Templates Hub

The Templates Hub (`/templates`) provides a unified interface for managing rotation templates and faculty weekly schedules. Access is tier-based, ensuring appropriate permissions for viewing and editing.

---

## Overview

The Templates Hub consolidates two key scheduling components:

1. **Rotation Templates** - Define how rotations are scheduled (activities, patterns, requirements)
2. **Faculty Templates** - Define weekly activity assignments for faculty members

### Access Levels

| Tier | Bar Color | Roles | Capabilities |
|------|-----------|-------|--------------|
| **0** | Green | Residents, Clinical Staff | View rotation templates, view own schedule |
| **0.5** | Green | Faculty | View rotation templates, view own schedule |
| **1** | Amber | Coordinator, Chief Resident | Edit rotation templates, edit any faculty template |
| **2** | Red | Admin | Bulk operations, system configuration |

---

## Tabs

### Rotations Tab (Tier 0+)

View all rotation templates with search and filtering capabilities.

**Features:**
- Search by name or abbreviation
- Filter by activity type (Clinic, Inpatient, Call, etc.)
- Sortable columns
- View template details

**For Tier 1+ Users:**
- Inline editing of template properties
- Create new templates
- Modify activity requirements

### My Schedule Tab (Tier 0+)

View your own weekly activity template in read-only mode.

**For Faculty:**
- See your default AM/PM activity assignments for each day
- Template mode shows repeating weekly pattern
- Week mode shows specific week with any overrides

**For Non-Faculty (Residents):**
- Message indicating schedule is managed through rotations
- Link to Schedule section for assignment details

!!! note "Requesting Changes"
    Faculty members cannot edit their own templates directly. To request changes, contact your program coordinator.

### Faculty Templates Tab (Tier 1+)

Select any faculty member and edit their weekly activity template.

**Features:**
- Searchable faculty dropdown
- Faculty role badges (PD, APD, OIC, Core, Adjunct)
- 7x2 grid editor (Monday-Sunday, AM/PM)
- Activity palette with role-permitted activities
- Slot locking for protected assignments
- Priority slider for soft constraints
- Template vs week-specific mode toggle

### Matrix View Tab (Tier 1+)

At-a-glance overview of all faculty schedules for a week.

**Features:**
- All faculty in rows, days in columns
- AM/PM cells show activity abbreviations
- Color-coded by activity type
- Adjunct faculty toggle
- Workload badges showing deviation from mean
- Click any cell to open editor modal

### Bulk Operations Tab (Tier 2)

Administrative tools for system-wide template management.

**Features:**
- Copy templates between faculty
- Bulk update activity requirements
- Coverage gap analysis

---

## Workflows

### Viewing Your Schedule (All Users)

1. Navigate to `/templates`
2. Click the **My Schedule** tab
3. View your weekly activity assignments
4. Use the week navigator to see specific weeks

### Editing a Faculty Template (Coordinators)

1. Navigate to `/templates`
2. Click the **Faculty Templates** tab
3. Select a faculty member from the dropdown
4. Click a cell in the grid to assign an activity
5. Use the activity palette to select activities
6. Click **Save** to commit changes

### Using the Matrix View (Coordinators)

1. Navigate to `/templates`
2. Click the **Matrix View** tab
3. Use the week navigator to select a date range
4. Toggle "Include Adjunct" if needed
5. Click any cell to edit that faculty member's template

---

## Activity Types

| Type | Color | Description |
|------|-------|-------------|
| **Clinic** | Blue | Outpatient clinic sessions |
| **Inpatient** | Orange | Hospital ward coverage |
| **Call** | Red | On-call duty |
| **Admin/GME** | Green | Administrative or GME time |
| **Education** | Purple | Teaching, conferences |
| **Leave** | Gray | Vacation, sick leave |

---

## Related Documentation

- [Schedule Management](schedule.md) - Managing resident schedules
- [Block Scheduler](block-scheduler.md) - Rotation assignments
- [Compliance](compliance.md) - ACGME compliance monitoring
