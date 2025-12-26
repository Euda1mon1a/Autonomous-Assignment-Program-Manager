# Scratchpad - Temporary Working Files

> **Purpose:** Temporary workspace for development, experiments, and working notes
> **Retention:** Auto-cleanup after 7 days (configurable)
> **Status:** NOT committed to git (added to .gitignore)

---

## Overview

The Scratchpad is a temporary workspace for AI agents and developers to work through problems, experiment with solutions, and document in-progress thinking **without polluting permanent storage**.

**Key Principle:** Scratchpad is for **messy, iterative work**. History is for **clean, finalized records**. Think of Scratchpad as your whiteboard, and History as your filing cabinet.

**What Makes Scratchpad Different:**

| Aspect | Scratchpad | History |
|--------|------------|---------|
| **Permanence** | Temporary (7-day default) | Permanent (committed to git) |
| **Audience** | Self (current agent/developer) | Future reviewers, auditors |
| **Formality** | Informal notes, half-baked ideas | Structured, complete documentation |
| **Review** | No review required | Quality checklist before commit |
| **Version Control** | **NOT** in git (gitignored) | Committed and versioned |
| **Cleanup** | Auto-delete after retention period | Manual archive only |

---

## When to Use Scratchpad

**Use Scratchpad for:**

### 1. Debugging & Investigation
```markdown
# Scratchpad/2025-08-15_14-30_debug_solver_timeout.md

## Problem
Solver timing out on Block 11. Investigating why.

## Observations
- Constraint count: 1247 (vs. 987 in Block 10)
- New constraints added:
  - N95 Fit requirement (added 180 constraints)
  - Flu Vax requirement (added 80 constraints)
- Leave requests: 5 (vs. 3 in Block 10)

## Hypothesis
Over-constrained problem. Too many hard constraints for solver to satisfy.

## Tests
1. Relaxed N95 Fit to soft → solved in 6m 12s ✅
2. Relaxed Flu Vax to soft → solved in 5m 45s ✅
3. Both relaxed → solved in 4m 58s ✅

## Conclusion
Credential requirements are hard constraints but should be soft with penalties.
Need to reclassify in constraint catalog.

## Next Steps
- [ ] Create PR to reclassify credential constraints
- [ ] Add test case for over-constrained scenarios
- [ ] Document in History after fix deployed
```

### 2. Experiment Design
```markdown
# Scratchpad/2025-08-10_09-15_experiment_pareto_optimization.md

## Experiment: Multi-Objective Pareto Optimization

**Goal:** Test if Pareto optimization improves preference satisfaction without
sacrificing fairness.

**Hypothesis:** Current single-objective approach (minimize penalty) leaves
preference satisfaction on the table. Pareto frontier exploration will find
better trade-off.

**Method:**
1. Run baseline (current algorithm) on Block 10 data
2. Run Pareto optimization with objectives: [fairness, preferences, continuity]
3. Compare solutions on Pareto frontier
4. Select best trade-off solution

**Results:**
- Baseline: fairness=0.8σ, pref_sat=58%, continuity=72%
- Pareto solution 1: fairness=0.9σ, pref_sat=65%, continuity=68%
- Pareto solution 2: fairness=0.7σ, pref_sat=61%, continuity=75%

**Decision:** Solution 2 is Pareto dominant. Adopt for production.

**Promote to:** History after implementation + validation
```

