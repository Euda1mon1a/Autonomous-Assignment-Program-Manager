---
name: acgme-compliance
description: ACGME regulatory compliance expertise for medical residency scheduling. Use when validating schedules, checking work hour limits, supervision ratios, or answering compliance questions. Integrates with MCP validation tools.
---

# ACGME Compliance Skill

Expert knowledge of ACGME (Accreditation Council for Graduate Medical Education) requirements for residency program scheduling.

## When This Skill Activates

- Validating schedule compliance
- Checking resident work hours
- Verifying supervision ratios
- Answering ACGME-related questions
- Before finalizing any schedule changes
- When coverage gaps are detected

## Core ACGME Rules

### 1. 80-Hour Rule (Duty Hours)
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

### 2. 1-in-7 Rule (Days Off)
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

### 3. Supervision Ratios
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

### 4. Duty Period Limits
| Scenario | Maximum Duration |
|----------|------------------|
| Standard shift | 24 hours |
| With strategic napping | 28 hours (rare exception) |
| Minimum time off between shifts | 8 hours |
| Extended (in-house call) | 24 + 4 hours transition |

### 5. Night Float Requirements
- Maximum 6 consecutive nights
- Adequate handoff time
- No other clinical duties during night float block

## MCP Tool Integration

### Primary Validation Tool
```
Tool: validate_acgme_compliance
Purpose: Full compliance check against all rules
Returns: violations[], warnings[], compliant_areas[]
```

### Supporting Tools
| Tool | Use Case |
|------|----------|
| `get_schedule` | Retrieve schedule data for analysis |
| `check_utilization_threshold_tool` | Verify 80% utilization limit |
| `run_contingency_analysis_resilience_tool` | Check N-1 coverage |

## Validation Workflow

### Step 1: Gather Data
```bash
# Use MCP tool to get current schedule
mcp call validate_acgme_compliance --schedule_id=current
```

### Step 2: Analyze Results
Check each rule category:
- [ ] 80-hour weekly average
- [ ] 1-in-7 days off
- [ ] Supervision ratios by rotation
- [ ] Duty period lengths
- [ ] Night float compliance

### Step 3: Prioritize Issues
| Severity | Response |
|----------|----------|
| **Violation** | Immediate correction required |
| **Warning** | Schedule adjustment within 48 hours |
| **At Risk** | Monitor closely, plan mitigation |

### Step 4: Recommend Fixes
Always suggest specific, actionable corrections:
- Who needs relief
- Which dates are affected
- Available swap candidates
- Impact on other metrics

## Escalation Triggers

**Escalate to Program Director when:**
1. Multiple simultaneous violations
2. Systemic pattern (same issue recurring)
3. Fix requires policy exception
4. Involves moonlighting hours
5. Resident health/safety concern

## Common Scenarios

### Scenario: Post-Call Scheduling
**Problem:** Resident scheduled for clinic after 24-hour call
**Rule:** Must have 8+ hours off after extended duty
**Fix:** Remove clinic assignment, ensure coverage

### Scenario: Holiday Coverage
**Problem:** Same residents covering multiple holidays
**Rule:** Fair distribution, 80-hour limit still applies
**Fix:** Rotate holiday assignments, check cumulative hours

### Scenario: Supervision Gap
**Problem:** Night shift with insufficient faculty
**Rule:** PGY-1s need 2:1 supervision
**Fix:** Add faculty coverage or redistribute residents

## Reporting Format

When reporting compliance status:

```
## ACGME Compliance Summary

**Overall Status:** [COMPLIANT / WARNING / VIOLATION]

### Violations (Immediate Action Required)
- [List specific violations with affected people/dates]

### Warnings (Action Within 48h)
- [List warnings approaching thresholds]

### Recommendations
1. [Specific actionable fix]
2. [Specific actionable fix]

### Affected Personnel
- [List names and specific issues]
```

## References

- See `thresholds.md` for configurable warning levels
- See `exceptions.md` for documented exception procedures
- ACGME Common Program Requirements: https://www.acgme.org/
