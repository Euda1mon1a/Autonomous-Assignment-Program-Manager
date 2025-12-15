***REMOVED*** Rotation Templates

Rotation Templates define the types of activities and rotations in your residency program. They specify capacity limits, supervision requirements, and scheduling constraints.

---

***REMOVED******REMOVED*** Accessing Templates

Click **Templates** in the main navigation bar.

**Required Role**: Coordinator or Admin

---

***REMOVED******REMOVED*** Templates Page Overview

```
+------------------------------------------------------------------------+
|  ROTATION TEMPLATES                                [+ New Template]    |
+------------------------------------------------------------------------+
|                                                                         |
|  Activity Type: [All Types v]                                          |
|                                                                         |
+------------------------------------------------------------------------+
|                                                                         |
|  +---------------------------+   +---------------------------+          |
|  | [Blue Banner]             |   | [Purple Banner]           |          |
|  | CLINIC                    |   | INPATIENT                 |          |
|  +---------------------------+   +---------------------------+          |
|  |                           |   |                           |          |
|  | Clinic AM                 |   | Inpatient Ward            |          |
|  | Abbreviation: CLN-AM      |   | Abbreviation: INP         |          |
|  | Max Residents: 4          |   | Max Residents: 3          |          |
|  | Supervision: 1:4          |   | Supervision: 1:2          |          |
|  |                           |   |                           |          |
|  | [Edit] [Delete]           |   | [Edit] [Delete]           |          |
|  +---------------------------+   +---------------------------+          |
|                                                                         |
|  +---------------------------+   +---------------------------+          |
|  | [Red Banner]              |   | [Gray Banner]             |          |
|  | PROCEDURE                 |   | CONFERENCE                |          |
|  +---------------------------+   +---------------------------+          |
|  |                           |   |                           |          |
|  | Endoscopy Suite           |   | Grand Rounds              |          |
|  | Abbreviation: ENDO        |   | Abbreviation: GR          |          |
|  | Max Residents: 2          |   | Max Residents: 20         |          |
|  | Supervision: 1:1          |   | Supervision: N/A          |          |
|  | Requires: GI specialty    |   |                           |          |
|  |                           |   |                           |          |
|  | [Edit] [Delete]           |   | [Edit] [Delete]           |          |
|  +---------------------------+   +---------------------------+          |
|                                                                         |
+------------------------------------------------------------------------+
```

---

***REMOVED******REMOVED*** Understanding Templates

***REMOVED******REMOVED******REMOVED*** What is a Template?

A template defines a **type of rotation or activity** in your program:
- Clinical rotations (clinic, inpatient, procedures)
- Educational activities (conferences, lectures)
- Call schedules
- Elective rotations

***REMOVED******REMOVED******REMOVED*** Why Templates Matter

Templates control:
- **Capacity**: How many residents can be assigned
- **Supervision**: Faculty-to-resident ratios
- **Requirements**: Who can be assigned (specialty requirements)
- **Scheduling**: Integration with the schedule generator

---

***REMOVED******REMOVED*** Template Card Details

***REMOVED******REMOVED******REMOVED*** Card Layout

```
+---------------------------+
| [Color Banner]            |
| ACTIVITY TYPE             |
+---------------------------+
|                           |
| Template Name             |
| Abbreviation: XXX         |
| Max Residents: N          |
| Supervision: 1:X          |
| Location: (if set)        |
| Requires: (if set)        |
|                           |
| [Edit] [Delete]           |
+---------------------------+
```

***REMOVED******REMOVED******REMOVED*** Activity Type Colors

| Color | Activity Type | Typical Use |
|-------|---------------|-------------|
| **Blue** | Clinic | Outpatient clinical sessions |
| **Purple** | Inpatient | Hospital ward rotations |
| **Red** | Procedure | Procedural rotations |
| **Gray** | Conference | Educational sessions |
| **Green** | Elective | Elective rotations |
| **Orange** | Call | On-call schedules |

---

***REMOVED******REMOVED*** Template Fields

