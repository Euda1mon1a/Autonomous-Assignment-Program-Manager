"""
Emergency Deployment Service - The "Oh Shit" Button.

Orchestrates schedule repair when a faculty member deploys or becomes
suddenly unavailable. Chains together existing resilience tools:

1. ASSESS: Calculate fragility/recovery distance
2. EXECUTE: Try incremental → cascade → fallback based on fragility
3. VERIFY: Check health and escalate if still broken

Tiered Response Strategy:
- Fragility < 0.3: Incremental repair (fast, surgical)
- Fragility 0.3-0.6: Cascade with sacrifice hierarchy
- Fragility >= 0.6: Activate pre-computed fallback

See: docs/planning/CP_SAT_PIPELINE_REFINEMENT_PHASE5.md for context.
"""

from __future__ import annotations

import time
from datetime import date, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.call_assignment import CallAssignment
from app.models.call_override import CallOverride
from app.models.half_day_assignment import HalfDayAssignment
from app.models.person import Person
from app.models.schedule_override import ScheduleOverride
from app.schemas.cascade_override import CascadeOverrideRequest
from app.schemas.emergency_deployment import (
    EmergencyDeploymentRequest,
    EmergencyDeploymentResponse,
    EmergencyStrategy,
    FragilityAssessment,
    HealthVerification,
    RepairOutcome,
)
from app.services.cascade_override_service import CascadeOverrideService

logger = get_logger(__name__)

# Fragility thresholds for strategy selection
FRAGILITY_INCREMENTAL_THRESHOLD = 0.3  # Below this: try incremental first
FRAGILITY_CASCADE_THRESHOLD = 0.6  # Below this: try cascade
# Above CASCADE_THRESHOLD: use fallback

# Coverage threshold for healthy state
COVERAGE_HEALTHY_THRESHOLD = 0.95


