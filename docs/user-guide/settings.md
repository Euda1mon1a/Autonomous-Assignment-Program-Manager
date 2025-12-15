# Admin Settings

The Settings page allows administrators to configure system-wide parameters including academic year dates, ACGME compliance settings, and scheduling algorithm preferences.

---

## Accessing Settings

Click **Settings** in the main navigation bar.

**Required Role**: Admin only

Coordinators and Faculty will not see the Settings option.

---

## Settings Page Overview

```
+------------------------------------------------------------------------+
|  SETTINGS                                           [Save Changes]     |
+------------------------------------------------------------------------+
|                                                                         |
|  ACADEMIC YEAR SETTINGS                                                |
|  +------------------------------------------------------------------+  |
|  | Start Date:        [July 1, 2024    ]  [Calendar]                |  |
|  | End Date:          [June 30, 2025   ]  [Calendar]                |  |
|  | Block Duration:    [28             ] days                        |  |
|  +------------------------------------------------------------------+  |
|                                                                         |
|  ACGME SETTINGS                                                        |
|  +------------------------------------------------------------------+  |
|  | Max Weekly Hours:        [80 ]                                   |  |
|  | PGY-1 Supervision Ratio: [1:2]                                   |  |
|  | PGY-2/3 Supervision Ratio: [1:4]                                 |  |
|  +------------------------------------------------------------------+  |
|                                                                         |
|  SCHEDULING ALGORITHM                                                  |
|  +------------------------------------------------------------------+  |
|  | Default Algorithm:  ( ) Greedy                                   |  |
|  |                     (*) Min Conflicts                            |  |
|  |                     ( ) CP-SAT                                   |  |
|  +------------------------------------------------------------------+  |
|                                                                         |
|  FEDERAL HOLIDAYS                                                      |
|  +------------------------------------------------------------------+  |
|  | [x] New Year's Day        [x] Independence Day                   |  |
|  | [x] MLK Day               [x] Labor Day                          |  |
|  | [x] Presidents Day        [x] Columbus Day                       |  |
|  | [x] Memorial Day          [x] Veterans Day                       |  |
|  |                           [x] Thanksgiving                       |  |
|  |                           [x] Christmas                          |  |
|  +------------------------------------------------------------------+  |
|                                                                         |
+------------------------------------------------------------------------+
```

---

## Academic Year Settings

### Start Date

The first day of the academic year.

| Field | Default | Notes |
|-------|---------|-------|
| **Start Date** | July 1 | Standard for most residency programs |

**When to change**: If your program operates on a different academic calendar.

### End Date

The last day of the academic year.

| Field | Default | Notes |
|-------|---------|-------|
| **End Date** | June 30 | One year from start date |

**When to change**: Align with your institution's academic calendar.

### Block Duration

The length of each scheduling block in days.

| Field | Default | Options |
|-------|---------|---------|
| **Block Duration** | 28 days | 7, 14, 21, 28, 30 |

**Common configurations**:
- 28 days (4 weeks) - Most common
- 30 days (monthly) - Some programs
- 14 days (2 weeks) - For more flexible scheduling

---

## ACGME Settings

### Max Weekly Hours

Maximum hours a resident can work per week, averaged over 4 weeks.

| Setting | ACGME Requirement | Recommended |
|---------|-------------------|-------------|
| **Max Weekly Hours** | 80 | 80 |

**Note**: This is an ACGME requirement. Changing this value should only be done with explicit approval and documentation.

### PGY-1 Supervision Ratio

Required faculty-to-resident ratio for first-year residents.

| Setting | ACGME Requirement | Format |
|---------|-------------------|--------|
| **PGY-1 Ratio** | 1:2 | 1:N |

**Meaning**: 1 faculty supervising up to 2 PGY-1 residents.

### PGY-2/3 Supervision Ratio

Required faculty-to-resident ratio for second and third-year residents.

| Setting | ACGME Requirement | Format |
|---------|-------------------|--------|
| **PGY-2/3 Ratio** | 1:4 | 1:N |

**Meaning**: 1 faculty supervising up to 4 PGY-2/3 residents.

---

## Scheduling Algorithm

### Default Algorithm Selection

Sets the default algorithm for schedule generation.

#### Greedy (Fast)

```
( ) Greedy
```

**Characteristics**:
- Fastest execution
- Good for quick drafts
- May not optimize fully

**Best for**: Initial planning, simple schedules

#### Min Conflicts (Balanced)

```
(*) Min Conflicts
```

**Characteristics**:
- Moderate speed
- Better optimization
- Usually achieves compliance

**Best for**: Most production schedules

#### CP-SAT (Optimal)

```
( ) CP-SAT
```

**Characteristics**:
- Slowest execution
- Guaranteed optimal (if possible)
- Best ACGME compliance

