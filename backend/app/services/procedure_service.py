"""Procedure service for business logic."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.repositories.procedure import ProcedureRepository
from app.models.procedure import Procedure


class ProcedureService:
    """Service for procedure business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.procedure_repo = ProcedureRepository(db)

    def get_procedure(self, procedure_id: UUID) -> Optional[Procedure]:
        """Get a single procedure by ID."""
        return self.procedure_repo.get_by_id(procedure_id)

    def get_procedure_by_name(self, name: str) -> Optional[Procedure]:
        """Get a procedure by its name."""
        return self.procedure_repo.get_by_name(name)

    def list_procedures(
        self,
        specialty: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        complexity_level: Optional[str] = None,
    ) -> dict:
        """List procedures with optional filters."""
        procedures = self.procedure_repo.list_with_filters(
            specialty=specialty,
            category=category,
            is_active=is_active,
            complexity_level=complexity_level,
        )
        return {"items": procedures, "total": len(procedures)}

    def list_active_procedures(self) -> dict:
        """List all active procedures."""
        procedures = self.procedure_repo.list_active()
        return {"items": procedures, "total": len(procedures)}

    def list_by_specialty(self, specialty: str) -> dict:
        """List all procedures for a specialty."""
        procedures = self.procedure_repo.list_by_specialty(specialty)
        return {"items": procedures, "total": len(procedures)}

    def get_specialties(self) -> List[str]:
        """Get all unique specialties."""
        return self.procedure_repo.get_unique_specialties()

    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        return self.procedure_repo.get_unique_categories()

    def create_procedure(
        self,
        name: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        specialty: Optional[str] = None,
        supervision_ratio: int = 1,
        requires_certification: bool = True,
        complexity_level: str = 'standard',
        min_pgy_level: int = 1,
        is_active: bool = True,
    ) -> dict:
        """
        Create a new procedure.

        Returns dict with:
        - procedure: The created procedure
        - error: Error message if creation failed
        """
        # Check for duplicate name
        existing = self.procedure_repo.get_by_name(name)
        if existing:
            return {
                "procedure": None,
                "error": f"Procedure with name '{name}' already exists",
            }

        procedure_data = {
            "name": name,
            "description": description,
            "category": category,
            "specialty": specialty,
            "supervision_ratio": supervision_ratio,
            "requires_certification": requires_certification,
            "complexity_level": complexity_level,
            "min_pgy_level": min_pgy_level,
            "is_active": is_active,
        }

        procedure = self.procedure_repo.create(procedure_data)
        self.procedure_repo.commit()
        self.procedure_repo.refresh(procedure)

        return {"procedure": procedure, "error": None}

    def update_procedure(self, procedure_id: UUID, update_data: dict) -> dict:
        """
        Update a procedure's information.

        Returns dict with:
        - procedure: The updated procedure
        - error: Error message if update failed
        """
        procedure = self.procedure_repo.get_by_id(procedure_id)
        if not procedure:
            return {"procedure": None, "error": "Procedure not found"}

        # Check for duplicate name if name is being changed
        if "name" in update_data and update_data["name"] != procedure.name:
            existing = self.procedure_repo.get_by_name(update_data["name"])
            if existing:
                return {
                    "procedure": None,
                    "error": f"Procedure with name '{update_data['name']}' already exists",
                }

        procedure = self.procedure_repo.update(procedure, update_data)
        self.procedure_repo.commit()
        self.procedure_repo.refresh(procedure)

        return {"procedure": procedure, "error": None}

    def delete_procedure(self, procedure_id: UUID) -> dict:
        """Delete a procedure."""
        procedure = self.procedure_repo.get_by_id(procedure_id)
        if not procedure:
            return {"success": False, "error": "Procedure not found"}

        self.procedure_repo.delete(procedure)
        self.procedure_repo.commit()
        return {"success": True, "error": None}

    def deactivate_procedure(self, procedure_id: UUID) -> dict:
        """Deactivate a procedure (soft delete)."""
        return self.update_procedure(procedure_id, {"is_active": False})

    def activate_procedure(self, procedure_id: UUID) -> dict:
        """Activate a procedure."""
        return self.update_procedure(procedure_id, {"is_active": True})
