"""Pydantic schemas for Proxy Coverage Dashboard.

Shows "who is covering for whom" across the scheduling system including:
- Remote location surrogates
- Swap coverage (absorb and exchange)
- Backup call coverage
- Absence coverage
"""

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class CoverageType(str, Enum):
    """Type of coverage relationship."""

    REMOTE_SURROGATE = "remote_surrogate"  # Covering for someone at remote location
    SWAP_ABSORB = "swap_absorb"  # Absorbed shift (one-way swap)
    SWAP_EXCHANGE = "swap_exchange"  # Swapped shifts (bidirectional)
    BACKUP_CALL = "backup_call"  # Backup call coverage
    ABSENCE_COVERAGE = "absence_coverage"  # Covering for absent colleague
    TEMPORARY_PROXY = "temporary_proxy"  # General temporary proxy


class CoverageStatus(str, Enum):
    """Status of a coverage relationship."""

    ACTIVE = "active"  # Currently in effect
    SCHEDULED = "scheduled"  # Will become active in the future
    COMPLETED = "completed"  # Coverage period has ended
    CANCELLED = "cancelled"  # Was cancelled


class PersonRef(BaseModel):
    """Reference to a person for display."""

    id: UUID
    name: str
    pgy_level: int | None = Field(None, description="PGY level for residents")
    role_type: str | None = Field(
        None, description="Role type: resident, faculty, fellow"
    )


class CoverageRelationship(BaseModel):
    """A single coverage relationship between two people."""

    id: str = Field(..., description="Unique identifier")
    covering_person: PersonRef = Field(..., description="Person providing coverage")
    covered_person: PersonRef = Field(..., description="Person being covered for")
    coverage_type: CoverageType
    status: CoverageStatus
    start_date: date
    end_date: date | None = Field(None, description="End date, null if ongoing")
    location: str | None = Field(None, description="Location context if applicable")
    reason: str | None = Field(None, description="Reason for coverage")
    swap_id: UUID | None = Field(None, description="Related swap record ID")


class PersonCoverageSummary(BaseModel):
    """Summary of coverage relationships for a person."""

    person: PersonRef
    providing: list[CoverageRelationship] = Field(
        default_factory=list, description="Coverage this person provides"
    )
    receiving: list[CoverageRelationship] = Field(
        default_factory=list, description="Coverage this person receives"
    )


class CoverageCountByType(BaseModel):
    """Count of coverage by type."""

    remote_surrogate: int = 0
    swap_absorb: int = 0
    swap_exchange: int = 0
    backup_call: int = 0
    absence_coverage: int = 0
    temporary_proxy: int = 0


class TopCoverer(BaseModel):
    """Person providing most coverage."""

    person: PersonRef
    count: int


class CoverageStats(BaseModel):
    """Aggregated coverage statistics."""

    total_active: int = Field(0, description="Total active coverage relationships")
    total_scheduled: int = Field(0, description="Total scheduled for upcoming period")
    by_type: CoverageCountByType = Field(default_factory=CoverageCountByType)
    top_coverers: list[TopCoverer] = Field(
        default_factory=list, description="People providing most coverage"
    )
    most_covered: list[TopCoverer] = Field(
        default_factory=list, description="People being covered most"
    )


class ProxyCoverageResponse(BaseModel):
    """Response for proxy coverage dashboard endpoint."""

    date: date = Field(..., description="Date for which coverage is shown")
    active_coverage: list[CoverageRelationship] = Field(
        default_factory=list, description="All active coverage for the date"
    )
    upcoming_coverage: list[CoverageRelationship] = Field(
        default_factory=list, description="Upcoming scheduled coverage (next 7 days)"
    )
    by_coverer: list[PersonCoverageSummary] = Field(
        default_factory=list, description="Coverage grouped by person"
    )
    stats: CoverageStats = Field(default_factory=CoverageStats)
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="When data was generated"
    )


class ProxyCoverageFilter(BaseModel):
    """Filters for proxy coverage query."""

    coverage_type: CoverageType | None = None
    status: CoverageStatus | None = None
    person_id: UUID | None = Field(None, description="Filter by person (covering or covered)")
    start_date: date | None = None
    end_date: date | None = None
