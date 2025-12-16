"""Authentication API routes.

Thin routing layer that connects URL paths to controllers.
All business logic is in the service layer.
"""

from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserResponse, UserLogin
from app.core.security import get_current_user, get_current_active_user, get_admin_user
from app.controllers.auth_controller import AuthController

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_db),
):
    """
    Authenticate user and return JWT token.

    Accepts OAuth2 password flow (username + password).
    """
    controller = AuthController(db)
    return controller.login(form_data.username, form_data.password)


@router.post("/login/json", response_model=Token)
async def login_json(
    credentials: UserLogin,
    db=Depends(get_db),
):
    """
    Authenticate user with JSON body and return JWT token.

    Alternative to OAuth2 form-based login.
    """
    controller = AuthController(db)
    return controller.login(credentials.username, credentials.password)


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
):
    """
    Logout current user.

    Note: JWT tokens are stateless, so this is primarily for client-side
    token removal. In a production system, you might want to implement
    a token blacklist.
    """
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
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Register a new user.

    - If no users exist, first user becomes admin
    - Otherwise, requires admin to create new users
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
