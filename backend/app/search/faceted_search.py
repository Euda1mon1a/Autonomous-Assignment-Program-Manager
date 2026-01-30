"""
Faceted search service for the Residency Scheduler.

Provides comprehensive faceted search capabilities with:
- Facet extraction from search results
- Hierarchical facets (nested categories)
- Range facets (dates, numbers)
- Facet counts and statistics
- Multi-select facets (AND/OR logic)
- Facet caching for performance
- Dynamic facet ordering based on popularity
- Facet analytics and insights

Example:
    from app.search.faceted_search import FacetedSearchService, FacetConfig

    service = FacetedSearchService(db)
    result = await service.search_with_facets(
        query="cardiology",
        facet_config=FacetConfig(
            enabled_facets=["person_type", "pgy_level", "date_range"],
            max_facet_values=10
        )
    )
"""

import hashlib
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.cache import CachePrefix, CacheTTL, get_service_cache
from app.models.assignment import Assignment
from app.models.person import Person
from app.models.procedure import Procedure
from app.models.rotation_template import RotationTemplate
from app.models.swap import SwapRecord
from app.schemas.search import SearchResultItem

logger = logging.getLogger(__name__)


class FacetType(str, Enum):
    """
    Types of facets supported by the search system.

    Each type determines how facet values are collected,
    aggregated, and presented to users.
    """

    TERM = "term"  # Discrete values (e.g., person type, status)
    RANGE = "range"  # Numeric ranges (e.g., age, count)
    DATE_RANGE = "date_range"  # Date ranges (e.g., this week, this month)
    HIERARCHICAL = "hierarchical"  # Nested categories (e.g., specialty > subspecialty)


class FacetOrder(str, Enum):
    """
    Ordering strategies for facet values.

    Determines how facet values are sorted in the UI.
    """

    COUNT_DESC = "count_desc"  # By count, descending (most popular first)
    COUNT_ASC = "count_asc"  # By count, ascending
    VALUE_ASC = "value_asc"  # Alphabetically by value
    VALUE_DESC = "value_desc"  # Reverse alphabetically
    CUSTOM = "custom"  # Custom ordering defined by application


class DateRangePeriod(str, Enum):
    """
    Predefined date range periods for date facets.

    Provides common time periods for filtering search results.
    """

    TODAY = "today"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    THIS_QUARTER = "this_quarter"
    THIS_YEAR = "this_year"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    LAST_YEAR = "last_year"
    CUSTOM = "custom"


