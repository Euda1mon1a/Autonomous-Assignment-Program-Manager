***REMOVED*** User Guide

This guide explains how to use the Residency Scheduler application for managing medical residency schedules.

---

***REMOVED******REMOVED*** Table of Contents

1. [Dashboard Overview](***REMOVED***dashboard-overview)
2. [Managing People](***REMOVED***managing-people)
3. [Schedule Management](***REMOVED***schedule-management)
4. [Rotation Templates](***REMOVED***rotation-templates)
5. [Absences & Time Off](***REMOVED***absences--time-off)
6. [Swap Marketplace](***REMOVED***swap-marketplace)
7. [Compliance Monitoring](***REMOVED***compliance-monitoring)
8. [Exporting Data](***REMOVED***exporting-data)
9. [Personal Dashboard](***REMOVED***personal-dashboard)

---

***REMOVED******REMOVED*** Dashboard Overview

The main dashboard provides a quick overview of your residency program's scheduling status.

***REMOVED******REMOVED******REMOVED*** Dashboard Widgets

| Widget | Description |
|--------|-------------|
| **Compliance Status** | Current ACGME compliance indicators |
| **Today's Coverage** | Active assignments for today |
| **Upcoming Absences** | Scheduled time off in the next 7 days |
| **Pending Swaps** | Swap requests awaiting action |
| **Alerts** | Critical violations requiring attention |

***REMOVED******REMOVED******REMOVED*** Navigation

The sidebar provides access to all major sections:

- **Dashboard** - Home page with overview
- **Schedule** - View and manage schedules
- **People** - Manage residents and faculty
- **Templates** - Rotation template configuration
- **Absences** - Time-off management
- **Compliance** - ACGME compliance monitoring
- **Settings** - System configuration (Admin only)

---

***REMOVED******REMOVED*** Managing People

***REMOVED******REMOVED******REMOVED*** Adding a Person

1. Navigate to **People**
2. Click **Add Person**
3. Fill in the required fields:
   - **Name**: Full name
   - **Email**: Contact email
   - **Role**: Resident or Faculty
   - **PGY Level**: For residents (PGY-1, PGY-2, PGY-3)
   - **Specialty**: Primary specialty
4. Click **Save**

***REMOVED******REMOVED******REMOVED*** Bulk Import

Import multiple people from Excel:

1. Go to **Settings** → **Import Data**
2. Download the **People Template**
3. Fill in your data following the template format
4. Upload the completed file
5. Review the import preview
6. Click **Confirm Import**

***REMOVED******REMOVED******REMOVED*** Person Profiles

Click any person to view their profile:

- **Overview**: Contact info, role, PGY level
- **Schedule**: Their assigned blocks
- **Absences**: Scheduled time off
- **Certifications**: BLS, ACLS, PALS status
- **Credentials**: Procedure qualifications
- **History**: Assignment history

***REMOVED******REMOVED******REMOVED*** Managing Certifications

Track required certifications:

1. Open a person's profile
2. Click **Certifications** tab
3. Click **Add Certification**
4. Select type (BLS, ACLS, PALS, etc.)
5. Enter expiration date
6. Upload certificate document (optional)

The system automatically alerts before certifications expire.

---

***REMOVED******REMOVED*** Schedule Management

***REMOVED******REMOVED******REMOVED*** Viewing Schedules

Access schedules from **Schedule** in the navigation:

***REMOVED******REMOVED******REMOVED******REMOVED*** Calendar View
- Monthly/weekly/daily views
- Color-coded by rotation type
- Click any assignment for details

***REMOVED******REMOVED******REMOVED******REMOVED*** Timeline View
- Gantt-style visualization
- See all residents at once
- Identify coverage gaps

***REMOVED******REMOVED******REMOVED******REMOVED*** Daily Manifest
- Today's assignments at a glance
- Quick status overview
- Print-friendly format

***REMOVED******REMOVED******REMOVED*** Generating a Schedule

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

***REMOVED******REMOVED******REMOVED*** Manual Adjustments

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

***REMOVED******REMOVED******REMOVED*** Emergency Coverage

Handle unexpected absences:

1. Go to **Schedule** → **Emergency Coverage**
2. Select the affected assignment
3. Enter reason (medical, deployment, etc.)
4. System suggests available replacements
5. Select a replacement or enter manually
6. Notifications sent automatically

---

***REMOVED******REMOVED*** Rotation Templates

Templates define reusable scheduling patterns.

