"""
Barrier detection and classification for schedule changes.

This module identifies and classifies energy barriers that prevent or
hinder schedule changes. It integrates with the existing codebase:
- Freeze horizon service (kinetic barriers)
- Credential requirements (steric barriers)
- ACGME compliance (regulatory barriers)
- Role permissions (electronic barriers)
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.faculty_preference import FacultyPreference
from app.models.procedure_credential import ProcedureCredential
from app.models.rotation_template import RotationTemplate
from app.scheduling_catalyst.models import (
    ActivationEnergy,
    BarrierType,
    EnergyBarrier,
)


class ScheduleContext(Protocol):
    """Protocol for schedule change context."""

    assignment_id: UUID
    person_id: UUID
    target_date: date
    rotation_id: UUID | None


@dataclass
class BarrierWeights:
    """
    Configurable weights for different barrier types.

    These weights determine how much each barrier type contributes
    to the overall activation energy.
    """

    kinetic: float = 0.3  # Time-based barriers
    thermodynamic: float = 0.2  # Equilibrium barriers
    steric: float = 0.25  # Credential barriers
    electronic: float = 0.15  # Authorization barriers
    regulatory: float = 0.4  # Compliance barriers (highest)

    def get_weight(self, barrier_type: BarrierType) -> float:
        """Get weight for a barrier type."""
        return {
            BarrierType.KINETIC: self.kinetic,
            BarrierType.THERMODYNAMIC: self.thermodynamic,
            BarrierType.STERIC: self.steric,
            BarrierType.ELECTRONIC: self.electronic,
            BarrierType.REGULATORY: self.regulatory,
        }.get(barrier_type, 0.2)


class BarrierDetector:
    """
    Detects energy barriers for proposed schedule changes.

    Integrates with existing services to identify all obstacles
    that would prevent or hinder a schedule change.
    """

    def __init__(
        self,
        db: AsyncSession,
        weights: BarrierWeights | None = None,
    ) -> None:
        """
        Initialize the barrier detector.

        Args:
            db: Database session
            weights: Custom barrier weights (uses defaults if None)
        """
        self.db = db
        self.weights = weights or BarrierWeights()
        self._barriers: list[EnergyBarrier] = []

    async def detect_all_barriers(
        self,
        assignment_id: UUID,
        proposed_change: dict[str, Any],
        reference_date: date | None = None,
    ) -> list[EnergyBarrier]:
        """
        Detect all barriers for a proposed schedule change.

        Args:
            assignment_id: ID of the assignment to modify
            proposed_change: Dict describing the proposed change
            reference_date: Date to use for calculations (defaults to today)

        Returns:
            List of all detected energy barriers
        """
        self._barriers = []
        ref_date = reference_date or date.today()

        # Detect barriers in parallel categories
        await self._detect_kinetic_barriers(assignment_id, proposed_change, ref_date)
        await self._detect_steric_barriers(assignment_id, proposed_change)
        await self._detect_electronic_barriers(assignment_id, proposed_change)
        await self._detect_regulatory_barriers(assignment_id, proposed_change)
        await self._detect_thermodynamic_barriers(assignment_id, proposed_change)

        return self._barriers

    async def _detect_kinetic_barriers(
        self,
        assignment_id: UUID,
        proposed_change: dict[str, Any],
        reference_date: date,
    ) -> None:
        """
        Detect time-based (kinetic) barriers.

        Kinetic barriers include:
        - Freeze horizon restrictions
        - Notice period requirements
        - Lead time for approvals
        """
        target_date = proposed_change.get("target_date")
        if not target_date:
            return

        if isinstance(target_date, str):
            target_date = date.fromisoformat(target_date)

        days_until = (target_date - reference_date).days

        # Freeze horizon barrier
        # Default freeze is 14 days, but severity scales
        freeze_horizon_days = 14
        if days_until <= freeze_horizon_days:
            severity = 1.0 - (days_until / freeze_horizon_days)
            self._barriers.append(
                EnergyBarrier(
                    barrier_type=BarrierType.KINETIC,
                    name="Freeze Horizon",
                    description=f"Assignment is within {freeze_horizon_days}-day freeze period",
                    energy_contribution=min(0.8, severity * 0.8),
                    is_absolute=days_until <= 0,  # Same-day = absolute barrier
                    source="freeze_horizon",
                    metadata={
                        "days_until": days_until,
                        "freeze_horizon_days": freeze_horizon_days,
                    },
                )
            )

        # Short notice barrier (24-48 hour changes)
        if 0 < days_until <= 2:
            self._barriers.append(
                EnergyBarrier(
                    barrier_type=BarrierType.KINETIC,
                    name="Short Notice",
                    description="Change requires very short notice",
                    energy_contribution=0.3,
                    is_absolute=False,
                    source="short_notice",
                    metadata={"hours_until": days_until * 24},
                )
            )

    async def _detect_steric_barriers(
        self,
        assignment_id: UUID,
        proposed_change: dict[str, Any],
    ) -> None:
        """
        Detect structural (steric) barriers.

        Steric barriers include:
        - Missing credentials for rotation
        - Competency level requirements
        - Supervision ratio requirements
        """
        new_person_id = proposed_change.get("new_person_id")
        rotation_id = proposed_change.get("rotation_id")

        if not new_person_id or not rotation_id:
            return

        # Check credential requirements
        # In a real implementation, query the database for credentials
        has_required_credentials = await self._check_credentials(
            new_person_id, rotation_id
        )

        if not has_required_credentials:
            self._barriers.append(
                EnergyBarrier(
                    barrier_type=BarrierType.STERIC,
                    name="Missing Credentials",
                    description="Person lacks required credentials for this rotation",
                    energy_contribution=0.9,
                    is_absolute=True,  # Cannot bypass credential requirements
                    source="credential_check",
                    metadata={
                        "person_id": str(new_person_id),
                        "rotation_id": str(rotation_id),
                    },
                )
            )

        # Check competency level
        competency_level = await self._get_competency_level(new_person_id, rotation_id)
        if competency_level and competency_level < 2:  # Below "qualified"
            self._barriers.append(
                EnergyBarrier(
                    barrier_type=BarrierType.STERIC,
                    name="Insufficient Competency",
                    description="Person's competency level is below requirement",
                    energy_contribution=0.5,
                    is_absolute=False,  # Can be supervised
                    source="competency_check",
                    metadata={
                        "competency_level": competency_level,
                        "required_level": 2,
                    },
                )
            )

    async def _detect_electronic_barriers(
        self,
        assignment_id: UUID,
        proposed_change: dict[str, Any],
    ) -> None:
        """
        Detect authorization (electronic) barriers.

        Electronic barriers include:
        - User doesn't have permission to make changes
        - Requires coordinator approval
        - Requires faculty consent
        """
        requester_role = proposed_change.get("requester_role", "resident")
        change_type = proposed_change.get("change_type", "swap")

        # Role-based authorization barrier
        authorized_roles = {"admin", "coordinator"}
        if requester_role not in authorized_roles:
            if change_type == "reassignment":
                self._barriers.append(
                    EnergyBarrier(
                        barrier_type=BarrierType.ELECTRONIC,
                        name="Authorization Required",
                        description="Reassignments require coordinator authorization",
                        energy_contribution=0.4,
                        is_absolute=False,
                        source="role_authorization",
                        metadata={
                            "requester_role": requester_role,
                            "required_roles": list(authorized_roles),
                        },
                    )
                )

        # Consent barrier for swaps
        if change_type == "swap":
            other_person_consented = proposed_change.get(
                "other_person_consented", False
            )
            if not other_person_consented:
                self._barriers.append(
                    EnergyBarrier(
                        barrier_type=BarrierType.ELECTRONIC,
                        name="Consent Required",
                        description="Other party has not consented to swap",
                        energy_contribution=0.6,
                        is_absolute=True,  # Must have consent
                        source="consent_check",
                        metadata={"awaiting_consent": True},
                    )
                )

    async def _detect_regulatory_barriers(
        self,
        assignment_id: UUID,
        proposed_change: dict[str, Any],
    ) -> None:
        """
        Detect compliance (regulatory) barriers.

        Regulatory barriers include:
        - ACGME duty hour violations
        - Supervision ratio violations
        - 1-in-7 day off rule violations
        """
        new_person_id = proposed_change.get("new_person_id")
        target_date = proposed_change.get("target_date")

        if not new_person_id or not target_date:
            return

        # Check ACGME duty hours
        would_violate_hours = await self._check_acgme_hours(new_person_id, target_date)
        if would_violate_hours:
            self._barriers.append(
                EnergyBarrier(
                    barrier_type=BarrierType.REGULATORY,
                    name="ACGME Duty Hour Violation",
                    description="Change would violate 80-hour weekly limit",
                    energy_contribution=1.0,
                    is_absolute=True,  # ACGME violations are absolute barriers
                    source="acgme_hours",
                    metadata={"rule": "80_hour_week"},
                )
            )

        # Check 1-in-7 day off rule
        would_violate_day_off = await self._check_day_off_rule(
            new_person_id, target_date
        )
        if would_violate_day_off:
            self._barriers.append(
                EnergyBarrier(
                    barrier_type=BarrierType.REGULATORY,
                    name="ACGME Day-Off Violation",
                    description="Change would violate 1-in-7 day off requirement",
                    energy_contribution=1.0,
                    is_absolute=True,
                    source="acgme_day_off",
                    metadata={"rule": "1_in_7_day_off"},
                )
            )

    async def _detect_thermodynamic_barriers(
        self,
        assignment_id: UUID,
        proposed_change: dict[str, Any],
    ) -> None:
        """
        Detect equilibrium (thermodynamic) barriers.

        Thermodynamic barriers relate to system balance:
        - Workload imbalance
        - Preference violations
        - Coverage gaps created
        """
        new_person_id = proposed_change.get("new_person_id")

        if not new_person_id:
            return

        # Check workload balance
        current_workload = await self._get_workload(new_person_id)
        if current_workload and current_workload > 0.8:  # Over 80% utilized
            excess = current_workload - 0.8
            self._barriers.append(
                EnergyBarrier(
                    barrier_type=BarrierType.THERMODYNAMIC,
                    name="Workload Imbalance",
                    description="Person is already at high utilization",
                    energy_contribution=min(0.5, excess * 2.5),
                    is_absolute=False,
                    source="workload_balance",
                    metadata={
                        "current_utilization": current_workload,
                        "threshold": 0.8,
                    },
                )
            )

        # Check preference conflicts
        violates_preference = await self._check_preferences(
            new_person_id, proposed_change
        )
        if violates_preference:
            self._barriers.append(
                EnergyBarrier(
                    barrier_type=BarrierType.THERMODYNAMIC,
                    name="Preference Conflict",
                    description="Change conflicts with person's stated preferences",
                    energy_contribution=0.2,
                    is_absolute=False,
                    source="preference_check",
                    metadata={"preference_type": violates_preference},
                )
            )

    # Helper methods - integrate with actual services
    async def _check_credentials(self, person_id: UUID, rotation_id: UUID) -> bool:
        """
        Check if person has required credentials for rotation.

        Queries the procedure_credential table to verify the person has
        valid, active credentials for procedures associated with the rotation.

        Args:
            person_id: UUID of the person to check
            rotation_id: UUID of the target rotation

        Returns:
            True if person has all required credentials, False otherwise
        """
        # Query for active credentials for this person and rotation's procedures
        # First, get the rotation to find its required procedures
        rotation_result = await self.db.execute(
            select(RotationTemplate).where(RotationTemplate.id == rotation_id)
        )
        rotation = rotation_result.scalar_one_or_none()

        if not rotation:
            # Rotation not found - treat as no credential requirements
            return True

        # Get all credentials for this person
        creds_result = await self.db.execute(
            select(ProcedureCredential).where(
                ProcedureCredential.person_id == person_id,
                ProcedureCredential.status == "active",
            )
        )
        credentials = creds_result.scalars().all()

        # Check if any credentials are expired
        today = date.today()
        valid_credentials = [
            cred
            for cred in credentials
            if cred.expiration_date is None or cred.expiration_date >= today
        ]

        # For now, if person has any valid credentials, consider them credentialed
        # In a full implementation, would match rotation.required_procedures
        return len(valid_credentials) > 0 if credentials else True

    async def _get_competency_level(
        self, person_id: UUID, rotation_id: UUID
    ) -> int | None:
        """
        Get person's competency level for a rotation.

        Queries procedure_credential to find the competency level for
        procedures associated with the rotation.

        Args:
            person_id: UUID of the person
            rotation_id: UUID of the rotation

        Returns:
            Competency level as int (1=trainee, 2=qualified, 3=expert, 4=master)
            or None if no credential found
        """
        # Map competency level strings to integers
        level_map = {"trainee": 1, "qualified": 2, "expert": 3, "master": 4}

        # Get credentials for this person
        creds_result = await self.db.execute(
            select(ProcedureCredential).where(
                ProcedureCredential.person_id == person_id,
                ProcedureCredential.status == "active",
            )
        )
        credentials = creds_result.scalars().all()

        if not credentials:
            return None

        # Return the highest competency level found
        max_level = 0
        for cred in credentials:
            level = level_map.get(cred.competency_level, 2)
            max_level = max(max_level, level)

        return max_level if max_level > 0 else None

    async def _check_acgme_hours(self, person_id: UUID, target_date: Any) -> bool:
        """
        Check if adding this assignment would violate ACGME 80-hour rule.

        Calculates the rolling 4-week average of hours worked and checks
        if adding another assignment would push it over 80 hours/week.

        Args:
            person_id: UUID of the person
            target_date: Date of the proposed assignment

        Returns:
            True if would violate ACGME hours, False otherwise
        """
        if isinstance(target_date, str):
            target_date = date.fromisoformat(target_date)

        # Calculate the 4-week window around the target date
        window_start = target_date - timedelta(weeks=2)
        window_end = target_date + timedelta(weeks=2)

        # Query assignments in the window
        result = await self.db.execute(
            select(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .where(
                Assignment.person_id == person_id,
                Block.date >= window_start,
                Block.date <= window_end,
            )
        )
        assignments = result.scalars().all()

        # Calculate hours (assume 6 hours per half-day block)
        hours_per_block = 6
        total_hours = len(assignments) * hours_per_block

        # Check if adding one more would violate
        # 80 hours/week * 4 weeks = 320 hours max
        max_hours = 80 * 4
        projected_hours = total_hours + hours_per_block

        return projected_hours > max_hours

    async def _check_day_off_rule(self, person_id: UUID, target_date: Any) -> bool:
        """
        Check if assignment would violate 1-in-7 day off rule.

        ACGME requires at least one 24-hour period off every 7 days.
        This checks if adding an assignment on target_date would create
        7 or more consecutive working days.

        Args:
            person_id: UUID of the person
            target_date: Date of the proposed assignment

        Returns:
            True if would violate day-off rule, False otherwise
        """
        if isinstance(target_date, str):
            target_date = date.fromisoformat(target_date)

        # Check 7 days before and after target date
        check_start = target_date - timedelta(days=6)
        check_end = target_date + timedelta(days=6)

        # Get all assignment dates in this window
        result = await self.db.execute(
            select(Block.date)
            .distinct()
            .join(Assignment, Assignment.block_id == Block.id)
            .where(
                Assignment.person_id == person_id,
                Block.date >= check_start,
                Block.date <= check_end,
            )
        )
        work_dates = {row[0] for row in result.fetchall()}

        # Add the proposed date
        work_dates.add(target_date)

        # Check for 7+ consecutive days of work
        sorted_dates = sorted(work_dates)
        consecutive = 1
        max_consecutive = 1

        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 1

        return max_consecutive >= 7

    async def _get_workload(self, person_id: UUID) -> float | None:
        """
        Get current workload utilization for person.

        Calculates utilization as: assigned_blocks / available_blocks
        for the current rolling 4-week period.

        Args:
            person_id: UUID of the person

        Returns:
            Utilization as float (0.0 to 1.0), or None if cannot calculate
        """
        today = date.today()
        window_start = today - timedelta(weeks=2)
        window_end = today + timedelta(weeks=2)

        # Count assigned blocks
        result = await self.db.execute(
            select(func.count(Assignment.id))
            .join(Block, Assignment.block_id == Block.id)
            .where(
                Assignment.person_id == person_id,
                Block.date >= window_start,
                Block.date <= window_end,
            )
        )
        assigned_count = result.scalar() or 0

        # Calculate available blocks (2 blocks per day * 28 days)
        # Subtract weekends for realistic utilization (10 workdays * 2)
        available_blocks = 28 * 2  # 56 blocks in 4 weeks

        if available_blocks == 0:
            return None

        return min(1.0, assigned_count / available_blocks)

    async def _check_preferences(
        self, person_id: UUID, proposed_change: dict[str, Any]
    ) -> str | None:
        """
        Check if change violates person's scheduling preferences.

        Queries FacultyPreference to check if the proposed date/week
        is blocked or conflicts with stated preferences.

        Args:
            person_id: UUID of the person
            proposed_change: Dict with change details including target_date

        Returns:
            String describing the preference conflict, or None if no conflict
        """
        target_date = proposed_change.get("target_date")
        if not target_date:
            return None

        if isinstance(target_date, str):
            target_date = date.fromisoformat(target_date)

        # Get the ISO week string for this date
        week_start = target_date - timedelta(days=target_date.weekday())
        week_str = week_start.isoformat()

        # Query faculty preferences
        result = await self.db.execute(
            select(FacultyPreference).where(FacultyPreference.faculty_id == person_id)
        )
        prefs = result.scalar_one_or_none()

        if not prefs:
            return None

        # Check if week is blocked
        if prefs.blocked_weeks and week_str in prefs.blocked_weeks:
            return "blocked_week"

        # Check if already at max consecutive weeks
        # This would require more context about surrounding assignments
        # For now, just flag if the week isn't preferred but isn't blocked
        if prefs.preferred_weeks and week_str not in prefs.preferred_weeks:
            # Not in preferred weeks - soft preference violation
            if len(prefs.preferred_weeks) > 0:
                return "not_preferred_week"

        return None

    def calculate_activation_energy(self) -> ActivationEnergy:
        """
        Calculate total activation energy from detected barriers.

        Returns:
            ActivationEnergy with breakdown by barrier type
        """
        if not self._barriers:
            return ActivationEnergy(value=0.0)

        components: dict[BarrierType, float] = {}
        total = 0.0

        for barrier in self._barriers:
            bt = barrier.barrier_type
            weighted = barrier.energy_contribution * self.weights.get_weight(bt)
            if bt not in components:
                components[bt] = 0.0
            components[bt] += weighted
            total += weighted

        # Normalize to 0-1 range
        normalized_total = min(1.0, total)

        return ActivationEnergy(
            value=normalized_total,
            components=components,
        )


class BarrierClassifier:
    """
    Classifies barriers by severity and actionability.

    Provides analysis of barriers to help identify which catalysts
    would be most effective.
    """

    @staticmethod
    def classify_severity(barrier: EnergyBarrier) -> str:
        """
        Classify barrier severity.

        Returns:
            "critical", "high", "medium", or "low"
        """
        if barrier.is_absolute:
            return "critical"
        if barrier.energy_contribution >= 0.7:
            return "high"
        if barrier.energy_contribution >= 0.4:
            return "medium"
        return "low"

    @staticmethod
    def classify_actionability(barrier: EnergyBarrier) -> str:
        """
        Classify how actionable a barrier is.

        Returns:
            "immutable", "requires_escalation", "catalyzable", "auto_resolvable"
        """
        if barrier.is_absolute:
            return "immutable"

        # Regulatory barriers typically require escalation
        if barrier.barrier_type == BarrierType.REGULATORY:
            return "requires_escalation"

        # Electronic barriers can be catalyzed by authorized personnel
        if barrier.barrier_type == BarrierType.ELECTRONIC:
            return "catalyzable"

        # Time-based barriers may auto-resolve
        if barrier.barrier_type == BarrierType.KINETIC:
            if barrier.source == "freeze_horizon":
                return "catalyzable"  # Can be overridden
            return "auto_resolvable"  # Will resolve with time

        return "catalyzable"

    @staticmethod
    def get_recommended_catalysts(barrier: EnergyBarrier) -> list[str]:
        """
        Get recommended catalyst types for a barrier.

        Returns:
            List of catalyst identifiers that could address this barrier
        """
        if barrier.is_absolute:
            return []

        recommendations: dict[BarrierType, list[str]] = {
            BarrierType.KINETIC: [
                "coordinator_override",
                "emergency_code",
                "freeze_waiver",
            ],
            BarrierType.THERMODYNAMIC: [
                "workload_balancer",
                "preference_negotiation",
                "auto_matcher",
            ],
            BarrierType.STERIC: [
                "supervision_arrangement",
                "credential_expedite",
                "cross_trained_backup",
            ],
            BarrierType.ELECTRONIC: [
                "coordinator_approval",
                "faculty_consent",
                "admin_override",
            ],
            BarrierType.REGULATORY: [
                "schedule_adjustment",
                "coverage_redistribution",
            ],
        }

        return recommendations.get(barrier.barrier_type, [])

    @staticmethod
    def summarize_barriers(barriers: list[EnergyBarrier]) -> dict[str, Any]:
        """
        Generate a summary of all barriers.

        Returns:
            Dictionary with barrier statistics and recommendations
        """
        if not barriers:
            return {
                "total_count": 0,
                "has_absolute": False,
                "highest_severity": None,
                "by_type": {},
                "recommended_approach": "proceed",
            }

        by_type: dict[str, int] = {}
        severities: list[str] = []
        has_absolute = False

        for barrier in barriers:
            bt_name = barrier.barrier_type.value
            by_type[bt_name] = by_type.get(bt_name, 0) + 1
            severities.append(BarrierClassifier.classify_severity(barrier))
            if barrier.is_absolute:
                has_absolute = True

        # Determine highest severity
        severity_order = ["critical", "high", "medium", "low"]
        highest = "low"
        for sev in severity_order:
            if sev in severities:
                highest = sev
                break

        # Recommend approach
        if has_absolute:
            approach = "blocked"
        elif highest == "critical":
            approach = "requires_intervention"
        elif highest == "high":
            approach = "seek_catalyst"
        elif highest == "medium":
            approach = "proceed_with_caution"
        else:
            approach = "proceed"

        return {
            "total_count": len(barriers),
            "has_absolute": has_absolute,
            "highest_severity": highest,
            "by_type": by_type,
            "recommended_approach": approach,
        }
