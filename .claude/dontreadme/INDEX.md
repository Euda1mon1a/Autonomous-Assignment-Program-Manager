# Master Index - LLM-Focused Documentation

**Quick Navigation:**
- [Session Reports](#session-reports) - Chronological session history
- [Reconnaissance Reports](#reconnaissance-reports) - Exploratory findings
- [Technical Deep Dives](#technical-deep-dives) - Implementation details
- [Synthesis](#synthesis) - Cross-session patterns and learnings
- [Agent Notes](#agent-notes) - Multi-agent coordination

---

## Session Reports

**Location:** `/sessions/`

Chronological record of development sessions with completion reports and deliverables.

### Recent Sessions (Session 20+)
- SESSION_037_DOCUMENTATION_RESTRUCTURE.md (this session)
- SESSION_036_PARALLEL_BURN.md
- SESSION_030_LOAD_TESTING.md
- SESSION_029_CONSTRAINT_AUDIT.md
- SESSION_028_SECURITY_AUDIT.md
- SESSION_026_FRONTEND_TESTING.md
- SESSION_025_CONTEXT_INDEXING.md

### Burn Sessions (Multi-Task Parallel Execution)
- BURN_1000_TASKS.md
- BURN_500_TASKS.md
- BURN_200_TASKS.md
- BURN_100_TASKS.md
- BURN_50_TASKS.md

### Historical Sessions (Session 1-19)
- See `/sessions/archive/` for Sessions 1-19

---

## Reconnaissance Reports

**Location:** `/reconnaissance/`

Exploratory research and multi-agent reconnaissance missions.

### OVERNIGHT_BURN Series
- G2_RECON_MULTI_TERMINAL.md - Multi-terminal parallel reconnaissance
- SEARCH_PARTY_10_PROBES.md - 10 D&D-inspired exploration agents
- OVERNIGHT_BURN_CHRONICLE.md - Master chronicle of overnight sessions

### Specialized Recon
- FRONTEND_ISSUE_MAP.md - Frontend/backend boundary analysis
- BACKEND_ISSUES_THAT_LOOK_FRONTEND.md - Misattributed issues
- EXOTIC_CONCEPTS_RAG.md - RAG readiness for cross-disciplinary concepts

---

## Technical Deep Dives

**Location:** `/technical/`

Implementation-level documentation for LLM context loading.

### Constraint System
- CONSTRAINTS_REFACTORING_SUMMARY.md
- CONSTRAINT_PREFLIGHT_CHECKS.md
- ACGME_COMPLIANCE_INTERNALS.md

### Resilience Framework
- BURNOUT_FIRE_INDEX_IMPLEMENTATION.md
- SPC_STATISTICAL_PROCESS_CONTROL.md
- PROCESS_CAPABILITY_METRICS.md
- STABILITY_METRICS_IMPLEMENTATION.md

### Scheduling Engine
- SOLVER_ALGORITHM_INTERNALS.md
- SCHEDULE_GENERATION_PIPELINE.md
- CONFLICT_RESOLUTION_LOGIC.md

### MCP Server
- MCP_IMPLEMENTATION_SUMMARY.md
- AGENT_IMPLEMENTATION_DETAILS.md
- ERROR_HANDLING_PATTERNS.md
- API_CLIENT_ARCHITECTURE.md

### Frontend
- GRAPHQL_SUBSCRIPTIONS_IMPLEMENTATION.md
- ROLE_FILTER_ARCHITECTURE.md
- DASHBOARD_IMPLEMENTATION.md

---

## Synthesis

**Location:** `/synthesis/`

High-level patterns and cross-session learnings.

### Key Documents
- PATTERNS.md - Recurring implementation patterns (NEW: Embarrassingly Parallel pattern)
- DECISIONS.md - Architectural decision record (ADR)
- LESSONS_LEARNED.md - Aggregated insights across sessions
- CROSS_DISCIPLINARY_CONCEPTS.md - Resilience framework mappings

### RAG Ingest Queue
- RAG_INGEST_QUEUE/ - Documents pending ingestion into RAG knowledge base
  - ai_pattern_embarrassingly_parallel.md - High-priority parallelization pattern

---

## Agent Notes

**Location:** `/agents/`

Multi-agent coordination and PAI (Programmatic Artificial Intelligence) specifications.

### Agent Protocols
- SEARCH_PARTY_PROTOCOL.md - 10-agent recon protocol
- PARALLEL_ORCHESTRATION.md - Multi-terminal coordination
- AGENT_FACTORY_OUTPUTS.md - Generated agent specs

---

## How to Use This Index

### For New Sessions
1. Read **SYNTHESIS.md** first for current project state
2. Check **DECISIONS.md** for architectural constraints
3. Review relevant **TECHNICAL/** docs for implementation details
4. Reference **SESSIONS/** for recent work

### For Debugging
1. Check **PATTERNS.md** for known gotchas
2. Review **TECHNICAL/** for implementation internals
3. Cross-reference **SESSIONS/** for similar past issues

### For Research
1. Start with **RECONNAISSANCE/** for exploratory findings
2. Deep dive into **TECHNICAL/** for implementation details
3. Synthesize learnings into **SYNTHESIS/**

---

**Maintenance Notes:**
- Session reports added after each session
- Technical deep dives updated as implementations evolve
- Synthesis documents updated quarterly or after major milestones
- Agent notes added as new protocols emerge

**Last Updated:** 2026-01-01 (Session mcp-refinement)
