# MCP Priority List

> **Created:** 2026-01-28
> **Scope:** MCP Apps integration + Internal MCP server enhancements
> **Safe Zone:** All MCP work is isolated from backend (no Phase 3 conflicts)

---

## Priority Summary

| Priority | Category | Item | Effort | Value |
|----------|----------|------|--------|-------|
| **P0** | Internal | Wire ACGME block_quality to real validator | Low | High |
| **P1** | RAG | Diagram bundle auto-generation | Low | Medium |
| **P1** | Internal | Fix tool 500 errors (swap_candidates, conflicts) | Medium | High |
| **P2** | RAG | Graph RAG entity extraction | High | High |
| **P2** | External | Add Perplexity MCP for deep research | Low | Medium |
| **P3** | MCP Apps | Schedule visualization dashboard | High | High |
| **P3** | MCP Apps | Swap request approval UI | Medium | Medium |
| **P4** | External | Add Brave Search MCP | Low | Low |

---

## P0: Critical (Do First)

### Wire ACGME Block Quality to Real Validator

**Status:** Phase 3 scope (backend dependency)
**Location:** `backend/app/services/block_quality_report_service.py`
**Issue:** ACGME compliance is hardcoded to 100% (stub)

```python
# Current (stub)
"acgme_compliance_rate": 100.0  # PLACEHOLDER

# Target
"acgme_compliance_rate": await validator.calculate_compliance_rate()
```

**Note:** This touches backend - defer until Phase 3 merges.

---

## P1: High Priority

### 1.1 Diagram Bundle Auto-Generation

**Status:** Ready to implement
**Location:** `mcp-server/` + `docs/rag-knowledge/`
**Source:** PR #774 (merged)

**Tasks:**
- [ ] Create `scripts/generate-diagram-bundle.sh`
- [ ] Auto-extract mermaid blocks from `docs/architecture/*.md`
- [ ] Output to `docs/rag-knowledge/DIAGRAM_BUNDLE.md`
- [ ] Add to RAG ingestion with `doc_type=architecture_diagrams`
- [ ] Add pre-commit hook to regenerate on diagram changes

**Files:**
```
scripts/generate-diagram-bundle.sh (NEW)
docs/rag-knowledge/DIAGRAM_BUNDLE.md (exists from PR #774)
mcp-server/src/scheduler_mcp/tools/rag.py (update ingestion)
```

### 1.2 Fix MCP Tool 500 Errors

**Status:** Known issues from earlier session
**Tools affected:**
- `analyze_swap_candidates_tool` - 500 error
- `detect_conflicts_tool` - Intermittent issues

**Investigation needed:**
- Check API endpoint connectivity
- Verify auth token refresh
- Test with MCP_ALLOW_LOCAL_DEV=true

**Files:**
```
mcp-server/src/scheduler_mcp/tools/swap/
mcp-server/src/scheduler_mcp/tools/compliance/
```

---

## P2: Medium Priority

### 2.1 Graph RAG Entity Extraction

**Status:** Roadmap from PR #774
**Location:** `mcp-server/src/scheduler_mcp/`

**Tasks:**
- [ ] Create `DiagramService` class for mermaid parsing
- [ ] Extract nodes and edges from flowcharts
- [ ] Store entities in `diagram_entities` table
- [ ] Store relations in `diagram_relations` table
- [ ] Add `rag_graph_search` MCP tool

**Schema (from PR #774):**
```sql
CREATE TABLE diagram_entities (
    id UUID PRIMARY KEY,
    entity_name VARCHAR(255),
    entity_type VARCHAR(50),
    diagram_source VARCHAR(255),
    embedding vector(384)
);

CREATE TABLE diagram_relations (
    source_entity_id UUID REFERENCES diagram_entities(id),
    target_entity_id UUID REFERENCES diagram_entities(id),
    relation_type VARCHAR(50),
    relation_label VARCHAR(255)
);
```

### 2.2 Add Perplexity MCP Server

**Status:** Research complete (PR #775)
**Value:** Deep research capability for ACGME rules, medical policies

**Config:**
```json
{
  "mcpServers": {
    "perplexity": {
      "command": "npx",
      "args": ["-y", "@perplexity-ai/mcp-server"],
      "env": {
        "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}",
        "STRIP_THINKING": "true"
      }
    }
  }
}
```

**Requires:** API key setup (human action)

---

## P3: Nice to Have

### 3.1 MCP Apps: Schedule Visualization Dashboard

**Status:** Conceptual (MCP Apps just launched Jan 2026)
**Value:** Interactive schedule view in Claude conversation

**Features:**
- Block calendar view
- Coverage heatmap
- Conflict highlighting
- Click-to-drill into assignments

**Tech:**
- Use `@mcp-ui/client` for React components
- Return from MCP tool as interactive UI
- Leverage Three.js for 3D views (optional)

### 3.2 MCP Apps: Swap Request Approval UI

**Status:** Conceptual
**Value:** Approve/reject swaps without leaving conversation

**Features:**
- Swap request card with before/after view
- Approve/Reject buttons
- Impact summary (compliance, coverage)
- Audit trail

---

## P4: Low Priority / Future

### 4.1 Add Brave Search MCP

**Status:** Research complete
**Value:** General web search (privacy-focused)
**Effort:** Low (npm install + config)

### 4.2 Add GitHub MCP Server

**Status:** Research complete
**Value:** PR management, issue tracking from conversation
**Note:** Already have `gh` CLI via Bash

---

## Current MCP Tool Inventory

### Core Tools (34+)
| Category | Tools |
|----------|-------|
| **Validation** | validate_schedule, validate_by_id, detect_conflicts |
| **Scheduling** | contingency_analysis, swap_candidates |
| **Resilience** | circuit_breakers, defense_level, blast_radius |
| **RAG** | rag_search, rag_context, rag_health, rag_ingest |
| **Exotic** | game_theory, ecological_dynamics, fourier_analysis, kalman_filter |

### Tool Directories
```
mcp-server/src/scheduler_mcp/tools/
├── analytics/       # Metrics, reporting
├── compliance/      # ACGME, MTF
├── resilience/      # N-1/N-2, circuit breakers
├── schedule/        # Generation, validation
├── swap/            # Swap management
└── *.py             # Core + exotic tools
```

---

## External MCP Servers (Not Yet Configured)

| Server | Status | Value |
|--------|--------|-------|
| Perplexity | Researched | Deep research |
| Brave Search | Researched | Web search |
| Tavily | Researched | Citation-heavy research |
| PostgreSQL | Have internally | Direct DB access |
| Redis | Have internally | Cache inspection |
| GitHub | Researched | PR/issue management |

---

## Dependencies & Blockers

| Item | Blocker | Resolution |
|------|---------|------------|
| ACGME block_quality | Phase 3 backend | Wait for merge |
| Perplexity MCP | API key | Human action |
| MCP Apps | SDK maturity | Monitor releases |
| Graph RAG | DB migration | Create tables |

---

## Quick Wins (Can Do Now)

1. **Diagram bundle script** - 30 min
2. **Perplexity config** (if API key exists) - 10 min
3. **Investigate tool 500 errors** - 1 hr
4. **Add `doc_type=architecture_diagrams`** - 15 min

---

*This list is safe to work on while Phase 3 is in review - no backend conflicts.*
