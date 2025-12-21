"""
Freeze Horizon Service - Enforces schedule stability within a configurable time window.

This service provides a "change barrier" that prevents modifications to assignments
that are within N days of their scheduled date, unless an override is provided.

Design Philosophy (per ChatGPT Oracle consultation):
- Enforcement at SERVICE layer, not controller, so it applies to:
  - UI edits
  - Bulk regeneration
  - Resiliency repairs
  - Background tasks

- Converts "stability metrics" into "stability guarantees"
- Preserves deep optimization early, prevents late thrash
- Aligns with real-world cadence: proactive changes should happen beyond freeze horizon

Usage:
    from app.services.freeze_horizon_service import FreezeHorizonService

    service = FreezeHorizonService(db)

    # Check if an assignment is frozen
    result = service.check_freeze_status(assignment)
    if result.is_frozen:
        if not override_provided:
            raise FreezeHorizonViolation(result)

    # Validate and log an override
    service.validate_and_log_override(
        assignment=assignment,
        reason_code=OverrideReasonCode.SICK_CALL,
        reason_text="Dr. Smith called in sick",
        initiated_by="scheduler_system",
        initiating_module="resiliency_repair",
    )
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.settings import ApplicationSettings, FreezeScope, OverrideReasonCode

if TYPE_CHECKING:
    from app.models.assignment import Assignment
    from app.models.block import Block

logger = get_logger(__name__)


class FreezeCheckResult:
    """Result of checking freeze status for an assignment."""

    def __init__(
        self,
        is_frozen: bool,
        assignment_date: date | None,
        days_until_assignment: int | None,
        freeze_horizon_days: int,
        freeze_scope: FreezeScope,
        requires_override: bool,
        can_use_emergency_bypass: bool,
        message: str,
    ):
        self.is_frozen = is_frozen
        self.assignment_date = assignment_date
        self.days_until_assignment = days_until_assignment
        self.freeze_horizon_days = freeze_horizon_days
        self.freeze_scope = freeze_scope
        self.requires_override = requires_override
        self.can_use_emergency_bypass = can_use_emergency_bypass
        self.message = message

    def to_dict(self) -> dict:
        return {
            "is_frozen": self.is_frozen,
            "assignment_date": self.assignment_date.isoformat() if self.assignment_date else None,
            "days_until_assignment": self.days_until_assignment,
            "freeze_horizon_days": self.freeze_horizon_days,
            "freeze_scope": self.freeze_scope.value if isinstance(self.freeze_scope, FreezeScope) else self.freeze_scope,
            "requires_override": self.requires_override,
            "can_use_emergency_bypass": self.can_use_emergency_bypass,
            "message": self.message,
        }


@dataclass
class FreezeOverrideRequest:
    """Request to override a freeze horizon violation."""
    reason_code: OverrideReasonCode
    reason_text: str  # Required even for structured codes (additional context)
    initiated_by: str  # User ID or system identifier
    initiating_module: str  # "manual", "planning", "resiliency", "crisis"
    is_emergency: bool = False


@dataclass
class FreezeOverrideAuditRecord:
    """Audit record for a freeze horizon override."""
    id: UUID
    timestamp: datetime
    assignment_id: UUID
    block_id: UUID
    block_date: date
    days_until_assignment: int
    reason_code: OverrideReasonCode
    reason_text: str
    initiated_by: str
    initiating_module: str
    is_emergency: bool
    freeze_scope_at_time: FreezeScope
    freeze_horizon_at_time: int


class FreezeHorizonViolation(Exception):
    """Raised when an assignment modification violates freeze horizon."""

    def __init__(self, check_result: FreezeCheckResult):
        self.check_result = check_result
        super().__init__(check_result.message)


class FreezeHorizonService:
    """
    Service for enforcing freeze horizon policy on assignment changes.

    The freeze horizon is a stability guarantee that prevents modifications
    to assignments that are too close to their scheduled date.

    This service should be called by ALL code paths that modify assignments:
    - AssignmentService.create_assignment()
    - AssignmentService.update_assignment()
    - AssignmentService.delete_assignment()
    - Bulk regeneration
    - Resiliency repairs
    - Crisis mode operations
    """

    # Emergency reason codes that can bypass non-emergency freeze scope
    EMERGENCY_REASON_CODES = {
        OverrideReasonCode.SICK_CALL,
        OverrideReasonCode.DEPLOYMENT,
        OverrideReasonCode.SAFETY,
        OverrideReasonCode.COVERAGE_GAP,
        OverrideReasonCode.EMERGENCY_LEAVE,
        OverrideReasonCode.CRISIS_MODE,
    }

    def __init__(self, db: Session):
        self.db = db
        self._settings_cache: ApplicationSettings | None = None
        self._override_records: list[FreezeOverrideAuditRecord] = []

    def get_settings(self) -> ApplicationSettings:
        """Get application settings (cached for performance)."""
        if self._settings_cache is None:
            self._settings_cache = self.db.query(ApplicationSettings).first()
            if self._settings_cache is None:
                # Create default settings if none exist
                self._settings_cache = ApplicationSettings()
                self.db.add(self._settings_cache)
                self.db.commit()
        return self._settings_cache

    def clear_settings_cache(self) -> None:
        """Clear settings cache (call when settings are updated)."""
        self._settings_cache = None

    def check_freeze_status(
        self,
        block_date: date,
        reference_date: date | None = None,
    ) -> FreezeCheckResult:
        """
        Check if a date is within the freeze horizon.

        Args:
            block_date: The date of the assignment/block
            reference_date: Date to check from (defaults to today)

        Returns:
            FreezeCheckResult with freeze status and policy details
        """
        settings = self.get_settings()
        freeze_horizon_days = settings.freeze_horizon_days
        freeze_scope_str = settings.freeze_scope

        # Parse freeze scope
        try:
            freeze_scope = FreezeScope(freeze_scope_str)
        except ValueError:
            freeze_scope = FreezeScope.NON_EMERGENCY_ONLY

        # Handle disabled freeze horizon
        if freeze_scope == FreezeScope.NONE or freeze_horizon_days == 0:
            return FreezeCheckResult(
                is_frozen=False,
                assignment_date=block_date,
                days_until_assignment=None,
                freeze_horizon_days=freeze_horizon_days,
                freeze_scope=freeze_scope,
                requires_override=False,
                can_use_emergency_bypass=False,
                message="Freeze horizon is disabled",
            )

        # Calculate days until assignment
        if reference_date is None:
            reference_date = date.today()

        days_until = (block_date - reference_date).days

        # Check if within freeze horizon
        is_frozen = days_until <= freeze_horizon_days

        if not is_frozen:
            return FreezeCheckResult(
                is_frozen=False,
                assignment_date=block_date,
                days_until_assignment=days_until,
                freeze_horizon_days=freeze_horizon_days,
                freeze_scope=freeze_scope,
                requires_override=False,
                can_use_emergency_bypass=False,
                message=f"Assignment is {days_until} days out (beyond {freeze_horizon_days}-day freeze horizon)",
            )

        # Assignment is frozen
        can_use_emergency_bypass = freeze_scope == FreezeScope.NON_EMERGENCY_ONLY
        requires_override = True

        if days_until < 0:
            message = f"Assignment date has passed ({abs(days_until)} days ago). Change requires override."
        elif days_until == 0:
            message = f"Assignment is TODAY. Change requires override."
        else:
            message = f"Assignment is in {days_until} days (within {freeze_horizon_days}-day freeze horizon). Change requires override."

        return FreezeCheckResult(
            is_frozen=True,
            assignment_date=block_date,
            days_until_assignment=days_until,
            freeze_horizon_days=freeze_horizon_days,
            freeze_scope=freeze_scope,
            requires_override=requires_override,
            can_use_emergency_bypass=can_use_emergency_bypass,
            message=message,
        )

    def check_assignment_freeze_status(
        self,
        assignment: "Assignment",
        reference_date: date | None = None,
    ) -> FreezeCheckResult:
        """
        Check freeze status for a specific assignment.

        Args:
            assignment: The assignment to check
            reference_date: Date to check from (defaults to today)

        Returns:
            FreezeCheckResult with freeze status
        """
        # Get block date
        from app.models.block import Block
        block = self.db.query(Block).filter(Block.id == assignment.block_id).first()

        if not block:
            return FreezeCheckResult(
                is_frozen=False,
                assignment_date=None,
                days_until_assignment=None,
                freeze_horizon_days=self.get_settings().freeze_horizon_days,
                freeze_scope=FreezeScope(self.get_settings().freeze_scope),
                requires_override=False,
                can_use_emergency_bypass=False,
                message="Block not found - cannot determine freeze status",
            )

        return self.check_freeze_status(block.date, reference_date)

    def validate_override(
        self,
        freeze_result: FreezeCheckResult,
        override_request: FreezeOverrideRequest,
    ) -> tuple[bool, str]:
        """
        Validate that an override request is acceptable.

        Args:
            freeze_result: The freeze check result
            override_request: The override request

        Returns:
            Tuple of (is_valid, message)
        """
        if not freeze_result.is_frozen:
            return True, "No override needed - assignment is not frozen"

        # Check if emergency bypass is allowed
        if freeze_result.freeze_scope == FreezeScope.NON_EMERGENCY_ONLY:
            if override_request.reason_code in self.EMERGENCY_REASON_CODES:
                return True, f"Emergency override accepted: {override_request.reason_code.value}"
            else:
                return False, (
                    f"Reason code '{override_request.reason_code.value}' is not classified as emergency. "
                    f"Use one of: {[c.value for c in self.EMERGENCY_REASON_CODES]}"
                )

        # ALL_CHANGES_REQUIRE_OVERRIDE - any override with reason is valid
        if override_request.reason_text and len(override_request.reason_text.strip()) >= 10:
            return True, f"Override accepted with reason: {override_request.reason_code.value}"

        return False, "Override requires a reason with at least 10 characters"

    def create_audit_record(
        self,
        assignment_id: UUID,
        block_id: UUID,
        block_date: date,
        freeze_result: FreezeCheckResult,
        override_request: FreezeOverrideRequest,
    ) -> FreezeOverrideAuditRecord:
        """
        Create an audit record for a freeze override.

        Args:
            assignment_id: ID of the assignment being modified
            block_id: ID of the block
            block_date: Date of the block
            freeze_result: The freeze check result
            override_request: The override request

        Returns:
            FreezeOverrideAuditRecord
        """
        record = FreezeOverrideAuditRecord(
            id=uuid4(),
            timestamp=datetime.utcnow(),
            assignment_id=assignment_id,
            block_id=block_id,
            block_date=block_date,
            days_until_assignment=freeze_result.days_until_assignment or 0,
            reason_code=override_request.reason_code,
            reason_text=override_request.reason_text,
            initiated_by=override_request.initiated_by,
            initiating_module=override_request.initiating_module,
            is_emergency=override_request.is_emergency or (
                override_request.reason_code in self.EMERGENCY_REASON_CODES
            ),
            freeze_scope_at_time=freeze_result.freeze_scope,
            freeze_horizon_at_time=freeze_result.freeze_horizon_days,
        )

        # Store in memory (would also persist to database in production)
        self._override_records.append(record)

        # Log the override
        logger.warning(
            f"FREEZE OVERRIDE: assignment={assignment_id}, "
            f"block_date={block_date}, days_until={freeze_result.days_until_assignment}, "
            f"reason={override_request.reason_code.value}, "
            f"by={override_request.initiated_by}, "
            f"module={override_request.initiating_module}"
        )

        return record

    def enforce_freeze_or_override(
        self,
        block_date: date,
        override_request: FreezeOverrideRequest | None = None,
        assignment_id: UUID | None = None,
        block_id: UUID | None = None,
        reference_date: date | None = None,
    ) -> FreezeCheckResult:
        """
        Main enforcement method - check freeze and validate override if provided.

        This is the primary method that should be called by AssignmentService
        and other mutation paths.

        Args:
            block_date: Date of the assignment
            override_request: Override request if bypassing freeze
            assignment_id: ID of assignment (for audit)
            block_id: ID of block (for audit)
            reference_date: Reference date for freeze calculation

        Returns:
            FreezeCheckResult

        Raises:
            FreezeHorizonViolation: If frozen and no valid override provided
        """
        freeze_result = self.check_freeze_status(block_date, reference_date)

        if not freeze_result.is_frozen:
            return freeze_result

        # Assignment is frozen - check for override
        if override_request is None:
            raise FreezeHorizonViolation(freeze_result)

        # Validate the override
        is_valid, message = self.validate_override(freeze_result, override_request)

        if not is_valid:
            freeze_result.message = f"{freeze_result.message}. Override rejected: {message}"
            raise FreezeHorizonViolation(freeze_result)

        # Override is valid - create audit record
        if assignment_id and block_id:
            self.create_audit_record(
                assignment_id=assignment_id,
                block_id=block_id,
                block_date=block_date,
                freeze_result=freeze_result,
                override_request=override_request,
            )

        # Update result to indicate override was used
        freeze_result.message = f"Freeze overridden: {message}"
        freeze_result.requires_override = False

        return freeze_result

    def get_override_audit_records(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        initiated_by: str | None = None,
        initiating_module: str | None = None,
    ) -> list[FreezeOverrideAuditRecord]:
        """
        Query freeze override audit records.

        Args:
            start_date: Filter by timestamp >= start_date
            end_date: Filter by timestamp <= end_date
            initiated_by: Filter by initiator
            initiating_module: Filter by module

        Returns:
            List of FreezeOverrideAuditRecord
        """
        records = self._override_records

        if start_date:
            records = [r for r in records if r.timestamp.date() >= start_date]
        if end_date:
            records = [r for r in records if r.timestamp.date() <= end_date]
        if initiated_by:
            records = [r for r in records if r.initiated_by == initiated_by]
        if initiating_module:
            records = [r for r in records if r.initiating_module == initiating_module]

        return sorted(records, key=lambda r: r.timestamp, reverse=True)

    def get_freeze_statistics(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        """
        Get statistics about freeze overrides.

        Returns:
            Dict with override statistics
        """
        records = self.get_override_audit_records(start_date, end_date)

        if not records:
            return {
                "total_overrides": 0,
                "by_reason_code": {},
                "by_module": {},
                "emergency_count": 0,
                "non_emergency_count": 0,
            }

        by_reason_code = {}
        by_module = {}
        emergency_count = 0
        non_emergency_count = 0

        for record in records:
            # Count by reason code
            code = record.reason_code.value
            by_reason_code[code] = by_reason_code.get(code, 0) + 1

            # Count by module
            module = record.initiating_module
            by_module[module] = by_module.get(module, 0) + 1

            # Count emergency vs non-emergency
            if record.is_emergency:
                emergency_count += 1
            else:
                non_emergency_count += 1

        return {
            "total_overrides": len(records),
            "by_reason_code": by_reason_code,
            "by_module": by_module,
            "emergency_count": emergency_count,
            "non_emergency_count": non_emergency_count,
        }