***REMOVED******REMOVED******REMOVED*** Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| **Name** | Descriptive name | "Morning Clinic" |
| **Activity Type** | Category | Clinic, Inpatient, etc. |
| **Abbreviation** | Short code (2-6 chars) | "CLN-AM" |

***REMOVED******REMOVED******REMOVED*** Optional Fields

| Field | Description | Example |
|-------|-------------|---------|
| **Max Residents** | Capacity limit | 4 |
| **Supervision Required** | Needs faculty | Yes/No |
| **Max Supervision Ratio** | Faculty:Resident ratio | 1:4 |
| **Clinic Location** | Physical location | "Building A, Room 101" |
| **Requires Specialty** | Required training | "Gastroenterology" |

---

***REMOVED******REMOVED*** Creating a Template

***REMOVED******REMOVED******REMOVED*** Step-by-Step Guide

1. Click **+ New Template** button
2. Fill in the template form
3. Click **Create**

***REMOVED******REMOVED******REMOVED*** Template Form

```
+------------------------------------------+
|          Create New Template             |
+------------------------------------------+
|                                          |
|  Name *                                  |
|  [_________________________________]     |
|                                          |
|  Activity Type *                         |
|  [Clinic             v]                  |
|                                          |
|  Abbreviation *                          |
|  [_________________________________]     |
|                                          |
|  Max Residents                           |
|  [_________________________________]     |
|                                          |
|  Supervision Required                    |
|  [ ] Yes                                 |
|                                          |
|  Max Supervision Ratio                   |
|  [1:4                v]                  |
|                                          |
|  Clinic Location                         |
|  [_________________________________]     |
|                                          |
|  Requires Specialty                      |
|  [_________________________________]     |
|                                          |
|  [Cancel]              [Create]          |
+------------------------------------------+
```

***REMOVED******REMOVED******REMOVED*** Example: Creating a Clinic Template

1. **Name**: "Morning GI Clinic"
2. **Activity Type**: Clinic
3. **Abbreviation**: "GI-AM"
4. **Max Residents**: 3
5. **Supervision Required**: Yes
6. **Max Supervision Ratio**: 1:4
7. **Clinic Location**: "GI Clinic, 2nd Floor"
8. **Requires Specialty**: "Gastroenterology"

***REMOVED******REMOVED******REMOVED*** Example: Creating an Inpatient Template

1. **Name**: "Medicine Ward A"
2. **Activity Type**: Inpatient
3. **Abbreviation**: "MED-A"
4. **Max Residents**: 4
5. **Supervision Required**: Yes
6. **Max Supervision Ratio**: 1:2 (PGY-1 appropriate)

***REMOVED******REMOVED******REMOVED*** Example: Creating a Conference Template

1. **Name**: "Grand Rounds"
2. **Activity Type**: Conference
3. **Abbreviation**: "GR"
4. **Max Residents**: 30 (all residents)
5. **Supervision Required**: No

---

***REMOVED******REMOVED*** Editing a Template

***REMOVED******REMOVED******REMOVED*** When to Edit

- Capacity changes
- Location updates
- Supervision requirement changes
- Correcting errors

***REMOVED******REMOVED******REMOVED*** Edit Process

1. Find the template card
2. Click **Edit**
3. Modify fields as needed
4. Click **Save Changes**

**Note**: Changes affect future schedules. Existing assignments are not automatically updated.

---

***REMOVED******REMOVED*** Deleting a Template

***REMOVED******REMOVED******REMOVED*** Before Deleting

Check if the template is:
- Currently assigned in schedules
- Referenced by historical data

***REMOVED******REMOVED******REMOVED*** Delete Process

1. Click **Delete** on the template card
2. Confirm in the dialog
3. Template is removed

**Warning**: Deleting a template may affect schedule integrity.

---

***REMOVED******REMOVED*** Activity Types Explained

***REMOVED******REMOVED******REMOVED*** Clinic

Outpatient clinical sessions.

**Typical Settings**:
- Max Residents: 2-6
- Supervision: Usually required
- Ratio: 1:4 typical

**Examples**:
- Morning Clinic
- Afternoon Specialty Clinic
- Continuity Clinic

***REMOVED******REMOVED******REMOVED*** Inpatient

Hospital ward rotations.

