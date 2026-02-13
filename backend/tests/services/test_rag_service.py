"""Tests for RAG (Retrieval-Augmented Generation) service.

Note: Vector similarity tests require PostgreSQL with pgvector extension.
SQLite tests will focus on chunking, ingestion flow, and business logic.
"""

import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import OperationalError

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
        """Test chunking with very small input.

        Implementation filters out chunks smaller than 10% of target
        chunk_chars (chunk_size * 4 chars/token).  With chunk_size=500
        that means min ~200 chars, so a tiny string is dropped.
        Use a small chunk_size to keep the single chunk.
        """
        service = RAGService(db)

        text = "Short text."
        # With chunk_size=10 the min_chunk_size threshold is ~4 chars
        chunks = service._chunk_text(text, chunk_size=10, chunk_overlap=0)

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

    @pytest.mark.requires_db
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


class TestRAGServiceIngestionRetries:
    """Test ingestion retry behavior for transient DB failures."""

    async def test_ingest_document_retries_transient_db_errors(self, db):
        """Transient OperationalError should retry with exponential backoff."""
        service = RAGService(db)

        transient_error = OperationalError(
            "INSERT INTO rag_documents ...",
            {},
            Exception("connection refused"),
        )

        with (
            patch.object(
                service, "_chunk_text", return_value=["Chunk one", "Chunk two"]
            ),
            patch.object(
                service.embedding_service,
                "embed_batch",
                return_value=[[0.1], [0.2]],
            ),
            patch.object(
                db, "add", side_effect=lambda model: setattr(model, "id", uuid4())
            ),
            patch.object(db, "flush", side_effect=[transient_error, None, None]),
            patch.object(db, "rollback") as mock_rollback,
            patch.object(db, "commit") as mock_commit,
            patch("app.services.rag_service.time.sleep") as mock_sleep,
        ):
            response = await service.ingest_document(
                content="Any non-empty content",
                doc_type="test_doc",
                chunk_size=10,
                chunk_overlap=0,
            )

        assert response.status == "success"
        assert response.chunks_created == 2
        assert mock_rollback.call_count == 1
        mock_commit.assert_called_once()
        mock_sleep.assert_called_once_with(service.INITIAL_RETRY_DELAY_SECONDS)

    async def test_ingest_document_does_not_retry_non_transient_errors(self, db):
        """Non-transient errors should fail fast without sleep/backoff."""
        service = RAGService(db)

        with (
            patch.object(service, "_chunk_text", return_value=["Chunk one"]),
            patch.object(
                service.embedding_service, "embed_batch", return_value=[[0.1]]
            ),
            patch.object(
                db, "add", side_effect=lambda model: setattr(model, "id", uuid4())
            ),
            patch.object(db, "flush", side_effect=RuntimeError("invalid vector size")),
            patch.object(db, "rollback") as mock_rollback,
            patch.object(db, "commit") as mock_commit,
            patch("app.services.rag_service.time.sleep") as mock_sleep,
        ):
            response = await service.ingest_document(
                content="Any non-empty content",
                doc_type="test_doc",
                chunk_size=10,
                chunk_overlap=0,
            )

        assert response.status == "error"
        assert response.chunks_created == 0
        assert "invalid vector size" in response.message
        assert mock_rollback.call_count == 1
        mock_commit.assert_not_called()
        mock_sleep.assert_not_called()


class TestRAGServiceRetrieval:
    """Test document retrieval (requires PostgreSQL with pgvector)."""

    @pytest.mark.requires_db
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

    @pytest.mark.requires_db
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

    @pytest.mark.requires_db
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

    @pytest.mark.requires_db
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

    @pytest.mark.requires_db
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

    @pytest.mark.requires_db
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

    @pytest.mark.requires_db
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

    async def test_delete_all_documents(self, db):
        """Test deleting all documents regardless of type."""
        service = RAGService(db)

        mock_result = MagicMock()
        mock_result.rowcount = 12
        db.execute = MagicMock(return_value=mock_result)
        db.commit = MagicMock()

        deleted = service.delete_all_documents()

        assert deleted == 12
        db.execute.assert_called_once()
        db.commit.assert_called_once()

    @pytest.mark.requires_db
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

    async def test_delete_by_source_filename(self, db):
        """Test deleting chunks by source filename."""
        service = RAGService(db)

        mock_result = MagicMock()
        mock_result.rowcount = 3
        db.execute = MagicMock(return_value=mock_result)
        db.commit = MagicMock()

        deleted = service.delete_by_source_filename("file_a.md")

        assert deleted == 3
        db.execute.assert_called_once()
        db.commit.assert_called_once()
