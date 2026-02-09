"""Tests for RAG schemas (field_validators, Field bounds, defaults, nested)."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.rag import (
    DocumentIngestRequest,
    RAGRetrievalRequest,
    ContextBuildRequest,
    DocumentChunk,
    RetrievedDocument,
    IngestResponse,
    RetrievalResponse,
    RAGContext,
    RAGHealthResponse,
)


class TestDocumentIngestRequest:
    def test_valid_defaults(self):
        r = DocumentIngestRequest(content="Test content", doc_type="acgme_rules")
        assert r.metadata == {}
        assert r.chunk_size == 500
        assert r.chunk_overlap == 50

    def test_full(self):
        r = DocumentIngestRequest(
            content="Test content",
            doc_type="scheduling_policy",
            metadata={"source_file": "policy.md"},
            chunk_size=1000,
            chunk_overlap=100,
        )
        assert r.chunk_size == 1000
        assert r.metadata["source_file"] == "policy.md"

    # --- content min_length=1 ---

    def test_content_empty(self):
        with pytest.raises(ValidationError):
            DocumentIngestRequest(content="", doc_type="acgme_rules")

    # --- doc_type field_validator ---

    def test_valid_doc_types(self):
        valid_types = [
            "acgme_rules",
            "scheduling_policy",
            "user_guide",
            "technical_doc",
            "meeting_notes",
            "research_paper",
            "clinical_guideline",
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
            "other",
        ]
        for dt in valid_types:
            r = DocumentIngestRequest(content="content", doc_type=dt)
            assert r.doc_type == dt

    def test_doc_type_case_insensitive(self):
        r = DocumentIngestRequest(content="content", doc_type="ACGME_RULES")
        assert r.doc_type == "acgme_rules"

    def test_invalid_doc_type(self):
        with pytest.raises(ValidationError, match="Invalid doc_type"):
            DocumentIngestRequest(content="content", doc_type="invalid_type")

    # --- doc_type min_length=1, max_length=100 ---

    def test_doc_type_empty(self):
        with pytest.raises(ValidationError):
            DocumentIngestRequest(content="content", doc_type="")

    # --- chunk_size ge=100, le=2000 ---

    def test_chunk_size_below_min(self):
        with pytest.raises(ValidationError):
            DocumentIngestRequest(
                content="content", doc_type="acgme_rules", chunk_size=99
            )

    def test_chunk_size_above_max(self):
        with pytest.raises(ValidationError):
            DocumentIngestRequest(
                content="content", doc_type="acgme_rules", chunk_size=2001
            )

    def test_chunk_size_boundaries(self):
        r = DocumentIngestRequest(
            content="content", doc_type="acgme_rules", chunk_size=100
        )
        assert r.chunk_size == 100
        r = DocumentIngestRequest(
            content="content", doc_type="acgme_rules", chunk_size=2000
        )
        assert r.chunk_size == 2000

    # --- chunk_overlap ge=0, le=500 ---

    def test_chunk_overlap_below_min(self):
        with pytest.raises(ValidationError):
            DocumentIngestRequest(
                content="content", doc_type="acgme_rules", chunk_overlap=-1
            )

    def test_chunk_overlap_above_max(self):
        with pytest.raises(ValidationError):
            DocumentIngestRequest(
                content="content", doc_type="acgme_rules", chunk_overlap=501
            )


class TestRAGRetrievalRequest:
    def test_defaults(self):
        r = RAGRetrievalRequest(query="ACGME 80 hour rule")
        assert r.top_k == 5
        assert r.doc_type is None
        assert r.min_similarity == 0.5
        assert r.metadata_filters == {}

    # --- query min_length=1 ---

    def test_query_empty(self):
        with pytest.raises(ValidationError):
            RAGRetrievalRequest(query="")

    # --- top_k ge=1, le=50 ---

    def test_top_k_below_min(self):
        with pytest.raises(ValidationError):
            RAGRetrievalRequest(query="test", top_k=0)

    def test_top_k_above_max(self):
        with pytest.raises(ValidationError):
            RAGRetrievalRequest(query="test", top_k=51)

    # --- min_similarity ge=0.0, le=1.0 ---

    def test_min_similarity_below_min(self):
        with pytest.raises(ValidationError):
            RAGRetrievalRequest(query="test", min_similarity=-0.1)

    def test_min_similarity_above_max(self):
        with pytest.raises(ValidationError):
            RAGRetrievalRequest(query="test", min_similarity=1.1)


class TestContextBuildRequest:
    def test_defaults(self):
        r = ContextBuildRequest(query="What is the 80 hour rule?")
        assert r.max_tokens == 2000
        assert r.doc_type is None
        assert r.include_metadata is True

    # --- max_tokens ge=100, le=8000 ---

    def test_max_tokens_below_min(self):
        with pytest.raises(ValidationError):
            ContextBuildRequest(query="test", max_tokens=99)

    def test_max_tokens_above_max(self):
        with pytest.raises(ValidationError):
            ContextBuildRequest(query="test", max_tokens=8001)

    def test_max_tokens_boundaries(self):
        r = ContextBuildRequest(query="test", max_tokens=100)
        assert r.max_tokens == 100
        r = ContextBuildRequest(query="test", max_tokens=8000)
        assert r.max_tokens == 8000


class TestDocumentChunk:
    def test_valid(self):
        r = DocumentChunk(
            id=uuid4(),
            content="ACGME requires...",
            doc_type="acgme_rules",
            created_at=datetime(2026, 3, 1),
        )
        assert r.metadata == {}

    def test_with_metadata(self):
        r = DocumentChunk(
            id=uuid4(),
            content="Policy section 3...",
            doc_type="scheduling_policy",
            metadata={"section": "3", "page": 5},
            created_at=datetime(2026, 3, 1),
        )
        assert r.metadata["page"] == 5


class TestRetrievedDocument:
    def test_valid(self):
        r = RetrievedDocument(
            id=uuid4(),
            content="ACGME 80-hour rule...",
            doc_type="acgme_rules",
            similarity_score=0.92,
            created_at=datetime(2026, 3, 1),
        )
        assert r.similarity_score == 0.92
        assert r.metadata == {}

    # --- similarity_score ge=0.0, le=1.0 ---

    def test_similarity_below_min(self):
        with pytest.raises(ValidationError):
            RetrievedDocument(
                id=uuid4(),
                content="test",
                doc_type="other",
                similarity_score=-0.1,
                created_at=datetime(2026, 3, 1),
            )

    def test_similarity_above_max(self):
        with pytest.raises(ValidationError):
            RetrievedDocument(
                id=uuid4(),
                content="test",
                doc_type="other",
                similarity_score=1.1,
                created_at=datetime(2026, 3, 1),
            )


class TestIngestResponse:
    def test_valid(self):
        r = IngestResponse(
            status="success",
            chunks_created=5,
            doc_type="acgme_rules",
        )
        assert r.chunk_ids == []
        assert r.message == ""

    def test_with_ids(self):
        ids = [uuid4(), uuid4()]
        r = IngestResponse(
            status="success",
            chunks_created=2,
            chunk_ids=ids,
            doc_type="user_guide",
            message="Ingested successfully",
        )
        assert len(r.chunk_ids) == 2


class TestRetrievalResponse:
    def test_valid(self):
        r = RetrievalResponse(
            query="ACGME rules",
            documents=[],
            total_results=0,
            execution_time_ms=12.5,
        )
        assert r.total_results == 0
        assert r.execution_time_ms == 12.5


class TestRAGContext:
    def test_valid(self):
        r = RAGContext(
            query="What is the 80 hour rule?",
            context="The ACGME 80-hour rule states...",
            token_count=150,
        )
        assert r.sources == []
        assert r.metadata == {}

    def test_with_sources(self):
        doc = RetrievedDocument(
            id=uuid4(),
            content="80-hour rule...",
            doc_type="acgme_rules",
            similarity_score=0.95,
            created_at=datetime(2026, 3, 1),
        )
        r = RAGContext(
            query="80 hour rule",
            context="Context...",
            sources=[doc],
            token_count=200,
            metadata={"retrieval_ms": 15.0},
        )
        assert len(r.sources) == 1


class TestRAGHealthResponse:
    def test_valid(self):
        r = RAGHealthResponse(
            status="healthy",
            total_documents=67,
            documents_by_type={"acgme_rules": 10, "scheduling_policy": 15},
            embedding_model="text-embedding-3-small",
            embedding_dimensions=1536,
            vector_index_status="ready",
        )
        assert r.recommendations == []

    def test_with_recommendations(self):
        r = RAGHealthResponse(
            status="unhealthy",
            total_documents=0,
            documents_by_type={},
            embedding_model="text-embedding-3-small",
            embedding_dimensions=1536,
            vector_index_status="missing",
            recommendations=["Ingest ACGME rules", "Build vector index"],
        )
        assert len(r.recommendations) == 2
