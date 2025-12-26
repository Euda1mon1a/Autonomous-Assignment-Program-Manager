***REMOVED*** Learning Entry Template

---
id: LEARN-YYYY-NNN
date: YYYY-MM-DD
type: constraint_discovery | workflow_improvement | failure_pattern | optimization | edge_case
severity: info | warning | critical
source: incident | observation | experiment | user_feedback | code_review
status: draft | validated | implemented | archived
---

***REMOVED******REMOVED*** Summary
[One-line description of the learning]

***REMOVED******REMOVED*** Context
**When**: [Date/time of discovery]
**Where**: [File, function, or system component]
**Who**: [Agent/skill that made the discovery, or user who reported]
**What were we doing**: [Task or operation in progress]

***REMOVED******REMOVED*** Discovery
***REMOVED******REMOVED******REMOVED*** What We Learned
[Detailed description of the discovery]

***REMOVED******REMOVED******REMOVED*** Why It Matters
[Impact on system reliability, compliance, performance, or user experience]

***REMOVED******REMOVED******REMOVED*** How We Found It
[Detection method: test failure, production incident, code review, user report]

***REMOVED******REMOVED*** Evidence
***REMOVED******REMOVED******REMOVED*** References
- Commit: [commit hash or link]
- Issue: [GitHub issue number]
- PR: [Pull request number]
- Logs: [Log excerpt or path to log file]
- Conversation: [Claude conversation ID or session notes]

***REMOVED******REMOVED******REMOVED*** Reproduction Steps
1. [Step-by-step instructions to reproduce the issue or validate the learning]
2. [Include sample data if relevant]

***REMOVED******REMOVED******REMOVED*** Code Example (if applicable)
```python
***REMOVED*** Before (problematic pattern)
***REMOVED*** ...

***REMOVED*** After (improved pattern)
***REMOVED*** ...
```

***REMOVED******REMOVED*** Root Cause Analysis
***REMOVED******REMOVED******REMOVED*** Immediate Cause
[Direct trigger of the issue]

***REMOVED******REMOVED******REMOVED*** Contributing Factors
- [Factor 1]
- [Factor 2]

***REMOVED******REMOVED******REMOVED*** Root Cause
[Underlying systemic issue]

***REMOVED******REMOVED*** Impact Assessment
***REMOVED******REMOVED******REMOVED*** Affected Components
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

***REMOVED******REMOVED******REMOVED*** Severity Justification
**Critical**: Could cause data loss, compliance violations, or system outages
**Warning**: Degrades performance, user experience, or maintainability
**Info**: Useful knowledge, best practice, or optimization opportunity

***REMOVED******REMOVED******REMOVED*** Blast Radius
[How widespread is the impact? Single function, service, entire system?]

***REMOVED******REMOVED*** Action Items
***REMOVED******REMOVED******REMOVED*** Immediate Actions (within 24 hours)
- [ ] [Action 1]
- [ ] [Action 2]

***REMOVED******REMOVED******REMOVED*** Short-term Actions (within 1 week)
- [ ] Update skill: [skill name]
- [ ] Add test case: [test description]
- [ ] Document in: [documentation file]
- [ ] Create GitHub issue: [link when created]

***REMOVED******REMOVED******REMOVED*** Long-term Actions (within 1 month)
- [ ] Refactor: [component]
- [ ] Add monitoring: [metric]
- [ ] Update training data: [what to add]

***REMOVED******REMOVED******REMOVED*** Prevention Measures
- [ ] Add pre-commit check for [pattern]
- [ ] Update skill guardrails in [skill]
- [ ] Add to troubleshooting guide
- [ ] Include in onboarding documentation

***REMOVED******REMOVED*** Related Learnings
- Related to: [LEARN-YYYY-NNN]
- Supersedes: [LEARN-YYYY-NNN]
- See also: [LEARN-YYYY-NNN]

***REMOVED******REMOVED*** Tags
[Choose relevant tags]

**Domain Areas:**
***REMOVED***scheduling ***REMOVED***constraints ***REMOVED***ACGME ***REMOVED***resilience ***REMOVED***swaps ***REMOVED***credentials ***REMOVED***coverage ***REMOVED***procedures

**Technical Areas:**
***REMOVED***database ***REMOVED***api ***REMOVED***performance ***REMOVED***security ***REMOVED***testing ***REMOVED***deployment ***REMOVED***migration

**Patterns:**
***REMOVED***n+1_query ***REMOVED***race_condition ***REMOVED***timezone ***REMOVED***async ***REMOVED***validation ***REMOVED***error_handling

**Skills:**
***REMOVED***constraint-preflight ***REMOVED***acgme-compliance ***REMOVED***schedule-optimization ***REMOVED***systematic-debugger

**Severity:**
***REMOVED***bug ***REMOVED***regression ***REMOVED***edge_case ***REMOVED***optimization ***REMOVED***best_practice

---

