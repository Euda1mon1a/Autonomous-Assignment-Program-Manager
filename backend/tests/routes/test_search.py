"""Tests for search API routes.

Tests the search functionality including:
- Full-text search across entities
- Quick search
- Entity-specific searches (people, rotations, procedures)
- Global search
- Autocomplete suggestions
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.models.user import User


class TestSearchRoutes:
    """Test suite for search API endpoints."""

    # ========================================================================
    # Authentication Tests
    # ========================================================================

    def test_search_requires_auth(self, client: TestClient):
        """Test that search requires authentication."""
        response = client.post(
            "/api/search",
            json={"query": "test", "entity_types": ["person"]},
        )
        assert response.status_code == 401

    def test_quick_search_requires_auth(self, client: TestClient):
        """Test that quick search requires authentication."""
        response = client.get("/api/search/quick?query=test")
        assert response.status_code == 401

    def test_people_search_requires_auth(self, client: TestClient):
        """Test that people search requires authentication."""
        response = client.post(
            "/api/search/people",
            json={"query": "dr smith"},
        )
        assert response.status_code == 401

    def test_rotations_search_requires_auth(self, client: TestClient):
        """Test that rotations search requires authentication."""
        response = client.post(
            "/api/search/rotations",
            json={"query": "cardiology"},
        )
        assert response.status_code == 401

    def test_procedures_search_requires_auth(self, client: TestClient):
        """Test that procedures search requires authentication."""
        response = client.post(
            "/api/search/procedures",
            json={"query": "colonoscopy"},
        )
        assert response.status_code == 401

    def test_global_search_requires_auth(self, client: TestClient):
        """Test that global search requires authentication."""
        response = client.post("/api/search/global?query=test")
        assert response.status_code == 401

    def test_suggest_post_requires_auth(self, client: TestClient):
        """Test that suggestions (POST) requires authentication."""
        response = client.post(
            "/api/search/suggest",
            json={"query": "sm"},
        )
        assert response.status_code == 401

    def test_suggest_get_requires_auth(self, client: TestClient):
        """Test that suggestions (GET) requires authentication."""
        response = client.get("/api/search/suggest?query=sm")
        assert response.status_code == 401

    # ========================================================================
    # Main Search Tests
    # ========================================================================

    @patch("app.api.routes.search.SearchService")
    def test_search_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful search."""
        mock_service = MagicMock()
        mock_service.search = AsyncMock(
            return_value={
                "items": [
                    {
                        "id": str(uuid4()),
                        "entity_type": "person",
                        "title": "Dr. Smith",
                        "description": "Faculty - Cardiology",
                        "score": 0.95,
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 20,
                "total_pages": 1,
                "facets": {"entity_type": {"person": 1}},
                "query": "smith",
            }
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/search",
            headers=auth_headers,
            json={
                "query": "smith",
                "entity_types": ["person"],
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Dr. Smith"

    @patch("app.api.routes.search.SearchService")
    def test_search_with_filters(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test search with filters and pagination."""
        mock_service = MagicMock()
        mock_service.search = AsyncMock(
            return_value={
                "items": [],
                "total": 0,
                "page": 2,
                "page_size": 10,
                "total_pages": 0,
                "query": "test",
            }
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/search",
            headers=auth_headers,
            json={
                "query": "test",
                "entity_types": ["person", "rotation"],
                "filters": {"department": "cardiology"},
                "page": 2,
                "page_size": 10,
                "sort_by": "name",
                "sort_order": "asc",
            },
        )
        assert response.status_code == 200

    @patch("app.api.routes.search.SearchService")
    def test_search_invalid_query(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test search with invalid query."""
        mock_service = MagicMock()
        mock_service.search = AsyncMock(side_effect=ValueError("Invalid query"))
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/search",
            headers=auth_headers,
            json={"query": "*", "entity_types": ["person"]},
        )
        assert response.status_code == 400

    # ========================================================================
    # Quick Search Tests
    # ========================================================================

    @patch("app.api.routes.search.SearchService")
    def test_quick_search_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful quick search."""
        mock_indexer = MagicMock()
        mock_indexer.quick_search = AsyncMock(
            return_value=[
                {
                    "id": str(uuid4()),
                    "entity_type": "person",
                    "title": "Dr. Johnson",
                    "score": 0.9,
                }
            ]
        )
        mock_service = MagicMock()
        mock_service.indexer = mock_indexer
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/search/quick?query=john&entity_type=person&limit=5",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert data["query"] == "john"
        assert data["entity_type"] == "person"

    @patch("app.api.routes.search.SearchService")
    def test_quick_search_default_params(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test quick search with default parameters."""
        mock_indexer = MagicMock()
        mock_indexer.quick_search = AsyncMock(return_value=[])
        mock_service = MagicMock()
        mock_service.indexer = mock_indexer
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/search/quick?query=test",
            headers=auth_headers,
        )
        assert response.status_code == 200

        mock_indexer.quick_search.assert_called_once_with(
            query_string="test",
            entity_type="person",
            limit=10,
        )

    # ========================================================================
    # People Search Tests
    # ========================================================================

    @patch("app.api.routes.search.SearchService")
    def test_search_people_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful people search."""
        mock_service = MagicMock()
        mock_service.search_people = AsyncMock(
            return_value={
                "items": [
                    {
                        "id": str(uuid4()),
                        "entity_type": "person",
                        "title": "Dr. Smith",
                        "description": "PGY-2 Resident",
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 20,
                "total_pages": 1,
                "query": "smith",
            }
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/search/people",
            headers=auth_headers,
            json={"query": "smith"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 1

    @patch("app.api.routes.search.SearchService")
    def test_search_people_with_filters(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test people search with type and PGY level filters."""
        mock_service = MagicMock()
        mock_service.search_people = AsyncMock(
            return_value={
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
                "total_pages": 0,
                "query": "test",
            }
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/search/people",
            headers=auth_headers,
            json={
                "query": "test",
                "type": "resident",
                "pgy_level": 2,
            },
        )
        assert response.status_code == 200

        mock_service.search_people.assert_called_once()

    # ========================================================================
    # Rotations Search Tests
    # ========================================================================

    @patch("app.api.routes.search.SearchService")
    def test_search_rotations_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful rotations search."""
        mock_indexer = MagicMock()
        mock_indexer.search_rotations = AsyncMock(
            return_value={
                "items": [
                    {
                        "id": str(uuid4()),
                        "entity_type": "rotation",
                        "title": "Cardiology Clinic",
                        "description": "Outpatient cardiology rotation",
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 20,
                "total_pages": 1,
                "query": "cardiology",
            }
        )
        mock_service = MagicMock()
        mock_service.indexer = mock_indexer
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/search/rotations",
            headers=auth_headers,
            json={"query": "cardiology"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 1

    @patch("app.api.routes.search.SearchService")
    def test_search_rotations_with_category(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test rotations search with category filter."""
        mock_indexer = MagicMock()
        mock_indexer.search_rotations = AsyncMock(
            return_value={
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
                "total_pages": 0,
                "query": "test",
            }
        )
        mock_service = MagicMock()
        mock_service.indexer = mock_indexer
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/search/rotations",
            headers=auth_headers,
            json={"query": "test", "category": "outpatient"},
        )
        assert response.status_code == 200

    # ========================================================================
    # Procedures Search Tests
    # ========================================================================

    @patch("app.api.routes.search.SearchService")
    def test_search_procedures_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful procedures search."""
        mock_indexer = MagicMock()
        mock_indexer.search_procedures = AsyncMock(
            return_value={
                "items": [
                    {
                        "id": str(uuid4()),
                        "entity_type": "procedure",
                        "title": "Colonoscopy",
                        "description": "CPT: 45378",
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 20,
                "total_pages": 1,
                "query": "45378",
            }
        )
        mock_service = MagicMock()
        mock_service.indexer = mock_indexer
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/search/procedures",
            headers=auth_headers,
            json={"query": "45378"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 1

    # ========================================================================
    # Global Search Tests
    # ========================================================================

    @patch("app.api.routes.search.SearchService")
    def test_global_search_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful global search across all entity types."""
        mock_indexer = MagicMock()
        mock_indexer.global_search = AsyncMock(
            return_value={
                "items": [
                    {
                        "id": str(uuid4()),
                        "entity_type": "person",
                        "title": "Dr. Test",
                    },
                    {
                        "id": str(uuid4()),
                        "entity_type": "rotation",
                        "title": "Test Rotation",
                    },
                ],
                "total": 2,
                "page": 1,
                "page_size": 20,
                "total_pages": 1,
                "facets": {"entity_type": {"person": 1, "rotation": 1}},
                "query": "test",
            }
        )
        mock_service = MagicMock()
        mock_service.indexer = mock_indexer
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/search/global?query=test",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 2

    @patch("app.api.routes.search.SearchService")
    def test_global_search_pagination(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test global search with pagination."""
        mock_indexer = MagicMock()
        mock_indexer.global_search = AsyncMock(
            return_value={
                "items": [],
                "total": 100,
                "page": 3,
                "page_size": 25,
                "total_pages": 4,
                "query": "test",
            }
        )
        mock_service = MagicMock()
        mock_service.indexer = mock_indexer
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/search/global?query=test&page=3&page_size=25",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["page"] == 3
        assert data["page_size"] == 25

    # ========================================================================
    # Suggestions Tests
    # ========================================================================

    @patch("app.api.routes.search.SearchService")
    def test_suggest_post_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test POST suggestions endpoint."""
        mock_service = MagicMock()
        mock_service.suggest = AsyncMock(
            return_value=["Smith, John", "Smith, Jane", "Smithson, Robert"]
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/search/suggest",
            headers=auth_headers,
            json={
                "query": "smi",
                "entity_type": "person",
                "limit": 5,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) == 3
        assert data["query"] == "smi"

    @patch("app.api.routes.search.SearchService")
    def test_suggest_get_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test GET suggestions endpoint."""
        mock_service = MagicMock()
        mock_service.suggest = AsyncMock(
            return_value=["Cardiology", "Cardiology Clinic"]
        )
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/search/suggest?query=card&entity_type=rotation&limit=3",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "suggestions" in data
        assert data["entity_type"] == "rotation"

    @patch("app.api.routes.search.SearchService")
    def test_suggest_empty_results(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test suggestions with no matching results."""
        mock_service = MagicMock()
        mock_service.suggest = AsyncMock(return_value=[])
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/search/suggest?query=zzz",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["suggestions"] == []

    # ========================================================================
    # Error Handling Tests
    # ========================================================================

    @patch("app.api.routes.search.SearchService")
    def test_search_server_error(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test search handles server errors gracefully."""
        mock_service = MagicMock()
        mock_service.search = AsyncMock(side_effect=Exception("Database error"))
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/search",
            headers=auth_headers,
            json={"query": "test", "entity_types": ["person"]},
        )
        assert response.status_code == 500
        assert "Search failed" in response.json()["detail"]

    @patch("app.api.routes.search.SearchService")
    def test_suggest_server_error(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test suggestions handle server errors gracefully."""
        mock_service = MagicMock()
        mock_service.suggest = AsyncMock(side_effect=Exception("Index error"))
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/search/suggest?query=test",
            headers=auth_headers,
        )
        assert response.status_code == 500
        assert "failed" in response.json()["detail"].lower()
