"""
Tests for search indexer service.

Comprehensive test suite for SearchIndexer and SearchService classes,
covering search operations, faceting, suggestions, and result counting.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.search.indexer import SearchIndexer, SearchService
from app.services.search.query import QueryBuilder, SearchQuery
from app.services.search.backends import PostgreSQLSearchBackend


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return MagicMock()


@pytest.fixture
def mock_backend():
    """Create mock search backend."""
    backend = AsyncMock(spec=PostgreSQLSearchBackend)
    return backend


@pytest.fixture
def search_indexer(mock_db, mock_backend):
    """Create SearchIndexer instance with mock dependencies."""
    indexer = SearchIndexer(db=mock_db, backend=mock_backend)
    return indexer


@pytest.fixture
def search_service(mock_db):
    """Create SearchService instance with mock dependencies."""
    service = SearchService(db=mock_db)
    return service


class TestSearchIndexer:
    """Test suite for SearchIndexer class."""

    @pytest.mark.asyncio
    async def test_search_with_query_object(self, search_indexer, mock_backend):
        """Test search with SearchQuery object returns paginated results."""
        ***REMOVED*** Arrange
        query = QueryBuilder().search("cardiology").in_people().page(1, 20).build()

        mock_backend.search.return_value = {
            "items": [
                {"id": str(uuid4()), "name": "Dr. Smith", "type": "person"},
                {"id": str(uuid4()), "name": "Dr. Jones", "type": "person"},
            ],
            "total": 2,
            "facets": {"person_type": {"faculty": 2}},
        }

        ***REMOVED*** Act
        result = await search_indexer.search(query)

        ***REMOVED*** Assert
        assert result["total"] == 2
        assert len(result["items"]) == 2
        assert result["page"] == 1
        assert result["page_size"] == 20
        assert result["total_pages"] == 1
        assert result["query"] == "cardiology"
        assert "facets" in result

    @pytest.mark.asyncio
    async def test_search_calculates_pagination_correctly(
        self, search_indexer, mock_backend
    ):
        """Test search calculates total pages correctly."""
        ***REMOVED*** Arrange
        query = QueryBuilder().search("test").everywhere().page(1, 10).build()

        mock_backend.search.return_value = {
            "items": [],
            "total": 45,  ***REMOVED*** 45 results, 10 per page = 5 pages
            "facets": {},
        }

        ***REMOVED*** Act
        result = await search_indexer.search(query)

        ***REMOVED*** Assert
        assert result["total"] == 45
        assert result["total_pages"] == 5  ***REMOVED*** Ceiling of 45/10

    @pytest.mark.asyncio
    async def test_quick_search_returns_limited_results(
        self, search_indexer, mock_backend
    ):
        """Test quick search returns limited results without pagination metadata."""
        ***REMOVED*** Arrange
        mock_backend.search.return_value = {
            "items": [
                {"id": str(uuid4()), "name": "PGY1-01"},
                {"id": str(uuid4()), "name": "PGY1-02"},
            ],
            "total": 2,
            "facets": {},
        }

        ***REMOVED*** Act
        result = await search_indexer.quick_search("PGY", entity_type="person", limit=5)

        ***REMOVED*** Assert
        assert isinstance(result, list)
        assert len(result) == 2
        mock_backend.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_people_with_filters(self, search_indexer, mock_backend):
        """Test searching people with type and PGY level filters."""
        ***REMOVED*** Arrange
        mock_backend.search.return_value = {
            "items": [{"id": str(uuid4()), "name": "PGY2-01", "pgy_level": 2}],
            "total": 1,
            "facets": {},
        }

        ***REMOVED*** Act
        result = await search_indexer.search_people(
            query_string="cardiology",
            person_type="resident",
            pgy_level=2,
            page=1,
            page_size=20,
        )

        ***REMOVED*** Assert
        assert result["total"] == 1
        assert len(result["items"]) == 1

    @pytest.mark.asyncio
    async def test_search_rotations_with_category_filter(
        self, search_indexer, mock_backend
    ):
        """Test searching rotations with category filter."""
        ***REMOVED*** Arrange
        mock_backend.search.return_value = {
            "items": [
                {"id": str(uuid4()), "name": "ICU Rotation", "category": "inpatient"}
            ],
            "total": 1,
            "facets": {},
        }

        ***REMOVED*** Act
        result = await search_indexer.search_rotations(
            query_string="ICU",
            category="inpatient",
            page=1,
            page_size=20,
        )

        ***REMOVED*** Assert
        assert result["total"] == 1
        assert result["items"][0]["category"] == "inpatient"

    @pytest.mark.asyncio
    async def test_search_procedures(self, search_indexer, mock_backend):
        """Test searching procedures."""
        ***REMOVED*** Arrange
        mock_backend.search.return_value = {
            "items": [
                {"id": str(uuid4()), "name": "Central Line Placement"},
            ],
            "total": 1,
            "facets": {},
        }

        ***REMOVED*** Act
        result = await search_indexer.search_procedures(
            query_string="central line",
            page=1,
            page_size=20,
        )

        ***REMOVED*** Assert
        assert result["total"] == 1
        assert "Central Line" in result["items"][0]["name"]

    @pytest.mark.asyncio
    async def test_global_search_across_all_entities(
        self, search_indexer, mock_backend
    ):
        """Test global search across all entity types."""
        ***REMOVED*** Arrange
        mock_backend.search.return_value = {
            "items": [
                {"id": str(uuid4()), "type": "person", "name": "Dr. Smith"},
                {"id": str(uuid4()), "type": "rotation", "name": "Cardiology"},
                {"id": str(uuid4()), "type": "procedure", "name": "Echo"},
            ],
            "total": 3,
            "facets": {"entity_type": {"person": 1, "rotation": 1, "procedure": 1}},
        }

        ***REMOVED*** Act
        result = await search_indexer.global_search(
            query_string="cardiology",
            page=1,
            page_size=20,
        )

        ***REMOVED*** Assert
        assert result["total"] == 3
        assert len(result["items"]) == 3
        assert result["facets"]["entity_type"]["person"] == 1

    @pytest.mark.asyncio
    async def test_suggest_returns_autocomplete_suggestions(
        self, search_indexer, mock_backend
    ):
        """Test suggest returns autocomplete suggestions."""
        ***REMOVED*** Arrange
        mock_backend.suggest.return_value = ["Dr. Smith", "Dr. Jones", "Dr. Brown"]

        ***REMOVED*** Act
        result = await search_indexer.suggest(
            query_string="Dr. S",
            entity_type="person",
            limit=10,
        )

        ***REMOVED*** Assert
        assert isinstance(result, list)
        assert len(result) == 3
        assert "Dr. Smith" in result
        mock_backend.suggest.assert_called_once_with(
            query="Dr. S",
            entity_type="person",
            limit=10,
        )

    @pytest.mark.asyncio
    async def test_get_facets_without_results(self, search_indexer, mock_backend):
        """Test getting facet counts without retrieving full results."""
        ***REMOVED*** Arrange
        mock_backend.search.return_value = {
            "items": [],
            "total": 25,
            "facets": {
                "person_type": {"resident": 15, "faculty": 10},
                "pgy_level": {1: 5, 2: 5, 3: 5},
            },
        }

        ***REMOVED*** Act
        result = await search_indexer.get_facets(
            query_string="cardiology",
            entity_types=["person"],
        )

        ***REMOVED*** Assert
        assert "person_type" in result
        assert result["person_type"]["resident"] == 15
        assert result["person_type"]["faculty"] == 10
        ***REMOVED*** Verify we requested 0 items (only facets)
        call_args = mock_backend.search.call_args
        assert call_args.kwargs["limit"] == 0

    @pytest.mark.asyncio
    async def test_count_results_without_retrieving_items(
        self, search_indexer, mock_backend
    ):
        """Test counting results without retrieving items."""
        ***REMOVED*** Arrange
        mock_backend.search.return_value = {
            "items": [],
            "total": 42,
            "facets": {},
        }

        ***REMOVED*** Act
        result = await search_indexer.count_results(
            query_string="test",
            entity_types=["person", "rotation"],
            filters={"person_type": "resident"},
        )

        ***REMOVED*** Assert
        assert result == 42
        ***REMOVED*** Verify we requested 0 items (only count)
        call_args = mock_backend.search.call_args
        assert call_args.kwargs["limit"] == 0

    def test_get_analyzer_returns_correct_analyzer(self, search_indexer):
        """Test getting appropriate analyzer for entity type."""
        ***REMOVED*** Act & Assert
        person_analyzer = search_indexer.get_analyzer("person")
        rotation_analyzer = search_indexer.get_analyzer("rotation")
        default_analyzer = search_indexer.get_analyzer("unknown_type")

        assert person_analyzer is not None
        assert rotation_analyzer is not None
        assert default_analyzer is not None


class TestSearchService:
    """Test suite for SearchService class."""

    @pytest.mark.asyncio
    async def test_service_search_with_filters(self, search_service):
        """Test service layer search with filters."""
        ***REMOVED*** Arrange
        with patch.object(
            search_service.indexer, "search", new_callable=AsyncMock
        ) as mock_search:
            mock_search.return_value = {
                "items": [{"id": str(uuid4()), "name": "Test"}],
                "total": 1,
                "page": 1,
                "page_size": 20,
                "total_pages": 1,
                "facets": {},
                "query": "test",
            }

            ***REMOVED*** Act
            result = await search_service.search(
                query_string="test",
                entity_types=["person"],
                filters={"person_type": "resident"},
                page=1,
                page_size=20,
            )

            ***REMOVED*** Assert
            assert result["total"] == 1
            assert len(result["items"]) == 1
            mock_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_service_search_people(self, search_service):
        """Test service layer search_people method."""
        ***REMOVED*** Arrange
        with patch.object(
            search_service.indexer, "search_people", new_callable=AsyncMock
        ) as mock_search_people:
            mock_search_people.return_value = {
                "items": [{"id": str(uuid4()), "name": "Dr. Smith", "pgy_level": 2}],
                "total": 1,
                "page": 1,
                "page_size": 20,
                "total_pages": 1,
                "facets": {},
                "query": "Smith",
            }

            ***REMOVED*** Act
            result = await search_service.search_people(
                query_string="Smith",
                person_type="resident",
                pgy_level=2,
                page=1,
                page_size=20,
            )

            ***REMOVED*** Assert
            assert result["total"] == 1
            mock_search_people.assert_called_once_with(
                query_string="Smith",
                person_type="resident",
                pgy_level=2,
                page=1,
                page_size=20,
            )

    @pytest.mark.asyncio
    async def test_service_suggest(self, search_service):
        """Test service layer suggest method."""
        ***REMOVED*** Arrange
        with patch.object(
            search_service.indexer, "suggest", new_callable=AsyncMock
        ) as mock_suggest:
            mock_suggest.return_value = ["Dr. Smith", "Dr. Jones"]

            ***REMOVED*** Act
            result = await search_service.suggest(
                query_string="Dr. S",
                entity_type="person",
                limit=10,
            )

            ***REMOVED*** Assert
            assert len(result) == 2
            assert "Dr. Smith" in result
            mock_suggest.assert_called_once_with(
                query_string="Dr. S",
                entity_type="person",
                limit=10,
            )
