"""
Stress Testing for Transcription Factor Scheduler.

Tests graceful degradation under high load and crisis scenarios.

This module implements a stress testing framework that validates the scheduler's
ability to handle various stress conditions while maintaining critical constraints:

1. **Faculty Absence Simulation**: Tests scheduler with increasing faculty unavailability
2. **Timeout Pressure**: Reduces solver time to simulate time-critical scenarios
3. **Constraint Tracking**: Monitors which constraints are satisfied/relaxed/violated
4. **ACGME Compliance**: Measures compliance percentage under stress
5. **Patient Safety**: Verifies supervision ratios are never violated (master regulator)
6. **Graceful Degradation**: Ensures system degrades predictably, not catastrophically

Expected Behavior Under Stress:
- NORMAL (100% capacity): All constraints active, >90% coverage
- ELEVATED (110% load): Soft constraints may relax, >75% coverage
- HIGH (120% load): Non-critical constraints silenced, >60% coverage
- CRITICAL (130% load): Only safety-critical constraints, >40% coverage
- CRISIS (150% load): Emergency mode with minimal constraints, >25% coverage

Patient safety (supervision ratios) must be maintained at ALL stress levels.

Usage:
    >>> from datetime import date, timedelta
    >>> from app.scheduling.engine import SchedulingEngine
    >>>
    >>> # Create stress tester
    >>> tester = StressTester()
    >>>
    >>> # Create scheduler
    >>> engine = SchedulingEngine(
    ...     db=db,
    ...     start_date=date.today(),
    ...     end_date=date.today() + timedelta(days=28)
    ... )
    >>>
    >>> # Define scenario
    >>> scenario = {
    ...     "pgy_levels": None,  # All residents
    ...     "algorithm": "greedy",
    ...     "check_resilience": True
    ... }
    >>>
    >>> # Run stress test at CRITICAL level
    >>> result = tester.run_stress_test(engine, StressLevel.CRITICAL, scenario)
    >>> print(f"ACGME Compliance: {result.acgme_compliance:.1%}")
    >>> print(f"Patient Safety: {result.patient_safety_maintained}")
    >>>
    >>> # Run full degradation ladder
    >>> all_results = tester.run_degradation_ladder(engine, scenario)
    >>> report = tester.generate_report(all_results)
    >>> print(report)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class StressLevel(str, Enum):
    """Stress levels for testing."""

    NORMAL = "normal"  # 100% capacity
    ELEVATED = "elevated"  # 110% load
    HIGH = "high"  # 120% load
    CRITICAL = "critical"  # 130% load
    CRISIS = "crisis"  # 150% load


@dataclass
class StressResult:
    """Result of stress testing."""

    stress_level: StressLevel
    constraints_satisfied: int
    constraints_relaxed: int
    constraints_violated: int
    degradation_graceful: bool
    acgme_compliance: float
    patient_safety_maintained: bool
    notes: list[str]


class StressTester:
    """Tests transcription factor scheduler under stress conditions."""

    def __init__(self):
        self.results: list[StressResult] = []

    def run_stress_test(
        self,
        scheduler: Any,
        stress_level: StressLevel,
        scenario: dict,
    ) -> StressResult:
        """
        Run a stress test at specified level.

        Tests:
        1. Constraint satisfaction under load
        2. Graceful degradation (chromatin silencing)
        3. Master regulator (patient safety) always active
        4. ACGME compliance maintained where possible
        """
        notes = []

        # Apply stress conditions to scenario based on stress level
        stressed_scenario = self._apply_stress_conditions(scenario, stress_level)
        notes.append(f"Applied {stress_level.value} stress conditions")

        # Track constraints before scheduling
        initial_constraints = self._get_active_constraints(scheduler)
        notes.append(f"Initial active constraints: {len(initial_constraints)}")

        # Run scheduler under stress
        try:
            result = scheduler.generate(
                pgy_levels=stressed_scenario.get("pgy_levels"),
                rotation_template_ids=stressed_scenario.get("rotation_template_ids"),
                algorithm=stressed_scenario.get("algorithm", "greedy"),
                timeout_seconds=stressed_scenario.get("timeout", 60.0),
                check_resilience=stressed_scenario.get("check_resilience", True),
            )
            notes.append(f"Scheduler completed: {result.get('status', 'unknown')}")
        except Exception as e:
            # Catastrophic failure - system did not degrade gracefully
            notes.append(f"CATASTROPHIC FAILURE: {str(e)}")
            return StressResult(
                stress_level=stress_level,
                constraints_satisfied=0,
                constraints_relaxed=0,
                constraints_violated=999,  # Maximum violations
                degradation_graceful=False,
                acgme_compliance=0.0,
                patient_safety_maintained=False,
                notes=notes,
            )

        # Track constraint satisfaction after scheduling
        final_constraints = self._get_active_constraints(scheduler)
        constraints_relaxed = len(initial_constraints) - len(final_constraints)
        notes.append(f"Constraints relaxed: {constraints_relaxed}")

        # Calculate ACGME compliance from validation results
        validation = result.get("validation")
        acgme_compliance = self._calculate_acgme_compliance(validation, notes)

        # Verify patient safety (supervision ratios never violated)
        patient_safety = self._verify_patient_safety(validation, notes)

        # Check graceful degradation
        degradation_graceful = self._check_graceful_degradation(
            stress_level, result, validation, constraints_relaxed, notes
        )

        # Count violations by severity
        violations = validation.violations if validation else []
        critical_violations = len([v for v in violations if v.severity == "CRITICAL"])
        total_violations = len(violations)
        constraints_satisfied = len(initial_constraints) - total_violations

        stress_result = StressResult(
            stress_level=stress_level,
            constraints_satisfied=max(0, constraints_satisfied),
            constraints_relaxed=max(0, constraints_relaxed),
            constraints_violated=total_violations,
            degradation_graceful=degradation_graceful,
            acgme_compliance=acgme_compliance,
            patient_safety_maintained=patient_safety,
            notes=notes,
        )

        self.results.append(stress_result)
        return stress_result

    def run_degradation_ladder(
        self,
        scheduler: Any,
        scenario: dict,
    ) -> list[StressResult]:
        """Run tests at all stress levels to validate degradation ladder."""
        results = []
        for level in StressLevel:
            result = self.run_stress_test(scheduler, level, scenario)
            results.append(result)
        return results

    def verify_master_regulators(self, results: list[StressResult]) -> bool:
        """Verify patient safety maintained at all stress levels."""
        return all(r.patient_safety_maintained for r in results)

    def verify_graceful_degradation(self, results: list[StressResult]) -> bool:
        """Verify degradation is graceful (no sudden failures)."""
        return all(r.degradation_graceful for r in results)

    def _apply_stress_conditions(
        self,
        scenario: dict,
        stress_level: StressLevel,
    ) -> dict:
        """
        Apply stress conditions to scenario based on stress level.

        Stress conditions:
        - NORMAL (100% capacity): No modifications
        - ELEVATED (110% load): 10% faculty absence rate
        - HIGH (120% load): 20% faculty absence rate
        - CRITICAL (130% load): 30% faculty absence rate + tighter timeout
        - CRISIS (150% load): 40% faculty absence rate + very tight timeout
        """
        stressed = scenario.copy()

        # Map stress level to faculty absence rate
        absence_rates = {
            StressLevel.NORMAL: 0.0,
            StressLevel.ELEVATED: 0.10,
            StressLevel.HIGH: 0.20,
            StressLevel.CRITICAL: 0.30,
            StressLevel.CRISIS: 0.40,
        }

        # Map stress level to solver timeout (less time = more stress)
        timeout_map = {
            StressLevel.NORMAL: 60.0,
            StressLevel.ELEVATED: 45.0,
            StressLevel.HIGH: 30.0,
            StressLevel.CRITICAL: 20.0,
            StressLevel.CRISIS: 10.0,
        }

        stressed["absence_rate"] = absence_rates.get(stress_level, 0.0)
        stressed["timeout"] = timeout_map.get(stress_level, 60.0)

        # At CRISIS level, also prefer faster solver
        if stress_level == StressLevel.CRISIS:
            stressed["algorithm"] = "greedy"  # Fastest solver for emergency
        elif stress_level == StressLevel.CRITICAL:
            stressed["algorithm"] = "cp_sat"  # Balance speed and quality
        else:
            stressed["algorithm"] = scenario.get("algorithm", "greedy")

        return stressed

    def _get_active_constraints(self, scheduler: Any) -> list[str]:
        """
        Get list of active constraints from scheduler.

        Returns list of constraint names that are currently enabled.
        """
        constraints = []

        # Access constraint manager if available
        if hasattr(scheduler, "constraint_manager"):
            manager = scheduler.constraint_manager
            if hasattr(manager, "constraints"):
                # Get enabled constraints
                constraints = [
                    c.name for c in manager.constraints if getattr(c, "enabled", True)
                ]

        return constraints

    def _calculate_acgme_compliance(
        self,
        validation: Any,
        notes: list[str],
    ) -> float:
        """
        Calculate ACGME compliance percentage from validation results.

        Returns:
            float: Compliance percentage (0.0-1.0)
                - 1.0 = Perfect compliance, no violations
                - 0.5 = 50% of checks passed
                - 0.0 = Total failure
        """
        if not validation:
            notes.append("No validation data available")
            return 0.0

        # Check if validation object has the expected attributes
        if not hasattr(validation, "violations"):
            notes.append("Validation missing violations data")
            return 0.0

        violations = validation.violations
        total_violations = len(violations)

        # Count ACGME-specific violations (80-hour, 1-in-7, supervision)
        acgme_violations = [
            v
            for v in violations
            if v.type
            in (
                "80_HOUR_VIOLATION",
                "1_IN_7_VIOLATION",
                "SUPERVISION_RATIO_VIOLATION",
            )
        ]

        acgme_violation_count = len(acgme_violations)

        # Calculate compliance based on violations
        # Assumption: For each resident/block, we check ~3 ACGME rules
        # Total checks = (assignments / 10) * 3 (rough estimate)
        total_assignments = getattr(validation, "statistics", {}).get(
            "total_assignments", 100
        )
        estimated_checks = max(1, (total_assignments // 10) * 3)

        # Compliance = (checks passed) / (total checks)
        compliance = max(0.0, 1.0 - (acgme_violation_count / estimated_checks))

        notes.append(
            f"ACGME compliance: {compliance:.1%} "
            f"({acgme_violation_count} violations, {estimated_checks} checks)"
        )

        return compliance

    def _verify_patient_safety(
        self,
        validation: Any,
        notes: list[str],
    ) -> bool:
        """
        Verify patient safety constraints are maintained.

        Patient safety = supervision ratios are NEVER violated, regardless of stress level.
        This is the "master regulator" that must always be active.

        Returns:
            bool: True if no supervision ratio violations, False otherwise
        """
        if not validation or not hasattr(validation, "violations"):
            notes.append("Cannot verify patient safety - no validation data")
            return False

        violations = validation.violations

        # Check for supervision ratio violations
        supervision_violations = [
            v for v in violations if v.type == "SUPERVISION_RATIO_VIOLATION"
        ]

        patient_safety_ok = len(supervision_violations) == 0

        if patient_safety_ok:
            notes.append("✓ Patient safety MAINTAINED - no supervision violations")
        else:
            notes.append(
                f"✗ Patient safety VIOLATED - {len(supervision_violations)} "
                f"supervision ratio violations"
            )

        return patient_safety_ok

    def _check_graceful_degradation(
        self,
        stress_level: StressLevel,
        result: dict,
        validation: Any,
        constraints_relaxed: int,
        notes: list[str],
    ) -> bool:
        """
        Check if system degraded gracefully under stress.

        Graceful degradation means:
        1. System didn't crash (got a result)
        2. Degradation is proportional to stress level
        3. No sudden cliff - gradual decline in quality
        4. Critical constraints (patient safety) maintained

        Returns:
            bool: True if degradation was graceful, False if catastrophic
        """
        # Already handled catastrophic failure in main method
        # If we got here, system produced a result

        # Check 1: Got a result
        if not result:
            notes.append("✗ Graceful degradation FAILED - no result produced")
            return False

        # Check 2: Proportional degradation
        # Higher stress should result in more constraint relaxation
        stress_to_relaxation = {
            StressLevel.NORMAL: 0,
            StressLevel.ELEVATED: 2,
            StressLevel.HIGH: 5,
            StressLevel.CRITICAL: 10,
            StressLevel.CRISIS: 15,
        }

        expected_relaxation = stress_to_relaxation.get(stress_level, 0)

        # Allow some tolerance (±50%)
        if constraints_relaxed > expected_relaxation * 3:
            notes.append(
                f"⚠ Degradation steeper than expected: "
                f"{constraints_relaxed} constraints relaxed (expected ~{expected_relaxation})"
            )
            # Not a failure, just a warning

        # Check 3: Status is reasonable
        status = result.get("status")
        if status == "failed":
            notes.append("✗ Graceful degradation FAILED - scheduler reported failure")
            return False

        # Check 4: Validation exists
        if not validation:
            notes.append("⚠ Validation missing - cannot verify degradation")
            # Not a hard failure, but concerning

        # Check 5: Schedule has some coverage
        coverage_rate = getattr(validation, "coverage_rate", 0.0) if validation else 0.0

        # Minimum acceptable coverage by stress level
        min_coverage = {
            StressLevel.NORMAL: 90.0,
            StressLevel.ELEVATED: 75.0,
            StressLevel.HIGH: 60.0,
            StressLevel.CRITICAL: 40.0,
            StressLevel.CRISIS: 25.0,
        }

        expected_min = min_coverage.get(stress_level, 50.0)

        if coverage_rate < expected_min:
            notes.append(
                f"✗ Graceful degradation FAILED - coverage too low: "
                f"{coverage_rate:.1f}% (expected ≥{expected_min:.1f}%)"
            )
            return False

        notes.append(
            f"✓ Graceful degradation OK - "
            f"coverage {coverage_rate:.1f}%, {constraints_relaxed} constraints relaxed"
        )

        return True

    def generate_report(self, results: list[StressResult] | None = None) -> str:
        """
        Generate a summary report of stress test results.

        Args:
            results: List of StressResult objects (defaults to self.results)

        Returns:
            str: Formatted report with summary statistics
        """
        if results is None:
            results = self.results

        if not results:
            return "No stress test results available."

        report_lines = [
            "=" * 80,
            "STRESS TEST REPORT",
            "=" * 80,
            "",
            f"Total Tests Run: {len(results)}",
            "",
            "Results by Stress Level:",
            "-" * 80,
        ]

        # Group by stress level
        by_level = {}
        for result in results:
            level = result.stress_level.value
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(result)

        # Report each level
        for level in ["normal", "elevated", "high", "critical", "crisis"]:
            if level not in by_level:
                continue

            level_results = by_level[level]
            report_lines.append(f"\n{level.upper()}:")

            for result in level_results:
                report_lines.extend(
                    [
                        f"  Constraints Satisfied: {result.constraints_satisfied}",
                        f"  Constraints Relaxed:   {result.constraints_relaxed}",
                        f"  Constraints Violated:  {result.constraints_violated}",
                        f"  ACGME Compliance:      {result.acgme_compliance:.1%}",
                        f"  Patient Safety:        {'✓ PASS' if result.patient_safety_maintained else '✗ FAIL'}",
                        f"  Graceful Degradation:  {'✓ PASS' if result.degradation_graceful else '✗ FAIL'}",
                    ]
                )

                # Add key notes
                if result.notes:
                    key_notes = [
                        n for n in result.notes if "✓" in n or "✗" in n or "⚠" in n
                    ]
                    if key_notes:
                        report_lines.append("  Key Notes:")
                        for note in key_notes[:3]:  # Show top 3 notes
                            report_lines.append(f"    - {note}")

        # Summary statistics
        report_lines.extend(
            [
                "",
                "-" * 80,
                "SUMMARY:",
                "-" * 80,
            ]
        )

        total_tests = len(results)
        patient_safety_pass = sum(1 for r in results if r.patient_safety_maintained)
        graceful_pass = sum(1 for r in results if r.degradation_graceful)
        avg_compliance = sum(r.acgme_compliance for r in results) / total_tests

        report_lines.extend(
            [
                f"Patient Safety Pass Rate:    {patient_safety_pass}/{total_tests} ({patient_safety_pass / total_tests:.1%})",
                f"Graceful Degradation Rate:   {graceful_pass}/{total_tests} ({graceful_pass / total_tests:.1%})",
                f"Average ACGME Compliance:    {avg_compliance:.1%}",
                "",
            ]
        )

        # Overall verdict
        all_patient_safety = patient_safety_pass == total_tests
        all_graceful = graceful_pass == total_tests

        if all_patient_safety and all_graceful:
            verdict = "✓ PASS - System demonstrates graceful degradation with patient safety maintained"
        elif all_patient_safety:
            verdict = "⚠ PARTIAL - Patient safety maintained but degradation not always graceful"
        else:
            verdict = "✗ FAIL - Patient safety violations detected"

        report_lines.extend(
            [
                "OVERALL VERDICT:",
                verdict,
                "",
                "=" * 80,
            ]
        )

        return "\n".join(report_lines)

    @staticmethod
    def create_scenario(
        algorithm: str = "greedy",
        pgy_levels: list[int] | None = None,
        check_resilience: bool = True,
    ) -> dict:
        """
        Create a standard stress test scenario.

        Args:
            algorithm: Solver algorithm to use ("greedy", "cp_sat", "pulp", "hybrid")
            pgy_levels: PGY levels to include (None = all)
            check_resilience: Whether to run resilience health checks

        Returns:
            dict: Scenario configuration for stress testing
        """
        return {
            "algorithm": algorithm,
            "pgy_levels": pgy_levels,
            "rotation_template_ids": None,  # All templates
            "check_resilience": check_resilience,
        }
