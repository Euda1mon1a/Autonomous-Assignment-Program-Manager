"""Clinic session model - tracks daily clinic staffing and screener ratios."""
import uuid
from datetime import date, datetime
from enum import Enum

from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, Float, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class SessionType(str, Enum):
    """
    Session time of day types.

    AM and PM sessions have different staffing requirements.
    """
    AM = "am"
    PM = "pm"


class ClinicType(str, Enum):
    """
    Clinic type categories.

    Different clinic types may have different screener requirements.
    """
    FAMILY_MEDICINE = "family_medicine"
    SPORTS_MEDICINE = "sports_medicine"
    PEDIATRICS = "pediatrics"
    PROCEDURES = "procedures"


class StaffingStatus(str, Enum):
    """
    Staffing adequacy status.

    Based on screener ratio quality and coverage levels.
    """
    OPTIMAL = "optimal"           # 1:3 or better
    ADEQUATE = "adequate"         # 1:4
    SUBOPTIMAL = "suboptimal"     # 1:5
    INADEQUATE = "inadequate"     # 1:6 or worse
    UNSTAFFED = "unstaffed"       # No screeners


class ClinicSession(Base):
    """
    Represents a single clinic session with staffing metrics.

    Tracks physician and screener counts, ratios, and whether
    RN fallback was used. Used for monitoring clinic staffing
    patterns and identifying understaffed sessions.
    """
    __tablename__ = "clinic_sessions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False, index=True)
    session_type = Column(String(2), nullable=False)  # SessionType enum value (am, pm)
    clinic_type = Column(String(50), nullable=False)  # ClinicType enum value

    # Staffing counts
    physician_count = Column(Integer, nullable=False, default=0)
    screener_count = Column(Integer, nullable=False, default=0)

    # Ratio metrics
    screener_ratio = Column(Float)  # Actual ratio (e.g., 3.5 for 1:3.5)

    # Status tracking
    staffing_status = Column(String(20), nullable=False)  # StaffingStatus enum value
    rn_fallback_used = Column(Boolean, default=False)  # Whether RN was used as fallback

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    # Note: Will be connected to assignments when screener assignments are implemented

    __table_args__ = (
        CheckConstraint("session_type IN ('am', 'pm')", name="check_session_type"),
        CheckConstraint(
            "clinic_type IN ('family_medicine', 'sports_medicine', 'pediatrics', 'procedures')",
            name="check_clinic_type"
        ),
        CheckConstraint(
            "staffing_status IN ('optimal', 'adequate', 'suboptimal', 'inadequate', 'unstaffed')",
            name="check_staffing_status"
        ),
        CheckConstraint("physician_count >= 0", name="check_physician_count"),
        CheckConstraint("screener_count >= 0", name="check_screener_count"),
        CheckConstraint("screener_ratio IS NULL OR screener_ratio >= 0", name="check_screener_ratio"),
    )

    def __repr__(self):
        return f"<ClinicSession(date='{self.date}', session='{self.session_type}', ratio='1:{self.screener_ratio}')>"

    @property
    def ratio_quality(self) -> str:
        """
        Get human-readable ratio quality assessment.

        Returns:
            str: Quality description based on screener ratio
        """
        if self.screener_ratio is None or self.screener_count == 0:
            return "No screener coverage"

        if self.screener_ratio <= 3.0:
            return "Optimal (1:3 or better)"
        elif self.screener_ratio <= 4.0:
            return "Adequate (1:4)"
        elif self.screener_ratio <= 5.0:
            return "Suboptimal (1:5)"
        else:
            return f"Inadequate (1:{self.screener_ratio:.1f})"

    @property
    def display_name(self) -> str:
        """Get display name for this clinic session."""
        return f"{self.date.strftime('%Y-%m-%d')} {self.session_type.upper()}"
