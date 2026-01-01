"""Certification models - track required certifications like BLS, ACLS, PALS, etc."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class CertificationType(Base):
    """
    Defines certification types that personnel may need.

    Examples:
    - BLS (Basic Life Support) - 2 year renewal
    - ACLS (Advanced Cardiovascular Life Support) - 2 year renewal
    - PALS (Pediatric Advanced Life Support) - 2 year renewal
    - ALSO (Advanced Life Support in Obstetrics) - variable
    - NRP (Neonatal Resuscitation Program) - 2 year renewal

    SQLAlchemy Relationships:
        person_certifications: One-to-many to PersonCertification.
            Back-populates PersonCertification.certification_type.
            Cascade: all, delete-orphan.
            All personnel certifications of this type.
    """

    __tablename__ = "certification_types"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)  # e.g., "BLS", "ACLS"
    full_name = Column(String(255))  # e.g., "Basic Life Support"
    description = Column(Text)

    # Renewal configuration
    renewal_period_months = Column(Integer, default=24)  # Default 2 years

    # Who needs this certification
    required_for_residents = Column(Boolean, default=True)
    required_for_faculty = Column(Boolean, default=True)
    required_for_specialties = Column(
        String(500)
    )  # Comma-separated, e.g., "OB/GYN,Pediatrics"

    # Reminder configuration (days before expiration)
    reminder_days_180 = Column(Boolean, default=True)  # 6 months
    reminder_days_90 = Column(Boolean, default=True)  # 3 months
    reminder_days_30 = Column(Boolean, default=True)  # 1 month
    reminder_days_14 = Column(Boolean, default=True)  # 2 weeks
    reminder_days_7 = Column(Boolean, default=True)  # 1 week

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    person_certifications = relationship(
        "PersonCertification",
        back_populates="certification_type",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<CertificationType(name='{self.name}', renewal_months={self.renewal_period_months})>"

    def get_reminder_days(self) -> list[int]:
        """Get list of days before expiration to send reminders."""
        days = []
        if self.reminder_days_180:
            days.append(180)
        if self.reminder_days_90:
            days.append(90)
        if self.reminder_days_30:
            days.append(30)
        if self.reminder_days_14:
            days.append(14)
        if self.reminder_days_7:
            days.append(7)
        return sorted(days, reverse=True)


class PersonCertification(Base):
    """
    Tracks an individual's certification status.

    Records when someone obtained a certification, when it expires,
    and tracks reminder notifications sent.

    SQLAlchemy Relationships:
        person: Many-to-one to Person.
            Back-populates Person.certifications.
            FK ondelete=CASCADE. The person holding this certification.

        certification_type: Many-to-one to CertificationType.
            Back-populates CertificationType.person_certifications.
            FK ondelete=CASCADE. The type of certification.
    """

    __tablename__ = "person_certifications"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Links
    person_id = Column(
        GUID(), ForeignKey("people.id", ondelete="CASCADE"), nullable=False
    )
    certification_type_id = Column(
        GUID(), ForeignKey("certification_types.id", ondelete="CASCADE"), nullable=False
    )

    # Certification details
    certification_number = Column(String(100))  # Card/certificate number
    issued_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)

    # Status
    status = Column(
        String(50), default="current"
    )  # 'current', 'expiring_soon', 'expired', 'pending'

    # Verification
    verified_by = Column(String(255))  # Who verified the cert
    verified_date = Column(Date)
    document_url = Column(String(500))  # Link to uploaded certificate image

    # Reminder tracking (to avoid duplicate emails)
    reminder_180_sent = Column(DateTime)
    reminder_90_sent = Column(DateTime)
    reminder_30_sent = Column(DateTime)
    reminder_14_sent = Column(DateTime)
    reminder_7_sent = Column(DateTime)

    # Notes
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    person = relationship("Person", back_populates="certifications")
    certification_type = relationship(
        "CertificationType", back_populates="person_certifications"
    )

    # Unique constraint: one certification type per person (latest one)
    __table_args__ = (
        UniqueConstraint(
            "person_id", "certification_type_id", name="uq_person_certification_type"
        ),
    )

    def __repr__(self):
        return f"<PersonCertification(person_id='{self.person_id}', type_id='{self.certification_type_id}', expires='{self.expiration_date}')>"

    @property
    def is_expired(self) -> bool:
        """Check if certification has expired."""
        return self.expiration_date < date.today()

    @property
    def is_expiring_soon(self) -> bool:
        """Check if certification expires within 6 months."""
        if self.is_expired:
            return False
        days_until = (self.expiration_date - date.today()).days
        return days_until <= 180

    @property
    def days_until_expiration(self) -> int:
        """Get days until expiration (negative if expired)."""
        return (self.expiration_date - date.today()).days

    def needs_reminder(self, days: int) -> bool:
        """Check if a reminder should be sent for this threshold."""
        if self.is_expired:
            return False

        days_until = self.days_until_expiration
        if days_until > days:
            return False

        # Check if reminder already sent
        reminder_field = f"reminder_{days}_sent"
        return not (hasattr(self, reminder_field) and getattr(self, reminder_field))

    def mark_reminder_sent(self, days: int) -> None:
        """Mark a reminder as sent."""
        reminder_field = f"reminder_{days}_sent"
        if hasattr(self, reminder_field):
            setattr(self, reminder_field, datetime.utcnow())
