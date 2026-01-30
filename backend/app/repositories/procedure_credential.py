"""ProcedureCredential repository for database operations."""

from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.person import Person
from app.models.procedure import Procedure
from app.models.procedure_credential import ProcedureCredential
from app.repositories.base import BaseRepository


class ProcedureCredentialRepository(BaseRepository[ProcedureCredential]):
    """Repository for ProcedureCredential entity operations."""

    def __init__(self, db: Session) -> None:
        super().__init__(ProcedureCredential, db)

    def get_by_person_and_procedure(
        self,
        person_id: UUID,
        procedure_id: UUID,
    ) -> ProcedureCredential | None:
        """Get a credential by person and procedure IDs."""
        return (
            self.db.query(ProcedureCredential)
            .filter(
                ProcedureCredential.person_id == person_id,
                ProcedureCredential.procedure_id == procedure_id,
            )
            .first()
        )

    def list_by_person(
        self,
        person_id: UUID,
        status: str | None = None,
        include_expired: bool = False,
    ) -> list[ProcedureCredential]:
        """
        List all credentials for a person.

        Args:
            person_id: The person's ID
            status: Optional status filter ('active', 'expired', 'suspended', 'pending')
            include_expired: If True, include expired credentials
        """
        query = (
            self.db.query(ProcedureCredential)
            .options(joinedload(ProcedureCredential.procedure))
            .filter(ProcedureCredential.person_id == person_id)
        )

        if status:
            query = query.filter(ProcedureCredential.status == status)

        if not include_expired:
            query = query.filter(
                (ProcedureCredential.expiration_date.is_(None))
                | (ProcedureCredential.expiration_date >= date.today())
            )

        return query.all()

    def list_by_procedure(
        self,
        procedure_id: UUID,
        status: str | None = None,
        include_expired: bool = False,
    ) -> list[ProcedureCredential]:
        """
        List all credentials for a procedure (who can supervise it).

        Args:
            procedure_id: The procedure's ID
            status: Optional status filter
            include_expired: If True, include expired credentials
        """
        query = (
            self.db.query(ProcedureCredential)
            .options(joinedload(ProcedureCredential.person))
            .filter(ProcedureCredential.procedure_id == procedure_id)
        )

        if status:
            query = query.filter(ProcedureCredential.status == status)

        if not include_expired:
            query = query.filter(
                (ProcedureCredential.expiration_date.is_(None))
                | (ProcedureCredential.expiration_date >= date.today())
            )

        return query.all()

    def list_active_credentials_for_person(
        self,
        person_id: UUID,
    ) -> list[ProcedureCredential]:
        """List all active, non-expired credentials for a person."""
        return (
            self.db.query(ProcedureCredential)
            .options(joinedload(ProcedureCredential.procedure))
            .filter(
                ProcedureCredential.person_id == person_id,
                ProcedureCredential.status == "active",
            )
            .filter(
                (ProcedureCredential.expiration_date.is_(None))
                | (ProcedureCredential.expiration_date >= date.today())
            )
            .all()
        )

    def list_qualified_faculty_for_procedure(
        self,
        procedure_id: UUID,
    ) -> list[Person]:
        """
        Get all faculty members qualified to supervise a specific procedure.

        Returns list of Person objects with active, non-expired credentials.
        """
        return (
            self.db.query(Person)
            .join(ProcedureCredential)
            .filter(
                ProcedureCredential.procedure_id == procedure_id,
                ProcedureCredential.status == "active",
                Person.type == "faculty",
            )
            .filter(
                (ProcedureCredential.expiration_date.is_(None))
                | (ProcedureCredential.expiration_date >= date.today())
            )
            .all()
        )

    def list_procedures_for_faculty(
        self,
        person_id: UUID,
    ) -> list[Procedure]:
        """
        Get all procedures a faculty member is qualified to supervise.

        Returns list of Procedure objects for active, non-expired credentials.
        """
        return (
            self.db.query(Procedure)
            .join(ProcedureCredential)
            .filter(
                ProcedureCredential.person_id == person_id,
                ProcedureCredential.status == "active",
            )
            .filter(
                (ProcedureCredential.expiration_date.is_(None))
                | (ProcedureCredential.expiration_date >= date.today())
            )
            .all()
        )

    def is_faculty_qualified_for_procedure(
        self,
        person_id: UUID,
        procedure_id: UUID,
    ) -> bool:
        """Check if a faculty member has an active credential for a procedure."""
        credential = self.get_by_person_and_procedure(person_id, procedure_id)
        if not credential:
            return False
        return credential.is_valid

    def list_expiring_soon(
        self,
        days: int = 30,
    ) -> list[ProcedureCredential]:
        """List credentials expiring within the specified number of days."""
        target_date = date.today()
        end_date = date(
            target_date.year,
            target_date.month,
            target_date.day,
        )
        from datetime import timedelta

        end_date = target_date + timedelta(days=days)

        return (
            self.db.query(ProcedureCredential)
            .options(
                joinedload(ProcedureCredential.person),
                joinedload(ProcedureCredential.procedure),
            )
            .filter(
                ProcedureCredential.status == "active",
                ProcedureCredential.expiration_date.isnot(None),
                ProcedureCredential.expiration_date >= target_date,
                ProcedureCredential.expiration_date <= end_date,
            )
            .order_by(ProcedureCredential.expiration_date)
            .all()
        )

    def count_qualified_faculty_for_procedure(
        self,
        procedure_id: UUID,
    ) -> int:
        """Count how many faculty are qualified for a procedure."""
        return (
            self.db.query(ProcedureCredential)
            .filter(
                ProcedureCredential.procedure_id == procedure_id,
                ProcedureCredential.status == "active",
            )
            .filter(
                (ProcedureCredential.expiration_date.is_(None))
                | (ProcedureCredential.expiration_date >= date.today())
            )
            .count()
        )
