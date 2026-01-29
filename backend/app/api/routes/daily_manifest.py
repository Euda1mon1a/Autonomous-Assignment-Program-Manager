"""Daily Manifest API routes.

Answers "Where is everyone NOW" - critical for clinic staff.
Shows current staffing at each location with real-time assignments.

V2 redesign focuses on nursing/front desk:
- Situational awareness (FMIT, nights, remote)
- Both AM and PM shown
- Attending at-a-glance
"""

from collections import defaultdict
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.call_assignment import CallAssignment
from app.models.call_override import CallOverride
from app.models.person import Person
from app.models.user import User
from app.schemas.daily_manifest import (
    AbsenceInfo,
    AssignmentInfo,
    AssignmentSummary,
    AttendingInfo,
    DailyManifestResponse,
    DailyManifestResponseV2,
    FMITSection,
    HalfDayStaff,
    LocationManifest,
    LocationManifestV2,
    NightCallInfo,
    PersonClinicCoverage,
    PersonSummary,
    RemoteAssignment,
    SituationalAwareness,
    StaffingSummary,
)

# Remote locations - NOT in main clinic
REMOTE_LOCATIONS = {"Hilo", "Okinawa", "Kapiolani"}

# FM Clinic abbreviations - rotations that happen IN the Family Medicine clinic
# Filter to ONLY these for the daily manifest (everything else is excluded)
# Based on actual database rotation_templates values:
#   CL = Clinic, PR = Procedures
# Exclusions (handled separately):
#   FM = FMIT (inpatient) -> situational awareness
#   NF = Night Float -> away section
#   IP = Inpatient, CA = Call -> not in FM clinic
#   CF = Conference, VA = Vacation, PC = Post-Call -> not patient care
FM_CLINIC_ABBREVIATIONS = {
    "CL",  # Clinic (main FM clinic rotation)
    "PR",  # Procedures
}


def is_fm_clinic_rotation(assignment) -> bool:
    """Check if assignment is a FM clinic rotation (should show on manifest)."""
    # Get abbreviation from rotation template
    abbrev = None
    if assignment.rotation_template:
        abbrev = (
            assignment.rotation_template.display_abbreviation
            or assignment.rotation_template.abbreviation
        )

    # Get activity override
    override = assignment.activity_override

    # Check if abbreviation or override matches any FM clinic pattern
    for pattern in FM_CLINIC_ABBREVIATIONS:
        # Match abbreviation (strip time suffix like -AM/-PM)
        if abbrev:
            abbrev_upper = abbrev.upper().split("-")[0]  # "C-AM" -> "C"
            if abbrev_upper == pattern or abbrev.upper().startswith(pattern + "-"):
                return True
        # Match activity override
        if override:
            override_upper = override.upper().split("-")[0]
            if override_upper == pattern or override.upper().startswith(pattern + "-"):
                return True

    return False


router = APIRouter()


