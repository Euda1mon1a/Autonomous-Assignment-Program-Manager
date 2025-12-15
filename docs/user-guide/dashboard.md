# Dashboard Overview

The Dashboard is your command center for the Residency Scheduler. It provides a comprehensive overview of your scheduling status, compliance alerts, and quick access to common actions.

---

## Accessing the Dashboard

- Click **Dashboard** in the navigation bar
- Click the **logo** from any page
- This is the default landing page after login

---

## Dashboard Layout

```
+------------------------------------------------------------------------+
|                           HEADER NAVIGATION                             |
+------------------------------------------------------------------------+
|                                                                         |
|  +-------------------------+     +-------------------------+            |
|  |    SCHEDULE SUMMARY     |     |    COMPLIANCE ALERT     |           |
|  |                         |     |                         |           |
|  |  Current Period:        |     |  Status: [Green/Red]    |           |
|  |  Block 3 (Jan 15-Feb 11)|     |  Violations: 0          |           |
|  |                         |     |                         |           |
|  |  Assignments: 156       |     |  [View Details]         |           |
|  |  Coverage: 94%          |     |                         |           |
|  +-------------------------+     +-------------------------+            |
|                                                                         |
|  +-------------------------+     +-------------------------+            |
|  |   UPCOMING ABSENCES     |     |     QUICK ACTIONS       |           |
|  |                         |     |                         |           |
|  |  Jan 16: Dr. Smith      |     |  [Generate Schedule]    |           |
|  |          (Vacation)     |     |  [Export Excel]         |           |
|  |  Jan 17: Dr. Jones      |     |  [Add Person]           |           |
|  |          (TDY)          |     |  [View Templates]       |           |
|  |  Jan 20: Dr. Brown      |     |                         |           |
|  |          (Conference)   |     |                         |           |
|  +-------------------------+     +-------------------------+            |
|                                                                         |
+------------------------------------------------------------------------+
```

---

## Dashboard Widgets

### Schedule Summary Widget

The Schedule Summary shows the current state of your schedule.

#### Information Displayed

| Field | Description |
|-------|-------------|
| **Current Period** | The active scheduling block (e.g., "Block 3: Jan 15 - Feb 11") |
| **Assignments** | Total number of scheduled assignments |
| **Coverage Rate** | Percentage of required positions filled |
| **Active Residents** | Number of residents currently scheduled |

#### Visual Indicators

- **Green bar**: Good coverage (>90%)
- **Yellow bar**: Moderate coverage (70-90%)
- **Red bar**: Low coverage (<70%)

#### Actions

- Click anywhere on the widget to view detailed schedule
- Hover over statistics for additional details

---

### Compliance Alert Widget

The Compliance Alert provides immediate visibility into ACGME compliance status.

#### Status Indicators

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| **Green checkmark** | All rules compliant | None |
| **Yellow warning** | Minor violations | Review recommended |
| **Red X** | Critical violations | Immediate attention |

#### Information Displayed

- **Overall Status**: Pass/Warning/Fail
- **Violation Count**: Number of active violations
- **Most Serious**: Type of most critical violation

#### Quick Actions

- **View Details**: Navigates to full Compliance page
- Clicking the widget opens detailed violation list

---

### Upcoming Absences Widget

Shows scheduled absences for the next 7-14 days.

#### Information Per Absence

| Field | Description |
|-------|-------------|
| **Date** | When the absence occurs |
| **Person** | Name of resident/faculty |
| **Type** | Absence category (icon + text) |

#### Absence Type Icons

| Icon | Type |
|------|------|
| Palm tree | Vacation |
| Medical cross | Medical/Sick |
| Airplane | Conference |
| Military star | Deployment |
| Briefcase | TDY |
| Heart | Family Emergency |

#### Actions

- Click any absence to view/edit details
- **View All**: Navigates to Absences page

---

### Quick Actions Widget

Four buttons for frequently performed tasks.

#### Generate Schedule

```
+------------------------+
|   Generate Schedule    |
|     [Calendar Icon]    |
+------------------------+
```

Opens the schedule generation dialog:

1. Click the button
2. Select **Start Date**
3. Select **End Date**
4. Choose **Algorithm**:
   - Greedy (Fast)
   - Min Conflicts (Balanced)
   - CP-SAT (Optimal)
5. Click **Generate**

**Tip**: Start with Greedy for quick results; use CP-SAT for optimal schedules.

---

#### Export Excel

```
+------------------------+
|     Export Excel       |
|     [Download Icon]    |
+------------------------+
```

Downloads the current 4-week block as an Excel file.

**Excel File Contents**:
- AM/PM columns for each day
- Color-coded rotation types
- Grouped by PGY level
- Federal holidays highlighted
- Ready for printing

---

#### Add Person

```
+------------------------+
|      Add Person        |
|      [User+ Icon]      |
+------------------------+
```

Navigates to People page with add dialog open.

Quick path to add:
- New residents (start of academic year)
- New faculty members
- Temporary staff

---

#### View Templates

```
+------------------------+
|    View Templates      |
|      [Grid Icon]       |
+------------------------+
```

Navigates to Templates page.

Use to:
- Review rotation definitions
- Check capacity limits
- Verify supervision requirements

---

## Dashboard for Different Roles

### Admin View

Full dashboard with all widgets and actions:
- All quick actions available
- Settings access in navigation
- Full edit capabilities

### Coordinator View

Same dashboard as Admin except:
- No Settings access
- Full schedule management capabilities

### Faculty View

Limited dashboard:
- Schedule Summary (view only)
- Compliance Alert (view only)
- Upcoming Absences (view only)
- Quick Actions: Only "Export Excel" functional

---

## Dashboard Best Practices

### Daily Check

Start your day by reviewing:
1. **Compliance Alert** - Any new violations?
2. **Upcoming Absences** - Who's out this week?
3. **Coverage Rate** - Any gaps to address?

### Weekly Tasks

Each week, use the dashboard to:
1. Export and distribute schedule
2. Check compliance trends
3. Review upcoming absences

### Monthly Tasks

At the start of each block:
1. Generate new schedule
2. Verify full compliance
3. Export for distribution

---

## Dashboard Data Refresh

### Automatic Refresh

- Dashboard data refreshes automatically every 5 minutes
- Real-time updates when changes are made in other tabs

### Manual Refresh

- Click the browser refresh button
- Use `F5` or `Cmd+R` / `Ctrl+R`
- Dashboard reloads with latest data

---

## Troubleshooting Dashboard Issues

| Issue | Solution |
|-------|----------|
| Data not updating | Refresh the page |
| Widgets not loading | Check network connection |
| Export not working | Try different browser |
| Charts not displaying | Enable JavaScript |

---

## Related Guides

- [Getting Started](getting-started.md) - Basic navigation
- [Schedule Generation](schedule-generation.md) - Detailed schedule creation
- [Compliance](compliance.md) - Understanding ACGME monitoring
- [Exporting Data](exporting-data.md) - Export options explained

---

*The Dashboard is your daily starting point for effective schedule management.*
