"""Pydantic schemas for block schedule import API responses."""

from pydantic import BaseModel, Field


class ResidentRosterItem(BaseModel):
    """Single resident in parsed roster."""

    name: str = Field(..., description="Resident name (Last, First format)")
    template: str = Field(..., description="Rotation template (R1, R2, R3, etc.)")
    role: str = Field(..., description="PGY level (PGY 1, PGY 2, PGY 3, FAC)")
    row: int = Field(..., description="Row number in source spreadsheet")
    confidence: float = Field(
        1.0, ge=0.0, le=1.0, description="Name match confidence (0.0-1.0)"
    )


class ParsedFMITWeekSchema(BaseModel):
    """FMIT attending assignment for a single week."""

    block_number: int = Field(..., description="Block number (1-13)")
    week_number: int = Field(..., description="Week within block (1-4)")
    start_date: str | None = Field(None, description="Week start date (ISO format)")
    end_date: str | None = Field(None, description="Week end date (ISO format)")
    faculty_name: str = Field("", description="Assigned faculty name")
    is_holiday_call: bool = Field(False, description="True if holiday call week")


class ParsedBlockAssignmentSchema(BaseModel):
    """Single daily assignment extracted from block schedule."""

    person_name: str = Field(..., description="Person name")
    date: str = Field(..., description="Assignment date (ISO format)")
    template: str = Field(..., description="Rotation template")
    role: str = Field(..., description="Person role/PGY level")
    slot_am: str | None = Field(None, description="AM slot value")
    slot_pm: str | None = Field(None, description="PM slot value")
    row_idx: int = Field(0, description="Source row in spreadsheet")
    confidence: float = Field(1.0, description="Name match confidence")


class BlockParseResponse(BaseModel):
    """Full response from block schedule parsing."""

    success: bool = Field(..., description="True if parsing succeeded without errors")
    block_number: int = Field(..., description="Block number parsed")
    start_date: str | None = Field(None, description="Block start date (ISO format)")
    end_date: str | None = Field(None, description="Block end date (ISO format)")

    # Roster
    residents: list[ResidentRosterItem] = Field(
        default_factory=list, description="All parsed residents"
    )
    residents_by_template: dict[str, list[ResidentRosterItem]] = Field(
        default_factory=dict, description="Residents grouped by template"
    )

    # FMIT schedule
    fmit_schedule: list[ParsedFMITWeekSchema] = Field(
        default_factory=list, description="FMIT weekly assignments"
    )

    # Daily assignments (optional, can be large)
    assignments: list[ParsedBlockAssignmentSchema] = Field(
        default_factory=list, description="Daily assignments (AM/PM slots)"
    )

    # Parsing metadata
    warnings: list[str] = Field(
        default_factory=list, description="Parsing warnings (low confidence matches)"
    )
    errors: list[str] = Field(default_factory=list, description="Parsing errors")
    total_residents: int = Field(0, description="Total resident count")
    total_assignments: int = Field(0, description="Total assignment count")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "block_number": 10,
                "start_date": "2025-03-12",
                "end_date": "2025-04-08",
                "total_residents": 25,
                "residents_by_template": {
                    "R3": [
                        {
                            "name": "Doria, Russell",
                            "template": "R3",
                            "role": "PGY 3",
                            "row": 11,
                            "confidence": 1.0,
                        }
                    ],
                    "R2": [
                        {
                            "name": "Smith, Jane",
                            "template": "R2",
                            "role": "PGY 3",
                            "row": 19,
                            "confidence": 1.0,
                        }
                    ],
                },
                "fmit_schedule": [
                    {
                        "block_number": 10,
                        "week_number": 1,
                        "faculty_name": "Chu",
                        "is_holiday_call": False,
                    },
                    {
                        "block_number": 10,
                        "week_number": 2,
                        "faculty_name": "Bevis",
                        "is_holiday_call": False,
                    },
                ],
                "warnings": [],
                "errors": [],
            }
        }
