"""Pydantic schemas for API validation."""
from app.schemas.person import PersonCreate, PersonUpdate, PersonResponse, PersonListResponse
from app.schemas.block import BlockCreate, BlockResponse, BlockListResponse
from app.schemas.rotation_template import (
    RotationTemplateCreate,
    RotationTemplateUpdate,
    RotationTemplateResponse,
    RotationTemplateListResponse,
)
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate, AssignmentResponse
from app.schemas.absence import AbsenceCreate, AbsenceUpdate, AbsenceResponse
from app.schemas.schedule import ScheduleRequest, ScheduleResponse, ValidationResult

__all__ = [
    "PersonCreate",
    "PersonUpdate",
    "PersonResponse",
    "PersonListResponse",
    "BlockCreate",
    "BlockResponse",
    "BlockListResponse",
    "RotationTemplateCreate",
    "RotationTemplateUpdate",
    "RotationTemplateResponse",
    "RotationTemplateListResponse",
    "AssignmentCreate",
    "AssignmentUpdate",
    "AssignmentResponse",
    "AbsenceCreate",
    "AbsenceUpdate",
    "AbsenceResponse",
    "ScheduleRequest",
    "ScheduleResponse",
    "ValidationResult",
]