**Best for**: Final schedules, complex programs

### Algorithm Selection Tips

| Program Size | Recommended Default |
|--------------|---------------------|
| Small (<15 residents) | Greedy or Min Conflicts |
| Medium (15-30 residents) | Min Conflicts |
| Large (>30 residents) | Min Conflicts |
| Complex constraints | CP-SAT |

---

## Federal Holidays

### Holiday Configuration

Select which federal holidays affect scheduling.

```
[x] New Year's Day        January 1
[x] MLK Day               3rd Monday in January
[x] Presidents Day        3rd Monday in February
[x] Memorial Day          Last Monday in May
[x] Independence Day      July 4
[x] Labor Day             First Monday in September
[x] Columbus Day          2nd Monday in October
[x] Veterans Day          November 11
[x] Thanksgiving          4th Thursday in November
[x] Christmas             December 25
```

### Holiday Impact

Checked holidays:
- Are highlighted in schedule exports
- May affect scheduling algorithms
- Are noted in the schedule calendar

### Customizing Holidays

Some organizations may want to:
- Add institutional holidays
- Remove certain federal holidays
- Add religious observances

**Note**: Contact your administrator about custom holiday additions.

---

## Saving Settings

### Save Process

1. Make desired changes
2. Click **Save Changes** button
3. Wait for confirmation message
4. Changes take effect immediately

### Save Confirmation

```
+------------------------------------------+
|     Settings Saved Successfully          |
+------------------------------------------+
|                                          |
|  Your settings have been updated.        |
|  Changes will apply to future            |
|  schedule generations.                   |
|                                          |
|                         [OK]             |
+------------------------------------------+
```

### What Happens After Saving

- New academic year dates apply to future generations
- ACGME settings update compliance calculations
- Algorithm default changes for new schedules
- Holiday settings update immediately

**Note**: Existing schedules are NOT automatically updated. Regenerate if needed.

---

## Best Practices

### Academic Year Setup

**Annual checklist** (typically in June):
1. Verify start date (usually July 1)
2. Confirm end date (usually June 30)
3. Review block duration
4. Save changes

### ACGME Settings

**Generally, don't change** unless:
- ACGME requirements change
- You have institutional exemption
- Documented approval exists

If you must change:
1. Document the reason
2. Get program director approval
3. Make the change
4. Log the change for accreditation records

### Algorithm Selection

**Evaluate periodically**:
- If schedules have frequent violations → try CP-SAT
- If generation is too slow → try Greedy
- For most cases → Min Conflicts works well

### Holiday Management

**Review annually**:
- Verify all applicable holidays checked
- Remove any that don't apply
- Document any custom requirements

---

## Common Configuration Scenarios

### New Program Setup

1. Set academic year dates
2. Verify ACGME defaults
3. Select appropriate algorithm
4. Check applicable holidays
5. Save

### Academic Year Transition

In June/July:
1. Update Start Date to new year
2. Update End Date to new year
3. Review other settings
4. Save

### Changing Block Duration

If changing from 28 to 30 days:
1. Complete current block first
2. Update Block Duration setting
3. Save
4. Generate new schedules with new duration

### Preparing for ACGME Review

Before accreditation:
1. Verify all ACGME settings match requirements
2. Document any variations
3. Ensure settings align with program documents

---

## Activity Log

### Viewing Setting Changes

Settings changes are logged for audit purposes.

**To view activity log**:
1. Scroll down on Settings page
2. Look for "Activity Log" section (if available)
3. Review recent changes

**Logged information**:
- What was changed
- Who made the change
- When it was changed
- Old and new values

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Can't see Settings | Verify Admin role |
| Save button doesn't work | Check all required fields |
| Changes not taking effect | Regenerate affected schedules |
| Algorithm option grayed out | May require system restart |
| Holidays not showing in export | Verify holiday dates within range |

### Settings Not Saving

If settings won't save:
1. Check all required fields filled
2. Verify valid date formats
3. Ensure no conflicting values
4. Try refreshing the page
5. Contact IT support if persistent

---

## Security Considerations

### Who Should Have Admin Access

Limit Admin role to:
- Program Directors
- Chief Administrative Officers
- Designated schedule managers

### Audit Trail

Settings changes are tracked for:
- Accreditation documentation
- Compliance verification
- Change management

### Backup Before Changes

Before major settings changes:
1. Note current values
2. Document reason for change
3. Make the change
4. Verify system functions correctly

---

## Related Guides

- [Getting Started](getting-started.md) - Role overview
- [Compliance](compliance.md) - How settings affect compliance
- [Schedule Generation](schedule-generation.md) - Algorithm usage
- [Troubleshooting](troubleshooting.md) - Settings issues

---

*Proper settings configuration ensures compliant and efficient scheduling.*
