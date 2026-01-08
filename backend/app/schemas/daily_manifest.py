"""Daily Manifest schemas - for "Where is everyone NOW" clinic view.

V2 redesign focuses on:
- Situational awareness (FMIT team, night rotation, attending)
- Both AM and PM shown simultaneously
- Remote locations (Hilo, Okinawa, Kapiolani) show who's away + surrogate
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PersonSummary(BaseModel):
    """Summary of person for manifest display."""

    id: UUID
    name: str
    pgy_level: int | None = Field(None, description="PGY level for residents")


class AssignmentSummary(BaseModel):
    """Summary of an assignment for manifest display."""

    person: PersonSummary
    role: str = Field(..., description="primary, supervising, or backup")
    activity: str = Field(..., description="Activity name or override")


class StaffingSummary(BaseModel):
    """Staffing summary for a location."""

    total: int = Field(..., description="Total number of people")
    residents: int = Field(..., description="Number of residents")
    faculty: int = Field(..., description="Number of faculty")


class LocationManifest(BaseModel):
    """Manifest for a single clinic location."""

    clinic_location: str | None = Field(None, description="Clinic location name")
    time_slots: dict[str, list[AssignmentSummary]] = Field(
        ...,
        description="Time slots (AM/PM) with assignments",
    )
    staffing_summary: StaffingSummary


class DailyManifestResponse(BaseModel):
    """Response for daily manifest endpoint."""

    date: date
    time_of_day: str | None = Field(None, description="AM or PM, or None for all day")
    locations: list[LocationManifest]
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this manifest was generated",
    )


# ============================================================================
# V2 Schemas - Redesigned for nursing staff / front desk
# ============================================================================


class FMITSection(BaseModel):
    """Family Medicine Inpatient Team - NOT in clinic today.

    Shows who is on inpatient service so staff know not to expect them.
    """

    attending: PersonSummary | None = Field(
        None, description="Attending physician for inpatient"
    )
    residents: list[PersonSummary] = Field(
        default_factory=list, description="Residents on FMIT"
    )


class NightCallInfo(BaseModel):
    """Night rotation information.

    Shows who is on night call so staff know they're unavailable during day.
    """

    person: PersonSummary
    call_type: str = Field("night", description="Type of call (night, backup)")


class RemoteAssignment(BaseModel):
    """Remote location assignment (Hilo, Okinawa, Kapiolani).

    Shows who is away at a remote site and their local surrogate/proxy.
    """

    person: PersonSummary
    location: str = Field(..., description="Remote location name")
    surrogate: PersonSummary | None = Field(
        None, description="Local proxy/surrogate if assigned"
    )


class AbsenceInfo(BaseModel):
    """Absence information for situational awareness.

    Shows who is absent and why (vacation, sick, deployment, etc.)
    """

    person: PersonSummary
    absence_type: str = Field(..., description="Type of absence (vacation, sick, deployment)")


class AttendingInfo(BaseModel):
    """Attending physician info for at-a-glance display."""

    am: PersonSummary | None = Field(None, description="AM attending")
    pm: PersonSummary | None = Field(None, description="PM attending")


class HalfDayStaff(BaseModel):
    """Staff assignments for a single half-day (AM or PM)."""

    assignments: list[AssignmentSummary] = Field(
        default_factory=list, description="Assignments for this half-day"
    )
    count: int = Field(0, description="Total people assigned")


class LocationManifestV2(BaseModel):
    """Manifest for a clinic location - V2 with AM/PM columns.

    Designed for table display with Location | AM | PM columns.
    """

    location: str = Field(..., description="Clinic location name")
    am: HalfDayStaff = Field(default_factory=HalfDayStaff)
    pm: HalfDayStaff = Field(default_factory=HalfDayStaff)


# ============================================================================
# Person-centric schemas for DayView-style layout
# ============================================================================


class AssignmentInfo(BaseModel):
    """Assignment details for a half-day (without person info)."""

    activity: str = Field(..., description="Activity type (e.g., clinical, leave)")
    abbreviation: str = Field(..., description="Short code (e.g., CL, PR)")
    role: str = Field(..., description="Role (primary, supervising, backup)")


class PersonClinicCoverage(BaseModel):
    """Person-centric clinic coverage for DayView-style layout.

    Shows person with their AM and PM assignments (if any).
    """

    person: PersonSummary
    am: AssignmentInfo | None = Field(None, description="AM assignment")
    pm: AssignmentInfo | None = Field(None, description="PM assignment")


class SituationalAwareness(BaseModel):
    """Top section - who is NOT in clinic and why.

    Critical for nursing/front desk to know who to NOT expect.
    """

    fmit_team: FMITSection = Field(
        default_factory=FMITSection, description="Inpatient team"
    )
    night_rotation: list[NightCallInfo] = Field(
        default_factory=list, description="People on night call"
    )
    remote_assignments: list[RemoteAssignment] = Field(
        default_factory=list, description="People at remote sites"
    )
    absences: list[AbsenceInfo] = Field(
        default_factory=list, description="People with absences (vacation, sick, etc.)"
    )


class DailyManifestResponseV2(BaseModel):
    """V2 Response - redesigned for nursing staff / front desk.

    Key changes:
    - Shows both AM and PM (no toggle)
    - Situational awareness at top (FMIT, nights, remote, absences)
    - Attending at-a-glance
    - Clinic coverage as Person | AM | PM (DayView-style layout)
    """

    date: date

    # Situational awareness - who is NOT in clinic
    situational_awareness: SituationalAwareness = Field(
        default_factory=SituationalAwareness
    )

    # At-a-glance: today's attending
    attending: AttendingInfo = Field(default_factory=AttendingInfo)

    # Clinic coverage (Person | AM | PM format)
    clinic_coverage: list[PersonClinicCoverage] = Field(
        default_factory=list, description="Clinic staffing by person (DayView style)"
    )

    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this manifest was generated",
    )
