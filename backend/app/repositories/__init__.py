"""Repository layer for database operations.

Repositories handle pure database CRUD operations and queries.
They abstract away SQLAlchemy specifics from the service layer.
"""

from app.repositories.base import BaseRepository
from app.repositories.assignment import AssignmentRepository
from app.repositories.person import PersonRepository
from app.repositories.block import BlockRepository
from app.repositories.absence import AbsenceRepository
from app.repositories.user import UserRepository
from app.repositories.procedure import ProcedureRepository
from app.repositories.procedure_credential import ProcedureCredentialRepository
from app.repositories.certification import CertificationTypeRepository, PersonCertificationRepository

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
]
