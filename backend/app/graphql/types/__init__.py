"""GraphQL type definitions."""

from app.graphql.types.assignment import (
    Assignment,
    AssignmentConnection,
    AssignmentCreateInput,
    AssignmentFilterInput,
    AssignmentRole,
    AssignmentUpdateInput,
    AssignmentWithWarnings,
    assignment_from_db,
)
from app.graphql.types.person import (
    FacultyRoleType,
    Person,
    PersonConnection,
    PersonCreateInput,
    PersonFilterInput,
    PersonUpdateInput,
    person_from_db,
)
from app.graphql.types.schedule import (
    Block,
    BlockConnection,
    BlockFilterInput,
    ScheduleFilterInput,
    ScheduleMetrics,
    ScheduleSummary,
    TimeOfDay,
    block_from_db,
)

__all__ = [
    # Person types
    "Person",
    "PersonConnection",
    "PersonCreateInput",
    "PersonUpdateInput",
    "PersonFilterInput",
    "FacultyRoleType",
    "person_from_db",
    # Assignment types
    "Assignment",
    "AssignmentConnection",
    "AssignmentCreateInput",
    "AssignmentUpdateInput",
    "AssignmentFilterInput",
    "AssignmentRole",
    "AssignmentWithWarnings",
    "assignment_from_db",
    # Schedule types
    "Block",
    "BlockConnection",
    "BlockFilterInput",
    "TimeOfDay",
    "ScheduleMetrics",
    "ScheduleSummary",
    "ScheduleFilterInput",
    "block_from_db",
]
