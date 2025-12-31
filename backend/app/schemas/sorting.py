"""
Sorting parameter schemas for API requests.
"""

from enum import Enum
from pydantic import BaseModel, Field, field_validator


class SortOrder(str, Enum):
    """Sort order enumeration."""

    ASC = "asc"
    DESC = "desc"


class SortParams(BaseModel):
    """Sorting parameters for requests."""

    sort_by: str = Field(..., description="Field to sort by")
    sort_order: SortOrder = Field(SortOrder.ASC, description="Sort order (asc, desc)")


class MultiSortParams(BaseModel):
    """Multiple field sorting parameters."""

    sorts: list[SortParams] = Field(
        ..., description="List of sort parameters", min_length=1, max_length=5
    )

    @field_validator("sorts")
    @classmethod
    def validate_sorts(cls, v: list[SortParams]) -> list[SortParams]:
        """Validate sort list is not too long."""
        if len(v) > 5:
            raise ValueError("Cannot sort by more than 5 fields")
        return v


class PersonSortField(str, Enum):
    """Valid sort fields for Person."""

    NAME = "name"
    TYPE = "type"
    PGY_LEVEL = "pgy_level"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class PersonSort(BaseModel):
    """Sort parameters for Person queries."""

    sort_by: PersonSortField = Field(
        PersonSortField.NAME, description="Field to sort by"
    )
    sort_order: SortOrder = Field(SortOrder.ASC, description="Sort order")


class AssignmentSortField(str, Enum):
    """Valid sort fields for Assignment."""

    DATE = "date"
    PERSON_NAME = "person_name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class AssignmentSort(BaseModel):
    """Sort parameters for Assignment queries."""

    sort_by: AssignmentSortField = Field(
        AssignmentSortField.DATE, description="Field to sort by"
    )
    sort_order: SortOrder = Field(SortOrder.ASC, description="Sort order")


class BlockSortField(str, Enum):
    """Valid sort fields for Block."""

    DATE = "date"
    SESSION = "session"
    CREATED_AT = "created_at"


class BlockSort(BaseModel):
    """Sort parameters for Block queries."""

    sort_by: BlockSortField = Field(BlockSortField.DATE, description="Field to sort by")
    sort_order: SortOrder = Field(SortOrder.ASC, description="Sort order")


class SwapSortField(str, Enum):
    """Valid sort fields for Swap."""

    CREATED_AT = "created_at"
    EXECUTED_AT = "executed_at"
    STATUS = "status"


class SwapSort(BaseModel):
    """Sort parameters for Swap queries."""

    sort_by: SwapSortField = Field(
        SwapSortField.CREATED_AT, description="Field to sort by"
    )
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort order")
