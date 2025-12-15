# People Management

The People page allows you to manage all residents and faculty in your program. This guide covers viewing, adding, editing, and removing personnel.

---

## Accessing People Management

Click **People** in the main navigation bar.

**Required Role**: Coordinator or Admin

---

## People Page Overview

```
+------------------------------------------------------------------------+
|  PEOPLE                                            [+ Add Person]      |
+------------------------------------------------------------------------+
|                                                                         |
|  Filter: [All] [Residents] [Faculty]     PGY Level: [All v]            |
|                                                                         |
+------------------------------------------------------------------------+
|                                                                         |
|  +---------------------------+   +---------------------------+          |
|  | [Graduation Cap Icon]    |   | [User Icon]               |          |
|  |                          |   |                           |          |
|  | Dr. Jane Smith           |   | Dr. Robert Johnson        |          |
|  | Resident - PGY-1         |   | Faculty                   |          |
|  | jsmith@hospital.org      |   | Gastroenterology          |          |
|  |                          |   | rjohnson@hospital.org     |          |
|  | [Edit] [Delete]          |   | [Edit] [Delete]           |          |
|  +---------------------------+   +---------------------------+          |
|                                                                         |
|  +---------------------------+   +---------------------------+          |
|  | [Graduation Cap Icon]    |   | [Graduation Cap Icon]     |          |
|  |                          |   |                           |          |
|  | Dr. Michael Brown        |   | Dr. Sarah Davis           |          |
|  | Resident - PGY-2         |   | Resident - PGY-3          |          |
|  | mbrown@hospital.org      |   | sdavis@hospital.org       |          |
|  |                          |   |                           |          |
|  | [Edit] [Delete]          |   | [Edit] [Delete]           |          |
|  +---------------------------+   +---------------------------+          |
|                                                                         |
+------------------------------------------------------------------------+
```

---

## Viewing People

### Person Cards

Each person is displayed as a card showing:

| Element | Description |
|---------|-------------|
| **Icon** | Graduation cap (resident) or user icon (faculty) |
| **Name** | Full name with title |
| **Type/Level** | "Resident - PGY-X" or "Faculty" |
| **Specialty** | Medical specialty (if assigned) |
| **Email** | Contact email address |
| **Actions** | Edit and Delete buttons |

### Filtering Options

#### By Type

| Filter | Shows |
|--------|-------|
| **All** | Everyone in the system |
| **Residents** | Only residents (all PGY levels) |
| **Faculty** | Only faculty members |

#### By PGY Level (Residents only)

| Filter | Shows |
|--------|-------|
| **All** | All residents |
| **PGY-1** | First-year residents (interns) |
| **PGY-2** | Second-year residents |
| **PGY-3** | Third-year residents |

---

## Adding a Person

### Opening the Add Dialog

1. Click **+ Add Person** button (top right)
2. The Add Person modal will appear

### Add Person Form

```
+------------------------------------------+
|            Add New Person                |
+------------------------------------------+
|                                          |
|  Name *                                  |
|  [_________________________________]     |
|                                          |
|  Type *                                  |
|  ( ) Resident    ( ) Faculty             |
|                                          |
|  PGY Level * (residents only)            |
|  [  1  v]                                |
|                                          |
|  Email                                   |
|  [_________________________________]     |
|                                          |
|  Specialties (comma-separated)           |
|  [_________________________________]     |
|                                          |
|  Target Clinical Blocks (residents)      |
|  [_________________________________]     |
|                                          |
|  [Cancel]              [Save Person]     |
+------------------------------------------+
```

### Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| **Name** | Yes | Full name (e.g., "Dr. Jane Smith") |
| **Type** | Yes | Resident or Faculty |
| **PGY Level** | Yes (residents) | 1, 2, or 3 |
| **Email** | No | Contact email address |
| **Specialties** | No | Medical specialties, comma-separated |
| **Target Clinical Blocks** | No | Number of clinical blocks for the year |

### Adding a Resident

1. Click **+ Add Person**
2. Enter the name: "Dr. Jane Smith"
3. Select **Resident**
4. Choose **PGY Level**: 1 (for interns)
5. Enter email: "jsmith@hospital.org"
6. Click **Save Person**

### Adding a Faculty Member

