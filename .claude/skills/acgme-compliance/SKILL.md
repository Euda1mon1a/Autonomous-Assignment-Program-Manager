---
name: acgme-compliance
description: ACGME regulatory compliance expertise for medical residency scheduling. Use when validating schedules, checking work hour limits, supervision ratios, or answering compliance questions. Integrates with MCP validation tools.
model_tier: opus
parallel_hints:
  can_parallel_with: [code-review, test-writer, constraint-preflight]
  must_serialize_with: [safe-schedule-generation, swap-execution]
  preferred_batch_size: 3
context_hints:
  max_file_context: 30
  compression_level: 1
  requires_git_context: false
  requires_db_context: true
escalation_triggers:
  - pattern: "violation"
    reason: "Compliance violations require human approval"
  - pattern: "exception"
    reason: "Policy exceptions need Program Director approval"
  - keyword: ["systemic", "recurring", "pattern"]
    reason: "Systemic issues require escalation"
---

***REMOVED*** ACGME Compliance Skill

Expert knowledge of ACGME (Accreditation Council for Graduate Medical Education) requirements for residency program scheduling.

***REMOVED******REMOVED*** When This Skill Activates

- Validating schedule compliance
- Checking resident work hours
- Verifying supervision ratios
- Answering ACGME-related questions
- Before finalizing any schedule changes
- When coverage gaps are detected

***REMOVED******REMOVED*** Core ACGME Rules

***REMOVED******REMOVED******REMOVED*** 1. 80-Hour Rule (Duty Hours)
**Requirement:** Maximum 80 hours per week, averaged over 4-week period

```
Weekly Hours ≤ 80 (averaged over rolling 4 weeks)
```

| Calculation | Formula |
|-------------|---------|
| 4-Week Average | `(Week1 + Week2 + Week3 + Week4) / 4` |
| Warning Threshold | > 75 hours/week |
| Violation | > 80 hours/week average |

**Common Violations:**
- Holiday coverage stacking
- Call schedule compression
- Inadequate post-call relief

***REMOVED******REMOVED******REMOVED*** 2. 1-in-7 Rule (Days Off)
**Requirement:** One 24-hour period free from duty every 7 days

```
Must have ≥ 1 day completely off per 7-day period
```

| Status | Definition |
|--------|------------|
| Compliant | 24+ continuous hours off in 7-day window |
| At Risk | 6 consecutive duty days |
| Violation | 7+ consecutive duty days |

**Note:** Averaged over 4 weeks for some programs

***REMOVED******REMOVED******REMOVED*** 3. Supervision Ratios
**Requirement:** Adequate faculty oversight based on training level

| Training Level | Max Residents per Faculty |
|----------------|---------------------------|
| PGY-1 (Intern) | 2:1 |
| PGY-2 | 4:1 |
| PGY-3+ | 4:1 |

**Critical Areas Requiring Direct Supervision:**
- Emergency procedures
- High-risk patient care
- Night float transitions

***REMOVED******REMOVED******REMOVED*** 4. Duty Period Limits
| Scenario | Maximum Duration |
|----------|------------------|
| Standard shift | 24 hours |
| With strategic napping | 28 hours (rare exception) |
| Minimum time off between shifts | 8 hours |
| Extended (in-house call) | 24 + 4 hours transition |

***REMOVED******REMOVED******REMOVED*** 5. Night Float Requirements
- Maximum 6 consecutive nights
- Adequate handoff time
- No other clinical duties during night float block

***REMOVED******REMOVED*** MCP Tool Integration

***REMOVED******REMOVED******REMOVED*** Primary Validation Tool
```
Tool: validate_acgme_compliance
Purpose: Full compliance check against all rules
Returns: violations[], warnings[], compliant_areas[]
```

***REMOVED******REMOVED******REMOVED*** Supporting Tools
| Tool | Use Case |
|------|----------|
| `get_schedule` | Retrieve schedule data for analysis |
| `check_utilization_threshold_tool` | Verify 80% utilization limit |
| `run_contingency_analysis_resilience_tool` | Check N-1 coverage |

