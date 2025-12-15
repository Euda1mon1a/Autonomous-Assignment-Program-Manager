# ACGME Compliance Monitoring

The Compliance page provides real-time monitoring of ACGME (Accreditation Council for Graduate Medical Education) requirements. It helps ensure your residency program maintains regulatory compliance.

---

## Accessing Compliance

Click **Compliance** in the main navigation bar.

**Available to**: All users (Faculty, Coordinator, Admin)

---

## Compliance Page Overview

```
+------------------------------------------------------------------------+
|  ACGME COMPLIANCE                                   Month: [< Jan >]   |
+------------------------------------------------------------------------+
|                                                                         |
|  +----------------------+  +----------------------+  +------------------+
|  |    80-HOUR RULE     |  |    1-IN-7 RULE      |  |   SUPERVISION    |
|  |                     |  |                      |  |                  |
|  |    [Green Check]    |  |    [Red X]           |  |   [Green Check]  |
|  |    COMPLIANT        |  |    2 VIOLATIONS      |  |   COMPLIANT      |
|  |                     |  |                      |  |                  |
|  +----------------------+  +----------------------+  +------------------+
|                                                                         |
|  +------------------------------------------------------------------+  |
|  |                      VIOLATIONS LIST                              |  |
|  +------------------------------------------------------------------+  |
|  | Severity | Type      | Person     | Details                       |  |
|  +------------------------------------------------------------------+  |
|  | [HIGH]   | 1-in-7    | Dr. Smith  | No day off 1/8-1/14          |  |
|  | [HIGH]   | 1-in-7    | Dr. Jones  | No day off 1/15-1/21         |  |
|  +------------------------------------------------------------------+  |
|                                                                         |
|  COVERAGE RATE: 94%                                                    |
|  +==================================================------------+      |
|                                                                         |
+------------------------------------------------------------------------+
```

---

## ACGME Rules Explained

### 80-Hour Rule

**Requirement**: Residents cannot work more than 80 hours per week, averaged over a 4-week period.

| Aspect | Details |
|--------|---------|
| **Maximum** | 80 hours/week average |
| **Period** | Rolling 4-week window |
| **Includes** | All clinical and educational activities |
| **Violation Severity** | Critical |

**Example Calculation**:
- Week 1: 75 hours
- Week 2: 82 hours
- Week 3: 78 hours
- Week 4: 85 hours
- **Average**: 80 hours = Compliant (exactly at limit)

### 1-in-7 Rule

**Requirement**: Residents must have one day (24 continuous hours) free from all clinical duties every 7 days.

| Aspect | Details |
|--------|---------|
| **Minimum** | One 24-hour period off |
| **Frequency** | Every 7 days |
| **Cannot be on-call** | Must be truly free |
| **Violation Severity** | High |

**Example**:
- If resident works Jan 1-7 with no full day off = Violation
- If resident has Jan 4 completely off within Jan 1-7 = Compliant

### Supervision Ratios

**Requirement**: Faculty must supervise residents at specific ratios based on PGY level.

| PGY Level | Required Ratio | Notes |
|-----------|----------------|-------|
| **PGY-1** | 1 faculty : 2 residents | Stricter for interns |
| **PGY-2/3** | 1 faculty : 4 residents | More independence |

**Example**:
- 4 PGY-1 residents on rotation = Need 2 faculty supervising
- 4 PGY-2 residents on rotation = Need 1 faculty supervising
- Mixed PGY levels = Calculate based on most restrictive need

---

## Compliance Cards

### Status Indicators

Each card shows one of these statuses:

| Indicator | Meaning | Color |
|-----------|---------|-------|
| **Checkmark** | Compliant | Green |
| **X with count** | Violations present | Red |
| **Warning** | At risk | Yellow |

### 80-Hour Card

```
+----------------------+
|    80-HOUR RULE     |
|                     |
|    [Checkmark]      |
|    COMPLIANT        |
|                     |
| Avg: 72.5 hrs/week  |
+----------------------+
```

Shows:
- Compliance status
- Average hours for the period
- Click for detailed breakdown

### 1-in-7 Card

```
+----------------------+
|    1-IN-7 RULE      |
|                     |
|    [Red X]          |
|   2 VIOLATIONS      |
|                     |
| 2 residents affected|
+----------------------+
```

Shows:
- Compliance status
- Number of violations
- Number of affected residents

### Supervision Card

```
+----------------------+
|    SUPERVISION      |
|                     |
|    [Checkmark]      |
|    COMPLIANT        |
|                     |
| All ratios met      |
+----------------------+
```

Shows:
- Overall supervision status
- Summary message

---

## Violations List

### Violation Details

Each violation shows:

| Column | Description |
|--------|-------------|
| **Severity** | Critical, High, Medium, Low |
| **Type** | Which rule was violated |
| **Person** | Affected resident |
| **Details** | Specific information about violation |

### Severity Levels

