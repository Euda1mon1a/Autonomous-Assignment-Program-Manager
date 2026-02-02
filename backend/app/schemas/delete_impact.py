"""Schemas for delete impact warnings."""

from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class DeleteImpactResource(str, Enum):
    person = "person"
    rotation_template = "rotation_template"
    block = "block"
    activity = "activity"
    academic_block = "academic_block"


class DeleteImpactDependency(BaseModel):
    table: str
    count: int
    columns: list[str]


class DeleteImpactResponse(BaseModel):
    resource_type: DeleteImpactResource
    resource_id: UUID
    dependencies: list[DeleteImpactDependency]
    total_dependents: int
