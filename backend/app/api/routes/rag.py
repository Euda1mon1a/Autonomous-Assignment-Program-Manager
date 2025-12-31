"""RAG (Retrieval-Augmented Generation) API routes.

Provides endpoints for:
- Semantic search across ingested documents
- Document ingestion for RAG knowledge base
- Context building for LLM injection
- RAG system health check
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.rag import (
    ContextBuildRequest,
    DocumentIngestRequest,
    IngestResponse,
    RAGContext,
    RAGHealthResponse,
    RAGRetrievalRequest,
    RetrievalResponse,
)
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_documents(
    request: RAGRetrievalRequest,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve relevant documents using semantic search.

    Performs vector similarity search against the RAG knowledge base
    to find documents most relevant to the query.

    Features:
    - Semantic similarity using sentence embeddings
    - Optional filtering by document type
    - Configurable similarity threshold
    - Metadata filtering support

    Args:
        request: RAGRetrievalRequest containing:
            - query: Search query text
            - top_k: Number of results to return (default: 5)
            - doc_type: Optional document type filter
            - min_similarity: Minimum similarity threshold (default: 0.5)
            - metadata_filters: Optional metadata key/value filters

    Returns:
        RetrievalResponse with:
            - query: Original query
            - documents: List of matching documents with similarity scores
            - total_results: Number of documents returned
            - execution_time_ms: Query execution time

    Requires authentication.
    """
    try:
        service = RAGService(db)
        response = await service.retrieve(
            query=request.query,
            top_k=request.top_k,
            doc_type=request.doc_type,
            min_similarity=request.min_similarity,
            metadata_filters=request.metadata_filters,
        )
        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (KeyError, AttributeError) as e:
        logger.error(f"RAG retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Retrieval failed")


@router.get("/health", response_model=RAGHealthResponse)
async def get_rag_health(
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get health status of the RAG system.

    Returns information about:
    - Overall system status (healthy/unhealthy)
    - Total document count
    - Documents by type
    - Embedding model information
    - Vector index status
    - System recommendations

    Useful for monitoring and debugging the RAG knowledge base.

    Returns:
        RAGHealthResponse with:
            - status: healthy or unhealthy
            - total_documents: Total ingested chunks
            - documents_by_type: Breakdown by document type
            - embedding_model: Model used for embeddings
            - embedding_dimensions: Vector dimension size
            - vector_index_status: Index status (ready/building/missing)
            - recommendations: System improvement suggestions

    Requires authentication.
    """
    try:
        service = RAGService(db)
        return await service.get_health()

    except Exception as e:
        logger.error(f"RAG health check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Health check failed")


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    request: DocumentIngestRequest,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Ingest a document into the RAG knowledge base.

    Chunks the document content and stores with embeddings for
    later semantic search retrieval.

    Args:
        request: DocumentIngestRequest containing:
            - content: Document text content
            - doc_type: Type of document (acgme_rules, scheduling_policy, etc.)
            - metadata: Additional metadata to store
            - chunk_size: Target chunk size in tokens (default: 500)
            - chunk_overlap: Overlap between chunks (default: 50)

    Returns:
        IngestResponse with:
            - status: success or error
            - chunks_created: Number of chunks created
            - chunk_ids: List of created chunk UUIDs
            - doc_type: Document type
            - message: Status message

    Requires authentication.
    """
    try:
        service = RAGService(db)
        response = await service.ingest_document(
            content=request.content,
            doc_type=request.doc_type,
            metadata=request.metadata,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
        )
        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Document ingestion failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ingestion failed")


@router.post("/context", response_model=RAGContext)
async def build_context(
    request: ContextBuildRequest,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Build context string for LLM injection from relevant documents.

    Retrieves relevant documents and formats them into a context
    string suitable for injecting into LLM prompts.

    Args:
        request: ContextBuildRequest containing:
            - query: Query to retrieve context for
            - max_tokens: Maximum tokens in context (default: 2000)
            - doc_type: Optional document type filter
            - include_metadata: Include metadata in context (default: True)

    Returns:
        RAGContext with:
            - query: Original query
            - context: Formatted context string
            - sources: Source documents used
            - token_count: Approximate token count
            - metadata: Context generation metadata

    Requires authentication.
    """
    try:
        service = RAGService(db)
        response = await service.build_context(
            query=request.query,
            max_tokens=request.max_tokens,
            doc_type=request.doc_type,
            include_metadata=request.include_metadata,
        )
        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Context building failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Context building failed")


@router.delete("/documents/{doc_type}")
async def delete_documents_by_type(
    doc_type: str,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """
    Delete all documents of a specific type.

    Useful for refreshing a category of documents in the knowledge base.

    Args:
        doc_type: Document type to delete (e.g., "acgme_rules")

    Returns:
        Dictionary with:
            - deleted_count: Number of documents deleted
            - doc_type: Document type that was deleted

    Requires authentication.
    """
    try:
        service = RAGService(db)
        count = service.delete_by_doc_type(doc_type)
        return {
            "deleted_count": count,
            "doc_type": doc_type,
        }

    except Exception as e:
        logger.error(f"Document deletion failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Deletion failed")


@router.get("/stats")
async def get_rag_stats(
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """
    Get statistics about the RAG knowledge base.

    Simplified endpoint for quick status checks.

    Returns:
        Dictionary with:
            - total_chunks: Total document chunks
            - categories: List of document types
            - status: System status

    Requires authentication.
    """
    try:
        service = RAGService(db)
        health = await service.get_health()

        return {
            "total_chunks": health.total_documents,
            "categories": list(health.documents_by_type.keys()),
            "documents_by_category": health.documents_by_type,
            "status": health.status,
            "embedding_model": health.embedding_model,
        }

    except Exception as e:
        logger.error(f"RAG stats failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Stats retrieval failed")
