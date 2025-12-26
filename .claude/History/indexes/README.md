# Phase Summary Indexes

This directory contains index files that organize phase summaries by different dimensions for quick reference.

## Index Files

### `by-phase-type.md`
Organizes phase summaries by type (planning, research, design, implementation, testing, deployment, debugging, refactoring).

**Example:**
```markdown
# Phase Summaries by Type

## Implementation
- [2024-01-15: Block 10 Schedule Generation](../active/2024-01-15_implementation_block10-schedule-generation.md)
- [2024-01-10: Block 9 Schedule Generation](../archive/2024/Q1/2024-01-10_implementation_block9-schedule-generation.md)

## Debugging
- [2024-01-16: Race Condition in Assignments](../active/2024-01-16_debugging_race-condition-assignments.md)
```

### `by-feature.md`
Organizes phase summaries by feature area (scheduling, swaps, compliance, resilience, etc.).

**Example:**
```markdown
# Phase Summaries by Feature Area

## Scheduling
- [2024-01-15: Block 10 Schedule Generation](../active/2024-01-15_implementation_block10-schedule-generation.md)
- [2024-01-10: Block 9 Schedule Generation](../archive/2024/Q1/2024-01-10_implementation_block9-schedule-generation.md)

## ACGME Compliance
- [2023-12-20: ACGME Validator Refactor](../archive/2023/2023-12-20_refactoring_acgme-validator.md)
```

### `by-agent.md`
Organizes phase summaries by the primary agent/author who completed the work.

**Example:**
```markdown
# Phase Summaries by Agent

## Claude (Scheduling Expert)
- [2024-01-15: Block 10 Schedule Generation](../active/2024-01-15_implementation_block10-schedule-generation.md)
- [2024-01-10: Block 9 Schedule Generation](../archive/2024/Q1/2024-01-10_implementation_block9-schedule-generation.md)

## Human (Dr. Smith)
- [2024-01-12: Resident Feedback Analysis](../active/2024-01-12_research_resident-feedback-analysis.md)
```

## Maintenance

Indexes should be updated:
- **Manually:** When creating new phase summaries (add entry to relevant indexes)
- **Automatically:** (Future) Script to regenerate indexes from phase summary YAML frontmatter

## Search Alternative

Instead of browsing indexes, you can search phase summaries directly:

```bash
# Search by keyword
grep -r "Night Float" .claude/History/active/
grep -r "ACGME" .claude/History/archive/

# Search by date range
find .claude/History/ -name "2024-01-*"

# Search by phase type
find .claude/History/ -name "*_implementation_*"
```
