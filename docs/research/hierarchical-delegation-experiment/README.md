# Hierarchical Delegation Experiment

> **Note:** This experiment used the pre-archive PAI v1 structure. Agent specs, identity cards, and governance files were archived in Feb 2026. See `.claude/archive/` for historical reference.

Research into multi-agent hierarchical delegation patterns, comparing SOF (Special Operations Forces) vs Conventional force structures for software engineering tasks.

## Overview

This experiment tests the hypothesis that proper hierarchical delegation with parallelization outperforms both solo execution AND improper force structure selection, regardless of SOF vs Conventional doctrine.

## Contents

| File | Description |
|------|-------------|
| `EXPERIMENT_PLAN_v2.md` | Complete v2.0 experiment design with doctrinal mandates |
| `SESSION_086_V1_REPORT.md` | Full historical record of v1.0 experiment (HISTORIAN report) |
| `QUICK_REFERENCE.md` | Summary of v2.0 design and key findings from v1.0 |

## Key Findings from v1.0

1. **Neither pool spawned subagents** - Task didn't require delegation
2. **Pool C (ARCHITECT+SYNTHESIZER) won** 2 of 3 evaluation phases
3. **Token efficiency is decisive** - Pool C was 3.65x more efficient
4. **Surgical Edit >> Full-file Write** - Tool selection discipline matters
5. **Context isolation is filtering, not overhead** - Full context paradox observed

## v2.0 Improvements

v2.0 addresses v1.0 failures with:
- Mandatory delegation via doctrinal mandates in prompts
- 150+ file task requiring parallel execution
- 10+ parallel agents minimum at execution tier
- 3-level hierarchy minimum
- Violation penalties for direct execution by Deputies/Coordinators

## Replication

To replicate this experiment:

1. **Identify 100+ independent files** for audit/remediation
2. **Create agent identity cards** per `.claude/Identities/*.identity.md` *(Archived -- see `.claude/archive/identities/`)*
3. **Include doctrinal mandates** in mission prompts
4. **Launch pools in parallel** via Task() with `run_in_background=true`
5. **Grade with neutral panel** (G6_SIGNAL, CODE_REVIEWER, DELEGATION_AUDITOR)

## Related Documentation

- `.claude/Governance/HIERARCHY.md` *(Archived -- see `.claude/archive/governance/`)* - PAI hierarchy structure
- `.claude/Governance/CONSTITUTION.md` *(Archived -- see `.claude/archive/governance/`)* - Auftragstaktik doctrine
- `.claude/Identities/` *(Archived -- see `.claude/archive/identities/`)* - Agent identity cards
- `CLAUDE.md` - Project guidelines including delegation philosophy

## Session History

- **Session 086 v1.0** - Initial experiment (failed: no delegation occurred)
- **Session 086 v2.0** - Redesign with forced delegation (pending execution)
