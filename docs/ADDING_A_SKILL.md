# Adding a New Skill to the Personal AI Infrastructure

> **Purpose:** Complete guide for creating new Skills in the PAI system
> **Audience:** AI agents, developers, system maintainers
> **Last Updated:** 2025-12-26

---

## Table of Contents

1. [When to Create a New Skill](#when-to-create-a-new-skill)
2. [Skill vs. Existing Capabilities](#skill-vs-existing-capabilities)
3. [Directory Structure Requirements](#directory-structure-requirements)
4. [SKILL.md Template and Specification](#skillmd-template-and-specification)
5. [Workflow File Template](#workflow-file-template)
6. [Reference File Template](#reference-file-template)
7. [Registering in CORE/SKILL.md](#registering-in-coreskillmd)
8. [Testing Checklist](#testing-checklist)
9. [Example: VACATION_MANAGEMENT Skill](#example-vacation_management-skill)
10. [Common Pitfalls](#common-pitfalls)

---

## When to Create a New Skill

### Create a NEW Skill When:

✅ **Domain-Specific Expertise Required**
- The task requires specialized knowledge (e.g., ACGME compliance, resilience scoring)
- Generic capabilities are insufficient
- Domain has unique workflows, terminology, or rules

✅ **Recurring Pattern Identified**
- Same type of task performed ≥3 times per month
- Clear workflow emerges from repeated executions
- Knowledge can be codified into reusable procedures

✅ **Multi-Step Process with Decision Points**
- Task involves 3+ sequential steps
- Each step has conditional logic or validation
- Failures require specific recovery procedures

✅ **Integration with Specialized Tools**
- Task uses MCP tools specific to a domain (e.g., `mcp__resilience_check_health`)
- Custom API endpoints exist for this domain
- Database tables or schemas are domain-specific

✅ **Quality Gates or Compliance Enforcement**
- Task ensures regulatory compliance (ACGME, HIPAA)
- Task enforces architectural standards (security, testing)
- Task prevents known failure modes

### ADD TO Existing Skill When:

❌ **Capability is a Simple Extension**
- New functionality fits naturally within existing skill scope
- Shares same workflows, just different parameters
- No new domain knowledge required

❌ **One-Off or Rare Task**
- Performed <2 times per month
- No clear pattern or workflow
- Better handled by general capabilities

❌ **Already Covered by Composition**
- Task = combination of 2+ existing skills
- No unique logic beyond orchestration
- Better solved by sequential skill invocation

---

## Skill vs. Existing Capabilities

### Decision Matrix

| Scenario | Solution |
|----------|----------|
| **"How do I calculate work hours?"** | General capabilities (read code, explain) |
| **"Validate this schedule for ACGME compliance"** | `acgme-compliance` skill (regulatory expertise) |
| **"Fix these failing tests"** | `automated-code-fixer` skill (systematic debugging) |
| **"Create tests for new feature"** | `test-writer` skill (test generation patterns) |
| **"Generate schedule + validate + deploy"** | Skill composition (orchestrate 3 skills) |
| **"Manage resident vacation requests with blackout dates"** | **NEW SKILL** (specialized workflow) |

### Before Creating a Skill: Ask These Questions

1. **Does this require domain expertise that general capabilities lack?**
   - If NO → Use general capabilities
   - If YES → Skill candidate

2. **Will this task be performed repeatedly?**
   - If <2x/month → General capabilities
   - If ≥3x/month → Skill candidate

3. **Does this integrate with specialized tools/APIs?**
   - If NO → General capabilities
   - If YES → Skill candidate

4. **Can existing skills handle this via composition?**
   - If YES → Document composition pattern, no new skill
   - If NO → Skill candidate

5. **Does this enforce quality gates or compliance?**
   - If YES → Strongly consider creating skill
   - If NO → Evaluate other criteria

---

## Directory Structure Requirements

### Simple Skill Structure

Use for skills with straightforward workflows and minimal supporting documentation:

```
.claude/skills/SKILL_NAME/
└── SKILL.md                    # Complete skill definition
```

**When to use:**
- Single workflow or process
- Minimal supporting documentation needed
- No complex reference data
- Examples: `test-writer`, `changelog-generator`, `pdf`

### Complex Skill Structure

Use for skills with multiple workflows, extensive reference material, or step-by-step procedures:

```
.claude/skills/SKILL_NAME/
├── SKILL.md                    # Main skill definition
├── Workflows/                  # Step-by-step procedures
│   ├── workflow-1.md
│   ├── workflow-2.md
│   └── workflow-3.md
├── Reference/                  # Knowledge base
│   ├── glossary.md
│   ├── thresholds.md
│   └── historical-data.md
└── Tools/                      # Optional: CLI scripts
    └── helper-script.sh
```

**When to use:**
- Multiple distinct workflows (≥3)
- Extensive reference documentation (rules, thresholds, formulas)
- Historical data or benchmarks needed
- Examples: `RESILIENCE_SCORING`, `COMPLIANCE_VALIDATION`, `SCHEDULING`

### Workflow Directory Guidelines

**What belongs in Workflows/:**
- Step-by-step execution procedures
- Conditional logic and decision trees
- Integration instructions (API calls, MCP tools)
- Error handling and recovery procedures
- Success criteria and validation steps

**Naming convention:** `{action}-{object}.md`
- ✅ `audit-current-schedule.md`
- ✅ `n1-failure-simulation.md`
- ✅ `compute-health-score.md`
- ❌ `workflow1.md` (too generic)
- ❌ `process.md` (unclear purpose)

### Reference Directory Guidelines

**What belongs in Reference/:**
- Glossaries and terminology
- Rules and regulations (e.g., ACGME citations)
- Thresholds and constants
- Formulas and calculations
- Historical benchmarks
- Decision matrices

**Naming convention:** `{category}-{type}.md`
- ✅ `acgme-rules-detailed.md`
- ✅ `metric-definitions.md`
- ✅ `thresholds.md`
- ✅ `historical-resilience.md`

### Tools Directory (Optional)

**What belongs in Tools/:**
- Helper scripts for common operations
- Data transformation utilities
- One-off analysis scripts
- Testing utilities

**Note:** Only include if tools are skill-specific and not part of main codebase.

---

## SKILL.md Template and Specification

### YAML Frontmatter (Optional but Recommended)

```yaml
---
name: SKILL_NAME
description: One-sentence description of skill purpose. Use when [trigger condition]. Ensures [outcome].
version: 1.0.0
category: [Schedule Analysis | Code Quality | Security | Infrastructure | Workflow]
dependencies: [list of required skills or none]
---
```

### Complete SKILL.md Template

```markdown
---
name: SKILL_NAME
description: One-sentence description. Use when [trigger]. Ensures [outcome].
version: 1.0.0
category: [Category]
dependencies: []
---

# SKILL_NAME Skill

## Metadata

- **Name**: SKILL_NAME
- **Version**: 1.0.0
- **Category**: [Category]
- **Dependencies**: [List skills this depends on, or "None"]

## Description

[2-3 sentence overview of what this skill does and why it exists]

## Purpose

[Detailed explanation of the problem this skill solves. Answer:]
- What gap does this fill?
- Who uses this skill?
- What outcomes does it enable?

## When to Use This Skill

Invoke this skill when:
- ✅ [Trigger condition 1]
- ✅ [Trigger condition 2]
- ✅ [Trigger condition 3]
- ✅ [Trigger condition 4]

Do NOT use for:
- ❌ [Anti-pattern 1 - use X skill instead]
- ❌ [Anti-pattern 2 - use general capabilities]
- ❌ [Anti-pattern 3 - this is out of scope]

## Core Capabilities

### Capability 1: [Name]
[Description of what this does]

**Input:** [What data is required]
**Output:** [What is produced]
**Example:**
```bash
[Example command or code]
```

### Capability 2: [Name]
[Description]

**Input:** [Data required]
**Output:** [What is produced]
**Example:**
```python
[Example code]
```

## Skill Phases (if multi-step workflow)

### Phase 1: [Phase Name]
**Input**: [What's needed to start]
**Output**: [What's produced]
**Workflow**: `Workflows/phase-1-workflow.md` (if complex skill)

[Brief description of phase]

### Phase 2: [Phase Name]
**Input**: [Output from Phase 1]
**Output**: [Final result or input to Phase 3]
**Workflow**: `Workflows/phase-2-workflow.md`

[Brief description]

## Key Files and Integration Points

### Backend Code (if applicable)
```
backend/app/[module]/
├── [key_file_1.py]        # [Description]
├── [key_file_2.py]        # [Description]
└── [key_file_3.py]        # [Description]
```

### Database Tables Used (if applicable)
- `[table_name]` - [Purpose]
- `[table_name]` - [Purpose]

### MCP Tools (if available)
- `mcp__[tool_name]` - [Purpose]
- `mcp__[tool_name]` - [Purpose]

### API Endpoints (if applicable)
- `GET /api/[endpoint]` - [Purpose]
- `POST /api/[endpoint]` - [Purpose]

## Output Formats

### [Output Type 1]
```json
{
  "field1": "value",
  "field2": 123,
  "nested": {
    "field3": "value"
  }
}
```

### [Output Type 2]
```
[Text-based output format example]
```

## Error Handling

### Common Errors

**Error: [Error message or type]**
```
Cause: [Root cause]
Fix: [How to resolve]
Command: [Example fix command]
```

**Error: [Error message or type]**
```
Cause: [Root cause]
Fix: [How to resolve]
SQL: [Example SQL query to diagnose]
```

### Recovery Procedures

**If [condition occurs]:**
1. [Recovery step 1]
2. [Recovery step 2]
3. [Recovery step 3]

**If [condition occurs]:**
1. [Recovery step 1]
2. [Recovery step 2]

## Integration with Other Skills

### Workflow: [Common Use Case]
```
1. [Step using Skill A]
2. [Step using this skill]
3. [Step using Skill B]
4. [Final step]
```

### Workflow: [Another Use Case]
```
1. [Skill composition pattern]
2. [This skill's role]
```

## Reference Documents (if complex skill)

- **[reference-file-1.md]**: [What information it contains]
- **[reference-file-2.md]**: [What information it contains]

## Quick Start Examples

### Example 1: [Use Case Name]
```bash
# Via MCP tool (if available)
[command]

# Via API
[curl command]

# Expected output: [Description]
```

### Example 2: [Use Case Name]
```python
# Python usage example
[code]
```

## Success Criteria

This skill is successfully applied when:
- ✅ [Criterion 1]
- ✅ [Criterion 2]
- ✅ [Criterion 3]
- ✅ [Criterion 4]

## Notes

- **[Important consideration 1]**
- **[Important consideration 2]**
- **[Important consideration 3]**

---

*This skill [complements/extends/enforces] [related system or concept].*
```

---

## Workflow File Template

Use this template for files in the `Workflows/` directory:

```markdown
# Workflow: [Workflow Name]

> **Note:** This is a template. Replace all placeholders in [brackets] with actual content specific to your skill's workflow.

## Overview

[2-3 sentence description of what this workflow does and when to use it]

## Prerequisites

- [ ] [Prerequisite 1 - e.g., "Database schema initialized with required tables"]
- [ ] [Prerequisite 2 - e.g., "API authentication configured"]
- [ ] [Prerequisite 3 - e.g., "Required MCP tools available"]

## Input Requirements

- **[Input 1]**: [Description, data type, constraints - e.g., "resident_id: UUID, must exist in persons table"]
- **[Input 2]**: [Description, data type, constraints - e.g., "start_date: ISO 8601 date string, must be future date"]

## Workflow Steps

### Step 1: [Step Name]

[Detailed description of what to do in this step]

**Actions:**
```bash
# Example commands
[command 1]
[command 2]
```

**Expected Output:**
```
[What you should see]
```

**Validation:**
- Check that [condition 1] is true
- Verify [condition 2]

**If Error Occurs:**
→ See [Error Handling](#error-handling) section below

### Step 2: [Step Name]

[Description]

**Actions:**
```python
# Example Python code
[code]
```

**Expected Output:**
```json
{
  "status": "success",
  "data": {...}
}
```

**Validation:**
- [ ] [Validation check 1 - e.g., "Confirm API returned 200 status"]
- [ ] [Validation check 2 - e.g., "Verify database record was created"]

### Step 3: [Step Name]

[Description]

**Decision Point:**
```
IF [condition - e.g., "schedule conflicts detected"]:
    → Go to Step 4
ELSE IF [condition - e.g., "ACGME compliance violated"]:
    → Go to Step 5
ELSE:
    → ABORT with error
```

### Step 4: [Conditional Step]

[Description - only execute if certain condition met]

## Final Verification

After completing all steps:
- [ ] [Final check 1 - e.g., "All test cases pass"]
- [ ] [Final check 2 - e.g., "No compliance violations detected"]
- [ ] [Final check 3 - e.g., "Audit log entries created"]

## Error Handling

### Error: [Common Error 1]
**Symptoms:** [How to recognize this error]
**Cause:** [Root cause]
**Resolution:**
1. [Fix step 1]
2. [Fix step 2]
3. Resume from Step [N]

### Error: [Common Error 2]
**Symptoms:** [How to recognize]
**Cause:** [Root cause]
**Resolution:**
1. [Fix step 1]
2. [Fix step 2]

## Success Criteria

- ✅ [What indicates successful completion]
- ✅ [What artifacts are produced]
- ✅ [What state changes occurred]

## Next Steps

After completing this workflow:
1. [Recommended next action 1]
2. [Recommended next action 2]
3. Document findings in [location]

## Related Workflows

- **[Other Workflow]**: Use when [condition]
- **[Other Workflow]**: Complements this workflow by [purpose]

---

*This workflow is part of the [SKILL_NAME] skill.*
```

---

## Reference File Template

Use this template for files in the `Reference/` directory:

```markdown
# Reference: [Topic Name]

> **Purpose:** [What knowledge this document contains]
> **Audience:** [Who should read this]
> **Last Updated:** YYYY-MM-DD

---

## Overview

[2-3 sentence introduction to the topic]

## [Section 1: Definitions/Rules/Formulas]

### [Item 1]

**Definition:** [Clear definition]

**Formula (if applicable):**
```
[Mathematical formula or calculation]
```

**Example:**
```
[Concrete example with numbers]
```

**Interpretation:**
- When [value/condition]: [Meaning]
- When [value/condition]: [Meaning]

### [Item 2]

[Same structure as Item 1]

## [Section 2: Thresholds/Constants]

| Threshold | Value | Meaning | Action Required |
|-----------|-------|---------|-----------------|
| [Name] | [Value] | [What it represents] | [What to do when exceeded] |
| [Name] | [Value] | [What it represents] | [What to do when exceeded] |

## [Section 3: Historical Data/Benchmarks]

### [Time Period or Category]

**Observed Values:**
- [Metric 1]: [Value] (Date: YYYY-MM-DD)
- [Metric 2]: [Value] (Date: YYYY-MM-DD)

**Trend:**
[Description of trend over time]

**Seasonal Patterns:**
- [Month/Season]: [Typical behavior]
- [Month/Season]: [Typical behavior]

## [Section 4: Decision Matrix]

| Condition | Action | Rationale |
|-----------|--------|-----------|
| [If this is true] | [Do this] | [Because...] |
| [If this is true] | [Do this] | [Because...] |

## Citations and Sources

1. [Citation 1 - e.g., ACGME Common Program Requirements Section II.A.4]
2. [Citation 2 - e.g., Internal policy document]
3. [Citation 3 - e.g., Research paper]

## Updates Log

| Date | Change | Reason |
|------|--------|--------|
| YYYY-MM-DD | [What changed] | [Why] |

---

*This reference is maintained as part of the [SKILL_NAME] skill.*
```

---

## Registering in CORE/SKILL.md

After creating your skill, you MUST register it in `.claude/skills/CORE/SKILL.md`.

### Step 1: Add to Available Skills List

Find the appropriate category (Domain-Specific, Security, Development, Infrastructure, etc.) and add your skill:

```markdown
#### [Number]. [Skill Display Name] (`skill-directory-name`)

**Purpose:** [One-sentence description]

**Triggers:**
- [When to activate this skill - trigger 1]
- [Trigger 2]
- [Trigger 3]

**Key Capabilities:**
- [Capability 1]
- [Capability 2]
- [Capability 3]

**Dependencies:**
- `[other-skill]` ([why it depends on this])
- `[another-skill]` ([why])

**Example Invocation:**
```
Task: "[Example user request]"
→ Activate: [skill-directory-name]
Reason: [Why this skill is appropriate]
```
```

### Step 2: Update Routing Logic Keywords

In the **III. ROUTING LOGIC** section, add keywords to the table:

```markdown
| Keywords | Skill |
|----------|-------|
| [keyword1], [keyword2], [keyword3] | `your-skill-name` |
```

**Example:**
```markdown
| vacation, leave, time-off, blackout dates | `vacation-management` |
```

### Step 3: Update Quick Reference (if applicable)

If your skill fits common workflows, add to **X. QUICK REFERENCE**:

```markdown
| Task Type | Primary Skill | Common Secondary Skills |
|-----------|---------------|-------------------------|
| [Task] | `your-skill-name` | `dependency-skill-1`, `dependency-skill-2` |
```

---

## Testing Checklist

Before deploying a new skill, complete this checklist:

### Documentation Quality

- [ ] **SKILL.md is complete**
  - All sections filled out (no TODO placeholders)
  - Examples are concrete (not generic)
  - Error handling documented
  - Integration points listed

- [ ] **YAML frontmatter present** (if using frontmatter style)
  - Name matches directory name
  - Description is clear and actionable
  - Version is `1.0.0` for new skills
  - Dependencies listed (or `[]` for none)

- [ ] **Workflows are step-by-step** (if complex skill)
  - Each step has clear actions
  - Examples include actual commands/code
  - Success criteria defined
  - Error handling included

- [ ] **Reference docs are accurate** (if complex skill)
  - Formulas/thresholds verified
  - Citations included where applicable
  - Historical data is real (not placeholder)

### Integration Testing

- [ ] **Registered in CORE/SKILL.md**
  - Added to appropriate category
  - Keywords added to routing table
  - Example invocation provided

- [ ] **Dependencies verified**
  - All listed dependencies exist
  - Dependency versions compatible
  - No circular dependencies

- [ ] **MCP tools tested** (if skill uses MCP)
  - All referenced MCP tools exist and work
  - Tool parameters documented correctly
  - Error handling for tool failures

- [ ] **API endpoints tested** (if skill uses APIs)
  - All endpoints return expected data
  - Authentication works
  - Rate limiting handled

### Functional Testing

- [ ] **Happy path tested**
  - Skill successfully completes main workflow
  - Output matches documented format
  - Success criteria met

- [ ] **Error conditions tested**
  - Documented errors can be reproduced
  - Error messages are helpful
  - Recovery procedures work

- [ ] **Edge cases tested**
  - Empty inputs handled gracefully
  - Boundary values don't crash
  - Null/undefined cases covered

### Code Quality (if skill involves code generation)

- [ ] **Generated code compiles/runs**
  - Python code passes `ruff check`
  - TypeScript code passes `npm run type-check`
  - No syntax errors

- [ ] **Tests exist for skill logic**
  - Unit tests for core functions
  - Integration tests for workflows
  - Coverage ≥70%

### User Acceptance

- [ ] **Examples are realistic**
  - Use actual domain data (sanitized)
  - Examples reflect common use cases
  - Examples include expected output

- [ ] **Documentation is readable**
  - No jargon without definitions
  - Clear headings and structure
  - Examples before complex concepts

- [ ] **Skill is discoverable**
  - Clear naming convention
  - Listed in appropriate category
  - Keywords make sense

---

## Example: VACATION_MANAGEMENT Skill

### Complete Walkthrough

Let's create a new skill for managing resident vacation requests with blackout dates, ACGME compliance, and coverage impact analysis.

#### Step 1: Determine if Skill is Needed

**Questions:**
1. Does this require domain expertise? → YES (vacation policies, ACGME rules, coverage gaps)
2. Will this be used repeatedly? → YES (vacation requests occur monthly)
3. Does it integrate with specialized tools? → YES (MCP tools, vacation API endpoints)
4. Can existing skills handle this? → NO (no existing vacation-specific skill)

**Decision:** Create new skill ✅

#### Step 2: Choose Structure

**Considerations:**
- Multiple workflows (request submission, approval, rollback)
- Reference data (blackout dates, policy rules)
- Complex validation logic

**Decision:** Use complex structure (SKILL.md + Workflows/ + Reference/)

#### Step 3: Create Directory Structure

```bash
mkdir -p /home/user/Autonomous-Assignment-Program-Manager/.claude/skills/vacation-management/Workflows
mkdir -p /home/user/Autonomous-Assignment-Program-Manager/.claude/skills/vacation-management/Reference
```

#### Step 4: Create SKILL.md

```markdown
---
name: vacation-management
description: Manage resident vacation requests with blackout dates, ACGME compliance, and coverage impact analysis. Use when processing leave requests or analyzing vacation patterns.
version: 1.0.0
category: Schedule Analysis
dependencies: ["acgme-compliance", "schedule-optimization"]
---

# VACATION_MANAGEMENT Skill

## Metadata

- **Name**: vacation-management
- **Version**: 1.0.0
- **Category**: Schedule Analysis
- **Dependencies**: `acgme-compliance`, `schedule-optimization`

## Description

Systematic vacation request processing for medical residency programs, ensuring compliance with ACGME work hour rules, respecting blackout dates, and analyzing coverage impact before approval.

## Purpose

Managing vacation requests in medical residency programs is complex because:
- Vacations affect ACGME compliance (work hours, supervision ratios)
- Certain periods have blackout dates (high census, specialty coverage needs)
- Approval requires coverage gap analysis (can remaining residents handle workload?)
- Requests may cascade (one vacation approved → others become infeasible)

This skill provides systematic workflows to:
- Validate requests against policies and blackout dates
- Assess coverage impact using resilience metrics
- Generate approval recommendations with risk scoring
- Handle rollback if post-approval issues discovered

## When to Use This Skill

Invoke this skill when:
- ✅ Processing new vacation requests from residents
- ✅ Analyzing vacation patterns for equity (are requests distributed fairly?)
- ✅ Checking if proposed dates violate blackout periods
- ✅ Assessing coverage gaps after leave approval
- ✅ Reviewing historical vacation data for policy refinement

Do NOT use for:
- ❌ Emergency leave (use `production-incident-responder` for immediate absences)
- ❌ ACGME compliance validation alone (use `acgme-compliance` skill)
- ❌ Schedule generation (use `schedule-optimization` skill)

## Core Capabilities

### Capability 1: Request Validation
Validates vacation requests against:
- Blackout date policies (defined per rotation)
- Maximum consecutive days off (typically 14-21 days)
- Minimum notice period (typically 30-60 days)
- ACGME work hour compliance impact

**Input:** Vacation request (resident ID, start date, end date)
**Output:** Validation report (pass/fail + violation reasons)

**Example:**
```python
from app.services.vacation_service import validate_vacation_request

request = VacationRequest(
    resident_id="PGY2-03",
    start_date=date(2025, 7, 15),
    end_date=date(2025, 7, 28)
)

result = await validate_vacation_request(db, request)
# Result: {"valid": False, "violations": ["Overlaps blackout: Block 10 Peds clinic"]}
```

### Capability 2: Coverage Impact Analysis
Calculates resilience metrics if request approved:
- Health score change (before vs. after approval)
- N-1 vulnerability (does this create critical resident?)
- Rotation coverage margins (understaffing risk)

**Input:** Vacation request + current schedule
**Output:** Impact report (health score delta, affected rotations, risk level)

**Example:**
```bash
curl -X POST http://localhost:8000/api/vacations/impact-analysis \
  -d '{"resident_id": "PGY2-03", "start_date": "2025-07-15", "end_date": "2025-07-28"}'

# Output: {"health_score_change": -0.08, "risk_level": "MEDIUM", "affected_rotations": ["EM", "Peds Clinic"]}
```

### Capability 3: Approval Recommendation
Generates recommendation (Approve, Conditional Approve, Deny) with rationale:
- Approve: No policy violations, low coverage risk
- Conditional Approve: Requires mitigation (e.g., add supplemental staff)
- Deny: Policy violation or unacceptable risk

**Input:** Validation + impact analysis results
**Output:** Recommendation with supporting data

## Skill Phases

### Phase 1: Request Validation
**Input**: Raw vacation request
**Output**: Validation report (pass/fail + violations)
**Workflow**: `Workflows/validate-vacation-request.md`

Checks request against:
1. Blackout date calendar
2. Policy constraints (max days, notice period)
3. Resident eligibility (not on probation, etc.)

### Phase 2: Coverage Impact Analysis
**Input**: Valid request + current schedule
**Output**: Resilience impact report
**Workflow**: `Workflows/assess-coverage-impact.md`

Simulates approval and calculates:
1. Health score change (using `RESILIENCE_SCORING` skill)
2. N-1 vulnerability shift
3. Rotation-specific coverage margins

### Phase 3: Approval Workflow
**Input**: Validation + impact reports
**Output**: Approval decision with rationale
**Workflow**: `Workflows/approve-vacation.md`

Generates recommendation based on:
1. Policy compliance (must pass)
2. Coverage risk (low/medium = approve, high = conditional, critical = deny)
3. Fairness analysis (is resident using appropriate vacation budget?)

## Key Files and Integration Points

### Backend Services
```
backend/app/services/
├── vacation_service.py              # Request validation
├── vacation_coverage_analyzer.py    # Impact analysis
└── vacation_approval.py             # Approval workflow
```

### Database Tables
- `vacation_requests` - All vacation requests (pending, approved, denied)
- `vacation_blackout_dates` - Blackout periods per rotation
- `vacation_policies` - Max days, notice periods, eligibility rules

### MCP Tools
- `mcp__vacation_validate` - Validate request against policies
- `mcp__vacation_coverage_check` - Assess coverage impact
- `mcp__vacation_approve` - Execute approval workflow

### API Endpoints
- `POST /api/vacations/requests` - Submit new request
- `GET /api/vacations/impact/{request_id}` - Get impact analysis
- `POST /api/vacations/approve/{request_id}` - Approve request
- `GET /api/vacations/blackout-dates` - Retrieve blackout calendar

## Output Formats

### Validation Report
```json
{
  "request_id": "vac-req-123",
  "resident_id": "PGY2-03",
  "valid": false,
  "violations": [
    {
      "type": "blackout_date_conflict",
      "message": "Overlaps Block 10 Peds clinic blackout (2025-07-20 to 2025-07-25)",
      "severity": "HIGH"
    }
  ],
  "warnings": [
    {
      "type": "short_notice",
      "message": "Request submitted 25 days before start (policy: 30 days)",
      "severity": "LOW"
    }
  ]
}
```

### Coverage Impact Report
```json
{
  "request_id": "vac-req-123",
  "current_health_score": 0.78,
  "projected_health_score": 0.70,
  "health_score_delta": -0.08,
  "risk_level": "MEDIUM",
  "affected_rotations": [
    {
      "rotation": "EM Night Shift",
      "current_coverage": 3,
      "projected_coverage": 2,
      "margin_change": "1.5x minimum → 1.0x minimum"
    }
  ],
  "n1_vulnerability": {
    "current_critical_residents": 2,
    "projected_critical_residents": 3,
    "new_critical": ["PGY3-01"]
  },
  "recommendations": [
    "Add 1 supplemental EM resident for week of 2025-07-20",
    "Cross-train PGY3-04 for EM backup"
  ]
}
```

### Approval Decision
```json
{
  "request_id": "vac-req-123",
  "decision": "CONDITIONAL_APPROVE",
  "rationale": "Request passes policy checks but creates medium coverage risk. Approval contingent on adding supplemental EM coverage.",
  "conditions": [
    "Secure supplemental EM resident for 2025-07-20 to 2025-07-25",
    "Notify Chief Resident of reduced EM staffing"
  ],
  "auto_approve_eligible": false,
  "requires_pd_approval": true
}
```

## Error Handling

### Common Errors

**Error: Blackout date conflict**
```
Cause: Request overlaps restricted period
Fix: Suggest alternative dates outside blackout
Command: GET /api/vacations/available-dates?resident_id=PGY2-03&duration=14
```

**Error: Coverage impact unacceptable (health score < 0.5)**
```
Cause: Approval would create critical schedule fragility
Fix: Deny request or require mitigation (supplemental staff)
Action: Generate impact report, escalate to Program Director
```

**Error: Resident over vacation budget**
```
Cause: Resident has used allotted vacation days for year
Fix: Check policy for exceptions (e.g., unused prior year days)
SQL: SELECT SUM(DATEDIFF(end_date, start_date)) FROM vacation_requests WHERE resident_id = 'PGY2-03' AND status = 'approved' AND YEAR(start_date) = 2025;
```

### Recovery Procedures

**If vacation approved but post-approval issue discovered:**
1. Check rollback eligibility (< 48 hours since approval)
2. Run `Workflows/rollback-vacation.md`
3. Notify resident of rollback reason
4. Suggest alternative dates

**If coverage gap detected after approval:**
1. Trigger supplemental staff recruitment
2. Notify Chief Resident and Program Director
3. Monitor health score daily
4. Prepare contingency plan (N-1 coverage)

## Integration with Other Skills

### Workflow: Complete Vacation Approval
```
1. vacation-management: Validate request (this skill)
2. acgme-compliance: Check ACGME impact (dependency)
3. RESILIENCE_SCORING: Calculate coverage impact (dependency)
4. vacation-management: Generate approval decision (this skill)
5. schedule-optimization: Re-optimize schedule if approved (dependency)
```

### Workflow: Quarterly Vacation Audit
```
1. vacation-management: Retrieve all requests (Q1 2025)
2. vacation-management: Analyze fairness (equal distribution?)
3. vacation-management: Identify blackout violations
4. Document findings in Reference/historical-vacation-patterns.md
```

## Reference Documents

- **blackout-dates-policy.md**: Rotation-specific blackout periods and rationale
- **vacation-policies.md**: Max days, notice periods, eligibility rules
- **historical-vacation-patterns.md**: Past trends, seasonal patterns

## Quick Start Examples

### Example 1: Validate Vacation Request
```bash
# Via API
curl -X POST http://localhost:8000/api/vacations/validate \
  -H "Content-Type: application/json" \
  -d '{
    "resident_id": "PGY2-03",
    "start_date": "2025-07-15",
    "end_date": "2025-07-28"
  }'

# Expected output: Validation report (pass/fail + violations)
```

### Example 2: Assess Coverage Impact
```bash
# Via MCP tool
mcp__vacation_coverage_check --resident PGY2-03 --start 2025-07-15 --end 2025-07-28

# Expected output: Health score delta, affected rotations, risk level
```

### Example 3: Approve Request (Programmatic)
```python
from app.services.vacation_approval import VacationApprovalService

service = VacationApprovalService()
decision = await service.process_request(db, request_id="vac-req-123")

if decision.decision == "APPROVE":
    await service.execute_approval(db, request_id)
    print(f"Approved: {decision.rationale}")
else:
    print(f"Denied: {decision.rationale}")
```

## Success Criteria

This skill is successfully applied when:
- ✅ Request validated against all policies (blackout, max days, notice)
- ✅ Coverage impact quantified (health score delta, N-1 vulnerability)
- ✅ Approval decision generated with clear rationale
- ✅ Affected rotations identified with coverage margins
- ✅ Findings documented in historical patterns
- ✅ Rollback capability maintained (< 48 hours post-approval)

## Notes

- **Blackout dates vary by rotation**: Peds clinic weeks differ from EM call weeks
- **ACGME compliance is critical**: Approvals must not violate work hour rules
- **Fairness matters**: Track vacation distribution to prevent inequity
- **Cascade effects**: One approval may invalidate other pending requests
- **Seasonal patterns**: Summer vacation requests spike (plan accordingly)

---

*This skill complements the `schedule-optimization` skill by handling dynamic leave requests and ensuring ongoing schedule resilience.*
```

#### Step 5: Create Workflow Files

**Workflows/validate-vacation-request.md:**

```markdown
# Workflow: Validate Vacation Request

## Overview

Validates a resident vacation request against institutional policies, blackout dates, and basic feasibility constraints. This is the first gate before coverage impact analysis.

## Prerequisites

- [ ] Vacation request submitted with resident ID, start date, end date
- [ ] Blackout date calendar populated in database
- [ ] Vacation policies configured (max days, notice period)

## Input Requirements

- **Resident ID**: Valid resident in system (e.g., "PGY2-03")
- **Start Date**: ISO 8601 format (YYYY-MM-DD), must be future date
- **End Date**: ISO 8601 format, must be after start date
- **Request Type**: "vacation" | "conference" | "personal" (different policies)

## Workflow Steps

### Step 1: Validate Input Data

**Actions:**
```python
from datetime import date

# Check dates are valid
if start_date < date.today():
    raise ValueError("Cannot request vacation for past dates")

if end_date <= start_date:
    raise ValueError("End date must be after start date")

duration_days = (end_date - start_date).days

if duration_days > 21:
    raise ValueError("Vacation exceeds maximum 21 consecutive days")
```

**Validation:**
- Start date is in future
- End date > start date
- Duration ≤ 21 days

### Step 2: Check Blackout Dates

**Actions:**
```sql
-- Query blackout dates that overlap request
SELECT bd.rotation, bd.start_date, bd.end_date, bd.reason
FROM vacation_blackout_dates bd
JOIN assignments a ON a.rotation_id = bd.rotation_id
WHERE a.person_id = :resident_id
  AND bd.start_date <= :end_date
  AND bd.end_date >= :start_date;
```

**Expected Output:**
```
rotation       | start_date | end_date   | reason
Peds Clinic    | 2025-07-20 | 2025-07-25 | High census - fellowship exams
```

**Validation:**
- If any blackout dates returned → VIOLATION

### Step 3: Check Notice Period

**Actions:**
```python
notice_days = (start_date - date.today()).days
policy_min_notice = 30  # days

if notice_days < policy_min_notice:
    warnings.append({
        "type": "short_notice",
        "message": f"Request submitted {notice_days} days before start (policy: {policy_min_notice} days)",
        "severity": "LOW"
    })
```

**Validation:**
- If notice < 30 days → WARNING (not blocking, but flagged)

### Step 4: Check Vacation Budget

**Actions:**
```sql
-- Check total vacation days used this year
SELECT SUM(DATEDIFF(end_date, start_date)) AS days_used
FROM vacation_requests
WHERE resident_id = :resident_id
  AND status = 'approved'
  AND YEAR(start_date) = :current_year;
```

**Expected Output:**
```
days_used
10
```

**Validation:**
```python
max_vacation_days = 21  # Annual limit
requested_days = (end_date - start_date).days

if days_used + requested_days > max_vacation_days:
    raise ValueError(f"Exceeds annual vacation budget: {days_used + requested_days} > {max_vacation_days}")
```

### Step 5: Generate Validation Report

**Actions:**
```python
validation_report = {
    "request_id": request.id,
    "resident_id": request.resident_id,
    "valid": len(violations) == 0,
    "violations": violations,
    "warnings": warnings,
    "checked_at": datetime.utcnow()
}

return validation_report
```

## Final Verification

- [ ] Validation report generated
- [ ] All policy checks executed
- [ ] Violations clearly documented
- [ ] Warnings flagged (non-blocking issues)

## Error Handling

### Error: Resident not found
**Symptoms:** Database query returns no results for resident_id
**Cause:** Invalid resident ID
**Resolution:**
1. Check resident ID format (should be PGY[1-3]-[01-12])
2. Query residents table to verify ID exists
3. If typo, correct and retry

### Error: Blackout date calendar empty
**Symptoms:** No blackout dates returned, but rotations have known blackout periods
**Cause:** vacation_blackout_dates table not populated
**Resolution:**
1. Run `scripts/populate_blackout_dates.py`
2. Verify data with: `SELECT COUNT(*) FROM vacation_blackout_dates;`
3. Retry validation

## Success Criteria

- ✅ All policy checks completed (blackout, budget, notice, duration)
- ✅ Violations clearly identified with severity
- ✅ Warnings flagged for non-blocking issues
- ✅ Report formatted consistently

## Next Steps

After validation:
1. If `valid == true`: Proceed to `Workflows/assess-coverage-impact.md`
2. If `valid == false`: Return violations to resident, suggest alternatives
3. Document request in vacation_requests table with status = 'validated' or 'rejected'

---

*This workflow is part of the vacation-management skill.*
```

**Workflows/assess-coverage-impact.md:**

```markdown
# Workflow: Assess Coverage Impact

## Overview

Analyzes the coverage impact of approving a vacation request. Calculates resilience metrics (health score, N-1 vulnerability) and identifies affected rotations.

## Prerequisites

- [ ] Vacation request passed validation (see `validate-vacation-request.md`)
- [ ] Current schedule exists in database (assignments table populated)
- [ ] Resilience metrics baseline computed (current health score known)

## Input Requirements

- **Validated Request**: Vacation request that passed policy checks
- **Current Schedule**: Active assignments for evaluation period
- **Baseline Metrics**: Current health score, N-1 vulnerability list

## Workflow Steps

### Step 1: Simulate Absence

Create temporary schedule with resident absent for requested dates.

**Actions:**
```python
from app.resilience.health_metrics import HealthScoreCalculator

# Mark resident as absent for requested period
simulated_schedule = current_schedule.copy()
simulated_schedule.mark_absent(
    resident_id=request.resident_id,
    start_date=request.start_date,
    end_date=request.end_date
)
```

### Step 2: Calculate Health Score Delta

**Actions:**
```python
calculator = HealthScoreCalculator(db)

# Baseline health score (current state)
baseline_report = await calculator.compute_health_score(
    start_date=request.start_date,
    end_date=request.end_date
)

# Projected health score (with absence)
projected_report = await calculator.compute_health_score_with_absence(
    start_date=request.start_date,
    end_date=request.end_date,
    absent_resident_id=request.resident_id
)

health_score_delta = projected_report.overall_health - baseline_report.overall_health
```

**Expected Output:**
```json
{
  "baseline_health": 0.78,
  "projected_health": 0.70,
  "delta": -0.08
}
```

### Step 3: Identify Affected Rotations

**Actions:**
```sql
-- Find rotations where resident is scheduled during vacation period
SELECT DISTINCT r.name, r.min_residents,
       COUNT(*) AS current_coverage,
       COUNT(*) - 1 AS projected_coverage
FROM assignments a
JOIN rotations r ON a.rotation_id = r.id
WHERE a.start_date <= :end_date
  AND a.end_date >= :start_date
  AND a.rotation_id IN (
      SELECT rotation_id FROM assignments WHERE person_id = :resident_id
  )
GROUP BY r.id;
```

**Expected Output:**
```
name         | min_residents | current_coverage | projected_coverage
EM Night     | 2             | 3                | 2
Peds Clinic  | 2             | 2                | 1
```

### Step 4: Run N-1 Vulnerability Analysis

**Actions:**
```python
from app.resilience.n_minus_analysis import N1Analyzer

analyzer = N1Analyzer(db)

# Baseline: critical residents under current schedule
baseline_critical = await analyzer.identify_critical_residents(
    start_date=request.start_date,
    end_date=request.end_date
)

# Projected: critical residents after vacation approval
projected_critical = await analyzer.identify_critical_residents_with_absence(
    start_date=request.start_date,
    end_date=request.end_date,
    absent_resident_id=request.resident_id
)

new_critical = set(projected_critical) - set(baseline_critical)
```

**Expected Output:**
```json
{
  "current_critical_residents": ["PGY3-02", "PGY2-05"],
  "projected_critical_residents": ["PGY3-02", "PGY2-05", "PGY3-01"],
  "new_critical": ["PGY3-01"]
}
```

### Step 5: Classify Risk Level

**Decision Point:**
```python
if health_score_delta > -0.05:
    risk_level = "LOW"
elif -0.10 < health_score_delta <= -0.05:
    risk_level = "MEDIUM"
elif -0.15 < health_score_delta <= -0.10:
    risk_level = "HIGH"
else:
    risk_level = "CRITICAL"
```

### Step 6: Generate Recommendations

**Actions:**
```python
recommendations = []

# Understaffed rotations
for rotation in affected_rotations:
    if rotation.projected_coverage < rotation.min_residents:
        recommendations.append(
            f"Add supplemental staff to {rotation.name} for {request.duration_days} days"
        )

# New critical residents
if len(new_critical) > 0:
    recommendations.append(
        f"Cross-train backup for: {', '.join(new_critical)}"
    )

# Health score mitigation
if risk_level in ["HIGH", "CRITICAL"]:
    recommendations.append(
        "Defer non-urgent rotations or reduce call frequency during absence"
    )
```

## Final Verification

- [ ] Health score delta calculated
- [ ] Affected rotations identified
- [ ] N-1 vulnerability assessed
- [ ] Risk level classified
- [ ] Mitigation recommendations generated

## Success Criteria

- ✅ Impact report generated with health score delta
- ✅ All affected rotations listed with coverage margins
- ✅ N-1 vulnerability change quantified
- ✅ Risk level assigned (LOW/MEDIUM/HIGH/CRITICAL)
- ✅ Actionable recommendations provided

## Next Steps

After impact analysis:
1. If risk = LOW: Auto-approve eligible (proceed to `approve-vacation.md`)
2. If risk = MEDIUM: Require Program Director review
3. If risk = HIGH/CRITICAL: Generate mitigation plan before approval
4. Document findings in `vacation_requests.impact_analysis` column

---

*This workflow is part of the vacation-management skill and depends on the RESILIENCE_SCORING skill.*
```

#### Step 6: Create Reference Files

**Reference/blackout-dates-policy.md:**

```markdown
# Reference: Blackout Dates Policy

> **Purpose:** Documents rotation-specific blackout periods and rationale
> **Audience:** Program leadership, vacation management system
> **Last Updated:** 2025-12-26

---

## Overview

Blackout dates are periods when resident vacation requests cannot be approved due to operational requirements. These dates vary by rotation and are reviewed annually.

## Rotation-Specific Blackout Periods

### Pediatrics Clinic

**Blackout Windows:**
- **Block 10 (July 15-28)**: Fellow board exam proctoring
- **Block 24 (November 1-14)**: Flu vaccine clinic (all hands required)
- **Block 36 (February 10-21)**: Residency Match Week (continuity critical)

**Rationale:**
- Peds clinic volume increases 30% during fellow exam period
- Flu vaccine clinic requires 100% resident staffing per public health mandate
- Match Week disruptions affect patient continuity scores

### Emergency Medicine

**Blackout Windows:**
- **Block 12 (August 1-14)**: New resident orientation (senior coverage essential)
- **Block 18 (October 1-14)**: Disaster preparedness drill
- **Holidays (Dec 24-Jan 2)**: High census, trauma spike

**Rationale:**
- New PGY-1 residents require 2:1 supervision during orientation
- Disaster drill requires all senior residents present
- Holiday period sees 40% ED volume increase

### Obstetrics & Gynecology

**Blackout Windows:**
- **Block 8 (June 15-30)**: End-of-year case log verification
- **Block 40 (March 1-14)**: Residency application season

**Rationale:**
- Case log finalization requires all residents available for review
- Residency applicants interview during this period (clinic coverage thin)

## Policy Enforcement

### Hard Blackouts (No Exceptions)
- Fellow board exam periods
- New resident orientation
- Public health mandates (e.g., flu clinic)

### Soft Blackouts (Exception with PD Approval)
- Holiday periods (exception for family emergencies)
- Residency Match Week (exception if substitute coverage secured)

## Exception Process

1. Resident submits request with exception justification
2. Chief Resident reviews coverage feasibility
3. Program Director makes final decision
4. If approved, supplemental staff must be secured before approval confirmed

## Annual Review

Blackout dates reviewed every July by:
- Program Director
- Chief Resident
- Rotation directors

Changes require 60-day notice to residents.

## Historical Data

### 2024 Blackout Violations (Approved Despite Blackout)

| Date | Rotation | Reason | Outcome |
|------|----------|--------|---------|
| 2024-07-20 | Peds Clinic | Family emergency | Supplemental faculty covered, no impact |
| 2024-12-28 | EM | Parental leave | Locum tenens secured, minimal impact |

**Lessons Learned:**
- Exceptions workable if planned >30 days ahead
- Locum tenens availability key for holiday exceptions

---

*This reference is maintained by the Program Director and reviewed annually.*
```

**Reference/vacation-policies.md:**

```markdown
# Reference: Vacation Policies

> **Purpose:** Defines vacation request policies and constraints
> **Audience:** Residents, Program leadership, vacation management system
> **Last Updated:** 2025-12-26

---

## Annual Vacation Allotment

| PGY Level | Vacation Days | CME Days | Total Days Off |
|-----------|---------------|----------|----------------|
| PGY-1     | 15 days       | 5 days   | 20 days        |
| PGY-2     | 18 days       | 5 days   | 23 days        |
| PGY-3     | 21 days       | 5 days   | 26 days        |

**Notes:**
- Vacation days = personal time off
- CME days = conference/educational leave
- Total includes vacation + CME (cannot exceed total)

## Request Constraints

### Minimum Notice Period

| Request Duration | Notice Required |
|------------------|-----------------|
| 1-3 days         | 14 days         |
| 4-7 days         | 21 days         |
| 8-14 days        | 30 days         |
| 15-21 days       | 45 days         |

**Exceptions:** Emergency leave (family emergency, medical) requires Chief Resident approval within 24 hours.

### Maximum Consecutive Days

| PGY Level | Max Consecutive Days |
|-----------|----------------------|
| PGY-1     | 14 days              |
| PGY-2     | 18 days              |
| PGY-3     | 21 days              |

**Rationale:** Prevents skill decay and ensures continuity of care.

### Blackout Periods

See `blackout-dates-policy.md` for rotation-specific blackout windows.

## Approval Workflow

### Auto-Approval Eligible

Requests are auto-approved if ALL conditions met:
- [ ] No blackout date conflicts
- [ ] Adequate notice period
- [ ] Within annual vacation budget
- [ ] Coverage impact risk = LOW (health score delta < -0.05)
- [ ] No pending requests for same period

### Program Director Approval Required

- Coverage impact risk = MEDIUM or HIGH
- Request during soft blackout period
- Exception to policy requested
- Second request within 30 days

### Denial Reasons

- Blackout date violation (hard blackout)
- Coverage impact risk = CRITICAL
- Exceeds annual vacation budget
- Inadequate notice (non-emergency)

## Rollback Policy

**Timeframe:** Vacation approvals can be rolled back within 48 hours if:
- Coverage gap discovered post-approval
- Schedule change invalidates initial approval
- Cascade effect creates critical vulnerability

**Notification:** Resident notified immediately with alternative dates suggested.

## Fairness Tracking

Program tracks vacation distribution quarterly to ensure equity:
- Days off per resident (within 10% variance target)
- Holiday period distribution (fair rotation)
- Blackout enforcement (consistent application)

**Audit:** Chief Resident reviews fairness report quarterly, escalates concerns to PD.

---

*Policy maintained by Program Director, updated annually or as needed.*
```

#### Step 7: Register in CORE/SKILL.md

Add to `.claude/skills/CORE/SKILL.md` under **Domain-Specific Skills**:

```markdown
#### 26. Vacation Management (`vacation-management`)

**Purpose:** Manage resident vacation requests with blackout dates, ACGME compliance, and coverage impact analysis

**Triggers:**
- Processing new vacation requests from residents
- Analyzing vacation patterns for equity
- Checking if proposed dates violate blackout periods
- Assessing coverage gaps after leave approval

**Key Capabilities:**
- Request validation against policies and blackout dates
- Coverage impact analysis using resilience metrics
- Approval recommendation with risk scoring
- Rollback handling for post-approval issues

**Dependencies:**
- `acgme-compliance` (ensure vacation doesn't violate work hours)
- `schedule-optimization` (re-optimize schedule if needed)
- `RESILIENCE_SCORING` (calculate health score impact)

**Example Invocation:**
```
Task: "Validate vacation request for PGY2-03 from July 15-28"
→ Activate: vacation-management
Reason: Vacation request processing is core purpose
```
```

Add routing keywords:

```markdown
| Keywords | Skill |
|----------|-------|
| vacation, leave, time-off, blackout dates, vacation request | `vacation-management` |
```

#### Step 8: Test the Skill

**Test Checklist:**

- [x] SKILL.md complete with all sections
- [x] Workflows created (validate, assess, approve)
- [x] Reference docs created (blackout dates, policies)
- [x] Registered in CORE/SKILL.md
- [x] Keywords added to routing
- [ ] Integration test with backend API (pending backend implementation)
- [ ] MCP tools tested (pending tool creation)
- [ ] Example requests validated (pending database setup)

**Next Steps:**
1. Implement backend services (`vacation_service.py`, etc.)
2. Create MCP tools (`mcp__vacation_validate`, etc.)
3. Populate database with test data
4. Run end-to-end test of validation → impact → approval workflow
5. Document findings in `Reference/historical-vacation-patterns.md`

---

## Common Pitfalls

### Pitfall 1: Skill Too Broad

**Problem:** Skill tries to do too much, becomes hard to maintain

**Example:**
```
❌ "schedule-management" skill that handles:
   - Schedule generation
   - Vacation requests
   - Swap processing
   - ACGME validation
   - Resilience scoring
```

**Solution:** Break into focused skills
```
✅ schedule-optimization (generation)
✅ vacation-management (vacation requests)
✅ swap-management (swaps)
✅ acgme-compliance (validation)
✅ RESILIENCE_SCORING (resilience)
```

### Pitfall 2: Skill Too Narrow

**Problem:** Skill does one trivial thing, better handled by general capabilities

**Example:**
```
❌ "email-validator" skill that just checks email format
```

**Solution:** Use general capabilities or extend existing skill
```
✅ Use built-in validation in API layer
OR
✅ Add to existing "data-validation" skill if one exists
```

### Pitfall 3: Missing Integration Points

**Problem:** Skill defined but doesn't connect to backend/APIs

**Example:**
```
SKILL.md says "Use MCP tool mcp__vacation_validate"
→ But tool doesn't exist
→ Skill fails when invoked
```

**Solution:** Verify integration points before deploying
- Check MCP tools exist: `docker-compose exec mcp-server python -c "from scheduler_mcp.server import mcp; print(mcp.tools)"`
- Check API endpoints exist: `curl http://localhost:8000/api/vacations/validate`
- Document missing integrations as prerequisites

### Pitfall 4: No Examples or Examples Too Generic

**Problem:** Documentation has examples like "Do X with Y"

**Example:**
```
❌ "Calculate health score"
```

**Solution:** Use concrete, domain-specific examples
```
✅ "Calculate health score for Block 10 (2026-03-12 to 2026-04-08) after approving PGY2-03 vacation"
```

### Pitfall 5: Undocumented Dependencies

**Problem:** Skill depends on other skills but doesn't list them

**Example:**
```
Skill uses RESILIENCE_SCORING to calculate coverage impact
→ But dependencies list is empty []
→ Users don't know they need to set up resilience framework
```

**Solution:** Explicitly list all dependencies with rationale
```yaml
dependencies: ["acgme-compliance", "RESILIENCE_SCORING"]
```

Then explain in SKILL.md:
```
**Dependencies:**
- `acgme-compliance` - Validates vacation doesn't violate work hour rules
- `RESILIENCE_SCORING` - Calculates health score impact of absence
```

### Pitfall 6: Stale Documentation

**Problem:** Skill works initially, but becomes outdated as codebase evolves

**Example:**
```
Skill documents API endpoint:
GET /api/resilience/health

→ But endpoint changed to:
GET /api/v2/resilience/health-score

→ Skill examples fail
```

**Solution:**
- Include "Last Updated" date in YAML frontmatter
- Review skills quarterly (META_UPDATER agent responsibility)
- Link to codebase files so discrepancies are obvious

### Pitfall 7: No Error Handling Documentation

**Problem:** Skill shows happy path only, no failure scenarios

**Example:**
```
✅ "Validate vacation request"
❌ No mention of what happens if:
   - Database is down
   - Blackout dates table is empty
   - Resident ID invalid
```

**Solution:** Always include "Error Handling" section with:
- Common errors (what can go wrong)
- Symptoms (how to recognize each error)
- Recovery procedures (how to fix)

### Pitfall 8: Circular Dependencies

**Problem:** Skill A depends on Skill B, which depends on Skill A

**Example:**
```
vacation-management depends on schedule-optimization
schedule-optimization depends on vacation-management
→ Infinite loop
```

**Solution:** Refactor to remove circular dependency
```
vacation-management depends on schedule-optimization
schedule-optimization depends on acgme-compliance (not vacation-management)
```

---

## Summary: Skill Creation Workflow

```
1. Identify Need
   ├─ Domain expertise required?
   ├─ Recurring pattern (≥3x/month)?
   └─ Integration with specialized tools?

2. Choose Structure
   ├─ Simple (SKILL.md only)
   └─ Complex (SKILL.md + Workflows/ + Reference/)

3. Create Directory
   └─ .claude/skills/SKILL_NAME/

4. Write SKILL.md
   ├─ Use template
   ├─ Include concrete examples
   └─ Document error handling

5. Create Supporting Files
   ├─ Workflows/ (step-by-step procedures)
   └─ Reference/ (knowledge base)

6. Register in CORE/SKILL.md
   ├─ Add to Available Skills list
   ├─ Add routing keywords
   └─ Update Quick Reference

7. Test Skill
   ├─ Validate documentation complete
   ├─ Test integration points
   └─ Run end-to-end workflow

8. Deploy & Monitor
   ├─ Track skill usage
   ├─ Collect feedback
   └─ Iterate based on lessons learned
```

---

**Questions? Issues?**
- Consult `.claude/Agents/META_UPDATER.md` for skill enhancement proposals
- Escalate to ARCHITECT for architectural questions
- Review existing skills for patterns and best practices

---

*This guide is maintained by META_UPDATER and updated as skill creation patterns evolve.*