class FacetValue(BaseModel):
    """
    A single facet value with count and metadata.

    Represents one possible value for a facet dimension,
    including the number of results that match this value.
    """

    value: str = Field(..., description="Facet value (display label)")
    key: str = Field(..., description="Facet key (for filtering)")
    count: int = Field(..., description="Number of results with this value")
    selected: bool = Field(default=False, description="Whether this facet is selected")
    parent: str | None = Field(
        default=None, description="Parent key for hierarchical facets"
    )
    children: list["FacetValue"] = Field(
        default_factory=list, description="Child facets"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class RangeFacetValue(BaseModel):
    """
    A range facet value representing a numeric or date range.

    Used for continuous values that should be bucketed into ranges
    (e.g., age groups, date periods).
    """

    label: str = Field(..., description="Human-readable label")
    min_value: float | None = Field(
        default=None, description="Minimum value (inclusive)"
    )
    max_value: float | None = Field(
        default=None, description="Maximum value (exclusive)"
    )
    count: int = Field(..., description="Number of results in this range")
    selected: bool = Field(default=False, description="Whether this range is selected")


class DateRangeFacetValue(BaseModel):
    """
    A date range facet value.

    Represents a specific time period for filtering by dates.
    """

    label: str = Field(..., description="Human-readable label")
    period: DateRangePeriod = Field(..., description="Predefined period")
    start_date: date | None = Field(default=None, description="Start date (inclusive)")
    end_date: date | None = Field(default=None, description="End date (inclusive)")
    count: int = Field(..., description="Number of results in this range")
    selected: bool = Field(default=False, description="Whether this range is selected")


class Facet(BaseModel):
    """
    A facet dimension for filtering search results.

    Contains all possible values for a single facet field,
    along with counts and metadata.
    """

    name: str = Field(..., description="Facet name (unique identifier)")
    label: str = Field(..., description="Display label for UI")
    type: FacetType = Field(..., description="Facet type")
    values: list[FacetValue] = Field(default_factory=list, description="Facet values")
    range_values: list[RangeFacetValue] = Field(
        default_factory=list, description="Range values (for range facets)"
    )
    date_range_values: list[DateRangeFacetValue] = Field(
        default_factory=list, description="Date range values (for date facets)"
    )
    total_count: int = Field(default=0, description="Total results across all values")
    order: FacetOrder = Field(
        default=FacetOrder.COUNT_DESC, description="Ordering strategy"
    )
    multi_select: bool = Field(
        default=True, description="Allow multiple value selection"
    )

    class Config:
        use_enum_values = True


class FacetConfig(BaseModel):
    """
    Configuration for faceted search behavior.

    Controls which facets are enabled, how they're ordered,
    and other search refinement options.
    """

    enabled_facets: list[str] = Field(
        default_factory=lambda: [
            "person_type",
            "pgy_level",
            "faculty_role",
            "rotation_type",
            "status",
            "date_range",
        ],
        description="List of facet names to enable",
    )
    max_facet_values: int = Field(default=10, description="Maximum values per facet")
    min_facet_count: int = Field(
        default=1, description="Minimum count to show facet value"
    )
    enable_hierarchical: bool = Field(
        default=True, description="Enable hierarchical facets"
    )
    enable_range_facets: bool = Field(default=True, description="Enable range facets")
    enable_date_facets: bool = Field(
        default=True, description="Enable date range facets"
    )
    cache_facets: bool = Field(default=True, description="Enable facet caching")
    cache_ttl: int = Field(default=CacheTTL.MEDIUM, description="Cache TTL in seconds")
    dynamic_ordering: bool = Field(
        default=True, description="Dynamically order facets by popularity"
    )


class FacetSelection(BaseModel):
    """
    Selected facet values for filtering.

    Represents the user's current facet selections,
    used to filter search results.
    """

    facet_name: str = Field(..., description="Facet name")
    values: list[str] = Field(default_factory=list, description="Selected values")
    range_min: float | None = Field(default=None, description="Range minimum")
    range_max: float | None = Field(default=None, description="Range maximum")
    date_start: date | None = Field(default=None, description="Date range start")
    date_end: date | None = Field(default=None, description="Date range end")
    operator: str = Field(default="OR", description="Combination operator (AND/OR)")


class FacetAnalytics(BaseModel):
    """
    Analytics data for facet usage and performance.

    Tracks how facets are used to inform UI improvements
    and search quality optimization.
    """

    facet_name: str = Field(..., description="Facet name")
    total_selections: int = Field(default=0, description="Total times selected")
    unique_users: set[str] = Field(default_factory=set, description="Unique user IDs")
    avg_result_reduction: float = Field(
        default=0.0, description="Average % reduction in results when applied"
    )
    popular_combinations: dict[str, int] = Field(
        default_factory=dict, description="Popular facet combinations"
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow, description="Last analytics update"
    )


class FacetedSearchResponse(BaseModel):
    """
    Response from faceted search including results and facets.

    Extends standard search response with facet information
    for search refinement.
    """

    items: list[SearchResultItem] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Results per page")
    total_pages: int = Field(..., description="Total number of pages")
    facets: list[Facet] = Field(default_factory=list, description="Available facets")
    applied_facets: list[FacetSelection] = Field(
        default_factory=list, description="Currently applied facets"
    )
    query: str = Field(..., description="Original query string")
    execution_time_ms: float = Field(default=0.0, description="Search execution time")


class FacetedSearchService:
    """
    Faceted search service for the Residency Scheduler.

    Provides comprehensive faceted search with:
    - Multiple facet types (term, range, hierarchical)
    - Dynamic facet ordering
    - Facet caching for performance
    - Multi-select facet logic
    - Facet analytics tracking
    """

    def __init__(self, db: Session) -> None:
        """
        Initialize faceted search service.

        Args:
            db: Database session
        """
        self.db = db
        self._cache = get_service_cache()
        self._facet_analytics: dict[str, FacetAnalytics] = {}

    def _get_cache_key(
        self,
        query: str,
        entity_types: list[str],
        selections: list[FacetSelection],
    ) -> str:
        """
        Generate cache key for facet results.

        Args:
            query: Search query
            entity_types: List of entity types
            selections: Applied facet selections

        Returns:
            Cache key string
        """
        # Create deterministic hash of search parameters
        params = {
            "query": query,
            "entity_types": sorted(entity_types),
            "selections": [
                {
                    "facet": s.facet_name,
                    "values": sorted(s.values) if s.values else [],
                    "range": (s.range_min, s.range_max),
                    "dates": (
                        s.date_start.isoformat() if s.date_start else None,
                        s.date_end.isoformat() if s.date_end else None,
                    ),
                }
                for s in sorted(selections, key=lambda x: x.facet_name)
            ],
        }

        param_str = str(params)
        param_hash = hashlib.sha256(param_str.encode()).hexdigest()[:16]

        return f"{CachePrefix.SCHEDULE.value}:facets:{param_hash}"

    async def search_with_facets(
        self,
        query: str,
        entity_types: list[str] | None = None,
        facet_selections: list[FacetSelection] | None = None,
        facet_config: FacetConfig | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> FacetedSearchResponse:
        """
        Execute a faceted search with dynamic facet generation.

        Args:
            query: Search query string
            entity_types: Entity types to search (default: all)
            facet_selections: Currently selected facets
            facet_config: Facet configuration
            page: Page number (1-based)
            page_size: Results per page

        Returns:
            Faceted search response with results and facets
        """
        start_time = datetime.utcnow()

        if entity_types is None:
            entity_types = ["person", "rotation", "procedure", "assignment", "swap"]

        if facet_selections is None:
            facet_selections = []

        if facet_config is None:
            facet_config = FacetConfig()

            # Check cache if enabled
        cache_key = self._get_cache_key(query, entity_types, facet_selections)
        if facet_config.cache_facets:
            cached_result = self._cache.get(cache_key)
            if cached_result:
                logger.debug(f"Facet cache hit for query: {query}")
                return cached_result

                # Execute search with filters
        results = await self._execute_search(
            query=query,
            entity_types=entity_types,
            facet_selections=facet_selections,
        )

        # Generate facets from results
        facets = await self._generate_facets(
            results=results,
            entity_types=entity_types,
            facet_config=facet_config,
            facet_selections=facet_selections,
        )

        # Apply pagination
        total = len(results)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_results = results[start_idx:end_idx]

        # Calculate execution time
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        response = FacetedSearchResponse(
            items=paginated_results,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
            facets=facets,
            applied_facets=facet_selections,
            query=query,
            execution_time_ms=execution_time,
        )

        # Cache result
        if facet_config.cache_facets:
            self._cache.set(cache_key, response, ttl=facet_config.cache_ttl)

            # Track analytics
        await self._track_facet_usage(facet_selections, total, len(results))

        return response

    async def _execute_search(
        self,
        query: str,
        entity_types: list[str],
        facet_selections: list[FacetSelection],
    ) -> list[SearchResultItem]:
        """
        Execute search with facet filters applied.

        Args:
            query: Search query
            entity_types: Entity types to search
            facet_selections: Applied facet selections

        Returns:
            List of search result items
        """
        all_results = []

        # Search each entity type
        if "person" in entity_types:
            person_results = await self._search_persons(query, facet_selections)
            all_results.extend(person_results)

        if "rotation" in entity_types:
            rotation_results = await self._search_rotations(query, facet_selections)
            all_results.extend(rotation_results)

        if "procedure" in entity_types:
            procedure_results = await self._search_procedures(query, facet_selections)
            all_results.extend(procedure_results)

        if "assignment" in entity_types:
            assignment_results = await self._search_assignments(query, facet_selections)
            all_results.extend(assignment_results)

        if "swap" in entity_types:
            swap_results = await self._search_swaps(query, facet_selections)
            all_results.extend(swap_results)

        return all_results

    async def _search_persons(
        self,
        query: str,
        facet_selections: list[FacetSelection],
    ) -> list[SearchResultItem]:
        """
        Search persons with facet filters.

        Args:
            query: Search query
            facet_selections: Applied facet selections

        Returns:
            List of person search results
        """
        query_obj = self.db.query(Person)

        # Apply text search
        if query:
            query_obj = query_obj.filter(
                or_(
                    Person.name.ilike(f"%{query}%"),
                    Person.email.ilike(f"%{query}%"),
                    Person.type.ilike(f"%{query}%"),
                )
            )

            # Apply facet filters
        for selection in facet_selections:
            if selection.facet_name == "person_type" and selection.values:
                if selection.operator == "OR":
                    query_obj = query_obj.filter(Person.type.in_(selection.values))
                else:  # AND - only makes sense for multi-field searches
                    for value in selection.values:
                        query_obj = query_obj.filter(Person.type == value)

            elif selection.facet_name == "pgy_level" and selection.values:
                pgy_levels = [
                    int(v.replace("PGY-", ""))
                    for v in selection.values
                    if v.startswith("PGY-")
                ]
                if pgy_levels:
                    query_obj = query_obj.filter(Person.pgy_level.in_(pgy_levels))

            elif selection.facet_name == "faculty_role" and selection.values:
                query_obj = query_obj.filter(Person.faculty_role.in_(selection.values))

        persons = query_obj.limit(100).all()

        results = []
        for person in persons:
            results.append(
                SearchResultItem(
                    id=str(person.id),
                    type="person",
                    title=person.name,
                    subtitle=person.type.title(),
                    score=1.0,
                    highlights={},
                    entity={
                        "id": str(person.id),
                        "name": person.name,
                        "email": person.email,
                        "type": person.type,
                        "pgy_level": person.pgy_level,
                        "faculty_role": person.faculty_role,
                    },
                )
            )

        return results

    async def _search_rotations(
        self,
        query: str,
        facet_selections: list[FacetSelection],
    ) -> list[SearchResultItem]:
        """
        Search rotations with facet filters.

        Args:
            query: Search query
            facet_selections: Applied facet selections

        Returns:
            List of rotation search results
        """
        query_obj = self.db.query(RotationTemplate)

        # Apply text search
        if query:
            query_obj = query_obj.filter(
                or_(
                    RotationTemplate.name.ilike(f"%{query}%"),
                    RotationTemplate.rotation_type.ilike(f"%{query}%"),
                )
            )

            # Apply facet filters
        for selection in facet_selections:
            if selection.facet_name == "rotation_type" and selection.values:
                query_obj = query_obj.filter(
                    RotationTemplate.rotation_type.in_(selection.values)
                )

        rotations = query_obj.limit(100).all()

        results = []
        for rotation in rotations:
            results.append(
                SearchResultItem(
                    id=str(rotation.id),
                    type="rotation",
                    title=rotation.name,
                    subtitle=rotation.rotation_type.title(),
                    score=1.0,
                    highlights={},
                    entity={
                        "id": str(rotation.id),
                        "name": rotation.name,
                        "rotation_type": rotation.rotation_type,
                    },
                )
            )

        return results

    async def _search_procedures(
        self,
        query: str,
        facet_selections: list[FacetSelection],
    ) -> list[SearchResultItem]:
        """
        Search procedures with facet filters.

        Args:
            query: Search query
            facet_selections: Applied facet selections

        Returns:
            List of procedure search results
        """
        query_obj = self.db.query(Procedure)

        # Apply text search
        if query:
            query_obj = query_obj.filter(
                or_(
                    Procedure.name.ilike(f"%{query}%"),
                    Procedure.category.ilike(f"%{query}%"),
                )
            )

            # Apply facet filters
        for selection in facet_selections:
            if selection.facet_name == "procedure_category" and selection.values:
                query_obj = query_obj.filter(Procedure.category.in_(selection.values))

        procedures = query_obj.limit(100).all()

        results = []
        for procedure in procedures:
            results.append(
                SearchResultItem(
                    id=str(procedure.id),
                    type="procedure",
                    title=procedure.name,
                    subtitle=procedure.category or "Procedure",
                    score=1.0,
                    highlights={},
                    entity={
                        "id": str(procedure.id),
                        "name": procedure.name,
                        "category": procedure.category,
                    },
                )
            )

        return results

    async def _search_assignments(
        self,
        query: str,
        facet_selections: list[FacetSelection],
    ) -> list[SearchResultItem]:
        """
        Search assignments with facet filters.

        Args:
            query: Search query
            facet_selections: Applied facet selections

        Returns:
            List of assignment search results
        """
        query_obj = self.db.query(Assignment)

        # Apply text search
        if query:
            query_obj = query_obj.filter(
                or_(
                    Assignment.role.ilike(f"%{query}%"),
                    Assignment.activity_override.ilike(f"%{query}%"),
                )
            )

            # Apply facet filters
        for selection in facet_selections:
            if selection.facet_name == "assignment_role" and selection.values:
                query_obj = query_obj.filter(Assignment.role.in_(selection.values))

                # Date range filter for assignments
            if selection.facet_name == "date_range":
                if selection.date_start and selection.date_end:
                    # This would require joining with Block table
                    pass  # Simplified for now

        assignments = query_obj.limit(100).all()

        results = []
        for assignment in assignments:
            results.append(
                SearchResultItem(
                    id=str(assignment.id),
                    type="assignment",
                    title=f"Assignment - {assignment.role}",
                    subtitle=assignment.role.title(),
                    score=1.0,
                    highlights={},
                    entity={
                        "id": str(assignment.id),
                        "role": assignment.role,
                    },
                )
            )

        return results

    async def _search_swaps(
        self,
        query: str,
        facet_selections: list[FacetSelection],
    ) -> list[SearchResultItem]:
        """
        Search swaps with facet filters.

        Args:
            query: Search query
            facet_selections: Applied facet selections

        Returns:
            List of swap search results
        """
        query_obj = self.db.query(SwapRecord)

        # Apply text search
        if query:
            query_obj = query_obj.filter(
                or_(
                    SwapRecord.status.ilike(f"%{query}%"),
                    SwapRecord.swap_type.ilike(f"%{query}%"),
                )
            )

            # Apply facet filters
        for selection in facet_selections:
            if selection.facet_name == "status" and selection.values:
                query_obj = query_obj.filter(SwapRecord.status.in_(selection.values))

        swaps = query_obj.limit(100).all()

        results = []
        for swap in swaps:
            results.append(
                SearchResultItem(
                    id=str(swap.id),
                    type="swap",
                    title=f"Swap - {swap.status}",
                    subtitle=swap.swap_type or "Swap",
                    score=1.0,
                    highlights={},
                    entity={
                        "id": str(swap.id),
                        "status": swap.status,
                        "swap_type": swap.swap_type,
                    },
                )
            )

        return results

    async def _generate_facets(
        self,
        results: list[SearchResultItem],
        entity_types: list[str],
        facet_config: FacetConfig,
        facet_selections: list[FacetSelection],
    ) -> list[Facet]:
        """
        Generate facets from search results.

        Args:
            results: Search results
            entity_types: Entity types being searched
            facet_config: Facet configuration
            facet_selections: Currently applied facets

        Returns:
            List of facets with counts
        """
        facets = []

        # Generate term facets
        if "person_type" in facet_config.enabled_facets:
            person_type_facet = self._generate_person_type_facet(
                results, facet_config, facet_selections
            )
            if person_type_facet:
                facets.append(person_type_facet)

        if "pgy_level" in facet_config.enabled_facets:
            pgy_level_facet = self._generate_pgy_level_facet(
                results, facet_config, facet_selections
            )
            if pgy_level_facet:
                facets.append(pgy_level_facet)

        if "faculty_role" in facet_config.enabled_facets:
            faculty_role_facet = self._generate_faculty_role_facet(
                results, facet_config, facet_selections
            )
            if faculty_role_facet:
                facets.append(faculty_role_facet)

        if "rotation_type" in facet_config.enabled_facets:
            rotation_type_facet = self._generate_rotation_type_facet(
                results, facet_config, facet_selections
            )
            if rotation_type_facet:
                facets.append(rotation_type_facet)

        if "status" in facet_config.enabled_facets:
            status_facet = self._generate_status_facet(
                results, facet_config, facet_selections
            )
            if status_facet:
                facets.append(status_facet)

                # Generate date range facets
        if (
            facet_config.enable_date_facets
            and "date_range" in facet_config.enabled_facets
        ):
            date_facet = self._generate_date_range_facet(
                results, facet_config, facet_selections
            )
            if date_facet:
                facets.append(date_facet)

                # Generate hierarchical facets
        if (
            facet_config.enable_hierarchical
            and "specialty" in facet_config.enabled_facets
        ):
            specialty_facet = self._generate_specialty_hierarchical_facet(
                results, facet_config, facet_selections
            )
            if specialty_facet:
                facets.append(specialty_facet)

                # Dynamic ordering
        if facet_config.dynamic_ordering:
            facets = self._apply_dynamic_facet_ordering(facets)

        return facets

    def _generate_person_type_facet(
        self,
        results: list[SearchResultItem],
        config: FacetConfig,
        selections: list[FacetSelection],
    ) -> Facet | None:
        """
        Generate person type facet.

        Args:
            results: Search results
            config: Facet configuration
            selections: Applied facet selections

        Returns:
            Person type facet or None
        """
        counts: dict[str, int] = defaultdict(int)

        for result in results:
            if result.type == "person" and result.entity:
                person_type = result.entity.get("type")
                if person_type:
                    counts[person_type] += 1

        if not counts:
            return None

            # Get selected values
        selected_values = set()
        for selection in selections:
            if selection.facet_name == "person_type":
                selected_values.update(selection.values)

                # Create facet values
        facet_values = [
            FacetValue(
                value=person_type.title(),
                key=person_type,
                count=count,
                selected=person_type in selected_values,
            )
            for person_type, count in counts.items()
            if count >= config.min_facet_count
        ]

        # Sort by count descending
        facet_values.sort(key=lambda x: x.count, reverse=True)

        # Limit values
        facet_values = facet_values[: config.max_facet_values]

        return Facet(
            name="person_type",
            label="Person Type",
            type=FacetType.TERM,
            values=facet_values,
            total_count=sum(counts.values()),
            order=FacetOrder.COUNT_DESC,
            multi_select=True,
        )

    def _generate_pgy_level_facet(
        self,
        results: list[SearchResultItem],
        config: FacetConfig,
        selections: list[FacetSelection],
    ) -> Facet | None:
        """
        Generate PGY level facet.

        Args:
            results: Search results
            config: Facet configuration
            selections: Applied facet selections

        Returns:
            PGY level facet or None
        """
        counts: dict[str, int] = defaultdict(int)

        for result in results:
            if result.type == "person" and result.entity:
                pgy_level = result.entity.get("pgy_level")
                if pgy_level:
                    key = f"PGY-{pgy_level}"
                    counts[key] += 1

        if not counts:
            return None

            # Get selected values
        selected_values = set()
        for selection in selections:
            if selection.facet_name == "pgy_level":
                selected_values.update(selection.values)

                # Create facet values
        facet_values = [
            FacetValue(
                value=key,
                key=key,
                count=count,
                selected=key in selected_values,
            )
            for key, count in counts.items()
            if count >= config.min_facet_count
        ]

        # Sort by value (PGY-1, PGY-2, PGY-3)
        facet_values.sort(key=lambda x: x.key)

        return Facet(
            name="pgy_level",
            label="PGY Level",
            type=FacetType.TERM,
            values=facet_values,
            total_count=sum(counts.values()),
            order=FacetOrder.VALUE_ASC,
            multi_select=True,
        )

    def _generate_faculty_role_facet(
        self,
        results: list[SearchResultItem],
        config: FacetConfig,
        selections: list[FacetSelection],
    ) -> Facet | None:
        """
        Generate faculty role facet.

        Args:
            results: Search results
            config: Facet configuration
            selections: Applied facet selections

        Returns:
            Faculty role facet or None
        """
        counts: dict[str, int] = defaultdict(int)

        for result in results:
            if result.type == "person" and result.entity:
                faculty_role = result.entity.get("faculty_role")
                if faculty_role:
                    counts[faculty_role] += 1

        if not counts:
            return None

            # Get selected values
        selected_values = set()
        for selection in selections:
            if selection.facet_name == "faculty_role":
                selected_values.update(selection.values)

                # Role labels
        role_labels = {
            "pd": "Program Director",
            "apd": "Associate Program Director",
            "oic": "Officer in Charge",
            "dept_chief": "Department Chief",
            "sports_med": "Sports Medicine",
            "core": "Core Faculty",
        }

        # Create facet values
        facet_values = [
            FacetValue(
                value=role_labels.get(role, role.upper()),
                key=role,
                count=count,
                selected=role in selected_values,
            )
            for role, count in counts.items()
            if count >= config.min_facet_count
        ]

        # Sort by count descending
        facet_values.sort(key=lambda x: x.count, reverse=True)
        facet_values = facet_values[: config.max_facet_values]

        return Facet(
            name="faculty_role",
            label="Faculty Role",
            type=FacetType.TERM,
            values=facet_values,
            total_count=sum(counts.values()),
            order=FacetOrder.COUNT_DESC,
            multi_select=True,
        )

    def _generate_rotation_type_facet(
        self,
        results: list[SearchResultItem],
        config: FacetConfig,
        selections: list[FacetSelection],
    ) -> Facet | None:
        """
        Generate rotation type facet.

        Args:
            results: Search results
            config: Facet configuration
            selections: Applied facet selections

        Returns:
            Rotation type facet or None
        """
        counts: dict[str, int] = defaultdict(int)

        for result in results:
            if result.type == "rotation" and result.entity:
                rotation_type = result.entity.get("rotation_type")
                if rotation_type:
                    counts[rotation_type] += 1

        if not counts:
            return None

            # Get selected values
        selected_values = set()
        for selection in selections:
            if selection.facet_name == "rotation_type":
                selected_values.update(selection.values)

                # Create facet values
        facet_values = [
            FacetValue(
                value=rotation_type.title(),
                key=rotation_type,
                count=count,
                selected=rotation_type in selected_values,
            )
            for rotation_type, count in counts.items()
            if count >= config.min_facet_count
        ]

        # Sort by count descending
        facet_values.sort(key=lambda x: x.count, reverse=True)
        facet_values = facet_values[: config.max_facet_values]

        return Facet(
            name="rotation_type",
            label="Rotation Type",
            type=FacetType.TERM,
            values=facet_values,
            total_count=sum(counts.values()),
            order=FacetOrder.COUNT_DESC,
            multi_select=True,
        )

    def _generate_status_facet(
        self,
        results: list[SearchResultItem],
        config: FacetConfig,
        selections: list[FacetSelection],
    ) -> Facet | None:
        """
        Generate status facet.

        Args:
            results: Search results
            config: Facet configuration
            selections: Applied facet selections

        Returns:
            Status facet or None
        """
        counts: dict[str, int] = defaultdict(int)

        for result in results:
            if result.entity:
                status = result.entity.get("status")
                if status:
                    counts[status] += 1

        if not counts:
            return None

            # Get selected values
        selected_values = set()
        for selection in selections:
            if selection.facet_name == "status":
                selected_values.update(selection.values)

                # Create facet values
        facet_values = [
            FacetValue(
                value=status.title(),
                key=status,
                count=count,
                selected=status in selected_values,
            )
            for status, count in counts.items()
            if count >= config.min_facet_count
        ]

        # Sort by count descending
        facet_values.sort(key=lambda x: x.count, reverse=True)
        facet_values = facet_values[: config.max_facet_values]

        return Facet(
            name="status",
            label="Status",
            type=FacetType.TERM,
            values=facet_values,
            total_count=sum(counts.values()),
            order=FacetOrder.COUNT_DESC,
            multi_select=True,
        )

    def _generate_date_range_facet(
        self,
        results: list[SearchResultItem],
        config: FacetConfig,
        selections: list[FacetSelection],
    ) -> Facet | None:
        """
        Generate date range facet.

        Args:
            results: Search results
            config: Facet configuration
            selections: Applied facet selections

        Returns:
            Date range facet or None
        """
        today = date.today()

        # Define date ranges
        ranges = [
            DateRangeFacetValue(
                label="Today",
                period=DateRangePeriod.TODAY,
                start_date=today,
                end_date=today,
                count=0,
            ),
            DateRangeFacetValue(
                label="This Week",
                period=DateRangePeriod.THIS_WEEK,
                start_date=today - timedelta(days=today.weekday()),
                end_date=today + timedelta(days=6 - today.weekday()),
                count=0,
            ),
            DateRangeFacetValue(
                label="This Month",
                period=DateRangePeriod.THIS_MONTH,
                start_date=today.replace(day=1),
                end_date=(today.replace(day=1) + timedelta(days=32)).replace(day=1)
                - timedelta(days=1),
                count=0,
            ),
            DateRangeFacetValue(
                label="Last 7 Days",
                period=DateRangePeriod.LAST_7_DAYS,
                start_date=today - timedelta(days=7),
                end_date=today,
                count=0,
            ),
            DateRangeFacetValue(
                label="Last 30 Days",
                period=DateRangePeriod.LAST_30_DAYS,
                start_date=today - timedelta(days=30),
                end_date=today,
                count=0,
            ),
            DateRangeFacetValue(
                label="Last 90 Days",
                period=DateRangePeriod.LAST_90_DAYS,
                start_date=today - timedelta(days=90),
                end_date=today,
                count=0,
            ),
        ]

        # Count results in each range
        # Note: This is simplified - in production, you'd query actual date fields
        for range_value in ranges:
            range_value.count = len(results)  # Placeholder

        return Facet(
            name="date_range",
            label="Date Range",
            type=FacetType.DATE_RANGE,
            date_range_values=ranges,
            total_count=len(results),
            order=FacetOrder.CUSTOM,
            multi_select=False,
        )

    def _generate_specialty_hierarchical_facet(
        self,
        results: list[SearchResultItem],
        config: FacetConfig,
        selections: list[FacetSelection],
    ) -> Facet | None:
        """
        Generate hierarchical specialty facet.

        Args:
            results: Search results
            config: Facet configuration
            selections: Applied facet selections

        Returns:
            Hierarchical specialty facet or None
        """
        # Hierarchical structure: Department > Specialty > Subspecialty
        hierarchy: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for result in results:
            if result.type == "person" and result.entity:
                specialties = result.entity.get("specialties", [])
                for specialty in specialties:
                    # Split specialty into hierarchy levels
                    # Example: "Sports Medicine > Orthopedics" or just "Cardiology"
                    if ">" in specialty:
                        parts = [p.strip() for p in specialty.split(">")]
                        parent = parts[0]
                        child = parts[1] if len(parts) > 1 else None
                        hierarchy[parent][child or "_total"] += 1
                    else:
                        hierarchy[specialty]["_total"] += 1

        if not hierarchy:
            return None

            # Build hierarchical facet values
        facet_values = []
        for parent, children in hierarchy.items():
            total_count = children.get("_total", 0) + sum(
                count for key, count in children.items() if key != "_total"
            )

            parent_value = FacetValue(
                value=parent,
                key=parent,
                count=total_count,
                selected=False,
            )

            # Add children
            for child, count in children.items():
                if child != "_total":
                    child_value = FacetValue(
                        value=child,
                        key=f"{parent}>{child}",
                        count=count,
                        selected=False,
                        parent=parent,
                    )
                    parent_value.children.append(child_value)

            facet_values.append(parent_value)

            # Sort by count
        facet_values.sort(key=lambda x: x.count, reverse=True)

        return Facet(
            name="specialty",
            label="Specialty",
            type=FacetType.HIERARCHICAL,
            values=facet_values[: config.max_facet_values],
            total_count=sum(v.count for v in facet_values),
            order=FacetOrder.COUNT_DESC,
            multi_select=True,
        )

    def _apply_dynamic_facet_ordering(self, facets: list[Facet]) -> list[Facet]:
        """
        Apply dynamic ordering to facets based on usage analytics.

        Args:
            facets: List of facets

        Returns:
            Reordered facets
        """

        # Sort by analytics data (if available)
        def get_popularity_score(facet: Facet) -> float:
            analytics = self._facet_analytics.get(facet.name)
            if analytics:
                return analytics.total_selections
            return 0.0

        facets.sort(key=get_popularity_score, reverse=True)
        return facets

    async def _track_facet_usage(
        self,
        selections: list[FacetSelection],
        total_before: int,
        total_after: int,
    ) -> None:
        """
        Track facet usage analytics.

        Args:
            selections: Applied facet selections
            total_before: Result count before facets
            total_after: Result count after facets
        """
        for selection in selections:
            if selection.facet_name not in self._facet_analytics:
                self._facet_analytics[selection.facet_name] = FacetAnalytics(
                    facet_name=selection.facet_name
                )

            analytics = self._facet_analytics[selection.facet_name]
            analytics.total_selections += 1

            # Calculate result reduction
            if total_before > 0:
                reduction = ((total_before - total_after) / total_before) * 100
                # Update moving average
                current_avg = analytics.avg_result_reduction
                new_avg = (current_avg + reduction) / 2
                analytics.avg_result_reduction = new_avg

            analytics.last_updated = datetime.utcnow()

    def get_facet_analytics(self, facet_name: str | None = None) -> dict[str, Any]:
        """
        Get facet usage analytics.

        Args:
            facet_name: Specific facet name or None for all facets

        Returns:
            Analytics data
        """
        if facet_name:
            analytics = self._facet_analytics.get(facet_name)
            if analytics:
                return {
                    "facet_name": analytics.facet_name,
                    "total_selections": analytics.total_selections,
                    "unique_users": len(analytics.unique_users),
                    "avg_result_reduction": analytics.avg_result_reduction,
                    "last_updated": analytics.last_updated.isoformat(),
                }
            return {}

            # Return all analytics
        return {
            name: {
                "facet_name": analytics.facet_name,
                "total_selections": analytics.total_selections,
                "unique_users": len(analytics.unique_users),
                "avg_result_reduction": analytics.avg_result_reduction,
                "last_updated": analytics.last_updated.isoformat(),
            }
            for name, analytics in self._facet_analytics.items()
        }


def get_faceted_search_service(db: Session) -> FacetedSearchService:
    """
    Get faceted search service instance.

    Args:
        db: Database session

    Returns:
        Configured faceted search service
    """
    return FacetedSearchService(db)
