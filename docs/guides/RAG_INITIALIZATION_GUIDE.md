# RAG Initialization Guide

This guide explains how to initialize and manage the RAG (Retrieval-Augmented Generation) vector embeddings for the knowledge base.

## Overview

The RAG system provides semantic search capabilities over domain knowledge documents stored in `docs/rag-knowledge/`. These documents are chunked, embedded using sentence-transformers, and stored in PostgreSQL with pgvector for efficient similarity search.

## Knowledge Base Documents

The following documents are embedded by default:

| Document | Doc Type | Description |
|----------|----------|-------------|
| `acgme-rules.md` | `acgme_rules` | ACGME duty hour requirements and compliance rules |
| `scheduling-policies.md` | `scheduling_policy` | Internal scheduling policies and procedures |
| `swap-system.md` | `swap_system` | Schedule swap workflow and validation rules |
| `military-specific.md` | `military_specific` | Military medical residency requirements |
| `resilience-concepts.md` | `resilience_concepts` | Cross-disciplinary resilience framework concepts |
| `user-guide-faq.md` | `user_guide_faq` | Frequently asked questions and troubleshooting |

## Method 1: CLI Script (Recommended for Initial Setup)

### Prerequisites

```bash
# Ensure backend dependencies are installed
cd backend
pip install -r requirements.txt

# Ensure PostgreSQL with pgvector extension is running
docker-compose up -d db

# Run migrations to create rag_documents table
alembic upgrade head
```

### Basic Usage

```bash
# Embed all documents in knowledge base
python scripts/init_rag_embeddings.py

# Embed a specific document
python scripts/init_rag_embeddings.py --doc acgme-rules.md

# Preview chunks without storing (dry run)
python scripts/init_rag_embeddings.py --dry-run

# Clear all existing embeddings
python scripts/init_rag_embeddings.py --clear-all

# Custom chunk size and overlap
python scripts/init_rag_embeddings.py --chunk-size 1000 --chunk-overlap 100
```

### CLI Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--doc` | string | None | Process only a specific document (e.g., `acgme-rules.md`) |
| `--clear-all` | flag | False | Clear all existing RAG documents before processing |
| `--dry-run` | flag | False | Preview chunks without storing in database |
| `--chunk-size` | int | 500 | Target chunk size in tokens |
| `--chunk-overlap` | int | 50 | Overlap between chunks in tokens |

### Example Output

```
RAG Embeddings Initialization Script
============================================================
  ✓ Database connection validated
  - Embedding model: all-MiniLM-L6-v2
  - Embedding dimensions: 384
  - Vector index status: ready
  - Existing documents: 0

============================================================
Found 6 document(s) to process
============================================================

============================================================
Processing: acgme-rules.md
Doc Type: acgme_rules
============================================================
  • File size: 45,231 characters
  ✓ Created 87 chunks
  ✓ Average chunk size: ~520 chars

...

============================================================
SUMMARY
============================================================
  ✓ Successful: 6/6
  ✗ Errors: 0/6
  • Total chunks created: 412
============================================================

✓ All documents processed successfully
```

## Method 2: Celery Tasks (Recommended for Production)

### Prerequisites

```bash
# Ensure Celery and Redis are running
../scripts/start-celery.sh both
```

### Available Tasks

#### 1. Initialize All Embeddings

```python
from app.tasks import initialize_embeddings

# Queue the task
task = initialize_embeddings.delay()

# Check status
result = task.get(timeout=300)
print(result)
# {
#   "timestamp": "2025-12-29T12:00:00",
#   "status": "completed",
#   "documents_processed": 6,
#   "documents_successful": 6,
#   "total_chunks": 412,
#   "results": [...]
# }
```

#### 2. Refresh Single Document

```python
from app.tasks import refresh_single_document

# Refresh just the ACGME rules
task = refresh_single_document.delay("acgme-rules.md")
result = task.get(timeout=60)
```

#### 3. Check RAG Health

```python
from app.tasks import check_rag_health

task = check_rag_health.delay()
result = task.get(timeout=30)
print(result)
# {
#   "status": "healthy",
#   "total_documents": 412,
#   "documents_by_type": {
#     "acgme_rules": 87,
#     "scheduling_policy": 65,
#     ...
#   },
#   "recommendations": []
# }
```

#### 4. Periodic Refresh (Scheduled)

```python
from app.tasks import periodic_refresh

# This is typically called by Celery Beat on a schedule
# But can be triggered manually:
task = periodic_refresh.delay()
```

#### 5. Clear All Embeddings

```python
from app.tasks import clear_all_embeddings

task = clear_all_embeddings.delay()
result = task.get(timeout=30)
print(result)
# {
#   "timestamp": "2025-12-29T12:00:00",
#   "status": "completed",
#   "total_deleted": 412
# }
```

### Scheduling with Celery Beat

To automatically refresh embeddings periodically, add to `backend/app/core/celery_app.py`:

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    # ... other schedules ...

    "refresh-rag-embeddings-weekly": {
        "task": "app.tasks.rag_tasks.periodic_refresh",
        "schedule": crontab(day_of_week=1, hour=2, minute=0),  # Monday 2 AM
    },

    "check-rag-health-daily": {
        "task": "app.tasks.rag_tasks.check_rag_health",
        "schedule": crontab(hour=6, minute=0),  # Daily at 6 AM
    },
}
```

## Method 3: Python API (Programmatic Access)

```python
from app.db.session import SessionLocal
from app.services.rag_service import RAGService
from pathlib import Path