***REMOVED******REMOVED*** Validation
***REMOVED******REMOVED******REMOVED*** Review Checklist
- [ ] Learning is clearly articulated
- [ ] Evidence is documented with links
- [ ] Impact assessment is accurate
- [ ] Action items are specific and assignable
- [ ] Related learnings are cross-referenced
- [ ] Tags are comprehensive

***REMOVED******REMOVED******REMOVED*** Reviewer Notes
[Space for META_UPDATER or human reviewer to add notes]

---

***REMOVED******REMOVED*** Implementation Tracking
***REMOVED******REMOVED******REMOVED*** Changes Made
- [Date] [Description of change] [Link to PR/commit]

***REMOVED******REMOVED******REMOVED*** Verification
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Skills updated
- [ ] Monitoring added
- [ ] Verified in production (if applicable)

***REMOVED******REMOVED******REMOVED*** Metrics
**Before**: [Relevant metric baseline]
**After**: [Metric after implementation]
**Improvement**: [Quantified benefit]

---

***REMOVED******REMOVED*** Example Learning Entry

---
id: LEARN-2025-001
date: 2025-12-15
type: constraint_discovery
severity: critical
source: incident
status: implemented
---

***REMOVED******REMOVED*** Summary
ACGME 1-in-7 rule validator fails when work periods span month boundaries due to incorrect rolling window calculation.

***REMOVED******REMOVED*** Context
**When**: 2025-12-15 14:30 HST
**Where**: `backend/app/scheduling/acgme_validator.py:_check_one_in_seven()`
**Who**: systematic-debugger skill (incident response)
**What were we doing**: Validating generated Block 10 schedule for January 2026

***REMOVED******REMOVED*** Discovery
***REMOVED******REMOVED******REMOVED*** What We Learned
The ACGME 1-in-7 rule validator incorrectly calculated rolling 7-day windows when a resident's work period spanned the end of one month and the beginning of the next. The validator was resetting the day-off counter at month boundaries, allowing schedules that violated the "one 24-hour period off every 7 days" rule.

***REMOVED******REMOVED******REMOVED*** Why It Matters
This is a CRITICAL compliance violation. If undetected, the program could face ACGME citations, which could jeopardize accreditation. Residents could also be illegally overworked, creating patient safety and resident wellbeing concerns.

***REMOVED******REMOVED******REMOVED*** How We Found It
Production incident: Schedule generated for Block 10 (Jan 2026) showed PGY2-03 working 14 consecutive days spanning Dec 28 - Jan 10. Flagged during manual review by Program Director.

***REMOVED******REMOVED*** Evidence
***REMOVED******REMOVED******REMOVED*** References
- Commit: d0efcc5a (fix applied)
- Issue: ***REMOVED***247
- PR: ***REMOVED***248
- Logs: `backend/logs/scheduler-2025-12-15.log` lines 1456-1489
- Conversation: claude-debug-session-20251215.md

***REMOVED******REMOVED******REMOVED*** Reproduction Steps
1. Create test resident with assignments:
   - Dec 28-31: Inpatient call (4 consecutive days)
   - Jan 1-10: Clinic days (10 consecutive days)
2. Run ACGME validator: `validate_one_in_seven(resident_id, date_range)`
3. Observe: Validator PASSES (incorrect)
4. Expected: Validator should FAIL (no day off in 14-day span)

***REMOVED******REMOVED******REMOVED*** Code Example
```python
***REMOVED*** Before (problematic pattern)
def _check_one_in_seven(self, person_id: str, start_date: date, end_date: date) -> bool:
    days_worked = 0
    for current_date in date_range(start_date, end_date):
        if self._has_assignment(person_id, current_date):
            days_worked += 1
            if days_worked >= 7:  ***REMOVED*** BUG: Never resets when day off found
                return False
        else:
            ***REMOVED*** BUG: Resets counter at month boundary due to query logic
            if current_date.day == 1:
                days_worked = 0
    return True

***REMOVED*** After (improved pattern)
def _check_one_in_seven(self, person_id: str, start_date: date, end_date: date) -> bool:
    """Validate 1-in-7 rule using sliding 7-day windows."""
    for window_start in date_range(start_date, end_date - timedelta(days=6)):
        window_end = window_start + timedelta(days=6)
        days_off = sum(
            1 for d in date_range(window_start, window_end)
            if not self._has_assignment(person_id, d)
        )
        if days_off == 0:  ***REMOVED*** No day off in this 7-day window
            logger.error(
                f"1-in-7 violation: {person_id} has no day off in "
                f"{window_start} to {window_end}"
            )
            return False
    return True
```

***REMOVED******REMOVED*** Root Cause Analysis
***REMOVED******REMOVED******REMOVED*** Immediate Cause
Month boundary logic in validator reset the consecutive-days counter

***REMOVED******REMOVED******REMOVED*** Contributing Factors
- Insufficient test coverage for month-spanning schedules
- Validator logic was too complex (stateful counter instead of sliding window)
- Missing edge case tests in `tests/scheduling/test_acgme_validator.py`

***REMOVED******REMOVED******REMOVED*** Root Cause
**Design flaw**: Original implementation used a stateful counter approach instead of the more robust sliding window approach. The counter logic was error-prone when dealing with calendar edge cases.

