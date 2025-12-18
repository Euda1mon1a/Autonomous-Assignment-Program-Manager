# User Guide

This guide explains how to use the Residency Scheduler application for managing medical residency schedules.

---

## Table of Contents

1. [Dashboard Overview](#dashboard-overview)
2. [Managing People](#managing-people)
3. [Schedule Management](#schedule-management)
4. [Rotation Templates](#rotation-templates)
5. [Absences & Time Off](#absences--time-off)
6. [Swap Marketplace](#swap-marketplace)
7. [Compliance Monitoring](#compliance-monitoring)
8. [Exporting Data](#exporting-data)
9. [Personal Dashboard](#personal-dashboard)

---

## Dashboard Overview

The main dashboard provides a quick overview of your residency program's scheduling status.

### Dashboard Widgets

| Widget | Description |
|--------|-------------|
| **Compliance Status** | Current ACGME compliance indicators |
| **Today's Coverage** | Active assignments for today |
| **Upcoming Absences** | Scheduled time off in the next 7 days |
| **Pending Swaps** | Swap requests awaiting action |
| **Alerts** | Critical violations requiring attention |

### Navigation

The sidebar provides access to all major sections:

- **Dashboard** - Home page with overview
- **Schedule** - View and manage schedules
- **People** - Manage residents and faculty
- **Templates** - Rotation template configuration
- **Absences** - Time-off management
- **Compliance** - ACGME compliance monitoring
- **Settings** - System configuration (Admin only)

---

## Managing People

### Adding a Person

1. Navigate to **People**
2. Click **Add Person**
3. Fill in the required fields:
   - **Name**: Full name
   - **Email**: Contact email
   - **Role**: Resident or Faculty
   - **PGY Level**: For residents (PGY-1, PGY-2, PGY-3)
   - **Specialty**: Primary specialty
4. Click **Save**

### Bulk Import

Import multiple people from Excel:

1. Go to **Settings** → **Import Data**
2. Download the **People Template**
3. Fill in your data following the template format
4. Upload the completed file
5. Review the import preview
6. Click **Confirm Import**

### Person Profiles

Click any person to view their profile:

- **Overview**: Contact info, role, PGY level
- **Schedule**: Their assigned blocks
- **Absences**: Scheduled time off
- **Certifications**: BLS, ACLS, PALS status
- **Credentials**: Procedure qualifications
- **History**: Assignment history

### Managing Certifications

Track required certifications:

1. Open a person's profile
2. Click **Certifications** tab
3. Click **Add Certification**
4. Select type (BLS, ACLS, PALS, etc.)
5. Enter expiration date
6. Upload certificate document (optional)

The system automatically alerts before certifications expire.

---

## Schedule Management

### Viewing Schedules

Access schedules from **Schedule** in the navigation:

#### Calendar View
- Monthly/weekly/daily views
- Color-coded by rotation type
- Click any assignment for details

#### Timeline View
- Gantt-style visualization
- See all residents at once
- Identify coverage gaps

#### Daily Manifest
- Today's assignments at a glance
- Quick status overview
- Print-friendly format

### Generating a Schedule

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

### Manual Adjustments

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

### Emergency Coverage

Handle unexpected absences:

1. Go to **Schedule** → **Emergency Coverage**
2. Select the affected assignment
3. Enter reason (medical, deployment, etc.)
4. System suggests available replacements
5. Select a replacement or enter manually
6. Notifications sent automatically

---

## Rotation Templates

Templates define reusable scheduling patterns.

### Creating a Template

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

### Template Types

| Type | Description |
|------|-------------|
| **Clinical** | Patient care rotations |
| **Administrative** | Non-clinical duties |
| **Call** | On-call assignments |
| **Elective** | Optional rotations |
| **Vacation** | Time-off blocks |

### Editing Templates

1. Click on a template
2. Modify fields as needed
3. Changes apply to future schedules
4. Existing assignments unchanged

---

## Absences & Time Off

### Recording an Absence

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

### Absence Types

| Type | Description |
|------|-------------|
| **Vacation** | Planned time off |
| **Medical** | Sick leave |
| **Deployment** | Military deployment |
| **TDY** | Temporary duty assignment |
| **Conference** | Educational conference |
| **Family Emergency** | Personal emergency |
| **Bereavement** | Loss of family member |

### Viewing Absences

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

## Swap Marketplace

The swap system allows residents to trade assignments.

### Requesting a Swap

1. Navigate to **Swap Marketplace**
2. Click **Request Swap**
3. Select:
   - **Your Assignment**: The block you want to trade
   - **Preferred Dates**: When you'd prefer to work
   - **Notes**: Additional context
4. Click **Submit Request**

### Auto-Matching

The system automatically finds compatible swaps using a 5-factor algorithm:

1. **Availability**: Both parties available
2. **Preferences**: Match preferences
3. **Specialization**: Required skills match
4. **PGY Balance**: Appropriate experience levels
5. **Coverage Impact**: Maintains adequate coverage

### Responding to Swap Requests

1. View incoming requests in your dashboard
2. Click **View Details** on a request
3. Review:
   - Assignment details
   - Impact on your schedule
   - Compliance status
4. Click **Accept** or **Decline**

### Swap Status

| Status | Description |
|--------|-------------|
| **Pending** | Awaiting response |
| **Matched** | Found potential match |
| **Accepted** | Both parties agreed |
| **Completed** | Swap executed |
| **Cancelled** | Request withdrawn |
| **Declined** | Request rejected |

---

## Compliance Monitoring

Monitor ACGME compliance in real-time.

### Compliance Dashboard

Navigate to **Compliance** to see:

- **Overall Score**: Program-wide compliance percentage
- **Active Violations**: Current issues requiring attention
- **Trends**: Compliance over time
- **By Person**: Individual compliance status

### ACGME Rules Monitored

| Rule | Description | Threshold |
|------|-------------|-----------|
| **80-Hour Rule** | Weekly work hours | ≤80 hours/week avg |
| **1-in-7 Rule** | Day off frequency | 1 day off per 7 days |
| **24-Hour Limit** | Continuous duty | ≤24 hours continuous |
| **Supervision** | Faculty ratios | PGY-1: 1:2, PGY-2/3: 1:4 |

### Violation Severity

| Level | Color | Response Required |
|-------|-------|------------------|
| **Critical** | Red | Immediate action |
| **High** | Orange | Same-day resolution |
| **Medium** | Yellow | Weekly review |
| **Low** | Blue | Informational |

### Resolving Violations

1. Click on a violation in the dashboard
2. Review details and affected parties
3. Choose resolution:
   - **Reassign**: Move assignment to another person
   - **Reschedule**: Change timing
   - **Document Exception**: Record approved variance
4. Add resolution notes
5. Click **Resolve**

---

## Exporting Data

### Excel Export

Export schedules to Excel:

1. Go to **Schedule**
2. Click **Export** → **Excel**
3. Select:
   - Date range
   - Data to include
   - Formatting options
4. Click **Download**

### Calendar Export (ICS)

Download your schedule as an ICS file for one-time import:

1. Go to **My Schedule** (or any person's profile)
2. Click **Calendar Sync** button
3. Select **ICS File Download**
4. Choose how many weeks ahead to include (4-52 weeks)
5. Click **Sync Now**
6. Import the downloaded `.ics` file into your calendar app

### WebCal Subscription (Live Updates)

Subscribe to a live-updating calendar feed that automatically syncs:

1. Go to **My Schedule**
2. Click **Calendar Sync** button
3. The system generates a secure subscription URL
4. Copy the `webcal://` URL provided
5. Add to your calendar app:

**Google Calendar:**
1. Open Google Calendar on desktop
2. Click "+" next to "Other calendars"
3. Select "From URL"
4. Paste the `webcal://` URL
5. Click "Add calendar"

**Apple Calendar (macOS/iOS):**
1. Open Calendar app
2. File → New Calendar Subscription (macOS) or
   Settings → Calendar → Accounts → Add Account → Other (iOS)
3. Paste the URL
4. Click "Subscribe"

**Microsoft Outlook:**
1. Open Outlook Calendar
2. Click "Add calendar" → "From Internet"
3. Paste the URL
4. Click "OK"

**Subscription Features:**
- Automatically refreshes every 15 minutes
- Shows assignments 6 months ahead
- Includes location, role, and notes
- Secure token-based authentication
- Can be revoked at any time from settings

### PDF Reports

Generate printable reports:

1. Navigate to desired view (schedule, compliance, etc.)
2. Click **Export** → **PDF**
3. Configure report options
4. Click **Generate**

---

## Personal Dashboard

Access your personal view from **My Schedule**.

### Your Schedule

- View your assigned blocks
- See upcoming shifts
- Check weekly hours
- Track compliance status

### My Swaps

- Pending swap requests
- Incoming requests
- Swap history

### Preferences

Set your scheduling preferences:

1. Click **Edit Preferences**
2. Configure:
   - Preferred shift times
   - Blocked dates
   - Rotation preferences
3. Click **Save**

Preferences are considered during schedule generation but not guaranteed.

### Notifications

Manage your notification settings:

| Notification Type | Default |
|-------------------|---------|
| Schedule changes | Email + In-app |
| Swap requests | Email + In-app |
| Compliance alerts | Email |
| Certification expiry | Email |

---

## Tips & Best Practices

### For Coordinators

1. **Plan ahead**: Generate schedules 2-4 weeks in advance
2. **Review daily**: Check the daily manifest each morning
3. **Monitor compliance**: Review violations weekly
4. **Process swaps promptly**: Quick turnaround improves satisfaction
5. **Document exceptions**: Always note approved variances

### For Residents

1. **Check your schedule daily**: Stay aware of upcoming assignments
2. **Request swaps early**: Earlier requests have more options
3. **Report absences promptly**: Helps coverage planning
4. **Keep certifications current**: System tracks expiration dates
5. **Use calendar sync**: Always have your schedule available

### For Faculty

1. **Review supervision assignments**: Ensure you're prepared
2. **Update availability**: Keep your schedule current
3. **Approve swaps timely**: Check pending requests regularly
4. **Report concerns**: Flag potential issues early

---

## Keyboard Shortcuts

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

## Getting Help

- **In-app help**: Click the `?` icon in any section
- **Documentation**: This wiki
- **Support**: Contact your system administrator
- **Issues**: Report bugs via GitHub Issues

---

## Related Documentation

- [Getting Started](Getting-Started) - Installation guide
- [API Reference](API-Reference) - For integrations
- [Troubleshooting](Troubleshooting) - Common issues
