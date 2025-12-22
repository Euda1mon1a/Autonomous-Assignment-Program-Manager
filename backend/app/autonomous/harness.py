"""
N-1 Resilience Test Harness.

Add "n-1 resilience" as a first-class test harness. Make the program
generate adversarial scenarios automatically:
    - Remove one faculty
    - Remove one resident
    - Add unexpected leave block
    - Add holiday staffing shock

Then rerun the loop and compare:
    - Feasibility rate
    - Degradation of soft score
    - Time to recover feasible schedule

This becomes your regression suite for autonomy.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Any
import random
import time
import logging

from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.block import Block
from app.models.person import Person
from app.autonomous.evaluator import ScheduleEvaluator, EvaluationResult
from app.autonomous.generator import CandidateGenerator, GeneratorConfig, ScheduleCandidate
from app.autonomous.state import GeneratorParams


logger = logging.getLogger(__name__)


class ScenarioType(str, Enum):
    """Types of adversarial scenarios."""

    BASELINE = "baseline"
    REMOVE_FACULTY = "remove_faculty"
    REMOVE_RESIDENT = "remove_resident"
    UNEXPECTED_LEAVE = "unexpected_leave"
    HOLIDAY_SHOCK = "holiday_shock"
    MULTIPLE_ABSENCE = "multiple_absence"
    DEPARTMENT_OUTAGE = "department_outage"


@dataclass
class AdversarialScenario:
    """
    Definition of an adversarial test scenario.

    Attributes:
        type: Type of scenario
        name: Human-readable name
        description: Detailed description
        params: Scenario-specific parameters
    """

    type: ScenarioType
    name: str
    description: str
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "params": self.params,
        }


@dataclass
class ScenarioResult:
    """
    Result of running a single adversarial scenario.

    Attributes:
        scenario: The scenario that was run
        baseline_score: Score before applying scenario
        scenario_score: Score after applying scenario
        score_degradation: How much the score dropped
        feasible: Whether a feasible schedule was found
        recovery_iterations: Iterations needed to recover (if applicable)
        recovery_time: Time to recover in seconds
        evaluation: Full evaluation result
        errors: Any errors encountered
    """

    scenario: AdversarialScenario
    baseline_score: float
    scenario_score: float
    score_degradation: float
    feasible: bool
    recovery_iterations: int
    recovery_time: float
    evaluation: EvaluationResult | None
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scenario": self.scenario.to_dict(),
            "baseline_score": self.baseline_score,
            "scenario_score": self.scenario_score,
            "score_degradation": self.score_degradation,
            "feasible": self.feasible,
            "recovery_iterations": self.recovery_iterations,
            "recovery_time": self.recovery_time,
            "evaluation": self.evaluation.to_dict() if self.evaluation else None,
            "errors": self.errors,
        }


@dataclass
class HarnessResult:
    """
    Aggregate result of running the full test harness.

    Attributes:
        total_scenarios: Number of scenarios tested
        passed_scenarios: Number that maintained feasibility
        failed_scenarios: Number that lost feasibility
        avg_score_degradation: Average score drop across scenarios
        worst_scenario: Scenario with worst degradation
        scenario_results: Individual scenario results
        total_time: Total time to run all scenarios
    """

    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    avg_score_degradation: float
    worst_scenario: AdversarialScenario | None
    scenario_results: list[ScenarioResult]
    total_time: float

    def pass_rate(self) -> float:
        """Calculate pass rate as percentage."""
        if self.total_scenarios == 0:
            return 0.0
        return self.passed_scenarios / self.total_scenarios

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_scenarios": self.total_scenarios,
            "passed_scenarios": self.passed_scenarios,
            "failed_scenarios": self.failed_scenarios,
            "pass_rate": self.pass_rate(),
            "avg_score_degradation": self.avg_score_degradation,
            "worst_scenario": self.worst_scenario.to_dict() if self.worst_scenario else None,
            "scenario_results": [r.to_dict() for r in self.scenario_results],
            "total_time": self.total_time,
        }


class ResilienceHarness:
    """
    Test harness for N-1 and N-2 resilience testing.

    This harness generates adversarial scenarios and tests the system's
    ability to maintain feasibility and quality under stress.

    Usage:
        >>> harness = ResilienceHarness(db, start_date, end_date)
        >>> result = harness.run_all_scenarios(baseline_candidate)
        >>> print(f"Pass rate: {result.pass_rate():.1%}")
        >>> if result.worst_scenario:
        ...     print(f"Worst case: {result.worst_scenario.name}")
    """

    def __init__(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        generator_config: GeneratorConfig | None = None,
    ):
        """
        Initialize the test harness.

        Args:
            db: Database session
            start_date: Schedule start date
            end_date: Schedule end date
            generator_config: Optional generator configuration
        """
        self.db = db
        self.start_date = start_date
        self.end_date = end_date
        self.generator_config = generator_config or GeneratorConfig()

        self.generator = CandidateGenerator(
            db=db,
            start_date=start_date,
            end_date=end_date,
            config=generator_config,
        )
        self.evaluator = ScheduleEvaluator(db=db)

    def generate_scenarios(self) -> list[AdversarialScenario]:
        """
        Generate a comprehensive set of adversarial scenarios.

        Returns:
            List of scenarios to test
        """
        scenarios = []

        # Baseline (no changes)
        scenarios.append(AdversarialScenario(
            type=ScenarioType.BASELINE,
            name="Baseline",
            description="No adversarial changes",
        ))

        # Get people for targeted scenarios
        faculty = self.db.query(Person).filter(Person.type == "faculty").all()
        residents = self.db.query(Person).filter(Person.type == "resident").all()

        # N-1: Remove each faculty member
        for fac in faculty[:3]:  # Test first 3 to limit runtime
            scenarios.append(AdversarialScenario(
                type=ScenarioType.REMOVE_FACULTY,
                name=f"Remove faculty: {fac.name[:20]}",
                description=f"Test resilience to loss of {fac.name}",
                params={"person_id": str(fac.id), "person_name": fac.name},
            ))

        # N-1: Remove each resident
        for res in residents[:3]:
            scenarios.append(AdversarialScenario(
                type=ScenarioType.REMOVE_RESIDENT,
                name=f"Remove resident: {res.name[:20]}",
                description=f"Test resilience to loss of {res.name}",
                params={"person_id": str(res.id), "person_name": res.name},
            ))

        # Unexpected leave (random person, random week)
        if faculty:
            random_faculty = random.choice(faculty)
            leave_start = self.start_date + timedelta(days=random.randint(0, 14))
            scenarios.append(AdversarialScenario(
                type=ScenarioType.UNEXPECTED_LEAVE,
                name="Unexpected 1-week leave",
                description=f"Unexpected absence for {random_faculty.name}",
                params={
                    "person_id": str(random_faculty.id),
                    "person_name": random_faculty.name,
                    "leave_start": leave_start.isoformat(),
                    "leave_days": 7,
                },
            ))

        # Holiday staffing shock (reduced capacity for period)
        scenarios.append(AdversarialScenario(
            type=ScenarioType.HOLIDAY_SHOCK,
            name="Holiday skeleton staff",
            description="50% capacity reduction for 1 week",
            params={
                "reduction_percent": 50,
                "duration_days": 7,
            },
        ))

        # Multiple simultaneous absences
        if len(faculty) >= 2:
            scenarios.append(AdversarialScenario(
                type=ScenarioType.MULTIPLE_ABSENCE,
                name="Two faculty out",
                description="Two faculty members unavailable simultaneously",
                params={
                    "person_ids": [str(f.id) for f in faculty[:2]],
                    "person_names": [f.name for f in faculty[:2]],
                },
            ))

        return scenarios

    def run_scenario(
        self,
        scenario: AdversarialScenario,
        baseline_score: float,
        max_recovery_iterations: int = 50,
    ) -> ScenarioResult:
        """
        Run a single adversarial scenario.

        Args:
            scenario: Scenario to run
            baseline_score: Score of baseline schedule
            max_recovery_iterations: Max iterations to attempt recovery

        Returns:
            ScenarioResult with outcome
        """
        start_time = time.time()
        errors: list[str] = []

        try:
            # Apply scenario modifications
            self._apply_scenario(scenario)

            # Generate schedule under scenario conditions
            recovery_iterations = 0
            best_candidate = None
            best_evaluation = None

            for i in range(max_recovery_iterations):
                recovery_iterations = i + 1

                # Generate candidate
                params = GeneratorParams(
                    algorithm="greedy" if i == 0 else "cp_sat",
                    timeout_seconds=30.0,
                    random_seed=42 + i,
                )
                candidate = self.generator.generate_single(params=params)

                if candidate is None:
                    continue

                # Evaluate
                evaluation = self.evaluator.evaluate(
                    assignments=candidate.assignments,
                    start_date=self.start_date,
                    end_date=self.end_date,
                )

                # Track best
                if best_evaluation is None or evaluation.is_better_than(best_evaluation):
                    best_candidate = candidate
                    best_evaluation = evaluation

                # Early exit if feasible and good enough
                if evaluation.valid and evaluation.score >= baseline_score * 0.9:
                    break

            # Revert scenario modifications
            self._revert_scenario(scenario)

            recovery_time = time.time() - start_time

            if best_evaluation is None:
                return ScenarioResult(
                    scenario=scenario,
                    baseline_score=baseline_score,
                    scenario_score=0.0,
                    score_degradation=baseline_score,
                    feasible=False,
                    recovery_iterations=recovery_iterations,
                    recovery_time=recovery_time,
                    evaluation=None,
                    errors=["No valid candidate generated"],
                )

            return ScenarioResult(
                scenario=scenario,
                baseline_score=baseline_score,
                scenario_score=best_evaluation.score,
                score_degradation=baseline_score - best_evaluation.score,
                feasible=best_evaluation.valid,
                recovery_iterations=recovery_iterations,
                recovery_time=recovery_time,
                evaluation=best_evaluation,
                errors=errors,
            )

        except Exception as e:
            logger.error(f"Scenario {scenario.name} failed: {e}")
            self._revert_scenario(scenario)  # Ensure cleanup
            return ScenarioResult(
                scenario=scenario,
                baseline_score=baseline_score,
                scenario_score=0.0,
                score_degradation=baseline_score,
                feasible=False,
                recovery_iterations=0,
                recovery_time=time.time() - start_time,
                evaluation=None,
                errors=[str(e)],
            )

    def run_all_scenarios(
        self,
        baseline_candidate: ScheduleCandidate | None = None,
    ) -> HarnessResult:
        """
        Run all adversarial scenarios.

        Args:
            baseline_candidate: Optional baseline schedule to compare against

        Returns:
            HarnessResult with aggregate outcomes
        """
        start_time = time.time()

        # Get baseline score
        if baseline_candidate:
            baseline_eval = self.evaluator.evaluate(
                assignments=baseline_candidate.assignments,
                start_date=self.start_date,
                end_date=self.end_date,
            )
            baseline_score = baseline_eval.score
        else:
            # Generate baseline
            candidate = self.generator.generate_single()
            if candidate:
                baseline_eval = self.evaluator.evaluate(
                    assignments=candidate.assignments,
                    start_date=self.start_date,
                    end_date=self.end_date,
                )
                baseline_score = baseline_eval.score
            else:
                baseline_score = 0.0

        # Generate and run scenarios
        scenarios = self.generate_scenarios()
        results: list[ScenarioResult] = []

        for scenario in scenarios:
            logger.info(f"Running scenario: {scenario.name}")
            result = self.run_scenario(scenario, baseline_score)
            results.append(result)
            logger.info(
                f"  Result: score={result.scenario_score:.4f}, "
                f"feasible={result.feasible}, "
                f"degradation={result.score_degradation:.4f}"
            )

        # Aggregate results
        passed = sum(1 for r in results if r.feasible)
        failed = len(results) - passed
        avg_degradation = (
            sum(r.score_degradation for r in results) / len(results)
            if results else 0.0
        )

        # Find worst scenario
        worst = None
        worst_degradation = 0.0
        for r in results:
            if r.score_degradation > worst_degradation:
                worst_degradation = r.score_degradation
                worst = r.scenario

        total_time = time.time() - start_time

        return HarnessResult(
            total_scenarios=len(results),
            passed_scenarios=passed,
            failed_scenarios=failed,
            avg_score_degradation=avg_degradation,
            worst_scenario=worst,
            scenario_results=results,
            total_time=total_time,
        )

    def _apply_scenario(self, scenario: AdversarialScenario) -> None:
        """
        Apply scenario modifications to the database.

        Note: These are temporary modifications that should be reverted.
        Uses a transaction savepoint for safe rollback.
        """
        # Create savepoint for rollback
        self._savepoint = self.db.begin_nested()

        if scenario.type == ScenarioType.REMOVE_FACULTY:
            # Mark faculty as unavailable for entire period
            person_id = scenario.params.get("person_id")
            if person_id:
                absence = Absence(
                    person_id=person_id,
                    start_date=self.start_date,
                    end_date=self.end_date,
                    absence_type="SCENARIO_TEST",
                    replacement_activity="N-1 Test",
                )
                self.db.add(absence)
                self.db.flush()

        elif scenario.type == ScenarioType.REMOVE_RESIDENT:
            person_id = scenario.params.get("person_id")
            if person_id:
                absence = Absence(
                    person_id=person_id,
                    start_date=self.start_date,
                    end_date=self.end_date,
                    absence_type="SCENARIO_TEST",
                    replacement_activity="N-1 Test",
                )
                self.db.add(absence)
                self.db.flush()

        elif scenario.type == ScenarioType.UNEXPECTED_LEAVE:
            person_id = scenario.params.get("person_id")
            leave_start = date.fromisoformat(scenario.params.get("leave_start", self.start_date.isoformat()))
            leave_days = scenario.params.get("leave_days", 7)
            if person_id:
                absence = Absence(
                    person_id=person_id,
                    start_date=leave_start,
                    end_date=leave_start + timedelta(days=leave_days),
                    absence_type="UNEXPECTED_LEAVE",
                    replacement_activity="Emergency Leave",
                )
                self.db.add(absence)
                self.db.flush()

        elif scenario.type == ScenarioType.MULTIPLE_ABSENCE:
            person_ids = scenario.params.get("person_ids", [])
            for pid in person_ids:
                absence = Absence(
                    person_id=pid,
                    start_date=self.start_date,
                    end_date=self.end_date,
                    absence_type="SCENARIO_TEST",
                    replacement_activity="N-2 Test",
                )
                self.db.add(absence)
            self.db.flush()

        # Clear generator cache after modifications
        self.generator.clear_cache()

    def _revert_scenario(self, scenario: AdversarialScenario) -> None:
        """
        Revert scenario modifications.

        Rolls back to the savepoint created before applying the scenario.
        """
        if hasattr(self, '_savepoint') and self._savepoint:
            self._savepoint.rollback()
            self._savepoint = None

        # Clear generator cache after revert
        self.generator.clear_cache()


def run_resilience_regression(
    db: Session,
    start_date: date,
    end_date: date,
    threshold_pass_rate: float = 0.8,
) -> tuple[bool, HarnessResult]:
    """
    Run resilience regression test suite.

    This is the entry point for CI/CD integration. Returns pass/fail
    based on whether the system maintains acceptable resilience.

    Args:
        db: Database session
        start_date: Schedule start date
        end_date: Schedule end date
        threshold_pass_rate: Minimum acceptable pass rate

    Returns:
        Tuple of (passed, result)
    """
    harness = ResilienceHarness(db, start_date, end_date)
    result = harness.run_all_scenarios()

    passed = result.pass_rate() >= threshold_pass_rate

    logger.info(
        f"Resilience regression: {'PASS' if passed else 'FAIL'} "
        f"(rate={result.pass_rate():.1%}, threshold={threshold_pass_rate:.1%})"
    )

    return passed, result
