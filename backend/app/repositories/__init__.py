"""Repository layer for database operations.

Repositories handle pure database CRUD operations and queries.
They abstract away SQLAlchemy specifics from the service layer.
"""

from app.repositories.absence import AbsenceRepository
from app.repositories.assignment import AssignmentRepository
from app.repositories.base import BaseRepository
from app.repositories.block import BlockRepository
from app.repositories.certification import (
    CertificationTypeRepository,
    PersonCertificationRepository,
)
from app.repositories.conflict_repository import ConflictRepository
from app.repositories.person import PersonRepository
from app.repositories.procedure import ProcedureRepository
from app.repositories.procedure_credential import ProcedureCredentialRepository
from app.repositories.swap_repository import SwapRepository
from app.repositories.user import UserRepository

__all__ = [
    "BaseRepository",
    "AssignmentRepository",
    "PersonRepository",
    "BlockRepository",
    "AbsenceRepository",
    "UserRepository",
    "ProcedureRepository",
    "ProcedureCredentialRepository",
    "CertificationTypeRepository",
    "PersonCertificationRepository",
    # FMIT repositories
    "SwapRepository",
    "ConflictRepository",
]
