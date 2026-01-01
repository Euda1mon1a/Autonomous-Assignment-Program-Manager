"""Admin user management API routes.

Provides endpoints for admin-only user management operations including:
- User CRUD operations
- Account locking/unlocking
- Invitation management
- Activity logging
- Bulk operations
"""

import math
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_admin_user, get_password_hash
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.admin_user import (
    AccountLockRequest,
    AccountLockResponse,
    ActivityAction,
    ActivityLogEntry,
    ActivityLogResponse,
    AdminUserCreate,
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserUpdate,
    BulkAction,
    BulkUserActionRequest,
    BulkUserActionResponse,
    ResendInviteResponse,
    UserRole,
    UserStatus,
)

router = APIRouter()


def _user_to_admin_response(user: User) -> AdminUserResponse:
    """Convert User model to AdminUserResponse schema."""
    return AdminUserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=getattr(user, "first_name", None),
        last_name=getattr(user, "last_name", None),
        role=user.role,
        is_active=user.is_active,
        is_locked=getattr(user, "is_locked", False),
        lock_reason=getattr(user, "lock_reason", None),
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login,
        invite_sent_at=getattr(user, "invite_sent_at", None),
        invite_accepted_at=getattr(user, "invite_accepted_at", None),
    )


def _log_activity(
    db: Session,
    action: ActivityAction,
    admin_user: User,
    target_user: User | None = None,
    details: dict | None = None,
    request: Request | None = None,
) -> None:
    """Log an admin activity to the database.

    Note: This is a placeholder implementation. In production, this would
    write to an activity_log table. For now, we just pass through.
    """
    # TODO: Implement activity logging to activity_log table when it exists
    # For now, this is a no-op placeholder
    pass


@router.get("", response_model=AdminUserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        20, ge=1, le=100, alias="pageSize", description="Items per page"
    ),
    role: UserRole | None = Query(None, description="Filter by role"),
    status: UserStatus | None = Query(None, description="Filter by status"),
    search: str | None = Query(
        None, max_length=100, description="Search by name or email"
    ),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user),
):
    """
    List all users with filtering and pagination.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        role: Filter by user role
        status: Filter by account status (active/inactive/locked/pending)
        search: Search term for username or email

    Returns:
        Paginated list of users
    """
    # Build base query
    query = db.query(User)

    # Apply role filter
    if role:
        query = query.filter(User.role == role.value)

    # Apply status filter
    if status:
        if status == UserStatus.ACTIVE:
            query = query.filter(User.is_active == True)
            if hasattr(User, "is_locked"):
                query = query.filter(User.is_locked == False)
        elif status == UserStatus.INACTIVE:
            query = query.filter(User.is_active == False)
        elif status == UserStatus.LOCKED:
            if hasattr(User, "is_locked"):
                query = query.filter(User.is_locked == True)
        elif status == UserStatus.PENDING:
            # Pending users have invite_sent but not accepted
            if hasattr(User, "invite_sent_at") and hasattr(User, "invite_accepted_at"):
                query = query.filter(User.invite_sent_at.isnot(None))
                query = query.filter(User.invite_accepted_at.is_(None))

    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.username.ilike(search_term),
                User.email.ilike(search_term),
            )
        )

    # Count total
    total = query.count()

    # Calculate pagination
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size

    # Apply pagination and ordering
    users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()

    return AdminUserListResponse(
        items=[_user_to_admin_response(user) for user in users],
        total=total,
        page=page,
        pageSize=page_size,
        totalPages=total_pages,
    )


