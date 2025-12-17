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
from app.services.conflict_auto_detector import ConflictAutoDetector, ConflictInfo
from app.services.faculty_preference_service import FacultyPreferenceService
from app.services.conflict_alert_service import ConflictAlertService
from app.services.swap_notification_service import SwapNotificationService
from app.services.fmit_scheduler_service import FMITSchedulerService
from app.services.swap_request_service import SwapRequestService

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
    # Conflict detection
    "ConflictAutoDetector",
    "ConflictInfo",
    # Phase 4 services
    "FacultyPreferenceService",
    "ConflictAlertService",
    "SwapNotificationService",
    # Phase 5 services
    "FMITSchedulerService",
    "SwapRequestService",
]
