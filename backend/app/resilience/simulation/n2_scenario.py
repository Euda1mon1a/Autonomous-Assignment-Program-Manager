"""
N-2 Contingency Validation Scenario

Tests whether the system can survive loss of any 2 faculty members without
cascading failure, inspired by power grid N-2 reliability standards.

The simulation:
1. Creates a faculty-zone assignment structure with overlapping coverage
2. Tests all (or random sample of) faculty pairs being unavailable
3. Checks if zones can maintain minimum coverage through borrowing
4. Identifies vulnerable pairs and failure patterns
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from random import Random


@dataclass
class N2ScenarioConfig:
    """Configuration for N-2 contingency scenario."""

    iterations: int = 1000
    faculty_count: int = 10
    zone_count: int = 6
    faculty_per_zone: int = 3  # With overlap, faculty can cover multiple zones
    minimum_zone_coverage: int = 2  # Minimum faculty needed per zone
    recovery_time_hours: float = 4.0
    borrowing_enabled: bool = True
    borrowing_success_rate: float = 0.8
    seed: int = 42


@dataclass
class N2IterationResult:
    """Result from a single N-2 iteration (testing one faculty pair loss)."""

    iteration: int
    faculty_pair_lost: tuple[int, int]  # Faculty indices
    passed: bool
    zones_failed: int
    zones_degraded: int  # Below minimum but not failed
    borrowing_attempts: int
    borrowing_successes: int
    recovery_time: float | None
    failure_mode: str | None  # "skill_gap", "capacity", "cascade", None if passed


@dataclass
class N2ScenarioResult:
    """Aggregated results from all N-2 iterations."""

    config: N2ScenarioConfig
    iterations_run: int
    passes: int
    failures: int
    pass_rate: float
    failure_modes: dict[str, int] = field(default_factory=dict)  # mode -> count
    most_vulnerable_pairs: list[tuple[int, int]] = field(
        default_factory=list
    )  # Top 5 pairs
    average_recovery_time: float = 0.0
    cascade_rate: float = 0.0  # % of failures that cascaded
    zones_most_affected: dict[int, int] = field(
        default_factory=dict
    )  # zone_idx -> failure_count
    recommendations: list[str] = field(default_factory=list)


class N2ContingencyScenario:
    """
    Simulates N-2 contingency scenarios for faculty-zone assignments.

    Tests whether the system can survive the loss of any 2 faculty members
    without cascading failures or zone coverage dropping below minimum thresholds.
    """

    def __init__(self, config: N2ScenarioConfig):
        self.config = config
        self._faculty: list[dict] = []  # Each: {id, zones, skills}
        self._zones: list[dict] = (
            []
        )  # Each: {id, faculty, min_coverage, required_skills}
        self._results: list[N2IterationResult] = []
        self._rng = Random(config.seed)

    def setup(self) -> None:
        """
        Initialize faculty and zone structures with overlapping assignments.

        Creates a realistic faculty-zone assignment where:
        - Each zone has multiple faculty assigned
        - Faculty can cover multiple zones
        - Some overlap exists for redundancy
        """
        # Initialize zones
        for zone_id in range(self.config.zone_count):
            self._zones.append(
                {
                    "id": zone_id,
                    "faculty": set(),
                    "min_coverage": self.config.minimum_zone_coverage,
                    "required_skills": self._generate_zone_skills(zone_id),
                }
            )

        # Initialize faculty with zone assignments
        for faculty_id in range(self.config.faculty_count):
            # Each faculty member is assigned to 2-4 zones (with some randomness)
            num_zones = self._rng.randint(2, 4)
            assigned_zones = self._rng.sample(
                range(self.config.zone_count), min(num_zones, self.config.zone_count)
            )

            faculty_skills = self._generate_faculty_skills(faculty_id)

            self._faculty.append(
                {
                    "id": faculty_id,
                    "zones": set(assigned_zones),
                    "skills": faculty_skills,
                }
            )

            # Update zone assignments
            for zone_id in assigned_zones:
                self._zones[zone_id]["faculty"].add(faculty_id)

        # Ensure each zone has at least minimum_zone_coverage + 1 faculty
        # (otherwise any 2 losses could trivially fail it)
        self._ensure_minimum_redundancy()

    def _generate_zone_skills(self, zone_id: int) -> set[str]:
        """Generate required skills for a zone."""
        # Different zones require different skill combinations
        skill_sets = [
            {"surgery", "emergency"},
            {"pediatrics", "general"},
            {"surgery", "ob_gyn"},
            {"emergency", "general"},
            {"ob_gyn", "pediatrics"},
            {"surgery", "general"},
        ]
        return skill_sets[zone_id % len(skill_sets)]

    def _generate_faculty_skills(self, faculty_id: int) -> set[str]:
        """Generate skills for a faculty member."""
        all_skills = ["surgery", "emergency", "pediatrics", "ob_gyn", "general"]
        # Each faculty has 2-3 skills
        num_skills = self._rng.randint(2, 3)
        return set(self._rng.sample(all_skills, num_skills))

    def _ensure_minimum_redundancy(self) -> None:
        """
        Ensure each zone has enough faculty for N-2 testing.

        Each zone needs at least min_coverage + 2 faculty to survive any 2 losses
        in the worst case (if both lost faculty were assigned to that zone).
        """
        target_per_zone = self.config.minimum_zone_coverage + 2

        for zone in self._zones:
            while len(zone["faculty"]) < target_per_zone:
                # Find faculty with fewest zone assignments
                faculty_by_load = sorted(self._faculty, key=lambda f: len(f["zones"]))

                for faculty in faculty_by_load:
                    if zone["id"] not in faculty["zones"]:
                        faculty["zones"].add(zone["id"])
                        zone["faculty"].add(faculty["id"])
                        break

    def _check_zone_sufficiency(self, available_faculty: set[int]) -> dict[int, str]:
        """
        Check each zone's status with available faculty.

        Args:
            available_faculty: Set of faculty IDs that are available

        Returns:
            Dict mapping zone_idx -> status
            Status can be: "ok", "degraded", "failed", "skill_gap"
        """
        zone_status = {}

        for zone in self._zones:
            # Count available faculty for this zone
            zone_available = zone["faculty"] & available_faculty
            available_count = len(zone_available)

            if available_count >= self.config.minimum_zone_coverage:
                # Check if skills are covered
                available_skills = set()
                for fac_id in zone_available:
                    available_skills.update(self._faculty[fac_id]["skills"])

                if zone["required_skills"].issubset(available_skills):
                    zone_status[zone["id"]] = "ok"
                else:
                    # Enough people but missing critical skills
                    zone_status[zone["id"]] = "skill_gap"
            elif available_count == self.config.minimum_zone_coverage - 1:
                zone_status[zone["id"]] = "degraded"
            else:
                zone_status[zone["id"]] = "failed"

        return zone_status

    def _attempt_borrowing(
        self, failed_zones: list[int], available_faculty: set[int]
    ) -> tuple[int, int]:
        """
        Attempt to borrow faculty from other zones to cover failures.

        Args:
            failed_zones: List of zone IDs that failed or are degraded
            available_faculty: Set of available faculty IDs

        Returns:
            Tuple of (attempts, successes)
        """
        if not self.config.borrowing_enabled:
            return 0, 0

        attempts = 0
        successes = 0

        for zone_id in failed_zones:
            zone = self._zones[zone_id]
            zone_available = zone["faculty"] & available_faculty
            shortfall = self.config.minimum_zone_coverage - len(zone_available)

            if shortfall <= 0:
                continue

            # Try to find faculty from other zones who have the needed skills
            needed_skills = zone["required_skills"]

            for _ in range(shortfall):
                attempts += 1

                # Find faculty not assigned to this zone but with relevant skills
                candidates = []
                for fac_id in available_faculty:
                    faculty = self._faculty[fac_id]
                    if (
                        zone_id not in faculty["zones"]
                        and faculty["skills"] & needed_skills
                    ):
                        candidates.append(fac_id)

                if (
                    candidates
                    and self._rng.random() < self.config.borrowing_success_rate
                ):
                    # Successfully borrowed
                    successes += 1
                    borrowed_fac = self._rng.choice(candidates)
                    available_faculty.remove(borrowed_fac)

        return attempts, successes

    def _run_iteration(self, iteration: int) -> N2IterationResult:
        """
        Run a single N-2 iteration by removing 2 faculty and checking zones.

        Args:
            iteration: Iteration number (used for deterministic pair selection)

        Returns:
            N2IterationResult with outcome of this test
        """
        # Determine which faculty pair to remove
        total_pairs = self.config.faculty_count * (self.config.faculty_count - 1) // 2

        if self.config.iterations >= total_pairs:
            # Test all pairs systematically
            all_pairs = list(combinations(range(self.config.faculty_count), 2))
            if iteration < len(all_pairs):
                faculty_pair = all_pairs[iteration]
            else:
                # Shouldn't happen, but handle gracefully
                faculty_pair = tuple(
                    self._rng.sample(range(self.config.faculty_count), 2)
                )
        else:
            # Random sampling
            faculty_pair = tuple(
                sorted(self._rng.sample(range(self.config.faculty_count), 2))
            )

        # Create available faculty set (all except the lost pair)
        available_faculty = set(range(self.config.faculty_count)) - set(faculty_pair)

        # Check zone sufficiency
        zone_status = self._check_zone_sufficiency(available_faculty)

        # Count failures and degradations
        failed_zones = [
            z_id
            for z_id, status in zone_status.items()
            if status in ("failed", "skill_gap")
        ]
        degraded_zones = [
            z_id for z_id, status in zone_status.items() if status == "degraded"
        ]

        # Attempt borrowing if there are failures
        borrowing_attempts = 0
        borrowing_successes = 0

        if failed_zones or degraded_zones:
            # Make a copy of available faculty for borrowing simulation
            available_for_borrowing = available_faculty.copy()
            borrowing_attempts, borrowing_successes = self._attempt_borrowing(
                failed_zones + degraded_zones, available_for_borrowing
            )

        # Determine if this iteration passed
        # After borrowing, re-check only if we had successes
        if borrowing_successes > 0:
            # Simple heuristic: each success covers one shortfall
            remaining_failures = max(0, len(failed_zones) - borrowing_successes)
            passed = remaining_failures == 0
        else:
            passed = len(failed_zones) == 0

        # Determine failure mode
        failure_mode = None
        recovery_time = None

        if not passed:
            # Analyze failure mode
            if any(zone_status[z_id] == "skill_gap" for z_id in failed_zones):
                failure_mode = "skill_gap"
            elif len(failed_zones) > 2:
                failure_mode = "cascade"
            elif borrowing_attempts > 0 and borrowing_successes == 0:
                failure_mode = "capacity"
            else:
                failure_mode = "capacity"
        else:
            # System passed - estimate recovery time
            workload_factor = 1.0 + (len(degraded_zones) * 0.2)
            recovery_time = self.config.recovery_time_hours * workload_factor

        return N2IterationResult(
            iteration=iteration,
            faculty_pair_lost=faculty_pair,
            passed=passed,
            zones_failed=len(failed_zones),
            zones_degraded=len(degraded_zones),
            borrowing_attempts=borrowing_attempts,
            borrowing_successes=borrowing_successes,
            recovery_time=recovery_time,
            failure_mode=failure_mode,
        )

    def run(self) -> N2ScenarioResult:
        """
        Run all N-2 iterations and aggregate results.

        Returns:
            N2ScenarioResult with complete analysis
        """
        # Setup if not already done
        if not self._faculty:
            self.setup()

        # Run iterations
        self._results = []
        for i in range(self.config.iterations):
            result = self._run_iteration(i)
            self._results.append(result)

        # Aggregate and return results
        return self._aggregate_results()

    def _aggregate_results(self) -> N2ScenarioResult:
        """Build final result with statistics from all iterations."""
        passes = sum(1 for r in self._results if r.passed)
        failures = len(self._results) - passes

        # Collect failure modes
        failure_modes = Counter(
            r.failure_mode for r in self._results if r.failure_mode is not None
        )

        # Find most vulnerable pairs (pairs that caused failures)
        vulnerable_pairs = [r.faculty_pair_lost for r in self._results if not r.passed]
        most_vulnerable = Counter(vulnerable_pairs).most_common(5)

        # Calculate average recovery time for successful cases
        recovery_times = [
            r.recovery_time for r in self._results if r.recovery_time is not None
        ]
        avg_recovery = (
            sum(recovery_times) / len(recovery_times) if recovery_times else 0.0
        )

        # Calculate cascade rate
        cascades = sum(1 for r in self._results if r.failure_mode == "cascade")
        cascade_rate = cascades / failures if failures > 0 else 0.0

        # Track which zones failed most often
        zones_affected = defaultdict(int)
        for result in self._results:
            if not result.passed:
                # Determine which zones were affected
                for zone in self._zones:
                    lost_faculty_in_zone = (
                        set(result.faculty_pair_lost) & zone["faculty"]
                    )
                    if lost_faculty_in_zone:
                        zones_affected[zone["id"]] += 1

        # Generate recommendations
        recommendations = self._generate_recommendations(
            failure_modes=dict(failure_modes),
            vulnerable_pairs=[pair for pair, _ in most_vulnerable],
            zones_affected=dict(zones_affected),
        )

        return N2ScenarioResult(
            config=self.config,
            iterations_run=len(self._results),
            passes=passes,
            failures=failures,
            pass_rate=passes / len(self._results) if self._results else 0.0,
            failure_modes=dict(failure_modes),
            most_vulnerable_pairs=[pair for pair, _ in most_vulnerable],
            average_recovery_time=avg_recovery,
            cascade_rate=cascade_rate,
            zones_most_affected=dict(zones_affected),
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self,
        failure_modes: dict[str, int],
        vulnerable_pairs: list[tuple[int, int]],
        zones_affected: dict[int, int],
    ) -> list[str]:
        """
        Generate recommendations based on failure patterns.

        Args:
            failure_modes: Mapping of failure mode to count
            vulnerable_pairs: List of faculty pairs that caused failures
            zones_affected: Zones that failed most often

        Returns:
            List of actionable recommendations
        """
        recommendations = []

        # Overall pass rate recommendation
        passes = sum(1 for r in self._results if r.passed)
        pass_rate = passes / len(self._results) if self._results else 0.0

        if pass_rate < 0.95:
            recommendations.append(
                f"CRITICAL: N-2 pass rate is {pass_rate:.1%}. "
                f"Industry standard is >95%. Increase faculty redundancy."
            )
        elif pass_rate < 0.98:
            recommendations.append(
                f"WARNING: N-2 pass rate is {pass_rate:.1%}. "
                f"Target is >98% for high reliability."
            )
        else:
            recommendations.append(
                f"GOOD: N-2 pass rate is {pass_rate:.1%}. "
                f"System meets reliability standards."
            )

        # Skill gap recommendations
        if failure_modes.get("skill_gap", 0) > 0:
            skill_gap_rate = failure_modes["skill_gap"] / len(self._results)
            recommendations.append(
                f"Skill gap failures: {skill_gap_rate:.1%}. "
                f"Cross-train faculty in critical skills or add specialists."
            )

        # Cascade failure recommendations
        if failure_modes.get("cascade", 0) > 0:
            cascade_count = failure_modes["cascade"]
            recommendations.append(
                f"Cascade failures detected ({cascade_count} cases). "
                f"Review zone interdependencies and add circuit breakers."
            )

        # Capacity recommendations
        if failure_modes.get("capacity", 0) > 0:
            capacity_rate = failure_modes["capacity"] / len(self._results)
            recommendations.append(
                f"Capacity failures: {capacity_rate:.1%}. "
                f"Increase borrowing pool or add float faculty."
            )

        # Vulnerable pair recommendations
        if vulnerable_pairs:
            recommendations.append(
                f"Found {len(vulnerable_pairs)} critical faculty pairs. "
                f"Review faculty {vulnerable_pairs[0]} - they may have "
                f"unique skill combinations. Avoid simultaneous leave."
            )

        # Zone-specific recommendations
        if zones_affected:
            most_affected = max(zones_affected.items(), key=lambda x: x[1])
            zone_id, failure_count = most_affected
            recommendations.append(
                f"Zone {zone_id} failed in {failure_count} scenarios. "
                f"Add dedicated backup faculty or reduce minimum requirements."
            )

        # Borrowing effectiveness
        total_borrow_attempts = sum(r.borrowing_attempts for r in self._results)
        total_borrow_success = sum(r.borrowing_successes for r in self._results)
        if total_borrow_attempts > 0:
            borrow_success_rate = total_borrow_success / total_borrow_attempts
            if borrow_success_rate < 0.7:
                recommendations.append(
                    f"Borrowing success rate is low ({borrow_success_rate:.1%}). "
                    f"Improve cross-zone protocols or increase faculty flexibility."
                )

        return recommendations
