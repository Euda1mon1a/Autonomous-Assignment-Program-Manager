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

    def get_by_name(self, name: str) -> CertificationType | None:
        """Get a certification type by name."""
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

    def get_by_person_and_type(
        self,
        person_id: UUID,
        certification_type_id: UUID,
    ) -> PersonCertification | None:
        """Get a certification by person and type."""
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
