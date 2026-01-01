"""Certification service for business logic."""

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.certification import CertificationType, PersonCertification
from app.repositories.certification import (
    CertificationTypeRepository,
    PersonCertificationRepository,
)
from app.repositories.person import PersonRepository


class CertificationService:
    """Service for certification business logic."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.cert_type_repo = CertificationTypeRepository(db)
        self.person_cert_repo = PersonCertificationRepository(db)
        self.person_repo = PersonRepository(db)

    # ========================================================================
    # Certification Type Operations
    # ========================================================================

    def get_certification_type(self, cert_type_id: UUID) -> CertificationType | None:
        """Get a certification type by ID."""
        return self.cert_type_repo.get_by_id(cert_type_id)

    def get_certification_type_by_name(self, name: str) -> CertificationType | None:
        """Get a certification type by name."""
        return self.cert_type_repo.get_by_name(name)

    def list_certification_types(self, active_only: bool = True) -> dict:
        """List all certification types."""
        if active_only:
            types = self.cert_type_repo.list_active()
        else:
            types = self.cert_type_repo.get_all()
        return {"items": types, "total": len(types)}

    def create_certification_type(
        self,
        name: str,
        full_name: str | None = None,
        description: str | None = None,
        renewal_period_months: int = 24,
        required_for_residents: bool = True,
        required_for_faculty: bool = True,
        **kwargs,
    ) -> dict:
        """Create a new certification type."""
        # Check for duplicate name
        existing = self.cert_type_repo.get_by_name(name)
        if existing:
            return {
                "certification_type": None,
                "error": f"Certification type '{name}' already exists",
            }

        data = {
            "name": name,
            "full_name": full_name,
            "description": description,
            "renewal_period_months": renewal_period_months,
            "required_for_residents": required_for_residents,
            "required_for_faculty": required_for_faculty,
            **kwargs,
        }

        cert_type = self.cert_type_repo.create(data)
        self.cert_type_repo.commit()
        self.cert_type_repo.refresh(cert_type)

        return {"certification_type": cert_type, "error": None}

    def update_certification_type(self, cert_type_id: UUID, update_data: dict) -> dict:
        """Update a certification type."""
        cert_type = self.cert_type_repo.get_by_id(cert_type_id)
        if not cert_type:
            return {"certification_type": None, "error": "Certification type not found"}

        cert_type = self.cert_type_repo.update(cert_type, update_data)
        self.cert_type_repo.commit()
        self.cert_type_repo.refresh(cert_type)

        return {"certification_type": cert_type, "error": None}

    # ========================================================================
    # Person Certification Operations
    # ========================================================================

    def get_person_certification(self, cert_id: UUID) -> PersonCertification | None:
        """Get a person certification by ID."""
        return self.person_cert_repo.get_by_id(cert_id)

    def list_certifications_for_person(
        self,
        person_id: UUID,
        include_expired: bool = True,
    ) -> dict:
        """List all certifications for a person."""
        certs = self.person_cert_repo.list_by_person(
            person_id, include_expired=include_expired
        )
        return {"items": certs, "total": len(certs)}

    def create_person_certification(
        self,
        person_id: UUID,
        certification_type_id: UUID,
        issued_date: date,
        expiration_date: date,
        certification_number: str | None = None,
        verified_by: str | None = None,
        notes: str | None = None,
    ) -> dict:
        """Create a certification for a person."""
        # Validate person exists
        person = self.person_repo.get_by_id(person_id)
        if not person:
            return {"certification": None, "error": "Person not found"}

        # Validate certification type exists
        cert_type = self.cert_type_repo.get_by_id(certification_type_id)
        if not cert_type:
            return {"certification": None, "error": "Certification type not found"}

        # Check for existing (update instead of duplicate)
        existing = self.person_cert_repo.get_by_person_and_type(
            person_id, certification_type_id
        )
        if existing:
            return {
                "certification": None,
                "error": f"Person already has a {cert_type.name} certification. Update it instead.",
            }

        # Determine status
        today = date.today()
        if expiration_date < today:
            status = "expired"
        elif expiration_date <= today + timedelta(days=180):
            status = "expiring_soon"
        else:
            status = "current"

        data = {
            "person_id": person_id,
            "certification_type_id": certification_type_id,
            "issued_date": issued_date,
            "expiration_date": expiration_date,
            "certification_number": certification_number,
            "verified_by": verified_by,
            "verified_date": date.today() if verified_by else None,
            "notes": notes,
            "status": status,
        }

        cert = self.person_cert_repo.create(data)
        self.person_cert_repo.commit()
        self.person_cert_repo.refresh(cert)

        return {"certification": cert, "error": None}

    def update_person_certification(self, cert_id: UUID, update_data: dict) -> dict:
        """Update a person's certification."""
        cert = self.person_cert_repo.get_by_id(cert_id)
        if not cert:
            return {"certification": None, "error": "Certification not found"}

        # Recalculate status if expiration date changes
        if "expiration_date" in update_data:
            today = date.today()
            exp_date = update_data["expiration_date"]
            if exp_date < today:
                update_data["status"] = "expired"
            elif exp_date <= today + timedelta(days=180):
                update_data["status"] = "expiring_soon"
            else:
                update_data["status"] = "current"

        cert = self.person_cert_repo.update(cert, update_data)
        self.person_cert_repo.commit()
        self.person_cert_repo.refresh(cert)

        return {"certification": cert, "error": None}

    def renew_certification(
        self,
        cert_id: UUID,
        new_issued_date: date,
        new_expiration_date: date,
        new_certification_number: str | None = None,
    ) -> dict:
        """Renew an existing certification with new dates."""
        cert = self.person_cert_repo.get_by_id(cert_id)
        if not cert:
            return {"certification": None, "error": "Certification not found"}

        update_data = {
            "issued_date": new_issued_date,
            "expiration_date": new_expiration_date,
            "status": "current",
            # Reset reminder tracking
            "reminder_180_sent": None,
            "reminder_90_sent": None,
            "reminder_30_sent": None,
            "reminder_14_sent": None,
            "reminder_7_sent": None,
        }
        if new_certification_number:
            update_data["certification_number"] = new_certification_number

        return self.update_person_certification(cert_id, update_data)

    def delete_person_certification(self, cert_id: UUID) -> dict:
        """Delete a person's certification."""
        cert = self.person_cert_repo.get_by_id(cert_id)
        if not cert:
            return {"success": False, "error": "Certification not found"}

        self.person_cert_repo.delete(cert)
        self.person_cert_repo.commit()
        return {"success": True, "error": None}

    # ========================================================================
    # Expiration & Compliance
    # ========================================================================

    def get_expiring_certifications(self, days: int = 180) -> dict:
        """Get all certifications expiring within N days."""
        certs = self.person_cert_repo.list_expiring_in_days(days)
        return {
            "items": certs,
            "total": len(certs),
            "days_threshold": days,
        }

    def get_expired_certifications(self) -> dict:
        """Get all expired certifications."""
        certs = self.person_cert_repo.list_expired()
        return {"items": certs, "total": len(certs)}

    def get_compliance_summary(self) -> dict:
        """Get overall compliance summary."""
        return self.person_cert_repo.get_compliance_summary()

    def get_person_compliance(self, person_id: UUID) -> dict:
        """Get compliance status for a single person."""
        person = self.person_repo.get_by_id(person_id)
        if not person:
            return {"error": "Person not found"}

        # Get person's certifications
        certs = self.person_cert_repo.list_by_person(person_id, include_expired=True)

        # Get required cert types
        required_types = self.cert_type_repo.list_required_for_person_type(person.type)

        # Get missing certs
        missing = self.person_cert_repo.get_missing_certifications_for_person(
            person_id, person.type
        )

        # Count statuses
        current = sum(1 for c in certs if not c.is_expired)
        expired = sum(1 for c in certs if c.is_expired)
        expiring_soon = sum(1 for c in certs if c.is_expiring_soon and not c.is_expired)

        return {
            "person": person,
            "total_required": len(required_types),
            "total_current": current,
            "expired": expired,
            "expiring_soon": expiring_soon,
            "missing": missing,
            "is_compliant": len(missing) == 0 and expired == 0,
            "error": None,
        }

    def get_certifications_needing_reminder(
        self, days: int
    ) -> list[PersonCertification]:
        """Get certifications that need a reminder for a specific threshold."""
        return self.person_cert_repo.list_needing_reminder(days)

    def mark_reminder_sent(self, cert_id: UUID, days: int) -> dict:
        """Mark a reminder as sent for a certification."""
        cert = self.person_cert_repo.get_by_id(cert_id)
        if not cert:
            return {"success": False, "error": "Certification not found"}

        cert.mark_reminder_sent(days)
        self.person_cert_repo.commit()
        return {"success": True, "error": None}

    def update_all_statuses(self) -> int:
        """Update status field for all certifications. Returns count updated."""
        count = self.person_cert_repo.update_all_statuses()
        self.person_cert_repo.commit()
        return count

    # ========================================================================
    # Bulk Operations
    # ========================================================================

    def bulk_add_certifications_for_person(
        self,
        person_id: UUID,
        certification_data: list[dict],
    ) -> dict:
        """Add multiple certifications for a person at once."""
        results = []
        errors = []

        for cert_data in certification_data:
            result = self.create_person_certification(
                person_id=person_id,
                certification_type_id=cert_data["certification_type_id"],
                issued_date=cert_data["issued_date"],
                expiration_date=cert_data["expiration_date"],
                certification_number=cert_data.get("certification_number"),
                verified_by=cert_data.get("verified_by"),
                notes=cert_data.get("notes"),
            )
            if result["error"]:
                errors.append({"data": cert_data, "error": result["error"]})
            else:
                results.append(result["certification"])

        return {
            "created": results,
            "errors": errors,
            "total_created": len(results),
            "total_errors": len(errors),
        }
