***REMOVED*** Absence Management

The Absences page allows you to track all types of time off for residents and faculty, including vacation, medical leave, military deployments, and more.

---

***REMOVED******REMOVED*** Accessing Absence Management

Click **Absences** in the main navigation bar.

**Required Role**: Coordinator or Admin

---

***REMOVED******REMOVED*** Absences Page Overview

```
+------------------------------------------------------------------------+
|  ABSENCES                                          [+ Add Absence]     |
+------------------------------------------------------------------------+
|                                                                         |
|  View: [Calendar] [List]     Type: [All Types v]     Month: [< Jan >]  |
|                                                                         |
+------------------------------------------------------------------------+
|                                                                         |
|  CALENDAR VIEW                                                         |
|  +------------------------------------------------------------------+  |
|  |  Sun    Mon    Tue    Wed    Thu    Fri    Sat                   |  |
|  +------------------------------------------------------------------+  |
|  |         1      2      3      4      5      6                     |  |
|  |                [VAC]                                             |  |
|  |                Smith                                             |  |
|  +------------------------------------------------------------------+  |
|  |  7      8      9      10     11     12     13                    |  |
|  |  [VAC]  [VAC]  [VAC]  [VAC]                                      |  |
|  |  Smith  Smith  Smith  Smith                                      |  |
|  +------------------------------------------------------------------+  |
|  |  14     15     16     17     18     19     20                    |  |
|  |         [TDY]  [TDY]  [TDY]  [TDY]  [TDY]                        |  |
|  |         Jones  Jones  Jones  Jones  Jones                        |  |
|  +------------------------------------------------------------------+  |
|                                                                         |
+------------------------------------------------------------------------+
```

---

***REMOVED******REMOVED*** View Modes

***REMOVED******REMOVED******REMOVED*** Calendar View

Visual month calendar showing absences as colored blocks.

**Features**:
- Month-at-a-glance overview
- Color-coded by absence type
- Click on absence to view/edit
- Navigate months with arrows

***REMOVED******REMOVED******REMOVED*** List View

Table format with detailed information.

```
+------------------------------------------------------------------------+
|  LIST VIEW                                                              |
+------------------------------------------------------------------------+
|  Person       | Type       | Start    | End      | Notes              |
+------------------------------------------------------------------------+
|  Dr. Smith    | Vacation   | Jan 2    | Jan 10   | Annual leave       |
|  Dr. Jones    | TDY        | Jan 15   | Jan 19   | Training at Ft Sam |
|  Dr. Brown    | Conference | Jan 22   | Jan 24   | AGA Meeting        |
|  Dr. Davis    | Medical    | Jan 5    | Jan 5    | Sick day           |
+------------------------------------------------------------------------+
```

**List View Columns**:
- **Person**: Name of resident/faculty
- **Type**: Absence category
- **Start**: Start date
- **End**: End date
- **Notes**: Additional information
- **Actions**: Edit/Delete buttons

---

***REMOVED******REMOVED*** Absence Types

***REMOVED******REMOVED******REMOVED*** Available Types

| Type | Icon | Description | Use For |
|------|------|-------------|---------|
| **Vacation** | Palm tree | Planned time off | Annual leave, PTO |
| **Medical** | Cross | Health-related | Sick days, appointments |
| **Deployment** | Star | Military deployment | Active duty orders |
| **TDY** | Briefcase | Temporary Duty | Military training, assignments |
| **Conference** | Airplane | Professional development | CME, medical meetings |
| **Family Emergency** | Heart | Personal matters | Family emergencies |

***REMOVED******REMOVED******REMOVED*** Type-Specific Fields

***REMOVED******REMOVED******REMOVED******REMOVED*** Standard Absences (Vacation, Medical, Conference, Family Emergency)

- Person
- Type
- Start Date
- End Date
- Notes

***REMOVED******REMOVED******REMOVED******REMOVED*** Military Absences (Deployment, TDY)

Additional fields:
- **Deployment Orders**: Order number/reference
- **TDY Location**: Where assigned (for TDY)
- **Is Blocking**: Completely blocks scheduling

---

***REMOVED******REMOVED*** Adding an Absence

***REMOVED******REMOVED******REMOVED*** Step-by-Step Guide

