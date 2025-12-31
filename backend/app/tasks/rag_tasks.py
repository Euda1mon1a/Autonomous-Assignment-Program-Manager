"""
Celery Tasks for RAG Embeddings.

Provides automated background tasks for:
- Initializing RAG embeddings from knowledge base
- Refreshing embeddings periodically
- Processing individual documents
- Health checks and maintenance
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from celery import shared_task
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Document type mapping (filename -> doc_type)
DOC_TYPE_MAP = {
    "acgme-rules.md": "acgme_rules",
    "scheduling-policies.md": "scheduling_policy",
    "swap-system.md": "swap_system",
    "military-specific.md": "military_specific",
    "resilience-concepts.md": "resilience_concepts",
    "user-guide-faq.md": "user_guide_faq",
    "session-learnings.md": "session_learnings",
    "session-protocols.md": "session_protocols",
    "delegation-patterns.md": "delegation_patterns",
    "exotic-concepts.md": "exotic_concepts",
}


def get_db_session() -> Session:
    """Get a database session for task execution."""
    from app.db.session import SessionLocal

    return SessionLocal()


def _run_async(coro):
    """Run an async coroutine from a synchronous Celery task."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    return loop.run_until_complete(coro)


def get_docs_path() -> Path:
    """Get the path to the RAG knowledge base documents.

    Returns:
        Path to docs/rag-knowledge directory
    """
    # Assume backend/ is the working directory
    backend_path = Path(__file__).parent.parent.parent
    return backend_path.parent / "docs" / "rag-knowledge"


