# pgvector Container Decision

> **Created:** 2025-12-29
> **Status:** Implemented
> **Decision:** Use `pgvector/pgvector:pg15` container image

---

## Decision Summary

Use the pre-built `pgvector/pgvector:pg15` Docker image instead of building a custom Postgres image with pgvector extension.

---

## Context

The RAG (Retrieval-Augmented Generation) service requires vector similarity search for:
- Cross-session memory retrieval
- Context-aware agent prompting
- Semantic search over documentation and history

pgvector is the leading Postgres extension for vector operations, providing:
- HNSW and IVFFlat indexing
- Cosine, L2, and inner product distance functions
- Native Postgres integration

---

## Options Considered

### Option 1: Official Postgres + Custom Dockerfile (Rejected)

```dockerfile
FROM postgres:15
RUN apt-get update && apt-get install -y postgresql-15-pgvector
```

**Pros:**
- Uses official postgres base image

**Cons:**
- Requires maintaining custom Dockerfile
- Build step adds complexity to CI/CD
- Extension version management burden
- Compilation flags may not be optimal

### Option 2: pgvector/pgvector Container (Selected)

```yaml
db:
  image: pgvector/pgvector:0.8.1-pg15
```

**Pros:**
- Maintained by pgvector team
- Drop-in replacement for postgres
- Optimized compilation flags
- No build step required
- Version pinned for reproducibility

**Cons:**
- Third-party image dependency (mitigated: widely used, open source)

---

## Implementation

### docker-compose.yml

```yaml
services:
  db:
    image: pgvector/pgvector:0.8.1-pg15  # Includes pgvector extension for embeddings
    container_name: residency-scheduler-db
    # ... rest of config unchanged
```

### Extension Activation

The extension must be enabled in the database:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

This is handled by the Alembic migration: `20251229_add_rag_documents_table.py`

### Version Strategy

- Pin to specific version (e.g., `0.8.1-pg15`) for reproducibility
- Update quarterly or when security patches released
- Test in dev before production upgrade

---

## Verification

```bash
# Check extension is available
docker compose exec db psql -U scheduler -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';"

# Check extension is enabled
docker compose exec db psql -U scheduler -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Test vector operations
docker compose exec db psql -U scheduler -c "SELECT '[1,2,3]'::vector <-> '[4,5,6]'::vector AS distance;"
```

---

## Components Enabled

| Component | Status | Purpose |
|-----------|--------|---------|
| G4_CONTEXT_MANAGER | Unblocked | Cross-session memory agent |
| RAG Service | Unblocked | Semantic document retrieval |
| rag_documents table | Unblocked | Embedding storage |
| init_rag_embeddings.py | Unblocked | Knowledge base initialization |

---

## Related Files

- `docker-compose.yml` - Container configuration
- `backend/app/models/rag_document.py` - Vector column model
- `backend/app/services/rag_service.py` - RAG operations
- `backend/alembic/versions/20251229_add_rag_documents_table.py` - Migration
- `docs/guides/RAG_INITIALIZATION_GUIDE.md` - Setup guide

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-29 | Initial decision documentation |

---

*Decision made during Session 016 PAI Organizational Expansion.*
