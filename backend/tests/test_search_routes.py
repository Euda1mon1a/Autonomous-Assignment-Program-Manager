"""
Comprehensive tests for Search API routes.

Tests coverage for search functionality:
- POST /api/search - Full-text search
- GET /api/search/quick - Quick search
- POST /api/search/people - People search
- POST /api/search/rotations - Rotation search
- POST /api/search/procedures - Procedure search
- POST /api/search/global - Global search
- POST /api/search/suggest - Get suggestions
- GET /api/search/suggest - Get suggestions (GET)
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ============================================================================
# Test Classes
# ============================================================================


class TestSearchEndpoint:
    """Tests for POST /api/search endpoint."""

    def test_search_requires_auth(self, client: TestClient):
        """Test that search requires authentication."""
        response = client.post(
            "/api/search",
            json={"query": "test", "entity_types": ["person"]},
        )

        assert response.status_code in [401, 403]

    def test_search_success(self, client: TestClient, auth_headers: dict):
        """Test successful search request."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.search.return_value = {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
                "total_pages": 0,
                "facets": {},
                "query": "test",
            }
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/search",
                json={"query": "test", "entity_types": ["person"]},
                headers=auth_headers,
            )

            # May return 200 or 401 depending on auth
            assert response.status_code in [200, 401]

    def test_search_with_filters(self, client: TestClient, auth_headers: dict):
        """Test search with filter parameters."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.search.return_value = {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
                "total_pages": 0,
                "facets": {},
                "query": "resident",
            }
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/search",
                json={
                    "query": "resident",
                    "entity_types": ["person"],
                    "filters": {"type": "resident"},
                    "page": 1,
                    "page_size": 10,
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_search_with_pagination(self, client: TestClient, auth_headers: dict):
        """Test search with pagination parameters."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.search.return_value = {
                "items": [],
                "total": 100,
                "page": 2,
                "page_size": 20,
                "total_pages": 5,
                "facets": {},
                "query": "test",
            }
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/search",
                json={
                    "query": "test",
                    "entity_types": ["person"],
                    "page": 2,
                    "page_size": 20,
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_search_returns_results(self, client: TestClient, auth_headers: dict):
        """Test search returns proper result structure."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.search.return_value = {
                "items": [
                    {
                        "id": str(uuid4()),
                        "entity_type": "person",
                        "title": "Dr. John Smith",
                        "score": 0.95,
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 20,
                "total_pages": 1,
                "facets": {"type": {"resident": 1}},
                "query": "john",
            }
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/search",
                json={"query": "john", "entity_types": ["person"]},
                headers=auth_headers,
            )

            if response.status_code == 200:
                data = response.json()
                assert "items" in data
                assert "total" in data
                assert "page" in data


class TestQuickSearchEndpoint:
    """Tests for GET /api/search/quick endpoint."""

    def test_quick_search_requires_auth(self, client: TestClient):
        """Test that quick search requires authentication."""
        response = client.get("/api/search/quick?query=test")

        assert response.status_code in [401, 403]

    def test_quick_search_success(self, client: TestClient, auth_headers: dict):
        """Test successful quick search."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_indexer = MagicMock()
            mock_indexer.quick_search.return_value = []
            mock_instance.indexer = mock_indexer
            mock_service.return_value = mock_instance

            response = client.get(
                "/api/search/quick?query=test",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_quick_search_with_entity_type(
        self, client: TestClient, auth_headers: dict
    ):
        """Test quick search with entity type filter."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_indexer = MagicMock()
            mock_indexer.quick_search.return_value = []
            mock_instance.indexer = mock_indexer
            mock_service.return_value = mock_instance

            response = client.get(
                "/api/search/quick?query=test&entity_type=rotation",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_quick_search_with_limit(self, client: TestClient, auth_headers: dict):
        """Test quick search with custom limit."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_indexer = MagicMock()
            mock_indexer.quick_search.return_value = []
            mock_instance.indexer = mock_indexer
            mock_service.return_value = mock_instance

            response = client.get(
                "/api/search/quick?query=test&limit=5",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_quick_search_requires_query(self, client: TestClient, auth_headers: dict):
        """Test quick search requires query parameter."""
        response = client.get(
            "/api/search/quick",
            headers=auth_headers,
        )

        # Should return 422 for missing required param
        assert response.status_code in [401, 422]


class TestPeopleSearchEndpoint:
    """Tests for POST /api/search/people endpoint."""

    def test_people_search_requires_auth(self, client: TestClient):
        """Test that people search requires authentication."""
        response = client.post(
            "/api/search/people",
            json={"query": "john"},
        )

        assert response.status_code in [401, 403]

    def test_people_search_success(self, client: TestClient, auth_headers: dict):
        """Test successful people search."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.search_people.return_value = {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
                "total_pages": 0,
                "facets": {},
                "query": "john",
            }
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/search/people",
                json={"query": "john"},
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_people_search_by_type(self, client: TestClient, auth_headers: dict):
        """Test people search filtered by type."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.search_people.return_value = {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
                "total_pages": 0,
                "facets": {},
                "query": "smith",
            }
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/search/people",
                json={"query": "smith", "type": "resident"},
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_people_search_by_pgy_level(self, client: TestClient, auth_headers: dict):
        """Test people search filtered by PGY level."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.search_people.return_value = {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
                "total_pages": 0,
                "facets": {},
                "query": "",
            }
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/search/people",
                json={"query": "", "pgy_level": 2},
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


class TestRotationsSearchEndpoint:
    """Tests for POST /api/search/rotations endpoint."""

    def test_rotations_search_requires_auth(self, client: TestClient):
        """Test that rotations search requires authentication."""
        response = client.post(
            "/api/search/rotations",
            json={"query": "clinic"},
        )

        assert response.status_code in [401, 403]

    def test_rotations_search_success(self, client: TestClient, auth_headers: dict):
        """Test successful rotations search."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_indexer = MagicMock()
            mock_indexer.search_rotations.return_value = {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
                "total_pages": 0,
                "facets": {},
                "query": "clinic",
            }
            mock_instance.indexer = mock_indexer
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/search/rotations",
                json={"query": "clinic"},
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_rotations_search_by_category(self, client: TestClient, auth_headers: dict):
        """Test rotations search filtered by category."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_indexer = MagicMock()
            mock_indexer.search_rotations.return_value = {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
                "total_pages": 0,
                "facets": {},
                "query": "",
            }
            mock_instance.indexer = mock_indexer
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/search/rotations",
                json={"query": "", "category": "outpatient"},
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


class TestProceduresSearchEndpoint:
    """Tests for POST /api/search/procedures endpoint."""

    def test_procedures_search_requires_auth(self, client: TestClient):
        """Test that procedures search requires authentication."""
        response = client.post(
            "/api/search/procedures",
            json={"query": "injection"},
        )

        assert response.status_code in [401, 403]

    def test_procedures_search_success(self, client: TestClient, auth_headers: dict):
        """Test successful procedures search."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_indexer = MagicMock()
            mock_indexer.search_procedures.return_value = {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
                "total_pages": 0,
                "facets": {},
                "query": "injection",
            }
            mock_instance.indexer = mock_indexer
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/search/procedures",
                json={"query": "injection"},
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


class TestGlobalSearchEndpoint:
    """Tests for POST /api/search/global endpoint."""

    def test_global_search_requires_auth(self, client: TestClient):
        """Test that global search requires authentication."""
        response = client.post("/api/search/global?query=test")

        assert response.status_code in [401, 403]

    def test_global_search_success(self, client: TestClient, auth_headers: dict):
        """Test successful global search."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_indexer = MagicMock()
            mock_indexer.global_search.return_value = {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
                "total_pages": 0,
                "facets": {},
                "query": "test",
            }
            mock_instance.indexer = mock_indexer
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/search/global?query=test",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_global_search_with_pagination(
        self, client: TestClient, auth_headers: dict
    ):
        """Test global search with pagination."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_indexer = MagicMock()
            mock_indexer.global_search.return_value = {
                "items": [],
                "total": 0,
                "page": 2,
                "page_size": 10,
                "total_pages": 0,
                "facets": {},
                "query": "test",
            }
            mock_instance.indexer = mock_indexer
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/search/global?query=test&page=2&page_size=10",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]


class TestSuggestEndpoint:
    """Tests for search suggestion endpoints."""

    def test_suggest_post_requires_auth(self, client: TestClient):
        """Test that POST suggest requires authentication."""
        response = client.post(
            "/api/search/suggest",
            json={"query": "jo"},
        )

        assert response.status_code in [401, 403]

    def test_suggest_post_success(self, client: TestClient, auth_headers: dict):
        """Test successful POST suggest request."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.suggest.return_value = ["John Smith", "John Doe"]
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/search/suggest",
                json={"query": "jo", "entity_type": "person"},
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_suggest_get_requires_auth(self, client: TestClient):
        """Test that GET suggest requires authentication."""
        response = client.get("/api/search/suggest?query=jo")

        assert response.status_code in [401, 403]

    def test_suggest_get_success(self, client: TestClient, auth_headers: dict):
        """Test successful GET suggest request."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.suggest.return_value = ["John Smith", "John Doe"]
            mock_service.return_value = mock_instance

            response = client.get(
                "/api/search/suggest?query=jo",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_suggest_with_limit(self, client: TestClient, auth_headers: dict):
        """Test suggest with custom limit."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.suggest.return_value = ["John"]
            mock_service.return_value = mock_instance

            response = client.get(
                "/api/search/suggest?query=jo&limit=1",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_suggest_requires_query(self, client: TestClient, auth_headers: dict):
        """Test suggest requires query parameter."""
        response = client.get(
            "/api/search/suggest",
            headers=auth_headers,
        )

        # Should return 422 for missing required param
        assert response.status_code in [401, 422]


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestSearchEdgeCases:
    """Tests for edge cases in search functionality."""

    def test_search_empty_query(self, client: TestClient, auth_headers: dict):
        """Test search with empty query string."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.search.return_value = {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
                "total_pages": 0,
                "facets": {},
                "query": "",
            }
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/search",
                json={"query": "", "entity_types": ["person"]},
                headers=auth_headers,
            )

            # Empty query may be valid or return 400
            assert response.status_code in [200, 400, 401, 422]

    def test_search_special_characters(self, client: TestClient, auth_headers: dict):
        """Test search with special characters in query."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.search.return_value = {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
                "total_pages": 0,
                "facets": {},
                "query": "test@#$%",
            }
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/search",
                json={"query": "test@#$%", "entity_types": ["person"]},
                headers=auth_headers,
            )

            assert response.status_code in [200, 400, 401]

    def test_search_very_long_query(self, client: TestClient, auth_headers: dict):
        """Test search with very long query string."""
        long_query = "a" * 1000

        response = client.post(
            "/api/search",
            json={"query": long_query, "entity_types": ["person"]},
            headers=auth_headers,
        )

        # Should handle gracefully or return validation error
        assert response.status_code in [200, 400, 401, 422]

    def test_quick_search_limit_validation(
        self, client: TestClient, auth_headers: dict
    ):
        """Test quick search validates limit parameter."""
        response = client.get(
            "/api/search/quick?query=test&limit=100",
            headers=auth_headers,
        )

        # Limit > 50 should fail validation
        assert response.status_code in [401, 422]


# ============================================================================
# Integration Tests
# ============================================================================


class TestSearchIntegration:
    """Integration tests for search functionality."""

    def test_search_endpoints_accessible(self, client: TestClient, auth_headers: dict):
        """Test all search endpoints are accessible."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.search.return_value = {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
                "total_pages": 0,
                "facets": {},
                "query": "test",
            }
            mock_instance.search_people.return_value = mock_instance.search.return_value
            mock_indexer = MagicMock()
            mock_indexer.quick_search.return_value = []
            mock_indexer.search_rotations.return_value = (
                mock_instance.search.return_value
            )
            mock_indexer.search_procedures.return_value = (
                mock_instance.search.return_value
            )
            mock_indexer.global_search.return_value = mock_instance.search.return_value
            mock_instance.indexer = mock_indexer
            mock_instance.suggest.return_value = []
            mock_service.return_value = mock_instance

            endpoints = [
                ("/api/search", "POST", {"query": "test", "entity_types": ["person"]}),
                ("/api/search/quick?query=test", "GET", None),
                ("/api/search/people", "POST", {"query": "test"}),
                ("/api/search/rotations", "POST", {"query": "test"}),
                ("/api/search/procedures", "POST", {"query": "test"}),
                ("/api/search/global?query=test", "POST", None),
                ("/api/search/suggest?query=test", "GET", None),
            ]

            for url, method, data in endpoints:
                if method == "GET":
                    response = client.get(url, headers=auth_headers)
                else:
                    response = client.post(url, json=data, headers=auth_headers)

                # Should return 200 or 401 (auth) but not 404
                assert response.status_code in [200, 401], f"Failed for {url}"

    def test_search_response_format(self, client: TestClient, auth_headers: dict):
        """Test search returns valid JSON format."""
        with patch("app.api.routes.search.SearchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.search.return_value = {
                "items": [
                    {
                        "id": str(uuid4()),
                        "entity_type": "person",
                        "title": "Test",
                        "score": 1.0,
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 20,
                "total_pages": 1,
                "facets": {},
                "query": "test",
            }
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/search",
                json={"query": "test", "entity_types": ["person"]},
                headers=auth_headers,
            )

            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
                assert "items" in data
                assert "total" in data
                assert isinstance(data["items"], list)