| Severity | Color | Meaning | Action Required |
|----------|-------|---------|-----------------|
| **Critical** | Dark Red | Serious violation | Immediate correction |
| **High** | Red | Important violation | Urgent correction |
| **Medium** | Orange | Moderate concern | Schedule adjustment |
| **Low** | Yellow | Minor issue | Review when possible |

### Violation Types

| Type | Related Rule | Common Causes |
|------|--------------|---------------|
| **Hours Exceeded** | 80-Hour | Too many shifts assigned |
| **No Day Off** | 1-in-7 | Missing rest day in 7-day period |
| **Under-Supervised** | Supervision | Insufficient faculty coverage |

---

## Month Navigation

### Viewing Different Periods

```
     [<]  January 2024  [>]
```

- Click `<` for previous month
- Click `>` for next month
- Compliance is calculated for the displayed month

### Why Check Different Months?

- **Past months**: Audit historical compliance
- **Current month**: Monitor active schedule
- **Future months**: Preview generated schedules

---

## Coverage Rate

### Understanding Coverage Rate

```
COVERAGE RATE: 94%
+==================================================------------+
```

**Coverage Rate** = Required positions filled / Total required positions

| Rate | Status | Interpretation |
|------|--------|----------------|
| 95-100% | Excellent | Fully staffed |
| 85-94% | Good | Minor gaps |
| 70-84% | Concerning | Review needed |
| <70% | Critical | Major gaps |

---

## Resolving Violations

### 80-Hour Violations

**Steps to resolve**:
1. Identify the affected resident
2. Review their schedule for the 4-week period
3. Reduce hours by:
   - Removing shifts
   - Assigning lighter rotations
   - Adding days off
4. Regenerate schedule if needed
5. Verify violation cleared

### 1-in-7 Violations

**Steps to resolve**:
1. Identify the resident and 7-day period
2. Find a day within that period to give off
3. Reassign their duties for that day
4. Verify 24-hour continuous break
5. Regenerate and verify

### Supervision Violations

**Steps to resolve**:
1. Identify the rotation/time with violation
2. Options:
   - Add faculty coverage
   - Reduce resident count
   - Reassign residents to different rotation
3. Verify ratio compliance after changes

---

## Compliance Workflow

### Daily Monitoring

1. Check Compliance page for any new violations
2. Address Critical/High violations immediately
3. Note Medium/Low for weekly review

### Weekly Review

1. Review all violations from the week
2. Identify patterns (same person? same rotation?)
3. Adjust templates or schedules as needed
4. Document any approved exceptions

### Monthly Audit

1. Navigate through the month
2. Document compliance status
3. Generate reports for GME office
4. Note any recurring issues for process improvement

---

## Compliance Best Practices

### Proactive Scheduling

- Check compliance BEFORE distributing schedules
- Use CP-SAT algorithm for optimal compliance
- Build in buffer (aim for <75 hours, not 80)

### Documentation

- Screenshot or export compliance reports
- Document any approved exceptions
- Keep records for accreditation reviews

### Communication

- Notify residents of near-violations
- Work with chief residents on schedule issues
- Report persistent issues to program leadership

---

## Understanding Calculations

### 80-Hour Calculation Method

```
Week 1 Hours + Week 2 Hours + Week 3 Hours + Week 4 Hours
--------------------------------------------------------- = Average
                         4

If Average > 80 --> Violation
```

### 1-in-7 Calculation Method

For each 7-day window:
1. List all scheduled activities
2. Find any 24-hour period with NO activities
3. If no such period exists --> Violation

### Supervision Calculation Method

For each block/rotation:
1. Count PGY-1 residents
2. Count PGY-2/3 residents
3. Count supervising faculty
4. Calculate required faculty:
   - PGY-1 requirement: PGY-1 count / 2
   - PGY-2/3 requirement: PGY-2/3 count / 4
5. If actual faculty < required --> Violation

---

## Reports and Documentation

### Compliance Reports

The system maintains:
- Monthly compliance summaries
- Individual resident hour logs
- Violation history

### Exporting Compliance Data

For accreditation purposes:
1. Navigate to desired month
2. Take screenshot or print
3. Export underlying data if needed

### Accreditation Documentation

Keep these records:
- Monthly compliance screenshots
- Exception documentation
- Corrective action records

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Unexpected violation | Verify schedule data accuracy |
| Violation won't clear | Check all 4 weeks for 80-hour; full 7 days for 1-in-7 |
| Coverage rate seems wrong | Verify all blocks have requirements set |
| Can't view compliance | Available to all users; check login status |

---

## Related Guides

- [Getting Started](getting-started.md) - Basic navigation
- [Schedule Generation](schedule-generation.md) - Creating compliant schedules
- [Settings](settings.md) - Configuring ACGME parameters
- [Common Workflows](common-workflows.md) - Resolving violation walkthrough
- [Troubleshooting](troubleshooting.md) - Common compliance issues

---

*ACGME compliance protects residents and ensures quality medical education.*
