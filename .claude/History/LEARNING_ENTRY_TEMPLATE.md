# Learning Entry Template

---
id: LEARN-YYYY-NNN
date: YYYY-MM-DD
type: constraint_discovery | workflow_improvement | failure_pattern | optimization | edge_case
severity: info | warning | critical
source: incident | observation | experiment | user_feedback | code_review
status: draft | validated | implemented | archived
---

## Summary
[One-line description of the learning]

## Context
**When**: [Date/time of discovery]
**Where**: [File, function, or system component]
**Who**: [Agent/skill that made the discovery, or user who reported]
**What were we doing**: [Task or operation in progress]

## Discovery
### What We Learned
[Detailed description of the discovery]

### Why It Matters
[Impact on system reliability, compliance, performance, or user experience]

### How We Found It
[Detection method: test failure, production incident, code review, user report]

## Evidence
### References
- Commit: [commit hash or link]
- Issue: [GitHub issue number]
- PR: [Pull request number]
- Logs: [Log excerpt or path to log file]
- Conversation: [Claude conversation ID or session notes]

### Reproduction Steps
1. [Step-by-step instructions to reproduce the issue or validate the learning]
2. [Include sample data if relevant]

### Code Example (if applicable)
```python
# Before (problematic pattern)
# ...

# After (improved pattern)
# ...
```

## Root Cause Analysis
### Immediate Cause
[Direct trigger of the issue]

### Contributing Factors
- [Factor 1]
- [Factor 2]

### Root Cause
[Underlying systemic issue]

## Impact Assessment
### Affected Components
- [ ] Scheduling engine
- [ ] ACGME validator
- [ ] Resilience framework
- [ ] Swap system
- [ ] API endpoints
- [ ] Frontend UI
- [ ] Database schema
- [ ] Background tasks (Celery)
- [ ] MCP tools
- [ ] Skills system
- [ ] Other: _______________

### Severity Justification
**Critical**: Could cause data loss, compliance violations, or system outages
**Warning**: Degrades performance, user experience, or maintainability
**Info**: Useful knowledge, best practice, or optimization opportunity

### Blast Radius
[How widespread is the impact? Single function, service, entire system?]

## Action Items
### Immediate Actions (within 24 hours)
- [ ] [Action 1]
- [ ] [Action 2]

### Short-term Actions (within 1 week)
- [ ] Update skill: [skill name]
- [ ] Add test case: [test description]
- [ ] Document in: [documentation file]
- [ ] Create GitHub issue: [link when created]

### Long-term Actions (within 1 month)
- [ ] Refactor: [component]
- [ ] Add monitoring: [metric]
- [ ] Update training data: [what to add]

### Prevention Measures
- [ ] Add pre-commit check for [pattern]
- [ ] Update skill guardrails in [skill]
- [ ] Add to troubleshooting guide
- [ ] Include in onboarding documentation

## Related Learnings
- Related to: [LEARN-YYYY-NNN]
- Supersedes: [LEARN-YYYY-NNN]
- See also: [LEARN-YYYY-NNN]

## Tags
[Choose relevant tags]

**Domain Areas:**
#scheduling #constraints #ACGME #resilience #swaps #credentials #coverage #procedures

**Technical Areas:**
#database #api #performance #security #testing #deployment #migration

**Patterns:**
#n+1_query #race_condition #timezone #async #validation #error_handling

**Skills:**
#constraint-preflight #acgme-compliance #schedule-optimization #systematic-debugger

**Severity:**
#bug #regression #edge_case #optimization #best_practice

---

## Validation
### Review Checklist
- [ ] Learning is clearly articulated
- [ ] Evidence is documented with links
- [ ] Impact assessment is accurate
- [ ] Action items are specific and assignable
- [ ] Related learnings are cross-referenced
- [ ] Tags are comprehensive

### Reviewer Notes
[Space for META_UPDATER or human reviewer to add notes]

---

## Implementation Tracking
### Changes Made
- [Date] [Description of change] [Link to PR/commit]

### Verification
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Skills updated
- [ ] Monitoring added
- [ ] Verified in production (if applicable)

