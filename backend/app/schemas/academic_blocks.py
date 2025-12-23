"""Academic block matrix schemas."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.validators.date_validators import validate_academic_year_date


class AcademicBlock(BaseModel):
    """
    Represents a rotation block period (typically 4 weeks).

    Groups the 730 daily half-day blocks into ~13 rotation periods.
    """

    block_number: int = Field(..., description="Academic block number (1-13)")
    start_date: date = Field(..., description="First date of the block")
    end_date: date = Field(..., description="Last date of the block")
    name: str | None = Field(
        None, description="Block name (e.g., 'Block 1', 'Block 2')"
    )

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_dates_in_range(cls, v: date) -> date:
        """Validate dates are within academic year bounds."""
        return validate_academic_year_date(v, field_name="date")

    @model_validator(mode="after")
    def validate_date_order(self) -> "AcademicBlock":
        """Ensure start_date is before or equal to end_date."""
        if self.start_date > self.end_date:
            raise ValueError(
                f"start_date ({self.start_date}) must be before or equal to "
                f"end_date ({self.end_date})"
            )
        return self


class ResidentRow(BaseModel):
    """Represents a row in the matrix (one resident)."""

    resident_id: UUID = Field(..., description="Resident UUID")
    name: str = Field(..., description="Resident name")
    pgy_level: int = Field(..., description="PGY level (1-3)")


class ACGMEStatus(BaseModel):
    """ACGME compliance status for a matrix cell."""

    is_compliant: bool = Field(..., description="Whether the cell is ACGME compliant")
    warnings: list[str] = Field(
        default_factory=list, description="List of ACGME warnings"
    )
    violations: list[str] = Field(
        default_factory=list, description="List of ACGME violations"
    )
    hours_worked: float = Field(..., description="Total hours worked in this block")
    max_hours_allowed: float = Field(80.0, description="Maximum hours allowed by ACGME")


class MatrixCell(BaseModel):
    """
    Represents a cell in the block matrix.

    Shows what rotation a resident is assigned to during a specific block,
    along with hours and compliance information.
    """

    row_index: int = Field(..., description="Row index (resident)")
    column_index: int = Field(..., description="Column index (block)")
    rotation: str | None = Field(None, description="Rotation name or abbreviation")
    rotation_full_name: str | None = Field(None, description="Full rotation name")
    hours: float = Field(..., description="Total hours in this block")
    acgme_status: ACGMEStatus = Field(..., description="ACGME compliance status")


class BlockMatrixResponse(BaseModel):
    """
    Complete block matrix response.

    Provides a grid view of residents (rows) × blocks (columns),
    showing rotation assignments and compliance for program coordinators.
    """

    columns: list[AcademicBlock] = Field(..., description="Academic blocks (columns)")
    rows: list[ResidentRow] = Field(..., description="Residents (rows)")
    cells: list[MatrixCell] = Field(..., description="Matrix cells with assignments")
    academic_year: str = Field(..., description="Academic year (e.g., '2024-2025')")
    summary: dict = Field(
        default_factory=dict,
        description="Summary statistics (total residents, blocks, compliance rate)",
    )


class BlockSummary(BaseModel):
    """Summary statistics for an academic block."""

    block_number: int
    name: str
    start_date: date
    end_date: date
    total_assignments: int = Field(..., description="Total assignments in this block")
    total_residents: int = Field(..., description="Number of residents assigned")
    compliance_rate: float = Field(
        ..., description="Percentage of compliant assignments (0-100)"
    )
    average_hours: float = Field(..., description="Average hours per resident")

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_dates_in_range(cls, v: date) -> date:
        """Validate dates are within academic year bounds."""
        return validate_academic_year_date(v, field_name="date")


class BlockListResponse(BaseModel):
    """Response for listing academic blocks."""

    blocks: list[BlockSummary] = Field(..., description="List of academic blocks")
    academic_year: str = Field(..., description="Academic year")
    total_blocks: int = Field(..., description="Total number of blocks")
