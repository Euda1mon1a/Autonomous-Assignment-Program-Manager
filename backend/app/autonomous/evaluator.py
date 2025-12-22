"""
Strict Evaluator with Numeric Scoring.

This is the line that makes autonomy possible. Without deterministic scoring,
the system cannot compute "better vs worse" and therefore cannot self-improve.

Responsibilities:
    - Hard constraints: pass/fail with specific violation objects
    - Soft constraints: numeric score with weighted components
    - Deterministic: same inputs always produce same outputs
    - Machine-readable: structured output for feedback into loop

The evaluator wraps existing ACGME validation and resilience checks,
but adds a unified numeric score that the control loop can optimize.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.scheduling.validator import ACGMEValidator
from app.resilience.service import ResilienceService, ResilienceConfig


class ViolationSeverity(str, Enum):
    """Severity levels for constraint violations."""

    CRITICAL = "critical"  # ACGME violations, must fix
    HIGH = "high"          # Serious issues, should fix
    MEDIUM = "medium"      # Minor issues, good to address
    LOW = "low"            # Preferences not met


@dataclass
class ViolationDetail:
    """
    Detailed information about a single constraint violation.

    Attributes:
        type: Violation type identifier (e.g., "80_HOUR_VIOLATION")
        severity: How serious the violation is
        message: Human-readable description
        person_id: Affected person if applicable
        block_id: Affected block if applicable
        details: Additional structured data
        penalty: Numeric penalty applied to score
    """

    type: str
    severity: ViolationSeverity
    message: str
    person_id: UUID | None = None
    block_id: UUID | None = None
    details: dict[str, Any] = field(default_factory=dict)
    penalty: float = 0.0


@dataclass
class ScoreComponent:
    """
    A single component of the overall score.

    Attributes:
        name: Component identifier
        weight: Weight in overall score (0.0-1.0)
        raw_value: Unweighted value (0.0-1.0 where 1.0 is perfect)
        weighted_value: raw_value * weight
        details: Explanation of how value was computed
    """

    name: str
    weight: float
    raw_value: float
    weighted_value: float = 0.0
    details: str = ""

    def __post_init__(self):
        self.weighted_value = self.raw_value * self.weight


@dataclass
class EvaluationResult:
    """
    Complete evaluation result with numeric score and structured violations.

    This is the primary output of the evaluator. The control loop uses
    the `score` field to determine if one candidate is better than another.
    The `violations` list provides structured feedback for parameter adaptation.

    Attributes:
        valid: True if all hard constraints are satisfied
        score: Overall score (0.0-1.0 where 1.0 is perfect)
        hard_constraint_pass: True if schedule is ACGME compliant
        soft_score: Score from soft constraints only
        coverage_rate: Percentage of blocks assigned (0.0-1.0)
        total_violations: Count of all violations
        critical_violations: Count of severity=CRITICAL violations
        violations: List of all violations with details
        components: Breakdown of score by component
        metrics: Additional metrics for reporting

    Score Interpretation:
        - 1.0: Perfect schedule (rare in practice)
        - 0.9+: Excellent, minor soft constraint violations only
        - 0.8-0.9: Good, acceptable for production
        - 0.7-0.8: Fair, some issues to address
        - 0.6-0.7: Poor, significant issues
        - <0.6: Unacceptable, major rework needed
        - 0.0: Hard constraints violated (invalid)
    """

    valid: bool
    score: float
    hard_constraint_pass: bool
    soft_score: float
    coverage_rate: float
    total_violations: int
    critical_violations: int
    violations: list[ViolationDetail] = field(default_factory=list)
    components: list[ScoreComponent] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "valid": self.valid,
            "score": self.score,
            "hard_constraint_pass": self.hard_constraint_pass,
            "soft_score": self.soft_score,
            "coverage_rate": self.coverage_rate,
            "total_violations": self.total_violations,
            "critical_violations": self.critical_violations,
            "violations": [
                {
                    "type": v.type,
                    "severity": v.severity.value,
                    "message": v.message,
                    "person_id": str(v.person_id) if v.person_id else None,
                    "block_id": str(v.block_id) if v.block_id else None,
                    "details": v.details,
                    "penalty": v.penalty,
                }
                for v in self.violations
            ],
            "components": [
                {
                    "name": c.name,
                    "weight": c.weight,
                    "raw_value": c.raw_value,
                    "weighted_value": c.weighted_value,
                    "details": c.details,
                }
                for c in self.components
            ],
            "metrics": self.metrics,
        }

    def is_better_than(self, other: "EvaluationResult") -> bool:
        """
        Compare this result to another.

        Comparison order:
        1. Valid schedules beat invalid schedules
        2. Higher scores beat lower scores
        3. Fewer critical violations beat more
        """
        if self.valid and not other.valid:
            return True
        if not self.valid and other.valid:
            return False
        if self.score != other.score:
            return self.score > other.score
        return self.critical_violations < other.critical_violations


class ScheduleEvaluator:
    """
    Strict evaluator that computes deterministic numeric scores for schedules.

    This evaluator wraps existing ACGME validation and resilience analysis,
    but produces a single numeric score that the control loop can optimize.

    The score is deterministic: the same inputs always produce the same output.
    This is critical for the control loop to reliably compare candidates.

    Weight Distribution:
        - ACGME compliance: 40% (hard constraint, but graded by severity)
        - Coverage rate: 25% (how many blocks are assigned)
        - Resilience score: 20% (N-1/N-2 compliance, utilization)
        - Load balance: 10% (equitable distribution across people)
        - Preference alignment: 5% (soft preferences from stigmergy)

    Example:
        >>> evaluator = ScheduleEvaluator(db)
        >>> result = evaluator.evaluate(
        ...     assignments=assignments,
        ...     start_date=date(2025, 1, 1),
        ...     end_date=date(2025, 3, 31),
        ... )
        >>> print(f"Score: {result.score:.3f}")
        >>> print(f"Valid: {result.valid}")
        >>> for v in result.violations:
        ...     print(f"  - {v.severity.value}: {v.message}")
    """

    # Weight distribution for score components
    WEIGHTS = {
        "acgme_compliance": 0.40,
        "coverage_rate": 0.25,
        "resilience": 0.20,
        "load_balance": 0.10,
        "preference_alignment": 0.05,
    }

    # Penalty multipliers by severity
    SEVERITY_PENALTIES = {
        ViolationSeverity.CRITICAL: 0.20,  # Each critical violation costs 20% of component
        ViolationSeverity.HIGH: 0.10,
        ViolationSeverity.MEDIUM: 0.05,
        ViolationSeverity.LOW: 0.02,
    }

    def __init__(
        self,
        db: Session,
        resilience_config: ResilienceConfig | None = None,
    ):
        """
        Initialize the evaluator.

        Args:
            db: Database session for querying data
            resilience_config: Optional resilience configuration
        """
        self.db = db
        self.acgme_validator = ACGMEValidator(db)
        self.resilience = ResilienceService(
            db=db,
            config=resilience_config or ResilienceConfig(),
        )

    def evaluate(
        self,
        assignments: list[Assignment],
        start_date: date,
        end_date: date,
        faculty: list[Person] | None = None,
        blocks: list[Block] | None = None,
    ) -> EvaluationResult:
        """
        Evaluate a schedule and produce a numeric score.

        This is the main entry point. It runs all constraint checks
        and produces a deterministic score that can be compared across
        different schedule candidates.

        Args:
            assignments: List of assignments to evaluate
            start_date: Start of evaluation period
            end_date: End of evaluation period
            faculty: Optional pre-loaded faculty list
            blocks: Optional pre-loaded blocks list

        Returns:
            EvaluationResult with score, violations, and metrics
        """
        violations: list[ViolationDetail] = []
        components: list[ScoreComponent] = []

        # Load data if not provided
        if faculty is None:
            faculty = self.db.query(Person).filter(Person.type == "faculty").all()
        if blocks is None:
            blocks = (
                self.db.query(Block)
                .filter(Block.date >= start_date, Block.date <= end_date)
                .all()
            )

        # 1. ACGME Compliance (hard constraints)
        acgme_component, acgme_violations = self._evaluate_acgme(
            assignments, start_date, end_date
        )
        components.append(acgme_component)
        violations.extend(acgme_violations)

        # 2. Coverage Rate
        coverage_component = self._evaluate_coverage(assignments, blocks)
        components.append(coverage_component)

        # 3. Resilience
        resilience_component, resilience_violations = self._evaluate_resilience(
            assignments, faculty, blocks
        )
        components.append(resilience_component)
        violations.extend(resilience_violations)

        # 4. Load Balance
        balance_component = self._evaluate_load_balance(assignments)
        components.append(balance_component)

        # 5. Preference Alignment
        preference_component = self._evaluate_preferences(assignments, faculty)
        components.append(preference_component)

        # Calculate overall score
        total_score = sum(c.weighted_value for c in components)

        # Check hard constraint pass (no CRITICAL violations)
        critical_count = sum(
            1 for v in violations if v.severity == ViolationSeverity.CRITICAL
        )
        hard_pass = critical_count == 0

        # If hard constraints fail, score is 0
        if not hard_pass:
            total_score = 0.0

        # Soft score (for comparing invalid schedules)
        soft_score = sum(
            c.weighted_value for c in components
            if c.name != "acgme_compliance"
        )

        # Coverage rate as percentage
        coverage_rate = coverage_component.raw_value

        return EvaluationResult(
            valid=hard_pass,
            score=total_score,
            hard_constraint_pass=hard_pass,
            soft_score=soft_score,
            coverage_rate=coverage_rate,
            total_violations=len(violations),
            critical_violations=critical_count,
            violations=violations,
            components=components,
            metrics={
                "assignment_count": len(assignments),
                "block_count": len(blocks),
                "faculty_count": len(faculty),
            },
        )

    def _evaluate_acgme(
        self,
        assignments: list[Assignment],
        start_date: date,
        end_date: date,
    ) -> tuple[ScoreComponent, list[ViolationDetail]]:
        """
        Evaluate ACGME compliance.

        Maps existing ACGMEValidator output to numeric score.
        """
        violations: list[ViolationDetail] = []

        # Run ACGME validation
        result = self.acgme_validator.validate_all(
            start_date=start_date,
            end_date=end_date,
            assignments=assignments,
        )

        # Convert violations to our format
        for v in result.violations:
            severity = self._map_severity(v.severity)
            penalty = self.SEVERITY_PENALTIES[severity]

            violations.append(ViolationDetail(
                type=v.type,
                severity=severity,
                message=v.message,
                person_id=getattr(v, "person_id", None),
                block_id=getattr(v, "block_id", None),
                details=v.details if hasattr(v, "details") else {},
                penalty=penalty,
            ))

        # Calculate score: start at 1.0, subtract penalties
        raw_score = 1.0
        for v in violations:
            raw_score -= v.penalty
        raw_score = max(0.0, raw_score)

        component = ScoreComponent(
            name="acgme_compliance",
            weight=self.WEIGHTS["acgme_compliance"],
            raw_value=raw_score,
            details=f"{len(violations)} violations, {result.total_violations} total from validator",
        )

        return component, violations

    def _evaluate_coverage(
        self,
        assignments: list[Assignment],
        blocks: list[Block],
    ) -> ScoreComponent:
        """
        Evaluate block coverage rate.

        Score is simply the percentage of blocks with assignments.
        """
        if not blocks:
            return ScoreComponent(
                name="coverage_rate",
                weight=self.WEIGHTS["coverage_rate"],
                raw_value=1.0,
                details="No blocks in period",
            )

        # Count unique blocks with assignments
        assigned_blocks = {a.block_id for a in assignments}

        # Only count weekday blocks
        weekday_blocks = [b for b in blocks if not b.is_weekend]
        total_blocks = len(weekday_blocks)

        if total_blocks == 0:
            coverage = 1.0
        else:
            coverage = len(assigned_blocks & {b.id for b in weekday_blocks}) / total_blocks

        return ScoreComponent(
            name="coverage_rate",
            weight=self.WEIGHTS["coverage_rate"],
            raw_value=coverage,
            details=f"{len(assigned_blocks)}/{total_blocks} weekday blocks assigned",
        )

    def _evaluate_resilience(
        self,
        assignments: list[Assignment],
        faculty: list[Person],
        blocks: list[Block],
    ) -> tuple[ScoreComponent, list[ViolationDetail]]:
        """
        Evaluate resilience metrics.

        Checks N-1/N-2 compliance and utilization levels.
        """
        violations: list[ViolationDetail] = []
        raw_score = 1.0

        try:
            health = self.resilience.check_health(
                faculty=faculty,
                blocks=blocks,
                assignments=assignments,
            )

            # N-1 compliance (single faculty loss)
            if not health.n1_pass:
                raw_score -= 0.25
                violations.append(ViolationDetail(
                    type="N1_VULNERABILITY",
                    severity=ViolationSeverity.HIGH,
                    message="Schedule vulnerable to single faculty loss",
                    details={"critical_faculty": health.critical_faculty},
                    penalty=0.25,
                ))

            # N-2 compliance (pair faculty loss)
            if not health.n2_pass:
                raw_score -= 0.15
                violations.append(ViolationDetail(
                    type="N2_VULNERABILITY",
                    severity=ViolationSeverity.MEDIUM,
                    message="Schedule vulnerable to pair faculty loss",
                    penalty=0.15,
                ))

            # Utilization level
            util_rate = health.utilization.utilization_rate
            if util_rate > 0.95:
                raw_score -= 0.30
                violations.append(ViolationDetail(
                    type="UTILIZATION_BLACK",
                    severity=ViolationSeverity.CRITICAL,
                    message=f"Utilization at BLACK level ({util_rate:.0%})",
                    details={"utilization_rate": util_rate},
                    penalty=0.30,
                ))
            elif util_rate > 0.90:
                raw_score -= 0.20
                violations.append(ViolationDetail(
                    type="UTILIZATION_RED",
                    severity=ViolationSeverity.HIGH,
                    message=f"Utilization at RED level ({util_rate:.0%})",
                    details={"utilization_rate": util_rate},
                    penalty=0.20,
                ))
            elif util_rate > 0.80:
                raw_score -= 0.10
                violations.append(ViolationDetail(
                    type="UTILIZATION_ORANGE",
                    severity=ViolationSeverity.MEDIUM,
                    message=f"Utilization at ORANGE level ({util_rate:.0%})",
                    details={"utilization_rate": util_rate},
                    penalty=0.10,
                ))

            raw_score = max(0.0, raw_score)
            details = f"N1: {'PASS' if health.n1_pass else 'FAIL'}, N2: {'PASS' if health.n2_pass else 'FAIL'}, Util: {util_rate:.0%}"

        except Exception as e:
            # If resilience check fails, give partial credit
            raw_score = 0.5
            details = f"Resilience check failed: {e}"

        component = ScoreComponent(
            name="resilience",
            weight=self.WEIGHTS["resilience"],
            raw_value=raw_score,
            details=details,
        )

        return component, violations

    def _evaluate_load_balance(
        self,
        assignments: list[Assignment],
    ) -> ScoreComponent:
        """
        Evaluate load balance across personnel.

        Uses coefficient of variation (CV) to measure dispersion.
        Lower CV = more balanced = higher score.
        """
        if not assignments:
            return ScoreComponent(
                name="load_balance",
                weight=self.WEIGHTS["load_balance"],
                raw_value=1.0,
                details="No assignments to balance",
            )

        # Count assignments per person
        counts: dict[UUID, int] = {}
        for a in assignments:
            counts[a.person_id] = counts.get(a.person_id, 0) + 1

        if len(counts) < 2:
            return ScoreComponent(
                name="load_balance",
                weight=self.WEIGHTS["load_balance"],
                raw_value=1.0,
                details="Only one person assigned",
            )

        # Calculate coefficient of variation
        values = list(counts.values())
        mean = sum(values) / len(values)
        if mean == 0:
            cv = 0.0
        else:
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5
            cv = std_dev / mean

        # Convert CV to score: CV of 0 = perfect (1.0), CV of 1 = poor (0.0)
        # CV > 1 is very unbalanced
        raw_score = max(0.0, 1.0 - cv)

        return ScoreComponent(
            name="load_balance",
            weight=self.WEIGHTS["load_balance"],
            raw_value=raw_score,
            details=f"CV={cv:.3f}, range={min(values)}-{max(values)}",
        )

    def _evaluate_preferences(
        self,
        assignments: list[Assignment],
        faculty: list[Person],
    ) -> ScoreComponent:
        """
        Evaluate preference alignment from stigmergy trails.

        This is a soft constraint - we prefer schedules that align
        with historical preferences but don't require it.
        """
        # Placeholder: full implementation would query preference trails
        # For now, give baseline score
        return ScoreComponent(
            name="preference_alignment",
            weight=self.WEIGHTS["preference_alignment"],
            raw_value=0.8,
            details="Preference alignment not yet implemented",
        )

    def _map_severity(self, severity_str: str) -> ViolationSeverity:
        """Map string severity to enum."""
        mapping = {
            "CRITICAL": ViolationSeverity.CRITICAL,
            "HIGH": ViolationSeverity.HIGH,
            "MEDIUM": ViolationSeverity.MEDIUM,
            "LOW": ViolationSeverity.LOW,
        }
        return mapping.get(severity_str.upper(), ViolationSeverity.MEDIUM)
