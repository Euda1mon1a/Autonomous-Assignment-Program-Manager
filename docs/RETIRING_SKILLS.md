# Retiring Skills - Deprecation and Archival Procedures

> **Purpose:** Document how to deprecate, archive, and remove obsolete skills from the PAI system
> **Audience:** META_UPDATER agent, ARCHITECT, system maintainers
> **Last Updated:** 2025-12-26

---

## Table of Contents

1. [When to Retire a Skill](#when-to-retire-a-skill)
2. [Deprecation Markers and Warnings](#deprecation-markers-and-warnings)
3. [Migration Path Documentation](#migration-path-documentation)
4. [Archive Location and Structure](#archive-location-and-structure)
5. [GitHub Issue Template for Retirement](#github-issue-template-for-retirement)
6. [Grace Period and Timeline](#grace-period-and-timeline)
7. [Removal Process](#removal-process)
8. [Example: Retiring OLD_COMPLIANCE_CHECKER](#example-retiring-old_compliance_checker)
9. [Post-Retirement Monitoring](#post-retirement-monitoring)

---

## When to Retire a Skill

### Retirement Criteria

Retire a skill when ANY of these conditions are met:

#### 1. Superseded by Better Skill

**Indicators:**
- New skill provides same functionality with improvements
- Old skill no longer maintained
- Usage migrated to new skill (>90% of invocations)

**Example:**
```
Old: old-compliance-checker (basic ACGME validation)
New: COMPLIANCE_VALIDATION (comprehensive audit workflows, historical analysis, remediation)

Result: Retire old-compliance-checker (superseded)
```

#### 2. No Usage in Extended Period

**Indicators:**
- Zero invocations in past 90 days
- No agents reference skill in recent conversations
- No integration points with active code

**Example:**
```
Skill: legacy-pdf-generator
Last invocation: 2024-09-15 (>90 days ago)
Reason: System migrated to new pdf skill
Result: Retire legacy-pdf-generator (unused)
```

**Query to detect unused skills:**
```sql
-- Find skills not invoked in 90 days
SELECT skill_name, MAX(invoked_at) AS last_used
FROM skill_invocations
GROUP BY skill_name
HAVING MAX(invoked_at) < NOW() - INTERVAL '90 days'
ORDER BY last_used ASC;
```

#### 3. Functionality Moved to Core System

**Indicators:**
- Skill's capability now built into backend/frontend
- No longer need separate skill (integrated into workflows)
- Skill becomes redundant

**Example:**
```
Skill: email-sender (sent notification emails)
Change: Email notifications integrated into backend service
Result: Retire email-sender (functionality in core system)
```

#### 4. Policy or Technology Obsolete

**Indicators:**
- ACGME policy changed, rendering skill obsolete
- Technology deprecated (e.g., API sunset)
- Regulatory requirement removed

**Example:**
```
Skill: covid-rotation-handler (handled COVID-19 rotation adjustments)
Change: COVID-19 special rotations no longer exist (policy ended)
Result: Retire covid-rotation-handler (policy obsolete)
```

#### 5. Security or Compliance Risk

**Indicators:**
- Skill uses vulnerable libraries (no fix available)
- Skill violates updated security policy
- Skill exposes sensitive data

**Example:**
```
Skill: legacy-auth-helper (used deprecated auth library)
Risk: Library has critical CVE, no patch available
Result: Immediate retirement (security risk)
```

### Retirement Decision Matrix

| Condition | Usage Last 90 Days | Replacement Available | Risk Level | Action |
|-----------|-------------------|----------------------|------------|--------|
| Superseded | >0 | Yes | Low | Deprecate → Migrate → Retire |
| Superseded | 0 | Yes | Low | Immediate Retire |
| Unused | 0 | N/A | Low | Deprecate → Retire (30-day grace) |
| Obsolete | Any | N/A | Any | Deprecate → Archive (document history) |
| Security Risk | Any | N/A | **High** | **Immediate Retire** (no grace period) |

---

## Deprecation Markers and Warnings

### Phase 1: Deprecation Announcement

**When:** As soon as retirement decision made

**What to update:**

#### 1. SKILL.md - Add Deprecation Notice

```yaml
---
name: old-compliance-checker
description: DEPRECATED - Use COMPLIANCE_VALIDATION instead. This skill will be removed on 2025-03-01.
version: 1.5.0
deprecated: true
deprecation_date: 2025-01-15
sunset_date: 2025-03-01
replacement: COMPLIANCE_VALIDATION
migration_guide: docs/skills/migration/old-to-new-compliance.md
---
```

Add prominent deprecation banner at top of SKILL.md:

```markdown
---
name: old-compliance-checker
deprecated: true
---

# ⚠️ DEPRECATED: old-compliance-checker

> **This skill is deprecated and will be removed on 2025-03-01.**
>
> **Use instead:** `COMPLIANCE_VALIDATION` skill
>
> **Migration guide:** [docs/skills/migration/old-to-new-compliance.md](../../skills/migration/old-to-new-compliance.md)
>
> **Questions?** Contact META_UPDATER or ARCHITECT

---

# old-compliance-checker Skill (Deprecated)

[Rest of skill documentation...]
```

#### 2. CORE/SKILL.md - Mark as Deprecated

Update skill registry with deprecation warning:

```markdown
### G. Deprecated Skills (Do Not Use)

#### 99. Old Compliance Checker (`old-compliance-checker`) ⚠️ DEPRECATED

**Status:** Deprecated as of 2025-01-15, sunset date 2025-03-01

**Replacement:** Use `COMPLIANCE_VALIDATION` skill instead

**Migration Guide:** [docs/skills/migration/old-to-new-compliance.md](../../skills/migration/old-to-new-compliance.md)

**Purpose (Historical):** Basic ACGME compliance validation

**Why Deprecated:** Superseded by COMPLIANCE_VALIDATION skill which provides comprehensive audit workflows, historical analysis, and violation remediation. old-compliance-checker only performed basic validation without remediation guidance.

**Last Supported Version:** 1.5.0

---
```

#### 3. Routing Logic - Add Deprecation Warning

Update routing table to warn agents:

```markdown
| Keywords | Skill | Notes |
|----------|-------|-------|
| compliance, ACGME, validation | `COMPLIANCE_VALIDATION` | ⚠️ `old-compliance-checker` is deprecated |
```

### Phase 2: Runtime Warnings (if skill invoked)

**Implement deprecation warning in skill invocation:**

```python
# .claude/skills/old-compliance-checker/SKILL.md (execution wrapper)

import warnings
from datetime import date

DEPRECATION_MESSAGE = """
⚠️  WARNING: Skill 'old-compliance-checker' is DEPRECATED

This skill will be removed on 2025-03-01.

Replacement: Use 'COMPLIANCE_VALIDATION' skill instead
Migration guide: docs/skills/migration/old-to-new-compliance.md

This warning will become an error on 2025-03-01.
"""

def invoke_skill():
    # Check if past sunset date
    sunset_date = date(2025, 3, 1)
    if date.today() >= sunset_date:
        raise DeprecationError(
            "Skill 'old-compliance-checker' has been removed. "
            "Use 'COMPLIANCE_VALIDATION' instead."
        )

    # Issue warning
    warnings.warn(DEPRECATION_MESSAGE, DeprecationWarning, stacklevel=2)

    # Continue with skill execution (until sunset)
    ...
```

### Phase 3: Communication

**Announce deprecation to all agents:**

```markdown
## Deprecation Notice: old-compliance-checker

**Date:** 2025-01-15
**From:** META_UPDATER
**Audience:** All agents (especially SCHEDULER, QA_TESTER)

---

### Summary

The `old-compliance-checker` skill is **deprecated** and will be removed on **2025-03-01** (45 days from now).

### Replacement

Use the `COMPLIANCE_VALIDATION` skill instead. It provides all capabilities of old-compliance-checker plus:
- Comprehensive audit workflows
- Historical compliance analysis
- Violation remediation guidance
- Systematic reporting

### Migration Guide

**Step-by-step migration:** [docs/skills/migration/old-to-new-compliance.md](docs/skills/migration/old-to-new-compliance.md)

**Quick comparison:**

| Task | old-compliance-checker | COMPLIANCE_VALIDATION |
|------|------------------------|----------------------|
| Validate schedule | `validate_schedule(id)` | `audit_current_schedule(id)` |
| Check violations | `get_violations()` | `Workflows/audit-current-schedule.md` |
| Remediate | ❌ Not supported | ✅ `Workflows/violation-remediation.md` |

### Timeline

- **2025-01-15** (Today): Deprecation announced
- **2025-02-01** (17 days): Reminder sent
- **2025-02-15** (31 days): Final warning
- **2025-03-01** (45 days): Skill removed (invocation will fail)

### Questions?

Contact META_UPDATER or ARCHITECT.

---
```

---

## Migration Path Documentation

### Migration Guide Template

Create comprehensive migration guide in `docs/skills/migration/`:

```markdown
# Migration Guide: old-compliance-checker → COMPLIANCE_VALIDATION

> **Audience:** Agents using old-compliance-checker
> **Sunset Date:** 2025-03-01 (old-compliance-checker will be removed)
> **Estimated Migration Time:** 1-2 hours

---

## Why Migrate?

The `old-compliance-checker` skill is deprecated. The `COMPLIANCE_VALIDATION` skill provides:
- ✅ Comprehensive audit workflows (not just basic validation)
- ✅ Historical compliance analysis (trend detection)
- ✅ Violation remediation guidance (actionable fixes)
- ✅ Systematic reporting (consistent output format)

---

## Breaking Changes

| Feature | old-compliance-checker | COMPLIANCE_VALIDATION | Migration Action |
|---------|------------------------|----------------------|------------------|
| **Invocation** | `validate_schedule(id)` | `audit_current_schedule(id)` | Update function call |
| **Output format** | Plain text | Structured JSON + formatted report | Update parsers |
| **Error handling** | Throws exception | Returns violation list | Update error handling |
| **Workflows** | None | `Workflows/audit-current-schedule.md` | Follow new workflow |

---

## Step-by-Step Migration

### Step 1: Update Skill Invocation

**Before (old-compliance-checker):**
```python
from old_compliance_checker import validate_schedule

result = validate_schedule(schedule_id="block-10")

if result.has_violations:
    print(f"Violations: {result.violations}")
```

**After (COMPLIANCE_VALIDATION):**
```python
from COMPLIANCE_VALIDATION import audit_current_schedule

# Use workflow instead of direct function call
result = audit_current_schedule(schedule_id="block-10")

if result.overall_status != "COMPLIANT":
    print(f"Tier 1 Violations: {result.tier1_violations}")
    print(f"Tier 2 Violations: {result.tier2_violations}")
```

### Step 2: Update Output Parsing

**Before (old-compliance-checker output):**
```
Violations:
- 80-hour rule violated for PGY2-03
- 1-in-7 rule violated for PGY3-01
```

**After (COMPLIANCE_VALIDATION output):**
```json
{
  "overall_status": "VIOLATION",
  "tier1_violations": [
    {
      "rule": "80_HOUR_RULE",
      "person_id": "PGY2-03",
      "details": "84 hours worked in week of 2025-03-15"
    }
  ],
  "tier2_violations": [
    {
      "rule": "1_IN_7_RULE",
      "person_id": "PGY3-01",
      "details": "No 24-hour off period in past 7 days"
    }
  ],
  "recommendations": [
    "Reduce PGY2-03 shift hours by 4 hours",
    "Grant PGY3-01 24-hour off period immediately"
  ]
}
```

**Migration code:**
```python
# Parse new format
if result.overall_status == "VIOLATION":
    for violation in result.tier1_violations:
        print(f"{violation.rule} violated for {violation.person_id}: {violation.details}")

    # Get remediation guidance (new feature!)
    for recommendation in result.recommendations:
        print(f"→ {recommendation}")
```

### Step 3: Follow New Workflows

**Before:** Direct function calls

**After:** Follow systematic workflows in `COMPLIANCE_VALIDATION/Workflows/`

**Example: Monthly compliance audit**

1. Read workflow: `COMPLIANCE_VALIDATION/Workflows/audit-current-schedule.md`
2. Follow steps:
   - Load schedule data
   - Run Tier 1/2 validators
   - Generate violation report
   - Classify by severity
   - Get remediation recommendations
3. Document findings

### Step 4: Update Error Handling

**Before (old-compliance-checker):**
```python
try:
    result = validate_schedule(schedule_id)
except ScheduleNotFoundError:
    print("Schedule not found")
except ValidationError as e:
    print(f"Validation failed: {e}")
```

**After (COMPLIANCE_VALIDATION):**
```python
# New skill returns violations instead of throwing exceptions
result = audit_current_schedule(schedule_id)

if result is None:
    print("Schedule not found")
elif result.overall_status == "ERROR":
    print(f"Audit failed: {result.error_message}")
else:
    # Process violations
    process_violations(result)
```

### Step 5: Update Integration Points

**Before:** Direct database queries

**After:** Use MCP tools (if available)

```python
# Before
result = validate_schedule(db, schedule_id)

# After (using MCP tool)
result = mcp__validate_acgme_compliance(schedule_id=schedule_id)

# OR use API endpoint
response = requests.post(
    "http://localhost:8000/api/compliance/validate",
    json={"schedule_id": schedule_id}
)
result = response.json()
```

---

## Validation Checklist

After migration, verify:

- [ ] All invocations of `old-compliance-checker` replaced
- [ ] Output parsing updated to handle new format
- [ ] Error handling updated (no exceptions for violations)
- [ ] Workflows followed (not just direct function calls)
- [ ] Integration points updated (MCP tools / API)
- [ ] Tests updated to use new skill
- [ ] No references to old skill in codebase

**Search for remaining references:**
```bash
# Find any remaining old-compliance-checker references
grep -r "old-compliance-checker" .claude/ backend/ frontend/

# Should return zero results after migration
```

---

## Rollback Plan

If migration causes issues, you can temporarily use old skill until 2025-03-01:

1. Revert skill invocations to old-compliance-checker
2. Create GitHub issue describing migration problem
3. Contact META_UPDATER for assistance
4. Complete migration before sunset date (2025-03-01)

**Note:** After 2025-03-01, old-compliance-checker will be removed. No rollback possible.

---

## Help & Support

**Questions?**
- Contact META_UPDATER agent
- GitHub issue: [#XXX - old-compliance-checker migration support](https://github.com/...)

**Common Issues:**
- [Migration FAQ](docs/skills/migration/compliance-checker-faq.md)
- [Troubleshooting guide](docs/skills/migration/compliance-checker-troubleshooting.md)

---

*This migration guide is maintained by META_UPDATER.*
```

---

## Archive Location and Structure

### Archive Directory

```
.claude/skills/ARCHIVE/
├── README.md                           # Archive index
├── old-compliance-checker/             # Archived skill
│   ├── RETIREMENT_NOTICE.md            # Why retired, when, replacement
│   ├── SKILL.md                        # Original skill spec (frozen)
│   ├── Workflows/                      # Original workflows (if any)
│   └── Reference/                      # Original reference docs (if any)
├── legacy-pdf-generator/               # Another archived skill
│   ├── RETIREMENT_NOTICE.md
│   └── SKILL.md
└── covid-rotation-handler/
    ├── RETIREMENT_NOTICE.md
    ├── SKILL.md
    └── Reference/
        └── covid-policies-2020-2023.md  # Historical reference
```

### Archive Index (README.md)

```markdown
# Skill Archive

This directory contains deprecated and retired skills. These skills are no longer active but preserved for historical reference.

---

## Archived Skills

| Skill Name | Retirement Date | Reason | Replacement | Documents Preserved |
|------------|-----------------|--------|-------------|---------------------|
| old-compliance-checker | 2025-03-01 | Superseded | COMPLIANCE_VALIDATION | SKILL.md, migration guide |
| legacy-pdf-generator | 2025-01-15 | Unused (90+ days) | pdf | SKILL.md |
| covid-rotation-handler | 2024-12-31 | Policy obsolete | N/A | SKILL.md, Reference docs |

---

## Why Archive Instead of Delete?

Archived skills provide:
- **Historical context**: Understanding how system evolved
- **Migration reference**: For systems still using old patterns
- **Lessons learned**: What worked, what didn't, why retired
- **Audit trail**: Compliance and regulatory documentation

---

## Accessing Archived Skills

**View archived skill:**
```bash
cat .claude/skills/ARCHIVE/old-compliance-checker/SKILL.md
```

**Search archive:**
```bash
grep -r "keyword" .claude/skills/ARCHIVE/
```

**Restore archived skill (emergency only):**
```bash
# Copy from archive back to active skills
cp -r .claude/skills/ARCHIVE/old-compliance-checker .claude/skills/

# Update CORE/SKILL.md to re-register

# Create GitHub issue documenting why restoration needed
```

---

## Retention Policy

Archived skills retained for:
- **Superseded skills**: 2 years (for migration reference)
- **Unused skills**: 1 year (in case usage resumes)
- **Obsolete skills**: Indefinitely (historical record)
- **Security risks**: 6 months (document vulnerability, then purge)

After retention period, skills may be permanently deleted.

---

*Archive maintained by META_UPDATER.*
```

### Retirement Notice Template

Create `RETIREMENT_NOTICE.md` for each archived skill:

```markdown
# Retirement Notice: old-compliance-checker

---

## Retirement Summary

**Skill Name:** old-compliance-checker
**Retirement Date:** 2025-03-01
**Last Supported Version:** 1.5.0
**Deprecation Announced:** 2025-01-15 (45-day notice)

---

## Reason for Retirement

**Category:** Superseded by better skill

**Details:**
The `old-compliance-checker` skill provided basic ACGME compliance validation but lacked:
- Systematic audit workflows
- Historical compliance analysis
- Violation remediation guidance
- Consistent output formatting

The `COMPLIANCE_VALIDATION` skill (introduced 2024-12-01) addressed all these gaps and became the preferred solution. By 2025-01-15, 95% of compliance validation invocations used the new skill.

**Usage Statistics:**
```
old-compliance-checker invocations:
- 2024-11: 45 invocations
- 2024-12: 12 invocations (after COMPLIANCE_VALIDATION released)
- 2025-01: 2 invocations (migration nearly complete)
```

---

## Replacement

**Use Instead:** `COMPLIANCE_VALIDATION` skill

**Migration Guide:** [docs/skills/migration/old-to-new-compliance.md](../../migration/old-to-new-compliance.md)

**Key Improvements:**
- Comprehensive audit workflows (3 systematic workflows vs. ad-hoc validation)
- Historical analysis (trend detection, compliance metrics over time)
- Violation remediation (actionable steps, not just error messages)
- Structured output (JSON format vs. plain text)

---

## Historical Context

### When Created
**Date:** 2023-05-12
**Creator:** Initial PAI system setup
**Purpose:** Provide ACGME compliance validation for early schedule generation

### Evolution
| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2023-05-12 | Initial release (80-hour rule, 1-in-7 rule) |
| 1.2.0 | 2023-08-20 | Added supervision ratio validation |
| 1.4.0 | 2024-03-15 | Added duty period limits |
| 1.5.0 | 2024-07-10 | Bug fixes (final version) |

### Peak Usage
**Date:** 2024-06 (78 invocations/month)
**Primary User:** SCHEDULER agent

### Decline
**Date:** 2024-12 (COMPLIANCE_VALIDATION released)
**Migration completed:** 2025-01 (95% of usage migrated)

---

## Lessons Learned

### What Worked Well
- Simple, focused scope (basic validation only)
- Easy to understand and use
- Reliable (few bugs after v1.2.0)

### What Could Be Improved
- Lacked systematic workflows (agents had to figure out when/how to validate)
- No remediation guidance (agents got violations but not fixes)
- Plain text output (hard to parse programmatically)
- No historical analysis (couldn't track compliance trends)

### Applied to COMPLIANCE_VALIDATION
- ✅ Added systematic workflows (audit, analyze, remediate phases)
- ✅ Included remediation guidance (actionable recommendations)
- ✅ Structured output (JSON format)
- ✅ Historical analysis (trend charts, compliance metrics over time)

---

## Preserved Artifacts

**What's Archived:**
- Original SKILL.md specification
- Version history and changelog
- Migration guide to COMPLIANCE_VALIDATION
- This retirement notice

**What's NOT Archived:**
- Backend code (preserved in git history if needed)
- Test files (preserved in git history)
- Temporary working files

**Access:**
`.claude/skills/ARCHIVE/old-compliance-checker/`

---

## Emergency Restoration

**If restoration needed:**
1. Copy from archive: `cp -r .claude/skills/ARCHIVE/old-compliance-checker .claude/skills/`
2. Re-register in CORE/SKILL.md
3. Create GitHub issue explaining why restoration needed
4. Notify META_UPDATER

**Restoration criteria:**
- Critical bug in replacement skill (COMPLIANCE_VALIDATION)
- Emergency rollback required
- Temporary bridge while fixing replacement

**Note:** Restoration is temporary. Address root cause and migrate back to replacement skill.

---

**Retirement Executed By:** META_UPDATER
**Approved By:** ARCHITECT, SCHEDULER (primary user)
**Date:** 2025-03-01

---

*This notice preserved for historical reference.*
```

---

## GitHub Issue Template for Retirement

### Issue Title

```
[RETIREMENT] Deprecate and retire [SKILL_NAME] by [SUNSET_DATE]
```

### Issue Template

```markdown
## Skill Retirement Proposal

**Skill Name:** [SKILL_NAME]
**Current Version:** [X.Y.Z]
**Proposed Sunset Date:** [YYYY-MM-DD] (XX days from now)
**Proposed By:** META_UPDATER
**Date:** [YYYY-MM-DD]

---

## Retirement Rationale

**Category:** [Superseded | Unused | Obsolete | Security Risk]

**Details:**
[Detailed explanation of why skill should be retired]

**Evidence:**
- Usage statistics: [invocations/month for past 6 months]
- Last invocation: [date]
- Replacement available: [Yes/No - if yes, name the replacement]
- Security risk: [Yes/No - if yes, describe CVE or vulnerability]

---

## Impact Analysis

**Affected Agents:**
- [Agent 1]: [How they use this skill, migration path]
- [Agent 2]: [How they use this skill, migration path]

**Affected Workflows:**
- [Workflow 1]: [What changes needed]

**Affected Systems:**
- Backend code: [List files/modules that reference this skill]
- MCP tools: [List MCP tools that use this skill]
- API endpoints: [List endpoints that depend on this skill]

**Estimated Migration Effort:**
- Agent migration: [Hours per agent]
- Codebase updates: [Hours]
- Testing: [Hours]
- **Total:** [Hours]

---

## Migration Plan

**Replacement Skill:** [REPLACEMENT_SKILL_NAME] (or "None" if functionality obsolete)

**Migration Steps:**
1. [Step 1: e.g., Update agents to use new skill]
2. [Step 2: e.g., Update backend code references]
3. [Step 3: e.g., Update tests]
4. [Step 4: e.g., Verify all integrations work with new skill]

**Migration Guide:** [Link to migration guide, or "To be created"]

**Migration Support:**
- Point of contact: [META_UPDATER or specialist agent]
- Timeline: [Start date] to [End date]
- Grace period: [XX days]

---

## Timeline

| Date | Milestone | Actions |
|------|-----------|---------|
| [YYYY-MM-DD] | Deprecation announced | Add deprecation markers, notify agents |
| [YYYY-MM-DD+14] | Reminder #1 | Check migration progress, offer support |
| [YYYY-MM-DD+28] | Reminder #2 | Final warning, escalate if needed |
| [YYYY-MM-DD+42] | Pre-retirement check | Verify all migrations complete |
| [YYYY-MM-DD+45] | **Sunset date** | **Remove skill, archive** |

**Grace Period:** 45 days (standard) OR [X days if emergency retirement]

---

## Deprecation Checklist

### Documentation Updates
- [ ] Add deprecation notice to SKILL.md (YAML frontmatter + banner)
- [ ] Update CORE/SKILL.md (mark as deprecated, add warning)
- [ ] Create migration guide (if replacement exists)
- [ ] Update routing keywords (warn about deprecation)

### Communication
- [ ] Post deprecation announcement (notify all agents)
- [ ] Send reminder #1 (14 days before sunset)
- [ ] Send reminder #2 (28 days before sunset)
- [ ] Send final warning (42 days before sunset)

### Migration Support
- [ ] Migration guide complete and tested
- [ ] Affected agents contacted
- [ ] Migration support available (META_UPDATER)
- [ ] Track migration progress (GitHub project board)

### Pre-Retirement Verification
- [ ] All affected agents migrated
- [ ] No invocations in past 7 days
- [ ] All integration points updated
- [ ] Tests updated (no references to old skill)

---

## Rollback Plan

**If retirement needs to be postponed:**
1. Extend sunset date by [XX days]
2. Update deprecation markers with new date
3. Notify agents of extension
4. Document reason for extension

**Rollback triggers:**
- Migration not complete by sunset date
- Critical dependency discovered
- Replacement skill has blocking bugs

---

## Archive Plan

**Archive Location:** `.claude/skills/ARCHIVE/[SKILL_NAME]/`

**Artifacts to Preserve:**
- [ ] SKILL.md (original spec, frozen)
- [ ] Workflows/ (if any)
- [ ] Reference/ (if any)
- [ ] RETIREMENT_NOTICE.md (why retired, when, replacement)
- [ ] Migration guide (for future reference)

**Retention Period:** [X years based on category]

---

## Approval Required

- [ ] **META_UPDATER** (self-review)
- [ ] **ARCHITECT** (architectural approval)
- [ ] **Affected Agents** (migration feasibility)
- [ ] **Faculty** (if policy-related skill)

---

## References

- **Usage statistics:** [Link to metrics dashboard or SQL query]
- **Replacement skill:** [Link to COMPLIANCE_VALIDATION/SKILL.md]
- **Migration guide:** [Link to docs/skills/migration/...]
- **Related issues:** [List related GitHub issues]

---

**Labels:** `skill-retirement`, `deprecation`, `[category: superseded|unused|obsolete|security]`

**Assignee:** META_UPDATER
**Reviewers:** ARCHITECT, [Affected Agents]

---

*This issue tracks the retirement of [SKILL_NAME]. All updates and progress will be documented here.*
```

---

## Grace Period and Timeline

### Standard Timeline (Non-Emergency)

```
Day 0: Deprecation Announced
├─ Add deprecation markers (SKILL.md, CORE/SKILL.md)
├─ Create GitHub issue
├─ Post announcement to all agents
└─ Create migration guide

Day 14: Reminder #1
├─ Email/notify affected agents
├─ Check migration progress (how many agents migrated?)
├─ Offer migration support
└─ Update GitHub issue with progress

Day 28: Reminder #2
├─ Send final warning
├─ Escalate to ARCHITECT if migration blocked
├─ Offer direct assistance (pair programming, debugging)
└─ Update GitHub issue

Day 42: Pre-Retirement Check
├─ Verify zero invocations in past 7 days
├─ Verify all integration points updated
├─ Verify all tests updated (no old skill references)
└─ Final approval from ARCHITECT

Day 45: Sunset Date
├─ Move skill to ARCHIVE/
├─ Remove from CORE/SKILL.md active list
├─ Update routing (remove keywords)
├─ Create RETIREMENT_NOTICE.md
├─ Close GitHub issue
└─ Post retirement confirmation
```

### Emergency Timeline (Security Risk)

```
Day 0: Security Issue Discovered
├─ Assess severity (CVE score, exploitability)
├─ If CRITICAL: Immediate retirement (no grace period)
└─ If HIGH: Abbreviated timeline (7-day grace period)

Day 0 (Immediate Retirement):
├─ Remove skill from active directory
├─ Update CORE/SKILL.md (mark as REMOVED for security)
├─ Archive with security notice
├─ Notify all agents (emergency notification)
├─ Document workaround or replacement
└─ Create incident report

Day 0-7 (Abbreviated Timeline):
├─ Day 0: Deprecation + security advisory
├─ Day 3: Migration support + progress check
├─ Day 7: Forced retirement (no extensions)
```

### Extension Policy

**When to extend sunset date:**
- Migration blocked by dependency issue
- Replacement skill has critical bug
- Unforeseen integration complexity

**Extension process:**
1. Create GitHub issue documenting reason
2. Propose new sunset date (typically +30 days)
3. Get ARCHITECT approval
4. Update deprecation markers with new date
5. Notify all affected agents
6. Document in retirement issue

**Maximum extensions:** 2 (total grace period ≤120 days)

---

## Removal Process

### Step 1: Final Verification (Day 42)

```bash
# Check for recent invocations
python scripts/check_skill_usage.py --skill old-compliance-checker --days 7

# Expected output: 0 invocations
```

```bash
# Search codebase for references
grep -r "old-compliance-checker" .claude/ backend/ frontend/

# Expected output: None (or only in migration guide / archive)
```

```bash
# Check test files
grep -r "old-compliance-checker" backend/tests/ frontend/__tests__/

# Expected output: None
```

**If any references found:**
- Contact owners of referencing code
- Require migration before sunset date
- Consider extending sunset date if justified

### Step 2: Move to Archive (Day 45)

```bash
# Create archive directory if not exists
mkdir -p .claude/skills/ARCHIVE/old-compliance-checker

# Move skill directory
mv .claude/skills/old-compliance-checker/* .claude/skills/ARCHIVE/old-compliance-checker/

# Create RETIREMENT_NOTICE.md
cat > .claude/skills/ARCHIVE/old-compliance-checker/RETIREMENT_NOTICE.md << 'EOF'
[Use RETIREMENT_NOTICE template from earlier section]
EOF

# Remove original directory
rmdir .claude/skills/old-compliance-checker
```

### Step 3: Update CORE/SKILL.md

**Remove from active skills list:**
```markdown
# BEFORE
#### 15. Old Compliance Checker (`old-compliance-checker`)
...

# AFTER (moved to Deprecated Skills section)
### G. Deprecated Skills (Archived)

#### old-compliance-checker ⚠️ RETIRED 2025-03-01
**Replacement:** COMPLIANCE_VALIDATION
**Archive:** .claude/skills/ARCHIVE/old-compliance-checker/
```

**Remove routing keywords:**
```markdown
# BEFORE
| compliance, ACGME | `old-compliance-checker` OR `COMPLIANCE_VALIDATION` |

# AFTER
| compliance, ACGME | `COMPLIANCE_VALIDATION` |
```

### Step 4: Update Documentation

```bash
# Update migration guide (mark as complete)
echo "Migration complete: 2025-03-01" >> docs/skills/migration/old-to-new-compliance.md

# Update CHANGELOG
echo "- RETIRED: old-compliance-checker skill (replaced by COMPLIANCE_VALIDATION)" >> CHANGELOG.md
```

### Step 5: Create Retirement PR

```markdown
## Retirement PR: old-compliance-checker

**Title:** `retire: old-compliance-checker skill (superseded by COMPLIANCE_VALIDATION)`

**Description:**
Retires the `old-compliance-checker` skill after 45-day deprecation period.

**Retirement Summary:**
- Deprecated: 2025-01-15
- Sunset: 2025-03-01
- Reason: Superseded by COMPLIANCE_VALIDATION
- Migration: 100% complete (0 invocations in past 7 days)

**Changes:**
- [x] Moved skill to .claude/skills/ARCHIVE/
- [x] Created RETIREMENT_NOTICE.md
- [x] Updated CORE/SKILL.md (removed from active, added to deprecated)
- [x] Removed routing keywords
- [x] Updated CHANGELOG.md

**Verification:**
```bash
# No recent invocations
python scripts/check_skill_usage.py --skill old-compliance-checker --days 7
# Output: 0 invocations

# No codebase references
grep -r "old-compliance-checker" .claude/ backend/ frontend/
# Output: None (except in ARCHIVE/)
```

**Approval Required:**
- [x] META_UPDATER (self-review)
- [x] ARCHITECT (architectural approval)
- [ ] Faculty (if needed)

**Labels:** `skill-retirement`, `archived`

---

*This PR completes the retirement of old-compliance-checker.*
```

### Step 6: Merge and Announce

```bash
# Merge retirement PR
gh pr merge [PR-number] --squash --delete-branch

# Tag retirement
git tag -a skills/old-compliance-checker-RETIRED-v1.5.0 \
  -m "Retired old-compliance-checker skill (superseded by COMPLIANCE_VALIDATION)"
git push origin skills/old-compliance-checker-RETIRED-v1.5.0

# Post retirement announcement
gh issue comment [retirement-issue] --body "✅ Skill retired successfully. Archived at .claude/skills/ARCHIVE/old-compliance-checker/"

# Close retirement issue
gh issue close [retirement-issue]
```

---

## Example: Retiring OLD_COMPLIANCE_CHECKER

### Complete Walkthrough

#### Day 0: Deprecation Decision (2025-01-15)

**Trigger:** Weekly scan detects 95% of compliance validation now uses COMPLIANCE_VALIDATION

**Analysis:**
```python
# Usage comparison
old_skill_invocations = 2  # Past 30 days
new_skill_invocations = 87  # Past 30 days

migration_percentage = new_skill_invocations / (old_skill_invocations + new_skill_invocations)
# Result: 97.8% migrated

# Decision: Retire old-compliance-checker
```

**Actions:**
1. Create GitHub issue: `[RETIREMENT] Deprecate old-compliance-checker by 2025-03-01`
2. Add deprecation markers to SKILL.md
3. Create migration guide
4. Post announcement

#### Day 0: Deprecation Markers Added

**SKILL.md updated:**
```yaml
---
name: old-compliance-checker
deprecated: true
deprecation_date: 2025-01-15
sunset_date: 2025-03-01
replacement: COMPLIANCE_VALIDATION
migration_guide: docs/skills/migration/old-to-new-compliance.md
---
```

**CORE/SKILL.md updated:**
```markdown
### G. Deprecated Skills

#### old-compliance-checker ⚠️ DEPRECATED
**Sunset Date:** 2025-03-01
**Replacement:** COMPLIANCE_VALIDATION
**Migration:** [Guide](docs/skills/migration/old-to-new-compliance.md)
```

**Migration guide created:**
- Step-by-step migration instructions
- Before/after code examples
- Validation checklist

#### Day 0: Announcement Posted

```markdown
## Deprecation Announcement: old-compliance-checker

**To:** All agents (especially SCHEDULER, QA_TESTER)
**From:** META_UPDATER
**Date:** 2025-01-15

The `old-compliance-checker` skill is **deprecated** and will be **removed on 2025-03-01** (45 days).

**Replacement:** COMPLIANCE_VALIDATION skill

**Migration Guide:** [docs/skills/migration/old-to-new-compliance.md]

**Timeline:**
- 2025-01-15: Deprecation announced (today)
- 2025-01-29: Reminder #1 (14 days)
- 2025-02-12: Reminder #2 (28 days)
- 2025-03-01: Skill removed (45 days)

**Questions?** Contact META_UPDATER
```

#### Day 14: Reminder #1 (2025-01-29)

**Check migration progress:**
```python
invocations_past_7_days = check_skill_usage("old-compliance-checker", days=7)
# Result: 1 invocation

# Identify agent still using old skill
last_user = get_last_skill_user("old-compliance-checker")
# Result: QA_TESTER (1 invocation on 2025-01-27)
```

**Contact QA_TESTER:**
```markdown
Hi QA_TESTER,

Reminder: `old-compliance-checker` will be retired in **31 days** (2025-03-01).

I noticed you invoked it on 2025-01-27. Need help migrating to COMPLIANCE_VALIDATION?

Migration guide: [link]

Let me know if you have questions!

- META_UPDATER
```

**QA_TESTER response:**
```
Thanks for the reminder! I was testing legacy code. I'll migrate this week.
```

#### Day 28: Reminder #2 (2025-02-12)

**Check migration progress:**
```python
invocations_past_7_days = check_skill_usage("old-compliance-checker", days=7)
# Result: 0 invocations ✅
```

**Send final warning:**
```markdown
## Final Reminder: old-compliance-checker Retirement

**To:** All agents
**Retirement Date:** 2025-03-01 (17 days)

The `old-compliance-checker` skill will be removed in **17 days**.

**Good news:** No invocations detected in past 7 days ✅

**Action Required:** Verify all code/tests updated (no references to old skill)

**Questions?** Last chance for migration support - contact META_UPDATER

- META_UPDATER
```

#### Day 42: Pre-Retirement Check (2025-02-26)

**Final verification:**
```bash
# Check invocations
python scripts/check_skill_usage.py --skill old-compliance-checker --days 7
# Output: 0 invocations ✅

# Search codebase
grep -r "old-compliance-checker" .claude/ backend/ frontend/
# Output:
#   docs/skills/migration/old-to-new-compliance.md (migration guide - OK)
#   CHANGELOG.md (deprecation notice - OK)
# ✅ No active references

# Check tests
grep -r "old-compliance-checker" backend/tests/ frontend/__tests__/
# Output: None ✅

# Verify replacement skill works
python scripts/test_skill.py --skill COMPLIANCE_VALIDATION
# Output: All tests passed ✅
```

**Approval:**
```markdown
## Pre-Retirement Approval Request

**Skill:** old-compliance-checker
**Sunset Date:** 2025-03-01 (3 days)

**Verification Results:**
✅ Zero invocations (past 7 days)
✅ No codebase references (except migration guide)
✅ No test references
✅ Replacement skill (COMPLIANCE_VALIDATION) fully functional

**Ready for retirement?**

- META_UPDATER
```

**ARCHITECT approval:**
```
✅ Approved. Proceed with retirement on 2025-03-01.
```

#### Day 45: Retirement Execution (2025-03-01)

**Execute retirement:**
```bash
# Move to archive
mkdir -p .claude/skills/ARCHIVE/old-compliance-checker
mv .claude/skills/old-compliance-checker/* .claude/skills/ARCHIVE/old-compliance-checker/
rmdir .claude/skills/old-compliance-checker

# Create RETIREMENT_NOTICE.md
cat > .claude/skills/ARCHIVE/old-compliance-checker/RETIREMENT_NOTICE.md << 'EOF'
# Retirement Notice: old-compliance-checker

**Retired:** 2025-03-01
**Reason:** Superseded by COMPLIANCE_VALIDATION
**Last Version:** 1.5.0

[Full retirement notice content...]
EOF

# Update CORE/SKILL.md
# (Remove from active skills, add to deprecated section)

# Update CHANGELOG
echo "- RETIRED: old-compliance-checker (replaced by COMPLIANCE_VALIDATION)" >> CHANGELOG.md

# Create retirement PR
gh pr create --title "retire: old-compliance-checker skill" --body "[PR template content]"

# Merge PR
gh pr merge --squash

# Tag retirement
git tag -a skills/old-compliance-checker-RETIRED-v1.5.0 -m "Retired old-compliance-checker"
git push origin skills/old-compliance-checker-RETIRED-v1.5.0
```

**Post retirement announcement:**
```markdown
## Retirement Complete: old-compliance-checker

**Date:** 2025-03-01

The `old-compliance-checker` skill has been **successfully retired**.

**Archived Location:** `.claude/skills/ARCHIVE/old-compliance-checker/`

**Replacement:** COMPLIANCE_VALIDATION skill

**Final Statistics:**
- Deprecation period: 45 days
- Migration success: 100% (0 invocations at retirement)
- Issues encountered: None

**Thank you** to all agents who migrated smoothly!

If you need historical reference, the archived skill is preserved at:
`.claude/skills/ARCHIVE/old-compliance-checker/`

- META_UPDATER
```

**Close retirement issue:**
```bash
gh issue close [retirement-issue-number]
```

**Outcome:**
```
✅ Skill retired successfully
✅ Zero disruption (all migrations complete)
✅ Archive preserved for historical reference
✅ COMPLIANCE_VALIDATION fully adopted
```

---

## Post-Retirement Monitoring

### Week 1: Monitor for Errors

**Check for attempts to invoke retired skill:**
```bash
# Monitor logs for old skill references
docker-compose logs backend | grep -i "old-compliance-checker"

# Check error logs
tail -f backend/logs/error.log | grep -i "skill.*not found.*old-compliance-checker"
```

**Expected:** Zero errors (if errors found, investigate)

**If errors detected:**
1. Identify source (which agent/code attempting to invoke)
2. Verify that code should have been updated during migration
3. Fix reference or provide guidance
4. Document in lessons learned

### Month 1: Verify Replacement Adoption

**Check COMPLIANCE_VALIDATION usage:**
```sql
-- Compare invocations before vs. after retirement
SELECT
    DATE_TRUNC('month', invoked_at) AS month,
    skill_name,
    COUNT(*) AS invocations
FROM skill_invocations
WHERE skill_name IN ('old-compliance-checker', 'COMPLIANCE_VALIDATION')
  AND invoked_at >= '2025-01-01'
GROUP BY month, skill_name
ORDER BY month, skill_name;
```

**Expected:**
```
month   | skill_name              | invocations
2025-01 | old-compliance-checker  | 2
2025-01 | COMPLIANCE_VALIDATION   | 87
2025-02 | old-compliance-checker  | 0
2025-02 | COMPLIANCE_VALIDATION   | 95
2025-03 | COMPLIANCE_VALIDATION   | 102
```

**Interpretation:**
- ✅ old-compliance-checker usage dropped to zero
- ✅ COMPLIANCE_VALIDATION usage increased (+17% growth)
- ✅ Smooth transition, no functionality lost

### Quarter 1: Lessons Learned

**Retrospective:**
```markdown
## Retirement Retrospective: old-compliance-checker

**Date:** 2025-04-01 (1 month post-retirement)

### What Went Well
✅ Clear migration guide (no agent confusion)
✅ Adequate grace period (45 days sufficient)
✅ Proactive communication (reminders at Day 14, 28)
✅ Zero disruption (100% migration before sunset)

### What Could Be Improved
⚠️ Migration guide could include video walkthrough
⚠️ Automated migration script (reduce manual effort)

### Metrics
- Deprecation period: 45 days
- Migration success rate: 100%
- Errors after retirement: 0
- Replacement adoption: 102 invocations/month (vs. 89 baseline)

### Lessons for Future Retirements
1. Migration guide is critical (invest time upfront)
2. 45-day grace period is appropriate for superseded skills
3. Direct contact with affected agents speeds migration
4. Pre-retirement verification checklist prevents issues

### Action Items
- [ ] Add video walkthrough template to retirement workflow
- [ ] Create automated migration script template
- [ ] Update RETIRING_SKILLS.md with lessons learned

---

*Retrospective conducted by META_UPDATER*
```

### Retention Review (Annual)

**Check if archived skills can be purged:**
```markdown
## Archive Retention Review - 2026-03-01

**Skill:** old-compliance-checker
**Retirement Date:** 2025-03-01 (1 year ago)
**Category:** Superseded
**Retention Policy:** 2 years

**Access Log (past year):**
- Archive accessed: 2 times (both for historical research)
- Migration guide accessed: 5 times (new agents learning migration patterns)

**Recommendation:** Retain for 1 more year (useful for migration reference)

**Next Review:** 2027-03-01
```

---

## Summary: Skill Retirement Lifecycle

```
1. Retirement Decision
   ├─ Trigger: Weekly scan, security issue, manual request
   ├─ Analysis: Usage stats, replacement available, impact
   └─ Create GitHub retirement issue

2. Deprecation Announcement (Day 0)
   ├─ Add deprecation markers (SKILL.md, CORE/SKILL.md)
   ├─ Create migration guide
   ├─ Post announcement to all agents
   └─ Set sunset date (typically +45 days)

3. Migration Support (Days 0-45)
   ├─ Day 14: Reminder #1, check progress
   ├─ Day 28: Reminder #2, final warning
   └─ Ongoing: Offer migration assistance

4. Pre-Retirement Check (Day 42)
   ├─ Verify zero invocations
   ├─ Search codebase (no active references)
   ├─ Test replacement skill
   └─ Get ARCHITECT approval

5. Retirement Execution (Day 45)
   ├─ Move skill to ARCHIVE/
   ├─ Create RETIREMENT_NOTICE.md
   ├─ Update CORE/SKILL.md (remove from active)
   ├─ Remove routing keywords
   ├─ Create retirement PR, merge
   └─ Post retirement announcement

6. Post-Retirement Monitoring
   ├─ Week 1: Check for errors
   ├─ Month 1: Verify replacement adoption
   ├─ Quarter 1: Lessons learned retrospective
   └─ Annual: Retention review (purge or keep)

7. Archive Maintenance
   ├─ Preserve skill for historical reference
   ├─ Retain for policy period (1-2 years)
   └─ Purge after retention period (if appropriate)
```

---

**Questions? Issues?**
- See `.claude/Agents/META_UPDATER.md` for retirement responsibilities
- See `docs/ADDING_A_SKILL.md` for skill creation guidance
- See `docs/SKILL_UPDATE_WORKFLOW.md` for update procedures

---

*This retirement workflow is maintained by META_UPDATER and updated as retirement processes evolve.*
