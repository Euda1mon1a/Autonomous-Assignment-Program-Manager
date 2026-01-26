# Residency Scheduler User Guide

> **Last Updated:** 2025-12-17

This guide explains how to use the Residency Scheduler application for managing medical residency schedules with ACGME compliance.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [User Roles](#user-roles)
3. [Dashboard](#dashboard)
4. [Schedule Views](#schedule-views)
5. [People Management](#people-management)
6. [Rotation Templates](#rotation-templates)
7. [Absence Management](#absence-management)
8. [ACGME Compliance](#acgme-compliance)
9. [Generating Schedules](#generating-schedules)
10. [Exporting Data](#exporting-data)
11. [Settings (Admin Only)](#settings-admin-only)
12. [Common Workflows](#common-workflows)
13. [Quick Reference Card](#quick-reference-card)
14. [Glossary](#glossary)
15. [FAQ](#frequently-asked-questions)

---

## Getting Started

### Logging In

1. Navigate to the application URL
2. Enter your **username** and **password**
3. Click **Sign In**

If you don't have an account, contact your program administrator.

After logging in, you'll be redirected to the Dashboard.

### Navigation

The main navigation bar provides access to all sections:

| Section | Description |
|---------|-------------|
| **Dashboard** | Overview with schedule summary, compliance alerts, and quick actions |
| **People** | Manage residents and faculty |
| **Templates** | Define rotation types and constraints |
| **Absences** | Track vacation, deployments, and other time off |
| **Compliance** | Monitor ACGME requirement violations |
| **Help** | Quick reference, glossary, and FAQ (printable as PDF) |
| **Settings** | System configuration (Admin only) |

---

## User Roles

The system has three user roles with different permissions:

### Admin
Full access to all features:
- View and manage all data
- Configure system settings (academic year, ACGME parameters, scheduling algorithm)
- Manage user accounts
- Generate and modify schedules
- Export data

### Coordinator
Schedule management access:
- View all data
- Add/edit/delete people, templates, and absences
- Generate and modify schedules
- Monitor compliance
- Export data
- **Cannot access** Settings

<<<<<<< HEAD
### Faculty
=======
##***REMOVED***
>>>>>>> origin/docs/session-14-summary
View-only access:
- View schedules and their assignments
- View compliance status
- **Cannot** add/modify data
- **Cannot** generate schedules

---

## Dashboard

The Dashboard is your home screen, showing:

### Schedule Summary
- Current block/week overview
- Number of scheduled assignments
- Coverage statistics

### Compliance Alert
- Quick status of ACGME compliance
- Count of any active violations
- Link to full compliance details

### Upcoming Absences
- Next few days of scheduled absences
- Who is out and why
- Quick visibility into coverage gaps

### Quick Actions
Four buttons for common tasks:

| Button | Action |
|--------|--------|
| **Generate Schedule** | Opens dialog to create new schedule |
| **Export Excel** | Downloads current 4-week block as Excel file |
| **Add Person** | Goes to People page to add resident/faculty |
| **View Templates** | Goes to Templates page |

---

## Schedule Views

Access the schedule via **Schedule** in the navigation. The schedule page offers multiple view modes to suit different planning needs.

### Standard Views

Use the **View Toggle** buttons (Day, Week, Month, Block) to switch between standard views:

| View | Description |
|------|-------------|
| **Day** | Single day with detailed AM/PM assignments |
| **Week** | 7-day view for weekly planning |
| **Month** | Calendar month overview |
| **Block** | 4-week block view (28 days) - default scheduling unit |

### Annual Drag-and-Drop Views

Two specialized views provide **year-at-a-glance** planning with **drag-and-drop** capability:

#### Resident Academic Year View (Res.)

Click the **Res.** button (graduation cap icon) to access:
- Full academic year view (July 1 - June 30)
- All residents grouped by PGY level (PGY-1, PGY-2, PGY-3)
- 52 weeks displayed with month headers and week numbers
- **Drag-and-drop** to reschedule assignments within a resident's row
- Compact/normal zoom toggle for different detail levels
- "Today" button to quickly navigate to current date
- Color-coded rotation types (Clinic, Inpatient, Procedure, Call, Elective, Leave)

**How to use drag-and-drop:**
1. Click and hold on any assignment cell
2. Drag horizontally to a new date/time slot in the same row
3. Release to move the assignment
4. A toast notification confirms the change

<<<<<<< HEAD
#### Faculty Inpatient Weeks View (Fac.)
=======
###***REMOVED*** Inpatient Weeks View (Fac.)
>>>>>>> origin/docs/session-14-summary

Click the **Fac.** button (users icon) to access:
- Faculty-focused view for managing inpatient service weeks
- Shows all faculty members sorted by inpatient week count
- **Summary statistics** at top:
  - Total inpatient weeks
  - Average weeks per faculty
  - Maximum/minimum weeks
- Toggle between "All" activities or "Inpatient only" filter
- Same drag-and-drop functionality as resident view
- Helps ensure equitable distribution of inpatient coverage

### View Navigation

All annual views include:
- **Academic year selector**: Navigate between years (e.g., AY 2024-2025)
- **Previous/Next buttons**: Move between academic years
- **Today button**: Jump to current date
- **Zoom toggle**: Switch between compact and normal cell sizes

### Legend

Color coding is consistent across all views:
- **Blue**: Clinic
- **Purple**: Inpatient
- **Red**: Procedure
- **Orange**: Call
- **Green**: Elective
- **Amber**: Leave/Vacation
- **Gray**: Conference

---

## People Management

Access via **People** in the navigation.

### Viewing People

The People page shows all residents and faculty in card format:
- **Name** with role icon (graduation cap for residents, user icon for faculty)
- **PGY Level** for residents (PGY-1, PGY-2, PGY-3)
- **Specialties** if assigned
- **Email** contact

### Filtering

Use the filter controls to narrow the list:
- **All / Resident / Faculty** tabs to filter by type
- **PGY Level** dropdown to filter residents by year

### Adding a Person

1. Click **Add Person** button
2. Fill in the form:
   - **Name** (required)
   - **Type**: Resident or Faculty
   - **PGY Level**: 1, 2, or 3 (for residents only)
   - **Email** (optional)
   - **Specialties** (optional)
3. Click **Save**

### Editing a Person

1. Find the person in the list
2. Click **Edit** on their card
3. Modify the information
4. Click **Save Changes**

### Deleting a Person

1. Find the person in the list
2. Click **Delete** on their card
3. Confirm the deletion

**Warning**: Deleting a person will affect any schedules they're assigned to.

---

## Rotation Templates

Access via **Templates** in the navigation.

Templates define the types of rotations/activities in your program with their constraints.

### Template Fields

| Field | Description |
|-------|-------------|
| **Name** | Template name (e.g., "Inpatient Ward", "Clinic AM") |
| **Rotation Type** | Category: clinic, inpatient, procedure, conference, elective, call |
| **Abbreviation** | Short code for schedule display (e.g., "INP", "CLN") |
| **Max Residents** | Maximum residents allowed on this rotation at once |
| **Supervision Ratio** | Faculty-to-resident ratio (1:2, 1:4, etc.) |
| **Requires Specialty** | If rotation requires specific training |

### Creating a Template

1. Click **New Template**
2. Fill in the template details
3. Click **Create**

### Editing a Template

1. Find the template card
2. Click **Edit**
3. Modify settings
4. Click **Save Changes**

### Rotation Type Colors

Templates are color-coded by rotation type:
- **Blue**: Clinic
- **Purple**: Inpatient
- **Red**: Procedure
- **Gray**: Conference
- **Green**: Elective
- **Orange**: Call

---

## Absence Management

Access via **Absences** in the navigation.

Track all types of time off for residents and faculty.

### Absence Types

| Type | Description | Typical Use |
|------|-------------|-------------|
| **Vacation** | Planned time off | Annual leave |
| **Medical** | Sick leave | Illness, appointments |
| **Deployment** | Military deployment | Active duty orders |
| **TDY** | Temporary Duty | Military training, assignments |
| **Conference** | Professional development | Medical conferences, CME |
| **Family Emergency** | Personal/family matters | Unexpected family situations |

### View Modes

Toggle between two views:
- **Calendar View**: Visual month calendar showing absences as colored blocks
- **List View**: Table format with full details

### Adding an Absence

1. Click **Add Absence**
2. Select the **Person** from dropdown
3. Choose **Absence Type**
4. Set **Start Date** and **End Date**
5. Add **Notes** (optional) - useful for deployment orders, TDY locations
6. Click **Save**

### Editing an Absence

1. Click on an absence (calendar) or click **Edit** (list)
2. Modify the details
3. Click **Save Changes**

### Filtering Absences

Use the **Type** dropdown to filter:
- All Types
- Vacation
- Sick / Medical
- Conference
- Personal / Family Emergency
- Deployment
- TDY

---

## ACGME Compliance

Access via **Compliance** in the navigation.

Monitor schedule compliance with ACGME (Accreditation Council for Graduate Medical Education) requirements.

### Compliance Rules Monitored

#### 80-Hour Rule
- Residents cannot exceed 80 hours/week averaged over 4 weeks
- **Critical violation** if exceeded

#### 1-in-7 Rule
- Residents must have one 24-hour period off every 7 days
- **High violation** if missed

#### Supervision Ratios
- PGY-1 residents: 1 faculty per 2 residents
- PGY-2/3 residents: 1 faculty per 4 residents
- **Medium violation** if ratios exceeded

### Compliance Cards

Three cards show pass/fail status for each rule:
- **Green checkmark**: No violations
- **Red X**: Violations present (with count)

### Violation List

Below the cards, any violations are listed with:
- **Severity**: Critical, High, Medium, Low (color-coded)
- **Type**: Which rule was violated
- **Message**: Details about the violation
- **Person**: Who is affected

### Month Navigation

Use the arrow buttons to check compliance for different months.

### Coverage Rate

Shows what percentage of required positions are filled for the selected period.

---

## Generating Schedules

### From Dashboard

1. Click **Generate Schedule** in Quick Actions
2. Set the **Start Date** and **End Date**
3. Select scheduling **Algorithm**:
   - **Greedy (Fast)**: Quick generation, good results
   - **Min Conflicts (Balanced)**: Better optimization, moderate speed
   - **CP-SAT (Optimal)**: Best results, slower
4. Click **Generate**

### What Happens During Generation

The scheduler:
1. Reads all people and their availability
2. Checks absence records
3. Applies rotation templates
4. Assigns residents to rotations respecting:
   - ACGME hour limits
   - Supervision ratios
   - Specialty requirements
   - Capacity limits
5. Reports any conflicts or gaps

### After Generation

- Review the schedule on the Dashboard
- Check **Compliance** page for any violations
- Export if needed

### Lessons Learned (Operational Safeguards)

These practices help prevent schedule loss or unexpected changes:

- **Avoid overwriting a good schedule**: Only regenerate when necessary, and confirm the date range before running.
- **Record manual overrides**: When you change assignments by hand, add a reason so the change is auditable.
- **Preserve manual decisions**: Use "locked" or "protected" assignments when available to prevent automatic replacements.
- **Emergency closures are manual**: Unexpected holidays (e.g., presidential orders) should be handled explicitly; do not assume clinic is canceled by default.
- **Double-check algorithm choice**: Faster modes are useful for drafts, but may not meet all constraints.
- **Document anomalies**: If coverage cannot be met, record the exception and why.

---

## Exporting Data

### Export Formats

#### CSV Export
- Available on People and Absences pages
- Click the **Export** dropdown
- Select **Export as CSV**
- Opens in Excel, Google Sheets, etc.

#### JSON Export
- Available on People and Absences pages
- Click the **Export** dropdown
- Select **Export as JSON**
- Useful for data integration

#### Legacy Excel Export
- Available from Dashboard Quick Actions
- Click **Export Excel**
- Generates a formatted .xlsx file with:
  - AM/PM columns for each day
  - Color-coded rotations
  - Grouped by PGY level
  - Federal holidays highlighted

---

## Settings (Admin Only)

Access via **Settings** in the navigation. **Admin role required**.

### Academic Year Settings

| Setting | Description | Default |
|---------|-------------|---------|
| **Start Date** | First day of academic year | July 1 |
| **End Date** | Last day of academic year | June 30 |
| **Block Duration** | Days per scheduling block | 28 |

### ACGME Settings

| Setting | Description | Default |
|---------|-------------|---------|
| **Max Weekly Hours** | Maximum hours per week | 80 |
| **PGY-1 Supervision Ratio** | Faculty per PGY-1 resident | 1:2 |
| **PGY-2/3 Supervision Ratio** | Faculty per PGY-2/3 resident | 1:4 |

### Scheduling Algorithm

| Algorithm | Description |
|-----------|-------------|
| **Greedy** | Fast, first-fit approach |
| **Min Conflicts** | Balances speed and quality |
| **CP-SAT** | Constraint programming, finds optimal |

### Federal Holidays

Lists recognized holidays that affect scheduling:
- New Year's Day
- MLK Day
- Presidents Day
- Memorial Day
- Independence Day
- Labor Day
- Columbus Day
- Veterans Day
- Thanksgiving
- Christmas

---

## Common Workflows

### Starting a New Academic Year

1. **Admin**: Go to Settings, update Academic Year dates
2. Add new incoming residents (People page)
3. Update PGY levels for continuing residents
4. Remove graduated residents
5. Review/update templates if needed

### Handling a Military Deployment

1. Go to **Absences**
2. Click **Add Absence**
3. Select the person being deployed
4. Set **Type** to "Deployment"
5. Enter deployment dates
6. Add deployment order info in **Notes**
7. **Regenerate schedules** for affected period

### Handling TDY (Temporary Duty)

1. Go to **Absences**
2. Click **Add Absence**
3. Select the person
4. Set **Type** to "TDY"
5. Enter TDY dates
6. Add location/purpose in **Notes**
7. Check **Compliance** to ensure coverage

### Resolving Compliance Violations

1. Go to **Compliance** page
2. Review listed violations
3. For 80-hour violations:
   - Reduce scheduled hours for affected resident
   - Add day off or lighter rotation
4. For 1-in-7 violations:
   - Ensure resident has a full day off within 7-day window
5. For supervision ratio violations:
   - Add faculty coverage
   - Reduce resident count on rotation
6. Regenerate schedule if needed
7. Verify violations are resolved

### Preparing Monthly Schedule Distribution

1. Generate schedule for the upcoming month
2. Review on Dashboard
3. Check **Compliance** page - resolve any violations
4. Click **Export Excel** for distribution file
5. Send to residents and faculty

### Adding a Last-Minute Absence

1. Go to **Absences**
2. Click **Add Absence**
3. Enter details
4. Check **Dashboard** for coverage impact
5. Consider regenerating affected dates
6. Verify **Compliance** is maintained

---

## Tips

- **Check compliance regularly** - run the compliance check after any schedule changes
- **Use templates** - well-defined templates make schedule generation more reliable
- **Document absences early** - enter known absences (vacation, conferences) as soon as approved
- **Export backups** - periodically export data as JSON for backup purposes
- **Use filtering** - the filter options on People and Absences pages help manage large lists

---

## Quick Reference Card

### Common Tasks at a Glance

| Task | Where to Go |
|------|-------------|
| Generate a schedule | Dashboard → Generate Schedule |
| Add a new resident | People → Add Person |
| Record time off | Absences → Add Absence |
| Check compliance | Compliance page |
| Export to Excel | Dashboard → Export Excel |
| Create rotation type | Templates → New Template |
| View full year schedule | Schedule → Res. (resident) or Fac. (faculty) |
| Drag to reschedule | Schedule → Res./Fac. view → drag assignment |

### Navigation Quick Guide

- **Dashboard** - Home page, overview, quick actions
- **Schedule** - View/edit schedules (Day/Week/Month/Block/Annual views)
- **People** - Manage residents and faculty
- **Templates** - Rotation types and rules
- **Absences** - Vacation, deployment, sick leave
- **Compliance** - ACGME rule monitoring
- **Help** - This reference guide (printable)
- **Settings** - System config (Admin only)

### Absence Types Quick Reference

| Type | Use For |
|------|---------|
| Vacation | Planned annual leave |
| Medical | Sick days, appointments |
| Deployment | Military active duty |
| TDY | Temporary duty assignment |
| Conference | CME, medical meetings |
| Family Emergency | Personal matters |

### ACGME Rules Quick Reference

| Rule | Limit |
|------|-------|
| 80-Hour Rule | Max 80 hrs/week (4-week avg) |
| 1-in-7 Rule | One day off every 7 days |
| PGY-1 Supervision | 1 faculty per 2 residents |
| PGY-2/3 Supervision | 1 faculty per 4 residents |

---

## Glossary

| Term | Definition |
|------|------------|
| **ACGME** | Accreditation Council for Graduate Medical Education - sets residency training standards |
| **PGY** | Post-Graduate Year - PGY-1 is first year, PGY-2 is second year, etc. |
| **Block** | A scheduling period, typically 4 weeks (28 days) |
| **Rotation** | A clinical assignment (e.g., Inpatient, Clinic, ICU) |
| **TDY** | Temporary Duty - military assignment away from home station |
| **Deployment** | Military active duty assignment, typically overseas |
| **Template** | A reusable rotation definition with rules and constraints |
| **Supervision Ratio** | Required number of faculty per resident (e.g., 1:2 means 1 faculty per 2 residents) |
| **Coverage Rate** | Percentage of required positions that are filled |
| **Violation** | When a schedule breaks an ACGME rule |
| **Academic Year** | Typically July 1 to June 30 for residency programs |
| **CME** | Continuing Medical Education - required ongoing training |
| **Greedy Algorithm** | Fast scheduling method that fills slots one at a time |
| **CP-SAT** | Constraint Programming - slower but finds optimal schedules |
| **AM/PM** | Morning and afternoon sessions in the daily schedule |
| **Faculty** | Attending physicians who supervise residents |

---

## Frequently Asked Questions

### Access & Permissions

**Q: Why can't I see the Settings page?**
A: Settings is only available to Admin users. Contact your program administrator if you need settings changed.

**Q: How do I reset my password?**
A: Contact your program administrator to reset your password.

**Q: Can multiple people use the system at the same time?**
A: Yes, multiple users can be logged in simultaneously. Changes are saved immediately.

### Scheduling

**Q: Which scheduling algorithm should I use?**
A: Start with "Greedy" for quick results. Try "Min Conflicts" if you're getting violations. Use "CP-SAT" when you need the best possible schedule and have time to wait.

**Q: How far in advance can I generate schedules?**
Schedules can be generated for any date range. Common practice is one block (4 weeks) at a time.

**Q: Why is the schedule showing compliance violations?**
A: Violations appear when the schedule breaks ACGME rules. Check the Compliance page to see details and adjust the schedule accordingly.

### People & Absences

**Q: How do I add a new resident at the start of the year?**
A: Go to People → Add Person. Select "Resident" as type, set PGY level to 1 for interns.

**Q: How do I update a resident's PGY level?**
A: Go to People, find the resident, click Edit, and change their PGY level.

**Q: What's the difference between Deployment and TDY?**
A: Deployment is typically longer military assignment (often overseas). TDY is shorter, usually for training or temporary work.

**Q: What happens if I delete a person with scheduled assignments?**
A: Their assignments will be affected. Remove or reassign their slots first, then delete.

### Exporting & Printing

**Q: How do I print the schedule for distribution?**
A: From Dashboard, click "Export Excel" to download a formatted spreadsheet you can print or email.

**Q: How do I print this help guide?**
A: Go to Help page in the application and click "Print / Save PDF" button.

### Mobile & Technical

**Q: Can I use this on my phone?**
A: Yes, the application works on mobile devices. For complex tasks, a tablet or computer is recommended.

---

## Getting Help

### In-App Help

Click **Help** in the navigation bar to access:
- Quick Reference Card
- Glossary of Terms
- Frequently Asked Questions
- **Print / Save PDF** button for offline reference

### Additional Support

If you encounter issues:
1. Check the in-app **Help** page
2. Review this user guide
3. Contact your program administrator
4. For technical issues, contact your IT support

---

*Residency Scheduler - Making medical education scheduling easier*
