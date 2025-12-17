"""Calendar ICS export API routes.

Simplified calendar export endpoint that provides direct ICS file downloads
for individual person schedules with a clean query parameter interface.
"""
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.calendar_service import CalendarService

router = APIRouter()


@router.get("/export.ics")
def export_calendar_ics(
    person_id: UUID = Query(..., description="Person UUID to export schedule for"),
    start_date: date = Query(..., description="Start date for calendar export (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date for calendar export (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
) -> Response:
    """
    Export individual's schedule as ICS calendar file.

    Downloads an ICS (iCalendar) file containing all assignments for the specified person
    within the date range. The file can be imported into:
    - Google Calendar
    - Microsoft Outlook
    - Apple Calendar
    - Any other iCalendar-compatible application

    **ICS File Structure:**
    - VCALENDAR with proper headers (PRODID, VERSION, CALSCALE, METHOD)
    - VTIMEZONE component for America/New_York
    - VEVENT for each assignment with:
      - DTSTART/DTEND: Block start and end times (AM: 8-12, PM: 1-5)
      - SUMMARY: Activity name with role modifier
      - LOCATION: Clinic location if available
      - DESCRIPTION: Role, block, type, notes
      - UID: Unique identifier for the event

    **Query Parameters:**
    - person_id: UUID of the person whose schedule to export
    - start_date: Beginning of date range (inclusive), format: YYYY-MM-DD
    - end_date: End of date range (inclusive), format: YYYY-MM-DD

    **Example Request:**
    ```
    GET /api/calendar/export.ics?person_id=123e4567-e89b-12d3-a456-426614174000&start_date=2025-01-01&end_date=2025-12-31
    ```

    **Response:**
    - Content-Type: text/calendar
    - Content-Disposition: attachment with filename
    - Body: ICS file content in RFC 5545 format

    Args:
        person_id: UUID of the person
        start_date: Start date for export
        end_date: End date for export
        db: Database session (injected)

    Returns:
        ICS file as downloadable attachment

    Raises:
        404: Person not found
        500: Failed to generate calendar
    """
    try:
        # Generate ICS content using the calendar service
        ics_content = CalendarService.generate_ics_for_person(
            db=db,
            person_id=person_id,
            start_date=start_date,
            end_date=end_date,
            include_types=None,  # Include all activity types
        )

        # Return ICS file as download with proper headers
        return Response(
            content=ics_content,
            media_type="text/calendar",
            headers={
                "Content-Disposition": f'attachment; filename="schedule_{person_id}_{start_date}_{end_date}.ics"',
                "Content-Type": "text/calendar; charset=utf-8",
            },
        )
    except ValueError as e:
        # Person not found or invalid data
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Unexpected error during calendar generation
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate calendar: {str(e)}"
        )
