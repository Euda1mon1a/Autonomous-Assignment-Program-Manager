"""
Pydantic schemas for Block Quality Reports.

Used by:
- BlockQualityReportService
- MCP tools
- Celery tasks
- API responses
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class BlockDates(BaseModel):
    """Block date range."""

    block_number: int
    academic_year: int
    start_date: date
    end_date: date
    days: int
    slots: int  # days * 2


class BlockAssignmentEntry(BaseModel):
    """A1: Single block assignment entry."""

    name: str
    pgy_level: int
    rotation: str


class AbsenceEntry(BaseModel):
    """A2: Single absence entry."""

    name: str
    absence_type: str
    start_date: date
    end_date: date


class CallCoverageSummary(BaseModel):
    """A3: Call coverage summary."""

    sun_thu_count: int = Field(description="Call assignments Sun-Thu")
    fri_sat_count: int = Field(description="FMIT-covered Fri-Sat nights")
    total_nights: int


class FacultyPreloadedEntry(BaseModel):
    """A4: Faculty preloaded assignment."""

    name: str
    slots: int
    role: str | None = None


class RotationSummary(BaseModel):
    """B1: Rotation assignment summary."""

    rotation: str
    rotation_type: str
    count: int


class ResidentDistribution(BaseModel):
    """B2: Resident slot distribution."""

    name: str
    pgy_level: int
    count: int
    utilization_pct: float


class PersonAssignmentSummary(BaseModel):
    """C1: Combined person assignment summary."""

    name: str
    person_type: str  # resident or faculty
    pgy_level: int | None = None
    preloaded: int
    solved: int
    total: int
    utilization_pct: float


class NFOneInSevenEntry(BaseModel):
    """D2: Night Float 1-in-7 check."""

    name: str
    rotation: str
    work_days: int
    off_days: int
    status: str  # PASS or FAIL


class PostCallEntry(BaseModel):
    """D3: Post-call PCAT/DO check."""

    name: str
    call_date: date
    am_next_day: str | None = None
    pm_next_day: str | None = None
    status: str  # PASS, PARTIAL, NO PCAT/DO


class AccountabilityEntry(BaseModel):
    """E1/E2: Accountability entry."""

    name: str
    pgy_level: int | None = None
    role: str | None = None
    assigned: int
    unaccounted: int
    notes: str


class ExecutiveSummary(BaseModel):
    """Executive summary for quick review."""

    block_number: int
    date_range: str
    total_assignments: int
    resident_assignments: int
    faculty_assignments: int
    acgme_compliance_rate: float
    double_bookings: int
    call_coverage: str  # e.g., "28/28"
    nf_one_in_seven: str  # e.g., "PASS (4/4)"
    post_call_pcat_do: str  # e.g., "GAP" or "PASS"
    overall_status: str  # PASS or FAIL


class SectionA(BaseModel):
    """Section A: Preloaded Data."""

    block_assignments: list[BlockAssignmentEntry]
    absences: list[AbsenceEntry]
    call_coverage: CallCoverageSummary
    faculty_preloaded: list[FacultyPreloadedEntry]


class SectionB(BaseModel):
    """Section B: Solved Data."""

    by_rotation: list[RotationSummary]
    resident_distribution: list[ResidentDistribution]
    total_solved: int


class SectionC(BaseModel):
    """Section C: Combined Gap Analysis."""

    all_assignments: list[PersonAssignmentSummary]
    preloaded_total: int
    solved_total: int
    grand_total: int
    resident_range: str  # e.g., "40-48"
    faculty_range: str  # e.g., "22-24"
    gaps_detected: list[str]


class SectionD(BaseModel):
    """Section D: Post-Constraint Verification."""

    faculty_fmit_friday: str  # N/A or status
    nf_one_in_seven: list[NFOneInSevenEntry]
    post_call_pcat_do: list[PostCallEntry]
    post_call_gap_count: int


class SectionE(BaseModel):
    """Section E: Accountability."""

    resident_accountability: list[AccountabilityEntry]
    faculty_accountability: list[AccountabilityEntry]
    all_accounted: bool


class BlockQualityReport(BaseModel):
    """Complete block quality report."""

    block_dates: BlockDates
    executive_summary: ExecutiveSummary
    section_a: SectionA
    section_b: SectionB
    section_c: SectionC
    section_d: SectionD
    section_e: SectionE
    generated_at: str


class BlockSummaryEntry(BaseModel):
    """Single block in multi-block summary."""

    block_number: int
    dates: str
    days: int
    resident_count: int
    faculty_count: int
    total: int
    acgme_compliance: str
    nf_one_in_seven: str
    post_call: str
    status: str


class CrossBlockSummary(BaseModel):
    """Cross-block summary report."""

    academic_year: int
    blocks: list[BlockSummaryEntry]
    total_assignments: int
    total_resident: int
    total_faculty: int
    overall_status: str
    gaps_identified: list[str]
    generated_at: str
