"""Notification API routes.

Provides endpoints for users to view and manage their notifications:
- List notifications (paginated)
- Get a single notification
- Mark as read
- Mark all as read
"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationMarkReadResponse,
    NotificationResponse,
)

router = APIRouter()


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NotificationListResponse:
    """List the current user's notifications with pagination."""
    if not current_user.person_id:
        return NotificationListResponse(
            items=[], total=0, page=page, page_size=page_size, pages=0
        )

    query = select(Notification).where(
        Notification.recipient_id == current_user.person_id
    )
    if unread_only:
        query = query.where(Notification.is_read == False)  # noqa: E712

    # Count
    count_q = select(func.count()).select_from(query.subquery())
    total = db.execute(count_q).scalar_one()

    # Fetch page
    query = (
        query.order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    notifications = db.execute(query).scalars().all()

    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NotificationResponse:
    """Get a single notification by ID."""
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.recipient_id == current_user.person_id,
        )
        .first()
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    return NotificationResponse.model_validate(notification)


@router.patch("/{notification_id}/read", response_model=NotificationMarkReadResponse)
async def mark_notification_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NotificationMarkReadResponse:
    """Mark a single notification as read."""
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.recipient_id == current_user.person_id,
        )
        .first()
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    notification.is_read = True
    notification.read_at = datetime.now(UTC)
    db.commit()

    return NotificationMarkReadResponse(
        success=True, message="Notification marked as read"
    )


@router.patch("/read-all", response_model=NotificationMarkReadResponse)
async def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NotificationMarkReadResponse:
    """Mark all of the current user's notifications as read."""
    if not current_user.person_id:
        return NotificationMarkReadResponse(
            success=True, message="No notifications to mark", count=0
        )

    now = datetime.now(UTC)
    result = db.execute(
        update(Notification)
        .where(
            Notification.recipient_id == current_user.person_id,
            Notification.is_read == False,  # noqa: E712
        )
        .values(is_read=True, read_at=now)
    )
    db.commit()

    count = result.rowcount  # type: ignore[union-attr]
    return NotificationMarkReadResponse(
        success=True,
        message=f"Marked {count} notification(s) as read",
        count=count,
    )
