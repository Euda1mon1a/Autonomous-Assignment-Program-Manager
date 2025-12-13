"""Schedule-related schemas."""
from datetime import date
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class ScheduleRequest(BaseModel):
    """Request schema for schedule generation."""
    start_date: date
    end_date: date
    pgy_levels: Optional[list[int]] = None  # Filter residents by PGY level
    rotation_template_ids: Optional[list[UUID]] = None  # Specific templates to use
    algorithm: str = "greedy"  # 'greedy', 'min_conflicts', 'cp_sat'


class Violation(BaseModel):
    """Schema for a single ACGME violation."""
    type: str  # 'SUPERVISION_RATIO', '80_HOUR', '1_IN_7', etc.
    severity: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    person_id: Optional[UUID] = None
    person_name: Optional[str] = None
    block_id: Optional[UUID] = None
    message: str
    details: Optional[dict] = None


class ValidationResult(BaseModel):
    """Schema for ACGME validation results."""
    valid: bool
    total_violations: int
    violations: list[Violation]
    coverage_rate: float  # Percentage of blocks covered
    statistics: Optional[dict] = None


class ScheduleResponse(BaseModel):
    """Response schema for schedule generation."""
    status: str  # 'success', 'partial', 'failed'
    message: str
    total_blocks_assigned: int
    total_blocks: int
    validation: ValidationResult
    run_id: Optional[UUID] = None


class EmergencyRequest(BaseModel):
    """Request schema for emergency coverage."""
    person_id: UUID
    start_date: date
    end_date: date
    reason: str
    is_deployment: bool = False


class EmergencyResponse(BaseModel):
    """Response schema for emergency coverage."""
    status: str  # 'success', 'partial', 'failed'
    replacements_found: int
    coverage_gaps: int
    requires_manual_review: bool
    details: list[dict]
