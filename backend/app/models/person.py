"""Person model - residents and faculty."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID, StringArrayType


class FacultyRole(str, Enum):
    """
    Faculty role types with specific scheduling constraints.

    Each role has different clinic requirements, FMIT eligibility,
    and call preferences. See FACULTY_SCHEDULING_SPECIFICATION.md.
    """

    PD = "pd"  # Program Director: 0 clinic, avoid Tue call
    APD = "apd"  # Associate Program Director: 2/week, avoid Tue call
    OIC = "oic"  # Officer in Charge: 2/week
    DEPT_CHIEF = "dept_chief"  # Department Chief: 1/week, prefers Wed call
    SPORTS_MED = "sports_med"  # Sports Medicine: 0 regular clinic, 4 SM clinic/week
    CORE = "core"  # Core Faculty: max 4/week
    ADJUNCT = (
        "adjunct"  # Adjunct Faculty: not auto-scheduled, can be pre-loaded to FMIT
    )


class ScreenerRole(str, Enum):
    """
    Screener role types for clinic session staffing.

    Different roles have different efficiency levels and availability.
    """

    DEDICATED = "dedicated"  # Dedicated screener (100% efficiency)
    RN = "rn"  # Registered Nurse (90% efficiency)
    EMT = "emt"  # Emergency Medical Technician (80% efficiency)
    RESIDENT = "resident"  # Resident serving as screener (70% efficiency)


class Person(Base):
    """
    Represents residents and faculty members.

    Residents have PGY levels (1-3) and are supervised.
    Faculty have specialties and can perform procedures.

    Performance Optimization Notes:
    - Consider adding composite index on (type, pgy_level) for resident queries
    - Consider adding index on faculty_role for faculty queries
    - Email already has unique constraint which creates an index

    Suggested indexes (add via Alembic migration):
    CREATE INDEX idx_people_type_pgy ON people(type, pgy_level) WHERE type = 'resident';
    CREATE INDEX idx_people_faculty_role ON people(faculty_role) WHERE type = 'faculty';
    CREATE INDEX idx_people_type_name ON people(type, name);
    """

    __tablename__ = "people"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)  # Performance: Indexed for name-based searches
    type = Column(String(50), nullable=False, index=True)  # Performance: Indexed for filtering by type
    email = Column(String(255), unique=True)  # Unique constraint creates index automatically

    # Resident-specific fields
    pgy_level = Column(Integer, index=True)  # Performance: Indexed for PGY-level filtering

    # Capacity/workload fields
    target_clinical_blocks = Column(
        Integer
    )  # Expected number of clinical blocks per scheduling period
    # Examples:
    # - Regular resident: 48-56 blocks (12-14 weeks * 4 blocks/week)
    # - Chief resident: 24 blocks (6 clinical + 6 admin)
    # - Research track: 8 blocks (2 clinical weeks)

    # Faculty-specific fields
    performs_procedures = Column(Boolean, default=False)
    specialties = Column(StringArrayType())  # e.g., ['Sports Medicine', 'Dermatology']
    primary_duty = Column(String(255))
    faculty_role = Column(
        String(50)
    )  # FacultyRole enum value (pd, apd, oic, dept_chief, sports_med, core)

    # Screener-specific fields
    screener_role = Column(
        String(50)
    )  # ScreenerRole enum value (dedicated, rn, emt, resident)
    can_screen = Column(
        Boolean, default=False
    )  # Whether this person can serve as screener
    screening_efficiency = Column(
        Integer, default=100
    )  # Efficiency percentage (70-100)

    # Call and FMIT equity tracking (reset annually)
    # These track cumulative counts for fair distribution
    sunday_call_count = Column(
        Integer, default=0
    )  # Sunday calls (tracked separately - worst day)
    weekday_call_count = Column(
        Integer, default=0
    )  # Mon-Thurs calls (combined equity pool)
    fmit_weeks_count = Column(
        Integer, default=0
    )  # FMIT weeks this year (target ~6 max)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignments = relationship("Assignment", back_populates="person")
    absences = relationship(
        "Absence", back_populates="person", foreign_keys="[Absence.person_id]"
    )
    call_assignments = relationship("CallAssignment", back_populates="person")
    procedure_credentials = relationship(
        "ProcedureCredential", back_populates="person", cascade="all, delete-orphan"
    )
    certifications = relationship(
        "PersonCertification", back_populates="person", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("type IN ('resident', 'faculty')", name="check_person_type"),
        CheckConstraint(
            "pgy_level IS NULL OR pgy_level BETWEEN 1 AND 3", name="check_pgy_level"
        ),
        CheckConstraint(
            "faculty_role IS NULL OR faculty_role IN ('pd', 'apd', 'oic', 'dept_chief', 'sports_med', 'core')",
            name="check_faculty_role",
        ),
        CheckConstraint(
            "screener_role IS NULL OR screener_role IN ('dedicated', 'rn', 'emt', 'resident')",
            name="check_screener_role",
        ),
        CheckConstraint(
            "screening_efficiency IS NULL OR screening_efficiency BETWEEN 0 AND 100",
            name="check_screening_efficiency",
        ),
    )

    def __repr__(self):
        return f"<Person(name='{self.name}', type='{self.type}')>"

    @property
    def is_resident(self) -> bool:
        """Check if person is a resident."""
        return self.type == "resident"

    @property
    def is_faculty(self) -> bool:
        """Check if person is faculty."""
        return self.type == "faculty"

    @property
    def supervision_ratio(self) -> int:
        """
        Get ACGME supervision ratio for this person.
        PGY-1: 1:2 (1 faculty per 2 residents)
        PGY-2/3: 1:4 (1 faculty per 4 residents)
        """
        if not self.is_resident:
            return 0
        return 2 if self.pgy_level == 1 else 4

    @property
    def role_enum(self) -> FacultyRole | None:
        """Get faculty role as enum, or None if not faculty or no role set."""
        if not self.is_faculty or not self.faculty_role:
            return None
        try:
            return FacultyRole(self.faculty_role)
        except ValueError:
            return None

    @property
    def weekly_clinic_limit(self) -> int:
        """
        Get weekly clinic half-day limit for this faculty member.

        Returns:
            int: Maximum clinic half-days per week (0 if not faculty)

        Role limits:
            - PD: 0
            - Dept Chief: 1
            - APD/OIC: 2
            - Sports Med: 0 (has SM clinic instead)
            - Core: 4
            - Adjunct: 0 (not auto-scheduled)
        """
        if not self.is_faculty:
            return 0

        role = self.role_enum
        if role is None:
            return 4  # Default to core faculty limit

        limits = {
            FacultyRole.PD: 0,
            FacultyRole.DEPT_CHIEF: 1,
            FacultyRole.APD: 2,
            FacultyRole.OIC: 2,
            FacultyRole.SPORTS_MED: 0,  # No regular clinic
            FacultyRole.CORE: 4,
            FacultyRole.ADJUNCT: 0,  # Not auto-scheduled
        }
        return limits.get(role, 4)

    @property
    def block_clinic_limit(self) -> int:
        """
        Get 4-week block clinic half-day limit.

        APD/OIC have flexibility within block (can do 0 one week, 4 another).
        Core faculty have hard max of 16/block.
        """
        if not self.is_faculty:
            return 0

        role = self.role_enum
        if role in (FacultyRole.APD, FacultyRole.OIC):
            return 8  # 2/week * 4 weeks, but flexible
        elif role == FacultyRole.CORE:
            return 16  # 4/week * 4 weeks, hard max
        else:
            return self.weekly_clinic_limit * 4

    @property
    def sm_clinic_weekly_target(self) -> int:
        """
        Get weekly SM clinic half-day target for sports medicine faculty.

        Returns:
            int: SM clinic half-days per week (4 for SM faculty, 0 otherwise)
        """
        if self.role_enum == FacultyRole.SPORTS_MED:
            return 4
        return 0

    @property
    def avoid_tuesday_call(self) -> bool:
        """Check if this faculty should avoid Tuesday call (academic commitments)."""
        return self.role_enum in (FacultyRole.PD, FacultyRole.APD)

    @property
    def prefer_wednesday_call(self) -> bool:
        """Check if this faculty prefers Wednesday call (personal preference)."""
        return self.role_enum == FacultyRole.DEPT_CHIEF

    @property
    def is_sports_medicine(self) -> bool:
        """Check if this person is sports medicine faculty or has SM specialty."""
        if self.role_enum == FacultyRole.SPORTS_MED:
            return True
        if self.specialties and "Sports Medicine" in self.specialties:
            return True
        return False