### 3. Brainstorming & Design
```markdown
# Scratchpad/2025-07-20_11-00_design_credential_dashboard.md

## Idea: Credential Expiration Dashboard

**Problem:** Faculty credentials expire silently, causing last-minute swap
rejections and schedule conflicts.

**Proposed Solution:**
- Dashboard widget showing expiring credentials (30/60/90 day windows)
- Email alerts at 30 days (reminder) and 14 days (urgent)
- Integration with swap validator (reject if credential expires before shift)

**UI Mockup:**
```
┌─────────────────────────────────────┐
│ Credential Expiration Alerts        │
├─────────────────────────────────────┤
│ Expiring in 30 Days (3)             │
│  - FAC-PD: BLS (Aug 15)             │
│  - PGY2-01: N95 Fit (Aug 22)        │
│  - PGY3-04: ACLS (Aug 28)           │
│                                     │
│ Expiring in 14 Days (1) 🔴          │
│  - FAC-APD: HIPAA (Aug 8)           │
└─────────────────────────────────────┘
```

**Questions:**
- Where to store credential data? (new table vs. extend persons table?)
- Who updates credential data? (admin only vs. self-service?)
- Renewal workflow? (manual entry vs. integration with HR system?)

**Next Steps:**
- [ ] Discuss with faculty
- [ ] Create formal spec in docs/
- [ ] Estimate implementation effort
```

### 4. Meeting Notes & Discussions
```markdown
# Scratchpad/2025-08-03_13-30_meeting_faculty_feedback.md

## Faculty Meeting: Block 10 Schedule Review

**Attendees:** FAC-PD, FAC-APD, Coordinator, SCHEDULER agent

**Feedback:**
1. Call distribution is fair ✅
2. Clinic days mostly good, but PGY1-03 unhappy with Tuesday (wanted Wednesday)
3. Night Float rotation too long (2 weeks → prefer 10 days max)
4. Procedure exposure uneven (PGY3-02 only 12 sessions vs. target 20)

**Action Items:**
- [ ] Consider soft constraint: max 10 days Night Float
- [ ] Add procedure exposure target to optimization objectives
- [ ] Review PGY1-03 clinic day preference for Block 11

**Follow-Up:** Block 11 generation (due Sept 1)
```

### 5. Draft Documentation
```markdown
# Scratchpad/2025-07-25_10-00_draft_constraint_audit_guide.md

## DRAFT: Quarterly Constraint Audit Guide

**Purpose:** Prevent constraint catalog bloat and over-constrained problems

**Procedure:**
1. Export constraint catalog to CSV
2. For each constraint:
   - Is it still relevant? (regulations change, policies updated)
   - Is it correctly tiered? (Tier 1 = regulatory, Tier 2 = policy, etc.)
   - Is it redundant? (duplicate or subsumed by other constraints)
   - What's its impact? (measure solve time delta)
3. Prune obsolete constraints
4. Reclassify mis-tiered constraints
5. Document changes in changelog

**Metrics:**
- Constraint count trend (target: ≤ 15:1 ratio to blocks)
- Solve time trend (flag >20% increase)
- Constraint activation rate (delete if <1% activation)

**Promote to:** docs/development/ after review
```

### 6. Quick Calculations & Scratch Work
```markdown
# Scratchpad/2025-08-12_16-45_calc_utilization_threshold.md

## Calculation: Safe Utilization Threshold

**Queuing Theory (Erlang C):**
Given:
- Residents: 12
- Avg demand: 15 shifts/day
- Avg shift duration: 12 hours

Utilization = demand / (capacity × availability)
           = 15 / (12 × 2)  # 2 sessions/day
           = 0.625 (62.5%)

Safe threshold (avoid queue buildup): 80% utilization
Max sustainable demand: 0.8 × 12 × 2 = 19.2 shifts/day

**Conclusion:** Current 62.5% utilization is safe (GREEN zone)

**Buffer capacity:** 19.2 - 15 = 4.2 shifts/day (28% buffer)
```

---

## Naming Convention

All Scratchpad entries follow this format:

```
YYYY-MM-DD_HH-MM_<task-description>.md
```

**Components:**
- `YYYY-MM-DD`: Date of creation
- `HH-MM`: Time of creation (24-hour format)
- `<task-description>`: Short, descriptive name (use hyphens, not spaces)

