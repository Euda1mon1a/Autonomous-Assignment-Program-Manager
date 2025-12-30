# RAG (Retrieval-Augmented Generation) Service

## Overview

The RAG service provides semantic search and document retrieval capabilities for the Residency Scheduler application. It enables the system to store, index, and retrieve relevant documentation using vector embeddings and similarity search.

**Key Features:**
- 🔍 **Semantic Search**: Find documents by meaning, not just keywords
- 📄 **Smart Chunking**: Automatically split long documents with overlap
- ⚡ **Fast Retrieval**: pgvector HNSW indexes for efficient similarity search
- 🤖 **LLM Integration**: Build context strings for AI model injection
- 📊 **Multi-Document Types**: Support for ACGME rules, policies, guides, etc.

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                      RAG Service                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Document Ingestion                                       │
│     ├─ Text chunking (configurable size/overlap)            │
│     ├─ Embedding generation (sentence-transformers)         │
│     └─ Storage in PostgreSQL with pgvector                  │
│                                                              │
│  2. Semantic Retrieval                                       │
│     ├─ Query embedding                                       │
│     ├─ Vector similarity search (cosine distance)           │
│     └─ Ranking and filtering                                │
│                                                              │
│  3. Context Building                                         │
│     ├─ Retrieve relevant documents                          │
│     ├─ Format for LLM consumption                           │
│     └─ Token budget management                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Database** | PostgreSQL 15 | Document storage |
| **Vector Extension** | pgvector 0.8.1 | Efficient similarity search |
| **Embeddings** | sentence-transformers | Text-to-vector conversion |
| **Model** | all-MiniLM-L6-v2 | 384-dim embeddings (fast, local) |
| **Indexing** | HNSW + IVFFlat | Vector indexes for speed |

## Database Schema

### `rag_documents` Table

```sql
CREATE TABLE rag_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    embedding vector(384) NOT NULL,
    doc_type VARCHAR(100) NOT NULL,
    metadata_ JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Indexes:**
- **HNSW index** on `embedding` (fast approximate search)
- **IVFFlat index** on `embedding` (alternative, faster build)
- **GIN index** on `metadata_` (JSON queries)
- **B-tree index** on `doc_type` (filtering)

## Usage

### 1. Document Ingestion

Ingest a document by chunking and embedding:

```python
from app.services.rag_service import RAGService
from app.db.session import SessionLocal

db = SessionLocal()
service = RAGService(db)

# Ingest ACGME documentation
response = await service.ingest_document(
    content="""
    ACGME Duty Hour Requirements:
    1. 80-Hour Work Week Limit...
    2. 1-in-7 Day Free of Duty...
    """,
    doc_type="acgme_rules",
    metadata={
        "source": "ACGME Manual 2024",
        "section": "Duty Hours",
        "version": "2024.1"
    },
    chunk_size=500,      # Target tokens per chunk
    chunk_overlap=50     # Overlap between chunks
)

print(f"Created {response.chunks_created} chunks")
```

**Parameters:**
- `content` (required): Document text
- `doc_type` (required): Category (acgme_rules, scheduling_policy, user_guide, etc.)
- `metadata` (optional): Additional context (source, section, author, etc.)
- `chunk_size` (default: 500): Target chunk size in tokens
- `chunk_overlap` (default: 50): Overlap between chunks

**Supported Document Types:**
- `acgme_rules` - ACGME regulations
- `scheduling_policy` - Institutional policies
- `user_guide` - User documentation
- `technical_doc` - Technical documentation
- `meeting_notes` - Meeting minutes
- `research_paper` - Academic papers
- `clinical_guideline` - Clinical protocols
- `other` - Miscellaneous

### 2. Semantic Retrieval

Search for relevant documents:

```python
# Retrieve documents by semantic similarity
response = await service.retrieve(
    query="What are the work hour limits for residents?",
    top_k=5,                  # Number of results
    doc_type="acgme_rules",   # Optional filter
    min_similarity=0.5,       # Threshold (0-1)
    metadata_filters={        # Optional metadata filters
        "version": "2024.1"
    }
)

