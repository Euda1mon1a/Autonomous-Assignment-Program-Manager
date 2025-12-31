"""RAG (Retrieval-Augmented Generation) service for document ingestion and retrieval.

This service provides semantic search capabilities for scheduling documentation,
ACGME rules, and other reference materials using pgvector and sentence-transformers.
"""

import logging
import re
import time
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models.rag_document import RAGDocument
from app.schemas.rag import (
    ContextBuildRequest,
    DocumentChunk,
    IngestResponse,
    RAGContext,
    RAGHealthResponse,
    RAGRetrievalRequest,
    RetrievalResponse,
    RetrievedDocument,
)
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG document ingestion and retrieval.

    Handles:
    - Document chunking with configurable size and overlap
    - Embedding generation using sentence-transformers
    - Vector storage in pgvector
    - Semantic similarity search
    - Context building for LLM injection
    """

    # Default configuration
    DEFAULT_CHUNK_SIZE = 500  # tokens
    DEFAULT_CHUNK_OVERLAP = 50  # tokens
    DEFAULT_TOP_K = 5
    DEFAULT_MIN_SIMILARITY = 0.5
    APPROX_CHARS_PER_TOKEN = 4  # Rough approximation for English text

    def __init__(self, db: Session):
        """Initialize RAG service.

        Args:
            db: Database session
        """
        self.db = db
        self.embedding_service = EmbeddingService()

    async def ingest_document(
        self,
        content: str,
        doc_type: str,
        metadata: dict[str, Any] | None = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> IngestResponse:
        """Ingest a document by chunking and storing with embeddings.

        Args:
            content: Document text content
            doc_type: Type of document (acgme_rules, scheduling_policy, etc.)
            metadata: Additional metadata to store with chunks
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens

        Returns:
            IngestResponse with status and chunk IDs

        Raises:
            ValueError: If content is empty or parameters are invalid
        """
        if not content or not content.strip():
            raise ValueError("Content cannot be empty")

        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

        metadata = metadata or {}

        try:
            # Chunk the document
            chunks = self._chunk_text(content, chunk_size, chunk_overlap)
            logger.info(
                f"Chunked document into {len(chunks)} chunks (type: {doc_type})"
            )

            # Generate embeddings for all chunks (batch for efficiency)
            embeddings = self.embedding_service.embed_batch(chunks)

            # Create RAGDocument records
            chunk_ids = []
            for chunk_text, embedding in zip(chunks, embeddings):
                rag_doc = RAGDocument(
                    content=chunk_text,
                    embedding=embedding,
                    doc_type=doc_type,
                    metadata_=metadata,
                )
                self.db.add(rag_doc)
                self.db.flush()  # Get ID without committing
                chunk_ids.append(rag_doc.id)

            # Commit all chunks
            self.db.commit()

            logger.info(
                f"Successfully ingested {len(chunk_ids)} chunks for doc_type={doc_type}"
            )

            return IngestResponse(
                status="success",
                chunks_created=len(chunk_ids),
                chunk_ids=chunk_ids,
                doc_type=doc_type,
                message=f"Successfully ingested {len(chunk_ids)} chunks",
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error ingesting document: {str(e)}", exc_info=True)
            return IngestResponse(
                status="error",
                chunks_created=0,
                chunk_ids=[],
                doc_type=doc_type,
                message=f"Error: {str(e)}",
            )

    async def retrieve(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        doc_type: str | None = None,
        min_similarity: float = DEFAULT_MIN_SIMILARITY,
        metadata_filters: dict[str, Any] | None = None,
    ) -> RetrievalResponse:
        """Retrieve relevant documents using vector similarity search.

        Args:
            query: Query text for semantic search
            top_k: Number of top results to return
            doc_type: Filter by document type (optional)
            min_similarity: Minimum cosine similarity threshold (0-1)
            metadata_filters: Additional metadata filters

        Returns:
            RetrievalResponse with ranked documents

        Raises:
            ValueError: If query is empty or parameters are invalid
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if not 0.0 <= min_similarity <= 1.0:
            raise ValueError("min_similarity must be between 0.0 and 1.0")

        start_time = time.time()

        try:
            # Generate query embedding
            query_embedding = self.embedding_service.embed_text(query)

            # Build query with vector similarity search
            # Using cosine distance: 1 - cosine_similarity
            # So similarity = 1 - distance
            stmt = select(
                RAGDocument,
                (1 - RAGDocument.embedding.cosine_distance(query_embedding)).label(
                    "similarity"
                ),
            )

            # Apply filters
            if doc_type:
                stmt = stmt.where(RAGDocument.doc_type == doc_type)

            # Apply metadata filters
            if metadata_filters:
                for key, value in metadata_filters.items():
                    # Use PostgreSQL JSON operators for metadata filtering
                    stmt = stmt.where(RAGDocument.metadata_[key].astext == str(value))

            # Filter by minimum similarity
            # Note: This is done in SQL for efficiency
            stmt = stmt.where(
                (1 - RAGDocument.embedding.cosine_distance(query_embedding))
                >= min_similarity
            )

            # Order by similarity (highest first) and limit
            stmt = stmt.order_by(text("similarity DESC")).limit(top_k)

            # Execute query
            results = self.db.execute(stmt).all()

            # Convert to RetrievedDocument schema
            documents = [
                RetrievedDocument(
                    id=row.RAGDocument.id,
                    content=row.RAGDocument.content,
                    doc_type=row.RAGDocument.doc_type,
                    metadata=row.RAGDocument.metadata_,
                    similarity_score=float(row.similarity),
                    created_at=row.RAGDocument.created_at,
                )
                for row in results
            ]

            execution_time_ms = (time.time() - start_time) * 1000

            logger.info(
                f"Retrieved {len(documents)} documents for query in {execution_time_ms:.2f}ms"
            )

            return RetrievalResponse(
                query=query,
                documents=documents,
                total_results=len(documents),
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}", exc_info=True)
            raise

    async def build_context(
        self,
        query: str,
        max_tokens: int = 2000,
        doc_type: str | None = None,
        include_metadata: bool = True,
    ) -> RAGContext:
        """Build context string for LLM injection from retrieved documents.

        Args:
            query: Query to retrieve context for
            max_tokens: Maximum tokens in context string
            doc_type: Filter by document type (optional)
            include_metadata: Include metadata in context string

        Returns:
            RAGContext with formatted context string and sources

        Raises:
            ValueError: If query is empty or max_tokens is invalid
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if max_tokens < 100:
            raise ValueError("max_tokens must be at least 100")

        # Retrieve relevant documents
        retrieval_response = await self.retrieve(
            query=query,
            top_k=20,  # Get more results, we'll filter by token count
            doc_type=doc_type,
            min_similarity=0.5,
        )

        # Build context string with token budget
        context_parts = []
        sources = []
        current_tokens = 0
        max_content_tokens = max_tokens - 200  # Reserve tokens for formatting

        for doc in retrieval_response.documents:
            # Estimate tokens for this document
            doc_text = doc.content
            if include_metadata and doc.metadata:
                # Add metadata as context
                metadata_str = ", ".join(f"{k}: {v}" for k, v in doc.metadata.items())
                doc_text = f"[{metadata_str}]\n{doc_text}"

            doc_tokens = len(doc_text) // self.APPROX_CHARS_PER_TOKEN

            # Check if adding this document would exceed budget
            if current_tokens + doc_tokens > max_content_tokens:
                # If we haven't added any documents yet, truncate this one
                if not context_parts:
                    remaining_chars = (
                        max_content_tokens - current_tokens
                    ) * self.APPROX_CHARS_PER_TOKEN
                    doc_text = doc_text[:remaining_chars] + "..."
                    context_parts.append(doc_text)
                    sources.append(doc)
                break

            context_parts.append(doc_text)
            sources.append(doc)
            current_tokens += doc_tokens

        # Format final context
        context = "\n\n---\n\n".join(context_parts)

        # Add header
        header = f"# Relevant Context for Query: {query}\n\n"
        context = header + context

        # Calculate final token count
        token_count = len(context) // self.APPROX_CHARS_PER_TOKEN

        logger.info(f"Built context with {len(sources)} sources, ~{token_count} tokens")

        return RAGContext(
            query=query,
            context=context,
            sources=sources,
            token_count=token_count,
            metadata={
                "doc_type_filter": doc_type,
                "include_metadata": include_metadata,
                "max_tokens": max_tokens,
            },
        )

    async def get_health(self) -> RAGHealthResponse:
        """Get health status of RAG system.

        Returns:
            RAGHealthResponse with system status and statistics
        """
        try:
            # Get total document count
            total_docs = self.db.scalar(select(func.count()).select_from(RAGDocument))

            # Get counts by doc_type
            type_counts = {}
            type_results = self.db.execute(
                select(RAGDocument.doc_type, func.count())
                .group_by(RAGDocument.doc_type)
                .order_by(RAGDocument.doc_type)
            ).all()

            for doc_type, count in type_results:
                type_counts[doc_type] = count

            # Check if pgvector extension is enabled
            vector_enabled = self.db.execute(
                text(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                )
            ).scalar()

            # Check if indexes exist
            index_check = self.db.execute(
                text("""
                    SELECT COUNT(*)
                    FROM pg_indexes
                    WHERE tablename = 'rag_documents'
                    AND indexname LIKE '%embedding%'
                """)
            ).scalar()

            vector_index_status = "ready" if index_check > 0 else "missing"

            # Generate recommendations
            recommendations = []
            if total_docs == 0:
                recommendations.append(
                    "No documents ingested yet. Use ingest_document() to add content."
                )
            elif total_docs < 10:
                recommendations.append(
                    "Low document count. Consider ingesting more reference materials for better retrieval."
                )

            if vector_index_status == "missing":
                recommendations.append(
                    "Vector indexes missing. Run migrations to create indexes for optimal performance."
                )

            status = "healthy" if vector_enabled and total_docs > 0 else "unhealthy"

            return RAGHealthResponse(
                status=status,
                total_documents=total_docs,
                documents_by_type=type_counts,
                embedding_model=self.embedding_service.MODEL_NAME,
                embedding_dimensions=self.embedding_service.EMBEDDING_DIM,
                vector_index_status=vector_index_status,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error(f"Error checking RAG health: {str(e)}", exc_info=True)
            return RAGHealthResponse(
                status="error",
                total_documents=0,
                documents_by_type={},
                embedding_model=self.embedding_service.MODEL_NAME,
                embedding_dimensions=self.embedding_service.EMBEDDING_DIM,
                vector_index_status="unknown",
                recommendations=[f"Error checking health: {str(e)}"],
            )

    def _chunk_text(
        self,
        text: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> list[str]:
        """Chunk text into smaller segments with overlap.

        Uses a sliding window approach with sentence-aware splitting to avoid
        breaking sentences when possible.

        Args:
            text: Text to chunk
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens

        Returns:
            List of text chunks
        """
        # Convert token size to approximate character count
        chunk_chars = chunk_size * self.APPROX_CHARS_PER_TOKEN
        overlap_chars = chunk_overlap * self.APPROX_CHARS_PER_TOKEN

        # Split into sentences (simple approach)
        sentences = self._split_into_sentences(text)

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            # If adding this sentence would exceed chunk size
            if current_length + sentence_length > chunk_chars and current_chunk:
                # Save current chunk
                chunks.append(" ".join(current_chunk))

                # Start new chunk with overlap
                # Keep last few sentences for overlap
                overlap_text = " ".join(current_chunk)
                if len(overlap_text) > overlap_chars:
                    # Trim to overlap size
                    overlap_text = overlap_text[-overlap_chars:]
                    # Try to start at sentence boundary
                    sentence_start = overlap_text.find(". ") + 2
                    if sentence_start > 2:
                        overlap_text = overlap_text[sentence_start:]

                current_chunk = (
                    [overlap_text, sentence] if overlap_chars > 0 else [sentence]
                )
                current_length = len(" ".join(current_chunk))
            else:
                current_chunk.append(sentence)
                current_length += sentence_length + 1  # +1 for space

        # Add final chunk if any
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        # Filter out very small chunks (< 10% of target size)
        min_chunk_size = chunk_chars // 10
        chunks = [c for c in chunks if len(c) >= min_chunk_size]

        return chunks

    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences using regex.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Simple sentence splitting regex
        # Matches periods, exclamation marks, question marks followed by space/newline
        sentence_endings = re.compile(r"(?<=[.!?])\s+")
        sentences = sentence_endings.split(text)

        # Clean up sentences
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def delete_by_doc_type(self, doc_type: str) -> int:
        """Delete all documents of a specific type.

        Args:
            doc_type: Document type to delete

        Returns:
            Number of documents deleted
        """
        try:
            count = (
                self.db.query(RAGDocument)
                .filter(RAGDocument.doc_type == doc_type)
                .delete()
            )
            self.db.commit()
            logger.info(f"Deleted {count} documents of type {doc_type}")
            return count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting documents: {str(e)}", exc_info=True)
            raise

    def delete_by_id(self, document_id: UUID) -> bool:
        """Delete a specific document by ID.

        Args:
            document_id: ID of document to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            doc = (
                self.db.query(RAGDocument).filter(RAGDocument.id == document_id).first()
            )
            if doc:
                self.db.delete(doc)
                self.db.commit()
                logger.info(f"Deleted document {document_id}")
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting document: {str(e)}", exc_info=True)
            raise
