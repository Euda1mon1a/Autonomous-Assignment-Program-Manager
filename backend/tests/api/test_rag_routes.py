"""Tests for RAG (Retrieval-Augmented Generation) API routes.

Tests the RAG endpoints for:
- Health check
- Document retrieval with authentication
- Category filtering
- Input validation
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.rag import (
    RAGHealthResponse,
    RetrievalResponse,
    RetrievedDocument,
)


# =============================================================================
# Health Endpoint Tests
# =============================================================================


class TestRAGHealth:
    """Tests for RAG health endpoint."""

    def test_rag_health_requires_auth(self, client: TestClient):
        """Test health endpoint requires authentication."""
        response = client.get("/api/rag/health")

        assert response.status_code == 401

    def test_rag_health_returns_stats(
        self, client: TestClient, auth_headers: dict, admin_user: User
    ):
        """Test health endpoint returns chunk count and statistics."""
        # Mock the RAG service to avoid needing pgvector in tests
        mock_health_response = RAGHealthResponse(
            status="healthy",
            total_documents=42,
            documents_by_type={
                "acgme_rules": 15,
                "scheduling_policy": 10,
                "user_guide": 17,
            },
            embedding_model="all-MiniLM-L6-v2",
            embedding_dimensions=384,
            vector_index_status="ready",
            recommendations=[],
        )

        with patch("app.api.routes.rag.RAGService") as MockRAGService:
            mock_service = MagicMock()
            mock_service.get_health = AsyncMock(return_value=mock_health_response)
            MockRAGService.return_value = mock_service

            response = client.get("/api/rag/health", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "status" in data
        assert data["status"] == "healthy"
        assert "total_documents" in data
        assert data["total_documents"] == 42
        assert "documents_by_type" in data
        assert data["documents_by_type"]["acgme_rules"] == 15
        assert "embedding_model" in data
        assert "embedding_dimensions" in data
        assert "vector_index_status" in data
        assert data["vector_index_status"] == "ready"


# =============================================================================
# Retrieval Endpoint Tests
# =============================================================================


class TestRAGRetrieve:
    """Tests for RAG retrieve endpoint."""

    def test_rag_retrieve_requires_auth(self, client: TestClient):
        """Test unauthenticated request returns 401."""
        response = client.post(
            "/api/rag/retrieve",
            json={"query": "What are the ACGME work hour limits?"},
        )

        assert response.status_code == 401

    def test_rag_retrieve_returns_results(
        self, client: TestClient, auth_headers: dict, admin_user: User
    ):
        """Test valid query returns relevant chunks."""
        # Create mock retrieved documents
        mock_docs = [
            RetrievedDocument(
                id=uuid4(),
                content="ACGME limits residents to 80 hours per week.",
                doc_type="acgme_rules",
                metadata={"source": "ACGME guidelines"},
                similarity_score=0.95,
                created_at=datetime.utcnow(),
            ),
            RetrievedDocument(
                id=uuid4(),
                content="Residents must have one day off per week.",
                doc_type="acgme_rules",
                metadata={"source": "ACGME guidelines"},
                similarity_score=0.87,
                created_at=datetime.utcnow(),
            ),
        ]

        mock_retrieval_response = RetrievalResponse(
            query="What are the ACGME work hour limits?",
            documents=mock_docs,
            total_results=2,
            execution_time_ms=45.2,
        )

        with patch("app.api.routes.rag.RAGService") as MockRAGService:
            mock_service = MagicMock()
            mock_service.retrieve = AsyncMock(return_value=mock_retrieval_response)
            MockRAGService.return_value = mock_service

            response = client.post(
                "/api/rag/retrieve",
                json={"query": "What are the ACGME work hour limits?"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "query" in data
        assert data["query"] == "What are the ACGME work hour limits?"
        assert "documents" in data
        assert len(data["documents"]) == 2
        assert "total_results" in data
        assert data["total_results"] == 2
        assert "execution_time_ms" in data

        # Verify document structure
        first_doc = data["documents"][0]
        assert "id" in first_doc
        assert "content" in first_doc
        assert "doc_type" in first_doc
        assert first_doc["doc_type"] == "acgme_rules"
        assert "similarity_score" in first_doc
        assert first_doc["similarity_score"] == 0.95

    def test_rag_retrieve_filters_by_category(
        self, client: TestClient, auth_headers: dict, admin_user: User
    ):
        """Test category filter works correctly."""
        # Create mock response with only scheduling_policy documents
        mock_docs = [
            RetrievedDocument(
                id=uuid4(),
                content="Faculty scheduling must maintain N-1 coverage.",
                doc_type="scheduling_policy",
                metadata={"section": "coverage requirements"},
                similarity_score=0.92,
                created_at=datetime.utcnow(),
            ),
        ]

        mock_retrieval_response = RetrievalResponse(
            query="scheduling coverage",
            documents=mock_docs,
            total_results=1,
            execution_time_ms=32.5,
        )

        with patch("app.api.routes.rag.RAGService") as MockRAGService:
            mock_service = MagicMock()
            mock_service.retrieve = AsyncMock(return_value=mock_retrieval_response)
            MockRAGService.return_value = mock_service

            response = client.post(
                "/api/rag/retrieve",
                json={
                    "query": "scheduling coverage",
                    "doc_type": "scheduling_policy",
                    "top_k": 5,
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()

        # Verify filter was applied (mock was called with doc_type)
        mock_service.retrieve.assert_called_once()
        call_kwargs = mock_service.retrieve.call_args[1]
        assert call_kwargs["doc_type"] == "scheduling_policy"

        # Verify response only contains scheduling_policy docs
        assert all(doc["doc_type"] == "scheduling_policy" for doc in data["documents"])

    def test_rag_retrieve_empty_query(
        self, client: TestClient, auth_headers: dict, admin_user: User
    ):
        """Test empty query returns 400."""
        # Test with empty string
        response = client.post(
            "/api/rag/retrieve",
            json={"query": ""},
            headers=auth_headers,
        )

        # Pydantic validation should catch empty string (min_length=1)
        assert response.status_code == 422

    def test_rag_retrieve_whitespace_only_query(
        self, client: TestClient, auth_headers: dict, admin_user: User
    ):
        """Test whitespace-only query returns 400."""
        # Whitespace-only query should fail validation in service
        with patch("app.api.routes.rag.RAGService") as MockRAGService:
            mock_service = MagicMock()
            mock_service.retrieve = AsyncMock(
                side_effect=ValueError("Query cannot be empty")
            )
            MockRAGService.return_value = mock_service

            response = client.post(
                "/api/rag/retrieve",
                json={"query": "   "},  # Whitespace only
                headers=auth_headers,
            )

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_rag_retrieve_with_similarity_threshold(
        self, client: TestClient, auth_headers: dict, admin_user: User
    ):
        """Test min_similarity parameter is respected."""
        mock_retrieval_response = RetrievalResponse(
            query="test query",
            documents=[],  # No documents meet the high threshold
            total_results=0,
            execution_time_ms=25.0,
        )

        with patch("app.api.routes.rag.RAGService") as MockRAGService:
            mock_service = MagicMock()
            mock_service.retrieve = AsyncMock(return_value=mock_retrieval_response)
            MockRAGService.return_value = mock_service

            response = client.post(
                "/api/rag/retrieve",
                json={
                    "query": "test query",
                    "min_similarity": 0.9,  # High threshold
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()

        # Verify min_similarity was passed to service
        mock_service.retrieve.assert_called_once()
        call_kwargs = mock_service.retrieve.call_args[1]
        assert call_kwargs["min_similarity"] == 0.9


# =============================================================================
# Ingest Endpoint Tests
# =============================================================================


class TestRAGIngest:
    """Tests for RAG ingest endpoint."""

    def test_rag_ingest_requires_auth(self, client: TestClient):
        """Test ingest endpoint requires authentication."""
        response = client.post(
            "/api/rag/ingest",
            json={
                "content": "Test document content.",
                "doc_type": "user_guide",
            },
        )

        assert response.status_code == 401

    def test_rag_ingest_success(
        self, client: TestClient, auth_headers: dict, admin_user: User
    ):
        """Test successful document ingestion."""
        from app.schemas.rag import IngestResponse

        mock_ingest_response = IngestResponse(
            status="success",
            chunks_created=3,
            chunk_ids=[uuid4(), uuid4(), uuid4()],
            doc_type="user_guide",
            message="Successfully ingested 3 chunks",
        )

        with patch("app.api.routes.rag.RAGService") as MockRAGService:
            mock_service = MagicMock()
            mock_service.ingest_document = AsyncMock(return_value=mock_ingest_response)
            MockRAGService.return_value = mock_service

            response = client.post(
                "/api/rag/ingest",
                json={
                    "content": "This is a test document with enough content to be chunked into multiple pieces for the RAG system.",
                    "doc_type": "user_guide",
                    "metadata": {"author": "Test Author"},
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["chunks_created"] == 3
        assert len(data["chunk_ids"]) == 3
        assert data["doc_type"] == "user_guide"

    def test_rag_ingest_invalid_doc_type(
        self, client: TestClient, auth_headers: dict, admin_user: User
    ):
        """Test ingestion with invalid doc_type returns 422."""
        response = client.post(
            "/api/rag/ingest",
            json={
                "content": "Test document content.",
                "doc_type": "invalid_type",  # Not in allowed list
            },
            headers=auth_headers,
        )

        # Pydantic validation should catch invalid doc_type
        assert response.status_code == 422


# =============================================================================
# Context Endpoint Tests
# =============================================================================


class TestRAGContext:
    """Tests for RAG context building endpoint."""

    def test_rag_context_requires_auth(self, client: TestClient):
        """Test context endpoint requires authentication."""
        response = client.post(
            "/api/rag/context",
            json={"query": "What are the scheduling rules?"},
        )

        assert response.status_code == 401

    def test_rag_context_success(
        self, client: TestClient, auth_headers: dict, admin_user: User
    ):
        """Test successful context building."""
        from app.schemas.rag import RAGContext

        mock_context_response = RAGContext(
            query="What are the scheduling rules?",
            context="# Relevant Context for Query: What are the scheduling rules?\n\nScheduling must follow ACGME guidelines...",
            sources=[
                RetrievedDocument(
                    id=uuid4(),
                    content="Scheduling must follow ACGME guidelines.",
                    doc_type="scheduling_policy",
                    metadata={},
                    similarity_score=0.88,
                    created_at=datetime.utcnow(),
                )
            ],
            token_count=150,
            metadata={
                "doc_type_filter": None,
                "include_metadata": True,
                "max_tokens": 2000,
            },
        )

        with patch("app.api.routes.rag.RAGService") as MockRAGService:
            mock_service = MagicMock()
            mock_service.build_context = AsyncMock(return_value=mock_context_response)
            MockRAGService.return_value = mock_service

            response = client.post(
                "/api/rag/context",
                json={
                    "query": "What are the scheduling rules?",
                    "max_tokens": 2000,
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()

        assert "query" in data
        assert data["query"] == "What are the scheduling rules?"
        assert "context" in data
        assert "sources" in data
        assert "token_count" in data
        assert data["token_count"] == 150


# =============================================================================
# Stats Endpoint Tests
# =============================================================================


class TestRAGStats:
    """Tests for RAG stats endpoint."""

    def test_rag_stats_requires_auth(self, client: TestClient):
        """Test stats endpoint requires authentication."""
        response = client.get("/api/rag/stats")

        assert response.status_code == 401

    def test_rag_stats_returns_summary(
        self, client: TestClient, auth_headers: dict, admin_user: User
    ):
        """Test stats endpoint returns summary statistics."""
        mock_health_response = RAGHealthResponse(
            status="healthy",
            total_documents=100,
            documents_by_type={
                "acgme_rules": 30,
                "scheduling_policy": 40,
                "user_guide": 30,
            },
            embedding_model="all-MiniLM-L6-v2",
            embedding_dimensions=384,
            vector_index_status="ready",
            recommendations=[],
        )

        with patch("app.api.routes.rag.RAGService") as MockRAGService:
            mock_service = MagicMock()
            mock_service.get_health = AsyncMock(return_value=mock_health_response)
            MockRAGService.return_value = mock_service

            response = client.get("/api/rag/stats", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert "total_chunks" in data
        assert data["total_chunks"] == 100
        assert "categories" in data
        assert "acgme_rules" in data["categories"]
        assert "documents_by_category" in data
        assert "status" in data
        assert data["status"] == "healthy"


# =============================================================================
# Delete Endpoint Tests
# =============================================================================


class TestRAGDelete:
    """Tests for RAG delete endpoint."""

    def test_rag_delete_requires_auth(self, client: TestClient):
        """Test delete endpoint requires authentication."""
        response = client.delete("/api/rag/documents/acgme_rules")

        assert response.status_code == 401

    def test_rag_delete_by_type_success(
        self, client: TestClient, auth_headers: dict, admin_user: User
    ):
        """Test successful deletion by document type."""
        with patch("app.api.routes.rag.RAGService") as MockRAGService:
            mock_service = MagicMock()
            mock_service.delete_by_doc_type = MagicMock(return_value=15)
            MockRAGService.return_value = mock_service

            response = client.delete(
                "/api/rag/documents/acgme_rules",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()

        assert data["deleted_count"] == 15
        assert data["doc_type"] == "acgme_rules"


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestRAGErrorHandling:
    """Tests for RAG endpoint error handling."""

    def test_rag_retrieve_service_error(
        self, client: TestClient, auth_headers: dict, admin_user: User
    ):
        """Test retrieval handles service errors gracefully."""
        with patch("app.api.routes.rag.RAGService") as MockRAGService:
            mock_service = MagicMock()
            mock_service.retrieve = AsyncMock(
                side_effect=Exception("Database connection failed")
            )
            MockRAGService.return_value = mock_service

            response = client.post(
                "/api/rag/retrieve",
                json={"query": "test query"},
                headers=auth_headers,
            )

        # Should return 500 with generic error message
        assert response.status_code == 500
        assert "Retrieval failed" in response.json()["detail"]

    def test_rag_health_service_error(
        self, client: TestClient, auth_headers: dict, admin_user: User
    ):
        """Test health check handles service errors gracefully."""
        with patch("app.api.routes.rag.RAGService") as MockRAGService:
            mock_service = MagicMock()
            mock_service.get_health = AsyncMock(
                side_effect=Exception("Vector extension not found")
            )
            MockRAGService.return_value = mock_service

            response = client.get("/api/rag/health", headers=auth_headers)

        # Should return 500 with generic error message
        assert response.status_code == 500
        assert "Health check failed" in response.json()["detail"]