1. Click **+ Add Absence** button
2. Fill in the absence form
3. Click **Save**

***REMOVED******REMOVED******REMOVED*** Absence Form

```
+------------------------------------------+
|            Add New Absence               |
+------------------------------------------+
|                                          |
|  Person *                                |
|  [Select person...            v]         |
|                                          |
|  Absence Type *                          |
|  [Vacation                    v]         |
|                                          |
|  Start Date *                            |
|  [____/____/________]                    |
|                                          |
|  End Date *                              |
|  [____/____/________]                    |
|                                          |
|  Notes                                   |
|  [_________________________________]     |
|  [_________________________________]     |
|                                          |
|  --- Military Absences Only ---         |
|                                          |
|  Deployment Orders                       |
|  [_________________________________]     |
|                                          |
|  TDY Location                            |
|  [_________________________________]     |
|                                          |
|  Is Blocking  [ ]                        |
|                                          |
|  [Cancel]              [Save Absence]    |
+------------------------------------------+
```

***REMOVED******REMOVED******REMOVED*** Example: Adding Vacation

1. Click **+ Add Absence**
2. **Person**: Dr. Jane Smith
3. **Type**: Vacation
4. **Start Date**: 2024-02-15
5. **End Date**: 2024-02-22
6. **Notes**: "Annual ski trip - approved 12/1"
7. Click **Save**

***REMOVED******REMOVED******REMOVED*** Example: Adding Deployment

1. Click **+ Add Absence**
2. **Person**: Dr. Michael Brown
3. **Type**: Deployment
4. **Start Date**: 2024-03-01
5. **End Date**: 2024-06-30
6. **Deployment Orders**: "Order ***REMOVED***12345-2024"
7. **Is Blocking**: Checked
8. **Notes**: "4-month deployment to Kuwait"
9. Click **Save**

***REMOVED******REMOVED******REMOVED*** Example: Adding TDY

1. Click **+ Add Absence**
2. **Person**: Dr. Sarah Jones
3. **Type**: TDY
4. **Start Date**: 2024-02-01
5. **End Date**: 2024-02-05
6. **TDY Location**: "Ft. Sam Houston, TX"
7. **Notes**: "Leadership training course"
8. Click **Save**

---

***REMOVED******REMOVED*** Editing an Absence

***REMOVED******REMOVED******REMOVED*** From Calendar View

1. Click on the absence block
2. The edit dialog opens
3. Modify fields
4. Click **Save Changes**

***REMOVED******REMOVED******REMOVED*** From List View

1. Find the absence row
2. Click **Edit** button
3. Modify fields
4. Click **Save Changes**

---

***REMOVED******REMOVED*** Deleting an Absence

***REMOVED******REMOVED******REMOVED*** Process

1. Find the absence (calendar or list)
2. Click **Delete** (or open and delete)
3. Confirm deletion

**Note**: Deleting an absence may affect schedule generation. Regenerate affected periods after deleting.

---

***REMOVED******REMOVED*** Filtering Absences

***REMOVED******REMOVED******REMOVED*** By Type

Use the **Type** dropdown:
- **All Types**: Show all absences
- **Vacation**: Only vacation
- **Medical**: Only medical/sick
- **Deployment**: Only deployments
- **TDY**: Only TDY
- **Conference**: Only conferences
- **Family Emergency**: Only emergencies

***REMOVED******REMOVED******REMOVED*** By Month

Use the month navigation arrows to view different months.

***REMOVED******REMOVED******REMOVED*** By Person (List View)

Click column headers to sort by person.

---

***REMOVED******REMOVED*** Impact on Scheduling

***REMOVED******REMOVED******REMOVED*** How Absences Affect Schedules

When you record an absence:
1. The person is marked **unavailable** for those dates
2. Schedule generation will **not assign** them during the absence
3. Existing assignments for those dates should be **reviewed**

***REMOVED******REMOVED******REMOVED*** Blocking vs. Non-Blocking

| Type | Default Behavior |
|------|------------------|
| **Blocking** | Person completely unavailable |
| **Non-Blocking** | Person partially available (reduced hours) |

Most absences are blocking by default.

***REMOVED******REMOVED******REMOVED*** Regenerating After Absences

