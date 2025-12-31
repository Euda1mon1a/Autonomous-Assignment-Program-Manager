"""Calendar export API routes."""

import logging
from datetime import date, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.calendar import (
    CalendarSubscriptionCreate,
    CalendarSubscriptionListResponse,
    CalendarSubscriptionResponse,
)
from app.services.calendar_service import CalendarService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/export/ics")
async def export_all_calendars(
    start_date: date = Query(..., description="Start date for calendar export"),
    end_date: date = Query(..., description="End date for calendar export"),
    person_ids: list[UUID] | None = Query(None, description="Person UUIDs to filter"),
    rotation_ids: list[UUID] | None = Query(
        None, description="Rotation UUIDs to filter"
    ),
    include_types: list[str] | None = Query(
        None, description="Activity types to include"
    ),
    db: AsyncSession = Depends(get_async_db),
) -> Response:
    """
    Export complete schedule as ICS file.

    Downloads an ICS file containing all assignments within the date range.
    Can be filtered by persons, rotations, or activity types.
    Compatible with Google Calendar, Outlook, and Apple Calendar.

    Args:
        start_date: Start date for export (YYYY-MM-DD)
        end_date: End date for export (YYYY-MM-DD)
        person_ids: Optional list of person UUIDs to filter
        rotation_ids: Optional list of rotation UUIDs to filter
        include_types: Optional list of activity types to filter
        db: Database session

    Returns:
        ICS file download
    """
    try:
        ics_content = CalendarService.generate_ics_all(
            db=db,
            start_date=start_date,
            end_date=end_date,
            person_ids=person_ids,
            rotation_ids=rotation_ids,
            include_types=include_types,
        )

        # Return ICS file as download
        return Response(
            content=ics_content,
            media_type="text/calendar",
            headers={
                "Content-Disposition": f'attachment; filename="complete_schedule_{start_date}_{end_date}.ics"'
            },
        )
    except Exception as e:
        logger.error(f"Error generating calendar export: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An error occurred generating the calendar"
        )


