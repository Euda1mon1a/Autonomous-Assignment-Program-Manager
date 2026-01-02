# MCP Tool Priority Matrix for PAI Agents

> **Session:** 039
> **Date:** 2026-01-01
> **Category:** MCP Architecture
> **Importance:** HIGH

## Priority Levels

### CRITICAL Priority (Must Have MCP Access)

| Agent | MCP Tools Needed |
|-------|-----------------|
| **SCHEDULER** | ALL scheduling tools + validation + resilience status |
| **SWAP_MANAGER** | swap tools + validation + contingency analysis |
| **COMPLIANCE_AUDITOR** | ALL acgme/compliance tools |
| **BURNOUT_SENTINEL** | ALL burnout/epidemiology tools |
| **G4_CONTEXT_MANAGER** | ALL RAG tools (owns semantic memory) |

### HIGH Priority

| Agent | MCP Tools Needed |
|-------|-----------------|
| RESILIENCE_ENGINEER | resilience + contingency + SPC tools |
| INCIDENT_COMMANDER | ALL monitoring tools + emergency overrides |
| DBA | database health + validation tools |
| BACKEND_ENGINEER | validation + conflict detection + task management |
| KNOWLEDGE_CURATOR | RAG tools for pattern capture |
| G2_RECON | RAG for reconnaissance persistence |
| G3_OPERATIONS | scheduling execution + resilience monitoring |

### MEDIUM Priority

| Agent | MCP Tools Needed |
|-------|-----------------|
| META_UPDATER | RAG tools for pattern detection |
| CODE_REVIEWER | validation tools (read-only) |
| QA_TESTER | validation + conflict detection |
| OPTIMIZATION_SPECIALIST | optimization + equity + capability tools |
| CAPACITY_OPTIMIZER | erlang + utilization + equity tools |

### LOW/None Priority

| Agent | Reason |
|-------|--------|
| UX_SPECIALIST | No MCP needed (external accessibility tools) |
| CRASH_RECOVERY_SPECIALIST | No MCP (filesystem only) |
| HISTORIAN | RAG ingest only (archival) |

## MCP Tool Categories

| Category | Tool Count | Primary Users |
|----------|------------|---------------|
| **RAG Tools** | 4 | G4_CONTEXT_MANAGER, KNOWLEDGE_CURATOR, G2_RECON |
| **Scheduling Tools** | 10+ | SCHEDULER, SWAP_MANAGER, COORD_ENGINE |
| **Compliance Tools** | 8+ | COMPLIANCE_AUDITOR, MEDCOM |
| **Resilience Tools** | 15+ | RESILIENCE_ENGINEER, BURNOUT_SENTINEL |
| **Optimization Tools** | 8+ | OPTIMIZATION_SPECIALIST, CAPACITY_OPTIMIZER |

## Access Patterns

### Read-Only Pattern
Agents that need data but don't modify state:
- CODE_REVIEWER: validate_schedule (verification only)
- QA_TESTER: validate_schedule, detect_conflicts (testing)
- MEDCOM: burnout metrics, compliance data (advisory)

### Read-Write Pattern
Agents that query AND modify:
- SCHEDULER: generate + validate + execute
- SWAP_MANAGER: analyze + validate + execute
- G4_CONTEXT_MANAGER: search + ingest
- KNOWLEDGE_CURATOR: search + ingest

---

*Ingested to `.claude/dontreadme/` as fallback. Queue for pgvector ingestion when MCP server available.*
