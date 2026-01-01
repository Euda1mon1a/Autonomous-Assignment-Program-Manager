"""Daily Manifest API routes.

Answers "Where is everyone NOW" - critical for clinic staff.
Shows current staffing at each location with real-time assignments.
"""

from collections import defaultdict
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.user import User
from app.schemas.daily_manifest import (
    AssignmentSummary,
    DailyManifestResponse,
    LocationManifest,
    PersonSummary,
    StaffingSummary,
)

router = APIRouter()


@router.get("/daily-manifest", response_model=DailyManifestResponse)
async def get_daily_manifest(
    date_param: date = Query(..., alias="date", description="Date for the manifest"),
    time_of_day: str | None = Query(
        None, description="AM or PM (optional, shows all if omitted)"
    ),
    db: AsyncSession = Depends(get_async_db),
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