for doc in response.documents:
    print(f"Similarity: {doc.similarity_score:.3f}")
    print(f"Content: {doc.content[:200]}...")
    print(f"Metadata: {doc.metadata}")
```

**Returns:** `RetrievalResponse` with:
- `documents`: List of `RetrievedDocument` objects
- `total_results`: Number of results
- `execution_time_ms`: Query duration

### 3. Context Building for LLMs

Build formatted context for AI model injection:

```python
# Build context string for LLM
context = await service.build_context(
    query="ACGME supervision requirements",
    max_tokens=2000,           # Token budget
    doc_type="acgme_rules",    # Optional filter
    include_metadata=True      # Include doc metadata
)

# Use in LLM prompt
prompt = f"""
Answer the following question using the provided context:

{context.context}

Question: {context.query}

Answer:
"""

print(f"Context uses {context.token_count} tokens")
print(f"Sources: {len(context.sources)} documents")
```

**Returns:** `RAGContext` with:
- `context`: Formatted context string (ready for LLM)
- `sources`: Source documents used
- `token_count`: Approximate tokens in context
- `metadata`: Additional context metadata

### 4. Health Check

Monitor RAG system status:

```python
health = await service.get_health()

print(f"Status: {health.status}")  # healthy/unhealthy/error
print(f"Total documents: {health.total_documents}")
print(f"By type: {health.documents_by_type}")
print(f"Model: {health.embedding_model}")
print(f"Index status: {health.vector_index_status}")

for recommendation in health.recommendations:
    print(f"⚠️  {recommendation}")
```

### 5. Document Deletion

Remove documents by type or ID:

```python
# Delete all documents of a type
count = service.delete_by_doc_type("acgme_rules")
print(f"Deleted {count} documents")

# Delete specific document
deleted = service.delete_by_id(document_id)
if deleted:
    print("Document deleted")
```

## Performance Tuning

### Chunk Size Selection

| Chunk Size | Use Case | Pros | Cons |
|------------|----------|------|------|
| 200-300 tokens | Precise retrieval | High precision | More chunks, slower ingestion |
| 500-700 tokens | **Recommended** | Balanced | Good for most use cases |
| 1000+ tokens | Large context | Fewer chunks | Lower precision |

**Rule of thumb:** Use smaller chunks for precise retrieval, larger chunks for broad context.

### Index Selection

The migration creates **two vector indexes**:

1. **HNSW** (Hierarchical Navigable Small World)
   - **Best for**: Production queries
   - **Pros**: Fastest queries, high recall
   - **Cons**: Slower build, more memory
   - **Parameters**: `m=16`, `ef_construction=64`

2. **IVFFlat** (Inverted File with Flat compression)
   - **Best for**: Development, smaller datasets
   - **Pros**: Faster build
   - **Cons**: Slower queries than HNSW
   - **Parameters**: `lists=100`

**PostgreSQL will automatically choose the optimal index.**

### Query Optimization

```python
# Fast query (fewer results, higher threshold)
await service.retrieve(
    query="supervision requirements",
    top_k=3,
    min_similarity=0.7  # High threshold
)

