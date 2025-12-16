"""Auth controller for request/response handling."""

from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.error_codes import ErrorCode, get_error_code_from_message
from app.services.auth_service import AuthService
from app.schemas.auth import (
    Token,
    UserCreate,
    UserResponse,
)
from app.models.user import User


class AuthController:
    """Controller for authentication endpoints."""

    def __init__(self, db: Session):
        self.service = AuthService(db)

    def login(self, username: str, password: str) -> Token:
        """Authenticate user and return JWT token."""
        result = self.service.authenticate(username, password)

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result["error"],
                headers={"WWW-Authenticate": "Bearer"},
            )

        return Token(
            access_token=result["access_token"],
            token_type=result["token_type"],
        )

    def register_user(
        self,
        user_in: UserCreate,
        current_user: Optional[User] = None,
    ) -> UserResponse:
        """Register a new user."""
        result = self.service.register_user(
            username=user_in.username,
            email=user_in.email,
            password=user_in.password,
            role=user_in.role,
            current_user=current_user,
        )

        if result["error"]:
            # Determine appropriate status code using structured error codes
            error_code = result.get("error_code") or get_error_code_from_message(result["error"])

            if error_code == ErrorCode.FORBIDDEN:
                status_code = status.HTTP_403_FORBIDDEN
            elif error_code == ErrorCode.UNAUTHORIZED:
                status_code = status.HTTP_401_UNAUTHORIZED
            else:
                status_code = status.HTTP_400_BAD_REQUEST

            raise HTTPException(status_code=status_code, detail=result["error"])

        return result["user"]

    def list_users(self) -> list[UserResponse]:
        """List all users."""
        return self.service.list_users()
