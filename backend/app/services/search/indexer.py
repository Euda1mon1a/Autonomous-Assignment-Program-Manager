"""Search indexer for managing search indices.

Coordinates search operations across different backends and provides
high-level search API for the application.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.services.search.analyzers import (
    MedicalTermAnalyzer,
    PersonNameAnalyzer,
    StandardAnalyzer,
)
from app.services.search.backends import PostgreSQLSearchBackend, SearchBackend
from app.services.search.query import QueryBuilder, SearchQuery


class SearchIndexer:
    """
    Main search service coordinating all search operations.

    Provides a unified interface for:
    - Searching across entity types
    - Getting search suggestions
    - Managing search indices
    - Calculating facets
    """

    def __init__(
        self,
        db: Session,
        backend: Optional[SearchBackend] = None,
    ):
        """
        Initialize search indexer.

        Args:
            db: Database session
            backend: Search backend (defaults to PostgreSQL)
        """
        self.db = db
        self.backend = backend or PostgreSQLSearchBackend(
            db=db,
            analyzer=StandardAnalyzer(),
        )

        # Specialized analyzers for different entity types
        self.analyzers = {
            'person': PersonNameAnalyzer(),
            'rotation': MedicalTermAnalyzer(),
            'procedure': MedicalTermAnalyzer(),
            'default': StandardAnalyzer(),
        }

    async def search(
        self,
        query: SearchQuery,
    ) -> Dict[str, Any]:
        """
        Execute a search query.

        Args:
            query: SearchQuery object with all search parameters

        Returns:
            Dictionary containing:
            - items: List of search results
            - total: Total number of results
            - facets: Facet counts for filtering
            - page: Current page number
            - page_size: Results per page
            - total_pages: Total number of pages
        """
        # Execute search via backend
        results = await self.backend.search(
            query=query.query_string,
            entity_types=query.entity_types,
            filters=query.filters,
            limit=query.limit,
            offset=query.offset,
        )

        # Calculate pagination metadata
        total_pages = (results['total'] + query.page_size - 1) // query.page_size

        return {
            'items': results['items'],
            'total': results['total'],
            'facets': results.get('facets', {}),
            'page': query.page,
            'page_size': query.page_size,
            'total_pages': total_pages,
            'query': query.query_string,
        }

    async def quick_search(
        self,
        query_string: str,
        entity_type: str = 'person',
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Perform a quick search with minimal parameters.

        Args:
            query_string: Text to search for
            entity_type: Entity type to search (default: person)
            limit: Maximum results to return

        Returns:
            List of search results
        """
        query = QueryBuilder.quick_search(query_string, entity_type)
        query.page_size = limit

        results = await self.search(query)
        return results['items']

    async def search_people(
        self,
        query_string: str,
        person_type: Optional[str] = None,
        pgy_level: Optional[int] = None,
        faculty_role: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Search for people (residents and faculty).

        Args:
            query_string: Search text
            person_type: Filter by type (resident/faculty)
            pgy_level: Filter by PGY level
            faculty_role: Filter by faculty role
            page: Page number
            page_size: Results per page

        Returns:
            Search results with pagination
        """
        builder = (
            QueryBuilder()
            .search(query_string)
            .in_people()
            .page(page, page_size)
        )

        if person_type:
            builder = builder.filter_type(person_type)

        if pgy_level:
            builder = builder.filter_pgy(pgy_level)

        if faculty_role:
            builder = builder.filter_faculty_role(faculty_role)

        query = builder.build()
        return await self.search(query)

    async def search_rotations(
        self,
        query_string: str,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Search for rotation templates.

        Args:
            query_string: Search text
            category: Filter by category
            page: Page number
            page_size: Results per page

        Returns:
            Search results with pagination
        """
        builder = (
            QueryBuilder()
            .search(query_string)
            .in_rotations()
            .page(page, page_size)
        )

        if category:
            builder = builder.filter('category', category)

        query = builder.build()
        return await self.search(query)

    async def search_procedures(
        self,
        query_string: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Search for procedures.

        Args:
            query_string: Search text
            page: Page number
            page_size: Results per page

        Returns:
            Search results with pagination
        """
        query = (
            QueryBuilder()
            .search(query_string)
            .in_procedures()
            .page(page, page_size)
            .build()
        )

        return await self.search(query)

    async def global_search(
        self,
        query_string: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Search across all entity types.

        Args:
            query_string: Search text
            page: Page number
            page_size: Results per page

        Returns:
            Search results from all entity types
        """
        query = (
            QueryBuilder()
            .search(query_string)
            .everywhere()
            .page(page, page_size)
            .build()
        )

        return await self.search(query)

    async def suggest(
        self,
        query_string: str,
        entity_type: str = 'person',
        limit: int = 10,
    ) -> List[str]:
        """
        Get autocomplete suggestions.

        Args:
            query_string: Partial search query
            entity_type: Entity type for suggestions
            limit: Maximum suggestions to return

        Returns:
            List of suggestion strings
        """
        return await self.backend.suggest(
            query=query_string,
            entity_type=entity_type,
            limit=limit,
        )

    async def get_facets(
        self,
        query_string: str,
        entity_types: List[str],
    ) -> Dict[str, Dict[str, int]]:
        """
        Get facet counts for a query without full results.

        Args:
            query_string: Search query
            entity_types: Entity types to analyze

        Returns:
            Dictionary of facet counts
        """
        results = await self.backend.search(
            query=query_string,
            entity_types=entity_types,
            filters={},
            limit=0,  # Don't need actual results
            offset=0,
        )

        return results.get('facets', {})

    async def count_results(
        self,
        query_string: str,
        entity_types: List[str],
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Count total results for a query without retrieving them.

        Args:
            query_string: Search query
            entity_types: Entity types to search
            filters: Optional filters

        Returns:
            Total result count
        """
        results = await self.backend.search(
            query=query_string,
            entity_types=entity_types,
            filters=filters or {},
            limit=0,
            offset=0,
        )

        return results['total']

    def get_analyzer(self, entity_type: str) -> StandardAnalyzer:
        """
        Get the appropriate analyzer for an entity type.

        Args:
            entity_type: Entity type name

        Returns:
            Analyzer instance
        """
        return self.analyzers.get(entity_type, self.analyzers['default'])


class SearchService:
    """
    Service layer wrapper for SearchIndexer.

    Provides a service-layer interface following the project's
    layered architecture pattern.
    """

    def __init__(self, db: Session):
        """
        Initialize search service.

        Args:
            db: Database session
        """
        self.db = db
        self.indexer = SearchIndexer(db)

    async def search(
        self,
        query_string: str,
        entity_types: List[str],
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = 'relevance',
        sort_order: str = 'desc',
    ) -> Dict[str, Any]:
        """
        Execute a search query.

        Args:
            query_string: Search text
            entity_types: List of entity types to search
            filters: Optional filter criteria
            page: Page number (1-based)
            page_size: Results per page
            sort_by: Field to sort by
            sort_order: Sort direction (asc/desc)

        Returns:
            Search results with pagination and facets
        """
        builder = (
            QueryBuilder()
            .search(query_string)
            .in_entities(entity_types)
            .page(page, page_size)
            .sort(sort_by, sort_order)
        )

        # Add filters
        if filters:
            for key, value in filters.items():
                builder = builder.filter(key, value)

        query = builder.build()
        return await self.indexer.search(query)

    async def search_people(
        self,
        query_string: str,
        person_type: Optional[str] = None,
        pgy_level: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Search for people."""
        return await self.indexer.search_people(
            query_string=query_string,
            person_type=person_type,
            pgy_level=pgy_level,
            page=page,
            page_size=page_size,
        )

    async def suggest(
        self,
        query_string: str,
        entity_type: str = 'person',
        limit: int = 10,
    ) -> List[str]:
        """Get autocomplete suggestions."""
        return await self.indexer.suggest(
            query_string=query_string,
            entity_type=entity_type,
            limit=limit,
        )
