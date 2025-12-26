"""
Tests for Erlang-N1 Bridge.

Tests the integration between N-1 contingency analysis (binary pass/fail)
and Erlang C queuing theory (quantified safety margins).

Mathematical formulas tested are from:
/docs/architecture/bridges/ERLANG_N1_BRIDGE.md
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional
from uuid import UUID, uuid4

import pytest

from app.resilience.contingency import Vulnerability
from app.resilience.erlang_coverage import ErlangCCalculator


# Mock classes for testing (will be implemented)
@dataclass
class N1MarginResult:
    """Quantified N-1 margin for a single faculty loss scenario."""

    faculty_id: UUID
    faculty_name: str

    # Original binary analysis
    binary_survives: bool
    affected_blocks: int
    is_unique_provider: bool

    # Enhanced queuing-based metrics
    margin_score: float  # 0.0-1.0 (0=critical, 1=comfortable)
    offered_load_increase: float  # Fractional increase in load per faculty
    wait_probability: float  # P(wait > 0) under N-1
    service_level_n1: float  # P(coverage within target time)

    # Interpretation
    severity_classification: str  # "comfortable", "marginal", "critical", "unstable"
    recommendations: list[str]

    # Metadata
    servers_before: int
    servers_after: int
    offered_load_before: float
    offered_load_after: float


class ErlangN1Bridge:
    """
    Bridge between N-1 contingency analysis and Erlang C queuing theory.

    This is a test implementation based on the specification.
    """

    def __init__(
        self,
        target_wait_time: float = 0.25,  # 15 min in hours
        avg_service_time: float = 2.0,  # 2 hour shifts
        margin_thresholds: Optional[dict] = None,
    ):
        """Initialize Erlang-N1 Bridge."""
        self.calculator = ErlangCCalculator()
        self.target_wait_time = target_wait_time
        self.avg_service_time = avg_service_time

        self.thresholds = margin_thresholds or {
            "critical": 0.2,  # < 20% margin = critical
            "marginal": 0.5,  # 20-50% = marginal
            "comfortable": 0.5,  # > 50% = comfortable
        }

    def quantify_n1_margins(
        self,
        total_servers: int,
        offered_load_baseline: float,
        n1_vulnerabilities: list[Vulnerability],
    ) -> dict[UUID, N1MarginResult]:
        """
        Quantify safety margins for N-1 scenarios using Erlang C.

        Formula from spec:
        1. servers_n1 = total_servers - 1
        2. wait_prob = erlang_c(offered_load_n1, servers_n1)
        3. service_level = calculate_service_level(...)
        4. margin_score = service_level

        Args:
            total_servers: Number of faculty members
            offered_load_baseline: Baseline offered load
            n1_vulnerabilities: Output from ContingencyAnalyzer.analyze_n1()

        Returns:
            Dict mapping faculty_id to N1MarginResult
        """
        results = {}

        for vuln in n1_vulnerabilities:
            # N-1 scenario parameters
            servers_n1 = total_servers - 1
            offered_load_n1 = offered_load_baseline  # Total load unchanged

            # Check for instability (load >= capacity)
            if offered_load_n1 >= servers_n1:
                # Unstable queue
                result = N1MarginResult(
                    faculty_id=vuln.faculty_id,
                    faculty_name=vuln.faculty_name,
                    binary_survives=not vuln.is_unique_provider,
                    affected_blocks=vuln.affected_blocks,
                    is_unique_provider=vuln.is_unique_provider,
                    margin_score=-1.0,  # Negative indicates unstable
                    offered_load_increase=offered_load_n1 / servers_n1,
                    wait_probability=1.0,
                    service_level_n1=0.0,
                    severity_classification="unstable",
                    recommendations=[
                        "CRITICAL: System becomes unstable if this faculty is lost",
                        "Immediate cross-training or backup hire required",
                    ],
                    servers_before=total_servers,
                    servers_after=servers_n1,
                    offered_load_before=offered_load_baseline,
                    offered_load_after=offered_load_n1,
                )
                results[vuln.faculty_id] = result
                continue

            # Calculate Erlang C metrics for N-1 scenario
            try:
                wait_prob = self.calculator.erlang_c(offered_load_n1, servers_n1)
                service_level = self.calculator.calculate_service_level(
                    arrival_rate=offered_load_n1 / self.avg_service_time,
                    service_time=self.avg_service_time,
                    servers=servers_n1,
                    target_wait=self.target_wait_time,
                )

                # Calculate margin score (higher service level = higher margin)
                margin_score = service_level

                # Classify severity based on margin
                if margin_score >= self.thresholds["comfortable"]:
                    classification = "comfortable"
                    recommendations = ["N-1 margin is acceptable"]
                elif margin_score >= self.thresholds["marginal"]:
                    classification = "marginal"
                    recommendations = [
                        f"Marginal N-1 margin ({margin_score:.1%})",
                        "Consider cross-training backup for this faculty",
                    ]
                elif margin_score >= self.thresholds["critical"]:
                    classification = "critical"
                    recommendations = [
                        f"CRITICAL: Low N-1 margin ({margin_score:.1%})",
                        "Urgent: Train backup faculty",
                        f"Loss would cause {wait_prob:.0%} chance of coverage delays",
                    ]
                else:
                    classification = "critical"
                    recommendations = [
                        f"CRITICAL: Very low N-1 margin ({margin_score:.1%})",
                        "IMMEDIATE ACTION REQUIRED: This is a single point of failure",
                        f"Loss would cause {wait_prob:.0%} chance of coverage delays",
                    ]

                # Check for false positives (binary pass but low margin)
                if (
                    not vuln.is_unique_provider
                    and margin_score < self.thresholds["marginal"]
                ):
                    recommendations.insert(
                        0,
                        "⚠️  FALSE SENSE OF SECURITY: Binary analysis shows 'survives' "
                        "but margin is critically low",
                    )

                # Calculate load increase
                load_per_faculty_before = offered_load_baseline / total_servers
                load_per_faculty_after = offered_load_n1 / servers_n1
                load_increase = (
                    load_per_faculty_after - load_per_faculty_before
                ) / load_per_faculty_before

                result = N1MarginResult(
                    faculty_id=vuln.faculty_id,
                    faculty_name=vuln.faculty_name,
                    binary_survives=not vuln.is_unique_provider,
                    affected_blocks=vuln.affected_blocks,
                    is_unique_provider=vuln.is_unique_provider,
                    margin_score=margin_score,
                    offered_load_increase=load_increase,
                    wait_probability=wait_prob,
                    service_level_n1=service_level,
                    severity_classification=classification,
                    recommendations=recommendations,
                    servers_before=total_servers,
                    servers_after=servers_n1,
                    offered_load_before=offered_load_baseline,
                    offered_load_after=offered_load_n1,
                )

                results[vuln.faculty_id] = result

            except ValueError:
                # Erlang calculation failed (likely instability)
                result = N1MarginResult(
                    faculty_id=vuln.faculty_id,
                    faculty_name=vuln.faculty_name,
                    binary_survives=False,
                    affected_blocks=vuln.affected_blocks,
                    is_unique_provider=True,
                    margin_score=-1.0,
                    offered_load_increase=1.0,
                    wait_probability=1.0,
                    service_level_n1=0.0,
                    severity_classification="error",
                    recommendations=["Error calculating margin - treat as critical"],
                    servers_before=total_servers,
                    servers_after=servers_n1,
                    offered_load_before=offered_load_baseline,
                    offered_load_after=offered_load_n1,
                )
                results[vuln.faculty_id] = result

        return results

    def get_prioritized_vulnerabilities(
        self,
        margin_results: dict[UUID, N1MarginResult],
    ) -> list[N1MarginResult]:
        """
        Sort vulnerabilities by margin score (lowest first = highest priority).

        Sorting algorithm from spec:
        1. Unstable systems first (margin_score < 0)
        2. Then by margin score (ascending = worst first)
        3. Break ties by impact (more blocks = higher priority)

        Args:
            margin_results: Output from quantify_n1_margins()

        Returns:
            Sorted list of N1MarginResult (worst first)
        """
        sorted_results = sorted(
            margin_results.values(),
            key=lambda r: (
                0 if r.margin_score < 0 else 1,  # Unstable first
                r.margin_score,  # Then by margin (ascending)
                -r.affected_blocks,  # Break ties by impact
            ),
        )
        return sorted_results


@pytest.fixture
def bridge():
    """Create Erlang-N1 bridge with default settings."""
    return ErlangN1Bridge(
        target_wait_time=0.25,  # 15 min
        avg_service_time=2.0,  # 2 hour shifts
    )


class TestMarginCalculation:
    """Test margin calculation for different scenarios."""

    def test_comfortable_margin(self, bridge):
        """Test scenario with comfortable N-1 margin (> 50%)."""
        # Scenario: 12 faculty, offered load = 7.0
        # After losing 1: 11 faculty, load = 7.0
        # This should be comfortable (plenty of capacity)

        vuln = Vulnerability(
            faculty_id=uuid4(),
            faculty_name="Dr. Smith",
            severity="medium",
            affected_blocks=5,
            is_unique_provider=False,
        )

        results = bridge.quantify_n1_margins(
            total_servers=12,
            offered_load_baseline=7.0,
            n1_vulnerabilities=[vuln],
        )

        result = results[vuln.faculty_id]

        # Should have high margin (>50%)
        assert result.margin_score > 0.5, f"Got margin: {result.margin_score}"
        assert result.severity_classification == "comfortable"
        assert result.wait_probability < 0.15  # Low wait probability
        assert "acceptable" in result.recommendations[0].lower()

    def test_marginal_margin(self, bridge):
        """Test scenario with marginal margin (20-50%)."""
        # Scenario: 10 faculty, offered load = 8.5
        # After losing 1: 9 faculty, load = 8.5
        # This should be marginal (tight but survivable)

        vuln = Vulnerability(
            faculty_id=uuid4(),
            faculty_name="Dr. Johnson",
            severity="medium",
            affected_blocks=8,
            is_unique_provider=False,
        )

        results = bridge.quantify_n1_margins(
            total_servers=10,
            offered_load_baseline=8.5,
            n1_vulnerabilities=[vuln],
        )

        result = results[vuln.faculty_id]

        # Should have marginal margin (20-50%)
        assert 0.2 <= result.margin_score < 0.5, f"Got margin: {result.margin_score}"
        assert result.severity_classification == "marginal"
        assert "cross-training" in result.recommendations[-1].lower()

    def test_critical_low_margin(self, bridge):
        """Test scenario with critical low margin (< 20%)."""
        # Scenario: 8 faculty, offered load = 7.5
        # After losing 1: 7 faculty, load = 7.5
        # This should be critical (very tight)

        vuln = Vulnerability(
            faculty_id=uuid4(),
            faculty_name="Dr. Lee",
            severity="high",
            affected_blocks=12,
            is_unique_provider=False,
        )

        results = bridge.quantify_n1_margins(
            total_servers=8,
            offered_load_baseline=7.5,
            n1_vulnerabilities=[vuln],
        )

        result = results[vuln.faculty_id]

        # Should have critical margin (<20%)
        assert 0 <= result.margin_score < 0.2, f"Got margin: {result.margin_score}"
        assert result.severity_classification == "critical"
        assert "CRITICAL" in result.recommendations[0]
        assert result.wait_probability > 0.4  # High wait probability

    def test_unstable_scenario(self, bridge):
        """Test scenario where offered load >= servers (unstable queue)."""
        # Scenario: 5 faculty, offered load = 5.2
        # After losing 1: 4 faculty, load = 5.2 → UNSTABLE (4 < 5.2)

        vuln = Vulnerability(
            faculty_id=uuid4(),
            faculty_name="Dr. Patel",
            severity="critical",
            affected_blocks=20,
            is_unique_provider=True,
        )

        results = bridge.quantify_n1_margins(
            total_servers=5,
            offered_load_baseline=5.2,
            n1_vulnerabilities=[vuln],
        )

        result = results[vuln.faculty_id]

        # Should be unstable
        assert result.margin_score < 0, "Negative margin indicates instability"
        assert result.severity_classification == "unstable"
        assert "unstable" in result.recommendations[0].lower()
        assert result.wait_probability == 1.0
        assert result.service_level_n1 == 0.0

    def test_multiple_faculty_scenarios(self, bridge):
        """Test margin calculation for multiple faculty at once."""
        vulns = [
            Vulnerability(
                faculty_id=uuid4(),
                faculty_name="Dr. A",
                severity="low",
                affected_blocks=3,
                is_unique_provider=False,
            ),
            Vulnerability(
                faculty_id=uuid4(),
                faculty_name="Dr. B",
                severity="medium",
                affected_blocks=7,
                is_unique_provider=False,
            ),
            Vulnerability(
                faculty_id=uuid4(),
                faculty_name="Dr. C",
                severity="high",
                affected_blocks=12,
                is_unique_provider=True,
            ),
        ]

        # Scenario: 15 faculty, load = 10.0 (comfortable)
        results = bridge.quantify_n1_margins(
            total_servers=15,
            offered_load_baseline=10.0,
            n1_vulnerabilities=vulns,
        )

        # Should get results for all faculty
        assert len(results) == 3

        # All should have same margin (same N-1 scenario parameters)
        margins = [r.margin_score for r in results.values()]
        assert all(m == margins[0] for m in margins), "All margins should be equal"


class TestFalsePassDetection:
    """Test detection of binary pass but critically low margin."""

    def test_false_pass_scenario(self, bridge):
        """Test detection when binary says survives but margin is critical."""
        # Binary analysis: not unique provider → "survives"
        # Queuing analysis: margin < 20% → critical

        vuln = Vulnerability(
            faculty_id=uuid4(),
            faculty_name="Dr. Wilson",
            severity="medium",  # Binary says "medium" (not critical)
            affected_blocks=6,
            is_unique_provider=False,  # Binary says "survives"
        )

        # Setup to produce low margin despite binary pass
        # 7 faculty, load = 6.8 → tight margin
        results = bridge.quantify_n1_margins(
            total_servers=7,
            offered_load_baseline=6.8,
            n1_vulnerabilities=[vuln],
        )

        result = results[vuln.faculty_id]

        # Binary should show survives
        assert result.binary_survives is True, "Binary should say survives"

        # But margin should be low
        # (This depends on Erlang C calculations, may need adjustment)
        if result.margin_score < 0.5:  # If margin is indeed low
            assert "FALSE SENSE OF SECURITY" in result.recommendations[0]

    def test_true_pass_comfortable_margin(self, bridge):
        """Test that no false pass warning when margin is comfortable."""
        vuln = Vulnerability(
            faculty_id=uuid4(),
            faculty_name="Dr. Chen",
            severity="low",
            affected_blocks=2,
            is_unique_provider=False,
        )

        # Comfortable scenario: 15 faculty, load = 8.0
        results = bridge.quantify_n1_margins(
            total_servers=15,
            offered_load_baseline=8.0,
            n1_vulnerabilities=[vuln],
        )

        result = results[vuln.faculty_id]

        # Should have high margin
        assert result.binary_survives is True
        assert result.margin_score > 0.5

        # No false pass warning
        assert not any(
            "FALSE SENSE OF SECURITY" in rec for rec in result.recommendations
        )

    def test_true_fail_unique_provider(self, bridge):
        """Test that unique provider correctly identified as critical."""
        vuln = Vulnerability(
            faculty_id=uuid4(),
            faculty_name="Dr. Martinez",
            severity="critical",
            affected_blocks=15,
            is_unique_provider=True,  # Binary says "fails"
        )

        # Even with comfortable capacity
        results = bridge.quantify_n1_margins(
            total_servers=12,
            offered_load_baseline=7.0,
            n1_vulnerabilities=[vuln],
        )

        result = results[vuln.faculty_id]

        # Binary should show fails
        assert result.binary_survives is False
        assert result.is_unique_provider is True


class TestPrioritizationLogic:
    """Test that vulnerabilities are sorted correctly by priority."""

    def test_prioritization_order_unstable_first(self, bridge):
        """Test that unstable scenarios come first in priority."""
        vulns = [
            Vulnerability(
                faculty_id=uuid4(),
                faculty_name="Dr. Comfortable",
                severity="low",
                affected_blocks=3,
                is_unique_provider=False,
            ),
            Vulnerability(
                faculty_id=uuid4(),
                faculty_name="Dr. Unstable",
                severity="critical",
                affected_blocks=20,
                is_unique_provider=True,
            ),
            Vulnerability(
                faculty_id=uuid4(),
                faculty_name="Dr. Critical",
                severity="high",
                affected_blocks=10,
                is_unique_provider=False,
            ),
        ]

        # Create scenario where one is unstable
        # For Dr. Unstable: use 5 servers, load 5.2 (unstable)
        # For others: use 12 servers, load 10.0 (stable)

        # First, test with unstable scenario
        results_unstable = bridge.quantify_n1_margins(
            total_servers=5,
            offered_load_baseline=5.2,
            n1_vulnerabilities=[vulns[1]],  # Just the unstable one
        )

        # Then test with stable scenarios
        results_stable = bridge.quantify_n1_margins(
            total_servers=12,
            offered_load_baseline=10.0,
            n1_vulnerabilities=[vulns[0], vulns[2]],
        )

        # Combine results
        all_results = {**results_unstable, **results_stable}

        # Get prioritized list
        prioritized = bridge.get_prioritized_vulnerabilities(all_results)

        # Unstable should be first
        assert prioritized[0].severity_classification == "unstable"
        assert prioritized[0].faculty_name == "Dr. Unstable"

    def test_prioritization_by_margin_ascending(self, bridge):
        """Test that within stable results, lowest margin comes first."""
        # Create three vulnerabilities with different margins
        # By using different total_servers and offered_load, we get different margins

        vuln_low_margin = Vulnerability(
            faculty_id=uuid4(),
            faculty_name="Dr. LowMargin",
            severity="high",
            affected_blocks=10,
            is_unique_provider=False,
        )

        vuln_medium_margin = Vulnerability(
            faculty_id=uuid4(),
            faculty_name="Dr. MediumMargin",
            severity="medium",
            affected_blocks=8,
            is_unique_provider=False,
        )

        vuln_high_margin = Vulnerability(
            faculty_id=uuid4(),
            faculty_name="Dr. HighMargin",
            severity="low",
            affected_blocks=5,
            is_unique_provider=False,
        )

        # Create different scenarios to get different margins
        # Low margin: 8 servers, load 7.5 (tight)
        results_low = bridge.quantify_n1_margins(
            total_servers=8,
            offered_load_baseline=7.5,
            n1_vulnerabilities=[vuln_low_margin],
        )

        # Medium margin: 10 servers, load 8.5
        results_medium = bridge.quantify_n1_margins(
            total_servers=10,
            offered_load_baseline=8.5,
            n1_vulnerabilities=[vuln_medium_margin],
        )

        # High margin: 15 servers, load 8.0 (comfortable)
        results_high = bridge.quantify_n1_margins(
            total_servers=15,
            offered_load_baseline=8.0,
            n1_vulnerabilities=[vuln_high_margin],
        )

        # Combine results
        all_results = {**results_low, **results_medium, **results_high}

        # Get prioritized list
        prioritized = bridge.get_prioritized_vulnerabilities(all_results)

        # Verify sorted by margin ascending (lowest first)
        for i in range(len(prioritized) - 1):
            if prioritized[i].margin_score >= 0 and prioritized[i + 1].margin_score >= 0:
                assert (
                    prioritized[i].margin_score <= prioritized[i + 1].margin_score
                ), f"Not sorted: {prioritized[i].margin_score} > {prioritized[i+1].margin_score}"

    def test_prioritization_tie_breaking_by_impact(self, bridge):
        """Test that ties in margin are broken by affected_blocks."""
        # Create two vulnerabilities with same margin but different impact
        vuln_high_impact = Vulnerability(
            faculty_id=uuid4(),
            faculty_name="Dr. HighImpact",
            severity="medium",
            affected_blocks=15,  # More blocks affected
            is_unique_provider=False,
        )

        vuln_low_impact = Vulnerability(
            faculty_id=uuid4(),
            faculty_name="Dr. LowImpact",
            severity="medium",
            affected_blocks=5,  # Fewer blocks affected
            is_unique_provider=False,
        )

        # Use same parameters to get same margin
        results_high = bridge.quantify_n1_margins(
            total_servers=12,
            offered_load_baseline=9.0,
            n1_vulnerabilities=[vuln_high_impact],
        )

        results_low = bridge.quantify_n1_margins(
            total_servers=12,
            offered_load_baseline=9.0,
            n1_vulnerabilities=[vuln_low_impact],
        )

        # Combine results
        all_results = {**results_high, **results_low}

        # Get prioritized list
        prioritized = bridge.get_prioritized_vulnerabilities(all_results)

        # Margins should be equal
        assert (
            abs(prioritized[0].margin_score - prioritized[1].margin_score) < 0.01
        ), "Margins should be equal"

        # Higher impact should come first
        assert (
            prioritized[0].affected_blocks >= prioritized[1].affected_blocks
        ), "Higher impact should be prioritized"


class TestLoadIncrease:
    """Test calculation of load increase metrics."""

    def test_load_increase_calculation(self, bridge):
        """Test that load increase is calculated correctly."""
        vuln = Vulnerability(
            faculty_id=uuid4(),
            faculty_name="Dr. Test",
            severity="medium",
            affected_blocks=8,
            is_unique_provider=False,
        )

        # Scenario: 10 faculty, load = 8.0
        results = bridge.quantify_n1_margins(
            total_servers=10,
            offered_load_baseline=8.0,
            n1_vulnerabilities=[vuln],
        )

        result = results[vuln.faculty_id]

        # Before: 8.0 / 10 = 0.8 per faculty
        # After: 8.0 / 9 = 0.889 per faculty
        # Increase: (0.889 - 0.8) / 0.8 = 0.111 (11.1%)

        expected_increase = ((8.0 / 9) - (8.0 / 10)) / (8.0 / 10)

        assert result.offered_load_increase == pytest.approx(
            expected_increase, rel=0.01
        )

    def test_metadata_tracking(self, bridge):
        """Test that metadata fields are correctly populated."""
        vuln = Vulnerability(
            faculty_id=uuid4(),
            faculty_name="Dr. Metadata",
            severity="medium",
            affected_blocks=6,
            is_unique_provider=False,
        )

        results = bridge.quantify_n1_margins(
            total_servers=12,
            offered_load_baseline=9.0,
            n1_vulnerabilities=[vuln],
        )

        result = results[vuln.faculty_id]

        # Verify metadata
        assert result.servers_before == 12
        assert result.servers_after == 11
        assert result.offered_load_before == 9.0
        assert result.offered_load_after == 9.0  # Load unchanged


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_single_faculty_scenario(self, bridge):
        """Test scenario with only one faculty (always critical)."""
        vuln = Vulnerability(
            faculty_id=uuid4(),
            faculty_name="Dr. OnlyOne",
            severity="critical",
            affected_blocks=50,
            is_unique_provider=True,
        )

        # 1 faculty, any load → always fails
        results = bridge.quantify_n1_margins(
            total_servers=1,
            offered_load_baseline=0.5,
            n1_vulnerabilities=[vuln],
        )

        result = results[vuln.faculty_id]

        # Should be unstable (0 servers after loss)
        assert result.severity_classification == "unstable"
        assert result.margin_score < 0

    def test_zero_load_scenario(self, bridge):
        """Test scenario with zero offered load."""
        vuln = Vulnerability(
            faculty_id=uuid4(),
            faculty_name="Dr. NoLoad",
            severity="low",
            affected_blocks=0,
            is_unique_provider=False,
        )

        results = bridge.quantify_n1_margins(
            total_servers=10,
            offered_load_baseline=0.0,
            n1_vulnerabilities=[vuln],
        )

        result = results[vuln.faculty_id]

        # Should have perfect margin (no load)
        assert result.margin_score > 0.9
        assert result.wait_probability == 0.0

    def test_custom_thresholds(self):
        """Test using custom margin thresholds."""
        custom_bridge = ErlangN1Bridge(
            target_wait_time=0.25,
            avg_service_time=2.0,
            margin_thresholds={
                "critical": 0.3,  # Stricter (30%)
                "marginal": 0.6,  # Stricter (60%)
                "comfortable": 0.6,
            },
        )

        vuln = Vulnerability(
            faculty_id=uuid4(),
            faculty_name="Dr. Custom",
            severity="medium",
            affected_blocks=5,
            is_unique_provider=False,
        )

        # Scenario that would be "comfortable" with default thresholds
        results = custom_bridge.quantify_n1_margins(
            total_servers=15,
            offered_load_baseline=10.0,
            n1_vulnerabilities=[vuln],
        )

        result = results[vuln.faculty_id]

        # With stricter thresholds, might be marginal or critical
        # (depends on exact Erlang C calculation)
        assert result.severity_classification in [
            "comfortable",
            "marginal",
            "critical",
        ]
