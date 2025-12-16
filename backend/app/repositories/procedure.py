"""Procedure repository for database operations."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.repositories.base import BaseRepository
from app.models.procedure import Procedure


class ProcedureRepository(BaseRepository[Procedure]):
    """Repository for Procedure entity operations."""

    def __init__(self, db: Session):
        super().__init__(Procedure, db)

    def get_by_name(self, name: str) -> Optional[Procedure]:
        """Get a procedure by its name."""
        return (
            self.db.query(Procedure)
            .filter(Procedure.name == name)
            .first()
        )

    def list_with_filters(
        self,
        specialty: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        complexity_level: Optional[str] = None,
    ) -> List[Procedure]:
        """List procedures with optional filters, ordered by name."""
        query = self.db.query(Procedure)

        if specialty:
            query = query.filter(Procedure.specialty == specialty)
        if category:
            query = query.filter(Procedure.category == category)
        if is_active is not None:
            query = query.filter(Procedure.is_active == is_active)
        if complexity_level:
            query = query.filter(Procedure.complexity_level == complexity_level)

        return query.order_by(Procedure.name).all()

    def list_active(self) -> List[Procedure]:
        """List all active procedures."""
        return (
            self.db.query(Procedure)
            .filter(Procedure.is_active == True)
            .order_by(Procedure.name)
            .all()
        )

    def list_by_specialty(self, specialty: str) -> List[Procedure]:
        """List all procedures for a given specialty."""
        return (
            self.db.query(Procedure)
            .filter(Procedure.specialty == specialty)
            .filter(Procedure.is_active == True)
            .order_by(Procedure.name)
            .all()
        )

    def list_by_category(self, category: str) -> List[Procedure]:
        """List all procedures in a given category."""
        return (
            self.db.query(Procedure)
            .filter(Procedure.category == category)
            .filter(Procedure.is_active == True)
            .order_by(Procedure.name)
            .all()
        )

    def get_unique_specialties(self) -> List[str]:
        """Get all unique specialties from procedures."""
        results = (
            self.db.query(Procedure.specialty)
            .filter(Procedure.specialty.isnot(None))
            .filter(Procedure.is_active == True)
            .distinct()
            .all()
        )
        return [r[0] for r in results if r[0]]

    def get_unique_categories(self) -> List[str]:
        """Get all unique categories from procedures."""
        results = (
            self.db.query(Procedure.category)
            .filter(Procedure.category.isnot(None))
            .filter(Procedure.is_active == True)
            .distinct()
            .all()
        )
        return [r[0] for r in results if r[0]]
