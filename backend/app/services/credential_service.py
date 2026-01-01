"""Credential service for business logic."""

from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.procedure_credential import ProcedureCredential
from app.repositories.person import PersonRepository
from app.repositories.procedure import ProcedureRepository
from app.repositories.procedure_credential import ProcedureCredentialRepository


class CredentialService:
    """Service for procedure credential business logic."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.credential_repo = ProcedureCredentialRepository(db)
        self.procedure_repo = ProcedureRepository(db)
        self.person_repo = PersonRepository(db)

    def get_credential(self, credential_id: UUID) -> ProcedureCredential | None:
        """Get a single credential by ID."""
        return self.credential_repo.get_by_id(credential_id)

    def get_credential_for_person_procedure(
        self,
        person_id: UUID,
        procedure_id: UUID,
    ) -> ProcedureCredential | None:
        """Get a credential for a specific person and procedure."""
        return self.credential_repo.get_by_person_and_procedure(person_id, procedure_id)

    def list_credentials_for_person(
        self,
        person_id: UUID,
        status: str | None = None,
        include_expired: bool = False,
    ) -> dict:
        """List all credentials for a person."""
        credentials = self.credential_repo.list_by_person(
            person_id=person_id,
            status=status,
            include_expired=include_expired,
        )
        return {"items": credentials, "total": len(credentials)}

    def list_credentials_for_procedure(
        self,
        procedure_id: UUID,
        status: str | None = None,
        include_expired: bool = False,
    ) -> dict:
        """List all credentials for a procedure (who can supervise it)."""
        credentials = self.credential_repo.list_by_procedure(
            procedure_id=procedure_id,
            status=status,
            include_expired=include_expired,
        )
        return {"items": credentials, "total": len(credentials)}

    def list_qualified_faculty_for_procedure(
        self,
        procedure_id: UUID,
    ) -> dict:
        """Get all faculty qualified to supervise a procedure."""
        procedure = self.procedure_repo.get_by_id(procedure_id)
        if not procedure:
            return {
                "procedure_id": procedure_id,
                "procedure_name": None,
                "qualified_faculty": [],
                "total": 0,
                "error": "Procedure not found",
            }

        faculty = self.credential_repo.list_qualified_faculty_for_procedure(
            procedure_id
        )
        return {
            "procedure_id": procedure_id,
            "procedure_name": procedure.name,
            "qualified_faculty": faculty,
            "total": len(faculty),
            "error": None,
        }

    def list_procedures_for_faculty(
        self,
        person_id: UUID,
    ) -> dict:
        """Get all procedures a faculty member can supervise."""
        person = self.person_repo.get_by_id(person_id)
        if not person:
            return {"items": [], "total": 0, "error": "Person not found"}

        if person.type != "faculty":
            return {"items": [], "total": 0, "error": "Person is not faculty"}

        procedures = self.credential_repo.list_procedures_for_faculty(person_id)
        return {"items": procedures, "total": len(procedures), "error": None}

    def is_faculty_qualified(
        self,
        person_id: UUID,
        procedure_id: UUID,
    ) -> dict:
        """Check if a faculty member is qualified for a procedure."""
        is_qualified = self.credential_repo.is_faculty_qualified_for_procedure(
            person_id, procedure_id
        )
        return {"is_qualified": is_qualified}

    def create_credential(
        self,
        person_id: UUID,
        procedure_id: UUID,
        status: str = "active",
        competency_level: str = "qualified",
        issued_date: date | None = None,
        expiration_date: date | None = None,
        last_verified_date: date | None = None,
        max_concurrent_residents: int | None = None,
        max_per_week: int | None = None,
        max_per_academic_year: int | None = None,
        notes: str | None = None,
    ) -> dict:
        """
        Create a new credential for a faculty member.

        Returns dict with:
        - credential: The created credential
        - error: Error message if creation failed
        """
        # Validate person exists and is faculty
        person = self.person_repo.get_by_id(person_id)
        if not person:
            return {"credential": None, "error": "Person not found"}
        if person.type != "faculty":
            return {
                "credential": None,
                "error": "Only faculty can have procedure credentials",
            }

        # Validate procedure exists
        procedure = self.procedure_repo.get_by_id(procedure_id)
        if not procedure:
            return {"credential": None, "error": "Procedure not found"}

        # Check for existing credential
        existing = self.credential_repo.get_by_person_and_procedure(
            person_id, procedure_id
        )
        if existing:
            return {
                "credential": None,
                "error": f"Credential already exists for {person.name} and {procedure.name}",
            }

        credential_data = {
            "person_id": person_id,
            "procedure_id": procedure_id,
            "status": status,
            "competency_level": competency_level,
            "issued_date": issued_date or date.today(),
            "expiration_date": expiration_date,
            "last_verified_date": last_verified_date,
            "max_concurrent_residents": max_concurrent_residents,
            "max_per_week": max_per_week,
            "max_per_academic_year": max_per_academic_year,
            "notes": notes,
        }

        credential = self.credential_repo.create(credential_data)
        self.credential_repo.commit()
        self.credential_repo.refresh(credential)

        return {"credential": credential, "error": None}

    def update_credential(self, credential_id: UUID, update_data: dict) -> dict:
        """
        Update a credential.

        Returns dict with:
        - credential: The updated credential
        - error: Error message if update failed
        """
        credential = self.credential_repo.get_by_id(credential_id)
        if not credential:
            return {"credential": None, "error": "Credential not found"}

        credential = self.credential_repo.update(credential, update_data)
        self.credential_repo.commit()
        self.credential_repo.refresh(credential)

        return {"credential": credential, "error": None}

    def delete_credential(self, credential_id: UUID) -> dict:
        """Delete a credential."""
        credential = self.credential_repo.get_by_id(credential_id)
        if not credential:
            return {"success": False, "error": "Credential not found"}

        self.credential_repo.delete(credential)
        self.credential_repo.commit()
        return {"success": True, "error": None}

    def suspend_credential(self, credential_id: UUID, notes: str | None = None) -> dict:
        """Suspend a credential."""
        update_data = {"status": "suspended"}
        if notes:
            update_data["notes"] = notes
        return self.update_credential(credential_id, update_data)

    def activate_credential(self, credential_id: UUID) -> dict:
        """Activate a credential."""
        return self.update_credential(credential_id, {"status": "active"})

    def verify_credential(self, credential_id: UUID) -> dict:
        """Mark a credential as verified today."""
        return self.update_credential(
            credential_id, {"last_verified_date": date.today()}
        )

    def list_expiring_credentials(self, days: int = 30) -> dict:
        """List credentials expiring soon."""
        credentials = self.credential_repo.list_expiring_soon(days=days)
        return {"items": credentials, "total": len(credentials)}

    def get_faculty_credential_summary(self, person_id: UUID) -> dict:
        """Get a summary of a faculty member's credentials."""
        person = self.person_repo.get_by_id(person_id)
        if not person:
            return {"error": "Person not found"}

        if person.type != "faculty":
            return {"error": "Person is not faculty"}

        # Get all credentials for this person
        all_credentials = self.credential_repo.list_by_person(
            person_id=person_id,
            include_expired=True,
        )

        # Count active credentials
        active_count = sum(1 for c in all_credentials if c.is_valid)

        # Count expiring soon (within 30 days)
        from datetime import timedelta

        today = date.today()
        expiring_soon = sum(
            1
            for c in all_credentials
            if c.is_valid
            and c.expiration_date
            and c.expiration_date <= today + timedelta(days=30)
        )

        # Get procedures for active credentials
        procedures = self.credential_repo.list_procedures_for_faculty(person_id)

        return {
            "person_id": person_id,
            "person_name": person.name,
            "total_credentials": len(all_credentials),
            "active_credentials": active_count,
            "expiring_soon": expiring_soon,
            "procedures": procedures,
            "error": None,
        }

    def bulk_create_credentials(
        self,
        person_id: UUID,
        procedure_ids: list[UUID],
        **credential_defaults,
    ) -> dict:
        """Create credentials for multiple procedures at once."""
        results = []
        errors = []

        for procedure_id in procedure_ids:
            result = self.create_credential(
                person_id=person_id,
                procedure_id=procedure_id,
                **credential_defaults,
            )
            if result["error"]:
                errors.append({"procedure_id": procedure_id, "error": result["error"]})
            else:
                results.append(result["credential"])

        return {
            "created": results,
            "errors": errors,
            "total_created": len(results),
            "total_errors": len(errors),
        }
