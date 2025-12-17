"""Person service for business logic."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.person import Person
from app.repositories.person import PersonRepository


class PersonService:
    """Service for person business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.person_repo = PersonRepository(db)

    def get_person(self, person_id: UUID) -> Person | None:
        """Get a single person by ID."""
        return self.person_repo.get_by_id(person_id)

    def list_people(
        self,
        type: str | None = None,
        pgy_level: int | None = None,
    ) -> dict:
        """List people with optional filters."""
        people = self.person_repo.list_with_filters(type=type, pgy_level=pgy_level)
        return {"items": people, "total": len(people)}

    def list_residents(self, pgy_level: int | None = None) -> dict:
        """List all residents with optional PGY filter."""
        residents = self.person_repo.list_residents(pgy_level=pgy_level)
        return {"items": residents, "total": len(residents)}

    def list_faculty(self, specialty: str | None = None) -> dict:
        """List all faculty with optional specialty filter."""
        faculty = self.person_repo.list_faculty(specialty=specialty)
        return {"items": faculty, "total": len(faculty)}

    def create_person(
        self,
        name: str,
        type: str,
        email: str | None = None,
        pgy_level: int | None = None,
        target_clinical_blocks: int | None = None,
        specialties: list[str] | None = None,
        performs_procedures: bool = False,
    ) -> dict:
        """
        Create a new person (resident or faculty).

        Returns dict with:
        - person: The created person
        - error: Error message if creation failed
        """
        # Validate resident requirements
        if type == "resident" and pgy_level is None:
            return {
                "person": None,
                "error": "PGY level required for residents",
            }

        person_data = {
            "name": name,
            "type": type,
        }
        if email:
            person_data["email"] = email
        if pgy_level is not None:
            person_data["pgy_level"] = pgy_level
        if target_clinical_blocks is not None:
            person_data["target_clinical_blocks"] = target_clinical_blocks
        if specialties:
            person_data["specialties"] = specialties
        if performs_procedures:
            person_data["performs_procedures"] = performs_procedures

        person = self.person_repo.create(person_data)
        self.person_repo.commit()
        self.person_repo.refresh(person)

        return {"person": person, "error": None}

    def update_person(self, person_id: UUID, update_data: dict) -> dict:
        """
        Update a person's information.

        Returns dict with:
        - person: The updated person
        - error: Error message if update failed
        """
        person = self.person_repo.get_by_id(person_id)
        if not person:
            return {"person": None, "error": "Person not found"}

        person = self.person_repo.update(person, update_data)
        self.person_repo.commit()
        self.person_repo.refresh(person)

        return {"person": person, "error": None}

    def delete_person(self, person_id: UUID) -> dict:
        """Delete a person."""
        person = self.person_repo.get_by_id(person_id)
        if not person:
            return {"success": False, "error": "Person not found"}

        self.person_repo.delete(person)
        self.person_repo.commit()
        return {"success": True, "error": None}
