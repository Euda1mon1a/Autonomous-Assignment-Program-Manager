"""
API routes for audience-scoped token management.

These endpoints allow users to request elevated permission tokens for
specific operations. Tokens are short-lived and audience-scoped to
minimize security risk.

Security Flow:
1. User authenticates with normal access token
2. User requests audience token for specific operation
3. System validates user role has permission for the audience
4. Frontend receives short-lived token
5. Frontend makes operation request with audience token
6. Backend validates audience token matches operation
7. Operation executes with full audit trail

Role-Based Access Control:
- admin (level 4): All audiences including admin.impersonate, database.*
- coordinator (level 3): schedule.delete, resilience.override, audit.export, jobs.kill, solver.abort
- faculty (level 2): swap.execute, swap.rollback
- clinical_staff/rn/lpn/msa (level 1): Basic operations
- resident (level 0): Most restricted access
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
from app.models.token_blacklist import TokenBlacklist
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

# =============================================================================
# Role Hierarchy and Audience Permission Mapping
# =============================================================================
# Role levels (lowest to highest privilege)
ROLE_LEVELS: dict[str, int] = {
    "resident": 0,
    "clinical_staff": 1,
    "rn": 1,
    "lpn": 1,
    "msa": 1,
    "faculty": 2,
    "coordinator": 3,
    "admin": 4,
}

# Minimum role level required for each audience
# Audiences not listed here are available to all authenticated users (level 0)
AUDIENCE_REQUIREMENTS: dict[str, int] = {
    # Admin-only audiences (level 4)
    "admin.impersonate": 4,
    "database.backup": 4,
    "database.restore": 4,
    # Coordinator-level audiences (level 3)
    "schedule.delete": 3,
    "resilience.override": 3,
    "audit.export": 3,
    "jobs.kill": 3,
    "solver.abort": 3,
    # Faculty-level audiences (level 2)
    "swap.execute": 2,
    "swap.rollback": 2,
}


def get_user_role_level(role: str) -> int:
    """
    Get the numeric privilege level for a user role.

    Args:
        role: User role string (e.g., 'admin', 'faculty', 'resident')

    Returns:
        Integer privilege level (0-4), defaults to 0 for unknown roles
    """
    return ROLE_LEVELS.get(role.lower(), 0)


def check_audience_permission(user_role: str, audience: str) -> tuple[bool, str | None]:
    """
    Check if a user's role has permission to request a specific audience token.

    This implements role-based access control (RBAC) for audience tokens,
    preventing privilege escalation attacks where lower-privileged users
    attempt to obtain tokens for high-privilege operations.

    Args:
        user_role: The user's role (e.g., 'admin', 'faculty', 'resident')
        audience: The requested audience scope (e.g., 'admin.impersonate')

    Returns:
        Tuple of (is_permitted: bool, error_message: Optional[str])
        - (True, None) if permitted
        - (False, "reason") if denied

    Security Notes:
        - Unknown roles default to lowest privilege level (0)
        - Audiences not in AUDIENCE_REQUIREMENTS are available to all users
        - This is a critical security control - changes require security review
    """
    user_level = get_user_role_level(user_role)
    required_level = AUDIENCE_REQUIREMENTS.get(audience, 0)

    if user_level >= required_level:
        return True, None

    # Construct informative error message (without revealing exact levels)
    required_role = "admin"
    if required_level == 3:
        required_role = "coordinator or higher"
    elif required_level == 2:
        required_role = "faculty or higher"
    elif required_level == 1:
        required_role = "clinical staff or higher"

    return False, f"Audience '{audience}' requires {required_role} role"


def get_token_owner_id(db: Session, jti: str) -> str | None:
    """
    Look up the owner (user_id) of a token by its JTI.

    This queries the TokenBlacklist to find if this token was previously
    recorded (e.g., during creation or a prior revocation attempt).

    Args:
        db: Database session
        jti: JWT ID to look up

    Returns:
        User ID string if found, None otherwise

    Note:
        If the token was never recorded in the blacklist, we cannot
        determine ownership from the database. In that case, we must
        decode the token to get the user_id from the 'sub' claim.
    """
    record = (
        await db.execute(select(TokenBlacklist).where(TokenBlacklist.jti == jti))
    ).scalar_one_or_none()
    if record and record.user_id:
        return str(record.user_id)
    return None


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

    **Role Requirements**:
    - admin.impersonate, database.backup, database.restore: admin only
    - schedule.delete, resilience.override, audit.export, jobs.kill, solver.abort: coordinator+
    - swap.execute, swap.rollback: faculty+
    - Other audiences: any authenticated user
    """
    # Security: Verify user role has permission for this audience
    is_permitted, error_msg = check_audience_permission(
        user_role=current_user.role,
        audience=request.audience,
    )

    if not is_permitted:
        logger.warning(
            f"Audience token denied: user={current_user.username}, "
            f"role={current_user.role}, audience={request.audience}, "
            f"reason={error_msg}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_msg,
        )

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
    db: AsyncSession = Depends(get_async_db),
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

    **Ownership Verification**:
    Token ownership is verified in the following order:
    1. If `token` is provided in request, decode it to get user_id
    2. Check if token is already in blacklist (has recorded user_id)
    3. Admins can revoke any token regardless of ownership
    """
    try:
        # Security: Verify token belongs to current user (or user is admin)
        token_owner_id: str | None = None
        expires_at = datetime.utcnow()  # Default expiration for cleanup

        # Method 1: If token is provided, decode it to get owner and expiration
        if request.token:
            try:
                # Decode token without verification (may be expired, that's OK)
                # We just need to extract the user_id and expiration
                payload = jwt.decode(
                    request.token,
                    settings.SECRET_KEY,
                    algorithms=[ALGORITHM],
                    options={"verify_exp": False},  # Allow expired tokens
                )

                # Verify the JTI matches
                token_jti = payload.get("jti")
                if token_jti != request.jti:
                    logger.warning(
                        f"Token JTI mismatch: provided_jti={request.jti}, "
                        f"token_jti={token_jti}, user={current_user.username}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Token JTI does not match provided JTI",
                    )

                token_owner_id = payload.get("sub")

                # Get actual expiration from token if available
                exp = payload.get("exp")
                if exp:
                    expires_at = datetime.utcfromtimestamp(exp)

            except JWTError as e:
                logger.warning(
                    f"Failed to decode token for revocation: error={e}, "
                    f"jti={request.jti}, user={current_user.username}"
                )
                # Continue without token owner info - will check blacklist next

        # Method 2: Check if token is already in blacklist (has user_id recorded)
        if not token_owner_id:
            token_owner_id = get_token_owner_id(db, request.jti)

        # Verify ownership: user must own the token OR be an admin
        if token_owner_id and token_owner_id != str(current_user.id):
            # Token belongs to someone else - check if current user is admin
            if not current_user.is_admin:
                logger.warning(
                    f"Unauthorized token revocation attempt: "
                    f"user={current_user.username}, user_id={current_user.id}, "
                    f"token_owner_id={token_owner_id}, jti={request.jti}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot revoke tokens belonging to other users",
                )
            else:
                # Admin revoking another user's token - log this elevated action
                logger.info(
                    f"Admin revoking another user's token: "
                    f"admin={current_user.username}, token_owner_id={token_owner_id}, "
                    f"jti={request.jti}, reason={request.reason}"
                )

        # If we couldn't determine ownership and user is not admin, require token
        if not token_owner_id and not current_user.is_admin:
            # We can't verify ownership - for security, require the token to be provided
            # This prevents users from revoking arbitrary JTIs by guessing
            if not request.token:
                logger.warning(
                    f"Token revocation without ownership proof: "
                    f"user={current_user.username}, jti={request.jti}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token must be provided for ownership verification, "
                    "or this JTI is not recognized",
                )

        # Revoke the token
        revoke_audience_token(
            db=db,
            jti=request.jti,
            expires_at=expires_at,
            user_id=str(current_user.id),  # Record who revoked it
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

    except HTTPException:
        # Re-raise HTTP exceptions (403, 400) as-is
        raise
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
    db: AsyncSession = Depends(get_async_db),
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
