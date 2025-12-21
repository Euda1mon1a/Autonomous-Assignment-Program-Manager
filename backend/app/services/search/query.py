"""Query builder for constructing search queries.

Provides a fluent interface for building complex search queries with:
- Multiple entity types
- Filtering and faceting
- Sorting and pagination
- Fuzzy matching options
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class SearchQuery:
    """
    Represents a search query with all parameters.

    Attributes:
        query_string: The search text
        entity_types: List of entity types to search
        filters: Filter criteria (facets)
        fuzzy: Enable fuzzy matching
        highlight: Enable result highlighting
        page: Page number (1-based)
        page_size: Results per page
        sort_by: Field to sort by
        sort_order: Sort direction (asc/desc)
    """

    query_string: str
    entity_types: List[str] = field(default_factory=lambda: ['person'])
    filters: Dict[str, Any] = field(default_factory=dict)
    fuzzy: bool = True
    highlight: bool = True
    page: int = 1
    page_size: int = 20
    sort_by: str = 'relevance'
    sort_order: str = 'desc'

    @property
    def offset(self) -> int:
        """Calculate pagination offset from page number."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get page size as limit."""
        return self.page_size

    def validate(self) -> List[str]:
        """
        Validate query parameters.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not self.query_string or len(self.query_string.strip()) == 0:
            errors.append("query_string cannot be empty")

        if self.page < 1:
            errors.append("page must be >= 1")

        if self.page_size < 1 or self.page_size > 100:
            errors.append("page_size must be between 1 and 100")

        if not self.entity_types:
            errors.append("entity_types cannot be empty")

        valid_entity_types = {'person', 'rotation', 'procedure', 'assignment', 'swap'}
        invalid_types = set(self.entity_types) - valid_entity_types
        if invalid_types:
            errors.append(f"Invalid entity types: {', '.join(invalid_types)}")

        valid_sort_fields = {'relevance', 'name', 'created_at', 'updated_at'}
        if self.sort_by not in valid_sort_fields:
            errors.append(f"sort_by must be one of: {', '.join(valid_sort_fields)}")

        if self.sort_order not in ('asc', 'desc'):
            errors.append("sort_order must be 'asc' or 'desc'")

        return errors


class QueryBuilder:
    """
    Fluent interface for building search queries.

    Example:
        query = (
            QueryBuilder()
            .search("john smith")
            .in_entities(["person"])
            .filter("type", "resident")
            .filter("pgy_level", 2)
            .enable_fuzzy()
            .page(1, 20)
            .build()
        )
    """

    def __init__(self):
        """Initialize query builder with defaults."""
        self._query_string: str = ""
        self._entity_types: List[str] = ["person"]
        self._filters: Dict[str, Any] = {}
        self._fuzzy: bool = True
        self._highlight: bool = True
        self._page: int = 1
        self._page_size: int = 20
        self._sort_by: str = "relevance"
        self._sort_order: str = "desc"

    def search(self, query_string: str) -> 'QueryBuilder':
        """
        Set the search query string.

        Args:
            query_string: Text to search for

        Returns:
            Self for chaining
        """
        self._query_string = query_string
        return self

    def in_entities(self, entity_types: List[str]) -> 'QueryBuilder':
        """
        Set entity types to search.

        Args:
            entity_types: List of entity type names

        Returns:
            Self for chaining
        """
        self._entity_types = entity_types
        return self

    def in_people(self) -> 'QueryBuilder':
        """Search only in people. Shorthand for in_entities(['person'])."""
        return self.in_entities(['person'])

    def in_rotations(self) -> 'QueryBuilder':
        """Search only in rotations. Shorthand for in_entities(['rotation'])."""
        return self.in_entities(['rotation'])

    def in_procedures(self) -> 'QueryBuilder':
        """Search only in procedures. Shorthand for in_entities(['procedure'])."""
        return self.in_entities(['procedure'])

    def everywhere(self) -> 'QueryBuilder':
        """Search across all entity types."""
        return self.in_entities(['person', 'rotation', 'procedure', 'assignment', 'swap'])

    def filter(self, key: str, value: Any) -> 'QueryBuilder':
        """
        Add a filter criterion.

        Args:
            key: Filter field name
            value: Filter value

        Returns:
            Self for chaining
        """
        self._filters[key] = value
        return self

    def filter_type(self, person_type: str) -> 'QueryBuilder':
        """
        Filter by person type.

        Args:
            person_type: 'resident' or 'faculty'

        Returns:
            Self for chaining
        """
        return self.filter('type', person_type)

    def filter_residents(self) -> 'QueryBuilder':
        """Filter to only residents."""
        return self.filter_type('resident')

    def filter_faculty(self) -> 'QueryBuilder':
        """Filter to only faculty."""
        return self.filter_type('faculty')

    def filter_pgy(self, pgy_level: int) -> 'QueryBuilder':
        """
        Filter by PGY level.

        Args:
            pgy_level: PGY level (1, 2, or 3)

        Returns:
            Self for chaining
        """
        return self.filter('pgy_level', pgy_level)

    def filter_faculty_role(self, role: str) -> 'QueryBuilder':
        """
        Filter by faculty role.

        Args:
            role: Faculty role (pd, apd, core, etc.)

        Returns:
            Self for chaining
        """
        return self.filter('faculty_role', role)

    def filter_status(self, status: str) -> 'QueryBuilder':
        """
        Filter by status (for swaps, etc.).

        Args:
            status: Status value

        Returns:
            Self for chaining
        """
        return self.filter('status', status)

    def enable_fuzzy(self, enabled: bool = True) -> 'QueryBuilder':
        """
        Enable or disable fuzzy matching.

        Args:
            enabled: Whether to enable fuzzy matching

        Returns:
            Self for chaining
        """
        self._fuzzy = enabled
        return self

    def enable_highlight(self, enabled: bool = True) -> 'QueryBuilder':
        """
        Enable or disable result highlighting.

        Args:
            enabled: Whether to enable highlighting

        Returns:
            Self for chaining
        """
        self._highlight = enabled
        return self

    def page(self, page: int, page_size: int = 20) -> 'QueryBuilder':
        """
        Set pagination parameters.

        Args:
            page: Page number (1-based)
            page_size: Results per page

        Returns:
            Self for chaining
        """
        self._page = page
        self._page_size = page_size
        return self

    def sort(self, field: str, order: str = 'desc') -> 'QueryBuilder':
        """
        Set sort parameters.

        Args:
            field: Field to sort by
            order: Sort order ('asc' or 'desc')

        Returns:
            Self for chaining
        """
        self._sort_by = field
        self._sort_order = order
        return self

    def sort_by_relevance(self) -> 'QueryBuilder':
        """Sort by relevance score (descending)."""
        return self.sort('relevance', 'desc')

    def sort_by_name(self, ascending: bool = True) -> 'QueryBuilder':
        """
        Sort by name.

        Args:
            ascending: If True, sort A-Z; if False, sort Z-A

        Returns:
            Self for chaining
        """
        return self.sort('name', 'asc' if ascending else 'desc')

    def sort_by_date(self, newest_first: bool = True) -> 'QueryBuilder':
        """
        Sort by creation date.

        Args:
            newest_first: If True, newest first; if False, oldest first

        Returns:
            Self for chaining
        """
        return self.sort('created_at', 'desc' if newest_first else 'asc')

    def build(self) -> SearchQuery:
        """
        Build the final SearchQuery object.

        Returns:
            SearchQuery instance

        Raises:
            ValueError: If query validation fails
        """
        query = SearchQuery(
            query_string=self._query_string,
            entity_types=self._entity_types,
            filters=self._filters.copy(),
            fuzzy=self._fuzzy,
            highlight=self._highlight,
            page=self._page,
            page_size=self._page_size,
            sort_by=self._sort_by,
            sort_order=self._sort_order,
        )

        # Validate the query
        errors = query.validate()
        if errors:
            raise ValueError(f"Invalid search query: {'; '.join(errors)}")

        return query

    @classmethod
    def quick_search(cls, query_string: str, entity_type: str = 'person') -> SearchQuery:
        """
        Create a quick search query with minimal setup.

        Args:
            query_string: Text to search
            entity_type: Entity type to search

        Returns:
            SearchQuery instance
        """
        return (
            cls()
            .search(query_string)
            .in_entities([entity_type])
            .build()
        )

    @classmethod
    def person_search(
        cls,
        query_string: str,
        person_type: Optional[str] = None,
        pgy_level: Optional[int] = None,
    ) -> SearchQuery:
        """
        Create a person search query.

        Args:
            query_string: Text to search
            person_type: Optional person type filter (resident/faculty)
            pgy_level: Optional PGY level filter

        Returns:
            SearchQuery instance
        """
        builder = cls().search(query_string).in_people()

        if person_type:
            builder = builder.filter_type(person_type)

        if pgy_level:
            builder = builder.filter_pgy(pgy_level)

        return builder.build()
