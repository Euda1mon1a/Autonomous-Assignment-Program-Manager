"""GraphQL types for Schedule and Block entities."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

import strawberry
from strawberry.scalars import JSON


@strawberry.enum
class TimeOfDay(str):
    """Time of day for blocks."""
    AM = "AM"
    PM = "PM"


@strawberry.type
class Block:
    """Block GraphQL type (half-day scheduling unit)."""
    id: strawberry.ID
    date: date
    time_of_day: TimeOfDay
    block_number: int
    is_weekend: bool = False
    is_holiday: bool = False
    holiday_name: Optional[str] = None

    @strawberry.field
    def display_name(self) -> str:
        """Get display name for this block."""
        return f"{self.date.strftime('%Y-%m-%d')} {self.time_of_day}"

    @strawberry.field
    def is_workday(self) -> bool:
        """Check if this is a regular workday."""
        return not self.is_weekend and not self.is_holiday


@strawberry.input
class BlockFilterInput:
    """Filter input for querying blocks."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    time_of_day: Optional[TimeOfDay] = None
    is_weekend: Optional[bool] = None
    is_holiday: Optional[bool] = None
    block_number: Optional[int] = None


@strawberry.type
class BlockConnection:
    """Paginated block results."""
    items: list[Block]
    total: int
    has_next_page: bool
    has_previous_page: bool


@strawberry.type
class ScheduleMetrics:
    """Schedule-wide metrics and statistics."""
    total_assignments: int
    total_blocks: int
    coverage_percentage: float
    acgme_compliance_score: float
    average_utilization: float


@strawberry.type
class ScheduleSummary:
    """High-level schedule summary."""
    start_date: date
    end_date: date
    total_people: int
    total_blocks: int
    total_assignments: int
    metrics: ScheduleMetrics


@strawberry.input
class ScheduleFilterInput:
    """Filter input for querying schedule data."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    person_ids: Optional[list[strawberry.ID]] = None
    include_weekends: bool = True
    include_holidays: bool = True


def block_from_db(db_block) -> Block:
    """Convert database Block model to GraphQL type."""
    return Block(
        id=strawberry.ID(str(db_block.id)),
        date=db_block.date,
        time_of_day=TimeOfDay(db_block.time_of_day),
        block_number=db_block.block_number,
        is_weekend=db_block.is_weekend or False,
        is_holiday=db_block.is_holiday or False,
        holiday_name=db_block.holiday_name,
    )
