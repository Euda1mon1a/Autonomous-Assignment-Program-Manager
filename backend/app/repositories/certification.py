"""Certification repository for database operations."""

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.certification import CertificationType, PersonCertification
from app.repositories.base import BaseRepository


class CertificationTypeRepository(BaseRepository[CertificationType]):
    """Repository for CertificationType entity operations."""

    def __init__(self, db: Session):
        super().__init__(CertificationType, db)

    def get_by_id(self, id: UUID) -> CertificationType | None:
        """Get a single entity by ID."""
        if id is None:
            raise ValueError("ID cannot be None")
        if not isinstance(id, UUID):
            raise TypeError(f"ID must be a UUID, got {type(id).__name__}")
        return super().get_by_id(id)

    def create(self, obj_in: dict) -> CertificationType:
        """Create a new entity from a dictionary."""
        if obj_in is None:
            raise ValueError("Input data cannot be None")
        if not isinstance(obj_in, dict):
            raise TypeError(f"Input data must be a dictionary, got {type(obj_in).__name__}")
        if not obj_in:
            raise ValueError("Input data cannot be empty")
        return super().create(obj_in)

    def update(self, db_obj: CertificationType, obj_in: dict) -> CertificationType:
        """Update an existing entity with new values."""
        if db_obj is None:
            raise ValueError("Database object cannot be None")
        if not isinstance(db_obj, CertificationType):
            raise TypeError(f"Database object must be a CertificationType, got {type(db_obj).__name__}")
        if obj_in is None:
            raise ValueError("Input data cannot be None")
        if not isinstance(obj_in, dict):
            raise TypeError(f"Input data must be a dictionary, got {type(obj_in).__name__}")
        if not obj_in:
            raise ValueError("Input data cannot be empty")
        return super().update(db_obj, obj_in)

    def delete(self, db_obj: CertificationType) -> None:
        """Delete an entity."""
        if db_obj is None:
            raise ValueError("Database object cannot be None")
        if not isinstance(db_obj, CertificationType):
            raise TypeError(f"Database object must be a CertificationType, got {type(db_obj).__name__}")
        super().delete(db_obj)

    def get_by_name(self, name: str) -> CertificationType | None:
        """Get a certification type by name."""
        if name is None:
            raise ValueError("Name cannot be None")
        if not isinstance(name, str):
            raise TypeError(f"Name must be a string, got {type(name).__name__}")
        if not name.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return (
            self.db.query(CertificationType)
            .filter(CertificationType.name == name)
            .first()
        )

    def list_active(self) -> list[CertificationType]:
        """List all active certification types."""
        return (
            self.db.query(CertificationType)
            .filter(CertificationType.is_active)
            .order_by(CertificationType.name)
            .all()
        )

    def list_required_for_person_type(self, person_type: str) -> list[CertificationType]:
        """List certifications required for residents or faculty."""
        if person_type is None:
            raise ValueError("Person type cannot be None")
        if not isinstance(person_type, str):
            raise TypeError(f"Person type must be a string, got {type(person_type).__name__}")
        if not person_type.strip():
            raise ValueError("Person type cannot be empty or whitespace")

        valid_person_types = ["resident", "faculty"]
        if person_type not in valid_person_types:
            raise ValueError(f"Person type must be one of {valid_person_types}, got '{person_type}'")

        query = self.db.query(CertificationType).filter(CertificationType.is_active)

        if person_type == "resident":
            query = query.filter(CertificationType.required_for_residents)
        elif person_type == "faculty":
            query = query.filter(CertificationType.required_for_faculty)

        return query.order_by(CertificationType.name).all()


