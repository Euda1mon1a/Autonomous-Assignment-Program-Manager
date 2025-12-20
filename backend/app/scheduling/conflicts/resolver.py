"""
Conflict Resolution Suggestion Generator.

This module provides intelligent suggestions for resolving detected conflicts.
It analyzes conflicts and proposes resolution strategies with impact assessments.
"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.scheduling.conflicts.types import (
    ACGMEViolationConflict,
    Conflict,
    ConflictType,
    ResourceContentionConflict,
    SupervisionConflict,
    TimeOverlapConflict,
)

logger = logging.getLogger(__name__)


class ResolutionSuggestion:
    """A suggested resolution for a conflict."""

    def __init__(
        self,
        suggestion_id: str,
        strategy: str,
        title: str,
        description: str,
        steps: list[str],
        impact: dict[str, Any],
        confidence: float,
        estimated_time_minutes: int,
        requires_approval: bool = True,
    ):
        """
        Initialize a resolution suggestion.

        Args:
            suggestion_id: Unique identifier
            strategy: Strategy type (e.g., "reassign", "swap", "add_faculty")
            title: Brief title
            description: Detailed description
            steps: List of steps to execute
            impact: Impact assessment dict
            confidence: Confidence in this solution (0-1)
            estimated_time_minutes: Estimated time to implement
            requires_approval: Whether human approval is needed
        """
        self.suggestion_id = suggestion_id
        self.strategy = strategy
        self.title = title
        self.description = description
        self.steps = steps
        self.impact = impact
        self.confidence = confidence
        self.estimated_time_minutes = estimated_time_minutes
        self.requires_approval = requires_approval


class ConflictResolver:
    """
    Conflict resolution suggestion generator.

    Analyzes conflicts and proposes resolution strategies with
    detailed implementation steps and impact assessments.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the conflict resolver.

        Args:
            db: Async database session
        """
        self.db = db

    async def suggest_resolutions(
        self,
        conflict: Conflict,
        max_suggestions: int = 5,
    ) -> list[ResolutionSuggestion]:
        """
        Generate resolution suggestions for a conflict.

        Args:
            conflict: The conflict to resolve
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of resolution suggestions, sorted by confidence
        """
        logger.info(f"Generating resolutions for conflict {conflict.conflict_id}")

        suggestions: list[ResolutionSuggestion] = []

        # Route to specific handlers based on conflict type
        if isinstance(conflict, TimeOverlapConflict):
            suggestions = await self._resolve_time_overlap(conflict)
        elif isinstance(conflict, SupervisionConflict):
            suggestions = await self._resolve_supervision_issue(conflict)
        elif isinstance(conflict, ACGMEViolationConflict):
            suggestions = await self._resolve_acgme_violation(conflict)
        elif isinstance(conflict, ResourceContentionConflict):
            suggestions = await self._resolve_resource_contention(conflict)
        else:
            # Generic suggestions
            suggestions = await self._generic_resolutions(conflict)

        # Sort by confidence and return top suggestions
        suggestions.sort(key=lambda s: s.confidence, reverse=True)
        return suggestions[:max_suggestions]

    async def _resolve_time_overlap(
        self,
        conflict: TimeOverlapConflict,
    ) -> list[ResolutionSuggestion]:
        """
        Suggest resolutions for time overlap conflicts.

        Args:
            conflict: Time overlap conflict

        Returns:
            List of resolution suggestions
        """
        suggestions = []

        # Strategy 1: Cancel one assignment
        if len(conflict.overlapping_assignment_ids) == 2:
            suggestions.append(
                ResolutionSuggestion(
                    suggestion_id=f"{conflict.conflict_id}_cancel",
                    strategy="cancel_assignment",
                    title="Cancel One Assignment",
                    description="Remove one of the overlapping assignments to eliminate conflict",
                    steps=[
                        "Review both assignments to determine which is less critical",
                        "Cancel the lower-priority assignment",
                        "Verify no coverage gaps are created",
                        "Notify affected parties",
                    ],
                    impact={
                        "affected_people": len(conflict.affected_people),
                        "disruption_level": "low",
                        "coverage_risk": "medium",
                    },
                    confidence=0.8,
                    estimated_time_minutes=10,
                    requires_approval=True,
                )
            )

        # Strategy 2: Reassign to different person
        suggestions.append(
            ResolutionSuggestion(
                suggestion_id=f"{conflict.conflict_id}_reassign",
                strategy="reassign_to_other",
                title="Reassign to Different Person",
                description="Move one assignment to a different available person",
                steps=[
                    "Identify available person with compatible qualifications",
                    "Verify ACGME compliance with reassignment",
                    "Update assignment to new person",
                    "Verify supervision ratios are maintained",
                    "Notify all affected parties",
                ],
                impact={
                    "affected_people": 2,  # Original + replacement
                    "disruption_level": "medium",
                    "coverage_risk": "low",
                },
                confidence=0.7,
                estimated_time_minutes=20,
                requires_approval=True,
            )
        )

        # Strategy 3: Split assignment
        if conflict.overlap_duration_hours >= 6.0:
            suggestions.append(
                ResolutionSuggestion(
                    suggestion_id=f"{conflict.conflict_id}_split",
                    strategy="split_coverage",
                    title="Split Block Coverage",
                    description="Divide the block between multiple people",
                    steps=[
                        "Determine optimal split point in block",
                        "Assign first half to person A",
                        "Assign second half to person B",
                        "Ensure handoff procedures are in place",
                        "Update documentation",
                    ],
                    impact={
                        "affected_people": 2,
                        "disruption_level": "medium",
                        "coverage_risk": "low",
                    },
                    confidence=0.6,
                    estimated_time_minutes=30,
                    requires_approval=True,
                )
            )

        return suggestions

    async def _resolve_supervision_issue(
        self,
        conflict: SupervisionConflict,
    ) -> list[ResolutionSuggestion]:
        """
        Suggest resolutions for supervision issues.

        Args:
            conflict: Supervision conflict

        Returns:
            List of resolution suggestions
        """
        suggestions = []

        faculty_deficit = conflict.required_faculty_count - conflict.faculty_count

        # Strategy 1: Add faculty
        suggestions.append(
            ResolutionSuggestion(
                suggestion_id=f"{conflict.conflict_id}_add_faculty",
                strategy="add_faculty",
                title=f"Assign {faculty_deficit} Additional Faculty",
                description=f"Add {faculty_deficit} faculty member(s) to meet supervision requirements",
                steps=[
                    "Identify available faculty for the block",
                    "Verify faculty qualifications and availability",
                    f"Create {faculty_deficit} new faculty assignment(s)",
                    "Verify supervision ratios are now compliant",
                    "Notify faculty of new assignment",
                ],
                impact={
                    "affected_people": faculty_deficit,
                    "disruption_level": "low",
                    "coverage_risk": "low",
                    "acgme_impact": "resolves_violation",
                },
                confidence=0.85,
                estimated_time_minutes=15,
                requires_approval=True,
            )
        )

        # Strategy 2: Reduce resident count
        if conflict.pgy2_3_count > 0:
            suggestions.append(
                ResolutionSuggestion(
                    suggestion_id=f"{conflict.conflict_id}_reduce_residents",
                    strategy="reduce_residents",
                    title="Reassign Some Residents",
                    description="Move residents to other blocks to reduce supervision burden",
                    steps=[
                        "Identify residents who can be reassigned",
                        "Find alternative blocks for reassignment",
                        "Update resident assignments",
                        "Verify new blocks have adequate supervision",
                        "Verify coverage is maintained",
                    ],
                    impact={
                        "affected_people": conflict.pgy2_3_count,
                        "disruption_level": "high",
                        "coverage_risk": "medium",
                        "acgme_impact": "resolves_violation",
                    },
                    confidence=0.6,
                    estimated_time_minutes=45,
                    requires_approval=True,
                )
            )

        # Strategy 3: Use backup faculty
        suggestions.append(
            ResolutionSuggestion(
                suggestion_id=f"{conflict.conflict_id}_backup_faculty",
                strategy="escalate_to_backup",
                title="Activate Backup Faculty",
                description="Contact backup/on-call faculty to provide supervision",
                steps=[
                    "Identify backup faculty on call roster",
                    "Contact backup faculty to confirm availability",
                    "Create backup faculty assignment",
                    "Update supervision tracking",
                    "Document backup activation",
                ],
                impact={
                    "affected_people": 1,
                    "disruption_level": "medium",
                    "coverage_risk": "low",
                    "acgme_impact": "resolves_violation",
                },
                confidence=0.75,
                estimated_time_minutes=20,
                requires_approval=False,  # Backup activation is standard procedure
            )
        )

        return suggestions

    async def _resolve_acgme_violation(
        self,
        conflict: ACGMEViolationConflict,
    ) -> list[ResolutionSuggestion]:
        """
        Suggest resolutions for ACGME violations.

        Args:
            conflict: ACGME violation conflict

        Returns:
            List of resolution suggestions
        """
        suggestions = []

        if conflict.conflict_type == ConflictType.EIGHTY_HOUR_VIOLATION:
            # 80-hour violation resolutions
            suggestions.append(
                ResolutionSuggestion(
                    suggestion_id=f"{conflict.conflict_id}_reduce_hours",
                    strategy="reduce_assignments",
                    title="Reduce Assignment Load",
                    description=f"Remove {conflict.excess_amount:.1f} hours of assignments to meet 80-hour limit",
                    steps=[
                        f"Identify {conflict.excess_amount:.1f} hours of assignments to remove",
                        "Find replacement coverage for removed assignments",
                        "Update schedule to remove excess assignments",
                        "Verify resident is now under 80-hour limit",
                        "Redistribute workload among team",
                    ],
                    impact={
                        "affected_people": 1,
                        "hours_reduced": conflict.excess_amount,
                        "disruption_level": "high",
                        "coverage_risk": "high",
                        "acgme_impact": "resolves_violation",
                    },
                    confidence=0.7,
                    estimated_time_minutes=60,
                    requires_approval=True,
                )
            )

            suggestions.append(
                ResolutionSuggestion(
                    suggestion_id=f"{conflict.conflict_id}_redistribute",
                    strategy="redistribute_workload",
                    title="Redistribute to Other Residents",
                    description="Balance workload across multiple residents",
                    steps=[
                        "Identify other residents with capacity",
                        "Calculate optimal distribution",
                        "Reassign blocks to balance hours",
                        "Verify all residents meet ACGME limits",
                        "Update and communicate schedule changes",
                    ],
                    impact={
                        "affected_people": 3,  # Usually affects 2-3 residents
                        "disruption_level": "medium",
                        "coverage_risk": "low",
                        "acgme_impact": "resolves_violation",
                    },
                    confidence=0.8,
                    estimated_time_minutes=45,
                    requires_approval=True,
                )
            )

        elif conflict.conflict_type == ConflictType.ONE_IN_SEVEN_VIOLATION:
            # 1-in-7 violation resolutions
            suggestions.append(
                ResolutionSuggestion(
                    suggestion_id=f"{conflict.conflict_id}_add_day_off",
                    strategy="insert_day_off",
                    title="Insert Mandatory Day Off",
                    description="Add a day off within the consecutive work period",
                    steps=[
                        "Identify best day to insert off day (lowest impact)",
                        "Find coverage for that day",
                        "Remove resident's assignments for selected day",
                        "Verify 1-in-7 compliance is restored",
                        "Notify resident and team of schedule change",
                    ],
                    impact={
                        "affected_people": 2,  # Resident + replacement
                        "disruption_level": "medium",
                        "coverage_risk": "medium",
                        "acgme_impact": "resolves_violation",
                    },
                    confidence=0.75,
                    estimated_time_minutes=30,
                    requires_approval=True,
                )
            )

        return suggestions

    async def _resolve_resource_contention(
        self,
        conflict: ResourceContentionConflict,
    ) -> list[ResolutionSuggestion]:
        """
        Suggest resolutions for resource contention.

        Args:
            conflict: Resource contention conflict

        Returns:
            List of resolution suggestions
        """
        suggestions = []

        # Generic resource allocation suggestion
        suggestions.append(
            ResolutionSuggestion(
                suggestion_id=f"{conflict.conflict_id}_allocate",
                strategy="allocate_resource",
                title=f"Allocate Additional {conflict.resource_type}",
                description=f"Acquire {conflict.deficit} additional {conflict.resource_type}",
                steps=[
                    f"Identify available {conflict.resource_type}",
                    "Request allocation through proper channels",
                    "Update resource assignments",
                    "Verify conflict is resolved",
                ],
                impact={
                    "affected_people": len(conflict.affected_people),
                    "disruption_level": "low",
                    "coverage_risk": "low",
                },
                confidence=0.6,
                estimated_time_minutes=30,
                requires_approval=True,
            )
        )

        return suggestions

    async def _generic_resolutions(
        self,
        conflict: Conflict,
    ) -> list[ResolutionSuggestion]:
        """
        Generate generic resolution suggestions.

        Used when no specific handler exists for the conflict type.

        Args:
            conflict: The conflict to resolve

        Returns:
            List of generic resolution suggestions
        """
        suggestions = []

        # Manual review suggestion (always available)
        suggestions.append(
            ResolutionSuggestion(
                suggestion_id=f"{conflict.conflict_id}_manual",
                strategy="manual_review",
                title="Manual Review Required",
                description="This conflict requires manual review and resolution",
                steps=[
                    "Review conflict details and context",
                    "Consult with scheduling coordinator",
                    "Identify appropriate resolution strategy",
                    "Implement changes manually",
                    "Verify conflict is resolved",
                ],
                impact={
                    "affected_people": len(conflict.affected_people),
                    "disruption_level": "unknown",
                    "coverage_risk": "unknown",
                },
                confidence=0.5,
                estimated_time_minutes=60,
                requires_approval=True,
            )
        )

        return suggestions

    async def assess_impact(
        self,
        suggestion: ResolutionSuggestion,
        conflict: Conflict,
    ) -> dict[str, Any]:
        """
        Perform detailed impact assessment for a resolution suggestion.

        Args:
            suggestion: The resolution suggestion to assess
            conflict: The conflict being resolved

        Returns:
            Detailed impact assessment
        """
        assessment = {
            "suggestion_id": suggestion.suggestion_id,
            "conflict_id": conflict.conflict_id,
            "estimated_time_minutes": suggestion.estimated_time_minutes,
            "confidence": suggestion.confidence,
            "requires_approval": suggestion.requires_approval,
            **suggestion.impact,
        }

        # Add complexity score
        complexity_factors = 0
        if suggestion.impact.get("affected_people", 0) > 3:
            complexity_factors += 1
        if suggestion.impact.get("disruption_level") == "high":
            complexity_factors += 1
        if suggestion.impact.get("coverage_risk") in ["high", "medium"]:
            complexity_factors += 1

        assessment["complexity_score"] = min(complexity_factors / 3.0, 1.0)

        # Add feasibility score
        feasibility = 1.0
        if suggestion.impact.get("coverage_risk") == "high":
            feasibility -= 0.3
        if suggestion.estimated_time_minutes > 60:
            feasibility -= 0.2

        assessment["feasibility_score"] = max(feasibility, 0.0)

        return assessment