***REMOVED******REMOVED******REMOVED*** Creating a Template

1. Navigate to **Templates**
2. Click **Create Template**
3. Configure:

| Field | Description |
|-------|-------------|
| **Name** | Template identifier (e.g., "ICU", "Clinic") |
| **Type** | Rotation category |
| **Duration** | Length in blocks |
| **Capacity** | Maximum simultaneous residents |
| **PGY Requirements** | Required experience levels |
| **Supervision Ratio** | Faculty-to-resident ratio |

4. Click **Save**

***REMOVED******REMOVED******REMOVED*** Template Types

| Type | Description |
|------|-------------|
| **Clinical** | Patient care rotations |
| **Administrative** | Non-clinical duties |
| **Call** | On-call assignments |
| **Elective** | Optional rotations |
| **Vacation** | Time-off blocks |

***REMOVED******REMOVED******REMOVED*** Editing Templates

1. Click on a template
2. Modify fields as needed
3. Changes apply to future schedules
4. Existing assignments unchanged

---

***REMOVED******REMOVED*** Absences & Time Off

***REMOVED******REMOVED******REMOVED*** Recording an Absence

1. Go to **Absences**
2. Click **Add Absence**
3. Fill in details:

| Field | Description |
|-------|-------------|
| **Person** | Who is absent |
| **Type** | Vacation, Medical, Deployment, etc. |
| **Start Date** | When absence begins |
| **End Date** | When absence ends |
| **Notes** | Additional details |

4. Click **Save**
5. System updates availability automatically

***REMOVED******REMOVED******REMOVED*** Absence Types

| Type | Description |
|------|-------------|
| **Vacation** | Planned time off |
| **Medical** | Sick leave |
| **Deployment** | Military deployment |
| **TDY** | Temporary duty assignment |
| **Conference** | Educational conference |
| **Family Emergency** | Personal emergency |
| **Bereavement** | Loss of family member |

***REMOVED******REMOVED******REMOVED*** Viewing Absences

The absence calendar shows:

- All scheduled absences
- Impact on coverage
- Overlapping absences (potential issues)

Filter by:
- Person
- Date range
- Absence type
- Status

---

***REMOVED******REMOVED*** Swap Marketplace

The swap system allows residents to trade assignments.

***REMOVED******REMOVED******REMOVED*** Requesting a Swap

1. Navigate to **Swap Marketplace**
2. Click **Request Swap**
3. Select:
   - **Your Assignment**: The block you want to trade
   - **Preferred Dates**: When you'd prefer to work
   - **Notes**: Additional context
4. Click **Submit Request**

***REMOVED******REMOVED******REMOVED*** Auto-Matching

The system automatically finds compatible swaps using a 5-factor algorithm:

1. **Availability**: Both parties available
2. **Preferences**: Match preferences
3. **Specialization**: Required skills match
4. **PGY Balance**: Appropriate experience levels
5. **Coverage Impact**: Maintains adequate coverage

***REMOVED******REMOVED******REMOVED*** Responding to Swap Requests

1. View incoming requests in your dashboard
2. Click **View Details** on a request
3. Review:
   - Assignment details
   - Impact on your schedule
   - Compliance status
4. Click **Accept** or **Decline**

***REMOVED******REMOVED******REMOVED*** Swap Status

| Status | Description |
|--------|-------------|
| **Pending** | Awaiting response |
| **Matched** | Found potential match |
| **Accepted** | Both parties agreed |
| **Completed** | Swap executed |
| **Cancelled** | Request withdrawn |
| **Declined** | Request rejected |

---

***REMOVED******REMOVED*** Compliance Monitoring

Monitor ACGME compliance in real-time.

***REMOVED******REMOVED******REMOVED*** Compliance Dashboard

Navigate to **Compliance** to see:

- **Overall Score**: Program-wide compliance percentage
- **Active Violations**: Current issues requiring attention
- **Trends**: Compliance over time
- **By Person**: Individual compliance status

***REMOVED******REMOVED******REMOVED*** ACGME Rules Monitored

| Rule | Description | Threshold |
|------|-------------|-----------|
| **80-Hour Rule** | Weekly work hours | ≤80 hours/week avg |
| **1-in-7 Rule** | Day off frequency | 1 day off per 7 days |
| **24-Hour Limit** | Continuous duty | ≤24 hours continuous |
| **Supervision** | Faculty ratios | PGY-1: 1:2, PGY-2/3: 1:4 |

