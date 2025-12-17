"""User repository for database operations."""


from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User entity operations."""

    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_username(self, username: str) -> User | None:
        """Get a user by username."""
        return (
            self.db.query(User)
            .filter(User.username == username)
            .first()
        )

    def get_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        return (
            self.db.query(User)
            .filter(User.email == email)
            .first()
        )

    def list_ordered_by_username(self) -> list[User]:
        """List all users ordered by username."""
        return self.db.query(User).order_by(User.username).all()

    def get_admins(self) -> list[User]:
        """Get all admin users."""
        return (
            self.db.query(User)
            .filter(User.role == "admin")
            .all()
        )

    def username_exists(self, username: str) -> bool:
        """Check if a username is already taken."""
        return (
            self.db.query(User)
            .filter(User.username == username)
            .first()
            is not None
        )

    def email_exists(self, email: str) -> bool:
        """Check if an email is already registered."""
        return (
            self.db.query(User)
            .filter(User.email == email)
            .first()
            is not None
        )
