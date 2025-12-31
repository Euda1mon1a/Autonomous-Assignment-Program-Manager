<!--
Multi-agent parallel implementation with automatic task decomposition.
Spawns domain-appropriate agents to implement features across multiple files.
Use for features touching multiple areas of the codebase.
-->

Arguments: $ARGUMENTS

---

## Overview

This command decomposes implementation tasks by domain and spawns appropriate agents (SCHEDULER, ARCHITECT, QA_TESTER, etc.) to work in parallel.

## Usage

```
/parallel-implement "Add swap timeout feature with tests"
/parallel-implement --agents=3 "Implement resilience dashboard API"
/parallel-implement --dry-run "Refactor auth to use refresh tokens"
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--agents` | 3 | Maximum parallel agents |
| `--dry-run` | false | Plan only, no execution |
| `--domain` | auto | Force specific domain |

## Behavior

1. **Analyze** - Determine domains affected:
   - Backend API → BACKEND_ENGINEER
   - Database → ARCHITECT
   - Scheduling → SCHEDULER
   - Tests → QA_TESTER
   - Frontend → FRONTEND_ENGINEER

2. **Decompose** - Split task by domain boundaries

3. **Spawn** - Launch agents respecting PARALLELISM_FRAMEWORK:
   - Check Level 1 (domain conflicts)
   - Check Level 2 (dependencies)
   - Check Level 3 (integration points)

4. **Coordinate** - SYNTHESIZER integrates results

## Example Decomposition

Task: "Add swap timeout feature with tests"

Agents:
1. SCHEDULER - Implement timeout logic in swap_executor.py
2. ARCHITECT - Add timeout_at column to swap model
3. QA_TESTER - Write tests for timeout scenarios

Dependency: ARCHITECT runs first (schema change), then SCHEDULER + QA_TESTER parallel.

## Model Selection

Uses auto-tier selection from ORCHESTRATOR:
- Simple file edits → sonnet
- Architecture decisions → opus
- Test generation → sonnet

## Related Commands

- `/parallel-explore` - Codebase exploration
- `/parallel-test` - Test execution
- `/handoff-session` - Multi-terminal coordination