@router.get("/daily-manifest", response_model=DailyManifestResponse)
async def get_daily_manifest(
    date_param: date = Query(..., alias="date", description="Date for the manifest"),
    time_of_day: str | None = Query(
        None, description="AM or PM (optional, shows all if omitted)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get daily manifest showing where everyone is assigned.

    Returns staffing by location for the specified date and time.
    Critical for clinic staff to know current assignments.

    Query Parameters:
    - date: The date to query (required, format: YYYY-MM-DD)
    - time_of_day: AM or PM (optional, shows all if omitted)

    Example: GET /api/assignments/daily-manifest?date=2025-01-15&time_of_day=AM
    """
    # Validate time_of_day if provided
    if time_of_day and time_of_day not in ("AM", "PM"):
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="time_of_day must be 'AM' or 'PM' if provided",
        )

    # Query assignments for the given date
    query = (
        db.query(Assignment)
        .join(Block, Assignment.block_id == Block.id)
        .join(Person, Assignment.person_id == Person.id)
        .options(
            joinedload(Assignment.person),
            joinedload(Assignment.block),
            joinedload(Assignment.rotation_template),
        )
        .filter(Block.date == date_param)
    )

    # Filter by time_of_day if specified
    if time_of_day:
        query = query.filter(Block.time_of_day == time_of_day)

    # Order by time of day and person name for consistent display
    query = query.order_by(Block.time_of_day, Person.name)

    assignments = query.all()

    # Group assignments by location and time slot
    location_data = defaultdict(lambda: {"AM": [], "PM": []})

    for assignment in assignments:
        # Get clinic location from rotation template
        clinic_location = "Unassigned"
        if (
            assignment.rotation_template
            and assignment.rotation_template.clinic_location
        ):
            clinic_location = assignment.rotation_template.clinic_location

        # Get activity name
        activity = assignment.activity_name

        # Get time slot from block
        time_slot = assignment.block.time_of_day

        # Create person summary
        person_summary = PersonSummary(
            id=assignment.person.id,
            name=assignment.person.name,
            pgy_level=assignment.person.pgy_level,
        )

        # Create assignment summary
        assignment_summary = AssignmentSummary(
            person=person_summary,
            role=assignment.role,
            activity=activity,
        )

        # Add to location data
        location_data[clinic_location][time_slot].append(assignment_summary)

    # Build location manifests with staffing summaries
    locations = []
    for clinic_location, time_slots in location_data.items():
        # Calculate staffing summary across all time slots
        all_assignments = []
        for slot_assignments in time_slots.values():
            all_assignments.extend(slot_assignments)

        total = len(all_assignments)
        residents = sum(1 for a in all_assignments if a.person.pgy_level is not None)
        faculty = total - residents

        staffing_summary = StaffingSummary(
            total=total,
            residents=residents,
            faculty=faculty,
        )

        location_manifest = LocationManifest(
            clinic_location=clinic_location,
            time_slots=time_slots,
            staffing_summary=staffing_summary,
        )
        locations.append(location_manifest)

    # Sort locations by name for consistent display (Unassigned last)
    locations.sort(
        key=lambda loc: (loc.clinic_location == "Unassigned", loc.clinic_location or "")
    )

    return DailyManifestResponse(
        date=date_param,
        time_of_day=time_of_day,
        locations=locations,
        generated_at=datetime.utcnow(),
    )


@router.get("/daily-manifest/v2", response_model=DailyManifestResponseV2)
async def get_daily_manifest_v2(
    date_param: date = Query(..., alias="date", description="Date for the manifest"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get daily manifest V2 - redesigned for nursing/front desk.

    Returns:
    - Situational awareness: FMIT team, night rotation, remote assignments
    - Attending at-a-glance: AM and PM attending physicians
    - Clinic coverage: Location × AM/PM table

    Example: GET /api/assignments/daily-manifest/v2?date=2025-01-15
    """
    # Query all assignments for the date
    assignments_query = (
        db.query(Assignment)
        .join(Block, Assignment.block_id == Block.id)
        .join(Person, Assignment.person_id == Person.id)
        .options(
            joinedload(Assignment.person),
            joinedload(Assignment.block),
            joinedload(Assignment.rotation_template),
        )
        .filter(Block.date == date_param)
        .order_by(Block.time_of_day, Person.name)
    )
    assignments = assignments_query.all()

    # Query call assignments for the date (night call)
    call_assignments = (
        db.query(CallAssignment)
        .options(joinedload(CallAssignment.person))
        .filter(CallAssignment.date == date_param)
        .all()
    )
    if call_assignments:
        call_ids = [c.id for c in call_assignments]
        call_overrides = (
            db.query(CallOverride)
            .options(joinedload(CallOverride.replacement_person))
            .filter(CallOverride.call_assignment_id.in_(call_ids))
            .filter(CallOverride.is_active.is_(True))
            .all()
        )
        override_map = {o.call_assignment_id: o for o in call_overrides}
        updated_calls = []
        for call in call_assignments:
            override = override_map.get(call.id)
            if not override or not override.replacement_person:
                updated_calls.append(call)
                continue
            clone = CallAssignment(
                id=call.id,
                date=call.date,
                person_id=override.replacement_person.id,
                call_type=call.call_type,
                is_weekend=call.is_weekend,
                is_holiday=call.is_holiday,
                created_at=call.created_at,
            )
            clone.person = override.replacement_person
            updated_calls.append(clone)
        call_assignments = updated_calls

    # Query absences that overlap with the date
    absences_query = (
        db.query(Absence)
        .options(joinedload(Absence.person))
        .filter(Absence.start_date <= date_param)
        .filter(Absence.end_date >= date_param)
        .all()
    )

    # === Build Situational Awareness ===

    # 1. FMIT Team
    fmit_attending = None
    fmit_residents = []

    # 2. Remote assignments
    remote_assignments = []

    # 3. Night rotation (from NF/LDNF assignments AND call assignments)
    night_rotation = []

    # 4. Track attending for AM/PM
    attending_am = None
    attending_pm = None

    # 5. Absences for situational awareness
    absence_list = []
    for absence in absences_query:
        person_summary = PersonSummary(
            id=absence.person.id,
            name=absence.person.name,
            pgy_level=absence.person.pgy_level,
        )
        absence_list.append(
            AbsenceInfo(person=person_summary, absence_type=absence.absence_type)
        )

    # Clinic coverage by person (Person | AM | PM format)
    # Key: person_id, Value: {person, am, pm}
    person_clinic_data: dict[str, dict] = {}

    for assignment in assignments:
        person = assignment.person
        rotation = assignment.rotation_template
        block = assignment.block
        time_slot = block.time_of_day

        # Build person summary
        person_summary = PersonSummary(
            id=person.id,
            name=person.name,
            pgy_level=person.pgy_level,
        )

        # Get abbreviation for routing logic
        abbrev = None
        if rotation:
            abbrev = rotation.display_abbreviation or rotation.abbreviation
            abbrev = abbrev.upper() if abbrev else None

        # Check if FMIT - goes to situational awareness (abbreviation = "FM")
        if abbrev == "FM":
            if assignment.role == "supervising":
                fmit_attending = person_summary
            else:
                fmit_residents.append(person_summary)
            continue  # Don't add to clinic coverage

        # Check if Night rotation - goes to "away" section (NF = Night Float, LDNF = Long Days/Night Float)
        if abbrev in ("NF", "LDNF"):
            # Add to night_rotation with special call_type
            night_rotation.append(
                NightCallInfo(person=person_summary, call_type="night_float")
            )
            continue  # Don't add to clinic coverage

        # Check for remote location - goes to "away" section
        clinic_location = rotation.clinic_location if rotation else None
        if clinic_location and clinic_location in REMOTE_LOCATIONS:
            remote_assignments.append(
                RemoteAssignment(
                    person=person_summary,
                    location=clinic_location,
                    surrogate=None,
                )
            )
            continue  # Don't add to clinic coverage

        # Check if this is an FM clinic rotation (filter to only these)
        if not is_fm_clinic_rotation(assignment):
            continue  # Skip non-FM-clinic rotations

        # Check for attending (supervising role) - shown in banner AND table
        if assignment.role == "supervising":
            if time_slot == "AM":
                attending_am = person_summary
            else:
                attending_pm = person_summary

        # Get activity name and abbreviation for display
        activity = assignment.activity_name
        abbrev_display = abbrev or "?"

        # Build assignment info (without person, since grouped by person)
        assignment_info = AssignmentInfo(
            activity=activity,
            abbreviation=abbrev_display,
            role=assignment.role,
        )

        # Add to person clinic data (grouped by person)
        person_id = str(person.id)
        if person_id not in person_clinic_data:
            person_clinic_data[person_id] = {
                "person": person_summary,
                "am": None,
                "pm": None,
            }

        # Set AM or PM assignment
        if time_slot == "AM":
            person_clinic_data[person_id]["am"] = assignment_info
        else:
            person_clinic_data[person_id]["pm"] = assignment_info

    # 5. Add call assignments to night rotation
    for call in call_assignments:
        # 'weekday' and 'sunday' are overnight call types
        if call.call_type in ("weekday", "sunday"):
            person_summary = PersonSummary(
                id=call.person.id,
                name=call.person.name,
                pgy_level=call.person.pgy_level,
            )
            night_rotation.append(
                NightCallInfo(person=person_summary, call_type=call.call_type)
            )

    # === Build Response ===

    # Build FMIT section
    fmit_section = FMITSection(attending=fmit_attending, residents=fmit_residents)

    # Deduplicate remote assignments by person ID
    seen_remote = set()
    unique_remote = []
    for ra in remote_assignments:
        if ra.person.id not in seen_remote:
            seen_remote.add(ra.person.id)
            unique_remote.append(ra)

    # Build situational awareness (with absences)
    situational_awareness = SituationalAwareness(
        fmit_team=fmit_section,
        night_rotation=night_rotation,
        remote_assignments=unique_remote,
        absences=absence_list,
    )

    # Build attending info
    attending = AttendingInfo(am=attending_am, pm=attending_pm)

    # Build clinic coverage (Person | AM | PM format)
    # Sort by PGY level (1, 2, 3, then Faculty/None), then name
    def sort_key(item):
        person = item["person"]
        # PGY level: 1, 2, 3 come first; None (faculty) comes last as 999
        pgy = person.pgy_level if person.pgy_level is not None else 999
        return (pgy, person.name.lower())

    sorted_people = sorted(person_clinic_data.values(), key=sort_key)

    clinic_coverage = [
        PersonClinicCoverage(
            person=p["person"],
            am=p["am"],
            pm=p["pm"],
        )
        for p in sorted_people
    ]

    return DailyManifestResponseV2(
        date=date_param,
        situational_awareness=situational_awareness,
        attending=attending,
        clinic_coverage=clinic_coverage,
        generated_at=datetime.utcnow(),
    )
