"""Calendar export API routes."""
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.calendar import (
    CalendarSubscriptionCreate,
    CalendarSubscriptionResponse,
)
from app.services.calendar_service import CalendarService

router = APIRouter()


@router.get("/export/person/{person_id}")
def export_person_calendar(
    person_id: UUID,
    start_date: date = Query(..., description="Start date for calendar export"),
    end_date: date = Query(..., description="End date for calendar export"),
    include_types: Optional[list[str]] = Query(None, description="Activity types to include"),
    db: Session = Depends(get_db),
) -> Response:
    """
    Export calendar for a person as ICS file.

    Downloads an ICS file containing all assignments for the specified person
    within the date range. Can be imported into Google Calendar, Outlook, or Apple Calendar.

    Args:
        person_id: Person UUID
        start_date: Start date for export (YYYY-MM-DD)
        end_date: End date for export (YYYY-MM-DD)
        include_types: Optional list of activity types to filter
        db: Database session

    Returns:
        ICS file download
    """
    try:
        ics_content = CalendarService.generate_ics_for_person(
            db=db,
            person_id=person_id,
            start_date=start_date,
            end_date=end_date,
            include_types=include_types,
        )

        # Return ICS file as download
        return Response(
            content=ics_content,
            media_type="text/calendar",
            headers={
                "Content-Disposition": f'attachment; filename="schedule_{person_id}_{start_date}_{end_date}.ics"'
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate calendar: {str(e)}")


@router.get("/export/rotation/{rotation_id}")
def export_rotation_calendar(
    rotation_id: UUID,
    start_date: date = Query(..., description="Start date for calendar export"),
    end_date: date = Query(..., description="End date for calendar export"),
    db: Session = Depends(get_db),
) -> Response:
    """
    Export calendar for a rotation as ICS file.

    Downloads an ICS file containing all assignments for the specified rotation
    within the date range. Useful for rotation coordinators to see who is assigned.

    Args:
        rotation_id: Rotation template UUID
        start_date: Start date for export (YYYY-MM-DD)
        end_date: End date for export (YYYY-MM-DD)
        db: Database session

    Returns:
        ICS file download
    """
    try:
        ics_content = CalendarService.generate_ics_for_rotation(
            db=db,
            rotation_id=rotation_id,
            start_date=start_date,
            end_date=end_date,
        )

        # Return ICS file as download
        return Response(
            content=ics_content,
            media_type="text/calendar",
            headers={
                "Content-Disposition": f'attachment; filename="rotation_{rotation_id}_{start_date}_{end_date}.ics"'
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate calendar: {str(e)}")


@router.post("/subscribe", response_model=CalendarSubscriptionResponse)
def create_subscription(
    request: CalendarSubscriptionCreate,
    db: Session = Depends(get_db),
) -> CalendarSubscriptionResponse:
    """
    Create a subscription URL for calendar feeds.

    Generates a unique token that can be used to subscribe to a person's calendar
    in calendar applications. The subscription URL will automatically update when
    the schedule changes.

    Args:
        request: Subscription creation request
        db: Database session

    Returns:
        Subscription details including URL
    """
    try:
        token, expires_at = CalendarService.create_subscription_token(
            db=db,
            person_id=request.person_id,
            expires_days=request.expires_days,
        )

        # Generate subscription URL
        # In production, this would use the actual server URL from config
        base_url = "http://localhost:8000/api/calendar"
        subscription_url = f"{base_url}/feed/{token}"

        return CalendarSubscriptionResponse(
            token=token,
            subscription_url=subscription_url,
            person_id=request.person_id,
            created_at=None,  # Would come from database
            expires_at=expires_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create subscription: {str(e)}")


@router.get("/feed/{token}")
def get_subscription_feed(
    token: str,
    db: Session = Depends(get_db),
) -> Response:
    """
    Get calendar feed for subscription.

    Returns an ICS file for the subscribed calendar. This endpoint is called
    automatically by calendar applications to fetch updates.

    Args:
        token: Subscription token
        db: Database session

    Returns:
        ICS file content
    """
    try:
        # Validate token and get person_id
        person_id = CalendarService.validate_subscription_token(db, token)
        if not person_id:
            raise HTTPException(status_code=401, detail="Invalid or expired subscription token")

        # Generate calendar for the next 6 months
        from datetime import datetime, timedelta

        start_date = date.today()
        end_date = (datetime.now() + timedelta(days=180)).date()

        ics_content = CalendarService.generate_ics_for_person(
            db=db,
            person_id=person_id,
            start_date=start_date,
            end_date=end_date,
        )

        # Return ICS file
        return Response(
            content=ics_content,
            media_type="text/calendar",
            headers={
                "Content-Type": "text/calendar; charset=utf-8",
                "Cache-Control": "no-cache, no-store, must-revalidate",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate feed: {str(e)}")
