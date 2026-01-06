"""Impersonation API routes for Admin 'View As User' feature.

This module provides endpoints for user impersonation, allowing administrators
to temporarily assume the identity of other users for troubleshooting and
support purposes.

Security:
- POST /api/auth/impersonate - Requires admin role
- POST /api/auth/end-impersonation - Requires valid impersonation token
- GET /api/auth/impersonation-status - Requires valid impersonation token

All impersonation events are logged to the audit trail.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.security import get_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.impersonation import (
    EndImpersonationResponse,
    ImpersonateRequest,
    ImpersonateResponse,
    ImpersonationStatus,
)
from app.services.impersonation_service import (
    ImpersonationForbiddenError,
    ImpersonationService,
    ImpersonationTokenError,
)

router = APIRouter()


def _get_impersonation_token(request: Request) -> str | None:
    """Extract impersonation token from request.

    Checks for token in:
    1. X-Impersonation-Token header
    2. impersonation_token cookie

    Args:
        request: FastAPI request object.

    Returns:
        Impersonation token if found, None otherwise.
    """
    # Check header first
    token = request.headers.get("X-Impersonation-Token")
    if token:
        return token

    # Fall back to cookie
    cookie_token = request.cookies.get("impersonation_token")
    if cookie_token:
        return cookie_token

    return None


@router.post("/impersonate", response_model=ImpersonateResponse)
async def start_impersonation(
    request: Request,
    response: Response,
    impersonate_request: ImpersonateRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Start impersonating another user.

    Allows an administrator to temporarily assume the identity of another user
    for troubleshooting and support purposes. Creates a short-lived impersonation
    token that can be used to act as the target user.

    Args:
        request: FastAPI request object for audit logging.
        response: FastAPI response object for setting cookies.
        impersonate_request: Request containing target user ID.
        current_user: Current admin user (from auth).
        db: Database session.

    Returns:
        ImpersonateResponse with impersonation token and target user details.

    Raises:
        HTTPException: If impersonation is not allowed or target user not found.

    Security:
        - Requires admin role
        - Cannot self-impersonate
        - Cannot impersonate while already impersonating
        - All events logged to audit trail
    """
    # Check if already impersonating (nested impersonation not allowed)
    existing_token = _get_impersonation_token(request)
    if existing_token:
        service = ImpersonationService(db)
        status_result = service.get_impersonation_status(existing_token)
        if status_result.is_impersonating:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot start new impersonation while already impersonating. "
                "End current impersonation first.",
            )

    service = ImpersonationService(db)

    try:
        result = service.start_impersonation(
            admin_user=current_user,
            target_user_id=impersonate_request.target_user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )

        # Set impersonation token as cookie for convenience
        response.set_cookie(
            key="impersonation_token",
            value=result.impersonation_token,
            httponly=True,
            secure=True,  # Always secure for impersonation
            samesite="strict",
            max_age=30 * 60,  # 30 minutes
            path="/",
        )

        return result

    except ImpersonationForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/end-impersonation", response_model=EndImpersonationResponse)
async def end_impersonation(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """End the current impersonation session.

    Revokes the impersonation token and restores the admin's normal session.
    The token is added to the blacklist and cannot be reused.

    Args:
        request: FastAPI request object for token extraction.
        response: FastAPI response object for clearing cookies.
        db: Database session.

    Returns:
        EndImpersonationResponse confirming impersonation was ended.

    Raises:
        HTTPException: If no active impersonation or token is invalid.
    """
    token = _get_impersonation_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active impersonation session found",
        )

    service = ImpersonationService(db)

    try:
        service.end_impersonation(
            token=token,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )

        # Clear impersonation cookie
        response.delete_cookie(key="impersonation_token", path="/")

        return EndImpersonationResponse(
            success=True,
            message="Impersonation ended successfully",
        )

    except ImpersonationTokenError as e:
        # Clear cookie even if token was invalid
        response.delete_cookie(key="impersonation_token", path="/")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/impersonation-status", response_model=ImpersonationStatus)
async def get_impersonation_status(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get the current impersonation status.

    Returns information about the current impersonation session, including
    the target user, original admin, and expiration time.

    Args:
        request: FastAPI request object for token extraction.
        db: Database session.

    Returns:
        ImpersonationStatus with current session details.
    """
    token = _get_impersonation_token(request)
    if not token:
        return ImpersonationStatus(is_impersonating=False)

    service = ImpersonationService(db)
    return service.get_impersonation_status(token)
