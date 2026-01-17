# RAG Quick Reference

> **Scan Time:** <1 minute | **Purpose:** Daily RAG operations cheat sheet

---

## MCP Tools (Primary Method)

| Tool | Purpose | Example |
|------|---------|---------|
| `rag_search` | Semantic search | `rag_search(query="80 hour rule", top_k=5)` |
| `rag_ingest` | Add documents | `rag_ingest(content, doc_type, metadata)` |
| `rag_context` | LLM context | `rag_context(query, max_tokens=2000)` |
| `rag_health` | System check | `rag_health()` |

---

## Common Queries by Domain

| Need | Query |
|------|-------|
| ACGME rules | `rag_search(query="work hour limits", doc_type="acgme_rules")` |
| Delegation patterns | `rag_search(query="Auftragstaktik", doc_type="delegation_patterns")` |
| Agent specs | `rag_search(query="ORCHESTRATOR charter", doc_type="agent_spec")` |
| Resilience | `rag_search(query="N-1 failure", doc_type="resilience_concepts")` |
| Exotic concepts | `rag_search(query="time crystal", doc_type="exotic_concepts")` |

---

## Health Check One-Liners

**MCP (AI Agents):**
```python
mcp__residency-scheduler__rag_health()
```

**CLI (Manual):**
```bash
python scripts/init_rag_embeddings.py --dry-run
```

**Python API:**
```python
from app.tasks import check_rag_health
check_rag_health.delay().get(timeout=30)
```

**Database Direct:**
```bash
docker-compose exec db psql -U scheduler -d residency_scheduler \
  -c "SELECT doc_type, COUNT(*) FROM rag_documents GROUP BY doc_type;"
```

---

## Decision Tree: When to Use Each Method

```
Need to ingest?
├── AI Agent session → MCP rag_ingest
├── Bulk initial setup → CLI script
└── Production automation → Celery tasks

Need to search?
├── AI Agent session → MCP rag_search / rag_context
├── API endpoint → RAGService.retrieve()
└── Direct SQL → pgvector cosine similarity
```

---

## Valid doc_types

| Type | Use For |
|------|---------|
| `acgme_rules` | ACGME regulations, duty hour rules |
| `scheduling_policy` | Internal scheduling procedures |
| `swap_system` | Swap workflow, validation rules |
| `military_specific` | Military medical requirements |
| `resilience_concepts` | Cross-disciplinary resilience patterns |
| `user_guide_faq` | FAQ, user help content |
| `exotic_concepts` | Physics/biology cross-domain patterns |
| `research_paper` | Academic sources, citations |
| `agent_spec` | PAI agent identities, charters |
| `delegation_patterns` | Auftragstaktik, command philosophy |
| `technical_doc` | Implementation patterns, architecture |
| `session_handoff` | Session continuity notes |
| `ai_patterns` | AI behavioral patterns |
| `ai_decisions` | Architectural decisions |

---

## Quick Troubleshooting

| Symptom | Fix |
|---------|-----|
| Empty results | Try without `doc_type` filter |
| Irrelevant results | Rephrase using domain terminology |
| "Connection refused" | `docker ps \| grep mcp` → restart if needed |
| Stale results | Re-ingest: `rag_ingest(content, doc_type, metadata)` |
| MCP timeout | Check backend logs: `docker logs scheduler-local-backend` |

---

## Ingestion Template

```python
# Standard ingestion pattern
mcp__residency-scheduler__rag_ingest(
    content=open("docs/rag-knowledge/my-doc.md").read(),
    doc_type="technical_doc",
    metadata={
        "source": "my-doc.md",
        "session": "current_session_id",
        "date": "2026-01-16"
    }
)
```

---

## Related Docs

- Full guide: `docs/guides/RAG_INITIALIZATION_GUIDE.md`
- Best practices: `docs/rag-knowledge/rag-ingestion-patterns.md`
- Content policy: `docs/rag-knowledge/README.md`
- Lifecycle: `docs/rag-knowledge/RAG_CONTENT_LIFECYCLE.md`

---

*Quick reference v1.0 | Created 2026-01-16*
