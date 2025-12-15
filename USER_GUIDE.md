# Residency Scheduler User Guide

This guide explains how to use the Residency Scheduler application for managing medical residency schedules with ACGME compliance.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [User Roles](#user-roles)
3. [Dashboard](#dashboard)
4. [People Management](#people-management)
5. [Rotation Templates](#rotation-templates)
6. [Absence Management](#absence-management)
7. [ACGME Compliance](#acgme-compliance)
8. [Generating Schedules](#generating-schedules)
9. [Exporting Data](#exporting-data)
10. [Settings (Admin Only)](#settings-admin-only)
11. [Common Workflows](#common-workflows)

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

### Faculty
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
| **Activity Type** | Category: clinic, inpatient, procedure, conference, elective, call |
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

### Activity Type Colors

Templates are color-coded by activity type:
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

## Getting Help

If you encounter issues:
1. Check this guide for the relevant section
2. Contact your program administrator
3. For technical issues, contact your IT support

---

*Residency Scheduler - Making medical education scheduling easier*