# Create database session
db = SessionLocal()
rag_service = RAGService(db)

try:
    # Read a document
    doc_path = Path("docs/rag-knowledge/acgme-rules.md")
    content = doc_path.read_text()

    # Ingest document
    result = await rag_service.ingest_document(
        content=content,
        doc_type="acgme_rules",
        metadata={"filename": "acgme-rules.md"},
        chunk_size=500,
        chunk_overlap=50
    )

    print(f"Created {result.chunks_created} chunks")

finally:
    db.close()
```

## Troubleshooting

### Issue: "pgvector extension not found"

**Solution:**
```bash
# Connect to database
docker-compose exec db psql -U scheduler -d residency_scheduler

# Enable extension
CREATE EXTENSION IF NOT EXISTS vector;
```

### Issue: "No documents found"

**Solution:**
Ensure documents exist in `docs/rag-knowledge/`:
```bash
ls -la docs/rag-knowledge/*.md
```

### Issue: "Insufficient samples" or empty results

**Solution:**
The documents may be too small. Check minimum chunk size:
- Default minimum chunk size: 10% of `chunk_size`
- For 500 token chunks, minimum is ~200 characters

### Issue: Task timeout

**Solution:**
Increase timeout for large knowledge bases:
```python
task = initialize_embeddings.delay()
result = task.get(timeout=600)  # 10 minutes
```

### Issue: Memory errors during embedding

**Solution:**
Reduce batch size in embedding service or process documents individually:
```bash
# Process one at a time
for doc in acgme-rules.md scheduling-policies.md swap-system.md; do
    python scripts/init_rag_embeddings.py --doc $doc
done
```

## Verification

### Check embeddings were created

```bash
# Via CLI script
python scripts/init_rag_embeddings.py --dry-run

# Via psql
docker-compose exec db psql -U scheduler -d residency_scheduler \
  -c "SELECT doc_type, COUNT(*) FROM rag_documents GROUP BY doc_type;"
```

Expected output:
```
      doc_type       | count
---------------------+-------
 acgme_rules         |    87
 scheduling_policy   |    65
 swap_system         |    42
 military_specific   |    38
 resilience_concepts |   105
 user_guide_faq      |    75
(6 rows)
```

### Test semantic search

```python
from app.db.session import SessionLocal
from app.services.rag_service import RAGService

db = SessionLocal()
rag_service = RAGService(db)

try:
    # Search for ACGME rules
    result = await rag_service.retrieve(
        query="What are the maximum work hours per week?",
        top_k=3,
        doc_type="acgme_rules"
    )

    for doc in result.documents:
        print(f"Score: {doc.similarity_score:.3f}")
        print(f"Content: {doc.content[:200]}...")
        print()

finally:
    db.close()
```

## Performance Considerations

### Chunk Size Selection

| Chunk Size | Use Case | Pros | Cons |
|------------|----------|------|------|
| 200-300 tokens | Precise retrieval | Granular matching | More chunks, slower indexing |
| 500-700 tokens (default) | Balanced | Good context + speed | Standard |
| 1000-1500 tokens | Long context | Fewer chunks | May lose precision |

### Embedding Model

Current model: `all-MiniLM-L6-v2`
- Dimensions: 384
- Speed: ~500 sentences/sec (CPU)
- Quality: Good for general domain

To change model, update `backend/app/services/embedding_service.py`.

### Database Indexes

Ensure vector indexes exist for optimal performance:
```sql
-- Check indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'rag_documents';

-- Create index if missing (should be in migrations)
CREATE INDEX IF NOT EXISTS idx_rag_documents_embedding_cosine
ON rag_documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

## Integration with MCP Server

The MCP server can use these embeddings for AI-assisted scheduling:

```python
# In MCP tool
from app.services.rag_service import RAGService

async def answer_scheduling_question(question: str):
    """Answer a question using RAG context."""
    rag_service = RAGService(db)

    # Build context from knowledge base
    context = await rag_service.build_context(
        query=question,
        max_tokens=2000,
        include_metadata=True
    )

    # Use context in LLM prompt
    prompt = f"""
    Context from knowledge base:
    {context.context}

    Question: {question}

    Answer based on the context provided.
    """

    # Send to LLM...
```

## Maintenance

### When to re-index

Re-run initialization when:
- Knowledge base documents are updated
- Chunk size strategy changes
- Embedding model is upgraded
- Database is migrated

### Monitoring

Track these metrics:
- Total chunks per doc_type
- Average chunk size
- Retrieval latency (via logs)
- Search result relevance scores

### Backup

RAG embeddings can be regenerated from source documents, but for faster recovery:

```bash
# Backup rag_documents table
docker-compose exec db pg_dump -U scheduler -d residency_scheduler \
  -t rag_documents --data-only > rag_backup.sql

# Restore
docker-compose exec -T db psql -U scheduler -d residency_scheduler < rag_backup.sql
```

## Next Steps

1. Initialize embeddings: `python scripts/init_rag_embeddings.py`
2. Verify with health check: `python -c "from app.tasks import check_rag_health; check_rag_health.delay().get()"`
3. Test retrieval via API: `curl http://localhost:8000/api/v1/rag/retrieve -d '{"query":"80 hour rule"}'`
4. Integrate with MCP tools for AI-assisted scheduling

## Related Documentation

- [RAG Service Architecture](../architecture/rag-architecture.md)
- [MCP Integration Guide](../guides/AI_AGENT_USER_GUIDE.md)
- [Database Schema](../database/SCHEMA.md)
- [API Reference](../api/rag-endpoints.md)
