# RAG Ingestion Patterns

> **Session:** 087 | **Date:** 2026-01-10 | **Status:** Lesson Learned

---

## TL;DR: Use MCP, Not Docker Exec

**Wrong approach (Session 087 mistake):**
```bash
# Manually piping content to Docker container
docker exec scheduler-local-backend bash -c "python -c '...'"
```

**Right approach:**
```
mcp__residency-scheduler__rag_ingest(
  content="...",
  doc_type="technical_doc",
  metadata={"source": "filename.md"}
)
```

---

## Why This Matters

1. **MCP handles auth** - No need to manually authenticate with the API
2. **MCP handles connection** - Routes to the right backend automatically
3. **Faster** - Single tool call vs multi-step Docker exec
4. **Cleaner** - No base64 encoding, no shell escaping

---

## Docker Volume Gotcha

The `docs/` folder is **NOT** mounted in the backend container:

```
Mounted:
  /Users/.../backend → /app
  /Users/.../scripts → /scripts

NOT Mounted:
  /Users/.../docs → (nowhere)
```

If you must use Docker exec, you'll need to pipe content via base64 or add a volume mount.

---

## Available MCP RAG Tools

| Tool | Purpose |
|------|---------|
| `rag_ingest` | Add documents to knowledge base |
| `rag_search` | Semantic search (query, top_k, doc_type) |
| `rag_context` | Get relevant context for LLM injection |
| `rag_health` | Check RAG system status |

---

## Valid doc_types

```
acgme_rules, scheduling_policy, user_guide, technical_doc,
meeting_notes, research_paper, clinical_guideline, swap_system,
military_specific, resilience_concepts, user_guide_faq,
session_handoff, ai_patterns, ai_decisions, delegation_patterns,
exotic_concepts, agent_spec, other
```

---

## Example: Correct RAG Ingestion

```python
# Read file content
content = open("docs/rag-knowledge/my-doc.md").read()

# Use MCP tool
result = mcp__residency-scheduler__rag_ingest(
    content=content,
    doc_type="technical_doc",
    metadata={
        "source": "my-doc.md",
        "session": "087"
    }
)
# Returns: {"status": "success", "chunks_created": 4, ...}
```

---

*Documented after Session 087 fumbled with Docker exec instead of using MCP.*
