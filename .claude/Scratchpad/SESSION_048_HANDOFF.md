# Session 048 Handoff: RAG Schema Fix & Knowledge Base Population

> **Date:** 2026-01-03
> **Branch:** `fix/rag-schema-and-ingestion-20260103` (from `explore/subagents-rag-20260102`)
> **Status:** RAG FULLY LOADED - Ready for next phase

---

## Summary

Fixed RAG ingestion 422 errors by expanding the Pydantic doc_type validator, then successfully populated the RAG knowledge base with 31 chunks across 9 document types.

---

## Problem Solved

### Root Cause: Schema Validation Failure

The `DocumentIngestRequest` schema in `backend/app/schemas/rag.py` only allowed 8 doc_types:
- `acgme_rules`, `scheduling_policy`, `user_guide`, `technical_doc`, `meeting_notes`, `research_paper`, `clinical_guideline`, `other`

Attempting to ingest with types like `swap_system`, `military_specific`, `exotic_concepts` returned **422 Unprocessable Entity**.

### Fix Applied

Added 10 new doc_types to the validator:
```python
# RAG knowledge base categories (from docs/rag-knowledge/)
"swap_system",
"military_specific",
"resilience_concepts",
"user_guide_faq",
"session_handoff",
"ai_patterns",
"ai_decisions",
"delegation_patterns",
"exotic_concepts",
"agent_spec",
```

**File:** `backend/app/schemas/rag.py` (lines 50-71)

---

## RAG Knowledge Base Status

**Total Chunks:** 31
**Vector Index:** Ready
**Embedding Model:** all-MiniLM-L6-v2 (384 dimensions)

| Document Type | Chunks | Source File |
|---------------|--------|-------------|
| `acgme_rules` | 7 | acgme-rules.md |
| `scheduling_policy` | 9 | scheduling-policies.md |
| `swap_system` | 2 | swap-system.md |
| `military_specific` | 2 | military-specific.md |
| `resilience_concepts` | 3 | resilience-concepts.md |
| `user_guide_faq` | 2 | user-guide-faq.md |
| `ai_patterns` | 2 | session-learnings.md |
| `delegation_patterns` | 2 | delegation-patterns.md |
| `exotic_concepts` | 2 | exotic-concepts.md |

---

## Design Decision: Condensed vs Full Content

**Decision:** Keep 31 condensed chunks (not expand to ~185 full chunks)

**Rationale:**
- RAG is for **quick semantic lookup of concepts**, not replacing documentation
- Agents can `Read` source files when full detail needed
- Less noise = higher signal-to-noise in search results
- "Missing" content is mostly procedural UI instructions and code examples (redundant with codebase)

---

## Key Learnings

### MCP Token Caching Issue
The MCP client singleton caches JWT token from container startup. When token expires:
- 401 Unauthorized errors
- **Fix:** `docker compose restart mcp-server`
- **Permanent fix needed:** Token refresh on 401 (documented in HUMAN_TODO.md)

### Container Rebuild Required for Schema Changes
Just restarting backend doesn't pick up Python code changes in Docker:
- **Wrong:** `docker compose restart backend`
- **Right:** `docker compose up -d --build backend`

---

## Verified Working

```bash
# RAG health check
mcp__residency-scheduler__rag_health
# Returns: 31 documents, healthy, ready

# RAG search test
mcp__residency-scheduler__rag_search "What are the ACGME work hour limits?"
# Returns: Relevant chunks with similarity scores 0.66-0.71
```

---

## Next Steps (For Future Session)

1. **Merge schema fix to main** if not already committed upstream
2. **Consider adding:** session_handoff doc_type for session handoff notes
3. **Monitor:** If search results feel thin on specific topics, selectively add detail
4. **Permanent fix:** MCP token refresh on 401 (avoid container restart dance)

---

## Git State

```
Branch: fix/rag-schema-and-ingestion-20260103
Parent: explore/subagents-rag-20260102
Status: Clean working tree
```

Schema changes may already be committed in parent branch (check `git log` for commit containing "rag" schema updates).

---

*Handoff prepared for autocompact context transition.*
