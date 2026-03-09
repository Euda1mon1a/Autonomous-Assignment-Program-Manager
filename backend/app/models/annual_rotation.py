"""Annual Rotation Optimizer models — plan and assignment storage."""

import uuid
from datetime import datetime, UTC

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class AnnualRotationPlan(Base):
    """
    An annual rotation optimization plan.

    Lifecycle: draft → optimized → approved → published.
    Each plan stores solver results and links to its assignments.
    """

    __tablename__ = "annual_rotation_plans"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    academic_year = Column(Integer, nullable=False)  # e.g., 2026
    name = Column(String(200), nullable=False)
    status = Column(
        String(20), nullable=False, default="draft"
    )  # draft, optimized, approved, published
    solver_time_limit = Column(Float, default=30.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(GUID(), ForeignKey("users.id"), nullable=True)

    # Solver results
    objective_value = Column(Integer, nullable=True)
    solver_status = Column(String(50), nullable=True)
    solve_duration_ms = Column(Integer, nullable=True)

    # Relationships
    assignments = relationship(
        "AnnualRotationAssignment",
        back_populates="plan",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<AnnualRotationPlan(name='{self.name}', "
            f"year={self.academic_year}, status='{self.status}')>"
        )


class AnnualRotationAssignment(Base):
    """
    A single rotation assignment within an annual plan.

    Links a person to a rotation name for a specific block number.
    The is_fixed flag marks assignments that come from fixed rules
    (FMO, Military) rather than the solver.
    """

    __tablename__ = "annual_rotation_assignments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    plan_id = Column(
        GUID(),
        ForeignKey("annual_rotation_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    person_id = Column(GUID(), ForeignKey("people.id"), nullable=False)
    block_number = Column(Integer, nullable=False)  # 0-12
    rotation_name = Column(String(100), nullable=False)
    is_fixed = Column(Boolean, default=False)  # FMO, Military — not from solver

    __table_args__ = (UniqueConstraint("plan_id", "person_id", "block_number"),)

    plan = relationship("AnnualRotationPlan", back_populates="assignments")
