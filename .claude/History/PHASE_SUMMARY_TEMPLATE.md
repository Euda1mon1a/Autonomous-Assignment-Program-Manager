# Phase Summary: [Phase Name]

---
**Metadata:**
```yaml
phase_name: "[Descriptive name of this work phase]"
started_at: "YYYY-MM-DD HH:MM"
completed_at: "YYYY-MM-DD HH:MM"
agents_involved:
  - "Agent Name/ID 1"
  - "Agent Name/ID 2"
outcome: "[SUCCESS | PARTIAL | BLOCKED | FAILED]"
related_phases:
  - "[Previous phase name]"
  - "[Next phase name]"
tags:
  - "[tag1]"
  - "[tag2]"
```
---

## Executive Summary

[2-3 sentences capturing the essence of this phase]

**What:** [What was accomplished]
**Why:** [Why this work was necessary]
**Impact:** [What changed as a result]

---

## Objectives

### Primary Goals

1. [Primary objective 1]
2. [Primary objective 2]
3. [Primary objective 3]

### Secondary Goals

- [Secondary objective 1]
- [Secondary objective 2]

### Success Criteria

- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

---

## Approach

### Methodology

[Describe the high-level approach taken to accomplish objectives]

### Phases/Steps

1. **[Step 1 Name]**
   - Description: [Brief description]
   - Duration: [Time spent]
   - Outcome: [Result]

2. **[Step 2 Name]**
   - Description: [Brief description]
   - Duration: [Time spent]
   - Outcome: [Result]

3. **[Step 3 Name]**
   - Description: [Brief description]
   - Duration: [Time spent]
   - Outcome: [Result]

### Tools & Technologies Used

| Tool/Technology | Purpose | Notes |
|----------------|---------|-------|
| [Tool 1] | [Purpose] | [Key learnings] |
| [Tool 2] | [Purpose] | [Key learnings] |

---

## Key Decisions

### Decision 1: [Decision Name]

**Context:** [What situation required a decision]

**Options Considered:**
- **Option A:** [Description]
  - Pros: [List advantages]
  - Cons: [List disadvantages]
- **Option B:** [Description]
  - Pros: [List advantages]
  - Cons: [List disadvantages]
- **Option C:** [Description]
  - Pros: [List advantages]
  - Cons: [List disadvantages]

**Decision:** [Which option was chosen]

**Rationale:** [Why this option was selected]

**Alternatives Rejected:** [Why other options were not chosen]

**Reversibility:** [Can this decision be changed? At what cost?]

---

### Decision 2: [Decision Name]

[Same structure as Decision 1]

---

## Outcomes

### Deliverables

- [x] [Deliverable 1] - [Status/Location]
- [x] [Deliverable 2] - [Status/Location]
- [ ] [Deliverable 3] - [Status/Notes on why not completed]

### Metrics & Results

| Metric | Target | Actual | Notes |
|--------|--------|--------|-------|
| [Metric 1] | [Target value] | [Actual value] | [Analysis] |
| [Metric 2] | [Target value] | [Actual value] | [Analysis] |
| [Metric 3] | [Target value] | [Actual value] | [Analysis] |

### Quality Assessment

**Code Quality:**
- Test Coverage: [X%]
- Linting: [Pass/Fail with notes]
- Type Safety: [Pass/Fail with notes]

**Documentation Quality:**
- API Documentation: [Complete/Partial/Missing]
- User Guide Updates: [Complete/Partial/Missing]
- Code Comments: [Adequate/Needs Improvement]

**Security & Compliance:**
- Security Review: [Pass/Fail/N/A]
- ACGME Compliance: [Pass/Fail/N/A]
- HIPAA Compliance: [Pass/Fail/N/A]

---

## Artifacts

### Files Created

```
path/to/new/file1.py
path/to/new/file2.tsx
path/to/new/file3.md
```

**Purpose:** [Brief description of what these files do]

---

### Files Modified

```
path/to/modified/file1.py
  - Added: [What was added]
  - Changed: [What was changed]
  - Removed: [What was removed]

path/to/modified/file2.tsx
  - Added: [What was added]
  - Changed: [What was changed]
```

---

### Database Changes

**Migrations:**
- `YYYY-MM-DD_migration_name.py` - [Description]

**Schema Changes:**
- Table `[table_name]`: [Description of changes]
- Added columns: `[column_list]`
- Modified columns: `[column_list]`
- Added indexes: `[index_list]`

---

### Configuration Changes

**Environment Variables:**
- Added: `NEW_VAR` - [Purpose]
- Modified: `EXISTING_VAR` - [What changed and why]

**Docker/Infrastructure:**
- [List any infrastructure changes]

---

## Lessons Learned

### What Went Well

1. **[Success 1]**
   - [Description of what worked well]
   - [Why it worked]
   - [How to replicate in future phases]

2. **[Success 2]**
   - [Description]

### What Could Be Improved