### Metrics
**Before**: [Relevant metric baseline]
**After**: [Metric after implementation]
**Improvement**: [Quantified benefit]

---

## Example Learning Entry

---
id: LEARN-2025-001
date: 2025-12-15
type: constraint_discovery
severity: critical
source: incident
status: implemented
---

## Summary
ACGME 1-in-7 rule validator fails when work periods span month boundaries due to incorrect rolling window calculation.

## Context
**When**: 2025-12-15 14:30 HST
**Where**: `backend/app/scheduling/acgme_validator.py:_check_one_in_seven()`
**Who**: systematic-debugger skill (incident response)
**What were we doing**: Validating generated Block 10 schedule for January 2026

## Discovery
### What We Learned
The ACGME 1-in-7 rule validator incorrectly calculated rolling 7-day windows when a resident's work period spanned the end of one month and the beginning of the next. The validator was resetting the day-off counter at month boundaries, allowing schedules that violated the "one 24-hour period off every 7 days" rule.

### Why It Matters
This is a CRITICAL compliance violation. If undetected, the program could face ACGME citations, which could jeopardize accreditation. Residents could also be illegally overworked, creating patient safety and resident wellbeing concerns.

### How We Found It
Production incident: Schedule generated for Block 10 (Jan 2026) showed PGY2-03 working 14 consecutive days spanning Dec 28 - Jan 10. Flagged during manual review by Program Director.

## Evidence
### References
- Commit: d0efcc5a (fix applied)
- Issue: #247
- PR: #248
- Logs: `backend/logs/scheduler-2025-12-15.log` lines 1456-1489
- Conversation: claude-debug-session-20251215.md

### Reproduction Steps
1. Create test resident with assignments:
   - Dec 28-31: Inpatient call (4 consecutive days)
   - Jan 1-10: Clinic days (10 consecutive days)
2. Run ACGME validator: `validate_one_in_seven(resident_id, date_range)`
3. Observe: Validator PASSES (incorrect)
4. Expected: Validator should FAIL (no day off in 14-day span)

### Code Example
```python
# Before (problematic pattern)
def _check_one_in_seven(self, person_id: str, start_date: date, end_date: date) -> bool:
    days_worked = 0
    for current_date in date_range(start_date, end_date):
        if self._has_assignment(person_id, current_date):
            days_worked += 1
            if days_worked >= 7:  # BUG: Never resets when day off found
                return False
        else:
            # BUG: Resets counter at month boundary due to query logic
            if current_date.day == 1:
                days_worked = 0
    return True

# After (improved pattern)
def _check_one_in_seven(self, person_id: str, start_date: date, end_date: date) -> bool:
    """Validate 1-in-7 rule using sliding 7-day windows."""
    for window_start in date_range(start_date, end_date - timedelta(days=6)):
        window_end = window_start + timedelta(days=6)
        days_off = sum(
            1 for d in date_range(window_start, window_end)
            if not self._has_assignment(person_id, d)
        )
        if days_off == 0:  # No day off in this 7-day window
            logger.error(
                f"1-in-7 violation: {person_id} has no day off in "
                f"{window_start} to {window_end}"
            )
            return False
    return True
```

## Root Cause Analysis
### Immediate Cause
Month boundary logic in validator reset the consecutive-days counter

### Contributing Factors
- Insufficient test coverage for month-spanning schedules
- Validator logic was too complex (stateful counter instead of sliding window)
- Missing edge case tests in `tests/scheduling/test_acgme_validator.py`

### Root Cause
**Design flaw**: Original implementation used a stateful counter approach instead of the more robust sliding window approach. The counter logic was error-prone when dealing with calendar edge cases.

## Impact Assessment
### Affected Components
- [x] Scheduling engine (validates before saving)
- [x] ACGME validator (core bug)
- [ ] Resilience framework
- [ ] Swap system (also validates post-swap)
- [x] API endpoints (schedule generation endpoint)
- [ ] Frontend UI
- [ ] Database schema
- [ ] Background tasks (Celery)
- [ ] MCP tools (schedule validation tools)
- [x] Skills system (acgme-compliance skill needs update)
- [ ] Other: _______________

