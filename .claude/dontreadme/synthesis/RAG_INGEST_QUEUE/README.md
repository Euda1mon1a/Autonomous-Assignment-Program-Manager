# RAG Ingest Queue

This directory contains documents prepared for ingestion into the RAG knowledge base.

## Purpose

When the MCP server's `rag_ingest` tool is available, documents in this directory should be ingested with their specified metadata.

## Document Format

Each document should include YAML frontmatter:

```yaml
**doc_type:** ai_patterns | ai_decisions | session_handoff | scheduling_policy | acgme_rules
**priority:** high | medium | low
**discovery_date:** YYYY-MM-DD
**session:** session identifier
**tags:** comma, separated, tags
```

## Ingestion Command

When MCP server is running:

```python
# Via MCP tool
await rag_ingest(
    content=file_content,
    doc_type="ai_patterns",  # from frontmatter
    metadata={
        "priority": "high",
        "discovery_date": "2026-01-01",
        "session": "mcp-refinement",
        "tags": ["parallelization", "multi-agent"]
    }
)
```

## Queue Status

| File | doc_type | Priority | Ingested |
|------|----------|----------|----------|
| ai_pattern_embarrassingly_parallel.md | ai_patterns | high | **INGESTED** (2026-01-01) |

### Ingestion Log

**2026-01-01 (G4_CONTEXT_MANAGER - mcp-refinement session):**
- Updated `docs/rag-knowledge/session-learnings.md` with:
  - The 99/1 Rule (Cardinal Rule)
  - Embarrassingly Parallel Pattern
  - Special Operators Model
  - Always ORCHESTRATOR Mode
- Updated `docs/rag-knowledge/delegation-patterns.md` with:
  - 99/1 Rule section (top of document)
  - Embarrassingly Parallel Pattern section
- Note: Content moved to canonical RAG knowledge files rather than kept as separate queue document
- To re-embed, run: `python scripts/init_rag_embeddings.py`

## Automated Ingestion

To ingest all pending documents, run:

```bash
# From project root, with MCP server running
docker-compose exec mcp-server python -c "
from scheduler_mcp.server import rag_ingest
import asyncio
# ingestion script here
"
```