1. **[Challenge 1]**
   - [Description of what didn't go smoothly]
   - [Root cause]
   - [How to prevent/improve next time]

2. **[Challenge 2]**
   - [Description]

### Unexpected Discoveries

- **[Discovery 1]:** [What was learned that wasn't expected]
- **[Discovery 2]:** [What was learned that wasn't expected]

### Technical Debt Incurred

- **[Debt Item 1]:** [Description and reason for accepting the debt]
  - Priority: [High/Medium/Low]
  - Estimated Effort to Resolve: [Time estimate]
  - Tracking: [Link to issue/ticket]

- **[Debt Item 2]:** [Description]

---

## Open Questions

### Unresolved Issues

1. **[Question 1]**
   - **Context:** [Why this matters]
   - **Blocking:** [What this blocks, if anything]
   - **Owner:** [Who should resolve this]
   - **Timeline:** [When this needs resolution]

2. **[Question 2]**
   - [Same structure]

### Future Considerations

- [Question or consideration for future phases]
- [Question or consideration for future phases]

### Dependencies on External Factors

- **[Dependency 1]:** [What we're waiting for]
  - Owner: [Who owns this]
  - ETA: [When expected]
  - Impact if delayed: [What happens]

---

## Next Phase Prerequisites

### Required Before Next Phase

- [ ] [Prerequisite 1] - [Why needed]
- [ ] [Prerequisite 2] - [Why needed]
- [ ] [Prerequisite 3] - [Why needed]

### Recommended Before Next Phase

- [ ] [Nice-to-have 1] - [Why recommended]
- [ ] [Nice-to-have 2] - [Why recommended]

### Handoff Information

**For Next Agent/Phase:**

[Critical information the next agent needs to know. Include:]
- Current system state
- Known issues or workarounds
- Relevant context from this phase
- Key files to review
- Testing notes

**Entry Points:**
- Code: `[File path to start reading]`
- Documentation: `[Doc to read first]`
- Tests: `[Test file to run]`

---

## References

### Related Documentation

- [Link to design doc]
- [Link to API spec]
- [Link to user guide]

### Related Issues/Tickets

- [Issue #123: Description]
- [Issue #456: Description]

### External Resources

- [Link to external reference 1]
- [Link to external reference 2]

---

## Example Usage (for this template)

Below is a minimal example showing how to fill out this template for a real phase:

---

# Phase Summary: Block 10 Schedule Generation

---
**Metadata:**
```yaml
phase_name: "Block 10 Schedule Generation - Initial Implementation"
started_at: "2024-01-15 09:00"
completed_at: "2024-01-15 16:30"
agents_involved:
  - "Claude (Scheduling Expert)"
  - "Human (Dr. Smith, Program Director)"
outcome: "SUCCESS"
related_phases:
  - "Block 9 Schedule Generation"
  - "Block 11 Planning"
tags:
  - "schedule-generation"
  - "acgme-compliance"
  - "constraint-solving"
```
---

## Executive Summary

**What:** Generated compliant Block 10 schedule for 12 residents across 6 rotations with 100% ACGME compliance.

**Why:** Block 10 begins March 1st and requires advance scheduling for resident planning and clinic staffing.

**Impact:** All residents have confirmed assignments, clinic coverage is complete, and all ACGME work hour limits are satisfied.

---

## Objectives

### Primary Goals

1. Generate Block 10 assignments for all 12 residents
2. Ensure 100% ACGME compliance (80-hour rule, 1-in-7 rule)
3. Maintain clinic coverage requirements (minimum 3 residents/day)

### Success Criteria

- [x] All residents assigned to exactly one rotation
- [x] No ACGME violations detected
- [x] Clinic coverage ≥ 3 residents per weekday
- [x] Night Float rotation has 2 residents minimum

---

## Key Decisions

### Decision 1: Use OR-Tools CP-SAT Solver

**Context:** Need to balance 47 constraints across 12 residents and 6 rotations.

**Options Considered:**
- **Option A:** Manual assignment with Excel
  - Pros: Familiar to staff
  - Cons: Error-prone, no automated compliance checking
- **Option B:** OR-Tools CP-SAT solver
  - Pros: Automated constraint solving, proven algorithm
  - Cons: Learning curve for customization

**Decision:** OR-Tools CP-SAT solver

**Rationale:** Automated compliance checking reduces risk and scales to future blocks.

---

## Outcomes

### Deliverables

- [x] Block 10 schedule exported to `schedules/block_10_final.json`
- [x] ACGME compliance report generated
- [x] Resident assignments committed to database

### Metrics & Results

| Metric | Target | Actual | Notes |
|--------|--------|--------|-------|
| ACGME Violations | 0 | 0 | All residents compliant |
| Clinic Coverage | ≥3/day | 3.2 avg | Exceeds minimum |
| Solver Runtime | <5 min | 2m 14s | Well within budget |

---

## Artifacts

### Files Created

```
backend/app/schedules/block_10_final.json
backend/app/reports/block_10_acgme_report.pdf
```

### Database Changes

**Migrations:**
- `2024-01-15_add_block_10_assignments.py`

**Schema Changes:**
- Table `assignments`: Added 240 new rows (12 residents × 20 days)

---

## Lessons Learned

### What Went Well

1. **Constraint prioritization**
   - Separating hard vs. soft constraints made debugging easier
   - Clear failure messages when constraints couldn't be satisfied

### What Could Be Improved

1. **Solver timeout handling**
   - Initial timeout of 60s was too short for complex constraint sets
   - Increased to 300s for production use

---

## Open Questions

### Unresolved Issues

1. **PGY-2 resident preference weighting**
   - **Context:** Current model weights all preferences equally
   - **Blocking:** Not blocking, but could improve resident satisfaction
   - **Owner:** Scheduling team
   - **Timeline:** Address in Block 11

---

## Next Phase Prerequisites

### Required Before Next Phase

- [ ] Resident feedback survey on Block 10 assignments
- [ ] Clinic preceptor availability for Block 11
- [ ] Updated ACGME guidelines for new academic year

---

**Phase completed by:** Claude
**Reviewed by:** Dr. Smith, Program Director
**Date:** 2024-01-15