***REMOVED******REMOVED*** Impact Assessment
***REMOVED******REMOVED******REMOVED*** Affected Components
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

***REMOVED******REMOVED******REMOVED*** Severity Justification
**Critical**: Could cause ACGME compliance violations leading to program citations or loss of accreditation. Legal liability if residents are overworked in violation of regulations.

***REMOVED******REMOVED******REMOVED*** Blast Radius
**High**: Affects all schedule validation workflows. Any schedule generated since feature launch (6 months ago) may contain undetected violations.

***REMOVED******REMOVED*** Action Items
***REMOVED******REMOVED******REMOVED*** Immediate Actions (within 24 hours)
- [x] Hotfix deployed to production (2025-12-15 16:00 HST)
- [x] Audit all generated schedules from past 6 months
- [x] Notify Program Director of audit results

***REMOVED******REMOVED******REMOVED*** Short-term Actions (within 1 week)
- [x] Update skill: acgme-compliance (add month-boundary test guidance)
- [x] Add test cases:
  - [x] `test_one_in_seven_month_boundary()`
  - [x] `test_one_in_seven_year_boundary()`
  - [x] `test_one_in_seven_leap_year()`
- [x] Document in: `docs/architecture/ACGME_VALIDATION_PATTERNS.md`
- [x] Create GitHub issue: ***REMOVED***249 (add calendar edge case test suite)

***REMOVED******REMOVED******REMOVED*** Long-term Actions (within 1 month)
- [x] Refactor: All ACGME validators to use sliding window approach
- [ ] Add monitoring: Track validation failure rates by rule type
- [x] Update training data: Add to systematic-debugger skill examples

***REMOVED******REMOVED******REMOVED*** Prevention Measures
- [x] Add pre-commit check for calendar edge case tests when modifying validators
- [x] Update skill guardrails in constraint-preflight (require calendar tests)
- [x] Add to troubleshooting guide: "Common Calendar Edge Cases"
- [ ] Include in onboarding documentation for new developers

***REMOVED******REMOVED*** Related Learnings
- Related to: LEARN-2024-087 (timezone handling in work hour calculations)
- See also: LEARN-2025-002 (leap year handling in date ranges)

***REMOVED******REMOVED*** Tags
***REMOVED***ACGME ***REMOVED***scheduling ***REMOVED***constraints ***REMOVED***critical ***REMOVED***bug ***REMOVED***compliance ***REMOVED***calendar ***REMOVED***edge_case ***REMOVED***validation ***REMOVED***acgme-compliance ***REMOVED***systematic-debugger ***REMOVED***month_boundary ***REMOVED***testing

---

***REMOVED******REMOVED*** Validation
***REMOVED******REMOVED******REMOVED*** Review Checklist
- [x] Learning is clearly articulated
- [x] Evidence is documented with links
- [x] Impact assessment is accurate
- [x] Action items are specific and assignable
- [x] Related learnings are cross-referenced
- [x] Tags are comprehensive

***REMOVED******REMOVED******REMOVED*** Reviewer Notes
**META_UPDATER (2025-12-16)**: High-priority learning. Updated acgme-compliance skill with new test patterns. Added calendar edge case checklist to constraint-preflight skill. Verified all ACGME validators now use sliding window approach.

**Human Reviewer (Program Director, 2025-12-16)**: Confirmed audit completed. 3 historical schedules had minor violations (residents had 1 occurrence of working 8 consecutive days instead of max 7). All affected residents contacted. No resident exceeded 80-hour rule. Issue contained.

---

***REMOVED******REMOVED*** Implementation Tracking
***REMOVED******REMOVED******REMOVED*** Changes Made
- 2025-12-15: Hotfix applied to `acgme_validator.py` (PR ***REMOVED***248)
- 2025-12-16: Test suite expanded (PR ***REMOVED***250)
- 2025-12-17: Skills updated (acgme-compliance, constraint-preflight)
- 2025-12-18: Documentation updated (ACGME_VALIDATION_PATTERNS.md)

***REMOVED******REMOVED******REMOVED*** Verification
- [x] Tests added/updated (15 new edge case tests)
- [x] Documentation updated
- [x] Skills updated (acgme-compliance, constraint-preflight)
- [ ] Monitoring added (pending Prometheus metric definition)
- [x] Verified in production (Jan 2026 schedule generated successfully)

***REMOVED******REMOVED******REMOVED*** Metrics
**Before**: 0% coverage for calendar edge cases in ACGME validators
**After**: 94% coverage (added 15 edge case tests)
**Improvement**: Eliminated entire class of calendar-related compliance bugs

---

***REMOVED******REMOVED*** Notes for META_UPDATER
This is a high-signal learning entry. When mining this:
1. Extract the pattern: "Always use sliding windows for time-based constraints, not stateful counters"
2. Priority: CRITICAL (affects regulatory compliance)
3. Frequency: Rare but high-impact
4. Skill update targets: acgme-compliance, constraint-preflight, systematic-debugger
5. Test template: Use this as template for calendar edge case test generation
