# Phase Summary Conventions

> **Purpose:** Guidelines for creating, naming, storing, and using phase summaries in long-horizon AI agent workflows
>
> **Last Updated:** 2024-01-15

---

## Table of Contents

1. [When to Create a Phase Summary](#when-to-create-a-phase-summary)
2. [Naming Conventions](#naming-conventions)
3. [Storage Organization](#storage-organization)
4. [How Agents Should Use Phase Summaries](#how-agents-should-use-phase-summaries)
5. [Context Window Management](#context-window-management)
6. [Archive and Retention Policy](#archive-and-retention-policy)
7. [Quality Standards](#quality-standards)

---

## When to Create a Phase Summary

### Mandatory Phase Summaries

Create a phase summary **immediately after** completing any of these major phases:

| Phase Type | Trigger | Example |
|------------|---------|---------|
| **Planning** | Major feature planning complete | "Block 10-15 Long-Range Planning" |
| **Research** | Technical spike or investigation done | "OR-Tools vs. Google Optimization Comparison" |
| **Design** | Architecture or API design finalized | "Swap Auto-Matcher Algorithm Design" |
| **Implementation** | Significant feature completed | "ACGME Compliance Validator Implementation" |
| **Testing** | Major test suite or load testing done | "Production Load Testing - 1000 Concurrent Users" |
| **Deployment** | Production deployment or migration | "PostgreSQL Migration to v15" |
| **Debugging** | Complex bug investigation resolved | "Race Condition in Schedule Assignment" |
| **Refactoring** | Major code restructuring complete | "Services Layer Extraction from Routes" |

### Optional Phase Summaries

Consider creating summaries for:

- Daily standup wrap-ups (for multi-day sprints)
- Code review outcomes (for large PRs)
- Retrospectives (after incidents or major releases)
- Knowledge transfer (before agent handoff)

### When NOT to Create a Phase Summary

**Don't create summaries for:**

- Trivial changes (typo fixes, minor refactors)
- Single-file edits
- Work still in progress (wait until phase completes)
- Duplicate summaries (one summary per phase)

---

## Naming Conventions

### File Naming Format

```
YYYY-MM-DD_phase-type_brief-description.md
```

**Examples:**
```
2024-01-15_implementation_block10-schedule-generation.md
2024-01-16_debugging_race-condition-assignments.md
2024-01-17_design_swap-auto-matcher-algorithm.md
2024-01-18_testing_acgme-compliance-load-test.md
```

### Naming Rules

1. **Date:** Use ISO 8601 format (YYYY-MM-DD) for the **completion** date
2. **Phase Type:** Use one of the standard phase types (lowercase, hyphenated):
   - `planning`
   - `research`
   - `design`
   - `implementation`
   - `testing`
   - `deployment`
   - `debugging`
   - `refactoring`
   - `migration`
   - `optimization`

3. **Description:**
   - Lowercase with hyphens
   - Max 50 characters
   - Descriptive but concise
   - Avoid generic terms like "feature" or "update"

### Bad Naming Examples

❌ `phase_summary.md` - No date, no description
❌ `2024-01-15.md` - No phase type or description
❌ `schedule_generation_phase_summary_final_v2.md` - No date, verbose
❌ `01-15-2024_implementation_thing.md` - Wrong date format, vague description

### Good Naming Examples

✅ `2024-01-15_implementation_block10-schedule-generation.md`
✅ `2024-01-16_debugging_race-condition-assignments.md`
✅ `2024-01-17_design_swap-auto-matcher-algorithm.md`

---

## Storage Organization

### Directory Structure

```
.claude/History/
├── PHASE_SUMMARY_TEMPLATE.md          # Template for new summaries
├── PHASE_CONVENTIONS.md               # This file
├── active/                            # Current work (last 30 days)
│   ├── 2024-01-15_implementation_block10-schedule-generation.md
│   ├── 2024-01-16_debugging_race-condition-assignments.md
│   └── 2024-01-17_design_swap-auto-matcher-algorithm.md
├── archive/                           # Completed work (30-365 days)
│   ├── 2023/
│   │   ├── 2023-12-01_implementation_initial-scheduling-engine.md
│   │   └── 2023-12-15_testing_acgme-validator-unit-tests.md
│   └── 2024/
│       └── Q1/
│           └── [older summaries]
├── examples/                          # Example summaries for reference
│   └── 2024-01-15_block10-schedule-generation.md
└── indexes/
    ├── by-phase-type.md              # Index organized by phase type
    ├── by-feature.md                 # Index organized by feature area
    └── by-agent.md                   # Index organized by agent/author
```

### Storage Location Rules

1. **New summaries** → `.claude/History/active/`
2. **After 30 days** → Move to `.claude/History/archive/YYYY/QN/`
3. **Examples/templates** → `.claude/History/examples/`

### Automatic Archival

Agents should check for summaries older than 30 days in `active/` and suggest moving them:

```bash
# Find summaries older than 30 days
find .claude/History/active/ -name "*.md" -mtime +30
```

---

## How Agents Should Use Phase Summaries

### Starting a New Phase

**Agent should:**

1. **Check for related previous phases:**
   ```bash
   # Search for related summaries
   grep -r "swap-management" .claude/History/active/
   grep -r "schedule-generation" .claude/History/archive/2024/
   ```

2. **Read relevant summaries:**
   - Load 1-3 most recent related summaries
   - Focus on: Key Decisions, Open Questions, Next Phase Prerequisites

3. **Reference in new work:**
   ```markdown
   ## Context from Previous Phases

   This work builds on:
   - [Block 9 Schedule Generation](../active/2024-01-10_implementation_block9-schedule-generation.md)
   - [ACGME Validator Refactor](../archive/2023/2023-12-20_refactoring_acgme-validator.md)

   Key carryover decisions:
   - Using OR-Tools CP-SAT solver (from Block 9)
   - 300s timeout for complex constraints (from Block 9)
   ```

### During a Phase

**Agent should:**

1. **Track decisions in real-time** (don't wait until end)
2. **Note open questions** as they arise
3. **Document artifacts** as they're created
4. **Log unexpected discoveries** immediately

### Completing a Phase

**Agent should:**

1. **Create phase summary** using template
2. **Fill all mandatory sections:**
   - Executive Summary
   - Objectives
   - Key Decisions
   - Outcomes
   - Artifacts
   - Next Phase Prerequisites

3. **Optional sections** (fill if relevant):
   - Lessons Learned
   - Open Questions
   - Technical Debt

4. **Commit summary with code:**
   ```bash
   git add .claude/History/active/2024-01-15_implementation_feature-name.md
   git commit -m "feat: Implement feature X + phase summary"
   ```

### Referencing Previous Summaries

**In conversations:**

```
Agent: I see from the Block 9 summary (2024-01-10_implementation_block9-schedule-generation.md)
that we chose a 300s solver timeout. Should I use the same for Block 10?
```

**In commit messages:**

```
feat: Implement Block 10 schedule generation

Based on approach from Block 9 (see .claude/History/active/2024-01-10_implementation_block9-schedule-generation.md).

Key changes:
- Increased clinic coverage minimum from 3 to 4 residents
- Added preference weighting for PGY-2 residents

Resolves open question from Block 9: "How to handle increased clinic demand?"
```

**In documentation:**

```markdown
## Design Rationale

This algorithm design is based on the swap auto-matcher research phase
(see `.claude/History/active/2024-01-17_design_swap-auto-matcher-algorithm.md`).

We chose Option B (graph-based matching) over Option A (greedy algorithm)
for the reasons documented in that phase summary.
```

---

## Context Window Management

### Context Window Budget

Assume a working context window of ~100,000 tokens. Allocate as follows:

| Content Type | Token Budget | Notes |
|--------------|--------------|-------|
| Current task description | 5,000 | User prompt + task context |
| Codebase context | 40,000 | Files being edited |
| Phase summaries | 15,000 | 3-5 recent summaries |
| Documentation | 10,000 | Relevant docs |
| Test results | 10,000 | Recent test output |
| Reserved buffer | 20,000 | For agent responses |

### When to Reload Summaries

**Reload summaries when:**

- Starting a new session on a multi-day project
- Context window is getting full (>80% capacity)
- Agent needs to understand decisions made in previous phases
- Investigating a bug that may relate to earlier changes

### When to Summarize Instead of Reload

**Create a mini-summary instead of loading full summary when:**

- Only need 1-2 key facts (e.g., "What timeout did we use?")
- Context window is very constrained
- Phase summary is very long (>10,000 tokens)

**Example mini-summary:**

```markdown
## Quick Context: Block 9 Schedule Generation
- Solver: OR-Tools CP-SAT
- Timeout: 300s
- Key constraint: Clinic coverage ≥ 3 residents/day
- Open issue: PGY-2 preference weighting not implemented
```

### Aggressive Context Pruning

If context window is critically full:

1. **Remove oldest summaries first** (keep most recent 2)
2. **Summarize code files** instead of loading full text
3. **Extract only Key Decisions** from summaries
4. **Link to full summaries** for later review

---

## Archive and Retention Policy

### Retention Schedule

| Age | Location | Retention |
|-----|----------|-----------|
| 0-30 days | `active/` | Keep all |
| 30-365 days | `archive/YYYY/QN/` | Keep all |
| 1-3 years | `archive/YYYY/QN/` | Keep significant phases only |
| 3+ years | `archive/YYYY/` | Keep major milestones only |

### Archival Process

**Every 30 days (automated via script):**

```bash
# Move summaries older than 30 days to archive
./scripts/archive-phase-summaries.sh
```

**Script logic:**

1. Find summaries in `active/` older than 30 days
2. Determine year and quarter from date
3. Move to `archive/YYYY/QN/`
4. Update indexes in `indexes/`

### Deletion Policy

**Never delete:**
- Major release summaries (v1.0, v2.0, etc.)
- Production incident post-mortems
- Architecture decision records
- Security audit summaries

**May delete after 3 years:**
- Routine implementation summaries
- Minor bug fix summaries
- Exploratory research that didn't lead anywhere

---

## Quality Standards

### Minimum Quality Requirements

All phase summaries MUST include:

- [ ] Valid YAML frontmatter with all required fields
- [ ] Executive Summary (at least 2 sentences)
- [ ] At least one Objective
- [ ] At least one Key Decision (with rationale)
- [ ] List of Artifacts (files created/modified)
- [ ] Next Phase Prerequisites (or "None" if truly standalone)

### High-Quality Summaries

High-quality summaries also include:

- [ ] Metrics & Results with actual vs. target comparison
- [ ] Lessons Learned (what went well, what didn't)
- [ ] Open Questions for future phases
- [ ] References to related summaries or documentation
- [ ] Clear handoff information for next agent

### Quality Checklist

Before committing a phase summary, verify:

1. **Completeness:**
   - [ ] All mandatory sections filled out
   - [ ] No "TODO" or "[Fill this in later]" placeholders
   - [ ] All file paths are absolute (not relative)

2. **Accuracy:**
   - [ ] Dates and times are correct
   - [ ] File paths actually exist
   - [ ] Metrics match actual test results

3. **Clarity:**
   - [ ] Executive summary is understandable standalone
   - [ ] Key decisions have clear rationale
   - [ ] Next agent can pick up work from this summary alone

4. **Utility:**
   - [ ] Contains enough context for future reference
   - [ ] Doesn't duplicate information from code/docs (links instead)
   - [ ] Highlights non-obvious decisions and rationale

---

## Examples of Good vs. Bad Summaries

### ❌ Bad Example

```markdown
# Phase Summary: Implemented stuff

We implemented the schedule generator. It works now.

Files changed:
- scheduler.py
- some other files

Next: Do Block 11
```

**Problems:**
- No YAML frontmatter
- Vague description ("stuff", "some other files")
- No objectives, decisions, or rationale
- No context for future reference
- No metrics or validation

---

### ✅ Good Example

See `.claude/History/examples/2024-01-15_block10-schedule-generation.md` for a complete example.

**Key strengths:**
- Complete YAML frontmatter with all metadata
- Clear executive summary explaining what/why/impact
- Explicit objectives with success criteria
- Key decisions with options considered and rationale
- Measurable outcomes with metrics
- Clear artifacts with file paths
- Actionable next phase prerequisites

---

## Integration with AI Agent Workflows

### Slash Commands (for future implementation)

```bash
/phase:start [phase-type] [description]
  # Initializes a new phase summary from template

/phase:decision [decision-name]
  # Logs a key decision in the current phase

/phase:artifact [file-path]
  # Adds artifact to current phase summary

/phase:complete
  # Finalizes phase summary and moves to active/

/phase:search [query]
  # Searches historical phase summaries

/phase:load [phase-name]
  # Loads a previous phase summary into context
```

### Agent Prompts

**When starting new work:**

```
Before implementing [feature], search for related phase summaries:
1. Load .claude/History/active/ summaries from last 30 days
2. Check for related work in archive/
3. Reference previous decisions in your plan
4. Note any open questions you're addressing
```

**When completing work:**

```
You've completed [feature]. Create a phase summary:
1. Use template at .claude/History/PHASE_SUMMARY_TEMPLATE.md
2. Fill all mandatory sections
3. Document key decisions with rationale
4. List all artifacts created/modified
5. Specify next phase prerequisites
6. Save to .claude/History/active/[date]_[type]_[description].md
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-01-15 | Initial conventions document |

---

**Maintained by:** AI Agent Infrastructure Team
**Questions:** See `.claude/History/PHASE_SUMMARY_TEMPLATE.md` for template and examples