1. Click **+ Add Person**
2. Enter the name: "Dr. Robert Johnson"
3. Select **Faculty**
4. Enter email: "rjohnson@hospital.org"
5. Enter specialties: "Gastroenterology, Hepatology"
6. Click **Save Person**

---

## Editing a Person

### Opening the Edit Dialog

1. Find the person's card
2. Click **Edit** button

### Edit Person Form

The edit form is identical to the add form, pre-populated with current data.

### Common Edits

#### Updating PGY Level (Annual Promotion)

At the start of a new academic year:
1. Find the resident's card
2. Click **Edit**
3. Change PGY Level (e.g., 1 to 2)
4. Click **Save Changes**

#### Updating Contact Information

1. Click **Edit** on the person's card
2. Update the email address
3. Click **Save Changes**

#### Adding Specialties

1. Click **Edit**
2. Enter specialties in the field (comma-separated)
3. Click **Save Changes**

---

## Deleting a Person

### Important Warning

**Deleting a person will affect:**
- All their current schedule assignments
- Historical schedule data
- Absence records

**Recommendation**: Remove or reassign their scheduled slots BEFORE deleting.

### Delete Process

1. Find the person's card
2. Click **Delete** button
3. Confirm in the dialog:

```
+------------------------------------------+
|           Confirm Deletion               |
+------------------------------------------+
|                                          |
|  Are you sure you want to delete         |
|  Dr. Jane Smith?                         |
|                                          |
|  This action cannot be undone.           |
|                                          |
|  [Cancel]              [Delete]          |
+------------------------------------------+
```

4. Click **Delete** to confirm

---

## Person Types Explained

### Residents

Medical school graduates in training programs.

| PGY Level | Description | Supervision Requirement |
|-----------|-------------|-------------------------|
| **PGY-1** | First year (intern) | 1 faculty per 2 residents |
| **PGY-2** | Second year | 1 faculty per 4 residents |
| **PGY-3** | Third year | 1 faculty per 4 residents |

**Key Fields**:
- PGY Level (required)
- Target Clinical Blocks (for workload tracking)

##***REMOVED***

Attending physicians who supervise residents.

**Key Fields**:
- Specialties (for rotation matching)
- Primary Duty (if applicable)
- Performs Procedures (boolean)

---

## Bulk Operations

### Exporting People Data

1. Click the **Export** dropdown (if available)
2. Select format:
   - **CSV**: For spreadsheet analysis
   - **JSON**: For data integration

### Importing People

Currently not supported via UI. Contact your administrator for bulk imports.

---

## Best Practices

### Naming Conventions

Use consistent naming:
- Include title: "Dr. Jane Smith"
- Or use format: "Smith, Jane MD"

### Email Addresses

- Use institutional email addresses
- Ensure accuracy for notifications

### Specialty Management

- Use consistent terminology
- Separate multiple specialties with commas
- Example: "Internal Medicine, Cardiology"

### PGY Level Maintenance

- Update PGY levels at academic year start
- Typically July 1 for most programs
- Review all residents during transition

---

## Common Scenarios

### New Academic Year Setup

**Adding Incoming Interns**:
1. Get list from GME office
2. Add each as Resident, PGY-1
3. Enter email addresses

**Promoting Existing Residents**:
1. Filter by "Residents"
2. Edit each PGY-1 → PGY-2
3. Edit each PGY-2 → PGY-3

**Removing Graduates**:
1. Clear assignments for graduating PGY-3s
2. Delete their records (or archive)

### Mid-Year Changes

**Resident Transfer In**:
1. Add as new person
2. Set appropriate PGY level
3. Enter transfer date in notes

**Resident Departure**:
1. Remove from future schedules
2. Consider deletion vs. keeping for records

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Can't add person | Check required fields (name, type, PGY level) |
| Delete button disabled | Person may have active assignments |
| Duplicate person created | Delete duplicate; use search before adding |
| PGY level not showing | Ensure "Resident" type is selected |

---

## Related Guides

- [Getting Started](getting-started.md) - Basic navigation
- [Absence Management](absences.md) - Recording time off
- [Schedule Generation](schedule-generation.md) - Creating assignments
- [Common Workflows](common-workflows.md) - New year setup walkthrough

---

*Accurate people data is the foundation of effective scheduling.*
