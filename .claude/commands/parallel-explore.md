<!--
Quick parallel codebase exploration with auto-decomposition.
Spawns multiple Explore agents to search different dimensions simultaneously.
Use for rapid feature understanding, debugging context, or codebase reconnaissance.
-->

Arguments: $ARGUMENTS

---

***REMOVED******REMOVED*** Overview

This command decomposes your exploration query into 3-5 search dimensions and executes them in parallel using Explore subagents.

***REMOVED******REMOVED*** Usage

```
/parallel-explore "Find all ACGME validation code"
/parallel-explore "Understand the swap feature end-to-end"
/parallel-explore "Where is authentication handled?"
```

***REMOVED******REMOVED*** Behavior

1. **Decompose** - Break query into orthogonal search dimensions:
   - File patterns (glob)
   - Code patterns (grep)
   - Documentation references
   - Test files (reveal intent)
   - Related configuration

2. **Spawn** - Launch 3-5 Explore agents in parallel:
   ```
   Task(subagent_type="Explore", prompt="Search dimension 1...")
   Task(subagent_type="Explore", prompt="Search dimension 2...")
   Task(subagent_type="Explore", prompt="Search dimension 3...")
   ```

3. **Synthesize** - Combine findings into unified response

***REMOVED******REMOVED*** Example Decomposition

Query: "Find all ACGME validation code"

Dimensions:
1. Files matching `*acgme*` or `*compliance*`
2. Code containing `ACGME`, `work_hours`, `supervision_ratio`
3. Test files for validation logic
4. API routes with compliance endpoints
5. Documentation referencing ACGME rules

***REMOVED******REMOVED*** Model Selection

All Explore agents use `haiku` for speed. If deeper analysis needed, escalate to `/parallel-implement`.

***REMOVED******REMOVED*** Related Commands

- `/parallel-implement` - Multi-agent implementation
- `/parallel-test` - Parallel test execution
- `/handoff-session` - Multi-terminal coordination
