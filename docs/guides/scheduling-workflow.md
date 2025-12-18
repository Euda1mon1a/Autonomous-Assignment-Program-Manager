# Schedule Management

View, generate, and edit schedules in Residency Scheduler.

---

## Viewing Schedules

Access schedules from **Schedule** in the navigation.

### Calendar View

- Monthly/weekly/daily views
- Color-coded by rotation type
- Click any assignment for details

### Timeline View

- Gantt-style visualization
- See all residents at once
- Identify coverage gaps

### Daily Manifest

- Today's assignments at a glance
- Quick status overview
- Print-friendly format

---

## Generating a Schedule

1. Navigate to **Schedule** → **Generate**
2. Configure generation parameters:

| Parameter | Description |
|-----------|-------------|
| **Date Range** | Start and end dates |
| **Algorithm** | Greedy, CP-SAT, Hybrid |
| **Priorities** | Weight factors for optimization |

3. Click **Generate Schedule**
4. Wait for processing (may take several minutes)
5. Review the generated schedule
6. Check compliance violations
7. Click **Publish** to make active

---

## Manual Adjustments

Edit individual assignments:

1. Click on an assignment in the calendar
2. Click **Edit**
3. Modify:
    - Person assigned
    - Time/date
    - Location
    - Notes
4. System validates ACGME compliance
5. Click **Save**

---

## Emergency Coverage

Handle unexpected absences:

1. Go to **Schedule** → **Emergency Coverage**
2. Select the affected assignment
3. Enter reason (medical, deployment, etc.)
4. System suggests available replacements
5. Select a replacement or enter manually
6. Notifications sent automatically

---

## Scheduling Algorithms

| Algorithm | Speed | Quality | Use Case |
|-----------|-------|---------|----------|
| **Greedy** | Fast | Good | Initial drafts |
| **CP-SAT** | Slow | Optimal | Final schedules |
| **Hybrid** | Medium | Better | Balanced approach |

!!! tip "Algorithm Selection"
    Start with Greedy for quick drafts, then use CP-SAT for final optimization.