### Severity Justification
**Critical**: Could cause ACGME compliance violations leading to program citations or loss of accreditation. Legal liability if residents are overworked in violation of regulations.

### Blast Radius
**High**: Affects all schedule validation workflows. Any schedule generated since feature launch (6 months ago) may contain undetected violations.

## Action Items
### Immediate Actions (within 24 hours)
- [x] Hotfix deployed to production (2025-12-15 16:00 HST)
- [x] Audit all generated schedules from past 6 months
- [x] Notify Program Director of audit results

### Short-term Actions (within 1 week)
- [x] Update skill: acgme-compliance (add month-boundary test guidance)
- [x] Add test cases:
  - [x] `test_one_in_seven_month_boundary()`
  - [x] `test_one_in_seven_year_boundary()`
  - [x] `test_one_in_seven_leap_year()`
- [x] Document in: `docs/architecture/ACGME_VALIDATION_PATTERNS.md`
- [x] Create GitHub issue: #249 (add calendar edge case test suite)

### Long-term Actions (within 1 month)
- [x] Refactor: All ACGME validators to use sliding window approach
- [ ] Add monitoring: Track validation failure rates by rule type
- [x] Update training data: Add to systematic-debugger skill examples

### Prevention Measures
- [x] Add pre-commit check for calendar edge case tests when modifying validators
- [x] Update skill guardrails in constraint-preflight (require calendar tests)
- [x] Add to troubleshooting guide: "Common Calendar Edge Cases"
- [ ] Include in onboarding documentation for new developers

## Related Learnings
- Related to: LEARN-2024-087 (timezone handling in work hour calculations)
- See also: LEARN-2025-002 (leap year handling in date ranges)

## Tags
#ACGME #scheduling #constraints #critical #bug #compliance #calendar #edge_case #validation #acgme-compliance #systematic-debugger #month_boundary #testing

---

## Validation
### Review Checklist
- [x] Learning is clearly articulated
- [x] Evidence is documented with links
- [x] Impact assessment is accurate
- [x] Action items are specific and assignable
- [x] Related learnings are cross-referenced
- [x] Tags are comprehensive

### Reviewer Notes
**META_UPDATER (2025-12-16)**: High-priority learning. Updated acgme-compliance skill with new test patterns. Added calendar edge case checklist to constraint-preflight skill. Verified all ACGME validators now use sliding window approach.

**Human Reviewer (Program Director, 2025-12-16)**: Confirmed audit completed. 3 historical schedules had minor violations (residents had 1 occurrence of working 8 consecutive days instead of max 7). All affected residents contacted. No resident exceeded 80-hour rule. Issue contained.

---

## Implementation Tracking
### Changes Made
- 2025-12-15: Hotfix applied to `acgme_validator.py` (PR #248)
- 2025-12-16: Test suite expanded (PR #250)
- 2025-12-17: Skills updated (acgme-compliance, constraint-preflight)
- 2025-12-18: Documentation updated (ACGME_VALIDATION_PATTERNS.md)

### Verification
- [x] Tests added/updated (15 new edge case tests)
- [x] Documentation updated
- [x] Skills updated (acgme-compliance, constraint-preflight)
- [ ] Monitoring added (pending Prometheus metric definition)
- [x] Verified in production (Jan 2026 schedule generated successfully)

### Metrics
**Before**: 0% coverage for calendar edge cases in ACGME validators
**After**: 94% coverage (added 15 edge case tests)
**Improvement**: Eliminated entire class of calendar-related compliance bugs

---

## Notes for META_UPDATER
This is a high-signal learning entry. When mining this:
1. Extract the pattern: "Always use sliding windows for time-based constraints, not stateful counters"
2. Priority: CRITICAL (affects regulatory compliance)
3. Frequency: Rare but high-impact
4. Skill update targets: acgme-compliance, constraint-preflight, systematic-debugger
5. Test template: Use this as template for calendar edge case test generation