@router.post("", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: AdminUserCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Create a new user.

    Args:
        user_data: User creation data including email, name, role, and invite preference

    Returns:
        Created user data
    """
    # Check if email already exists
    existing = (
        await db.execute(select(User).where(User.email == user_data.email))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    # Generate username from email if not provided
    username = user_data.username
    if not username:
        username = user_data.email.split("@")[0]

    # Check if username already exists
    existing_username = (
        await db.execute(select(User).where(User.username == username))
    ).scalar_one_or_none()
    if existing_username:
        # Append a random suffix
        username = f"{username}_{uuid.uuid4().hex[:6]}"

    # Create user with temporary password (they'll reset via invite)
    temp_password = uuid.uuid4().hex
    new_user = User(
        id=uuid.uuid4(),
        username=username,
        email=user_data.email,
        hashed_password=get_password_hash(temp_password),
        role=user_data.role.value,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Set optional fields if they exist on the model
    if hasattr(new_user, "first_name"):
        new_user.first_name = user_data.first_name
    if hasattr(new_user, "last_name"):
        new_user.last_name = user_data.last_name
    if hasattr(new_user, "invite_sent_at") and user_data.send_invite:
        new_user.invite_sent_at = datetime.utcnow()

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Log activity
    _log_activity(
        db=db,
        action=ActivityAction.USER_CREATED,
        admin_user=current_user,
        target_user=new_user,
        details={"send_invite": user_data.send_invite},
        request=request,
    )

    # TODO: Send invitation email if user_data.send_invite is True

    return _user_to_admin_response(new_user)


@router.put("/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_data: AdminUserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Update an existing user.

    Args:
        user_id: UUID of the user to update
        user_data: Fields to update

    Returns:
        Updated user data
    """
    # Fetch user
    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent admin from deactivating themselves
    if user.id == current_user.id and user_data.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    # Prevent changing own role
    if (
        user.id == current_user.id
        and user_data.role
        and user_data.role.value != user.role
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role",
        )

    # Track changes for activity log
    changes = {}

    # Update fields
    if user_data.email is not None and user_data.email != user.email:
        # Check email uniqueness
        existing = (
            db.query(User)
            .filter(User.email == user_data.email, User.id != user_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already in use",
            )
        changes["email"] = {"old": user.email, "new": user_data.email}
        user.email = user_data.email

    if user_data.role is not None and user_data.role.value != user.role:
        changes["role"] = {"old": user.role, "new": user_data.role.value}
        user.role = user_data.role.value

    if user_data.is_active is not None and user_data.is_active != user.is_active:
        changes["is_active"] = {"old": user.is_active, "new": user_data.is_active}
        user.is_active = user_data.is_active

    if hasattr(user, "first_name") and user_data.first_name is not None:
        old_value = getattr(user, "first_name", None)
        if user_data.first_name != old_value:
            changes["first_name"] = {"old": old_value, "new": user_data.first_name}
            user.first_name = user_data.first_name

    if hasattr(user, "last_name") and user_data.last_name is not None:
        old_value = getattr(user, "last_name", None)
        if user_data.last_name != old_value:
            changes["last_name"] = {"old": old_value, "new": user_data.last_name}
            user.last_name = user_data.last_name

    user.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(user)

    # Log activity
    if changes:
        _log_activity(
            db=db,
            action=ActivityAction.USER_UPDATED,
            admin_user=current_user,
            target_user=user,
            details={"changes": changes},
            request=request,
        )

    return _user_to_admin_response(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Delete a user.

    Args:
        user_id: UUID of the user to delete

    Returns:
        No content (204 status)
    """
    # Fetch user
    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    # Log activity before deletion
    _log_activity(
        db=db,
        action=ActivityAction.USER_DELETED,
        admin_user=current_user,
        target_user=user,
        details={"deleted_email": user.email, "deleted_username": user.username},
        request=request,
    )

    await db.delete(user)
    await db.commit()


@router.post("/{user_id}/lock", response_model=AccountLockResponse)
async def lock_user_account(
    user_id: uuid.UUID,
    lock_data: AccountLockRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Lock or unlock a user account.

    Args:
        user_id: UUID of the user to lock/unlock
        lock_data: Lock request with locked status and optional reason

    Returns:
        Updated lock status
    """
    # Fetch user
    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent admin from locking themselves
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot lock your own account",
        )

    # Check if model supports locking
    if not hasattr(user, "is_locked"):
        # Fall back to using is_active for locking
        if lock_data.locked:
            user.is_active = False
            action = ActivityAction.USER_LOCKED
            message = "Account deactivated (model does not support explicit locking)"
        else:
            user.is_active = True
            action = ActivityAction.USER_UNLOCKED
            message = "Account activated"

        user.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)

        _log_activity(
            db=db,
            action=action,
            admin_user=current_user,
            target_user=user,
            details={"reason": lock_data.reason} if lock_data.reason else None,
            request=request,
        )

        return AccountLockResponse(
            userId=user.id,
            isLocked=not user.is_active,
            lockReason=lock_data.reason,
            lockedAt=datetime.utcnow() if lock_data.locked else None,
            lockedBy=current_user.email if lock_data.locked else None,
            message=message,
        )

    # Model supports explicit locking
    user.is_locked = lock_data.locked
    if hasattr(user, "lock_reason"):
        user.lock_reason = lock_data.reason if lock_data.locked else None
    if hasattr(user, "locked_at"):
        user.locked_at = datetime.utcnow() if lock_data.locked else None
    if hasattr(user, "locked_by"):
        user.locked_by = str(current_user.id) if lock_data.locked else None

    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)

    action = (
        ActivityAction.USER_LOCKED if lock_data.locked else ActivityAction.USER_UNLOCKED
    )
    _log_activity(
        db=db,
        action=action,
        admin_user=current_user,
        target_user=user,
        details={"reason": lock_data.reason} if lock_data.reason else None,
        request=request,
    )

    return AccountLockResponse(
        userId=user.id,
        isLocked=user.is_locked,
        lockReason=getattr(user, "lock_reason", None),
        lockedAt=getattr(user, "locked_at", None),
        lockedBy=current_user.email if lock_data.locked else None,
        message="Account locked successfully"
        if lock_data.locked
        else "Account unlocked successfully",
    )


