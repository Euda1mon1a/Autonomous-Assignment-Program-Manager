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
| ai_pattern_embarrassingly_parallel.md | ai_patterns | high | pending |

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
