# Skill Update Workflow - How META_UPDATER Proposes Skill Enhancements

> **Purpose:** Document how the META_UPDATER agent detects, proposes, and manages skill updates
> **Audience:** META_UPDATER agent, ARCHITECT, system maintainers
> **Last Updated:** 2025-12-26

---

## Table of Contents

1. [Overview](#overview)
2. [Update Trigger Conditions](#update-trigger-conditions)
3. [Signal Detection Process](#signal-detection-process)
4. [GitHub PR Format for Skill Updates](#github-pr-format-for-skill-updates)
5. [Review and Approval Process](#review-and-approval-process)
6. [Merging and Activation](#merging-and-activation)
7. [Rollback Procedures](#rollback-procedures)
8. [Example: Updating SCHEDULING Skill](#example-updating-scheduling-skill)
9. [Monitoring Post-Update](#monitoring-post-update)

---

## Overview

### Purpose of Skill Updates

Skills must evolve to remain effective as:
- **Codebase changes**: New APIs, refactored services, updated MCP tools
- **Patterns emerge**: Recurring tasks reveal missing capabilities
- **Failures occur**: Incidents expose gaps in error handling or validation
- **Policies change**: ACGME rules update, institutional policies shift

### META_UPDATER Responsibility

The META_UPDATER agent monitors the system for signals indicating a skill needs enhancement:
- **Performance metrics**: Skill failure rates, escalation frequency
- **User feedback**: Agents report skill inadequacies
- **Code changes**: Backend updates that affect skill integration
- **Incident learnings**: Post-mortems reveal skill gaps

When signals detected, META_UPDATER:
1. Analyzes root cause
2. Drafts skill enhancement proposal
3. Creates GitHub PR with changes
4. Tracks review and approval
5. Monitors post-merge effectiveness

---

## Update Trigger Conditions

### Trigger 1: Weekly Scan (Scheduled)

**Frequency:** Every Monday 08:00 (via ORCHESTRATOR coordination)

**Process:**
```
1. Query GitHub Activity (past 7 days)
   - Commits touching skill-related code
   - Issues mentioning skill names
   - PRs that changed backend services used by skills

2. Analyze Escalation Logs
   - Which skills were invoked?
   - Did skills escalate to ARCHITECT?
   - How many times? For what reasons?

3. Check Skill Usage Metrics
   - Which skills used most/least?
   - Skill success rate (completed without errors)
   - Average execution time

4. Identify Anomalies
   - Skill failure rate >10% (needs improvement)
   - Skill not used in 30 days (candidate for deprecation)
   - Skill escalations increased >50% week-over-week
```

**Example Output:**
```
Weekly Scan Report - 2025-12-23

Skill Alerts:
- SCHEDULING skill: 8 escalations (up from 3 last week) +166%
  - Reason: "New constraint not in skill spec"
  - Action: Propose skill enhancement

- vacation-management skill: 0 invocations in 30 days
  - Reason: Low usage (Q4 vacation requests minimal)
  - Action: Monitor, no update needed

- test-writer skill: Failure rate 15% (above 10% threshold)
  - Reason: TypeScript examples outdated
  - Action: Propose documentation update
```

### Trigger 2: Post-Incident Review

**Frequency:** After any P0/P1 incident

**Process:**
```
1. Read Incident Report
   - Which skills were involved?
   - Did skills fail to prevent the issue?
   - What capability was missing?

2. Root Cause Analysis
   - Was skill spec incomplete?
   - Was workflow unclear?
   - Was error handling insufficient?

3. Extract Lessons Learned
   - What should skill have done differently?
   - What new workflow is needed?
   - What reference data should be added?

4. Draft Enhancement Proposal
   - Specific changes to prevent recurrence
   - Updated error handling
   - New validation steps
```

**Example:**
```
Incident: Schedule generation failed, violating 80-hour rule (2025-12-20)

Root Cause: SCHEDULING skill didn't validate rolling 4-week average

Skill Gap: Skill spec says "validate ACGME compliance" but doesn't specify rolling window calculation

Proposed Enhancement:
- Add Workflow: calculate-rolling-work-hours.md
- Add Reference: acgme-work-hour-formulas.md (with rolling average calculation)
- Update SKILL.md: Add "Rolling Work Hour Validation" capability
```

### Trigger 3: Manual Request

**Frequency:** Ad-hoc (when agent or human requests update)

**Process:**
```
1. Receive Update Request
   - Source: ARCHITECT, specialist agent (SCHEDULER, etc.), or human
   - Format: GitHub issue tagged "skill-enhancement"

2. Validate Request
   - Is this a skill update or new skill? (use ADDING_A_SKILL.md to decide)
   - Is the requested change in scope for the skill?
   - Does this conflict with existing capabilities?

3. Research Solution
   - How have similar projects solved this?
   - What tools/libraries can help?
   - Can we extend existing workflow vs. create new?

4. Draft Proposal
   - Use Improvement Proposal Template (see META_UPDATER.md)
   - Include before/after examples
   - Quantify expected impact
```

**Example:**
```
Request: "COMPLIANCE_VALIDATION skill should detect ACGME violations proactively, not just on-demand" (ARCHITECT, 2025-12-22)

Analysis:
- Current: Skill only runs when explicitly invoked
- Requested: Skill monitors schedule changes, auto-triggers validation
- Gap: No continuous monitoring workflow

Proposed Enhancement:
- Add Workflow: continuous-compliance-monitoring.md
- Add Reference: monitoring-thresholds.md (when to alert)
- Integrate with Celery background tasks (run validation every 4 hours)
```

### Trigger 4: Code Change Detection

**Frequency:** Automated (GitHub webhook on commits to `main`)

**Process:**
```
1. Detect Commits Affecting Skills
   - Changed files: backend/app/services/constraints/*.py
   - Skill potentially affected: SCHEDULING, COMPLIANCE_VALIDATION

2. Diff Analysis
   - What functions changed?
   - Do skill specs reference these functions?
   - Are skill examples still valid?

3. Validate Skill Alignment
   - Run skill examples against new code
   - Check if MCP tools still work
   - Verify API endpoints haven't changed

4. Propose Update (if misalignment detected)
   - Update skill examples
   - Update integration points
   - Add notes about new behavior
```

**Example:**
```
Commit: "Refactor ACGME validator to use async DB queries" (2025-12-21)
Files Changed: backend/app/validators/advanced_acgme.py

Affected Skills: COMPLIANCE_VALIDATION

Misalignment Detected:
- Skill examples use synchronous code: validate_schedule(db, schedule_id)
- New code requires async: await validate_schedule(db, schedule_id)

Proposed Update:
- Update all code examples in COMPLIANCE_VALIDATION/SKILL.md to use `await`
- Update Workflows/*.md with async patterns
- Add note: "As of v2.1.0, all validators are async"
```

---

## Signal Detection Process

### Signal 1: Constraint Violations

**What to Monitor:**
```sql
-- Query recent constraint violations
SELECT constraint_name, COUNT(*) AS violation_count
FROM acgme_violations
WHERE detected_at > NOW() - INTERVAL '7 days'
GROUP BY constraint_name
ORDER BY violation_count DESC;
```

**Interpretation:**
- **High violation count (>10/week)**: Constraint may be too strict or skill validation missing
- **New constraint violations**: New constraint added but skill not updated

**Example:**
```
Result:
constraint_name           | violation_count
NICU_FRIDAY_CLINIC        | 15
POST_CALL_BLOCKING        | 8
80_HOUR_RULE              | 2

Analysis:
- NICU_FRIDAY_CLINIC violations spiking (was 2/week, now 15)
- Likely cause: New constraint added but SCHEDULING skill doesn't enforce
- Action: Update SCHEDULING skill to validate NICU_FRIDAY_CLINIC before generation
```

**Skill Update Signal:**
```
IF violation_count > 10 AND constraint_name NOT IN (SELECT constraint_name FROM skill_constraints)
THEN propose_skill_update(skill="SCHEDULING", action="add_constraint_validation")
```

### Signal 2: Swap Failures

**What to Monitor:**
```sql
-- Query swap execution failures
SELECT failure_reason, COUNT(*) AS failure_count
FROM swap_executions
WHERE status = 'failed'
  AND executed_at > NOW() - INTERVAL '7 days'
GROUP BY failure_reason
ORDER BY failure_count DESC;
```

**Interpretation:**
- **Recurring failure reason (>5/week)**: Skill validation insufficient
- **New failure reason**: Edge case not handled

**Example:**
```
Result:
failure_reason                    | failure_count
Swap creates N-1 vulnerability    | 12
Overlapping call assignments      | 7
Resident on leave during swap     | 3

Analysis:
- N-1 vulnerability failures spiking
- SWAP_EXECUTION skill validates ACGME but not resilience impact
- Action: Update SWAP_EXECUTION to check health score delta before execution
```

**Skill Update Signal:**
```
IF failure_reason == "Swap creates N-1 vulnerability" AND failure_count > 5
THEN propose_skill_update(skill="SWAP_EXECUTION", action="add_resilience_validation")
```

### Signal 3: N-1 Fragility Increases

**What to Monitor:**
```python
# Weekly resilience scan
from app.resilience.n_minus_analysis import N1Analyzer

analyzer = N1Analyzer(db)
critical_residents = await analyzer.identify_critical_residents(
    start_date=date.today(),
    end_date=date.today() + timedelta(days=30)
)

critical_count = len(critical_residents)
```

**Interpretation:**
- **Critical count > 3**: Schedule is fragile, may need more robust generation
- **Critical count increasing week-over-week**: Scheduling algorithm not considering resilience

**Example:**
```
Weekly Critical Resident Count:
Week 1: 2 critical residents
Week 2: 3 critical residents
Week 3: 5 critical residents ← ALERT

Analysis:
- N-1 vulnerability increasing
- SCHEDULING skill not optimizing for resilience
- Action: Update SCHEDULING skill to include resilience scoring in objective function
```

**Skill Update Signal:**
```
IF critical_count > 3 AND (critical_count - last_week_count) >= 2
THEN propose_skill_update(skill="SCHEDULING", action="add_resilience_optimization")
```

### Signal 4: Agent Escalations

**What to Monitor:**
```
# Parse agent conversation logs for escalations
grep -r "Escalating to ARCHITECT" .claude/logs/ | \
  grep -oP 'Skill: \K\w+' | \
  sort | uniq -c | sort -rn
```

**Interpretation:**
- **Skill escalates >3 times/week**: Missing capability or unclear spec
- **Escalation reason repeats**: Specific gap in skill

**Example:**
```
Result:
5 SCHEDULING
3 COMPLIANCE_VALIDATION
1 test-writer

Analysis:
- SCHEDULING skill escalating 5 times this week (up from 1/week baseline)
- Common escalation reason: "How do I handle rotation-specific constraints?"
- Action: Add Workflow: add-custom-constraint.md to SCHEDULING skill
```

**Skill Update Signal:**
```
IF escalation_count > 3 AND escalation_reason.contains("How do I")
THEN propose_skill_update(skill=ESCALATING_SKILL, action="add_workflow", topic=escalation_reason)
```

---

## GitHub PR Format for Skill Updates

### PR Title Convention

```
skill: [SKILL_NAME] - [Brief description]
```

**Examples:**
- ✅ `skill: SCHEDULING - Add N-1 resilience optimization to generation workflow`
- ✅ `skill: COMPLIANCE_VALIDATION - Update async code examples`
- ✅ `skill: test-writer - Fix outdated TypeScript patterns`
- ❌ `Update skill` (too vague)
- ❌ `SCHEDULING improvements` (not clear it's a skill update)

### PR Description Template

```markdown
## Skill Enhancement Proposal

**Skill:** [SKILL_NAME]
**Version:** [Current] → [New] (e.g., 1.2.0 → 1.3.0)
**Type:** [Enhancement | Bug Fix | Documentation Update | Workflow Addition]
**Priority:** [P0 | P1 | P2 | P3]

---

## Problem Statement

**What issue are we solving?**
[Clear description of the gap or issue]

**Frequency:**
[How often does this occur? Quantify if possible]
- Constraint violations: [N per week]
- Escalations: [N per week]
- Failures: [N per week]

**Impact:**
[Who is affected? How much time wasted?]
- Affected agents: [List agents that use this skill]
- Time wasted: [Estimate hours/week]
- Risk if not fixed: [Description]

---

## Current State

**How does the skill work now?**
[Brief description]

**Why is this suboptimal?**
[Specific problems with current approach]

**Evidence:**
[Link to GitHub issues, commit history, incident reports, or logs]

---

## Proposed Changes

### Files Modified

- [ ] `.claude/skills/[SKILL_NAME]/SKILL.md` - [What changed]
- [ ] `.claude/skills/[SKILL_NAME]/Workflows/[workflow].md` - [What changed]
- [ ] `.claude/skills/[SKILL_NAME]/Reference/[reference].md` - [What changed]
- [ ] `.claude/skills/CORE/SKILL.md` - [Updated routing keywords / dependencies]

### Change Summary

**1. [Change Type] - [Component]**

**Before:**
```[language]
[Current code/text/workflow]
```

**After:**
```[language]
[Proposed code/text/workflow]
```

**Rationale:** [Why this change improves the skill]

**2. [Change Type] - [Component]**
[Repeat for each change]

---

## Benefits

- ✅ [Benefit 1: quantified if possible]
- ✅ [Benefit 2]
- ✅ [Benefit 3]

**Expected Impact:**
- Reduces [metric] by [percentage]
- Prevents [failure mode]
- Enables [new capability]

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| [Risk 1] | [Low/Med/High] | [Low/Med/High] | [How to mitigate] |
| [Risk 2] | [Low/Med/High] | [Low/Med/High] | [How to mitigate] |

**Backward Compatibility:**
- [ ] No breaking changes (skill interface unchanged)
- [ ] Breaking changes documented (version bump to [X.0.0])
- [ ] Migration guide provided (for agents using old patterns)

---

## Testing Checklist

- [ ] **Documentation review**: All sections complete, no TODOs
- [ ] **Examples validated**: Code examples run successfully
- [ ] **Integration tested**: MCP tools / API endpoints work
- [ ] **Workflow tested**: Step-by-step procedures verified
- [ ] **Error handling**: Common errors documented and tested

**Test Results:**
```
[Paste test output or link to test run]
```

---

## Rollback Plan

**If this update causes issues:**
1. [Rollback step 1]
2. [Rollback step 2]
3. [Rollback step 3]

**Rollback triggers:**
- Skill failure rate increases >20%
- Escalations spike >50%
- Integration breaks (MCP tools / API)

---

## Approval Required

- [ ] **ARCHITECT** (if architectural changes, dependencies, or workflow logic)
- [ ] **[Specialist Agent]** (e.g., SCHEDULER if updating SCHEDULING skill)
- [ ] **META_UPDATER** (self-review for documentation quality)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| [1.2.0] | [YYYY-MM-DD] | [Previous version summary] |
| [1.3.0] | [YYYY-MM-DD] | [This update] |

---

## References

- **Related Issues:** #[issue-number], #[issue-number]
- **Incident Reports:** [Link to incident post-mortem]
- **Code Changes:** [Link to backend PR if applicable]
- **Documentation:** [Link to related docs updates]

---

**Proposed by:** META_UPDATER
**Date:** YYYY-MM-DD
**Estimated Effort:** [Small (<2 hours) | Medium (2-8 hours) | Large (>8 hours)]
```

### PR Labels

All skill update PRs must have these labels:

| Label | When to Use |
|-------|-------------|
| `skill-enhancement` | Any skill update PR |
| `documentation` | If changes are doc-only (no logic changes) |
| `breaking-change` | If skill interface changes (major version bump) |
| `bug-fix` | If fixing incorrect skill behavior |
| `workflow-addition` | If adding new workflow to `Workflows/` directory |
| `high-priority` | If addressing P0/P1 incident or critical gap |

### PR File Organization

```
Files changed (typical skill update):

.claude/skills/SKILL_NAME/SKILL.md                  # Main spec update
.claude/skills/SKILL_NAME/Workflows/new-workflow.md # New workflow (if applicable)
.claude/skills/SKILL_NAME/Reference/new-ref.md      # New reference (if applicable)
.claude/skills/CORE/SKILL.md                        # Updated routing (if needed)
docs/SKILL_UPDATE_WORKFLOW.md                       # Update this doc if process changes
```

---

## Review and Approval Process

### Review Phases

#### Phase 1: Automated Checks (GitHub Actions)

```yaml
# .github/workflows/skill-update-check.yml
name: Skill Update Validation

on:
  pull_request:
    paths:
      - '.claude/skills/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Check YAML frontmatter
        run: |
          # Verify SKILL.md has valid YAML frontmatter
          python scripts/validate_skill_yaml.py

      - name: Check for TODOs
        run: |
          # Fail if TODO/FIXME found in updated skill files
          ! grep -r "TODO\|FIXME" .claude/skills/

      - name: Validate examples
        run: |
          # Run code examples to ensure they work
          python scripts/test_skill_examples.py

      - name: Check links
        run: |
          # Verify all internal links resolve
          markdown-link-check .claude/skills/**/*.md

      - name: Lint markdown
        run: |
          # Ensure consistent formatting
          markdownlint .claude/skills/**/*.md
```

**Auto-checks must pass before human review begins.**

#### Phase 2: Specialist Agent Review

**Who reviews:**
- **ARCHITECT**: If changes affect architecture, dependencies, or cross-skill integration
- **Specialist Agent**: Agent that commonly uses the skill (e.g., SCHEDULER reviews SCHEDULING updates)

**Review criteria:**
1. **Accuracy**: Is the proposed solution correct?
2. **Completeness**: Are all edge cases handled?
3. **Clarity**: Are instructions clear and unambiguous?
4. **Examples**: Are examples realistic and helpful?
5. **Integration**: Do integration points match reality (MCP tools, APIs)?

**Review format:**
```markdown
## Review: [REVIEWER_NAME]

**Approval Status:** [APPROVE | REQUEST_CHANGES | COMMENT]

### Strengths
- [What's good about this update]

### Concerns
- [Issues that need addressing]

### Suggestions
- [Optional improvements]

### Verification
- [ ] Examples tested and work
- [ ] Workflows are step-by-step clear
- [ ] Error handling comprehensive
- [ ] Integration points verified

**Final Recommendation:** [Merge | Hold | Reject]
```

#### Phase 3: META_UPDATER Self-Review

META_UPDATER reviews own PRs for:
- **Documentation quality**: Clear, well-formatted, no jargon
- **Consistency**: Follows patterns from existing skills
- **Completeness**: All template sections filled
- **Usability**: Can another agent use this skill effectively?

**Self-review checklist:**
- [ ] All sections of SKILL.md template present
- [ ] Examples are concrete (not placeholders)
- [ ] Error handling documented
- [ ] Success criteria defined
- [ ] Integration with other skills documented
- [ ] Version number incremented correctly

#### Phase 4: Human Review (Optional)

**When required:**
- Breaking changes (major version bump)
- Policy-related updates (ACGME, security)
- High-risk changes (production-critical skills)

**Human reviewers:**
- Faculty (for policy changes)
- Program Director (for ACGME-related changes)
- System Administrator (for infrastructure changes)

### Approval Criteria

**Approve (merge) when:**
- [ ] All automated checks pass
- [ ] At least 1 specialist agent approves
- [ ] META_UPDATER self-review complete
- [ ] No outstanding "Request Changes" reviews
- [ ] PR description complete
- [ ] Rollback plan documented

**Request Changes when:**
- Examples don't work
- Integration points incorrect
- Missing error handling
- Unclear instructions
- Breaking changes without migration guide

**Reject when:**
- Duplicate of existing capability
- Out of scope for skill
- Better solved by creating new skill
- Violates architectural principles

---

## Merging and Activation

### Merge Process

1. **Final Pre-Merge Check**
   ```bash
   # Run full test suite
   cd backend && pytest
   cd frontend && npm test

   # Verify skill examples
   python scripts/test_skill_examples.py

   # Check no merge conflicts
   git fetch origin main
   git merge origin/main
   ```

2. **Merge PR**
   ```bash
   # Squash merge (prefer for skill updates)
   gh pr merge [PR-number] --squash --delete-branch

   # OR merge commit (if preserving history important)
   gh pr merge [PR-number] --merge
   ```

3. **Tag Version**
   ```bash
   # If skill version bumped, tag the commit
   git tag -a skills/SKILL_NAME-v1.3.0 -m "skill: SKILL_NAME - Add N-1 resilience optimization"
   git push origin skills/SKILL_NAME-v1.3.0
   ```

### Activation Verification

**Immediately after merge:**

1. **Verify Skill Loads**
   ```bash
   # Check CORE/SKILL.md parses correctly
   python scripts/validate_core_registry.py

   # Verify routing keywords registered
   grep "SKILL_NAME" .claude/skills/CORE/SKILL.md
   ```

2. **Test Skill Invocation**
   ```bash
   # Simulate skill invocation
   python scripts/simulate_skill_invocation.py --skill SKILL_NAME --test-case happy-path
   ```

3. **Monitor for Errors**
   ```bash
   # Watch logs for skill-related errors (first 24 hours)
   docker-compose logs -f backend | grep -i "SKILL_NAME\|skill.*error"
   ```

### Rollout Strategy

**Immediate Rollout (Default):**
- Skill available to all agents as soon as PR merged
- Suitable for: bug fixes, documentation updates, workflow additions

**Gradual Rollout (High-Risk Updates):**
- Skill updated but flagged as "experimental"
- Test with 1-2 agents before full activation
- Suitable for: breaking changes, major refactors

**Experimental Flag:**
```yaml
# In SKILL.md frontmatter
---
name: SCHEDULING
version: 2.0.0
experimental: true  # Flag for gradual rollout
experimental_until: 2025-01-15
---
```

**Gradual activation process:**
```
Day 1: Merge PR, flag as experimental
Day 2-7: SCHEDULER agent uses new skill, monitors for issues
Day 8: Review feedback, fix issues if needed
Day 9: Remove experimental flag, full rollout
```

---

## Rollback Procedures

### When to Rollback

**Trigger rollback if within 48 hours of merge:**
- Skill failure rate increases >20% compared to baseline
- Critical integration breaks (MCP tools, API endpoints)
- Escalations spike >50% week-over-week
- Breaking change not caught in review

### Rollback Methods

#### Method 1: Git Revert (Preferred)

```bash
# Identify commit to revert
git log --oneline .claude/skills/SKILL_NAME/

# Revert the skill update commit
git revert [commit-hash]

# Push revert
git push origin main
```

**Advantages:**
- Preserves history
- Clear audit trail
- Easy to re-apply later

#### Method 2: Version Restore

```bash
# Restore previous version from git tag
git checkout skills/SKILL_NAME-v1.2.0 -- .claude/skills/SKILL_NAME/

# Commit restoration
git commit -m "rollback: Restore SKILL_NAME to v1.2.0 due to [reason]"
git push origin main
```

**When to use:**
- Multiple commits need reverting
- Clean slate desired

#### Method 3: Hotfix Branch

```bash
# Create hotfix branch from pre-update commit
git checkout -b hotfix/skill-SKILL_NAME [commit-before-update]

# Cherry-pick any critical fixes made since update
git cherry-pick [critical-fix-commit]

# Merge hotfix
git checkout main
git merge hotfix/skill-SKILL_NAME
git push origin main
```

**When to use:**
- Update partially good (keep some changes)
- Need to preserve critical fixes made since update

### Post-Rollback Actions

1. **Notify Stakeholders**
   ```markdown
   ## Rollback Notice: SKILL_NAME v1.3.0 → v1.2.0

   **Date:** YYYY-MM-DD HH:MM UTC
   **Reason:** [Brief reason for rollback]
   **Impact:** [What changed with rollback]

   **Next Steps:**
   - Root cause analysis (GitHub issue #XXX)
   - Fix in progress (ETA: [date])
   - Re-release as v1.3.1 (target: [date])

   **Affected Agents:**
   - [Agent 1]: [How to adapt]
   - [Agent 2]: [How to adapt]
   ```

2. **Create Incident Report**
   ```markdown
   ## Incident: SKILL_NAME v1.3.0 Rollback

   **Date:** YYYY-MM-DD
   **Severity:** P[0-3]
   **Duration:** [Time between merge and rollback]

   **Timeline:**
   - HH:MM: v1.3.0 merged to main
   - HH:MM: First failure detected
   - HH:MM: Failure rate exceeded threshold
   - HH:MM: Rollback initiated
   - HH:MM: v1.2.0 restored

   **Root Cause:**
   [Detailed analysis of what went wrong]

   **Lessons Learned:**
   1. [What we learned]
   2. [What to do differently next time]

   **Action Items:**
   - [ ] Fix root cause (assign to: [agent/human])
   - [ ] Improve testing (add test case for [scenario])
   - [ ] Update review checklist (add check for [gap])
   ```

3. **Update Skill Changelog**
   ```markdown
   ## Version History

   | Version | Date | Status | Changes |
   |---------|------|--------|---------|
   | 1.3.0 | 2025-12-26 | ROLLED BACK | N-1 optimization (rolled back due to [reason]) |
   | 1.2.0 | 2025-12-01 | ACTIVE | Added async examples |
   | 1.1.0 | 2025-11-15 | Deprecated | Initial version |
   ```

---

## Example: Updating SCHEDULING Skill with New Constraint

### Scenario

**Trigger:** Weekly scan detects recurring NICU Friday Clinic violations

**Signal Data:**
```
Constraint Violations (past 7 days):
- NICU_FRIDAY_CLINIC: 15 violations (up from 2/week baseline)

Root Cause:
- New institutional policy: All NICU residents must attend Friday clinic
- Policy added to database but SCHEDULING skill not updated
- Skill generates schedules violating new constraint
```

### Step 1: Analyze Root Cause

```
Current State:
- SCHEDULING skill validates Tier 1 (ACGME) and Tier 2 (institutional) constraints
- NICU_FRIDAY_CLINIC is Tier 2 institutional constraint
- Skill spec lists "FMIT Coverage, Night Float Headcount, Post-Call Blocking"
- NICU_FRIDAY_CLINIC not listed → skill doesn't validate

Gap:
- Skill spec outdated (doesn't include new constraint)
- No workflow for adding custom constraints
- Reference docs don't explain NICU clinic policy
```

### Step 2: Draft Skill Enhancement

**Proposed Changes:**

1. **SKILL.md Update:**
   - Add NICU_FRIDAY_CLINIC to Tier 2 constraint list
   - Document constraint logic and rationale

2. **Workflow Addition:**
   - Create `Workflows/add-custom-constraint.md`
   - Step-by-step guide for adding new constraints to schedule generation

3. **Reference Addition:**
   - Create `Reference/institutional-constraints.md`
   - Document all Tier 2 constraints with citations to policies

### Step 3: Create GitHub PR

**PR Title:**
```
skill: SCHEDULING - Add NICU Friday Clinic constraint validation
```

**PR Description:**
```markdown
## Skill Enhancement Proposal

**Skill:** SCHEDULING
**Version:** 1.4.0 → 1.5.0
**Type:** Enhancement (new constraint)
**Priority:** P1 (blocking schedule generation)

---

## Problem Statement

**What issue are we solving?**
NICU Friday Clinic constraint violations have spiked from 2/week to 15/week due to new institutional policy requiring all NICU residents to attend Friday clinic. SCHEDULING skill does not validate this constraint during generation.

**Frequency:**
- Constraint violations: 15 per week (7-day average)
- Escalations: 3 per week (SCHEDULER asking "How do I add this constraint?")

**Impact:**
- Affected agents: SCHEDULER (primary user of SCHEDULING skill)
- Time wasted: ~2 hours/week fixing violations manually
- Risk if not fixed: Continued policy violations, resident dissatisfaction

---

## Current State

**How does the skill work now?**
SCHEDULING skill validates:
- Tier 1: ACGME constraints (80-hour rule, 1-in-7 rule, etc.)
- Tier 2: Institutional constraints (FMIT coverage, Night Float, Post-Call Blocking)

**Why is this suboptimal?**
- NICU_FRIDAY_CLINIC is a Tier 2 institutional constraint but not listed in skill spec
- Skill generates schedules without validating this constraint
- Violations discovered only after schedule deployed

**Evidence:**
- GitHub Issue #487: "Add NICU Friday Clinic to institutional constraints"
- Constraint violation logs: 15 violations in past 7 days
- SCHEDULER escalation logs: 3 requests for "how to add custom constraint"

---

## Proposed Changes

### Files Modified

- [x] `.claude/skills/SCHEDULING/SKILL.md` - Add NICU_FRIDAY_CLINIC to Tier 2 constraints
- [x] `.claude/skills/SCHEDULING/Workflows/add-custom-constraint.md` - NEW workflow
- [x] `.claude/skills/SCHEDULING/Reference/institutional-constraints.md` - NEW reference
- [ ] `.claude/skills/CORE/SKILL.md` - No changes needed (routing unchanged)

### Change Summary

**1. Enhancement - SKILL.md**

**Before:**
```markdown
### Tier 2: Institutional Hard Constraints (HIGH)
- FMIT Coverage: Weekly faculty rotation
- Night Float Headcount: Exactly 1 resident
- Post-Call Blocking: Required recovery time
```

**After:**
```markdown
### Tier 2: Institutional Hard Constraints (HIGH)
- FMIT Coverage: Weekly faculty rotation
- Night Float Headcount: Exactly 1 resident
- NICU Friday Clinic: All NICU residents attend Friday 08:00-12:00
- Post-Call Blocking: Required recovery time
```

**Rationale:** Documents new constraint explicitly in skill spec

**2. Workflow Addition - add-custom-constraint.md**

New workflow provides step-by-step instructions for:
1. Adding constraint to database (`institutional_constraints` table)
2. Registering constraint in validator (`backend/app/services/constraints/institutional.py`)
3. Updating SCHEDULING skill spec
4. Testing constraint enforcement

**Rationale:** Prevents future escalations for "how do I add constraint?" question

**3. Reference Addition - institutional-constraints.md**

New reference documents all Tier 2 constraints:
- Constraint name
- Policy citation (e.g., "NICU Residency Handbook Section 4.2.1")
- Validation logic
- Historical context (when added, why)

**Rationale:** Centralizes institutional policy knowledge

---

## Benefits

- ✅ Reduces NICU Friday Clinic violations by 100% (prevents during generation)
- ✅ Saves ~2 hours/week in manual violation fixing
- ✅ Prevents SCHEDULER escalations for custom constraint questions
- ✅ Provides reusable workflow for future constraint additions

**Expected Impact:**
- Constraint violations: 15/week → 0/week
- SCHEDULER escalations: 3/week → 0/week
- Manual fix time: 2 hours/week → 0 hours/week

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Constraint too strict (over-constrains schedule) | Medium | Medium | Monitor schedule generation success rate; relax if <80% |
| Breaks existing schedules (retroactive violation) | Low | Low | Only apply to future schedules (start_date > today) |
| Unclear workflow (agents don't follow) | Low | Low | Test workflow with SCHEDULER before merge |

**Backward Compatibility:**
- [x] No breaking changes (skill interface unchanged)
- [ ] Breaking changes documented (N/A)
- [ ] Migration guide provided (N/A)

---

## Testing Checklist

- [x] **Documentation review**: All sections complete, no TODOs
- [x] **Examples validated**: Workflow tested with SCHEDULER agent
- [x] **Integration tested**: Backend constraint validator updated and tested
- [x] **Workflow tested**: Step-by-step procedures verified
- [x] **Error handling**: Constraint violation error message clear and actionable

**Test Results:**
```
Test: Generate Block 11 schedule with NICU Friday Clinic constraint
Result: PASS (all NICU residents assigned to clinic Friday 08:00-12:00)

Test: Generate schedule violating constraint (force NICU resident to different rotation Friday AM)
Result: FAIL with error "NICU_FRIDAY_CLINIC violated: PGY2-04 assigned to EM instead of clinic"

Test: Follow add-custom-constraint.md workflow to add test constraint
Result: PASS (SCHEDULER successfully added TEST_CONSTRAINT)
```

---

## Rollback Plan

**If this update causes issues:**
1. `git revert [commit-hash]` to restore v1.4.0
2. Remove NICU_FRIDAY_CLINIC from backend validator
3. Resume manual violation fixing until v1.5.1 fix ready

**Rollback triggers:**
- Schedule generation success rate drops <80%
- Constraint validation errors spike >10/day
- SCHEDULER reports workflow unclear

---

## Approval Required

- [x] **ARCHITECT** (reviewed workflow addition)
- [x] **SCHEDULER** (tested workflow, confirmed helpful)
- [x] **META_UPDATER** (self-review complete)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.4.0 | 2025-12-15 | Added async schedule generation |
| 1.5.0 | 2025-12-26 | Added NICU Friday Clinic constraint + custom constraint workflow |

---

## References

- **Related Issues:** #487
- **Incident Reports:** N/A
- **Code Changes:** PR #512 (backend constraint validator)
- **Documentation:** `backend/docs/INSTITUTIONAL_CONSTRAINTS.md`

---

**Proposed by:** META_UPDATER
**Date:** 2025-12-26
**Estimated Effort:** Small (<2 hours)
```

### Step 4: Review Process

**Phase 1: Automated Checks**
```
✅ YAML frontmatter valid
✅ No TODOs found
✅ Code examples run successfully
✅ All links resolve
✅ Markdown linting passed
```

**Phase 2: Specialist Review (SCHEDULER)**
```markdown
## Review: SCHEDULER

**Approval Status:** APPROVE

### Strengths
- Workflow is crystal clear (step-by-step with examples)
- Solves recurring problem (asked 3 times how to add constraints)
- Reference doc helpful (all constraints in one place)

### Concerns
- None

### Suggestions
- Consider adding constraint template (boilerplate code for new constraints)

### Verification
- [x] Examples tested and work
- [x] Workflows are step-by-step clear
- [x] Error handling comprehensive
- [x] Integration points verified

**Final Recommendation:** Merge
```

**Phase 3: META_UPDATER Self-Review**
```
✅ All sections present
✅ Examples concrete (NICU Friday Clinic, not generic)
✅ Error handling documented
✅ Success criteria defined
✅ Integration verified
✅ Version incremented (1.4.0 → 1.5.0)
```

### Step 5: Merge and Activate

```bash
# Merge PR
gh pr merge 515 --squash --delete-branch

# Tag version
git tag -a skills/SCHEDULING-v1.5.0 -m "skill: SCHEDULING - Add NICU Friday Clinic constraint"
git push origin skills/SCHEDULING-v1.5.0

# Verify activation
python scripts/validate_core_registry.py
# ✅ SCHEDULING skill v1.5.0 loaded successfully
```

### Step 6: Monitor Post-Update

**Day 1 (Immediate):**
```
Metrics:
- Schedule generation attempts: 5
- Schedule generation successes: 5 (100%)
- NICU_FRIDAY_CLINIC violations: 0
- SCHEDULER escalations: 0

Status: ✅ No issues detected
```

**Week 1 (7 days post-merge):**
```
Metrics:
- Schedule generation success rate: 98% (baseline: 95%)
- NICU_FRIDAY_CLINIC violations: 0 (baseline: 15/week)
- SCHEDULER escalations: 0 (baseline: 3/week)

Status: ✅ Update successful, exceeded expectations
```

**Outcome:**
```
✅ Constraint violations eliminated
✅ SCHEDULER no longer escalates for custom constraint questions
✅ Schedule generation success rate improved (+3%)
✅ No rollback needed

Action: Document success in monthly retrospective
```

---

## Monitoring Post-Update

### Metrics to Track

**Week 1 (Days 1-7):**
```sql
-- Skill invocation success rate
SELECT
    skill_name,
    COUNT(*) AS invocations,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS successes,
    ROUND(100.0 * SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate
FROM skill_invocations
WHERE skill_name = 'SCHEDULING'
  AND invoked_at > (SELECT merged_at FROM skill_updates WHERE skill_name = 'SCHEDULING' ORDER BY merged_at DESC LIMIT 1)
GROUP BY skill_name;
```

**Expected:** Success rate ≥95% (if lower, investigate)

**Week 1: Escalation frequency**
```bash
# Count escalations mentioning the updated skill
grep -r "Escalating.*SCHEDULING" .claude/logs/ | \
  grep -A 5 "$(date -d '7 days ago' +%Y-%m-%d)" | \
  wc -l
```

**Expected:** Escalations ≤ baseline (if higher, skill may be unclear)

**Week 1: Error rate**
```sql
-- Error frequency
SELECT
    error_type,
    COUNT(*) AS error_count
FROM skill_errors
WHERE skill_name = 'SCHEDULING'
  AND occurred_at > (SELECT merged_at FROM skill_updates WHERE skill_name = 'SCHEDULING' ORDER BY merged_at DESC LIMIT 1)
GROUP BY error_type
ORDER BY error_count DESC;
```

**Expected:** No new error types (if new errors, may indicate bugs)

### Week 2-4: Trend Analysis

```python
# Compare metrics pre- vs. post-update
from app.analytics.skill_metrics import compare_skill_versions

comparison = compare_skill_versions(
    skill_name="SCHEDULING",
    version_before="1.4.0",
    version_after="1.5.0",
    metric="success_rate"
)

print(f"Success rate change: {comparison.delta}%")
print(f"Statistical significance: {comparison.p_value < 0.05}")

# If p_value < 0.05 and delta > 0: Update improved performance ✅
# If p_value < 0.05 and delta < 0: Update degraded performance ❌ (consider rollback)
```

### Feedback Collection

**Agent Feedback:**
```markdown
## Skill Update Feedback: SCHEDULING v1.5.0

**Agent:** SCHEDULER
**Date:** 2025-12-30 (4 days post-update)

**What's working well:**
- Custom constraint workflow crystal clear
- No more escalations for "how to add constraint?"
- NICU Friday Clinic violations eliminated

**What could be better:**
- Workflow assumes familiarity with backend code structure
- Would be helpful to have constraint template (boilerplate)

**Overall Rating:** 9/10

**Recommendation:** Keep update, consider adding constraint template in v1.6.0
```

### Continuous Improvement

**Month 1: Identify Gaps**
```
Observed patterns (first 30 days):
- SCHEDULER uses add-custom-constraint workflow 3 times
- Each time, SCHEDULER modifies constraint template code slightly
- Opportunity: Extract constraint template into reusable boilerplate

Action: Propose v1.6.0 enhancement (add constraint template)
```

**Month 3: Performance Review**
```
3-Month Metrics (v1.5.0):
- Invocations: 156
- Success rate: 97.4% (baseline: 95.1%) ← +2.3%
- Escalations: 2 (baseline: 12) ← -83%
- NICU violations: 0 (baseline: 60 over 3 months) ← -100%

Outcome: ✅ Update highly successful
Action: No changes needed, document success in quarterly retrospective
```

---

## Summary: Skill Update Lifecycle

```
1. Trigger Detection
   ├─ Weekly scan (automated)
   ├─ Post-incident review
   ├─ Manual request
   └─ Code change detection

2. Signal Analysis
   ├─ Quantify frequency/impact
   ├─ Identify root cause
   └─ Assess if skill update appropriate

3. Proposal Draft
   ├─ Use Improvement Proposal Template
   ├─ Include before/after examples
   └─ Quantify expected benefits

4. GitHub PR Creation
   ├─ Follow PR title convention
   ├─ Complete PR description template
   └─ Add appropriate labels

5. Review Process
   ├─ Automated checks (GitHub Actions)
   ├─ Specialist agent review
   ├─ META_UPDATER self-review
   └─ Human review (if needed)

6. Merge & Activate
   ├─ Final pre-merge checks
   ├─ Squash merge PR
   ├─ Tag version
   └─ Verify activation

7. Monitor Post-Update
   ├─ Track success rate (Week 1)
   ├─ Monitor escalations (Week 1-4)
   ├─ Collect feedback (Month 1)
   └─ Performance review (Month 3)

8. Iterate
   ├─ Identify gaps from usage
   ├─ Propose next version
   └─ Continuous improvement
```

---

**Questions? Issues?**
- See `.claude/Agents/META_UPDATER.md` for META_UPDATER responsibilities
- See `docs/ADDING_A_SKILL.md` for skill creation guidance
- See `docs/RETIRING_SKILLS.md` for deprecation procedures

---

*This workflow is maintained by META_UPDATER and updated as skill update processes evolve.*
