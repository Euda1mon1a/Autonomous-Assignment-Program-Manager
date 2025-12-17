"""Authentication API routes.

Thin routing layer that connects URL paths to controllers.
All business logic is in the service layer.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt

from app.controllers.auth_controller import AuthController
from app.core.config import get_settings
from app.core.rate_limit import create_rate_limit_dependency
from app.core.security import (
    ALGORITHM,
    blacklist_token,
    get_admin_user,
    get_current_active_user,
    get_current_user,
    oauth2_scheme,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserLogin, UserResponse

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


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_db),
    _rate_limit: None = Depends(rate_limit_login),
):
    """
    Authenticate user and return JWT token.

    Accepts OAuth2 password flow (username + password).
    Rate limited to prevent brute force attacks.

    Security: Token is set as httpOnly cookie to prevent XSS attacks.
    """
    controller = AuthController(db)
    token_response = controller.login(form_data.username, form_data.password)

    # Set token as httpOnly cookie for XSS protection
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token_response.access_token}",
        httponly=True,
        secure=not settings.DEBUG,  # Secure in production
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    return token_response


@router.post("/login/json", response_model=Token)
async def login_json(
    response: Response,
    credentials: UserLogin,
    db=Depends(get_db),
    _rate_limit: None = Depends(rate_limit_login),
):
    """
    Authenticate user with JSON body and return JWT token.

    Alternative to OAuth2 form-based login.
    Rate limited to prevent brute force attacks.

    Security: Token is set as httpOnly cookie to prevent XSS attacks.
    """
    controller = AuthController(db)
    token_response = controller.login(credentials.username, credentials.password)

    # Set token as httpOnly cookie for XSS protection
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token_response.access_token}",
        httponly=True,
        secure=not settings.DEBUG,  # Secure in production
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    return token_response


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
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[ALGORITHM]
            )
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
                    reason="logout"
                )

        except JWTError:
            pass  # Token was invalid anyway, no need to blacklist

    # Delete the httpOnly cookie
    response.delete_cookie(key="access_token", path="/")

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    """Get current authenticated user information."""
    return current_user


@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(
    user_in: UserCreate,
    db=Depends(get_db),
    current_user: User | None = Depends(get_current_user),
    _rate_limit: None = Depends(rate_limit_register),
):
    """
    Register a new user.

    - If no users exist, first user becomes admin
    - Otherwise, requires admin to create new users
    Rate limited to prevent automated account creation attacks.
    """
    controller = AuthController(db)
    return controller.register_user(user_in, current_user)


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db=Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """List all users (admin only)."""
    controller = AuthController(db)
    return controller.list_users()