@router.post("/{user_id}/resend-invite", response_model=ResendInviteResponse)
async def resend_invite(
    user_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Resend invitation email to a user.

    Args:
        user_id: UUID of the user to resend invite to

    Returns:
        Confirmation of invite sent
    """
    # Fetch user
    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if user already accepted invite
    if hasattr(user, "invite_accepted_at") and user.invite_accepted_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has already accepted their invitation",
        )

    # Update invite sent timestamp
    if hasattr(user, "invite_sent_at"):
        user.invite_sent_at = datetime.utcnow()

    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)

    # Log activity
    _log_activity(
        db=db,
        action=ActivityAction.INVITE_RESENT,
        admin_user=current_user,
        target_user=user,
        request=request,
    )

    # TODO: Actually send the invitation email

    return ResendInviteResponse(
        userId=user.id,
        email=user.email,
        sentAt=datetime.utcnow(),
        message="Invitation resent successfully",
    )


@router.get("/activity-log", response_model=ActivityLogResponse)
async def get_activity_log(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        20, ge=1, le=100, alias="pageSize", description="Items per page"
    ),
    user_id: uuid.UUID | None = Query(
        None, alias="userId", description="Filter by user ID"
    ),
    action: ActivityAction | None = Query(None, description="Filter by action type"),
    date_from: datetime | None = Query(
        None, alias="dateFrom", description="Start date"
    ),
    date_to: datetime | None = Query(None, alias="dateTo", description="End date"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Get paginated activity log.

    Note: This is a placeholder implementation. In production, this would
    query an activity_log table. For now, returns an empty response.

    Args:
        page: Page number
        page_size: Items per page
        user_id: Filter by user who performed action
        action: Filter by action type
        date_from: Filter by start date
        date_to: Filter by end date

    Returns:
        Paginated activity log entries
    """
    # TODO: Implement when activity_log table exists
    # For now, return empty response
    return ActivityLogResponse(
        items=[],
        total=0,
        page=page,
        pageSize=page_size,
        totalPages=0,
    )


@router.post("/bulk", response_model=BulkUserActionResponse)
async def bulk_user_action(
    bulk_data: BulkUserActionRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Perform bulk actions on multiple users.

    Args:
        bulk_data: List of user IDs and action to perform

    Returns:
        Summary of affected users
    """
    success_ids: list[uuid.UUID] = []
    failed_ids: list[uuid.UUID] = []
    errors: list[str] = []

    for uid in bulk_data.user_ids:
        # Prevent action on self
        if uid == current_user.id:
            failed_ids.append(uid)
            errors.append(f"Cannot perform action on your own account: {uid}")
            continue

        # Fetch user
        user = (
            await db.execute(select(User).where(User.id == uid))
        ).scalar_one_or_none()

        if not user:
            failed_ids.append(uid)
            errors.append(f"User not found: {uid}")
            continue

        try:
            if bulk_data.action == BulkAction.ACTIVATE:
                user.is_active = True
                if hasattr(user, "is_locked"):
                    user.is_locked = False
            elif bulk_data.action == BulkAction.DEACTIVATE:
                user.is_active = False
            elif bulk_data.action == BulkAction.DELETE:
                db.delete(user)

            if bulk_data.action != BulkAction.DELETE:
                user.updated_at = datetime.utcnow()
            success_ids.append(uid)

        except (ValueError, KeyError, AttributeError) as e:
            failed_ids.append(uid)
            errors.append(f"Failed to process user {uid}: {str(e)}")
            logger.error(f"Bulk action error for user {uid}: {e}", exc_info=True)

    await db.commit()

    # Determine activity action
    activity_action = {
        BulkAction.ACTIVATE: ActivityAction.USER_UPDATED,
        BulkAction.DEACTIVATE: ActivityAction.USER_UPDATED,
        BulkAction.DELETE: ActivityAction.USER_DELETED,
    }.get(bulk_data.action, ActivityAction.USER_UPDATED)

    _log_activity(
        db=db,
        action=activity_action,
        admin_user=current_user,
        details={
            "bulk_action": bulk_data.action.value,
            "success_count": len(success_ids),
            "failed_count": len(failed_ids),
        },
        request=request,
    )

    action_past_tense = {
        BulkAction.ACTIVATE: "activated",
        BulkAction.DEACTIVATE: "deactivated",
        BulkAction.DELETE: "deleted",
    }.get(bulk_data.action, "processed")

    return BulkUserActionResponse(
        action=bulk_data.action.value,
        affectedCount=len(success_ids),
        successIds=success_ids,
        failedIds=failed_ids,
        errors=errors,
        message=f"Successfully {action_past_tense} {len(success_ids)} user(s)",
    )
