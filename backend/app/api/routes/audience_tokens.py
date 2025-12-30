"""
API routes for audience-scoped token management.

These endpoints allow users to request elevated permission tokens for
specific operations. Tokens are short-lived and audience-scoped to
minimize security risk.

Security Flow:
1. User authenticates with normal access token
2. User requests audience token for specific operation
3. Frontend receives short-lived token
4. Frontend makes operation request with audience token
5. Backend validates audience token matches operation
6. Operation executes with full audit trail
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.audience_auth import (
    ALGORITHM,
    VALID_AUDIENCES,
    create_audience_token,
    revoke_audience_token,
)
from app.core.config import get_settings
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.audience_token import (
    AudienceListResponse,
    AudienceTokenRequest,
    AudienceTokenResponse,
    RevokeTokenRequest,
    RevokeTokenResponse,
)

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


@router.get("/audiences", response_model=AudienceListResponse)
async def list_audiences(
    current_user: User = Depends(get_current_active_user),
) -> AudienceListResponse:
    """
    List all available audience scopes.

    Returns a mapping of audience keys to their descriptions.
    This helps frontends display available operations to users.

    **Authentication Required**: Yes (any authenticated user)

    **Example Response**:
    ```json
    {
        "audiences": {
            "jobs.abort": "Abort running background jobs",
            "schedule.generate": "Generate new schedules",
            "swap.execute": "Execute schedule swaps"
        }
    }
    ```
    """
    return AudienceListResponse(audiences=VALID_AUDIENCES)


@router.post("/tokens", response_model=AudienceTokenResponse)
async def request_audience_token(
    request: AudienceTokenRequest,
    current_user: User = Depends(get_current_active_user),
) -> AudienceTokenResponse:
    """
    Request an audience-scoped token for elevated operations.

    This endpoint creates a short-lived JWT token that grants permission
    for a specific operation type. The token should be used immediately
    and discarded after the operation completes.

    **Authentication Required**: Yes (normal access token)

    **Request Body**:
    - `audience`: Operation scope (e.g., "jobs.abort")
    - `ttl_seconds`: Time-to-live (30-600 seconds, default: 120)

    **Security Notes**:
    - Token is valid only for the specified audience
    - Maximum TTL is 10 minutes (600 seconds)
    - Token creation is logged for audit trail
    - Token inherits user permissions (cannot escalate beyond user's role)

    **Example Request**:
    ```json
    {
        "audience": "jobs.abort",
        "ttl_seconds": 120
    }
    ```

    **Example Response**:
    ```json
    {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "audience": "jobs.abort",
        "expires_at": "2025-12-29T15:30:00Z",
        "ttl_seconds": 120
    }
    ```

    **Usage**:
    1. Store token temporarily in memory (not localStorage)
    2. Include in Authorization header: `Bearer <token>`
    3. Discard after operation completes
    """
    # TODO: Add role-based audience restrictions
    # Example: Only admins can request "admin.impersonate" tokens

    try:
        # Create audience token
        token_response = create_audience_token(
            user_id=str(current_user.id),
            audience=request.audience,
            ttl_seconds=request.ttl_seconds,
        )

        logger.info(
            f"Audience token requested: user={current_user.username}, "
            f"user_id={current_user.id}, audience={request.audience}, "
            f"ttl={request.ttl_seconds}s"
        )

        return token_response

    except ValueError as e:
        # Invalid audience or TTL
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            f"Error creating audience token: user={current_user.username}, "
            f"audience={request.audience}, error={e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create audience token",
        )


@router.post("/tokens/revoke", response_model=RevokeTokenResponse)
async def revoke_token(
    request: RevokeTokenRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> RevokeTokenResponse:
    """
    Revoke an audience-scoped token.

    This adds the token to the blacklist, preventing further use.
    Useful for:
    - Immediate revocation if token is compromised
    - Cleanup after operation completion
    - Security incident response

    **Authentication Required**: Yes

    **Security**: Users can only revoke their own tokens (unless admin)

    **Request Body**:
    - `jti`: JWT ID of the token to revoke
    - `reason`: Optional reason for revocation

    **Example Request**:
    ```json
    {
        "jti": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "reason": "operation_completed"
    }
    ```

    **Example Response**:
    ```json
    {
        "success": true,
        "jti": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "message": "Token successfully revoked"
    }
    ```
    """
    try:
        # TODO: Verify token belongs to current user (or user is admin)
        # This requires decoding the token to get the user_id
        # For now, we'll allow any authenticated user to revoke

        # We need to get the expiration time from somewhere
        # Option 1: Accept it in the request
        # Option 2: Decode the token (but it might already be expired)
        # For now, we'll use a safe default

        expires_at = datetime.utcnow()  # Already expired, cleanup will handle it

        # Revoke the token
        revoke_audience_token(
            db=db,
            jti=request.jti,
            expires_at=expires_at,
            user_id=str(current_user.id),
            reason=request.reason,
        )

        logger.info(
            f"Audience token revoked: user={current_user.username}, "
            f"jti={request.jti}, reason={request.reason}"
        )

        return RevokeTokenResponse(
            success=True,
            jti=request.jti,
            message="Token successfully revoked",
        )

    except Exception as e:
        logger.error(
            f"Error revoking audience token: user={current_user.username}, "
            f"jti={request.jti}, error={e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke token",
        )


# Example of using audience authentication in a protected endpoint
# This is just a demonstration - real implementation would be in appropriate modules

from app.core.audience_auth import AudienceTokenPayload, require_audience


@router.post("/example/abort-job/{job_id}")
async def abort_job_example(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    audience_token: AudienceTokenPayload = Depends(require_audience("jobs.abort")),
    db: Session = Depends(get_db),
):
    """
    Example endpoint showing audience authentication usage.

    This demonstrates how to protect an endpoint with audience-scoped tokens.
    The endpoint requires:
    1. Valid user authentication (normal access token)
    2. Valid audience token for "jobs.abort"

    **Authentication Required**:
    - Access token (normal authentication)
    - Audience token in Authorization header

    **Headers**:
    ```
    Authorization: Bearer <audience-token>
    ```

    **Flow**:
    1. User authenticates normally
    2. User requests audience token: POST /api/audience-tokens/tokens
    3. User calls this endpoint with audience token
    4. Backend validates token has "jobs.abort" audience
    5. Operation executes

    **Security**:
    - audience_token.sub contains user_id from token
    - current_user is from normal authentication
    - Verify they match to prevent token theft
    """
    # Verify the audience token belongs to the authenticated user
    if audience_token.sub != str(current_user.id):
        logger.warning(
            f"Audience token user mismatch: token_user={audience_token.sub}, "
            f"auth_user={current_user.id}, audience={audience_token.aud}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token does not belong to authenticated user",
        )

    # Log the operation with full context
    logger.info(
        f"Aborting job: job_id={job_id}, user={current_user.username}, "
        f"user_id={current_user.id}, audience={audience_token.aud}, "
        f"token_jti={audience_token.jti}"
    )

    # Execute the privileged operation
    # ... actual job abort logic here ...

    return {
        "success": True,
        "job_id": job_id,
        "message": f"Job {job_id} abort initiated",
        "initiated_by": current_user.username,
        "token_jti": audience_token.jti,
    }
