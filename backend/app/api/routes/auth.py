"""Authentication API routes.

Thin routing layer that connects URL paths to controllers.
All business logic is in the service layer.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt

from app.controllers.auth_controller import AuthController
from app.core.config import get_settings
from app.core.rate_limit import create_rate_limit_dependency
from app.core.security import (
    ALGORITHM,
    blacklist_token,
    create_access_token,
    create_refresh_token,
    get_admin_user,
    get_current_active_user,
    get_current_user,
    get_user_by_id,
    oauth2_scheme,
    verify_refresh_token,
)
from app.db.session import get_async_db, get_db
from app.models.user import User
from app.schemas.auth import (
    RefreshTokenRequest,
    TokenWithRefresh,
    UserCreate,
    UserLogin,
    UserResponse,
)

settings = get_settings()
router = APIRouter()

# Rate limiting dependencies
rate_limit_login = create_rate_limit_dependency(
    max_requests=settings.RATE_LIMIT_LOGIN_ATTEMPTS,
    window_seconds=settings.RATE_LIMIT_LOGIN_WINDOW,
    key_prefix="login",
)

rate_limit_register = create_rate_limit_dependency(
    max_requests=settings.RATE_LIMIT_REGISTER_ATTEMPTS,
    window_seconds=settings.RATE_LIMIT_REGISTER_WINDOW,
    key_prefix="register",
)


@router.post("/login", response_model=TokenWithRefresh)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_db),
    _rate_limit: None = Depends(rate_limit_login),
):
    """
    Authenticate user and return JWT access and refresh tokens.

    Accepts OAuth2 password flow (username + password).
    Rate limited to prevent brute force attacks.

    Security: Access token is set as httpOnly cookie to prevent XSS attacks.
    Refresh token is returned in the response body for secure storage.
    """
    controller = AuthController(db)
    token_response = controller.login(form_data.username, form_data.password)

    # Set access token as httpOnly cookie for XSS protection
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token_response.access_token}",
        httponly=True,
        secure=not settings.DEBUG,  # Secure in production
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    # Decode access token to get user info for refresh token
    payload = jwt.decode(
        token_response.access_token, settings.SECRET_KEY, algorithms=[ALGORITHM]
    )
    user_id = payload.get("sub")
    username = payload.get("username")

    # Generate refresh token with user data
    refresh_token, _, _ = create_refresh_token(
        data={"sub": user_id, "username": username}
    )

    return TokenWithRefresh(
        access_token=token_response.access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/login/json", response_model=TokenWithRefresh)
async def login_json(
    response: Response,
    credentials: UserLogin,
    db=Depends(get_db),
    _rate_limit: None = Depends(rate_limit_login),
):
    """
    Authenticate user with JSON body and return JWT access and refresh tokens.

    Alternative to OAuth2 form-based login.
    Rate limited to prevent brute force attacks.

    Security: Access token is set as httpOnly cookie to prevent XSS attacks.
    Refresh token is returned in the response body for secure storage.
    """
    controller = AuthController(db)
    token_response = controller.login(credentials.username, credentials.password)

    # Set access token as httpOnly cookie for XSS protection
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token_response.access_token}",
        httponly=True,
        secure=not settings.DEBUG,  # Secure in production
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    # Decode access token to get user info for refresh token
    payload = jwt.decode(
        token_response.access_token, settings.SECRET_KEY, algorithms=[ALGORITHM]
    )
    user_id = payload.get("sub")
    username = payload.get("username")

    # Generate refresh token with user data
    refresh_token, _, _ = create_refresh_token(
        data={"sub": user_id, "username": username}
    )

    return TokenWithRefresh(
        access_token=token_response.access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_active_user),
    token: str = Depends(oauth2_scheme),
    db=Depends(get_db),
):
    """
    Logout current user by blacklisting their token.

    The token will be added to the blacklist and rejected on future requests.
    Security: Deletes the httpOnly cookie containing the JWT token.
    """
    if token:
        try:
            # Decode token to get jti and expiration
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            jti = payload.get("jti")
            exp = payload.get("exp")

            if jti and exp:
                # Convert exp to datetime
                expires_at = datetime.utcfromtimestamp(exp)

                # Add to blacklist
                blacklist_token(
                    db=db,
                    jti=jti,
                    expires_at=expires_at,
                    user_id=current_user.id,
                    reason="logout",
                )

        except JWTError:
            pass  # Token was invalid anyway, no need to blacklist

    # Delete the httpOnly cookie
    response.delete_cookie(key="access_token", path="/")

    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=TokenWithRefresh)
async def refresh_token(
    response: Response,
    request: RefreshTokenRequest,
    db=Depends(get_db),
):
    """
    Exchange a refresh token for a new access token.

    Security:
    - When REFRESH_TOKEN_ROTATE is enabled, a new refresh token is issued
      and the old refresh token is IMMEDIATELY BLACKLISTED to prevent reuse.
    - This addresses the token theft window: if an attacker steals a refresh
      token, they cannot continue using it after the legitimate user refreshes.
    - The blacklist check happens before issuing new tokens, so a reused
      token will be rejected.

    Returns:
        TokenWithRefresh: New access token and optionally new refresh token
    """
    from uuid import UUID

    # Verify refresh token and optionally blacklist it if rotation is enabled
    # CRITICAL: blacklist_on_use=True ensures the old token cannot be reused
    token_data, old_jti, old_expires = verify_refresh_token(
        token=request.refresh_token,
        db=db,
        blacklist_on_use=settings.REFRESH_TOKEN_ROTATE,  # Blacklist when rotating
    )

    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user still exists and is active
    user = get_user_by_id(db, UUID(token_data.user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token, _, _ = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires,
    )

    # Set new access token as httpOnly cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_access_token}",
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    # Create new refresh token if rotation is enabled
    # The old token was already blacklisted in verify_refresh_token
    if settings.REFRESH_TOKEN_ROTATE:
        new_refresh_token, _, _ = create_refresh_token(
            data={"sub": str(user.id), "username": user.username}
        )
    else:
        # Return the same refresh token if rotation is disabled
        new_refresh_token = request.refresh_token

    return TokenWithRefresh(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    """Get current authenticated user information.

    Args:
        current_user: Authenticated user from JWT token.

    Returns:
        UserResponse with user details (id, username, email, role, etc.).

    Security:
        Requires valid JWT token in Authorization header or httpOnly cookie.
    """
    return current_user


@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(
    user_in: UserCreate,
    db=Depends(get_db),
    current_user: User | None = Depends(get_current_user),
    _rate_limit: None = Depends(rate_limit_register),
):
    """Register a new user account.

    Args:
        user_in: User creation payload (username, email, password, role).
        db: Database session.
        current_user: Current user (if authenticated). Admin required unless first user.
        _rate_limit: Rate limit enforcement dependency.

    Returns:
        UserResponse with created user details.

    Raises:
        HTTPException: If admin access required or username/email already exists.

    Security:
        - First user automatically becomes admin
        - Subsequent registrations require admin privileges
        - Rate limited to prevent automated account creation attacks

    Status Codes:
        - 201: User created successfully
        - 403: Admin access required
        - 409: Username or email already exists
    """
    controller = AuthController(db)
    return controller.register_user(user_in, current_user)


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db=Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """List all users in the system.

    Args:
        db: Database session.
        current_user: Current user (must be admin).

    Returns:
        List of UserResponse objects with all user details.

    Security:
        Requires admin role.

    Raises:
        HTTPException: If user is not an admin (403 Forbidden).
    """
    controller = AuthController(db)
    return controller.list_users()


@router.post("/initialize-admin")
async def initialize_admin(
    db=Depends(get_async_db),
):
    """
    Initialize database with default admin user if empty.

    Creates a default admin user with credentials:
    - username: admin
    - password: admin123

    This endpoint is idempotent - it only creates the user if the database
    is completely empty (no users exist).

    Security: This endpoint should only be called during initial setup.
    It automatically becomes a no-op after the first user is created.

    Returns:
        - 201: Admin user created
        - 200: Database already initialized (user already exists)
        - 500: Error during initialization

    Use Cases:
        - Docker initialization scripts
        - CI/CD setup pipelines
        - Development environment setup
        - RAG authentication bootstrap
    """
    from sqlalchemy import select

    try:
        # Check if any users exist
        user_count = await db.execute(select(User))
        existing_users = user_count.scalars().all()

        if len(existing_users) > 0:
            # Database already initialized
            return {
                "status": "already_initialized",
                "message": "Database already contains users",
                "user_count": len(existing_users),
            }

        # Create default admin user
        from app.core.security import get_password_hash

        admin_user = User(
            username="admin",
            email="admin@local.dev",
            hashed_password=get_password_hash("admin123"),
            role="admin",
            is_active=True,
        )

        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)

        return {
            "status": "created",
            "message": "Default admin user created successfully",
            "username": "admin",
            "note": "IMPORTANT: Change the default password in production!",
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize admin user: {str(e)}",
        )