@shared_task(
    bind=True,
    name="app.tasks.rag_tasks.initialize_embeddings",
    max_retries=2,
    default_retry_delay=300,
)
def initialize_embeddings(
    self,
    doc_filter: str | None = None,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """
    Initialize RAG embeddings from knowledge base documents.

    This task reads markdown files from docs/rag-knowledge/ and embeds them
    into the pgvector database for semantic search.

    Args:
        doc_filter: Optional filename filter (e.g., "acgme-rules.md")
                   If None, processes all documents.
        chunk_size: Target chunk size in tokens (default: 500)
        chunk_overlap: Overlap between chunks in tokens (default: 50)
        force_refresh: If True, clears existing docs before processing

    Returns:
        Dict with initialization results including:
        - documents_processed: Number of documents processed
        - documents_successful: Number successfully embedded
        - documents_failed: Number that failed
        - total_chunks: Total chunks created
        - results: Detailed results for each document

    Raises:
        Retries on failure up to max_retries.
    """
    logger.info("Starting RAG embeddings initialization")

    db = get_db_session()
    try:
        from app.services.rag_service import RAGService

        rag_service = RAGService(db)

        # Validate database
        health = _run_async(rag_service.get_health())
        if health.status == "error":
            logger.error(f"RAG system unhealthy: {health.recommendations}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": "RAG system health check failed",
                "recommendations": health.recommendations,
            }

        logger.info(
            f"RAG system healthy - {health.total_documents} existing docs, "
            f"index status: {health.vector_index_status}"
        )

        # Clear existing documents if force_refresh
        if force_refresh:
            logger.info("Force refresh enabled - clearing existing documents")
            total_deleted = 0
            for doc_type in DOC_TYPE_MAP.values():
                count = rag_service.delete_by_doc_type(doc_type)
                total_deleted += count
            logger.info(f"Cleared {total_deleted} existing chunks")

        # Get documents to process
        docs_path = get_docs_path()
        if not docs_path.exists():
            logger.error(f"Knowledge base directory not found: {docs_path}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": f"Directory not found: {docs_path}",
            }

        if doc_filter:
            files = [docs_path / doc_filter]
            if not files[0].exists():
                logger.error(f"Document not found: {doc_filter}")
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "error",
                    "error": f"File not found: {doc_filter}",
                }
        else:
            files = sorted(docs_path.glob("*.md"))

        if not files:
            logger.warning(f"No markdown files found in {docs_path}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": "No documents found",
            }

        logger.info(f"Processing {len(files)} document(s)")

        # Process each document
        results = []
        total_chunks = 0

        for filepath in files:
            filename = filepath.name
            doc_type = DOC_TYPE_MAP.get(filename, filename.replace(".md", ""))

            logger.info(f"Processing {filename} (type: {doc_type})")

            try:
                # Read content
                content = filepath.read_text(encoding="utf-8")

                if not content.strip():
                    logger.warning(f"Document {filename} is empty, skipping")
                    results.append(
                        {
                            "filename": filename,
                            "status": "skipped",
                            "reason": "empty_content",
                        }
                    )
                    continue

                # Clear existing docs of this type (idempotent)
                if not force_refresh:  # Already cleared if force_refresh
                    existing_count = rag_service.delete_by_doc_type(doc_type)
                    if existing_count > 0:
                        logger.info(
                            f"Cleared {existing_count} existing chunks for {doc_type}"
                        )

                # Ingest document
                metadata = {
                    "filename": filename,
                    "source": "docs/rag-knowledge",
                    "file_size": len(content),
                    "task_id": self.request.id,
                }

                ingest_result = _run_async(
                    rag_service.ingest_document(
                        content=content,
                        doc_type=doc_type,
                        metadata=metadata,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                    )
                )

                if ingest_result.status == "success":
                    logger.info(
                        f"✓ Created {ingest_result.chunks_created} chunks for {filename}"
                    )
                    results.append(
                        {
                            "filename": filename,
                            "status": "success",
                            "chunks_created": ingest_result.chunks_created,
                            "doc_type": doc_type,
                        }
                    )
                    total_chunks += ingest_result.chunks_created
                else:
                    logger.error(
                        f"✗ Failed to ingest {filename}: {ingest_result.message}"
                    )
                    results.append(
                        {
                            "filename": filename,
                            "status": "error",
                            "error": ingest_result.message,
                            "doc_type": doc_type,
                        }
                    )

            except Exception as e:
                logger.error(f"Error processing {filename}: {e}", exc_info=True)
                results.append(
                    {
                        "filename": filename,
                        "status": "error",
                        "error": str(e),
                        "doc_type": doc_type,
                    }
                )

        # Calculate summary
        success_count = sum(1 for r in results if r["status"] == "success")
        error_count = sum(1 for r in results if r["status"] == "error")

        logger.info(
            f"RAG initialization complete: {success_count}/{len(files)} successful, "
            f"{total_chunks} total chunks"
        )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "completed",
            "documents_processed": len(files),
            "documents_successful": success_count,
            "documents_failed": error_count,
            "total_chunks": total_chunks,
            "results": results,
            "task_status": "completed",
        }

    except Exception as e:
        logger.error(f"RAG initialization failed: {e}", exc_info=True)
        raise self.retry(exc=e)
    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.rag_tasks.refresh_single_document",
    max_retries=2,
    default_retry_delay=60,
)
def refresh_single_document(
    self,
    filename: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> dict[str, Any]:
    """
    Refresh embeddings for a single document.

    Useful for updating a specific document after edits without
    re-processing the entire knowledge base.

    Args:
        filename: Name of the file in docs/rag-knowledge/ (e.g., "acgme-rules.md")
        chunk_size: Target chunk size in tokens (default: 500)
        chunk_overlap: Overlap between chunks in tokens (default: 50)

    Returns:
        Dict with refresh results.

    Raises:
        Retries on failure up to max_retries.
    """
    logger.info(f"Refreshing embeddings for {filename}")

    return initialize_embeddings(
        self,
        doc_filter=filename,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        force_refresh=False,  # Will clear just this doc_type
    )


@shared_task(
    bind=True,
    name="app.tasks.rag_tasks.check_rag_health",
    max_retries=1,
    default_retry_delay=60,
)
def check_rag_health(self) -> dict[str, Any]:
    """
    Check health of RAG system and embeddings.

    Returns:
        Dict with RAG system health status including:
        - status: "healthy" or "unhealthy"
        - total_documents: Number of embedded chunks
        - documents_by_type: Breakdown by doc_type
        - embedding_model: Model name
        - embedding_dimensions: Vector dimensions
        - vector_index_status: Index availability
        - recommendations: Suggested actions
    """
    logger.info("Checking RAG system health")

    db = get_db_session()
    try:
        from app.services.rag_service import RAGService

        rag_service = RAGService(db)
        health = _run_async(rag_service.get_health())

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": health.status,
            "total_documents": health.total_documents,
            "documents_by_type": health.documents_by_type,
            "embedding_model": health.embedding_model,
            "embedding_dimensions": health.embedding_dimensions,
            "vector_index_status": health.vector_index_status,
            "recommendations": health.recommendations,
            "task_status": "completed",
        }

    except Exception as e:
        logger.error(f"RAG health check failed: {e}", exc_info=True)
        raise self.retry(exc=e)
    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.rag_tasks.periodic_refresh",
    max_retries=2,
    default_retry_delay=600,
)
def periodic_refresh(self) -> dict[str, Any]:
    """
    Periodic refresh of RAG embeddings.

    This task should be scheduled via Celery Beat to keep embeddings
    up-to-date with the latest knowledge base content.

    Recommended schedule: Weekly or when documents are updated.

    Returns:
        Dict with refresh results.
    """
    logger.info("Running periodic RAG embeddings refresh")

    # Check if any documents have changed (simple check)
    docs_path = get_docs_path()
    files = sorted(docs_path.glob("*.md"))

    if not files:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "skipped",
            "reason": "No documents found",
        }

    # For now, do a full refresh
    # Future enhancement: Only refresh changed files based on mtime
    return initialize_embeddings(
        self,
        doc_filter=None,
        chunk_size=500,
        chunk_overlap=50,
        force_refresh=True,  # Full refresh
    )


@shared_task(
    bind=True,
    name="app.tasks.rag_tasks.clear_all_embeddings",
    max_retries=1,
    default_retry_delay=60,
)
def clear_all_embeddings(self) -> dict[str, Any]:
    """
    Clear all RAG embeddings from the database.

    Useful for:
    - Resetting the knowledge base
    - Clearing before a full re-index
    - Maintenance operations

    Returns:
        Dict with deletion results.
    """
    logger.info("Clearing all RAG embeddings")

    db = get_db_session()
    try:
        from app.services.rag_service import RAGService

        rag_service = RAGService(db)

        total_deleted = 0
        for doc_type in DOC_TYPE_MAP.values():
            count = rag_service.delete_by_doc_type(doc_type)
            total_deleted += count
            logger.info(f"Deleted {count} chunks of type {doc_type}")

        logger.info(f"Cleared {total_deleted} total chunks")

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "completed",
            "total_deleted": total_deleted,
            "task_status": "completed",
        }

    except Exception as e:
        logger.error(f"Failed to clear embeddings: {e}", exc_info=True)
        raise self.retry(exc=e)
    finally:
        db.close()