**Examples:**
```
2025-08-15_14-30_debug_solver_timeout.md
2025-08-10_09-15_experiment_pareto_optimization.md
2025-07-20_11-00_design_credential_dashboard.md
2025-08-03_13-30_meeting_faculty_feedback.md
2025-07-25_10-00_draft_constraint_audit_guide.md
```

**Tips:**
- Be specific in description (not "notes.md", use "debug_swap_validation.md")
- Include ticket/issue number if applicable (e.g., "fix_issue_247_swap_bug.md")
- Date prefix enables automatic cleanup sorting

---

## Auto-Cleanup Policy

**Retention Period:** 7 days (default)

**Cleanup Schedule:**
- **Daily cleanup:** Runs at 00:00 local time
- **Checks:** All files older than retention period
- **Action:** Move to `.claude/Scratchpad/archive/` (then delete archive after 30 days)

**Configure retention period:**
```bash
# In .claude/settings.json
{
  "scratchpad": {
    "retention_days": 7,
    "archive_retention_days": 30,
    "auto_cleanup": true
  }
}
```

**Manual cleanup:**
```bash
# List files older than 7 days
find .claude/Scratchpad/ -name "*.md" -mtime +7

# Archive old files
mkdir -p .claude/Scratchpad/archive
find .claude/Scratchpad/ -name "*.md" -mtime +7 -exec mv {} .claude/Scratchpad/archive/ \;

# Delete very old archives (>30 days)
find .claude/Scratchpad/archive/ -name "*.md" -mtime +30 -delete
```

**Prevent cleanup (pin important files):**
```bash
# Add .keep suffix to prevent auto-cleanup
mv 2025-08-15_important_notes.md 2025-08-15_important_notes.md.keep
```

---

## When to Promote to Permanent Storage

**Promote Scratchpad → History when:**

1. **Investigation Complete**
   - Root cause identified
   - Solution implemented and tested
   - Incident resolved
   → Create incident postmortem in `.claude/History/incidents/`

2. **Experiment Successful**
   - Hypothesis validated
   - Results reproducible
   - Decision to deploy made
   → Document in `.claude/History/scheduling/` or relevant category

3. **Design Finalized**
   - Stakeholder approval obtained
   - Implementation plan ready
   - Formal spec needed
   → Move to `docs/planning/` or `docs/architecture/`

4. **Decision Documented**
   - Trade-off analysis complete
   - Rationale clear and justified
   - Permanent record needed for future reference
   → Create History entry with decision rationale

**Promotion Checklist:**
- [ ] Content is finalized (no "TODO" or "DRAFT" sections)
- [ ] Formatting is clean (use History template)
- [ ] Context is clear for future readers (not just for you)
- [ ] Sensitive data redacted (OPSEC/PERSEC check)
- [ ] Appropriate category selected (scheduling, swaps, incidents, etc.)
- [ ] Committed to git (History only, never Scratchpad)

**Example Promotion Workflow:**
```bash
# 1. Copy content from Scratchpad to History (using template)
cp .claude/History/incidents/TEMPLATE.md \
   .claude/History/incidents/2025-08-15_solver_timeout.md

# 2. Fill in template with finalized content from Scratchpad
vim .claude/History/incidents/2025-08-15_solver_timeout.md

# 3. Commit to git
git add .claude/History/incidents/2025-08-15_solver_timeout.md
git commit -m "history: Document solver timeout incident (INC-042)"

# 4. Delete Scratchpad file (or let auto-cleanup handle it)
rm .claude/Scratchpad/2025-08-15_14-30_debug_solver_timeout.md
```

---

## Best Practices

### 1. Start with Scratchpad, Finish with History

**Workflow:**
```
Scratchpad (rough notes)
    ↓
Iterate (refine understanding)
    ↓
Finalize (clean up, structure)
    ↓
Promote to History (permanent record)
```

**Don't:**
- Write directly to History (skipping Scratchpad)
- Leave important info in Scratchpad past retention period
- Commit Scratchpad to git

