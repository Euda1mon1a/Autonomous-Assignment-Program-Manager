# RAG Knowledge Base

This directory contains markdown documents that are embedded into the pgvector database for semantic search and RAG (Retrieval-Augmented Generation) capabilities.

## Documents

| Document | Type | Description | Status |
|----------|------|-------------|--------|
| `acgme-rules.md` | `acgme_rules` | ACGME compliance rules and regulations | Embedded |
| `scheduling-policies.md` | `scheduling_policy` | Scheduling policies and procedures | Embedded |
| `swap-system.md` | `swap_system` | Swap management system documentation | Embedded |
| `military-specific.md` | `military_specific` | Military medical residency specifics | Embedded |
| `resilience-concepts.md` | `resilience_concepts` | Tier 1-3 resilience framework concepts | Embedded |
| `user-guide-faq.md` | `user_guide_faq` | User guide and FAQ | Embedded |
| `session-learnings.md` | `session_learnings` | Session learnings and patterns | Embedded |
| `session-protocols.md` | `session_protocols` | Session protocols and workflows | Embedded |
| `delegation-patterns.md` | `delegation_patterns` | Multi-agent delegation patterns | Embedded |
| `exotic-concepts.md` | `exotic_concepts` | Tier 5 exotic frontier concepts (NEW) | **Needs Embedding** |

## Embedding Documents

### Method 1: Using the initialization script (Recommended)

From the project root:

```bash
# Embed all documents
python scripts/init_rag_embeddings.py

# Embed a specific document
python scripts/init_rag_embeddings.py --doc exotic-concepts.md

# Preview chunks without storing
python scripts/init_rag_embeddings.py --dry-run

# Clear and re-embed all
python scripts/init_rag_embeddings.py --clear-all
```

### Method 2: Using Celery task

From the backend directory:

```python
from app.tasks.rag_tasks import refresh_single_document

# Trigger embedding task
result = refresh_single_document.delay("exotic-concepts.md")
```

### Method 3: Using the RAG API endpoint

```bash
# Assuming backend is running on localhost:8000
curl -X POST http://localhost:8000/api/v1/rag/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "content": "<file content>",
    "doc_type": "exotic_concepts",
    "metadata": {"filename": "exotic-concepts.md"}
  }'
```

## Recent Changes

**2025-12-30:**
- Added `exotic-concepts.md` documenting 10 Tier 5 exotic frontier concepts:
  - Metastability Detection (statistical mechanics)
  - Spin Glass Model (condensed matter physics)
  - Circadian PRC (chronobiology)
  - Penrose Process (astrophysics)
  - Anderson Localization (quantum physics)
  - Persistent Homology (topology)
  - Free Energy Principle (neuroscience)
  - Keystone Species Analysis (ecology)
  - Quantum Zeno Effect (quantum mechanics)
  - Catastrophe Theory (mathematics)
- Updated `DOC_TYPE_MAP` in `scripts/init_rag_embeddings.py` and `backend/app/tasks/rag_tasks.py`
- **ACTION REQUIRED:** Run `python scripts/init_rag_embeddings.py --doc exotic-concepts.md` to embed the new document

## Verification

Check RAG system health:

```bash
# Using script
python scripts/init_rag_embeddings.py --dry-run

# Using Python
python -c "
from app.db.session import SessionLocal
from app.services.rag_service import RAGService
import asyncio

async def check():
    db = SessionLocal()
    rag = RAGService(db)
    health = await rag.get_health()
    print(f'Total documents: {health.total_documents}')
    print(f'By type: {health.documents_by_type}')
    db.close()

asyncio.run(check())
"
```

## Troubleshooting

**Issue:** `ImportError: cannot import name 'NotRequired' from 'typing'`
- **Cause:** System Python is too old (needs Python 3.11+)
- **Solution:** Use Docker container: `docker-compose exec backend python scripts/init_rag_embeddings.py`

**Issue:** `FileNotFoundError` in Docker container
- **Cause:** `docs/` directory not mounted in container
- **Solution:** Copy script to mounted volume or use host Python with backend virtualenv

**Issue:** Document not appearing in search results
- **Cause:** Document not embedded or embedding failed
- **Solution:** Check logs, verify database connection, re-run embedding script