class PersonCertificationRepository(BaseRepository[PersonCertification]):
    """Repository for PersonCertification entity operations."""

    def __init__(self, db: Session):
        super().__init__(PersonCertification, db)

    def get_by_id(self, id: UUID) -> PersonCertification | None:
        """Get a single entity by ID."""
        if id is None:
            raise ValueError("ID cannot be None")
        if not isinstance(id, UUID):
            raise TypeError(f"ID must be a UUID, got {type(id).__name__}")
        return super().get_by_id(id)

    def create(self, obj_in: dict) -> PersonCertification:
        """Create a new entity from a dictionary."""
        if obj_in is None:
            raise ValueError("Input data cannot be None")
        if not isinstance(obj_in, dict):
            raise TypeError(f"Input data must be a dictionary, got {type(obj_in).__name__}")
        if not obj_in:
            raise ValueError("Input data cannot be empty")
        return super().create(obj_in)

    def update(self, db_obj: PersonCertification, obj_in: dict) -> PersonCertification:
        """Update an existing entity with new values."""
        if db_obj is None:
            raise ValueError("Database object cannot be None")
        if not isinstance(db_obj, PersonCertification):
            raise TypeError(f"Database object must be a PersonCertification, got {type(db_obj).__name__}")
        if obj_in is None:
            raise ValueError("Input data cannot be None")
        if not isinstance(obj_in, dict):
            raise TypeError(f"Input data must be a dictionary, got {type(obj_in).__name__}")
        if not obj_in:
            raise ValueError("Input data cannot be empty")
        return super().update(db_obj, obj_in)

    def delete(self, db_obj: PersonCertification) -> None:
        """Delete an entity."""
        if db_obj is None:
            raise ValueError("Database object cannot be None")
        if not isinstance(db_obj, PersonCertification):
            raise TypeError(f"Database object must be a PersonCertification, got {type(db_obj).__name__}")
        super().delete(db_obj)

    def get_by_person_and_type(
        self,
        person_id: UUID,
        certification_type_id: UUID,
    ) -> PersonCertification | None:
        """Get a certification by person and type."""
        if person_id is None:
            raise ValueError("Person ID cannot be None")
        if not isinstance(person_id, UUID):
            raise TypeError(f"Person ID must be a UUID, got {type(person_id).__name__}")
        if certification_type_id is None:
            raise ValueError("Certification type ID cannot be None")
        if not isinstance(certification_type_id, UUID):
            raise TypeError(f"Certification type ID must be a UUID, got {type(certification_type_id).__name__}")
        return (
            self.db.query(PersonCertification)
            .filter(
                PersonCertification.person_id == person_id,
                PersonCertification.certification_type_id == certification_type_id,
            )
            .first()
        )

    def list_by_person(
        self,
        person_id: UUID,
        include_expired: bool = True,
    ) -> list[PersonCertification]:
        """List all certifications for a person."""
        if person_id is None:
            raise ValueError("Person ID cannot be None")
        if not isinstance(person_id, UUID):
            raise TypeError(f"Person ID must be a UUID, got {type(person_id).__name__}")
        if not isinstance(include_expired, bool):
            raise TypeError(f"include_expired must be a boolean, got {type(include_expired).__name__}")

        query = (
            self.db.query(PersonCertification)
            .options(joinedload(PersonCertification.certification_type))
            .filter(PersonCertification.person_id == person_id)
        )

        if not include_expired:
            query = query.filter(PersonCertification.expiration_date >= date.today())

        return query.order_by(PersonCertification.expiration_date).all()

    def list_expiring_in_days(
        self,
        days: int,
        exact: bool = False,
    ) -> list[PersonCertification]:
        """
        List certifications expiring within N days.

        Args:
            days: Number of days to look ahead
            exact: If True, only return certs expiring exactly on that day
        """
        if days is None:
            raise ValueError("Days cannot be None")
        if not isinstance(days, int):
            raise TypeError(f"Days must be an integer, got {type(days).__name__}")
        if days < 0:
            raise ValueError(f"Days must be non-negative, got {days}")
        if not isinstance(exact, bool):
            raise TypeError(f"exact must be a boolean, got {type(exact).__name__}")

        today = date.today()
        target_date = today + timedelta(days=days)

        query = (
            self.db.query(PersonCertification)
            .options(
                joinedload(PersonCertification.person),
                joinedload(PersonCertification.certification_type),
            )
            .filter(PersonCertification.expiration_date >= today)  # Not already expired
        )

        if exact:
            query = query.filter(PersonCertification.expiration_date == target_date)
        else:
            query = query.filter(PersonCertification.expiration_date <= target_date)

        return query.order_by(PersonCertification.expiration_date).all()

    def list_needing_reminder(self, days: int) -> list[PersonCertification]:
        """
        List certifications that need a reminder for a specific threshold.

        Returns certs expiring within `days` that haven't had that reminder sent.
        """
        if days is None:
            raise ValueError("Days cannot be None")
        if not isinstance(days, int):
            raise TypeError(f"Days must be an integer, got {type(days).__name__}")
        if days < 0:
            raise ValueError(f"Days must be non-negative, got {days}")

        today = date.today()
        target_date = today + timedelta(days=days)
        reminder_field = f"reminder_{days}_sent"

        query = (
            self.db.query(PersonCertification)
            .options(
                joinedload(PersonCertification.person),
                joinedload(PersonCertification.certification_type),
            )
            .filter(
                PersonCertification.expiration_date >= today,
                PersonCertification.expiration_date <= target_date,
            )
        )

        # Filter where reminder hasn't been sent
        if hasattr(PersonCertification, reminder_field):
            query = query.filter(getattr(PersonCertification, reminder_field).is_(None))

        return query.all()

    def list_expired(self) -> list[PersonCertification]:
        """List all expired certifications."""
        return (
            self.db.query(PersonCertification)
            .options(
                joinedload(PersonCertification.person),
                joinedload(PersonCertification.certification_type),
            )
            .filter(PersonCertification.expiration_date < date.today())
            .order_by(PersonCertification.expiration_date.desc())
            .all()
        )

    def list_by_certification_type(
        self,
        certification_type_id: UUID,
        status: str | None = None,
    ) -> list[PersonCertification]:
        """List all certifications of a specific type."""
        if certification_type_id is None:
            raise ValueError("Certification type ID cannot be None")
        if not isinstance(certification_type_id, UUID):
            raise TypeError(f"Certification type ID must be a UUID, got {type(certification_type_id).__name__}")
        if status is not None and not isinstance(status, str):
            raise TypeError(f"Status must be a string or None, got {type(status).__name__}")
        if status is not None and not status.strip():
            raise ValueError("Status cannot be empty or whitespace")

        query = (
            self.db.query(PersonCertification)
            .options(joinedload(PersonCertification.person))
            .filter(PersonCertification.certification_type_id == certification_type_id)
        )

        if status:
            query = query.filter(PersonCertification.status == status)

        return query.order_by(PersonCertification.expiration_date).all()

    def get_compliance_summary(self) -> dict:
        """Get overall certification compliance summary."""
        today = date.today()
        soon = today + timedelta(days=180)

        total = self.db.query(PersonCertification).count()
        current = (
            self.db.query(PersonCertification)
            .filter(PersonCertification.expiration_date >= today)
            .count()
        )
        expiring_soon = (
            self.db.query(PersonCertification)
            .filter(
                PersonCertification.expiration_date >= today,
                PersonCertification.expiration_date <= soon,
            )
            .count()
        )
        expired = (
            self.db.query(PersonCertification)
            .filter(PersonCertification.expiration_date < today)
            .count()
        )

        return {
            "total": total,
            "current": current,
            "expiring_soon": expiring_soon,
            "expired": expired,
            "compliance_rate": (current / total * 100) if total > 0 else 100,
        }

    def get_missing_certifications_for_person(
        self,
        person_id: UUID,
        person_type: str,
    ) -> list[CertificationType]:
        """Get certifications a person is missing but should have."""
        if person_id is None:
            raise ValueError("Person ID cannot be None")
        if not isinstance(person_id, UUID):
            raise TypeError(f"Person ID must be a UUID, got {type(person_id).__name__}")
        if person_type is None:
            raise ValueError("Person type cannot be None")
        if not isinstance(person_type, str):
            raise TypeError(f"Person type must be a string, got {type(person_type).__name__}")
        if not person_type.strip():
            raise ValueError("Person type cannot be empty or whitespace")

        valid_person_types = ["resident", "faculty"]
        if person_type not in valid_person_types:
            raise ValueError(f"Person type must be one of {valid_person_types}, got '{person_type}'")

        # Get required cert types
        cert_type_repo = CertificationTypeRepository(self.db)
        required_types = cert_type_repo.list_required_for_person_type(person_type)

        # Get person's current certs
        current_certs = self.list_by_person(person_id, include_expired=False)
        current_type_ids = {c.certification_type_id for c in current_certs}

        # Find missing
        missing = [ct for ct in required_types if ct.id not in current_type_ids]
        return missing

    def update_all_statuses(self) -> int:
        """Update status field for all certifications based on expiration date."""
        today = date.today()
        soon = today + timedelta(days=180)
        updated = 0

        all_certs = self.db.query(PersonCertification).all()
        for cert in all_certs:
            old_status = cert.status
            if cert.expiration_date < today:
                cert.status = 'expired'
            elif cert.expiration_date <= soon:
                cert.status = 'expiring_soon'
            else:
                cert.status = 'current'

            if cert.status != old_status:
                updated += 1

        self.db.flush()
        return updated