### 2. Use Descriptive Filenames

**Good:**
- `2025-08-15_debug_swap_validation_failure.md`
- `2025-07-20_experiment_pareto_vs_single_objective.md`
- `2025-08-03_meeting_block10_faculty_review.md`

**Bad:**
- `notes.md` (what notes?)
- `debug.md` (debug what?)
- `temp.md` (temp for what?)

### 3. Date Everything

**Why:** Enables chronological sorting and auto-cleanup

**Format:** `YYYY-MM-DD_HH-MM` (ISO 8601 compatible)

**Example:** `2025-08-15_14-30` = August 15, 2025 at 2:30 PM

### 4. Link to Related Records

**Cross-reference permanent docs:**
```markdown
## Related
- Schedule: .claude/History/scheduling/2025-07-15_block10_gen001.md
- Incident: .claude/History/incidents/2025-08-05_solver_timeout.md
- Design Doc: docs/architecture/SOLVER_ALGORITHM.md
- Issue: GitHub issue #247
```

**This enables:**
- Context reconstruction
- Impact tracing
- Related work discovery

### 5. Capture Uncertainty

**Scratchpad is for thinking out loud:**
```markdown
## Hypothesis
Maybe the solver timeout is because constraint count grew too high?

## Evidence
- Block 10: 987 constraints → solve time 4m 30s
- Block 11: 1247 constraints → timeout at 30m

## Uncertainty
Not sure if it's just constraint count or also constraint interdependency.
Need to profile solver to see where time is spent.

## Next Steps
- [ ] Run solver with profiling enabled
- [ ] Analyze constraint graph for cycles
- [ ] Test with constraint pruning
```

**Don't censor yourself** - capture all ideas, even half-formed ones.

---

## Integration with Other PAI Components

### Scratchpad ↔ History

**Relationship:** Scratchpad is the rough draft, History is the final publication

**Workflow:**
```
Investigation/Experiment
    ↓
Scratchpad (working notes)
    ↓
Resolution/Completion
    ↓
History (permanent record)
```

### Scratchpad ↔ MetaUpdater

**MetaUpdater scans Scratchpad for:**
- Recurring patterns (same debug session repeated?)
- Common experiments (same hypothesis tested multiple times?)
- Frequent blockers (what slows agents down?)

**Example:**
- **Pattern Detected:** "3 Scratchpad files in 30 days debugging solver timeout"
- **MetaUpdater Action:** "Propose: Add automated solver timeout detection to pre-flight checks"
- **Outcome:** Permanent fix added, pattern breaks

### Scratchpad ↔ Skills

**Skills can create Scratchpad entries:**

Example: `systematic-debugger` skill
```markdown
# Scratchpad/2025-08-15_15-00_systematic_debug_swap_error.md

## Generated by: systematic-debugger skill

### Phase 1: Exploration
[Agent reads code, examines logs]

### Phase 2: Hypothesis Generation
[Agent creates 5 hypotheses for root cause]

### Phase 3: Testing
[Agent tests each hypothesis]

### Phase 4: Fix
[Agent implements fix]

### Promotion
Promoted to: .claude/History/incidents/2025-08-15_swap_validation_bug.md
```

---

## Security & Privacy

**Scratchpad is NOT committed to git** (added to `.gitignore`)

**Why:**
- Prevents accidental commit of sensitive debugging data
- Allows agents to work freely without permanent record
- Avoids repo bloat from temporary files

**However:**
- Scratchpad is still **local disk storage** (not encrypted by default)
- Follow OPSEC/PERSEC rules:
  - Use role IDs (`PGY2-01`), not real names
  - Redact sensitive data (TDY destinations, medical info)
  - Don't copy production passwords/tokens to Scratchpad

**If Scratchpad contains sensitive data:**
```bash
# Secure delete (overwrite before removal)
shred -vfz -n 10 .claude/Scratchpad/sensitive_file.md
```

---

