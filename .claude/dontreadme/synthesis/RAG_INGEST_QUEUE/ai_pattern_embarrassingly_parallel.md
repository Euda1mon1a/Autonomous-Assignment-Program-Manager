# RAG Ingest: Embarrassingly Parallel Pattern

**doc_type:** ai_patterns
**priority:** high
**discovery_date:** 2026-01-01
**session:** mcp-refinement
**tags:** parallelization, multi-agent, context-management, orchestration

---

## Pattern: Embarrassingly Parallel = N Agents for N Tasks

When facing N independent tasks, spawn N agents rather than 1 agent doing N tasks serially.

### The Anti-Pattern (Context Collapse)

Spawning 1 agent to do N file edits serially causes failure:
- Agent reads all N files into context
- Context grows with each file
- Eventually hits token limit
- Work stops partway through

Example failure: 2 agents assigned 25 files each. Both hit context limits, 0 files edited.

### The Correct Pattern (Parallel Isolation)

Spawn N agents for N independent tasks:
- Each agent has isolated context
- Each reads only 1 file
- No cross-contamination
- All succeed trivially

Formula: If tasks are independent, parallelism is free.

### When to Apply

Use this pattern for:
- Updating multiple files with similar changes
- Running validation across many files
- Any "for each file, do X" operation
- Search/reconnaissance across directories
- Batch processing operations

### Cost Analysis

| Approach | Token Cost | Wall-Clock Time | Success Rate |
|----------|------------|-----------------|--------------|
| 1 agent, N tasks | N files processed | Time(N) | ~60% (context limited) |
| N agents, 1 task each | N files processed | Time(1) | ~100% (isolated context) |

Token cost is identical (each file processed once either way), but parallel approach finishes in time of 1 task instead of N, with 100% success rate vs context-limited failure.

### Related Protocols

- /search-party: 120 parallel probes (12 G-2 RECON agents x 10 probes each)
- /qa-party: 8+ parallel QA agents for validation
- /plan-party: 10 parallel planning probes for strategy generation

### Implementation Guidance

When orchestrating multi-file operations:

1. Identify if tasks are truly independent (no shared mutable state)
2. If independent, spawn one agent per task
3. Aggregate results after all agents complete
4. Handle partial failures gracefully

### Retrieval Triggers

This pattern should be retrieved when agents:
- Plan to process multiple files
- Discuss "iterating over" or "for each" operations
- Consider batch updates or mass edits
- Face context limit warnings
- Plan reconnaissance or search operations
