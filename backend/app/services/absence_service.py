"""Absence service for business logic."""

from datetime import date
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.repositories.absence import AbsenceRepository
from app.models.absence import Absence


class AbsenceService:
    """Service for absence business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.absence_repo = AbsenceRepository(db)

    def get_absence(self, absence_id: UUID) -> Optional[Absence]:
        """Get a single absence by ID."""
        return self.absence_repo.get_by_id(absence_id)

    def list_absences(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        person_id: Optional[UUID] = None,
        absence_type: Optional[str] = None,
    ) -> dict:
        """List absences with optional filters."""
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
        replacement_activity: Optional[str] = None,
        deployment_orders: bool = False,
        tdy_location: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """
        Create a new absence.

        Returns dict with:
        - absence: The created absence
        - error: Error message if creation failed
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
        """
        Update an absence.

        Returns dict with:
        - absence: The updated absence
        - error: Error message if update failed
        """
        absence = self.absence_repo.get_by_id(absence_id)
        if not absence:
            return {"absence": None, "error": "Absence not found"}

        absence = self.absence_repo.update(absence, update_data)
        self.absence_repo.commit()
        self.absence_repo.refresh(absence)

        return {"absence": absence, "error": None}

    def delete_absence(self, absence_id: UUID) -> dict:
        """Delete an absence."""
        absence = self.absence_repo.get_by_id(absence_id)
        if not absence:
            return {"success": False, "error": "Absence not found"}

        self.absence_repo.delete(absence)
        self.absence_repo.commit()
        return {"success": True, "error": None}

    def is_person_absent(self, person_id: UUID, on_date: date) -> bool:
        """Check if a person has an absence on a specific date."""
        return self.absence_repo.has_absence_on_date(person_id, on_date)
