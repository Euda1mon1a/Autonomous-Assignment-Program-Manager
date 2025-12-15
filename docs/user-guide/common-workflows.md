# Common Workflows

This guide provides step-by-step instructions for common tasks in the Residency Scheduler. Each workflow is a complete procedure from start to finish.

---

## Table of Contents

1. [Starting a New Academic Year](#starting-a-new-academic-year)
2. [Monthly Schedule Generation](#monthly-schedule-generation)
3. [Handling Military Deployment](#handling-military-deployment)
4. [Managing TDY (Temporary Duty)](#managing-tdy-temporary-duty)
5. [Processing Vacation Requests](#processing-vacation-requests)
6. [Resolving Compliance Violations](#resolving-compliance-violations)
7. [Adding Mid-Year Residents](#adding-mid-year-residents)
8. [Emergency Coverage Situations](#emergency-coverage-situations)
9. [Preparing for ACGME Site Visit](#preparing-for-acgme-site-visit)
10. [End of Year Archival](#end-of-year-archival)

---

## Starting a New Academic Year

### Overview

Annual process typically performed in late June to prepare for the July 1 academic year start.

### Timeline

| Task | When | Duration |
|------|------|----------|
| Update settings | Late June | 30 min |
| Update residents | June 25-30 | 1-2 hours |
| Generate July schedule | June 28-30 | 1-2 hours |
| Final review | June 30 | 1 hour |

### Step-by-Step Procedure

#### Step 1: Update Academic Year Settings (Admin)

1. Go to **Settings**
2. Update **Start Date** to new year (e.g., July 1, 2025)
3. Update **End Date** to new year (e.g., June 30, 2026)
4. Review other settings
5. Click **Save Changes**

#### Step 2: Promote Existing Residents

1. Go to **People**
2. Filter by **Residents**
3. For each PGY-2 resident:
   - Click **Edit**
   - Change PGY Level to **3**
   - Click **Save**
4. For each PGY-1 resident:
   - Click **Edit**
   - Change PGY Level to **2**
   - Click **Save**

#### Step 3: Remove Graduated Residents

1. Filter by **PGY-3** (now promoted, actually graduating)
2. For each graduating resident:
   - Verify no future assignments
   - Click **Delete**
   - Confirm deletion

#### Step 4: Add New Interns

1. Click **+ Add Person**
2. For each incoming intern:
   - Enter **Name**
   - Select **Type**: Resident
   - Set **PGY Level**: 1
   - Enter **Email**
   - Click **Save**
3. Repeat for all new interns

#### Step 5: Review Templates

1. Go to **Templates**
2. Verify all templates are current
3. Update any capacity or supervision changes
4. Add new templates if needed

#### Step 6: Enter Known Absences

1. Go to **Absences**
2. Add any pre-approved vacations for July
3. Add known conference attendance
4. Add any military obligations

#### Step 7: Generate First Block Schedule

1. Go to **Dashboard**
2. Click **Generate Schedule**
3. Set dates: July 1 - July 28
4. Select **Algorithm**: CP-SAT (for optimal start)
5. Click **Generate**

#### Step 8: Review and Verify

1. Check **Compliance** page - resolve any violations
2. Review Dashboard for coverage gaps
3. Export and review the schedule
4. Make manual adjustments if needed

#### Step 9: Distribute Schedule

1. Click **Export Excel**
2. Review exported file
3. Email to all residents and faculty
4. Post to shared location

---

## Monthly Schedule Generation

### Overview

Standard process for generating each month's schedule.

### Step-by-Step Procedure

#### Step 1: Verify Data

1. Go to **People** - verify roster is current
2. Go to **Absences** - verify all time off is recorded
3. Go to **Templates** - verify templates are current

#### Step 2: Generate Schedule

1. Go to **Dashboard**
2. Click **Generate Schedule**
3. Set **Start Date**: First day of month
4. Set **End Date**: Last day of month
5. Select **Algorithm**: Min Conflicts (standard) or CP-SAT (optimal)
6. Click **Generate**

#### Step 3: Check Compliance

1. Go to **Compliance**
2. Navigate to the generated month
3. Review all three compliance cards
4. If violations exist:
   - Note affected residents
   - Proceed to violation resolution

#### Step 4: Review Schedule

1. Return to **Dashboard**
2. Review schedule summary
3. Check coverage rate
4. Identify any gaps

#### Step 5: Make Adjustments (if needed)

1. Address any coverage gaps
2. Consider manual swaps for preferences
3. Re-check compliance after changes

#### Step 6: Export and Distribute

1. Click **Export Excel**
2. Save with descriptive filename
3. Review final schedule
4. Distribute to residents and faculty

---

## Handling Military Deployment

### Overview

Process for managing a resident's military deployment, which typically involves extended absence.

### Step-by-Step Procedure

#### Step 1: Receive Deployment Orders

1. Obtain copy of deployment orders
2. Note key information:
   - Resident name
   - Start date
   - End date (or estimated duration)
   - Order number

#### Step 2: Record the Absence

1. Go to **Absences**
2. Click **+ Add Absence**
3. Fill in details:
   - **Person**: [Select resident]
   - **Type**: Deployment
   - **Start Date**: Deployment start
   - **End Date**: Deployment end
   - **Deployment Orders**: Order number
   - **Is Blocking**: Checked
   - **Notes**: Additional details
4. Click **Save**

#### Step 3: Assess Impact

1. Go to **Dashboard**
2. Review coverage for deployment period
3. Go to **Compliance**
4. Check if violations will occur

#### Step 4: Regenerate Affected Schedules

1. Click **Generate Schedule**
2. Set date range covering deployment
3. Select algorithm (recommend CP-SAT)
4. Click **Generate**

#### Step 5: Review New Schedule

1. Check **Compliance**
2. Verify coverage maintained
3. Check workload distribution among remaining residents

#### Step 6: Communicate Changes

1. Export updated schedule
2. Notify affected residents
3. Document in program records

#### Step 7: Plan for Return

1. Add calendar reminder for deployment end
2. When return date confirmed:
   - Update absence end date if needed
   - Plan reintegration into schedule

---

## Managing TDY (Temporary Duty)

### Overview

TDY (Temporary Duty) assignments are typically shorter military obligations away from the primary duty station.

### Step-by-Step Procedure

#### Step 1: Receive TDY Information

1. Obtain TDY orders or notification
2. Note:
   - Resident name
   - TDY dates
   - Location
   - Purpose

#### Step 2: Record the Absence

1. Go to **Absences**
2. Click **+ Add Absence**
3. Fill in:
   - **Person**: [Select resident]
   - **Type**: TDY
   - **Start Date**: TDY start
   - **End Date**: TDY end
   - **TDY Location**: "Fort Sam Houston, TX" (example)
   - **Notes**: Purpose of TDY
4. Click **Save**

#### Step 3: Check Schedule Impact

1. Go to **Dashboard**
2. Review assignments for TDY dates
3. Identify coverage needs

#### Step 4: Adjust Schedule

Option A - Manual adjustment:
1. Swap assignments with other residents
2. Verify compliance maintained

Option B - Regenerate:
1. Generate schedule for affected period
2. Review and verify

#### Step 5: Communicate

1. Notify affected parties
2. Update shared schedule

---

## Processing Vacation Requests

### Overview

Standard process for approving and recording vacation requests.

### Step-by-Step Procedure

#### Step 1: Receive Request

1. Resident submits vacation request
2. Review for:
   - Dates requested
   - Program policy compliance (advance notice, etc.)
   - Coverage feasibility

#### Step 2: Check Feasibility

1. Go to **Absences**
2. Check existing absences for requested dates
3. Determine if coverage is possible

#### Step 3: Approve/Deny

Based on feasibility:
- **Approve**: Proceed to Step 4
- **Deny**: Communicate to resident with reason

#### Step 4: Record Approved Absence

1. Click **+ Add Absence**
2. Fill in:
   - **Person**: [Resident name]
   - **Type**: Vacation
   - **Start Date**: First day of vacation
   - **End Date**: Last day of vacation
   - **Notes**: "Approved [date], request #[number]"
3. Click **Save**

#### Step 5: Update Schedule (if needed)

If schedule for vacation period already exists:
1. Regenerate for affected dates
2. Or manually reassign duties

#### Step 6: Confirm with Resident

1. Notify resident of approval
2. Remind them schedule will reflect absence

---

## Resolving Compliance Violations

### Overview

Process for identifying and resolving ACGME compliance violations.

### Types of Violations

| Violation | Severity | Typical Resolution |
|-----------|----------|-------------------|
| 80-hour exceeded | Critical | Reduce hours |
| 1-in-7 missing | High | Add day off |
| Supervision ratio | Medium | Add faculty |

### Step-by-Step: 80-Hour Violation

#### Step 1: Identify the Violation

1. Go to **Compliance**
2. Find the violation in the list
3. Note the affected resident and period

#### Step 2: Analyze the Schedule

1. Calculate current hours for 4-week period
2. Identify which days have heavy assignments
3. Determine hours to reduce

#### Step 3: Reduce Hours

Options:
- Remove non-essential assignments
- Swap with less-loaded resident
- Add an off day
- Change to lighter rotation

#### Step 4: Verify Resolution

1. Return to **Compliance**
2. Verify 80-hour card shows compliant
3. Check no new violations created

### Step-by-Step: 1-in-7 Violation

#### Step 1: Identify the 7-Day Period

1. Go to **Compliance**
2. Note which 7-day window lacks a day off
3. Identify the affected resident

#### Step 2: Find a Day to Give Off

1. Review schedule for that 7-day window
2. Identify which day can be made an off day
3. Consider coverage needs

#### Step 3: Modify Schedule

1. Remove assignment for the chosen day
2. Reassign duties to another resident
3. Or regenerate for the period

#### Step 4: Verify Resolution

1. Check **Compliance** page
2. Verify 1-in-7 card shows compliant
3. Ensure new assignment doesn't create violations elsewhere

### Step-by-Step: Supervision Violation

#### Step 1: Identify the Violation

1. Note which rotation/time has violation
2. Identify current resident count
3. Identify current faculty count

#### Step 2: Calculate Required Faculty

```
PGY-1 residents: [count] ÷ 2 = [required]
PGY-2/3 residents: [count] ÷ 4 = [required]
Total required = max of above
```

#### Step 3: Add Faculty Coverage

1. Assign additional faculty to the rotation
2. Or reduce resident count on rotation
3. Or split rotation into smaller groups

#### Step 4: Verify Resolution

1. Check **Compliance** page
2. Verify supervision card shows compliant

---

## Adding Mid-Year Residents

### Overview

Process for adding residents who join mid-academic year (transfers, military rotations, etc.).

### Step-by-Step Procedure

#### Step 1: Gather Information

1. Obtain resident details:
   - Name
   - PGY level
   - Start date
   - Email
   - Any restrictions

#### Step 2: Add the Person

1. Go to **People**
2. Click **+ Add Person**
3. Enter all information
4. Click **Save**

#### Step 3: Enter Known Absences

If resident has pre-approved time off:
1. Go to **Absences**
2. Add any known absences

#### Step 4: Integrate into Schedule

Option A - Regenerate upcoming schedules:
1. Generate schedule from their start date
2. They'll be included automatically

Option B - Manual addition:
1. Assign them to specific rotations
2. Ensure compliance is maintained

#### Step 5: Orientation

1. Provide login credentials
2. Show them the system
3. Point to this user guide

---

## Emergency Coverage Situations

### Overview

Handling same-day or short-notice absence situations.

### Step-by-Step Procedure

#### Step 1: Receive Emergency Notice

Document:
- Who is out
- Reason (for absence record)
- Duration
- Their current assignments

#### Step 2: Record the Absence

1. Go to **Absences**
2. Click **+ Add Absence**
3. Record with appropriate type
4. Note urgency in comments

#### Step 3: Identify Coverage Needs

1. Check what assignments they had
2. Determine priority (patient care first)

#### Step 4: Find Coverage

Options:
1. Call available residents
2. Check who has lighter days
3. Use faculty if needed
4. Check call schedule for backup

#### Step 5: Update Schedule

1. Make manual assignment changes
2. Or quick regenerate for affected days

#### Step 6: Communicate

1. Notify affected staff
2. Update shared schedule
3. Document for records

---

## Preparing for ACGME Site Visit

### Overview

Steps to prepare documentation and verify compliance before accreditation review.

### Step-by-Step Procedure

#### Step 1: Compliance Audit

1. Go to **Compliance**
2. Review each month of the review period
3. Document any violations and resolutions
4. Screenshot compliance status for each month

#### Step 2: Generate Reports

1. Export schedules for review period
2. Export people list
3. Export absence records
4. Organize by month/quarter

#### Step 3: Verify Settings

1. Go to **Settings** (Admin)
2. Verify ACGME parameters match requirements
3. Document current settings

#### Step 4: Prepare Documentation Binder

Contents:
- Compliance reports by month
- Schedule exports
- Exception documentation
- Corrective action records

#### Step 5: Review with Leadership

1. Review findings with program director
2. Address any concerns
3. Prepare responses for potential questions

---

## End of Year Archival

### Overview

Process for archiving the completed academic year data.

### Step-by-Step Procedure

#### Step 1: Export All Data

1. Export schedules for entire year (by month or block)
2. Export final people list
3. Export all absences

#### Step 2: Generate Summary Reports

1. Compliance summary by month
2. Hour logs by resident
3. Rotation completion records

#### Step 3: Archive Files

1. Create dated archive folder
2. Store all exports
3. Include compliance screenshots
4. Store securely per policy

#### Step 4: Backup System Data

Contact IT for:
- Database backup
- System state snapshot

#### Step 5: Prepare for New Year

1. Follow "Starting a New Academic Year" workflow
2. Reference archived data as needed

---

## Quick Reference Table

| Workflow | Frequency | Role Required |
|----------|-----------|---------------|
| New Academic Year | Annually | Admin |
| Monthly Schedule | Monthly | Coordinator |
| Deployment | As needed | Coordinator |
| TDY | As needed | Coordinator |
| Vacation Request | Ongoing | Coordinator |
| Compliance Resolution | As needed | Coordinator |
| Mid-Year Addition | As needed | Coordinator |
| Emergency Coverage | As needed | Coordinator |
| ACGME Prep | Periodically | Admin |
| Year-End Archival | Annually | Admin |

---

## Related Guides

- [Getting Started](getting-started.md) - Basic operations
- [Dashboard](dashboard.md) - Quick actions
- [Compliance](compliance.md) - Violation details
- [Absences](absences.md) - Absence management
- [Schedule Generation](schedule-generation.md) - Generation options
- [Settings](settings.md) - System configuration

---

*Following standardized workflows ensures consistent, compliant operations.*
