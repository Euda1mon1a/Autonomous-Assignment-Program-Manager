"""Absence service for business logic."""

from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.repositories.absence import AbsenceRepository


class AbsenceService:
    """Service for absence business logic."""

    def __init__(self, db: Session):
        """Initialize absence service.

        Args:
            db: Database session for absence operations.
        """
        self.db = db
        self.absence_repo = AbsenceRepository(db)

    def get_absence(self, absence_id: UUID) -> Absence | None:
        """Get a single absence by ID.

        Args:
            absence_id: UUID of the absence record.

        Returns:
            Absence object if found, None otherwise.
        """
        return self.absence_repo.get_by_id(absence_id)

    def list_absences(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        person_id: UUID | None = None,
        absence_type: str | None = None,
    ) -> dict:
        """List absences with optional filters.

        Args:
            start_date: Filter absences starting on or after this date.
            end_date: Filter absences ending on or before this date.
            person_id: Filter absences for a specific person.
            absence_type: Filter by absence type (e.g., 'TDY', 'Leave', 'Deployment').

        Returns:
            Dictionary with 'items' (list of Absence objects) and 'total' (count).
        """
        absences = self.absence_repo.list_with_filters(
            start_date=start_date,
            end_date=end_date,
            person_id=person_id,
            absence_type=absence_type,
        )
        return {"items": absences, "total": len(absences)}

    def create_absence(
        self,
        person_id: UUID,
        start_date: date,
        end_date: date,
        absence_type: str,
        replacement_activity: str | None = None,
        deployment_orders: bool = False,
        tdy_location: str | None = None,
        notes: str | None = None,
    ) -> dict:
        """Create a new absence record for leave, TDY, or deployment.

        Args:
            person_id: UUID of the person with the absence.
            start_date: First date of the absence.
            end_date: Last date of the absence (inclusive).
            absence_type: Type of absence ('Leave', 'TDY', 'Deployment', etc.).
            replacement_activity: Activity scheduled during absence (optional).
            deployment_orders: Whether this is a deployment with official orders.
            tdy_location: Location for TDY assignments (optional).
            notes: Additional notes about the absence.

        Returns:
            Dictionary with 'absence' (created Absence object) and 'error' (None if successful).
        """
        absence_data = {
            "person_id": person_id,
            "start_date": start_date,
            "end_date": end_date,
            "absence_type": absence_type,
        }
        if replacement_activity:
            absence_data["replacement_activity"] = replacement_activity
        if deployment_orders:
            absence_data["deployment_orders"] = deployment_orders
        if tdy_location:
            absence_data["tdy_location"] = tdy_location
        if notes:
            absence_data["notes"] = notes

        absence = self.absence_repo.create(absence_data)
        self.absence_repo.commit()
        self.absence_repo.refresh(absence)

        return {"absence": absence, "error": None}

    def update_absence(self, absence_id: UUID, update_data: dict) -> dict:
        """Update an existing absence record.

        Args:
            absence_id: UUID of the absence to update.
            update_data: Dictionary of fields to update.

        Returns:
            Dictionary with 'absence' (updated Absence object) and 'error' (None if successful,
            error message if absence not found).
        """
        absence = self.absence_repo.get_by_id(absence_id)
        if not absence:
            return {"absence": None, "error": "Absence not found"}

        absence = self.absence_repo.update(absence, update_data)
        self.absence_repo.commit()
        self.absence_repo.refresh(absence)

        return {"absence": absence, "error": None}

    def delete_absence(self, absence_id: UUID) -> dict:
        """Delete an absence record.

        Args:
            absence_id: UUID of the absence to delete.

        Returns:
            Dictionary with 'success' (bool) and 'error' (None if successful,
            error message if absence not found).
        """
        absence = self.absence_repo.get_by_id(absence_id)
        if not absence:
            return {"success": False, "error": "Absence not found"}

        self.absence_repo.delete(absence)
        self.absence_repo.commit()
        return {"success": True, "error": None}

    def is_person_absent(self, person_id: UUID, on_date: date) -> bool:
        """Check if a person has a blocking absence on a specific date.

        Args:
            person_id: UUID of the person to check.
            on_date: Date to check for absences.

        Returns:
            True if person has an absence covering this date, False otherwise.
        """
        return self.absence_repo.has_absence_on_date(person_id, on_date)
