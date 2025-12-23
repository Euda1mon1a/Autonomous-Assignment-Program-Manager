"""GraphQL types for Person entity."""

from datetime import datetime
from enum import Enum

import strawberry


@strawberry.enum
class FacultyRoleType(str, Enum):
    """Faculty role types."""

    PD = "pd"
    APD = "apd"
    OIC = "oic"
    DEPT_CHIEF = "dept_chief"
    SPORTS_MED = "sports_med"
    CORE = "core"


@strawberry.type
class Person:
    """Person GraphQL type (Resident or Faculty)."""

    id: strawberry.ID
    name: str
    type: str
    email: str | None = None
    pgy_level: int | None = None
    target_clinical_blocks: int | None = None
    performs_procedures: bool = False
    specialties: list[str] | None = None
    primary_duty: str | None = None
    faculty_role: FacultyRoleType | None = None
    sunday_call_count: int = 0
    weekday_call_count: int = 0
    fmit_weeks_count: int = 0
    created_at: datetime
    updated_at: datetime

    @strawberry.field
    def is_resident(self) -> bool:
        """Check if person is a resident."""
        return self.type == "resident"

    @strawberry.field
    def is_faculty(self) -> bool:
        """Check if person is faculty."""
        return self.type == "faculty"

    @strawberry.field
    def supervision_ratio(self) -> int:
        """
        Get ACGME supervision ratio.
        PGY-1: 1:2, PGY-2/3: 1:4
        """
        if not self.is_resident:
            return 0
        return 2 if self.pgy_level == 1 else 4


@strawberry.input
class PersonCreateInput:
    """Input type for creating a person."""

    name: str
    type: str
    email: str | None = None
    pgy_level: int | None = None
    target_clinical_blocks: int | None = None
    performs_procedures: bool = False
    specialties: list[str] | None = None
    primary_duty: str | None = None
    faculty_role: FacultyRoleType | None = None


@strawberry.input
class PersonUpdateInput:
    """Input type for updating a person."""

    name: str | None = None
    email: str | None = None
    pgy_level: int | None = None
    target_clinical_blocks: int | None = None
    performs_procedures: bool | None = None
    specialties: list[str] | None = None
    primary_duty: str | None = None
    faculty_role: FacultyRoleType | None = None


@strawberry.input
class PersonFilterInput:
    """Filter input for querying persons."""

    type: str | None = None
    pgy_level: int | None = None
    faculty_role: FacultyRoleType | None = None
    performs_procedures: bool | None = None


@strawberry.type
class PersonConnection:
    """Paginated person results."""

    items: list[Person]
    total: int
    has_next_page: bool
    has_previous_page: bool


def person_from_db(db_person) -> Person:
    """Convert database Person model to GraphQL type."""
    return Person(
        id=strawberry.ID(str(db_person.id)),
        name=db_person.name,
        type=db_person.type,
        email=db_person.email,
        pgy_level=db_person.pgy_level,
        target_clinical_blocks=db_person.target_clinical_blocks,
        performs_procedures=db_person.performs_procedures or False,
        specialties=db_person.specialties,
        primary_duty=db_person.primary_duty,
        faculty_role=(
            FacultyRoleType(db_person.faculty_role) if db_person.faculty_role else None
        ),
        sunday_call_count=db_person.sunday_call_count or 0,
        weekday_call_count=db_person.weekday_call_count or 0,
        fmit_weeks_count=db_person.fmit_weeks_count or 0,
        created_at=db_person.created_at,
        updated_at=db_person.updated_at,
    )
