"""User model for authentication."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, String

from app.db.base import Base
from app.db.types import GUID


class User(Base):
    """
    User model for authentication and authorization.

    Roles:
    - admin: Full access to all features
    - coordinator: Can manage schedules and people
    - faculty: Can view schedules and manage own availability
    - clinical_staff: General clinical staff (RN, LPN, MSA)
    - rn: Registered Nurse
    - lpn: Licensed Practical Nurse
    - msa: Medical Support Assistant
    - resident: Resident physician
    """
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
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
            "role IN ('admin', 'coordinator', 'faculty', 'clinical_staff', 'rn', 'lpn', 'msa', 'resident')",
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
    def is_clinical_staff(self) -> bool:
        """Check if user has clinical staff role (rn, lpn, msa, or clinical_staff)."""
        return self.role in ("clinical_staff", "rn", "lpn", "msa")

    @property
    def is_faculty(self) -> bool:
        """Check if user has faculty role."""
        return self.role == "faculty"

    @property
    def is_resident(self) -> bool:
        """Check if user has resident role."""
        return self.role == "resident"

    @property
    def can_manage_schedules(self) -> bool:
        """Check if user can create/modify schedules."""
        return self.role in ("admin", "coordinator")
