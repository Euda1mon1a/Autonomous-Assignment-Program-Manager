"""Search schemas for request/response validation."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SearchRequest(BaseModel):
    """Request schema for search endpoint."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query text")
    entity_types: List[str] = Field(
        default=['person'],
        description="Entity types to search: person, rotation, procedure, assignment, swap"
    )
    filters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional filters (type, pgy_level, status, etc.)"
    )
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=20, ge=1, le=100, description="Results per page")
    sort_by: str = Field(default='relevance', description="Field to sort by")
    sort_order: str = Field(default='desc', description="Sort order: asc or desc")
    highlight: bool = Field(default=True, description="Enable result highlighting")
    fuzzy: bool = Field(default=True, description="Enable fuzzy matching")

    @field_validator('entity_types')
    @classmethod
    def validate_entity_types(cls, v: List[str]) -> List[str]:
        """Validate entity types."""
        valid_types = {'person', 'rotation', 'procedure', 'assignment', 'swap'}
        invalid = set(v) - valid_types
        if invalid:
            raise ValueError(f"Invalid entity types: {', '.join(invalid)}")
        if not v:
            raise ValueError("At least one entity type is required")
        return v

    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        """Validate sort order."""
        if v not in ('asc', 'desc'):
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v


class SearchResultItem(BaseModel):
    """Individual search result item."""

    id: str = Field(..., description="Entity ID")
    type: str = Field(..., description="Entity type")
    title: str = Field(..., description="Result title")
    subtitle: str = Field(default="", description="Result subtitle/description")
    score: float = Field(default=0.0, description="Relevance score")
    highlights: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Highlighted text fragments"
    )
    entity: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Full entity data (optional)"
    )

    class Config:
        from_attributes = True


class FacetCount(BaseModel):
    """Facet count for filtering."""

    value: str = Field(..., description="Facet value")
    count: int = Field(..., description="Number of results with this value")


class SearchFacets(BaseModel):
    """Facets for search results."""

    type: Dict[str, int] = Field(default_factory=dict, description="Person type facets")
    pgy_level: Dict[str, int] = Field(default_factory=dict, description="PGY level facets")
    faculty_role: Dict[str, int] = Field(default_factory=dict, description="Faculty role facets")
    status: Dict[str, int] = Field(default_factory=dict, description="Status facets")
    category: Dict[str, int] = Field(default_factory=dict, description="Category facets")


class SearchResponse(BaseModel):
    """Response schema for search endpoint."""

    items: List[SearchResultItem] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Results per page")
    total_pages: int = Field(..., description="Total number of pages")
    facets: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        description="Facet counts for filtering"
    )
    query: str = Field(..., description="Original query string")


class SuggestionRequest(BaseModel):
    """Request schema for autocomplete suggestions."""

    query: str = Field(..., min_length=1, max_length=200, description="Partial search query")
    entity_type: str = Field(default='person', description="Entity type for suggestions")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum suggestions to return")

    @field_validator('entity_type')
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        """Validate entity type."""
        valid_types = {'person', 'rotation', 'procedure', 'assignment', 'swap'}
        if v not in valid_types:
            raise ValueError(f"Invalid entity type: {v}")
        return v


class SuggestionResponse(BaseModel):
    """Response schema for autocomplete suggestions."""

    suggestions: List[str] = Field(..., description="List of suggestions")
    query: str = Field(..., description="Original query string")
    entity_type: str = Field(..., description="Entity type")


class PeopleSearchRequest(BaseModel):
    """Specialized request schema for people search."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query text")
    type: Optional[str] = Field(None, description="Filter by type: resident or faculty")
    pgy_level: Optional[int] = Field(None, ge=1, le=3, description="Filter by PGY level")
    faculty_role: Optional[str] = Field(None, description="Filter by faculty role")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Results per page")

    @field_validator('type')
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate person type."""
        if v is not None and v not in ('resident', 'faculty'):
            raise ValueError("type must be 'resident' or 'faculty'")
        return v

    @field_validator('faculty_role')
    @classmethod
    def validate_faculty_role(cls, v: Optional[str]) -> Optional[str]:
        """Validate faculty role."""
        valid_roles = {'pd', 'apd', 'oic', 'dept_chief', 'sports_med', 'core'}
        if v is not None and v not in valid_roles:
            raise ValueError(f"Invalid faculty role: {v}")
        return v


class RotationSearchRequest(BaseModel):
    """Specialized request schema for rotation search."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query text")
    category: Optional[str] = Field(None, description="Filter by category")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Results per page")


class ProcedureSearchRequest(BaseModel):
    """Specialized request schema for procedure search."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query text")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Results per page")


class QuickSearchRequest(BaseModel):
    """Request schema for quick search."""

    query: str = Field(..., min_length=1, max_length=200, description="Search query text")
    entity_type: str = Field(default='person', description="Entity type to search")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results")

    @field_validator('entity_type')
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        """Validate entity type."""
        valid_types = {'person', 'rotation', 'procedure', 'assignment', 'swap'}
        if v not in valid_types:
            raise ValueError(f"Invalid entity type: {v}")
        return v


class QuickSearchResponse(BaseModel):
    """Response schema for quick search."""

    items: List[SearchResultItem] = Field(..., description="Search results")
    query: str = Field(..., description="Original query")
    entity_type: str = Field(..., description="Entity type searched")
