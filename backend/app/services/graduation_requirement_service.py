import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.graduation_requirement import GraduationRequirement
from app.schemas.graduation_requirement import (
    GraduationRequirementCreate,
    GraduationRequirementUpdate,
)


class GraduationRequirementService:
    @staticmethod
    def get_by_pgy(db: Session, pgy_level: int) -> list[GraduationRequirement]:
        """Get all graduation requirements for a specific PGY level."""
        return (
            db.query(GraduationRequirement)
            .filter(GraduationRequirement.pgy_level == pgy_level)
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, req_id: uuid.UUID) -> GraduationRequirement | None:
        """Get a single graduation requirement by ID."""
        return (
            db.query(GraduationRequirement)
            .filter(GraduationRequirement.id == req_id)
            .first()
        )

    @staticmethod
    def get_by_pgy_and_template(
        db: Session, pgy_level: int, rotation_template_id: uuid.UUID
    ) -> GraduationRequirement | None:
        """Get a specific requirement by PGY level and template."""
        return (
            db.query(GraduationRequirement)
            .filter(
                GraduationRequirement.pgy_level == pgy_level,
                GraduationRequirement.rotation_template_id == rotation_template_id,
            )
            .first()
        )

    @staticmethod
    def create(
        db: Session, obj_in: GraduationRequirementCreate
    ) -> GraduationRequirement:
        """Create a new graduation requirement."""
        db_obj = GraduationRequirement(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def update(
        db: Session, db_obj: GraduationRequirement, obj_in: GraduationRequirementUpdate
    ) -> GraduationRequirement:
        """Update an existing graduation requirement."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete(db: Session, db_obj: GraduationRequirement) -> None:
        """Delete a graduation requirement."""
        db.delete(db_obj)
        db.commit()


graduation_requirement_service = GraduationRequirementService()