***REMOVED******REMOVED******REMOVED*** Violation Severity

| Level | Color | Response Required |
|-------|-------|------------------|
| **Critical** | Red | Immediate action |
| **High** | Orange | Same-day resolution |
| **Medium** | Yellow | Weekly review |
| **Low** | Blue | Informational |

***REMOVED******REMOVED******REMOVED*** Resolving Violations

1. Click on a violation in the dashboard
2. Review details and affected parties
3. Choose resolution:
   - **Reassign**: Move assignment to another person
   - **Reschedule**: Change timing
   - **Document Exception**: Record approved variance
4. Add resolution notes
5. Click **Resolve**

---

***REMOVED******REMOVED*** Exporting Data

***REMOVED******REMOVED******REMOVED*** Excel Export

Export schedules to Excel:

1. Go to **Schedule**
2. Click **Export** → **Excel**
3. Select:
   - Date range
   - Data to include
   - Formatting options
4. Click **Download**

***REMOVED******REMOVED******REMOVED*** Calendar Export (ICS)

Subscribe to schedules in your calendar app:

1. Go to **My Schedule** (or any person's profile)
2. Click **Calendar Sync**
3. Copy the ICS URL
4. Add to your calendar app:
   - **Google Calendar**: Other calendars → From URL
   - **Outlook**: Add calendar → From Internet
   - **Apple Calendar**: File → New Calendar Subscription

***REMOVED******REMOVED******REMOVED*** PDF Reports

Generate printable reports:

1. Navigate to desired view (schedule, compliance, etc.)
2. Click **Export** → **PDF**
3. Configure report options
4. Click **Generate**

---

***REMOVED******REMOVED*** Personal Dashboard

Access your personal view from **My Schedule**.

***REMOVED******REMOVED******REMOVED*** Your Schedule

- View your assigned blocks
- See upcoming shifts
- Check weekly hours
- Track compliance status

***REMOVED******REMOVED******REMOVED*** My Swaps

- Pending swap requests
- Incoming requests
- Swap history

***REMOVED******REMOVED******REMOVED*** Preferences

Set your scheduling preferences:

1. Click **Edit Preferences**
2. Configure:
   - Preferred shift times
   - Blocked dates
   - Rotation preferences
3. Click **Save**

Preferences are considered during schedule generation but not guaranteed.

***REMOVED******REMOVED******REMOVED*** Notifications

Manage your notification settings:

| Notification Type | Default |
|-------------------|---------|
| Schedule changes | Email + In-app |
| Swap requests | Email + In-app |
| Compliance alerts | Email |
| Certification expiry | Email |

---

***REMOVED******REMOVED*** Tips & Best Practices

***REMOVED******REMOVED******REMOVED*** For Coordinators

1. **Plan ahead**: Generate schedules 2-4 weeks in advance
2. **Review daily**: Check the daily manifest each morning
3. **Monitor compliance**: Review violations weekly
4. **Process swaps promptly**: Quick turnaround improves satisfaction
5. **Document exceptions**: Always note approved variances

***REMOVED******REMOVED******REMOVED*** For Residents

1. **Check your schedule daily**: Stay aware of upcoming assignments
2. **Request swaps early**: Earlier requests have more options
3. **Report absences promptly**: Helps coverage planning
4. **Keep certifications current**: System tracks expiration dates
5. **Use calendar sync**: Always have your schedule available

***REMOVED******REMOVED******REMOVED*** For Faculty

1. **Review supervision assignments**: Ensure you're prepared
2. **Update availability**: Keep your schedule current
3. **Approve swaps timely**: Check pending requests regularly
4. **Report concerns**: Flag potential issues early

---

***REMOVED******REMOVED*** Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `?` | Show help |
| `g d` | Go to Dashboard |
| `g s` | Go to Schedule |
| `g p` | Go to People |
| `n` | New (context-sensitive) |
| `e` | Edit (when item selected) |
| `Esc` | Close modal/cancel |

---

***REMOVED******REMOVED*** Getting Help

- **In-app help**: Click the `?` icon in any section
- **Documentation**: This wiki
- **Support**: Contact your system administrator
- **Issues**: Report bugs via GitHub Issues

---

***REMOVED******REMOVED*** Related Documentation

- [Getting Started](Getting-Started) - Installation guide
- [API Reference](API-Reference) - For integrations
- [Troubleshooting](Troubleshooting) - Common issues