# Comprehensive query (more results, lower threshold)
await service.retrieve(
    query="supervision requirements",
    top_k=20,
    min_similarity=0.3  # Lower threshold
)
```

**Benchmark:**
- 1,000 documents: ~10-30ms query time
- 10,000 documents: ~30-100ms query time
- 100,000 documents: ~100-300ms query time

## Best Practices

### 1. Document Ingestion

✅ **DO:**
- Use descriptive `doc_type` values
- Include rich metadata (source, date, version)
- Chunk long documents (>2000 tokens)
- Use 10-20% overlap between chunks

❌ **DON'T:**
- Ingest very short texts (< 50 tokens)
- Use generic doc_types like "document"
- Skip metadata (reduces retrieval quality)

### 2. Retrieval

✅ **DO:**
- Use specific queries (better than vague)
- Set appropriate `min_similarity` threshold (0.5-0.7 typical)
- Filter by `doc_type` when possible
- Review similarity scores in results

❌ **DON'T:**
- Use very broad queries ("everything about X")
- Set `min_similarity` too high (> 0.9) - you'll miss relevant docs
- Retrieve too many results (top_k > 50) - diminishing returns

### 3. Context Building

✅ **DO:**
- Set realistic `max_tokens` budget (account for prompt overhead)
- Include metadata for source attribution
- Review generated context before LLM use

❌ **DON'T:**
- Exceed LLM context window
- Assume all retrieved docs are relevant (check similarity scores)

## Example: Integrating with Claude API

```python
from app.services.rag_service import RAGService
from app.services.claude_service import ClaudeService

# 1. Build context from RAG
rag_service = RAGService(db)
context = await rag_service.build_context(
    query="ACGME work hour limits",
    max_tokens=2000
)

# 2. Inject into Claude prompt
claude_service = ClaudeService()
prompt = f"""
You are an expert on ACGME residency requirements.

Relevant Documentation:
{context.context}

Question: {context.query}

Provide a concise answer citing specific ACGME requirements:
"""

response = await claude_service.execute_task(
    request=ClaudeCodeRequest(
        action="answer_question",
        context={"prompt": prompt}
    ),
    user_id=user_id
)

print(response["result"])
```

## Troubleshooting

### Issue: No results returned

**Cause:** Query too specific or `min_similarity` too high

**Solution:**
```python
# Lower similarity threshold
response = await service.retrieve(
    query="your query",
    min_similarity=0.3  # Lower from 0.7
)
```

### Issue: Slow ingestion

**Cause:** Large documents, many chunks

**Solution:**
```python
# Ingest in background with Celery
from app.tasks.rag_tasks import ingest_document_task

ingest_document_task.delay(
    content=large_document,
    doc_type="acgme_rules"
)
```

### Issue: Poor retrieval quality

**Cause:** Chunk size too large, missing metadata

**Solution:**
```python
# Use smaller chunks
await service.ingest_document(
    content=document,
    chunk_size=300,  # Smaller chunks
    chunk_overlap=50,
    metadata={       # Rich metadata
        "source": "ACGME Manual",
        "section": "Duty Hours",
        "page": 42
    }
)
```

### Issue: Index not found

**Cause:** Migrations not run

**Solution:**
```bash
cd backend
alembic upgrade head
```

## Monitoring

### Key Metrics

```python
# Check system health
health = await service.get_health()

# Track these metrics:
- Total document count (should grow over time)
- Documents by type (balanced distribution)
- Vector index status (should be "ready")
- Query execution time (< 100ms typical)
```

### Database Queries

```sql
-- Check document distribution
SELECT doc_type, COUNT(*) as count
FROM rag_documents
GROUP BY doc_type
ORDER BY count DESC;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE tablename = 'rag_documents';

-- Check table size
SELECT pg_size_pretty(pg_total_relation_size('rag_documents'));
```

## Future Enhancements

Potential improvements:
- [ ] Hybrid search (combine vector + keyword search)
- [ ] Multi-language support
- [ ] Document versioning
- [ ] Re-ranking with cross-encoders
- [ ] Automatic chunking strategy selection
- [ ] Cache frequently accessed embeddings
- [ ] Bulk ingestion optimizations

## References

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [sentence-transformers](https://www.sbert.net/)
- [HNSW Algorithm](https://arxiv.org/abs/1603.09320)
- [RAG Survey Paper](https://arxiv.org/abs/2312.10997)

## API Reference

See Pydantic schemas in `backend/app/schemas/rag.py` for complete API documentation.