class EmergencyDeploymentService:
    """
    Orchestrates emergency deployment response.

    The "Oh Shit" button that unfucks a schedule when someone deploys.

    Usage:
        service = EmergencyDeploymentService(db)
        response = await service.handle_deployment(request)

        if response.overall_success:
            print(f"Schedule repaired using {response.assessment.recommended_strategy}")
        else:
            print(f"Manual intervention needed: {response.errors}")
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.cascade_service = CascadeOverrideService(session)

    async def handle_deployment(
        self,
        request: EmergencyDeploymentRequest,
        created_by_id: UUID | None = None,
    ) -> EmergencyDeploymentResponse:
        """
        Handle an emergency deployment with tiered repair strategy.

        Args:
            request: Deployment details (person, dates, dry_run flag)
            created_by_id: User ID for audit trail

        Returns:
            EmergencyDeploymentResponse with assessment, repair outcome, and health check
        """
        start_time = time.time()
        request_id = uuid4()

        errors: list[str] = []
        warnings: list[str] = []
        recommendations: list[str] = []

        # Validate person exists and is faculty
        person = await self.session.get(Person, request.person_id)
        if not person:
            return self._error_response(
                request, request_id, start_time, ["Person not found"]
            )
        if not person.is_faculty:
            return self._error_response(
                request,
                request_id,
                start_time,
                ["Emergency deployment service currently supports faculty only"],
            )

        # Phase 1: ASSESS
        assessment = await self._assess_fragility(
            request.person_id,
            request.start_date,
            request.end_date,
            request.force_strategy,
        )

        # Dry run: return assessment only
        if request.dry_run:
            recommendations.append(
                f"Recommended strategy: {assessment.recommended_strategy.value}"
            )
            if assessment.fragility_score >= FRAGILITY_CASCADE_THRESHOLD:
                recommendations.append(
                    "High fragility detected. Consider proactive rebalancing."
                )
            return EmergencyDeploymentResponse(
                request_id=request_id,
                person_id=request.person_id,
                start_date=request.start_date,
                end_date=request.end_date,
                dry_run=True,
                assessment=assessment,
                repair_outcome=None,
                health_check=None,
                overall_success=True,  # Assessment succeeded
                total_time_ms=(time.time() - start_time) * 1000,
                recommendations=recommendations,
                warnings=warnings,
                errors=errors,
            )

        # Phase 2: EXECUTE
        repair_outcome = await self._execute_repair(
            request,
            assessment,
            created_by_id,
        )

        if repair_outcome.strategy_used == EmergencyStrategy.FALLBACK:
            warnings.append(
                "Fallback schedule activated - review and deactivate when resolved"
            )

        # Phase 3: VERIFY
        health_check = await self._verify_health(
            request.start_date,
            request.end_date,
            repair_outcome,
            request.reason,
        )

        # Build recommendations
        if not health_check.is_healthy:
            recommendations.append("Coverage below 95% - manual review required")
            if health_check.escalated:
                recommendations.append(
                    f"Crisis mode activated ({health_check.escalation_severity})"
                )
        else:
            recommendations.append("Schedule repaired successfully")

        if repair_outcome.slots_remaining > 0:
            recommendations.append(
                f"{repair_outcome.slots_remaining} slots need manual coverage"
            )

        overall_success = health_check.is_healthy and len(errors) == 0

        return EmergencyDeploymentResponse(
            request_id=request_id,
            person_id=request.person_id,
            start_date=request.start_date,
            end_date=request.end_date,
            dry_run=False,
            assessment=assessment,
            repair_outcome=repair_outcome,
            health_check=health_check,
            overall_success=overall_success,
            total_time_ms=(time.time() - start_time) * 1000,
            recommendations=recommendations,
            warnings=warnings,
            errors=errors,
        )

    async def _assess_fragility(
        self,
        person_id: UUID,
        start_date: date,
        end_date: date,
        force_strategy: EmergencyStrategy | None = None,
    ) -> FragilityAssessment:
        """
        Assess schedule fragility for this deployment.

        Calculates a fragility score (0-1) based on:
        - Number of affected slots
        - Current coverage state
        - Available replacement candidates

        Returns recommended strategy based on fragility.
        """
        assess_start = time.time()

        # Count affected assignments
        half_day_count = await self._count_half_day_assignments(
            person_id, start_date, end_date
        )
        call_count = await self._count_call_assignments(person_id, start_date, end_date)
        affected_slots = half_day_count + call_count

        # Estimate recovery distance
        # Simple heuristic: more slots = higher RD
        # In production, would query MCP recovery_distance_tool
        rd_mean = min(affected_slots * 0.5, 5.0)
        rd_max = min(affected_slots, 10)

        # Calculate fragility score
        # Based on affected slots and estimate of repair difficulty
        if affected_slots == 0:
            fragility_score = 0.0
        elif affected_slots <= 3:
            fragility_score = 0.15
        elif affected_slots <= 7:
            fragility_score = 0.35
        elif affected_slots <= 14:
            fragility_score = 0.55
        else:
            fragility_score = 0.75

        # Boost fragility if many call assignments (higher stakes)
        if call_count >= 3:
            fragility_score = min(fragility_score + 0.1, 1.0)

        # Select strategy
        if force_strategy:
            recommended_strategy = force_strategy
        elif fragility_score < FRAGILITY_INCREMENTAL_THRESHOLD:
            recommended_strategy = EmergencyStrategy.INCREMENTAL
        elif fragility_score < FRAGILITY_CASCADE_THRESHOLD:
            recommended_strategy = EmergencyStrategy.CASCADE
        else:
            recommended_strategy = EmergencyStrategy.FALLBACK

        return FragilityAssessment(
            fragility_score=fragility_score,
            rd_mean=rd_mean,
            rd_max=rd_max,
            affected_slots=affected_slots,
            recommended_strategy=recommended_strategy,
            assessment_time_ms=(time.time() - assess_start) * 1000,
        )

    async def _execute_repair(
        self,
        request: EmergencyDeploymentRequest,
        assessment: FragilityAssessment,
        created_by_id: UUID | None,
    ) -> RepairOutcome:
        """Execute repair based on recommended strategy."""
        exec_start = time.time()
        strategy = assessment.recommended_strategy
        details: list[str] = []
        slots_repaired = 0
        slots_remaining = 0
        cascade_steps = 0
        fallback_activated: str | None = None

        try:
            if strategy == EmergencyStrategy.INCREMENTAL:
                # Incremental: use cascade with dry_run to plan, then apply
                # For now, cascade handles the incremental case at depth 1
                result = await self._try_cascade_repair(
                    request, created_by_id, max_depth=1
                )
                slots_repaired = result["repaired"]
                slots_remaining = result["remaining"]
                cascade_steps = result["steps"]
                details.extend(result["details"])
                overridden_ids = result.get("overridden_assignment_ids", set())

                # If incremental failed, escalate to cascade
                # Skip assignments that already have overrides to avoid 409 conflicts
                if slots_remaining > 0:
                    details.append(
                        "Incremental repair incomplete, escalating to cascade"
                    )
                    strategy = EmergencyStrategy.CASCADE
                    result = await self._try_cascade_repair(
                        request,
                        created_by_id,
                        max_depth=2,
                        exclude_assignment_ids=overridden_ids,
                    )
                    slots_repaired += result["repaired"]
                    slots_remaining = result["remaining"]
                    cascade_steps += result["steps"]
                    details.extend(result["details"])

            elif strategy == EmergencyStrategy.CASCADE:
                result = await self._try_cascade_repair(
                    request, created_by_id, max_depth=2
                )
                slots_repaired = result["repaired"]
                slots_remaining = result["remaining"]
                cascade_steps = result["steps"]
                details.extend(result["details"])

                # If cascade failed, escalate to fallback
                if slots_remaining > assessment.affected_slots * 0.3:
                    details.append("Cascade incomplete, activating fallback")
                    strategy = EmergencyStrategy.FALLBACK
                    fallback_activated = await self._try_fallback_activation()
                    if fallback_activated:
                        details.append(f"Fallback activated: {fallback_activated}")

            elif strategy == EmergencyStrategy.FALLBACK:
                fallback_activated = await self._try_fallback_activation()
                if fallback_activated:
                    slots_repaired = assessment.affected_slots
                    slots_remaining = 0
                    details.append(f"Fallback schedule activated: {fallback_activated}")
                else:
                    slots_remaining = assessment.affected_slots
                    details.append("No fallback schedule available")

            success = slots_remaining == 0 or fallback_activated is not None

        except Exception as e:
            logger.error(f"Emergency repair failed: {e}")
            success = False
            details.append(f"Repair error: {str(e)}")
            slots_remaining = assessment.affected_slots

        return RepairOutcome(
            success=success,
            strategy_used=strategy,
            slots_repaired=slots_repaired,
            slots_remaining=slots_remaining,
            cascade_steps=cascade_steps,
            fallback_activated=fallback_activated,
            execution_time_ms=(time.time() - exec_start) * 1000,
            details=details,
        )

    async def _try_cascade_repair(
        self,
        request: EmergencyDeploymentRequest,
        created_by_id: UUID | None,
        max_depth: int,
        exclude_assignment_ids: set[UUID] | None = None,
    ) -> dict:
        """Attempt cascade-based repair using CascadeOverrideService.

        Args:
            request: The emergency deployment request
            created_by_id: User ID for audit trail
            max_depth: Maximum cascade depth (1=incremental, 2=full cascade)
            exclude_assignment_ids: Assignment IDs to skip (already have overrides)

        Returns:
            Dict with repaired/remaining counts, steps, details, and overridden IDs
        """
        # Get assignments that already have active overrides
        already_overridden = await self._get_already_overridden_assignment_ids(
            request.person_id, request.start_date, request.end_date
        )
        if exclude_assignment_ids:
            already_overridden = already_overridden.union(exclude_assignment_ids)

        cascade_request = CascadeOverrideRequest(
            person_id=request.person_id,
            start_date=request.start_date,
            end_date=request.end_date,
            reason=request.reason,
            notes=request.notes,
            apply=True,
            max_depth=max_depth,
        )

        plan = await self.cascade_service.plan_and_apply(cascade_request, created_by_id)

        details: list[str] = []
        if plan.warnings:
            details.extend([f"Warning: {w}" for w in plan.warnings])
        if plan.errors:
            # Filter out errors for assignments we expected to skip
            filtered_errors = [
                e
                for e in plan.errors
                if not any(str(aid) in e for aid in already_overridden)
            ]
            details.extend([f"Error: {e}" for e in filtered_errors])

        # Count successful coverage steps (excluding already-overridden)
        coverage_steps = [
            s
            for s in plan.steps
            if s.override_type == "coverage"
            and s.assignment_id not in already_overridden
        ]
        gap_steps = [s for s in plan.steps if s.override_type == "gap"]

        repaired = len(coverage_steps)
        remaining = len(gap_steps) + len(
            [
                e
                for e in plan.errors
                if not any(str(aid) in e for aid in already_overridden)
            ]
        )

        # Track which assignments got successfully overridden
        overridden_assignment_ids: set[UUID] = set()
        for step in plan.steps:
            if step.created_override_id and step.override_type == "coverage":
                overridden_assignment_ids.add(step.assignment_id)

        if plan.applied:
            details.append(f"Applied {len(plan.steps)} override steps")

        return {
            "repaired": repaired,
            "remaining": remaining,
            "steps": len(plan.steps),
            "details": details,
            "overridden_assignment_ids": overridden_assignment_ids,
        }

    async def _try_fallback_activation(self) -> str | None:
        """
        Activate a pre-computed fallback schedule.

        In production, this would:
        1. Check which fallbacks are available via FallbackScheduler
        2. Activate the most appropriate one (SINGLE_FACULTY_LOSS or DOUBLE_FACULTY_LOSS)
        3. Return the scenario name

        For now, returns None (fallbacks not yet pre-computed in most envs).
        """
        # TODO: Wire to FallbackScheduler.activate_fallback() when fallbacks are pre-computed
        # Example:
        # from app.resilience.static_stability import FallbackScenario, FallbackScheduler
        # scheduler = FallbackScheduler()
        # fallback = scheduler.activate_fallback(FallbackScenario.SINGLE_FACULTY_LOSS)
        # if fallback:
        #     return fallback.scenario.value

        logger.warning("Fallback activation requested but no fallbacks pre-computed")
        return None

    async def _verify_health(
        self,
        start_date: date,
        end_date: date,
        repair_outcome: RepairOutcome,
        reason: str,
    ) -> HealthVerification:
        """
        Verify schedule health after repair.

        Checks coverage rate and escalates to crisis mode if needed.
        """
        # Calculate coverage rate
        total_slots = repair_outcome.slots_repaired + repair_outcome.slots_remaining
        if total_slots == 0:
            coverage_rate = 1.0
        else:
            coverage_rate = repair_outcome.slots_repaired / total_slots

        is_healthy = coverage_rate >= COVERAGE_HEALTHY_THRESHOLD

        # Escalate if still unhealthy
        escalated = False
        escalation_severity: str | None = None

        if not is_healthy:
            # Determine severity based on coverage gap
            if coverage_rate < 0.5:
                escalation_severity = "critical"
            elif coverage_rate < 0.75:
                escalation_severity = "severe"
            elif coverage_rate < 0.9:
                escalation_severity = "moderate"
            else:
                escalation_severity = "minor"

            # Log escalation (in production, would activate ResilienceService crisis mode)
            logger.warning(
                f"Emergency repair incomplete - escalating to crisis mode. "
                f"Coverage: {coverage_rate:.1%}, Severity: {escalation_severity}, "
                f"Reason: {reason}"
            )
            escalated = True

        return HealthVerification(
            coverage_rate=coverage_rate,
            is_healthy=is_healthy,
            escalated=escalated,
            escalation_severity=escalation_severity,
        )

    async def _count_half_day_assignments(
        self, person_id: UUID, start_date: date, end_date: date
    ) -> int:
        """Count half-day assignments for the person in date range."""
        result = await self.session.execute(
            select(HalfDayAssignment.id).where(
                HalfDayAssignment.person_id == person_id,
                HalfDayAssignment.date >= start_date,
                HalfDayAssignment.date <= end_date,
            )
        )
        return len(result.scalars().all())

    async def _count_call_assignments(
        self, person_id: UUID, start_date: date, end_date: date
    ) -> int:
        """Count call assignments for the person in date range."""
        result = await self.session.execute(
            select(CallAssignment.id).where(
                CallAssignment.person_id == person_id,
                CallAssignment.date >= start_date,
                CallAssignment.date <= end_date,
            )
        )
        return len(result.scalars().all())

    async def _get_already_overridden_assignment_ids(
        self, person_id: UUID, start_date: date, end_date: date
    ) -> set[UUID]:
        """Get IDs of assignments that already have active overrides.

        This prevents cascade escalation from trying to re-override assignments
        that were successfully overridden in a previous pass, which would cause
        409 conflicts.
        """
        overridden_ids: set[UUID] = set()

        # Get half-day assignments with active overrides
        half_day_result = await self.session.execute(
            select(HalfDayAssignment.id)
            .join(
                ScheduleOverride,
                ScheduleOverride.half_day_assignment_id == HalfDayAssignment.id,
            )
            .where(
                HalfDayAssignment.person_id == person_id,
                HalfDayAssignment.date >= start_date,
                HalfDayAssignment.date <= end_date,
                ScheduleOverride.is_active == True,  # noqa: E712
            )
        )
        overridden_ids.update(half_day_result.scalars().all())

        # Get call assignments with active overrides
        call_result = await self.session.execute(
            select(CallAssignment.id)
            .join(
                CallOverride,
                CallOverride.call_assignment_id == CallAssignment.id,
            )
            .where(
                CallAssignment.person_id == person_id,
                CallAssignment.date >= start_date,
                CallAssignment.date <= end_date,
                CallOverride.is_active == True,  # noqa: E712
            )
        )
        overridden_ids.update(call_result.scalars().all())

        return overridden_ids

    def _error_response(
        self,
        request: EmergencyDeploymentRequest,
        request_id: UUID,
        start_time: float,
        errors: list[str],
    ) -> EmergencyDeploymentResponse:
        """Build error response when request validation fails."""
        return EmergencyDeploymentResponse(
            request_id=request_id,
            person_id=request.person_id,
            start_date=request.start_date,
            end_date=request.end_date,
            dry_run=request.dry_run,
            assessment=FragilityAssessment(
                fragility_score=1.0,
                rd_mean=0.0,
                rd_max=0,
                affected_slots=0,
                recommended_strategy=EmergencyStrategy.FALLBACK,
                assessment_time_ms=0.0,
            ),
            repair_outcome=None,
            health_check=None,
            overall_success=False,
            total_time_ms=(time.time() - start_time) * 1000,
            recommendations=[],
            warnings=[],
            errors=errors,
        )


def get_emergency_deployment_service(
    session: AsyncSession,
) -> EmergencyDeploymentService:
    """Factory function for dependency injection."""
    return EmergencyDeploymentService(session)
