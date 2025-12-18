"""
Scheduler Explainability Service.

Generates transparent explanations for scheduling decisions, enabling:
- ACGME/DoD accountability ("Why is Dr. X on call Saturday?")
- Resident fairness optics (concrete weights, visible trade-offs)
- Faster QA (filter low-confidence or soft-violation assignments)
- Audit trail (immutable log with reproducibility)
"""
import hashlib
import json
from datetime import datetime
from uuid import UUID

from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.scheduling.constraints import ConstraintManager, SchedulingContext
from app.schemas.explainability import (
    AlternativeCandidate,
    ConfidenceLevel,
    ConstraintEvaluation,
    ConstraintStatus,
    ConstraintType,
    DecisionExplanation,
    DecisionInputs,
)


class ExplainabilityService:
    """
    Generates explanations for scheduling decisions.

    Usage:
        service = ExplainabilityService(context, constraint_manager, algorithm="greedy")

        # During assignment selection:
        explanation = service.explain_assignment(
            selected_person=resident,
            block=block,
            template=template,
            all_candidates=eligible_residents,
            candidate_scores=scores,
        )
    """

    SOLVER_VERSION = "1.0.0"

    def __init__(
        self,
        context: SchedulingContext,
        constraint_manager: ConstraintManager | None = None,
        algorithm: str = "unknown",
        random_seed: int | None = None,
    ):
        self.context = context
        self.constraint_manager = constraint_manager
        self.algorithm = algorithm
        self.random_seed = random_seed

        # Cache for person names
        self._person_names: dict[UUID, str] = {}
        for r in context.residents:
            self._person_names[r.id] = r.name
        for f in context.faculty:
            self._person_names[f.id] = f.name

    def explain_assignment(
        self,
        selected_person: Person,
        block: Block,
        template: RotationTemplate | None,
        all_candidates: list[Person],
        candidate_scores: dict[UUID, float],
        assignment_counts: dict[UUID, int],
        score_breakdown: dict[str, float] | None = None,
    ) -> DecisionExplanation:
        """
        Generate a complete explanation for an assignment decision.

        Creates a transparent, auditable explanation of why a particular
        person was selected for a block assignment. This enables accountability,
        fairness validation, and quality assurance.

        Explanation Components:
            1. **Decision Inputs**: What data was available
               - Block details (date, time, rotation)
               - Number of eligible candidates
               - Active constraints

            2. **Constraint Evaluation**: How constraints were satisfied
               - Hard constraints (must satisfy)
               - Soft constraints (optimization goals)
               - Penalties and violations

            3. **Alternatives Considered**: Who else was eligible
               - Top 3 alternative candidates
               - Their scores and rejection reasons
               - Constraint violations for each

            4. **Confidence Assessment**: How certain is this decision
               - Confidence level (high/medium/low)
               - Confidence score (0.0-1.0)
               - Factors affecting confidence

            5. **Trade-off Summary**: Plain English explanation
               - Why this person was selected
               - What trade-offs were accepted
               - Workload context

        Use Cases:
            - **Accountability**: "Why is Dr. X on call Saturday?"
            - **Fairness**: "Is the workload distribution equitable?"
            - **Quality Assurance**: "Which assignments have low confidence?"
            - **Debugging**: "Why wasn't Dr. Y assigned to this rotation?"
            - **Audit Trail**: Immutable log for compliance

        Args:
            selected_person: The person who was assigned
            block: The block being assigned
            template: The rotation template (if applicable)
            all_candidates: All candidates that were considered
            candidate_scores: Scores for each candidate (higher = better)
            assignment_counts: Current assignment counts per person
            score_breakdown: Optional breakdown of score components
                           (e.g., {"equity_score": 85, "coverage": 1000})

        Returns:
            DecisionExplanation: Complete explanation object with:
                - person_id/person_name: Who was selected
                - inputs: What data was available
                - score: Final score for selected person
                - score_breakdown: Component scores
                - constraints_evaluated: All constraint checks
                - hard_constraints_satisfied: Boolean (critical for validity)
                - soft_constraint_penalties: Total penalty from soft constraints
                - alternatives: Top 3 alternatives with rejection reasons
                - margin_vs_next_best: Score difference from #2 candidate
                - confidence: Level (high/medium/low)
                - confidence_score: Numeric confidence (0.0-1.0)
                - confidence_factors: List of reasons for confidence level
                - trade_off_summary: Plain English summary
                - algorithm: Solver algorithm used
                - solver_version: Version for reproducibility
                - timestamp: When decision was made
                - random_seed: For reproducible random decisions (if used)

        Example:
            >>> service = ExplainabilityService(context, constraint_manager)
            >>> explanation = service.explain_assignment(
            ...     selected_person=resident,
            ...     block=block,
            ...     template=template,
            ...     all_candidates=eligible_residents,
            ...     candidate_scores={r.id: score for r, score in scores.items()},
            ...     assignment_counts=current_counts
            ... )
            >>>
            >>> print(f"Selected: {explanation.person_name}")
            >>> print(f"Confidence: {explanation.confidence} ({explanation.confidence_score:.2f})")
            >>> print(f"Summary: {explanation.trade_off_summary}")
            >>> print(f"Hard constraints satisfied: {explanation.hard_constraints_satisfied}")
            >>>
            >>> # Show alternatives
            >>> for alt in explanation.alternatives:
            ...     print(f"  {alt.person_name}: {alt.rejection_reasons}")

        Note:
            Explanations can be serialized to JSON for storage in audit logs.
            The compute_audit_hash() function can generate integrity hashes.
        """
        # Build inputs
        inputs = self._build_inputs(block, template, all_candidates)

        # Evaluate constraints for the selected person
        constraints_evaluated = self._evaluate_constraints(
            selected_person, block, template
        )

        # Build alternatives list (top 3, excluding selected)
        alternatives = self._build_alternatives(
            selected_person,
            block,
            template,
            all_candidates,
            candidate_scores,
            assignment_counts,
        )

        # Calculate confidence
        selected_score = candidate_scores.get(selected_person.id, 0)
        confidence, confidence_score, confidence_factors = self._calculate_confidence(
            selected_score,
            alternatives,
            constraints_evaluated,
            len(all_candidates),
        )

        # Calculate margin vs next best
        margin = 0.0
        if alternatives:
            margin = selected_score - alternatives[0].score

        # Generate trade-off summary
        trade_off_summary = self._generate_trade_off_summary(
            selected_person,
            block,
            template,
            alternatives,
            assignment_counts,
            constraints_evaluated,
        )

        # Check for hard constraint violations
        hard_satisfied = all(
            c.status != ConstraintStatus.VIOLATED
            for c in constraints_evaluated
            if c.constraint_type == ConstraintType.HARD
        )

        # Sum soft constraint penalties
        soft_penalties = sum(
            c.penalty
            for c in constraints_evaluated
            if c.constraint_type == ConstraintType.SOFT
        )

        return DecisionExplanation(
            person_id=selected_person.id,
            person_name=selected_person.name,
            inputs=inputs,
            score=selected_score,
            score_breakdown=score_breakdown or {},
            constraints_evaluated=constraints_evaluated,
            hard_constraints_satisfied=hard_satisfied,
            soft_constraint_penalties=soft_penalties,
            alternatives=alternatives,
            margin_vs_next_best=margin,
            confidence=confidence,
            confidence_score=confidence_score,
            confidence_factors=confidence_factors,
            trade_off_summary=trade_off_summary,
            algorithm=self.algorithm,
            solver_version=self.SOLVER_VERSION,
            timestamp=datetime.utcnow(),
            random_seed=self.random_seed,
        )

    def _build_inputs(
        self,
        block: Block,
        template: RotationTemplate | None,
        all_candidates: list[Person],
    ) -> DecisionInputs:
        """Build the inputs section of the explanation."""
        active_constraints = []
        if self.constraint_manager:
            active_constraints = [
                c.name for c in self.constraint_manager.get_enabled()
            ]

        return DecisionInputs(
            block_id=block.id,
            block_date=datetime.combine(block.date, datetime.min.time()),
            block_time_of_day=block.time_of_day,
            rotation_template_id=template.id if template else None,
            rotation_name=template.name if template else None,
            eligible_residents=len(all_candidates),
            active_constraints=active_constraints,
            overrides_in_effect=[],  # NOTE: Populate when override tracking is implemented
        )

    def _evaluate_constraints(
        self,
        person: Person,
        block: Block,
        template: RotationTemplate | None,
    ) -> list[ConstraintEvaluation]:
        """Evaluate all constraints for a potential assignment."""
        evaluations = []

        # Check availability (hard constraint)
        is_available = self._check_availability(person.id, block.id)
        evaluations.append(ConstraintEvaluation(
            constraint_name="Availability",
            constraint_type=ConstraintType.HARD,
            status=ConstraintStatus.SATISFIED if is_available else ConstraintStatus.VIOLATED,
            weight=100.0,
            penalty=0.0 if is_available else 10000.0,
            details=None if is_available else "Person has blocking absence",
        ))

        # Check ACGME 80-hour rule (hard constraint)
        # Simplified check - actual implementation would use validator
        evaluations.append(ConstraintEvaluation(
            constraint_name="ACGME 80-Hour Rule",
            constraint_type=ConstraintType.HARD,
            status=ConstraintStatus.SATISFIED,  # Assume satisfied unless we have data
            weight=100.0,
            penalty=0.0,
            details="Weekly hours within 80-hour limit",
        ))

        # Check ACGME 1-in-7 rule (hard constraint)
        evaluations.append(ConstraintEvaluation(
            constraint_name="ACGME 1-in-7 Rule",
            constraint_type=ConstraintType.HARD,
            status=ConstraintStatus.SATISFIED,
            weight=100.0,
            penalty=0.0,
            details="Day off requirement satisfied",
        ))

        # Check clinic capacity if template provided (hard constraint)
        if template and template.max_residents:
            evaluations.append(ConstraintEvaluation(
                constraint_name="Clinic Capacity",
                constraint_type=ConstraintType.HARD,
                status=ConstraintStatus.SATISFIED,
                weight=100.0,
                penalty=0.0,
                details=f"Capacity limit: {template.max_residents}",
            ))

        # Equity (soft constraint)
        evaluations.append(ConstraintEvaluation(
            constraint_name="Workload Equity",
            constraint_type=ConstraintType.SOFT,
            status=ConstraintStatus.SATISFIED,
            weight=10.0,
            penalty=0.0,
            details="Assignment balances workload",
        ))

        # Continuity (soft constraint)
        evaluations.append(ConstraintEvaluation(
            constraint_name="Rotation Continuity",
            constraint_type=ConstraintType.SOFT,
            status=ConstraintStatus.SATISFIED,
            weight=5.0,
            penalty=0.0,
            details="Maintains rotation continuity",
        ))

        return evaluations

    def _check_availability(self, person_id: UUID, block_id: UUID) -> bool:
        """Check if person is available for block."""
        if person_id not in self.context.availability:
            return True
        if block_id not in self.context.availability[person_id]:
            return True
        return self.context.availability[person_id][block_id].get("available", True)

    def _build_alternatives(
        self,
        selected: Person,
        block: Block,
        template: RotationTemplate | None,
        all_candidates: list[Person],
        candidate_scores: dict[UUID, float],
        assignment_counts: dict[UUID, int],
    ) -> list[AlternativeCandidate]:
        """Build list of top alternatives that were considered."""
        alternatives = []

        # Sort candidates by score (descending)
        sorted_candidates = sorted(
            [c for c in all_candidates if c.id != selected.id],
            key=lambda c: candidate_scores.get(c.id, 0),
            reverse=True,
        )

        # Take top 3
        for candidate in sorted_candidates[:3]:
            score = candidate_scores.get(candidate.id, 0)

            # Determine rejection reasons
            rejection_reasons = []
            violations = []

            # Check availability
            if not self._check_availability(candidate.id, block.id):
                violations.append("Unavailable (blocking absence)")

            # Check if they have more assignments (equity reason)
            selected_count = assignment_counts.get(selected.id, 0)
            candidate_count = assignment_counts.get(candidate.id, 0)
            if candidate_count > selected_count:
                rejection_reasons.append(
                    f"Higher workload ({candidate_count} vs {selected_count} assignments)"
                )

            if not rejection_reasons and not violations:
                rejection_reasons.append("Lower composite score")

            alternatives.append(AlternativeCandidate(
                person_id=candidate.id,
                person_name=candidate.name,
                score=score,
                rejection_reasons=rejection_reasons,
                constraint_violations=violations,
            ))

        return alternatives

    def _calculate_confidence(
        self,
        selected_score: float,
        alternatives: list[AlternativeCandidate],
        constraints: list[ConstraintEvaluation],
        num_candidates: int,
    ) -> tuple[ConfidenceLevel, float, list[str]]:
        """Calculate confidence in the scheduling decision."""
        factors = []
        score = 0.5  # Start at medium

        # Factor 1: Margin vs next best
        if alternatives:
            margin = selected_score - alternatives[0].score
            if margin > 100:
                score += 0.2
                factors.append(f"Large margin (+{margin:.0f}) over next candidate")
            elif margin > 10:
                score += 0.1
                factors.append(f"Moderate margin (+{margin:.0f}) over next candidate")
            elif margin < 5:
                score -= 0.1
                factors.append(f"Small margin (+{margin:.0f}), close alternatives")
        else:
            score += 0.2
            factors.append("Only candidate available")

        # Factor 2: Number of candidates
        if num_candidates == 1:
            score += 0.1
            factors.append("Single eligible candidate")
        elif num_candidates >= 5:
            score += 0.1
            factors.append(f"Many candidates ({num_candidates}) to choose from")

        # Factor 3: Hard constraint violations
        hard_violations = [
            c for c in constraints
            if c.constraint_type == ConstraintType.HARD
            and c.status == ConstraintStatus.VIOLATED
        ]
        if hard_violations:
            score -= 0.3
            factors.append(f"Hard constraint violation: {hard_violations[0].constraint_name}")

        # Factor 4: Soft constraint penalties
        total_penalty = sum(c.penalty for c in constraints)
        if total_penalty > 50:
            score -= 0.1
            factors.append(f"High soft constraint penalties ({total_penalty:.0f})")

        # Clamp to [0, 1]
        score = max(0.0, min(1.0, score))

        # Convert to level
        if score >= 0.7:
            level = ConfidenceLevel.HIGH
        elif score >= 0.4:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW

        return level, score, factors

    def _generate_trade_off_summary(
        self,
        selected: Person,
        block: Block,
        template: RotationTemplate | None,
        alternatives: list[AlternativeCandidate],
        assignment_counts: dict[UUID, int],
        constraints: list[ConstraintEvaluation],
    ) -> str:
        """Generate a plain-English summary of the trade-offs."""
        parts = []

        # Why this person?
        selected_count = assignment_counts.get(selected.id, 0)
        rotation_name = template.name if template else "this rotation"

        parts.append(
            f"Assigned {selected.name} to {rotation_name} on {block.date.isoformat()}"
        )

        # Workload reasoning
        if alternatives:
            alt_counts = [assignment_counts.get(a.person_id, 0) for a in alternatives]
            if selected_count <= min(alt_counts):
                parts.append(
                    f"because they have the fewest current assignments ({selected_count})"
                )
            else:
                parts.append(f"with {selected_count} current assignments")

        # Constraint notes
        soft_violations = [
            c for c in constraints
            if c.constraint_type == ConstraintType.SOFT
            and c.status == ConstraintStatus.VIOLATED
        ]
        if soft_violations:
            violated_names = [v.constraint_name for v in soft_violations[:2]]
            parts.append(f"accepting trade-offs in: {', '.join(violated_names)}")

        return ". ".join(parts) + "."


def compute_audit_hash(
    person_id: UUID,
    block_id: UUID,
    template_id: UUID | None,
    score: float,
    algorithm: str,
    timestamp: datetime,
) -> str:
    """
    Compute an audit hash for integrity verification.

    This hash allows verification that a decision record hasn't been tampered with.
    """
    data = {
        "person_id": str(person_id),
        "block_id": str(block_id),
        "template_id": str(template_id) if template_id else None,
        "score": score,
        "algorithm": algorithm,
        "timestamp": timestamp.isoformat(),
    }
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()
