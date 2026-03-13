import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, Integer, ForeignKey, Date, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class GraduationRequirement(Base):
    """
    Graduation requirements based on clinic types / rotation templates.
    """

    __tablename__ = "graduation_requirements"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    pgy_level = Column(Integer, nullable=False, index=True)
    rotation_template_id = Column(
        GUID(),
        ForeignKey("rotation_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    min_halves = Column(Integer, nullable=False, default=0)
    target_halves = Column(Integer, nullable=True)
    by_date = Column(Date, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    rotation_template = relationship("RotationTemplate")

    __table_args__ = (
        UniqueConstraint(
            "pgy_level", "rotation_template_id", name="uq_graduation_req_pgy_template"
        ),
    )
