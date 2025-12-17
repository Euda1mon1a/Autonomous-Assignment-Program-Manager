"""Service layer for business logic.

Services use repositories as building blocks to implement
business rules and complex operations.
"""

from app.services.assignment_service import AssignmentService
from app.services.person_service import PersonService
from app.services.block_service import BlockService
from app.services.absence_service import AbsenceService
from app.services.auth_service import AuthService
from app.services.swap_validation import SwapValidationService, SwapValidationResult
from app.services.swap_executor import SwapExecutor, ExecutionResult, RollbackResult
from app.services.leave_providers import (
    LeaveProvider,
    LeaveRecord,
    DatabaseLeaveProvider,
    CSVLeaveProvider,
    LeaveProviderFactory,
)

__all__ = [
    "AssignmentService",
    "PersonService",
    "BlockService",
    "AbsenceService",
    "AuthService",
    # FMIT Swap services
    "SwapValidationService",
    "SwapValidationResult",
    "SwapExecutor",
    "ExecutionResult",
    "RollbackResult",
    # Leave providers
    "LeaveProvider",
    "LeaveRecord",
    "DatabaseLeaveProvider",
    "CSVLeaveProvider",
    "LeaveProviderFactory",
]
