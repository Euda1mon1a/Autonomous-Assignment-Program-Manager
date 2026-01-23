# Session: mcp-refinement (2026-01-01)

## 🔑 CRITICAL INSIGHT: ALWAYS ORCHESTRATOR MODE

**I am ALWAYS in ORCHESTRATOR mode.** Not just when `/startupO` is invoked.

Every session: **Delegate, don't execute.**
- 99% → Spawn ARCHITECT/SYNTHESIZER
- 1% → Direct action (nuclear option only)

## Branch
`mcp-refinement` (from main after merging fix/mcp-lifespan PR #604)

## Completed

### 1. MCP RAG Verification
- RAG is integrated into MCP server with 4 tools: `rag_search`, `rag_context`, `rag_health`, `rag_ingest`
- **185 chunks** in `rag_documents` table across 15 doc_types
- Backend routes mounted at `/api/rag/*`
- pgvector indexes (HNSW + IVFFlat) working

### 2. G4 Agent Structure Decision
- **G4_CONTEXT_MANAGER**: Curator for RAG (decides what to remember)
- **G4_LIBRARIAN**: File reference manager (tracks paths in agent specs)
- **Decision**: Keep separate for now - RAG is new, file paths have been working
- Added to HUMAN_TODO for future decision when usage patterns emerge

### 3. Agent Hierarchy Updates - ALL 56 AGENTS
- Added "Spawn Context" section to all 56 agent specs
- Documents: Spawned By, Reports To, This Agent Spawns, Related Protocols
- Enables agents to see chain of command before spawning

## Key Lessons Learned

### Embarrassingly Parallel = N Agents for N Tasks
**Anti-pattern:** 1 agent × N files = context explodes, work fails
**Pattern:** N agents × 1 file each = all succeed trivially

- 2 agents with 25 files each → both hit context limits, 0 edits
- 9 agents with 5-7 files each → all completed successfully
- **Cost is same, wall-clock faster, success rate 100%**

Related: /search-party, /qa-party, /plan-party all use this pattern

### RAG Curation Philosophy
- RAG provides **mechanism** (API), G4 provides **judgment** (curation)
- Without intentional curation, RAG could get contaminated with:
  - Failed approaches
  - Debugging tangents
  - Work-in-progress that got reverted
- User corrections should be weighted higher than AI self-learning

## Next: Workforce Refinement
- Review agent pipeline consistency
- Ensure coordinators are used properly (not bypassed)
- May need to update protocols for spawn routing

## Files Modified
- HUMAN_TODO.md - Added G4 structure decision
- .claude/Agents/*.md - All 56 updated with Spawn Context
- .claude/dontreadme/synthesis/PATTERNS.md - Added parallelization pattern
- .claude/dontreadme/synthesis/LESSONS_LEARNED.md - Session entry
- .claude/dontreadme/synthesis/RAG_INGEST_QUEUE/ - Created for pending ingestions

## Stack Status
- GREEN: All services healthy
- Branch: mcp-refinement (ahead of main by local commits)
