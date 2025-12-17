"""Service layer for business logic.

Services use repositories as building blocks to implement
business rules and complex operations.
"""

from app.services.absence_service import AbsenceService
from app.services.assignment_service import AssignmentService
from app.services.auth_service import AuthService
from app.services.block_service import BlockService
from app.services.conflict_alert_service import ConflictAlertService
from app.services.conflict_auto_detector import ConflictAutoDetector, ConflictInfo
from app.services.faculty_preference_service import FacultyPreferenceService
from app.services.fmit_scheduler_service import FMITSchedulerService
from app.services.leave_providers import (
    CSVLeaveProvider,
    DatabaseLeaveProvider,
    LeaveProvider,
    LeaveProviderFactory,
    LeaveRecord,
)
from app.services.person_service import PersonService
from app.services.role_filter_service import RoleFilterService, UserRole, ResourceType
from app.services.swap_executor import ExecutionResult, RollbackResult, SwapExecutor
from app.services.swap_notification_service import SwapNotificationService
from app.services.swap_request_service import SwapRequestService
from app.services.swap_validation import SwapValidationResult, SwapValidationService

__all__ = [
    "AssignmentService",
    "PersonService",
    "BlockService",
    "AbsenceService",
    "AuthService",
    # Role-based filtering
    "RoleFilterService",
    "UserRole",
    "ResourceType",
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
