# Call Roster

The Call Roster shows who is on call and their contact information.

---

## Overview

Navigate to **Call Roster** from the main navigation to see on-call assignments. This is essential for nurses and staff who need to know who to page for coverage.

---

## View Modes

### Calendar View

Shows on-call assignments in a monthly calendar format:

- Color-coded by role (Attending, Senior Resident, Intern)
- Click any day to see details
- Today is highlighted

### List View

Shows on-call assignments as a detailed list:

- Sortable by date, role, or person
- Full contact information visible
- Filterable by date range

---

## Reading the Calendar

### Color Coding

| Color | Role |
|-------|------|
| Red | Attending Physician |
| Blue | Senior Resident (PGY-2/3) |
| Green | Intern (PGY-1) |

### Day Details

Click any day to see:

- All on-call personnel
- Contact information
- Shift times
- Backup coverage

---

## Contact Information

### Quick Actions

For each on-call person:

- **Phone**: Click to call (on mobile devices)
- **Pager**: Copy pager number to clipboard
- **Email**: Open email client

### Contact Display

Shows available contact methods:
- Primary phone
- Pager number
- Email address
- Backup contact

---

## Today's On-Call

The top section highlights today's coverage:

1. **Attending on Call** - Primary faculty coverage
2. **Senior Resident** - PGY-2/3 first-line coverage
3. **Intern** - PGY-1 coverage

Each shows:
- Name and photo (if available)
- Role and specialty
- Contact information
- Shift end time

---

## Filters

### Role Filter

Filter by on-call role:
- All Roles
- Attending Only
- Senior Residents
- Interns

### Date Filter

- Select specific date
- Date range picker
- Week/Month view toggles

---

## Navigation

### Month Navigation

- Previous/Next month buttons
- Jump to specific month
- **Today** button returns to current date

### Person Links

Click any person to:
- View their profile
- See their full call schedule
- Access their contact details

---

## Features

### Copy to Clipboard

Click the copy icon next to any contact number to copy it for pasting.

### Click to Call

On mobile devices, phone numbers are clickable to initiate calls.

### Hover Details

Hover over any calendar cell to see a tooltip with:
- Full names
- Contact numbers
- Shift times

---

## For Nurses and Staff

### Finding Who to Page

1. Open Call Roster
2. Check "Today's On-Call" section
3. Use contact information to reach on-call provider

### After Hours

The roster shows 24-hour coverage:
- Day shift on-call
- Night shift on-call
- Weekend coverage

---

## How Call is Assigned

### Automated Overnight Call (Sun-Thu)

Overnight call for Sunday through Thursday nights is **automatically generated** by the scheduling solver. The system:

1. **Ensures Coverage**: Every night has exactly one faculty on call
2. **Excludes Adjuncts**: Adjunct faculty are not auto-assigned (can be added manually)
3. **Respects Availability**: Honors approved leave and absences
4. **Balances Distribution**: Optimizes equity across faculty

### FMIT Weekend Coverage (Fri-Sat)

Friday and Saturday nights are covered by the **FMIT (Faculty Managing Inpatient Teaching)** faculty member who is on their inpatient rotation that week. This is pre-assigned when FMIT weeks are scheduled.

### Manual Adjustments

Coordinators can manually adjust call assignments through:
- **Create**: Add new call assignments
- **Update**: Modify existing assignments
- **Delete**: Remove assignments (use sparingly)

---

## Reports

### Coverage Report

Administrators can view coverage gaps:
- Total expected nights vs. covered nights
- Coverage percentage
- List of uncovered dates requiring attention

### Equity Report

View call distribution fairness:
- Sunday calls tracked separately (considered hardest)
- Mon-Thu weekday call statistics
- Per-faculty breakdown with totals

Access reports via **Schedule** > **Call Reports**.

---

## Best Practices

!!! tip "Bookmark This Page"
    Keep the Call Roster easily accessible for quick lookups.

!!! tip "Check Multiple Roles"
    For complex issues, you may need both attending and resident
    on-call contacts.

!!! tip "Verify Before Paging"
    Confirm the date - make sure you're looking at the correct day.

!!! tip "Review Coverage Reports"
    Coordinators should check the coverage report weekly to identify
    gaps before they become problems.

---

## Related Documentation

- **[Daily Manifest](daily-manifest.md)** - Who is where today
- **[Schedule Management](schedule.md)** - Full schedule view
- **[People Management](people.md)** - Contact information updates
- **[FMIT Scheduling](../architecture/FMIT_CONSTRAINTS.md)** - How FMIT weeks work