***REMOVED******REMOVED*** Validation Workflow

***REMOVED******REMOVED******REMOVED*** Phase 1: Data Gathering and Analysis

**Step 1.1: Collect Schedule Data**
```bash
***REMOVED*** Use MCP tool to get current schedule
mcp call validate_acgme_compliance --schedule_id=current
```

Response includes:
- All assignments for specified period
- Work hours accumulated per resident
- Duty period configurations
- Supervision assignments

**Step 1.2: Extract Compliance Metrics**
For each resident:
- [ ] Cumulative hours this week/4-week average
- [ ] Days off in last 7 days
- [ ] Current supervision ratio in each rotation
- [ ] Consecutive duty days count
- [ ] Night float block duration

***REMOVED******REMOVED******REMOVED*** Phase 2: Rule-by-Rule Analysis

**Step 2.1: 80-Hour Rule Analysis**
```
For each resident:
1. Calculate rolling 4-week average
   = (Week-4 + Week-3 + Week-2 + Week-1) / 4

2. Compare to threshold:
   - Compliant: < 80 hours/week average
   - Warning: 75-80 hours/week average
   - Violation: > 80 hours/week average

3. Identify problematic weeks:
   - Which week(s) exceed limit?
   - What assignments cause excess?
```

**Step 2.2: 1-in-7 Rule Analysis**
```
For each resident:
1. Look at each 7-day rolling window
2. Count continuous duty-free days
   - Need at least one 24-hour period off

3. Identify violations:
   - 7+ consecutive duty days = VIOLATION
   - 6 consecutive duty days = WARNING
   - Schedule relief needed by [DATE]
```

**Step 2.3: Supervision Ratio Analysis**
```
For each rotation with residents:
1. Count residents scheduled
2. Count faculty available on shift
3. Calculate ratio by training level
4. Compare to requirements:
   - PGY-1: Must be ≤ 2:1
   - PGY-2/3: Must be ≤ 4:1

4. Flag violations:
   - Specific shift/date
   - Gap count (how many too many)
   - Recommended faculty additions
```

**Step 2.4: Duty Period Analysis**
```
For each assignment:
1. Calculate duty period duration
2. Check for adequate rest after:
   - Post-24h call: minimum 8 hours off before next duty
   - Extended (28h): minimum 10 hours off

3. Flag violations with specific dates
```

***REMOVED******REMOVED******REMOVED*** Phase 3: Issue Prioritization and Reporting

**Step 3.1: Categorize Findings**
| Severity | Criteria | Response Time |
|----------|----------|---|
| **VIOLATION** | Actual breach of rule | Immediate (today) |
| **WARNING** | Approaching threshold | 48 hours |
| **AT RISK** | Potential issue | Monitor, plan |
| **COMPLIANT** | Within all limits | Continue |

**Step 3.2: Prioritize Issues**
```
Ranking (highest to lowest priority):
1. Violations affecting resident health/safety
2. Systemic violations (recurring pattern)
3. Single-resident violations
4. Warning-level issues
5. At-risk scenarios
```

***REMOVED******REMOVED******REMOVED*** Phase 4: Solution Development

**Step 4.1: Root Cause Analysis**
For each issue, identify:
- Underlying cause (staffing gap, schedule design, etc.)
- Whether it's systemic or isolated
- Historical context (has this happened before?)

**Step 4.2: Recommend Specific Fixes**
For violations, provide:
```
Issue: [Specific violation]
Affected: [Names and dates]
Root cause: [Why this happened]
Immediate fix: [Swap or reassignment specific to dates]
Long-term fix: [Schedule design change]
Impact assessment: [How fix affects other residents]
```

**Step 4.3: Validate Fix Doesn't Create New Issues**
After proposing fix:
- [ ] Verify fix resolves the violation
- [ ] Confirm it doesn't violate other rules
- [ ] Check supervision ratios remain compliant
- [ ] Verify affected residents don't now have 80-hour issues

***REMOVED******REMOVED*** Escalation Triggers

**Escalate to Program Director when:**
1. Multiple simultaneous violations
2. Systemic pattern (same issue recurring)
3. Fix requires policy exception
4. Involves moonlighting hours
5. Resident health/safety concern

