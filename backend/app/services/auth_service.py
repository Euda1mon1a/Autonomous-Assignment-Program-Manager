"""Authentication service for business logic."""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.repositories.user import UserRepository
from app.models.user import User
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
)
from app.core.config import get_settings

settings = get_settings()


class AuthService:
    """Service for authentication business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def authenticate(self, username: str, password: str) -> dict:
        """
        Authenticate a user and generate access token.

        Returns dict with:
        - user: The authenticated user
        - access_token: JWT access token
        - token_type: Token type (bearer)
        - error: Error message if authentication failed
        """
        user = self.user_repo.get_by_username(username)
        if not user:
            return {"user": None, "error": "Incorrect username or password"}

        if not verify_password(password, user.hashed_password):
            return {"user": None, "error": "Incorrect username or password"}

        # Update last login
        user.last_login = datetime.utcnow()
        self.user_repo.commit()

        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username},
            expires_delta=access_token_expires,
        )

        return {
            "user": user,
            "access_token": access_token,
            "token_type": "bearer",
            "error": None,
        }

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        role: str = "coordinator",
        current_user: Optional[User] = None,
    ) -> dict:
        """
        Register a new user.

        First user becomes admin. Otherwise requires admin to create users.

        Returns dict with:
        - user: The created user
        - error: Error message if registration failed
        """
        user_count = self.user_repo.count()

        # If users exist, require admin to create new users
        if user_count > 0:
            if current_user is None or not current_user.is_admin:
                return {
                    "user": None,
                    "error": "Admin access required to create users",
                }

        # Check if username already exists
        if self.user_repo.username_exists(username):
            return {"user": None, "error": "Username already registered"}

        # Check if email already exists
        if self.user_repo.email_exists(email):
            return {"user": None, "error": "Email already registered"}

        # First user becomes admin
        actual_role = "admin" if user_count == 0 else role

        user_data = {
            "username": username,
            "email": email,
            "hashed_password": get_password_hash(password),
            "role": actual_role,
        }

        user = self.user_repo.create(user_data)
        self.user_repo.commit()
        self.user_repo.refresh(user)

        return {"user": user, "error": None}

    def list_users(self) -> list[User]:
        """List all users ordered by username."""
        return self.user_repo.list_ordered_by_username()