## Troubleshooting

### "Scratchpad file disappeared!"

**Cause:** Auto-cleanup deleted file older than retention period

**Solution:**
1. Check archive: `.claude/Scratchpad/archive/`
2. If not archived, file is deleted (no recovery)
3. **Prevention:** Pin important files (`.keep` suffix) or promote to History

### "Scratchpad is getting cluttered"

**Solution:**
```bash
# Manual cleanup (preview first)
find .claude/Scratchpad/ -name "*.md" -mtime +3

# Delete files older than 3 days
find .claude/Scratchpad/ -name "*.md" -mtime +3 -delete
```

### "Want to share Scratchpad file with team"

**Solution:** Promote to appropriate permanent location
- Technical docs → `docs/`
- Decisions → `.claude/History/`
- Code → Implement + PR

**Don't:** Commit Scratchpad to git (defeats purpose of temporary workspace)

---

## Quick Reference

**Create new Scratchpad entry:**
```bash
# Auto-generate filename with timestamp
vim .claude/Scratchpad/$(date +%Y-%m-%d_%H-%M)_debug_issue.md
```

**List recent Scratchpad files:**
```bash
ls -lt .claude/Scratchpad/*.md | head -10
```

**Find Scratchpad file by content:**
```bash
grep -r "solver timeout" .claude/Scratchpad/
```

**Archive old Scratchpad files manually:**
```bash
mkdir -p .claude/Scratchpad/archive
find .claude/Scratchpad/ -name "*.md" -mtime +7 -exec mv {} .claude/Scratchpad/archive/ \;
```

**Check Scratchpad disk usage:**
```bash
du -sh .claude/Scratchpad/
```

---

## Related Documentation

- **History/README.md:** Permanent audit trail system
- **CONSTITUTION.md:** Foundational rules for all operations
- **docs/PERSONAL_INFRASTRUCTURE.md:** Complete PAI architecture
- **docs/development/DEBUGGING_WORKFLOW.md:** Systematic debugging methodology

---

**Version:** 1.0.0
**Last Updated:** 2025-12-26
**Maintained By:** All agents (collaborative workspace)

---

## Example Scratchpad Session

**Scenario:** Debugging a swap validation bug

```markdown
# Scratchpad/2025-08-15_14-30_debug_swap_validation_failure.md

## Problem
Swap request S12347 rejected with error: "ACGME violation detected"
But manual calculation shows no violation. Investigating.

## Investigation

### Step 1: Reproduce
- Swap: PGY2-01 ↔ PGY2-03 for Aug 20 PM
- Error: "PGY2-01 would exceed 80-hour limit"
- Manual calc: PGY2-01 has 68 hours this week (Aug 14-20)

### Step 2: Examine Code
File: backend/app/services/swap_validator.py, line 142

```python
# Bug found!
weekly_hours = calculate_work_hours(
    person_id, week_start, week_end
)
# This includes the CURRENT shift being swapped!
# Should exclude current shift, only count NEW shift
```

### Step 3: Hypothesis
Work hour calculation is double-counting the shift being swapped out.

### Step 4: Test
- Remove current shift from calculation: 68 - 12 = 56 hours
- Add new shift: 56 + 12 = 68 hours
- Still under 80-hour limit ✅

### Step 5: Fix
Update calculate_work_hours() to accept exclude_blocks parameter.

```python
def calculate_work_hours(
    person_id: str,
    start_date: date,
    end_date: date,
    exclude_blocks: list[int] = None  # NEW
) -> float:
    # Filter out excluded blocks
    ...
```

## Outcome
- Bug fixed in PR #352
- Test added: test_swap_validator_excludes_current_shift()
- Validated with S12347 (now approves correctly)

## Promote To
.claude/History/incidents/2025-08-15_swap_validation_bug.md
```

---

**Remember:** Scratchpad is your thinking space. Write freely, iterate rapidly, then distill the best insights into permanent History records.