***REMOVED******REMOVED*** Common Scenarios

***REMOVED******REMOVED******REMOVED*** Scenario: Post-Call Scheduling
**Problem:** Resident scheduled for clinic after 24-hour call
**Rule:** Must have 8+ hours off after extended duty
**Fix:** Remove clinic assignment, ensure coverage

***REMOVED******REMOVED******REMOVED*** Scenario: Holiday Coverage
**Problem:** Same residents covering multiple holidays
**Rule:** Fair distribution, 80-hour limit still applies
**Fix:** Rotate holiday assignments, check cumulative hours

***REMOVED******REMOVED******REMOVED*** Scenario: Supervision Gap
**Problem:** Night shift with insufficient faculty
**Rule:** PGY-1s need 2:1 supervision
**Fix:** Add faculty coverage or redistribute residents

***REMOVED******REMOVED*** Reporting Format

When reporting compliance status:

```
***REMOVED******REMOVED*** ACGME Compliance Summary

**Overall Status:** [COMPLIANT / WARNING / VIOLATION]

***REMOVED******REMOVED******REMOVED*** Violations (Immediate Action Required)
- [List specific violations with affected people/dates]

***REMOVED******REMOVED******REMOVED*** Warnings (Action Within 48h)
- [List warnings approaching thresholds]

***REMOVED******REMOVED******REMOVED*** Recommendations
1. [Specific actionable fix]
2. [Specific actionable fix]

***REMOVED******REMOVED******REMOVED*** Affected Personnel
- [List names and specific issues]
```

***REMOVED******REMOVED*** Integration with Other Skills

***REMOVED******REMOVED******REMOVED*** With safe-schedule-generation
**Coordination:** ACGME compliance must be verified after each schedule generation
```
1. safe-schedule-generation creates schedule
2. acgme-compliance validates against all rules
3. If violations found, feedback to schedule generation
4. Repeat until compliant schedule produced
```

***REMOVED******REMOVED******REMOVED*** With constraint-preflight
**Coordination:** Ensure constraints encode ACGME rules correctly
```
1. constraint-preflight validates constraint definitions
2. acgme-compliance tests constraints with real schedule data
3. Verify constraints actually prevent violations
```

***REMOVED******REMOVED******REMOVED*** With swap-execution
**Coordination:** Verify swaps don't violate ACGME rules
```
1. swap-execution proposes swap
2. acgme-compliance pre-validates swap impact
3. Only execute if compliant
```

***REMOVED******REMOVED*** Quick Reference Commands

***REMOVED******REMOVED******REMOVED*** Validation Commands
```bash
***REMOVED*** Full compliance check
python -m app.scheduling.acgme_validator --schedule_id=current --full-report

***REMOVED*** Quick 80-hour check
python -m app.scheduling.acgme_validator --check-rule 80-hour --residents=all

***REMOVED*** Specific resident check
python -m app.scheduling.acgme_validator --resident-id=PGY1-01 --period=4-weeks

***REMOVED*** Export compliance report
python -m app.scheduling.acgme_validator --schedule_id=current --export=pdf
```

***REMOVED******REMOVED******REMOVED*** Database Queries for Analysis
```python
***REMOVED*** Get hours for resident this week
SELECT SUM(duration) FROM assignments
WHERE resident_id = 'PGY1-01'
AND assignment_date BETWEEN CURRENT_DATE - 7 AND CURRENT_DATE;

***REMOVED*** Check consecutive duty days
SELECT DISTINCT(assignment_date) FROM assignments
WHERE resident_id = 'PGY1-01'
ORDER BY assignment_date DESC LIMIT 10;

***REMOVED*** Supervision ratio check
SELECT rotation, COUNT(DISTINCT resident_id), COUNT(DISTINCT faculty_id)
FROM assignments
WHERE assignment_date = CURRENT_DATE
GROUP BY rotation;
```

***REMOVED******REMOVED*** Validation Checklist

