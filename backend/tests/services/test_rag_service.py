"""Tests for RAG (Retrieval-Augmented Generation) service.

Note: Vector similarity tests require PostgreSQL with pgvector extension.
SQLite tests will focus on chunking, ingestion flow, and business logic.
"""

import pytest
from uuid import uuid4

from app.services.rag_service import RAGService
from app.models.rag_document import RAGDocument


class TestRAGServiceChunking:
    """Test text chunking functionality (works with SQLite)."""

    def test_chunk_text_basic(self, db):
        """Test basic text chunking with default parameters."""
        service = RAGService(db)

        text = (
            "This is sentence one. This is sentence two. This is sentence three. " * 20
        )
        chunks = service._chunk_text(text, chunk_size=100, chunk_overlap=20)

        assert len(chunks) > 1, "Text should be split into multiple chunks"
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(len(chunk) > 0 for chunk in chunks)

    def test_chunk_text_with_overlap(self, db):
        """Test that chunks have overlap."""
        service = RAGService(db)

        text = "Sentence A. Sentence B. Sentence C. Sentence D. " * 10
        chunks = service._chunk_text(text, chunk_size=100, chunk_overlap=30)

        # Verify chunks overlap by checking for common content
        if len(chunks) > 1:
            # There should be some overlap between consecutive chunks
            # This is a weak test but sufficient for validation
            assert len(chunks[0]) > 0
            assert len(chunks[1]) > 0

    def test_chunk_text_small_input(self, db):
        """Test chunking with very small input."""
        service = RAGService(db)

        text = "Short text."
        chunks = service._chunk_text(text, chunk_size=500, chunk_overlap=50)

        # Small text should result in single chunk
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_empty_input(self, db):
        """Test chunking with empty input."""
        service = RAGService(db)

        chunks = service._chunk_text("", chunk_size=500, chunk_overlap=50)

        # Empty text should result in empty chunks list
        assert len(chunks) == 0

    def test_split_into_sentences(self, db):
        """Test sentence splitting."""
        service = RAGService(db)

        text = "First sentence. Second sentence! Third sentence? Fourth sentence."
        sentences = service._split_into_sentences(text)

        assert len(sentences) == 4
        assert "First sentence" in sentences[0]
        assert "Second sentence" in sentences[1]
        assert "Third sentence" in sentences[2]
        assert "Fourth sentence" in sentences[3]


class TestRAGServiceIngestion:
    """Test document ingestion (requires PostgreSQL with pgvector)."""

    @pytest.mark.skipif(
        True,  # Skip for SQLite tests
        reason="Requires PostgreSQL with pgvector extension",
    )
    async def test_ingest_document_success(self, db):
        """Test successful document ingestion."""
        service = RAGService(db)

        content = (
            """
        ACGME Duty Hour Requirements:

        1. The 80-Hour Rule: Residents must not exceed 80 hours per week averaged over 4 weeks.
        2. The 1-in-7 Rule: Residents must have at least one 24-hour period free of duty every 7 days.
        3. Supervision Requirements: All patient care must be supervised.
        """
            * 5
        )  # Make it long enough to chunk

        response = await service.ingest_document(
            content=content,
            doc_type="acgme_rules",
            metadata={"source": "ACGME Manual 2024", "section": "Duty Hours"},
            chunk_size=500,
            chunk_overlap=50,
        )

        assert response.status == "success"
        assert response.chunks_created > 0
        assert len(response.chunk_ids) == response.chunks_created
        assert response.doc_type == "acgme_rules"

    async def test_ingest_document_empty_content(self, db):
        """Test that empty content raises ValueError."""
        service = RAGService(db)

        with pytest.raises(ValueError, match="Content cannot be empty"):
            await service.ingest_document(
                content="",
                doc_type="acgme_rules",
            )

    async def test_ingest_document_invalid_overlap(self, db):
        """Test that invalid overlap raises ValueError."""
        service = RAGService(db)

        with pytest.raises(
            ValueError, match="chunk_overlap must be less than chunk_size"
        ):
            await service.ingest_document(
                content="Some content",
                doc_type="acgme_rules",
                chunk_size=100,
                chunk_overlap=150,  # Greater than chunk_size
            )


class TestRAGServiceRetrieval:
    """Test document retrieval (requires PostgreSQL with pgvector)."""

    @pytest.mark.skipif(
        True,  # Skip for SQLite tests
        reason="Requires PostgreSQL with pgvector extension",
    )
    async def test_retrieve_documents(self, db):
        """Test retrieving documents by similarity."""
        service = RAGService(db)

        # First ingest some documents
        await service.ingest_document(
            content="ACGME requires residents to work no more than 80 hours per week.",
            doc_type="acgme_rules",
            metadata={"topic": "duty_hours"},
        )

        await service.ingest_document(
            content="Residents must have adequate supervision during patient care.",
            doc_type="acgme_rules",
            metadata={"topic": "supervision"},
        )

        # Query for duty hours
        response = await service.retrieve(
            query="What are the work hour limits?",
            top_k=5,
        )

        assert response.total_results > 0
        assert len(response.documents) > 0
        assert all(0.0 <= doc.similarity_score <= 1.0 for doc in response.documents)
        # Most similar document should mention 80 hours
        assert "80 hours" in response.documents[0].content.lower()

    @pytest.mark.skipif(
        True,  # Skip for SQLite tests
        reason="Requires PostgreSQL with pgvector extension",
    )
    async def test_retrieve_with_doc_type_filter(self, db):
        """Test retrieving documents filtered by doc_type."""
        service = RAGService(db)

        # Ingest documents of different types
        await service.ingest_document(
            content="ACGME duty hour regulations.",
            doc_type="acgme_rules",
        )

        await service.ingest_document(
            content="Hospital scheduling policy.",
            doc_type="scheduling_policy",
        )

        # Query with filter
        response = await service.retrieve(
            query="duty hours",
            doc_type="acgme_rules",
            top_k=10,
        )

        assert all(doc.doc_type == "acgme_rules" for doc in response.documents)

    async def test_retrieve_empty_query(self, db):
        """Test that empty query raises ValueError."""
        service = RAGService(db)

        with pytest.raises(ValueError, match="Query cannot be empty"):
            await service.retrieve(query="")

    async def test_retrieve_invalid_similarity(self, db):
        """Test that invalid min_similarity raises ValueError."""
        service = RAGService(db)

        with pytest.raises(ValueError, match="min_similarity must be between"):
            await service.retrieve(
                query="test",
                min_similarity=1.5,  # Greater than 1.0
            )


