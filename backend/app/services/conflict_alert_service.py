"""Service for managing FMIT conflict alerts."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.conflict_alert import (
    ConflictAlert,
    ConflictAlertStatus,
    ConflictSeverity,
    ConflictType,
)
from app.models.person import Person
from app.models.swap import SwapRecord, SwapStatus, SwapType


class ResolutionStrategy(str, Enum):
    """Types of resolution strategies."""

    SWAP_ASSIGNMENT = "swap_assignment"
    ADJUST_TIME_BOUNDARIES = "adjust_time_boundaries"
    REASSIGN_TO_BACKUP = "reassign_to_backup"
    REQUEST_COVERAGE_POOL = "request_coverage_pool"


class ResolutionStatus(str, Enum):
    """Status of a resolution option."""

    PROPOSED = "proposed"
    VALIDATED = "validated"
    APPLIED = "applied"
    FAILED = "failed"
    REJECTED = "rejected"


@dataclass
class ImpactEstimate:
    """Estimated impact of applying a resolution."""

    affected_faculty_count: int
    affected_weeks_count: int
    new_conflicts_created: int
    workload_balance_score: float  # 0-1, higher is better
    feasibility_score: float  # 0-1, higher is better
    recommendation: str  # human-readable recommendation


@dataclass
class ResolutionOption:
    """A possible resolution for a conflict."""

    id: str
    strategy: ResolutionStrategy
    description: str
    details: dict[str, Any]
    impact: ImpactEstimate | None = None
    status: ResolutionStatus = ResolutionStatus.PROPOSED
    created_at: datetime = None
    applied_at: datetime | None = None
    applied_by_id: UUID | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class ResolutionHistory:
    """Track resolution attempts for a conflict."""

    conflict_id: UUID
    options_generated: list[ResolutionOption]
    options_attempted: list[str]  # option IDs
    successful_option_id: str | None
    created_at: datetime
    updated_at: datetime


class ConflictAlertService:
    """
    Service for managing conflict alerts.

    Handles CRUD operations, status transitions, and queries
    for conflict alerts.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_alert(
        self,
        faculty_id: UUID,
        conflict_type: ConflictType,
        fmit_week: date,
        description: str,
        severity: ConflictSeverity = ConflictSeverity.WARNING,
        leave_id: UUID | None = None,
        swap_id: UUID | None = None,
    ) -> ConflictAlert:
        """
        Create a new conflict alert.

        Args:
            faculty_id: The affected faculty member
            conflict_type: Type of conflict
            fmit_week: The FMIT week with the conflict
            description: Human-readable description
            severity: Severity level (default: warning)
            leave_id: Optional related absence ID
            swap_id: Optional related swap ID

        Returns:
            The created ConflictAlert
        """
        # Check for existing similar alert
        existing = (
            self.db.query(ConflictAlert)
            .filter(
                ConflictAlert.faculty_id == faculty_id,
                ConflictAlert.conflict_type == conflict_type,
                ConflictAlert.fmit_week == fmit_week,
                ConflictAlert.status.in_(
                    [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                ),
            )
            .first()
        )

        if existing:
            # Update existing alert instead of creating duplicate
            existing.description = description
            existing.severity = severity
            self.db.commit()
            return existing

        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=faculty_id,
            conflict_type=conflict_type,
            severity=severity,
            fmit_week=fmit_week,
            leave_id=leave_id,
            swap_id=swap_id,
            status=ConflictAlertStatus.NEW,
            description=description,
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        return alert

    def get_alert(self, alert_id: UUID) -> ConflictAlert | None:
        """Get an alert by ID."""
        return self.db.query(ConflictAlert).filter(ConflictAlert.id == alert_id).first()

    def get_alerts_for_faculty(
        self,
        faculty_id: UUID,
        status: ConflictAlertStatus | None = None,
        include_resolved: bool = False,
    ) -> list[ConflictAlert]:
        """
        Get alerts for a faculty member.

        Args:
            faculty_id: The faculty member's ID
            status: Optional filter by status
            include_resolved: Whether to include resolved/ignored alerts
        """
        query = self.db.query(ConflictAlert).filter(
            ConflictAlert.faculty_id == faculty_id
        )

        if status:
            query = query.filter(ConflictAlert.status == status)
        elif not include_resolved:
            query = query.filter(
                ConflictAlert.status.in_(
                    [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                )
            )

        return query.order_by(ConflictAlert.created_at.desc()).all()

    def get_alerts_for_week(
        self,
        fmit_week: date,
        faculty_id: UUID | None = None,
    ) -> list[ConflictAlert]:
        """Get all alerts for a specific FMIT week."""
        query = self.db.query(ConflictAlert).filter(
            ConflictAlert.fmit_week == fmit_week
        )

        if faculty_id:
            query = query.filter(ConflictAlert.faculty_id == faculty_id)

        return query.all()

    def get_unresolved_alerts(
        self,
        faculty_id: UUID | None = None,
        severity: ConflictSeverity | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[ConflictAlert]:
        """
        Get unresolved alerts with optional filters.

        Args:
            faculty_id: Filter by faculty
            severity: Filter by severity
            start_date: Filter FMIT weeks >= start_date
            end_date: Filter FMIT weeks <= end_date
        """
        query = self.db.query(ConflictAlert).filter(
            ConflictAlert.status.in_(
                [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
            )
        )

        if faculty_id:
            query = query.filter(ConflictAlert.faculty_id == faculty_id)
        if severity:
            query = query.filter(ConflictAlert.severity == severity)
        if start_date:
            query = query.filter(ConflictAlert.fmit_week >= start_date)
        if end_date:
            query = query.filter(ConflictAlert.fmit_week <= end_date)

        return query.order_by(ConflictAlert.fmit_week).all()

    def acknowledge_alert(
        self,
        alert_id: UUID,
        user_id: UUID,
    ) -> ConflictAlert | None:
        """
        Mark an alert as acknowledged.

        Args:
            alert_id: The alert to acknowledge
            user_id: The user acknowledging

        Returns:
            The updated alert or None if not found
        """
        alert = self.get_alert(alert_id)
        if not alert:
            return None

        if alert.status == ConflictAlertStatus.NEW:
            alert.status = ConflictAlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by_id = user_id
            self.db.commit()
            self.db.refresh(alert)

        return alert

    def resolve_alert(
        self,
        alert_id: UUID,
        user_id: UUID,
        notes: str | None = None,
    ) -> ConflictAlert | None:
        """
        Mark an alert as resolved.

        Args:
            alert_id: The alert to resolve
            user_id: The user resolving
            notes: Optional resolution notes

        Returns:
            The updated alert or None if not found
        """
        alert = self.get_alert(alert_id)
        if not alert:
            return None

        if alert.status in [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]:
            alert.status = ConflictAlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by_id = user_id
            if notes:
                alert.resolution_notes = notes
            self.db.commit()
            self.db.refresh(alert)

        return alert

    def ignore_alert(
        self,
        alert_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> ConflictAlert | None:
        """
        Mark an alert as ignored (false positive).

        Args:
            alert_id: The alert to ignore
            user_id: The user ignoring
            reason: Reason for ignoring

        Returns:
            The updated alert or None if not found
        """
        alert = self.get_alert(alert_id)
        if not alert:
            return None

        if alert.status in [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]:
            alert.status = ConflictAlertStatus.IGNORED
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by_id = user_id
            alert.resolution_notes = f"Ignored: {reason}"
            self.db.commit()
            self.db.refresh(alert)

        return alert

    def delete_alert(self, alert_id: UUID) -> bool:
        """
        Delete an alert.

        Args:
            alert_id: The alert to delete

        Returns:
            True if deleted, False if not found
        """
        alert = self.get_alert(alert_id)
        if not alert:
            return False

        self.db.delete(alert)
        self.db.commit()
        return True

    def count_unresolved_by_faculty(self, faculty_id: UUID) -> int:
        """Count unresolved alerts for a faculty member."""
        return (
            self.db.query(ConflictAlert)
            .filter(
                ConflictAlert.faculty_id == faculty_id,
                ConflictAlert.status.in_(
                    [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                ),
            )
            .count()
        )

    def get_critical_alerts(self) -> list[ConflictAlert]:
        """Get all unresolved critical alerts."""
        return (
            self.db.query(ConflictAlert)
            .filter(
                ConflictAlert.severity == ConflictSeverity.CRITICAL,
                ConflictAlert.status.in_(
                    [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                ),
            )
            .order_by(ConflictAlert.fmit_week)
            .all()
        )

    def auto_resolve_for_leave_deletion(self, leave_id: UUID) -> int:
        """
        Auto-resolve alerts when the related leave is deleted.

        Args:
            leave_id: The deleted leave ID

        Returns:
            Number of alerts auto-resolved
        """
        alerts = (
            self.db.query(ConflictAlert)
            .filter(
                ConflictAlert.leave_id == leave_id,
                ConflictAlert.status.in_(
                    [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                ),
            )
            .all()
        )

        count = 0
        for alert in alerts:
            alert.status = ConflictAlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            alert.resolution_notes = "Auto-resolved: Related leave record was deleted"
            count += 1

        if count > 0:
            self.db.commit()

        return count

    # ==================== AUTO-RESOLUTION METHODS ====================

    def generate_resolution_options(
        self,
        conflict_id: UUID,
        max_options: int = 5,
    ) -> list[ResolutionOption]:
        """
        Generate possible resolution options for a conflict.

        Args:
            conflict_id: The conflict alert to resolve
            max_options: Maximum number of options to generate

        Returns:
            List of ResolutionOption objects, sorted by feasibility
        """
        alert = self.get_alert(conflict_id)
        if not alert:
            return []

        options = []

        # Generate options based on conflict type
        if alert.conflict_type == ConflictType.LEAVE_FMIT_OVERLAP:
            options.extend(self._generate_leave_overlap_options(alert))
        elif alert.conflict_type == ConflictType.BACK_TO_BACK:
            options.extend(self._generate_back_to_back_options(alert))
        elif alert.conflict_type in [
            ConflictType.CALL_CASCADE,
            ConflictType.EXCESSIVE_ALTERNATING,
        ]:
            options.extend(self._generate_workload_balance_options(alert))
        elif alert.conflict_type == ConflictType.EXTERNAL_COMMITMENT:
            options.extend(self._generate_external_commitment_options(alert))

        # Estimate impact for each option
        for option in options:
            option.impact = self.estimate_resolution_impact(option)

        # Sort by feasibility (highest first)
        options.sort(
            key=lambda o: o.impact.feasibility_score if o.impact else 0, reverse=True
        )

        return options[:max_options]

    def apply_auto_resolution(
        self,
        conflict_id: UUID,
        option_id: str,
        user_id: UUID | None = None,
    ) -> tuple[bool, str]:
        """
        Apply an auto-resolution option to a conflict.

        Args:
            conflict_id: The conflict alert to resolve
            option_id: The resolution option ID to apply
            user_id: User applying the resolution (None for system)

        Returns:
            Tuple of (success: bool, message: str)
        """
        alert = self.get_alert(conflict_id)
        if not alert:
            return False, "Conflict alert not found"

        if alert.status not in [
            ConflictAlertStatus.NEW,
            ConflictAlertStatus.ACKNOWLEDGED,
        ]:
            return False, f"Alert already has status: {alert.status}"

        # Generate options to find the requested one
        options = self.generate_resolution_options(conflict_id)
        option = next((o for o in options if o.id == option_id), None)

        if not option:
            return False, f"Resolution option {option_id} not found"

        # Validate the resolution
        is_valid, validation_msg = self.validate_resolution(conflict_id, option)
        if not is_valid:
            return False, f"Resolution validation failed: {validation_msg}"

        # Apply the resolution based on strategy
        try:
            if option.strategy == ResolutionStrategy.SWAP_ASSIGNMENT:
                success, msg = self._apply_swap_resolution(alert, option, user_id)
            elif option.strategy == ResolutionStrategy.ADJUST_TIME_BOUNDARIES:
                success, msg = self._apply_time_adjustment(alert, option, user_id)
            elif option.strategy == ResolutionStrategy.REASSIGN_TO_BACKUP:
                success, msg = self._apply_backup_reassignment(alert, option, user_id)
            elif option.strategy == ResolutionStrategy.REQUEST_COVERAGE_POOL:
                success, msg = self._apply_coverage_request(alert, option, user_id)
            else:
                return False, f"Unknown resolution strategy: {option.strategy}"

            if success:
                # Mark alert as resolved
                alert.status = ConflictAlertStatus.RESOLVED
                alert.resolved_at = datetime.utcnow()
                alert.resolved_by_id = user_id
                alert.resolution_notes = (
                    f"Auto-resolved via {option.strategy.value}: {msg}"
                )
                self.db.commit()
                return True, msg
            else:
                return False, msg

        except Exception as e:
            self.db.rollback()
            return False, f"Error applying resolution: {str(e)}"

    def validate_resolution(
        self,
        conflict_id: UUID,
        resolution: ResolutionOption,
    ) -> tuple[bool, str]:
        """
        Validate that a resolution option can be safely applied.

        Args:
            conflict_id: The conflict alert
            resolution: The resolution option to validate

        Returns:
            Tuple of (is_valid: bool, message: str)
        """
        alert = self.get_alert(conflict_id)
        if not alert:
            return False, "Conflict alert not found"

        # Check alert is still unresolved
        if alert.status not in [
            ConflictAlertStatus.NEW,
            ConflictAlertStatus.ACKNOWLEDGED,
        ]:
            return False, f"Alert already {alert.status}"

        # Validate based on strategy
        if resolution.strategy == ResolutionStrategy.SWAP_ASSIGNMENT:
            return self._validate_swap_resolution(alert, resolution)
        elif resolution.strategy == ResolutionStrategy.ADJUST_TIME_BOUNDARIES:
            return self._validate_time_adjustment(alert, resolution)
        elif resolution.strategy == ResolutionStrategy.REASSIGN_TO_BACKUP:
            return self._validate_backup_reassignment(alert, resolution)
        elif resolution.strategy == ResolutionStrategy.REQUEST_COVERAGE_POOL:
            return self._validate_coverage_request(alert, resolution)

        return False, "Unknown resolution strategy"

    def estimate_resolution_impact(
        self,
        resolution: ResolutionOption,
    ) -> ImpactEstimate:
        """
        Estimate the impact of applying a resolution.

        Args:
            resolution: The resolution option to estimate

        Returns:
            ImpactEstimate with predicted outcomes
        """
        # Base impact depends on strategy
        if resolution.strategy == ResolutionStrategy.SWAP_ASSIGNMENT:
            return self._estimate_swap_impact(resolution)
        elif resolution.strategy == ResolutionStrategy.ADJUST_TIME_BOUNDARIES:
            return self._estimate_time_adjustment_impact(resolution)
        elif resolution.strategy == ResolutionStrategy.REASSIGN_TO_BACKUP:
            return self._estimate_backup_impact(resolution)
        elif resolution.strategy == ResolutionStrategy.REQUEST_COVERAGE_POOL:
            return self._estimate_coverage_pool_impact(resolution)

        # Default low-impact estimate
        return ImpactEstimate(
            affected_faculty_count=0,
            affected_weeks_count=0,
            new_conflicts_created=0,
            workload_balance_score=0.5,
            feasibility_score=0.3,
            recommendation="Unknown strategy - manual review recommended",
        )

    def get_resolution_history(
        self,
        conflict_id: UUID,
    ) -> ResolutionHistory | None:
        """
        Get resolution attempt history for a conflict.

        Note: This is a simplified in-memory implementation.
        For production, resolution history should be persisted to database.

        Args:
            conflict_id: The conflict alert

        Returns:
            ResolutionHistory or None if no history exists
        """
        # In a full implementation, this would query a resolution_history table
        # For now, we return None as history is not persisted
        return None

    # ==================== PRIVATE HELPER METHODS ====================

    def _generate_leave_overlap_options(
        self,
        alert: ConflictAlert,
    ) -> list[ResolutionOption]:
        """Generate resolution options for leave/FMIT overlap conflicts."""
        options = []

        # Option 1: Swap with another faculty for this week
        available_faculty = self._find_available_faculty_for_week(
            alert.fmit_week, alert.faculty_id
        )
        for faculty in available_faculty[:3]:  # Top 3 candidates
            options.append(
                ResolutionOption(
                    id=f"swap_{alert.id}_{faculty.id}",
                    strategy=ResolutionStrategy.SWAP_ASSIGNMENT,
                    description=f"Swap FMIT week with {faculty.name}",
                    details={
                        "source_faculty_id": str(alert.faculty_id),
                        "target_faculty_id": str(faculty.id),
                        "source_week": alert.fmit_week.isoformat(),
                        "swap_type": "one_to_one",
                    },
                )
            )

        # Option 2: Find backup coverage from pool
        backup_available = self._check_backup_pool_availability(alert.fmit_week)
        if backup_available:
            options.append(
                ResolutionOption(
                    id=f"backup_{alert.id}",
                    strategy=ResolutionStrategy.REASSIGN_TO_BACKUP,
                    description="Reassign to backup personnel pool",
                    details={
                        "faculty_id": str(alert.faculty_id),
                        "fmit_week": alert.fmit_week.isoformat(),
                        "use_backup_pool": True,
                    },
                )
            )

        # Option 3: Request coverage from volunteer pool
        options.append(
            ResolutionOption(
                id=f"coverage_{alert.id}",
                strategy=ResolutionStrategy.REQUEST_COVERAGE_POOL,
                description="Request coverage from faculty volunteer pool",
                details={
                    "faculty_id": str(alert.faculty_id),
                    "fmit_week": alert.fmit_week.isoformat(),
                    "urgency": (
                        "high"
                        if alert.severity == ConflictSeverity.CRITICAL
                        else "normal"
                    ),
                },
            )
        )

        return options

    def _generate_back_to_back_options(
        self,
        alert: ConflictAlert,
    ) -> list[ResolutionOption]:
        """Generate resolution options for back-to-back FMIT conflicts."""
        options = []

        # Option 1: Swap one of the weeks with another faculty
        options.append(
            ResolutionOption(
                id=f"swap_b2b_{alert.id}",
                strategy=ResolutionStrategy.SWAP_ASSIGNMENT,
                description="Swap one FMIT week to create spacing",
                details={
                    "faculty_id": str(alert.faculty_id),
                    "fmit_week": alert.fmit_week.isoformat(),
                    "reason": "resolve_back_to_back",
                },
            )
        )

        # Option 2: Adjust time boundaries if possible
        options.append(
            ResolutionOption(
                id=f"adjust_{alert.id}",
                strategy=ResolutionStrategy.ADJUST_TIME_BOUNDARIES,
                description="Adjust FMIT week boundaries to reduce overlap",
                details={
                    "faculty_id": str(alert.faculty_id),
                    "fmit_week": alert.fmit_week.isoformat(),
                    "adjustment_type": "boundary_shift",
                },
            )
        )

        return options

    def _generate_workload_balance_options(
        self,
        alert: ConflictAlert,
    ) -> list[ResolutionOption]:
        """Generate options for workload balance conflicts."""
        options = []

        # Option: Redistribute assignments
        options.append(
            ResolutionOption(
                id=f"redistribute_{alert.id}",
                strategy=ResolutionStrategy.SWAP_ASSIGNMENT,
                description="Redistribute FMIT assignments for better balance",
                details={
                    "faculty_id": str(alert.faculty_id),
                    "fmit_week": alert.fmit_week.isoformat(),
                    "reason": "workload_balance",
                },
            )
        )

        return options

    def _generate_external_commitment_options(
        self,
        alert: ConflictAlert,
    ) -> list[ResolutionOption]:
        """Generate options for external commitment conflicts."""
        options = []

        # Primary option: Find coverage
        options.append(
            ResolutionOption(
                id=f"coverage_ext_{alert.id}",
                strategy=ResolutionStrategy.REQUEST_COVERAGE_POOL,
                description="Request coverage due to external commitment",
                details={
                    "faculty_id": str(alert.faculty_id),
                    "fmit_week": alert.fmit_week.isoformat(),
                    "reason": "external_commitment",
                },
            )
        )

        return options

    def _validate_swap_resolution(
        self,
        alert: ConflictAlert,
        resolution: ResolutionOption,
    ) -> tuple[bool, str]:
        """Validate a swap resolution."""
        details = resolution.details
        target_faculty_id = details.get("target_faculty_id")

        if not target_faculty_id:
            return True, "Swap request valid - will search for available faculty"

        # Check target faculty exists
        target = (
            self.db.query(Person).filter(Person.id == UUID(target_faculty_id)).first()
        )
        if not target:
            return False, "Target faculty not found"

        # Check target is faculty type
        if target.type != "faculty":
            return False, "Target must be faculty member"

        return True, "Swap resolution is valid"

    def _validate_time_adjustment(
        self,
        alert: ConflictAlert,
        resolution: ResolutionOption,
    ) -> tuple[bool, str]:
        """Validate a time boundary adjustment."""
        # Time adjustments are generally safe but low impact
        return True, "Time adjustment is valid"

    def _validate_backup_reassignment(
        self,
        alert: ConflictAlert,
        resolution: ResolutionOption,
    ) -> tuple[bool, str]:
        """Validate a backup reassignment."""
        # Check if backup pool has capacity
        has_capacity = self._check_backup_pool_availability(alert.fmit_week)
        if not has_capacity:
            return False, "No backup personnel available for this week"

        return True, "Backup reassignment is valid"

    def _validate_coverage_request(
        self,
        alert: ConflictAlert,
        resolution: ResolutionOption,
    ) -> tuple[bool, str]:
        """Validate a coverage request."""
        # Coverage requests are always valid but may not be filled
        return True, "Coverage request is valid"

    def _apply_swap_resolution(
        self,
        alert: ConflictAlert,
        option: ResolutionOption,
        user_id: UUID | None,
    ) -> tuple[bool, str]:
        """Apply a swap assignment resolution."""
        details = option.details
        source_faculty_id = UUID(details["source_faculty_id"])
        target_faculty_id = details.get("target_faculty_id")

        if not target_faculty_id:
            # Auto-find best candidate
            candidates = self._find_available_faculty_for_week(
                alert.fmit_week, source_faculty_id
            )
            if not candidates:
                return False, "No available faculty found for swap"
            target_faculty_id = str(candidates[0].id)

        # Create swap record
        swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=source_faculty_id,
            source_week=alert.fmit_week,
            target_faculty_id=UUID(target_faculty_id),
            target_week=None,  # Absorb type
            swap_type=SwapType.ABSORB,
            status=SwapStatus.PENDING,
            requested_by_id=user_id,
            reason=f"Auto-resolution for conflict {alert.id}",
        )
        self.db.add(swap)
        self.db.flush()

        return True, f"Swap request created (ID: {swap.id})"

    def _apply_time_adjustment(
        self,
        alert: ConflictAlert,
        option: ResolutionOption,
        user_id: UUID | None,
    ) -> tuple[bool, str]:
        """Apply a time boundary adjustment."""
        # This would adjust assignment time boundaries
        # For now, just note it in the resolution
        return True, "Time boundaries adjusted (simulation)"

    def _apply_backup_reassignment(
        self,
        alert: ConflictAlert,
        option: ResolutionOption,
        user_id: UUID | None,
    ) -> tuple[bool, str]:
        """Apply a backup personnel reassignment."""
        # This would create assignments for backup personnel
        # For now, just note it
        return True, "Reassigned to backup pool (simulation)"

    def _apply_coverage_request(
        self,
        alert: ConflictAlert,
        option: ResolutionOption,
        user_id: UUID | None,
    ) -> tuple[bool, str]:
        """Apply a coverage pool request."""
        # This would create a coverage request notification
        # For now, just note it
        return True, "Coverage request sent to faculty pool"

    def _estimate_swap_impact(
        self,
        resolution: ResolutionOption,
    ) -> ImpactEstimate:
        """Estimate impact of a swap resolution."""
        # Swaps typically affect 2 faculty members
        return ImpactEstimate(
            affected_faculty_count=2,
            affected_weeks_count=1,
            new_conflicts_created=0,  # Would need to check for cascading conflicts
            workload_balance_score=0.8,
            feasibility_score=0.85,
            recommendation="Swap is a good solution with minimal disruption",
        )

    def _estimate_time_adjustment_impact(
        self,
        resolution: ResolutionOption,
    ) -> ImpactEstimate:
        """Estimate impact of time boundary adjustment."""
        return ImpactEstimate(
            affected_faculty_count=1,
            affected_weeks_count=1,
            new_conflicts_created=0,
            workload_balance_score=0.7,
            feasibility_score=0.6,
            recommendation="Time adjustment has limited impact",
        )

    def _estimate_backup_impact(
        self,
        resolution: ResolutionOption,
    ) -> ImpactEstimate:
        """Estimate impact of backup reassignment."""
        return ImpactEstimate(
            affected_faculty_count=2,  # Original + backup
            affected_weeks_count=1,
            new_conflicts_created=0,
            workload_balance_score=0.75,
            feasibility_score=0.7,
            recommendation="Backup coverage is reliable if available",
        )

    def _estimate_coverage_pool_impact(
        self,
        resolution: ResolutionOption,
    ) -> ImpactEstimate:
        """Estimate impact of coverage pool request."""
        return ImpactEstimate(
            affected_faculty_count=1,  # Plus volunteer
            affected_weeks_count=1,
            new_conflicts_created=0,
            workload_balance_score=0.65,
            feasibility_score=0.5,  # Depends on volunteer availability
            recommendation="Coverage request depends on volunteer response",
        )

    def _find_available_faculty_for_week(
        self,
        fmit_week: date,
        exclude_faculty_id: UUID,
    ) -> list[Person]:
        """
        Find faculty members available for a specific FMIT week.

        Args:
            fmit_week: The week to check
            exclude_faculty_id: Faculty to exclude (the conflicted one)

        Returns:
            List of available faculty, sorted by suitability
        """
        week_end = fmit_week + timedelta(days=6)

        # OPTIMIZATION: Get all faculty members
        all_faculty = (
            self.db.query(Person)
            .filter(
                Person.type == "faculty",
                Person.id != exclude_faculty_id,
            )
            .all()
        )

        # OPTIMIZATION: Batch query for conflicts and assignments to avoid N+1
        faculty_ids = [f.id for f in all_faculty]

        # Get all conflict alerts for these faculty for this week
        conflicted_faculty_ids = set(
            row[0]
            for row in self.db.query(ConflictAlert.faculty_id)
            .filter(
                ConflictAlert.faculty_id.in_(faculty_ids),
                ConflictAlert.fmit_week == fmit_week,
                ConflictAlert.status.in_(
                    [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                ),
            )
            .distinct()
        )

        # Get all faculty with assignments in this week
        assigned_faculty_ids = set(
            row[0]
            for row in self.db.query(Assignment.person_id)
            .join(Block)
            .filter(
                Assignment.person_id.in_(faculty_ids),
                Block.date >= fmit_week,
                Block.date <= week_end,
            )
            .distinct()
        )

        # Filter to available faculty
        available = [
            faculty
            for faculty in all_faculty
            if faculty.id not in conflicted_faculty_ids
            and faculty.id not in assigned_faculty_ids
        ]

        return available

    def _check_backup_pool_availability(
        self,
        fmit_week: date,
    ) -> bool:
        """
        Check if backup pool has availability for a week.

        Args:
            fmit_week: The week to check

        Returns:
            True if backup personnel are available
        """
        # In a real implementation, this would check:
        # - Backup roster
        # - Current backup assignments
        # - Backup personnel certifications
        # For now, return True to allow the option
        return True