- [ ] 80-hour rule: All residents average ≤ 80 hours/week (4-week rolling)
- [ ] 1-in-7 rule: No resident has 7+ consecutive duty days
- [ ] Supervision ratios: PGY-1 at 2:1 or better, PGY-2/3 at 4:1 or better
- [ ] Duty periods: No shift exceeds 24 hours (28 max with strategic napping)
- [ ] Post-call rest: ≥ 8 hours off after 24-hour call before next duty
- [ ] Night float limits: ≤ 6 consecutive nights maximum
- [ ] Handoff times: Adequate time for shift handoff documented
- [ ] Time off: Residents able to use protected time
- [ ] No systemic issues: Not a recurring pattern of violations
- [ ] Documentation: Exceptions documented with Program Director approval

***REMOVED******REMOVED*** Context Management

**Input Context Requirements:**
- Schedule data (assignments with dates, durations)
- Resident demographics (training level)
- Faculty assignments (supervision tracking)
- Any applicable exceptions or waivers

**Compression Strategy:**
- Keep: Violation summaries, specific issue details
- Remove: Intermediate calculation steps
- Summarize: Pass/fail results from large reports

**Required Context for Next Phase:**
- Identified violations (if any)
- Affected residents and dates
- Root causes identified
- Proposed fixes

***REMOVED******REMOVED*** Common Patterns

***REMOVED******REMOVED******REMOVED*** Pattern 1: Good - Explicit Rule Implementation
```python
***REMOVED*** GOOD: Clear implementation of 80-hour rule
def check_80_hour_rule(resident_id: str) -> Tuple[bool, float]:
    """Check if resident exceeds 80-hour weekly average."""
    weeks = get_last_4_weeks(resident_id)
    hours_per_week = [sum_hours(week) for week in weeks]
    average = sum(hours_per_week) / len(hours_per_week)

    is_compliant = average <= 80.0
    return is_compliant, average
```

***REMOVED******REMOVED******REMOVED*** Pattern 2: Problematic - Ambiguous Threshold
```python
***REMOVED*** BAD: Unclear threshold and calculation
def check_hours(resident_id):
    hours = get_hours(resident_id)  ***REMOVED*** What period?
    if hours > 85:  ***REMOVED*** Why 85? Rule is 80
        return "violation"
```

***REMOVED******REMOVED******REMOVED*** Pattern 3: Good - Supervision Ratio Clarity
```python
***REMOVED*** GOOD: Clear calculation of supervision ratios
SUPERVISION_RATIOS = {
    "PGY1": 2,  ***REMOVED*** 2 residents per faculty
    "PGY2": 4,
    "PGY3": 4,
}

def verify_supervision(rotation: Rotation) -> bool:
    """Verify supervision ratios for rotation."""
    for level, max_ratio in SUPERVISION_RATIOS.items():
        residents = count_residents_by_level(rotation, level)
        faculty = count_faculty_in_rotation(rotation)
        actual_ratio = residents / faculty if faculty > 0 else 0

        if actual_ratio > max_ratio:
            log_violation(f"{level}: {actual_ratio}:1 exceeds {max_ratio}:1")
            return False
    return True
```

***REMOVED******REMOVED******REMOVED*** Pattern 4: Problematic - Hardcoded Values Without Context
```python
***REMOVED*** BAD: Magic numbers without explanation
if days_off < 1:  ***REMOVED*** Why 1? Context?
    flag_issue()
```

***REMOVED******REMOVED*** Error Recovery

**If validation fails unexpectedly:**
1. Verify data source is correct (right schedule ID)
2. Check for data quality issues (missing assignments, invalid dates)
3. Confirm compliance logic matches current ACGME rules
4. If issue persists, escalate to human reviewer with error logs

**If fix implementation fails:**
1. Don't force invalid assignments
2. Report specific constraint that prevents fix
3. Suggest alternative solutions
4. Escalate if no valid solution exists

***REMOVED******REMOVED*** References

- See `thresholds.md` for configurable warning levels
- See `exceptions.md` for documented exception procedures
- ACGME Common Program Requirements: https://www.acgme.org/
- See PROMPT_LIBRARY.md for detailed validation prompt templates