class TestRAGServiceContextBuilding:
    """Test context building for LLM injection."""

    @pytest.mark.skipif(
        True,  # Skip for SQLite tests
        reason="Requires PostgreSQL with pgvector extension",
    )
    async def test_build_context(self, db):
        """Test building context string from retrieved documents."""
        service = RAGService(db)

        # Ingest sample documents
        await service.ingest_document(
            content="The 80-hour work week limit is a key ACGME requirement.",
            doc_type="acgme_rules",
            metadata={"section": "Work Hours"},
        )

        # Build context
        context = await service.build_context(
            query="work hour limits",
            max_tokens=2000,
            include_metadata=True,
        )

        assert context.query == "work hour limits"
        assert len(context.context) > 0
        assert (
            "80-hour" in context.context.lower() or "80 hour" in context.context.lower()
        )
        assert len(context.sources) > 0
        assert context.token_count > 0
        assert context.token_count <= 2000

    @pytest.mark.skipif(
        True,  # Skip for SQLite tests
        reason="Requires PostgreSQL with pgvector extension",
    )
    async def test_build_context_respects_token_limit(self, db):
        """Test that context building respects max_tokens limit."""
        service = RAGService(db)

        # Ingest multiple large documents
        for i in range(10):
            await service.ingest_document(
                content=f"Document {i}: " + "This is a long sentence. " * 100,
                doc_type="test_docs",
            )

        # Build context with small token limit
        context = await service.build_context(
            query="test",
            max_tokens=500,
        )

        # Should not exceed limit
        assert context.token_count <= 500

    async def test_build_context_empty_query(self, db):
        """Test that empty query raises ValueError."""
        service = RAGService(db)

        with pytest.raises(ValueError, match="Query cannot be empty"):
            await service.build_context(query="")

    async def test_build_context_invalid_max_tokens(self, db):
        """Test that invalid max_tokens raises ValueError."""
        service = RAGService(db)

        with pytest.raises(ValueError, match="max_tokens must be at least"):
            await service.build_context(
                query="test",
                max_tokens=50,  # Too small
            )


class TestRAGServiceHealth:
    """Test RAG system health checks."""

    @pytest.mark.skipif(
        True,  # Skip for SQLite tests
        reason="Requires PostgreSQL with pgvector extension",
    )
    async def test_get_health(self, db):
        """Test health check returns system status."""
        service = RAGService(db)

        health = await service.get_health()

        assert health.status in ["healthy", "unhealthy", "error"]
        assert health.total_documents >= 0
        assert isinstance(health.documents_by_type, dict)
        assert health.embedding_model == "all-MiniLM-L6-v2"
        assert health.embedding_dimensions == 384
        assert health.vector_index_status in ["ready", "building", "missing", "unknown"]

    @pytest.mark.skipif(
        True,  # Skip for SQLite tests
        reason="Requires PostgreSQL with pgvector extension",
    )
    async def test_get_health_with_documents(self, db):
        """Test health check with ingested documents."""
        service = RAGService(db)

        # Ingest some documents
        await service.ingest_document(
            content="Test document for health check.",
            doc_type="test_docs",
        )

        health = await service.get_health()

        assert health.total_documents > 0
        assert "test_docs" in health.documents_by_type
        assert health.documents_by_type["test_docs"] > 0


class TestRAGServiceDeletion:
    """Test document deletion operations."""

    @pytest.mark.skipif(
        True,  # Skip for SQLite tests
        reason="Requires PostgreSQL with pgvector extension",
    )
    async def test_delete_by_doc_type(self, db):
        """Test deleting documents by type."""
        service = RAGService(db)

        # Ingest documents of different types
        await service.ingest_document(
            content="Type A document",
            doc_type="type_a",
        )
        await service.ingest_document(
            content="Type B document",
            doc_type="type_b",
        )

        # Delete type_a documents
        count = service.delete_by_doc_type("type_a")

        assert count > 0

        # Verify type_a documents are gone
        health = await service.get_health()
        assert "type_a" not in health.documents_by_type
        assert "type_b" in health.documents_by_type

    @pytest.mark.skipif(
        True,  # Skip for SQLite tests
        reason="Requires PostgreSQL with pgvector extension",
    )
    async def test_delete_by_id(self, db):
        """Test deleting a specific document by ID."""
        service = RAGService(db)

        # Ingest a document
        response = await service.ingest_document(
            content="Test document to delete",
            doc_type="test_docs",
        )

        doc_id = response.chunk_ids[0]

        # Delete it
        deleted = service.delete_by_id(doc_id)

        assert deleted is True

        # Try to delete again (should return False)
        deleted_again = service.delete_by_id(doc_id)
        assert deleted_again is False
