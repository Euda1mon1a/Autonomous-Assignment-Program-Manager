"""Base repository with common CRUD operations."""

from typing import Generic, TypeVar, Type, Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository providing common CRUD operations.

    All entity-specific repositories inherit from this class
    and can override or extend these methods as needed.
    """

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """Get a single entity by ID."""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self) -> List[ModelType]:
        """Get all entities."""
        return self.db.query(self.model).all()

    def create(self, obj_in: dict) -> ModelType:
        """Create a new entity from a dictionary."""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.flush()  # Get ID without committing
        return db_obj

    def update(self, db_obj: ModelType, obj_in: dict) -> ModelType:
        """Update an existing entity with new values."""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        self.db.flush()
        return db_obj

    def delete(self, db_obj: ModelType) -> None:
        """Delete an entity."""
        self.db.delete(db_obj)
        self.db.flush()

    def commit(self) -> None:
        """Commit the current transaction."""
        self.db.commit()

    def refresh(self, db_obj: ModelType) -> ModelType:
        """Refresh an entity from the database."""
        self.db.refresh(db_obj)
        return db_obj

    def count(self) -> int:
        """Count all entities."""
        return self.db.query(self.model).count()
