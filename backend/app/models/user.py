"""User model for authentication."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class User(Base):
    """
    User model for authentication and authorization.

    Roles:
    - admin: Full access to all features
    - coordinator: Can manage schedules and people
    - faculty: Can view schedules and manage own availability
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="coordinator")
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'coordinator', 'faculty')",
            name="check_user_role"
        ),
    )

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == "admin"

    @property
    def is_coordinator(self) -> bool:
        """Check if user has coordinator role."""
        return self.role == "coordinator"

    @property
    def can_manage_schedules(self) -> bool:
        """Check if user can create/modify schedules."""
        return self.role in ("admin", "coordinator")