**Typical Settings**:
- Max Residents: 2-5
- Supervision: Required
- Ratio: 1:2 for PGY-1, 1:4 for PGY-2/3

**Examples**:
- Medicine Ward
- ICU
- Step-Down Unit

***REMOVED******REMOVED******REMOVED*** Procedure

Hands-on procedural rotations.

**Typical Settings**:
- Max Residents: 1-3
- Supervision: Always required
- Ratio: 1:1 or 1:2

**Examples**:
- Endoscopy Suite
- Cardiac Cath Lab
- Procedure Clinic

***REMOVED******REMOVED******REMOVED*** Conference

Educational and academic sessions.

**Typical Settings**:
- Max Residents: High (all residents)
- Supervision: Not typically required

**Examples**:
- Grand Rounds
- Morbidity & Mortality
- Journal Club
- Didactic Sessions

***REMOVED******REMOVED******REMOVED*** Elective

Optional or selective rotations.

**Typical Settings**:
- Max Residents: 1-3
- Supervision: Varies
- Often specialty-specific

**Examples**:
- Research Elective
- Subspecialty Rotation
- Away Rotation

***REMOVED******REMOVED******REMOVED*** Call

On-call coverage schedules.

**Typical Settings**:
- Max Residents: Based on coverage needs
- Supervision: Required for PGY-1

**Examples**:
- Night Call
- Weekend Call
- Holiday Coverage

---

***REMOVED******REMOVED*** Supervision Ratios

***REMOVED******REMOVED******REMOVED*** ACGME Requirements

| PGY Level | Required Ratio |
|-----------|----------------|
| PGY-1 | 1 faculty : 2 residents |
| PGY-2/3 | 1 faculty : 4 residents |

***REMOVED******REMOVED******REMOVED*** Setting Appropriate Ratios

| Activity Type | Recommended Ratio |
|---------------|-------------------|
| Procedure | 1:1 or 1:2 |
| Inpatient (PGY-1) | 1:2 |
| Inpatient (PGY-2/3) | 1:4 |
| Clinic | 1:4 |
| Conference | N/A |

---

***REMOVED******REMOVED*** Best Practices

***REMOVED******REMOVED******REMOVED*** Naming Conventions

Use clear, consistent names:
- Include time of day if relevant: "Morning Clinic", "Afternoon Clinic"
- Include location if multiple: "GI Clinic North", "GI Clinic South"
- Include day if specific: "Tuesday Procedure Day"

***REMOVED******REMOVED******REMOVED*** Abbreviations

Keep abbreviations:
- Short (2-6 characters)
- Unique across templates
- Recognizable on schedules

**Good Examples**: CLN, INP, ENDO, GR, CALL
**Poor Examples**: C, CLIN-MORNING-GASTRO, X

***REMOVED******REMOVED******REMOVED*** Capacity Planning

Set Max Residents based on:
- Physical space capacity
- Supervision availability
- Educational effectiveness
- Patient volume

***REMOVED******REMOVED******REMOVED*** Regular Review

Quarterly, review templates for:
- Accuracy of settings
- Unused templates (consider removal)
- New rotation needs

---

***REMOVED******REMOVED*** Filtering Templates

***REMOVED******REMOVED******REMOVED*** By Activity Type

Use the dropdown to filter:
- **All Types**: Show everything
- **Clinic**: Only clinic templates
- **Inpatient**: Only inpatient templates
- Etc.

---

***REMOVED******REMOVED*** Troubleshooting

| Issue | Solution |
|-------|----------|
| Can't create template | Check required fields are filled |
| Abbreviation error | Must be unique; try different abbreviation |
| Template not showing in schedule | Verify it's assigned to a block |
| Supervision ratio error | Format should be "1:X" (e.g., "1:4") |

---

***REMOVED******REMOVED*** Related Guides

- [Getting Started](getting-started.md) - Basic navigation
- [Schedule Generation](schedule-generation.md) - Using templates in schedules
- [Compliance](compliance.md) - Supervision ratio monitoring
- [Common Workflows](common-workflows.md) - Template setup examples

---

*Well-defined templates are the building blocks of compliant schedules.*