When adding last-minute absences:
1. Add the absence
2. Check Dashboard for coverage gaps
3. Regenerate schedule for affected period if needed
4. Verify Compliance

---

***REMOVED******REMOVED*** Calendar View Features

***REMOVED******REMOVED******REMOVED*** Color Coding

Absences are color-coded by type:

| Type | Color |
|------|-------|
| Vacation | Blue |
| Medical | Red |
| Deployment | Gold/Yellow |
| TDY | Purple |
| Conference | Green |
| Family Emergency | Orange |

***REMOVED******REMOVED******REMOVED*** Multi-Day Absences

Multi-day absences span across calendar days with a continuous bar.

***REMOVED******REMOVED******REMOVED*** Overlapping Absences

When multiple people are out on the same day, each shows as a separate block stacked vertically.

***REMOVED******REMOVED******REMOVED*** Month Navigation

```
     [<]  January 2024  [>]
```

- Click `<` for previous month
- Click `>` for next month
- Current month is highlighted

---

***REMOVED******REMOVED*** Best Practices

***REMOVED******REMOVED******REMOVED*** Early Entry

Enter known absences as soon as they're approved:
- Vacation requests
- Conference attendance
- Planned medical (surgery, appointments)

This helps with:
- Better schedule generation
- Coverage planning
- Compliance management

***REMOVED******REMOVED******REMOVED*** Complete Notes

Include useful information in notes:
- Approval reference/date
- Contact information (for emergencies)
- Special arrangements

**Example Notes**:
- "Approved by Dr. Director 1/15/24"
- "Can be reached at personal cell for emergencies"
- "Covering physician: Dr. Brown"

***REMOVED******REMOVED******REMOVED*** Military Absence Documentation

For deployments and TDY:
- Always include order numbers
- Specify locations
- Note if partial availability exists

***REMOVED******REMOVED******REMOVED*** Regular Audit

Monthly, review absences for:
- Accuracy of dates
- Missing approved absences
- Coverage planning for upcoming absences

---

***REMOVED******REMOVED*** Common Scenarios

***REMOVED******REMOVED******REMOVED*** Recording Annual Leave

**Process**:
1. Receive approved leave request
2. Add Vacation absence
3. Include approval reference in notes
4. Verify coverage for the dates

***REMOVED******REMOVED******REMOVED*** Handling Sick Calls

**Same-day sick call**:
1. Add Medical absence (start = end = today)
2. Note: "Called in sick [time]"
3. Check coverage impact
4. Consider regenerating if critical gaps

***REMOVED******REMOVED******REMOVED*** Planning for Deployments

**When orders received**:
1. Add Deployment absence with full date range
2. Enter order number
3. Mark as blocking
4. Immediately regenerate affected schedules
5. Review compliance for extended absence impact

***REMOVED******REMOVED******REMOVED*** Conference Season

**Multiple attendees**:
1. Add Conference absence for each attendee
2. Note conference name
3. Verify adequate coverage remains
4. Consider limiting same-conference attendance

---

***REMOVED******REMOVED*** Troubleshooting

| Issue | Solution |
|-------|----------|
| Can't find person in dropdown | Check People page - person must exist |
| Date picker not working | Try different browser; ensure JavaScript enabled |
| Absence not showing on calendar | Check month navigation; verify save completed |
| Can't delete absence | May need Coordinator/Admin role |

---

***REMOVED******REMOVED*** Export Options

***REMOVED******REMOVED******REMOVED*** Exporting Absence Data

From the List view:
1. Click **Export** dropdown
2. Select format:
   - **CSV**: Spreadsheet format
   - **JSON**: Data format

***REMOVED******REMOVED******REMOVED*** Use Cases for Export

- Reporting to GME office
- Integration with HR systems
- Backup/archival

---

***REMOVED******REMOVED*** Related Guides

- [Getting Started](getting-started.md) - Basic navigation
- [People Management](people-management.md) - Managing residents and faculty
- [Schedule Generation](schedule-generation.md) - Creating schedules considering absences
- [Compliance](compliance.md) - How absences affect compliance
- [Common Workflows](common-workflows.md) - Deployment handling workflow

---

*Accurate absence tracking ensures reliable schedules and compliant coverage.*