@router.get("/export/ics/{person_id}")
async def export_person_ics(
    person_id: UUID,
    start_date: date = Query(..., description="Start date for calendar export"),
    end_date: date = Query(..., description="End date for calendar export"),
    include_types: list[str] | None = Query(
        None, description="Activity types to include"
    ),
    db: AsyncSession = Depends(get_async_db),
) -> Response:
    """
    Export individual's schedule as ICS file.

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
        logger.error(f"Invalid request for calendar export: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail="Resource not found")
    except Exception as e:
        logger.error(f"Error generating calendar export: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An error occurred generating the calendar"
        )


@router.get("/export/person/{person_id}")
async def export_person_calendar(
    person_id: UUID,
    start_date: date = Query(..., description="Start date for calendar export"),
    end_date: date = Query(..., description="End date for calendar export"),
    include_types: list[str] | None = Query(
        None, description="Activity types to include"
    ),
    db: AsyncSession = Depends(get_async_db),
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
        logger.error(f"Invalid request for calendar export: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail="Resource not found")
    except Exception as e:
        logger.error(f"Error generating calendar export: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An error occurred generating the calendar"
        )


@router.get("/export/rotation/{rotation_id}")
async def export_rotation_calendar(
    rotation_id: UUID,
    start_date: date = Query(..., description="Start date for calendar export"),
    end_date: date = Query(..., description="End date for calendar export"),
    db: AsyncSession = Depends(get_async_db),
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
        logger.error(f"Invalid request for calendar export: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail="Resource not found")
    except Exception as e:
        logger.error(f"Error generating calendar export: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An error occurred generating the calendar"
        )


# =============================================================================
# Webcal Subscription Endpoints
# =============================================================================


def _get_base_url(request: Request) -> str:
    """Get the base URL for subscription URLs from the request."""
    # Use X-Forwarded-Proto and X-Forwarded-Host if behind a proxy
    proto = request.headers.get("X-Forwarded-Proto", request.url.scheme)
    host = request.headers.get("X-Forwarded-Host", request.url.netloc)
    return f"{proto}://{host}/api/calendar"


@router.post("/subscribe", response_model=CalendarSubscriptionResponse)
async def create_subscription(
    request_body: CalendarSubscriptionCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> CalendarSubscriptionResponse:
    """
    Create a webcal subscription URL for calendar feeds.

    Generates a secure token that allows subscribing to a calendar feed.
    The subscription URL automatically updates when the schedule changes.

    **How to use:**
    1. Copy the `webcal_url` from the response
    2. Paste it into your calendar app (Google Calendar, Outlook, Apple Calendar)
    3. Your calendar will automatically refresh with schedule updates

    Args:
        request_body: Subscription creation request with person_id and optional expiration
        request: HTTP request (for URL generation)
        db: Database session
        current_user: Authenticated user

    Returns:
        Subscription details including webcal:// URL for calendar apps
    """
    try:
        subscription = CalendarService.create_subscription(
            db=db,
            person_id=request_body.person_id,
            created_by_user_id=current_user.id,
            label=request_body.label,
            expires_days=request_body.expires_days,
        )

        base_url = _get_base_url(request)
        http_url = f"{base_url}/subscribe/{subscription.token}"
        webcal_url = CalendarService.generate_subscription_url(
            subscription.token, base_url
        )

        return CalendarSubscriptionResponse(
            token=subscription.token,
            subscription_url=http_url,
            webcal_url=webcal_url,
            person_id=subscription.person_id,
            label=subscription.label,
            created_at=subscription.created_at,
            expires_at=subscription.expires_at,
            last_accessed_at=subscription.last_accessed_at,
            is_active=subscription.is_active,
        )
    except ValueError as e:
        logger.error(f"Invalid request for calendar subscription: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail="Resource not found")
    except Exception as e:
        logger.error(f"Error creating calendar subscription: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An error occurred creating the subscription"
        )


@router.get("/subscribe/{token}")
async def get_subscription_feed(
    token: str,
    db: AsyncSession = Depends(get_async_db),
) -> Response:
    """
    Get calendar feed for a subscription (webcal endpoint).

    This is the endpoint that calendar applications call to fetch updates.
    **No authentication required** - the token serves as authentication.

    The feed includes:
    - All assignments from today through 6 months in the future
    - Proper VTIMEZONE for America/New_York
    - Event details including location, notes, and role

    **Cache behavior:**
    Calendar apps typically poll every 15-60 minutes. The response includes
    Cache-Control headers to suggest a 15-minute refresh interval.

    Args:
        token: Subscription token from the URL
        db: Database session

    Returns:
        ICS calendar file content
    """
    try:
        # Validate token and get person_id
        person_id = CalendarService.validate_subscription_token(db, token)
        if not person_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired subscription token. Please generate a new subscription.",
            )

        # Generate calendar: today through 6 months ahead
        start_date = date.today()
        end_date = (datetime.now() + timedelta(days=180)).date()

        ics_content = CalendarService.generate_ics_for_person(
            db=db,
            person_id=person_id,
            start_date=start_date,
            end_date=end_date,
        )

        # Return ICS with proper headers for calendar apps
        return Response(
            content=ics_content,
            media_type="text/calendar",
            headers={
                "Content-Type": "text/calendar; charset=utf-8",
                # Suggest 15-minute refresh, but allow caching
                "Cache-Control": "private, max-age=900",
                # Prevent transformation by proxies
                "X-Content-Type-Options": "nosniff",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating calendar feed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An error occurred generating the calendar feed"
        )


@router.get("/subscriptions", response_model=CalendarSubscriptionListResponse)
async def list_subscriptions(
    request: Request,
    person_id: UUID | None = Query(None, description="Filter by person"),
    active_only: bool = Query(True, description="Only show active subscriptions"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> CalendarSubscriptionListResponse:
    """
    List calendar subscriptions.

    Returns all subscriptions created by the current user, optionally filtered.

    Args:
        request: HTTP request
        person_id: Optional filter by person
        active_only: Only return active subscriptions (default True)
        db: Database session
        current_user: Authenticated user

    Returns:
        List of subscriptions with URLs
    """
    subscriptions = CalendarService.list_subscriptions(
        db=db,
        person_id=person_id,
        created_by_user_id=current_user.id,
        active_only=active_only,
    )

    base_url = _get_base_url(request)

    return CalendarSubscriptionListResponse(
        subscriptions=[
            CalendarSubscriptionResponse(
                token=sub.token,
                subscription_url=f"{base_url}/subscribe/{sub.token}",
                webcal_url=CalendarService.generate_subscription_url(
                    sub.token, base_url
                ),
                person_id=sub.person_id,
                label=sub.label,
                created_at=sub.created_at,
                expires_at=sub.expires_at,
                last_accessed_at=sub.last_accessed_at,
                is_active=sub.is_active,
            )
            for sub in subscriptions
        ],
        total=len(subscriptions),
    )


@router.delete("/subscribe/{token}")
async def revoke_subscription(
    token: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Revoke a calendar subscription.

    Permanently disables the subscription token. Calendar apps using this
    subscription will no longer receive updates.

    Args:
        token: Subscription token to revoke
        db: Database session
        current_user: Authenticated user

    Returns:
        Success message
    """
    # Verify the subscription exists and belongs to the user
    subscription = CalendarService.get_subscription(db, token)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if subscription.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to revoke this subscription"
        )

    success = CalendarService.revoke_subscription(db, token)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to revoke subscription")

    return {"success": True, "message": "Subscription revoked successfully"}


# Legacy endpoint for backward compatibility
@router.get("/feed/{token}")
async def get_subscription_feed_legacy(
    token: str,
    db: AsyncSession = Depends(get_async_db),
) -> Response:
    """Legacy endpoint - redirects to /subscribe/{token}."""
    return get_subscription_feed(token, db)
