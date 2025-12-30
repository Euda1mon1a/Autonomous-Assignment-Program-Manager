# Block Scheduler

> Automated resident rotation assignment with leave-eligible matching

---

## Overview

The Block Scheduler automates the assignment of residents to rotations for each academic block (28-day periods), intelligently handling leave requests to ensure proper coverage.

### Key Benefits

- **Automatic leave handling** - Residents with approved leave are assigned to leave-eligible rotations
- **Coverage protection** - Critical rotations (FMIT, inpatient) are staffed by available residents
- **Gap detection** - Identifies coverage shortfalls before they become problems
- **Preview mode** - Review assignments before committing

---

## How It Works

### The Algorithm

```
┌─────────────────────────────────────────────────────────────┐
│  BLOCK SCHEDULER PRIORITY ORDER                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. RESIDENTS WITH LEAVE                                     │
│     → Assigned to leave-eligible rotations                   │
│     (Electives, outpatient clinics, research)                │
│                                                              │
│  2. REMAINING RESIDENTS                                      │
│     → Fill non-leave-eligible rotations first (FMIT)         │
│     → Then balance across remaining rotations                │
│                                                              │
│  3. IDENTIFY GAPS                                            │
│     → Flag rotations without sufficient coverage             │
│     → Alert for manual intervention                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Rotation Categories

| Category | Leave Eligible | Examples |
|----------|----------------|----------|
| **Electives** | Yes | Sports Medicine, Dermatology |
| **Outpatient** | Yes | Specialty clinics, Research |
| **Inpatient** | **No** | FMIT, Night Float, ICU |
| **Coverage Required** | **No** | OB, Emergency |

---

## Using the Block Scheduler

### Step 1: View the Dashboard

Navigate to the Block Scheduler dashboard and select:
- **Block Number**: 1-13 (academic blocks) or 0 (orientation)
- **Academic Year**: e.g., 2025

The dashboard shows:
- Residents with approved leave in this block
- Rotation capacities and current assignments
- Unassigned residents

### Step 2: Preview Assignments

Click **"Preview Schedule"** (dry run mode) to see:
- Proposed assignments for each resident
- Assignment reasons (leave match, coverage priority, balanced)
- Coverage gaps with severity levels
- Any leave conflicts

### Step 3: Review and Adjust

Review the preview for:

**Coverage Gaps (Critical)**
```
⚠️ FMIT Inpatient: 1 gap (need 2, have 1)
   Severity: CRITICAL
```
→ May need to reassign or recruit additional coverage

**Leave Conflicts**
```
⚠️ Dr. Smith: No leave-eligible rotation available
   Leave Days: 5, Reason: No capacity
```
→ Consider expanding rotation capacity or rescheduling leave

### Step 4: Execute Schedule

Once satisfied with the preview:
1. Click **"Execute Schedule"**
2. Assignments are saved to the database
3. Manual adjustments can be made afterward

---

## Assignment Reasons

When reviewing assignments, you'll see these reasons:

| Reason | Icon | Meaning |
|--------|------|---------|
| `leave_eligible_match` | 🏖️ | Resident has leave, matched to leave-eligible rotation |
| `coverage_priority` | 🏥 | Assigned to fill critical coverage need |
| `balanced` | ⚖️ | Balanced distribution across rotations |
| `manual` | ✏️ | Manually assigned by coordinator |
| `specialty_match` | 🎯 | Matches specialty requirements |

---

## Manual Overrides

You can create or modify assignments manually:

### Create Manual Assignment

1. Go to Assignments section
2. Click "Add Assignment"
3. Select resident, block, and rotation
4. Save (will be marked as `manual`)

### Update Assignment

1. Find the assignment
2. Click "Edit"
3. Change rotation
4. Save (reason changes to `manual`)

### Delete Assignment

1. Find the assignment
2. Click "Delete"
3. Confirm

---

## Best Practices

### Before Scheduling

1. **Verify leave requests** are approved and up-to-date
2. **Check rotation templates** have correct `leave_eligible` settings
3. **Confirm capacity limits** are accurate

### During Scheduling

1. **Always preview first** before executing
2. **Review critical gaps** - they indicate potential coverage issues
3. **Address conflicts** before proceeding

### After Scheduling

1. **Communicate assignments** to residents
2. **Monitor for changes** in leave requests
3. **Update manually** if circumstances change

---

## Common Scenarios

### Scenario 1: Multiple Residents with Leave

When several residents have leave in the same block:

1. System assigns to leave-eligible rotations in order
2. If capacity runs out, conflicts are flagged
3. Consider:
   - Expanding rotation capacity
   - Staggering leave requests
   - Using multiple leave-eligible rotations

### Scenario 2: Coverage Emergency

When a non-leave-eligible rotation is understaffed:

1. Review the coverage gap alert
2. Options:
   - Reassign a resident from leave-eligible rotation
   - Request additional coverage (moonlighting, faculty backup)
   - Redistribute among remaining residents

### Scenario 3: Last-Minute Leave

For emergency/sick leave after scheduling:

1. The resident's assignment remains
2. Manually update if needed
3. System will flag conflicts on re-run

---

## Troubleshooting

### "No leave-eligible rotation available"

**Cause**: All leave-eligible rotations are at capacity

**Solutions**:
- Increase capacity on existing leave-eligible rotations
- Create additional leave-eligible rotation options
- Stagger leave across blocks

### "Critical coverage gap"

**Cause**: Non-leave-eligible rotation doesn't have enough residents

**Solutions**:
- Reassign residents from leave-eligible rotations
- Request additional coverage
- Check if any residents with leave can take this rotation

### "Assignment already exists"

**Cause**: Trying to create duplicate assignment

**Solution**: Update existing assignment instead of creating new

---

## Related Topics

- [Absences & Leave](absences.md) - Managing leave requests
- [Schedule](schedule.md) - Full schedule generation
- [Conflicts](conflicts.md) - Resolving scheduling conflicts
