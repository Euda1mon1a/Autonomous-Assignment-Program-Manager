# Erlang-N1 Bridge Specification

> **Status:** Implementation-Ready
> **Created:** 2025-12-26
> **Purpose:** Quantify N-1 safety margins using Erlang C queuing theory

---

## Executive Summary

The N-1 contingency analyzer currently returns **binary pass/fail** results: either a faculty loss is survivable or it isn't. This binary output doesn't capture **how close** the system is to failure.

The Erlang-N1 Bridge enhances this by using **Erlang C queuing theory** to quantify the safety margin numerically. Instead of "system survives" vs. "system fails," we get:

- **Binary survival:** Does coverage meet minimum requirements? (existing)
- **Margin score:** How much buffer remains? (0.0 = critical, 1.0 = comfortable)
- **Wait probability:** Likelihood of delayed coverage under N-1 scenario
- **Offered load increase:** How much load shifts to remaining faculty

This enables **prioritized remediation**: fix the lowest-margin vulnerabilities first.

---

## Problem Statement

### Current State (Binary N-1)

```python
# From backend/app/resilience/contingency.py
vulnerabilities = analyzer.analyze_n1(faculty, blocks, assignments, coverage_requirements)

# Returns:
# Vulnerability(
#     faculty_id=UUID('abc...'),
#     severity="critical",  # Based on is_unique_provider
#     affected_blocks=15,
#     is_unique_provider=True
# )
```

**Limitations:**
1. **All critical vulnerabilities look the same** - Can't prioritize between two "critical" failures
2. **No quantification of risk** - "10% margin" vs. "90% margin" both show as "survives"
3. **False sense of security** - Binary pass with 1% margin looks the same as 50% margin
4. **Ignores queuing effects** - Doesn't account for wait time and service degradation

### Desired State (Quantified N-1 Margins)

```python
# Enhanced output
margin_result = bridge.quantify_n1_margins(n1_scenarios)

# Returns:
# N1MarginResult(
#     faculty_id=UUID('abc...'),
#     binary_survives=True,        # Original binary result
#     margin_score=0.18,            # NEW: 18% margin (critical!)
#     offered_load_increase=0.35,   # 35% more load on survivors
#     wait_probability=0.42,        # 42% chance of delayed coverage
#     severity_classification="critical_low_margin"  # Binary pass but risky
# )
```

---

## Mathematical Foundation

### 1. Erlang C Probability of Waiting

**Formula:**
```
P(wait) = C(A, c) = B(A, c) / (1 - (A/c)(1 - B(A, c)))

Where:
- A = offered_load = λ * μ (arrival_rate * service_time)
- c = number of servers (faculty)
- B(A, c) = Erlang B probability (blocking)
```

**Key Insight:** As load approaches capacity, `P(wait)` increases nonlinearly. This captures the "phase transition" risk that binary analysis misses.

### 2. N-1 Margin Calculation

**Core Formula:**
```python
margin_score = 1 - P(wait > threshold | N-1 scenario)

Components:
1. Base capacity (normal):    c_normal faculty
2. N-1 capacity (degraded):   c_n1 = c_normal - 1
3. Offered load (after loss): A_n1 = A_normal + load_from_lost_faculty
4. Wait threshold:            t = acceptable_wait_time

margin_score = 1 - P(wait) * exp(-(c_n1 - A_n1) * t / μ)
```

**Interpretation:**
- **margin_score = 1.0** → Immediate coverage guaranteed (0% wait probability)
- **margin_score = 0.5** → 50% of requests delayed beyond threshold
- **margin_score = 0.0** → System at capacity or overloaded
- **margin_score < 0** → Unstable queue (load exceeds capacity)

### 3. Offered Load Redistribution

When a faculty member becomes unavailable:

```python
# Original state
A_original = λ * μ  # Total offered load
c_original = N      # Total faculty

# After faculty loss
load_lost = (assignments_by_faculty[lost_id].count / total_assignments) * A_original
A_n1 = A_original   # Same total workload
c_n1 = N - 1        # One fewer server

# Offered load per remaining faculty
load_per_faculty = A_n1 / c_n1
load_increase_pct = (A_n1 / c_n1) - (A_original / c_original)
```

### 4. Service Level Under N-1

```python
service_level_n1 = 1 - P(wait) * exp(-(c_n1 - A_n1) * target_wait / μ)

# Example target: 95% coverage within 15 minutes
target_wait = 0.25 hours  # 15 min
service_time = 2.0 hours  # Avg shift duration

# If service_level_n1 < 0.95, system is degraded even though it "survives"
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. ContingencyAnalyzer.analyze_n1()                             │
│    → Generates list of N-1 scenarios (one per faculty)          │
│    → Each scenario: {faculty_id, affected_blocks, is_unique}    │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ n1_scenarios: list[Vulnerability]
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. ErlangN1Bridge.quantify_n1_margins(n1_scenarios)             │
│                                                                  │
│    For each scenario:                                            │
│    ┌─────────────────────────────────────────────────────┐     │
│    │ a. Extract faculty assignments                       │     │
│    │ b. Calculate offered_load_normal                     │     │
│    │ c. Simulate faculty loss → offered_load_n1          │     │
│    │ d. Calculate servers_n1 = servers_normal - 1        │     │
│    └─────────────────────────────────────────────────────┘     │
│                 ▼                                                │
│    ┌─────────────────────────────────────────────────────┐     │
│    │ ErlangCCalculator.erlang_c(offered_load_n1, c_n1)   │     │
│    │    → wait_probability                                │     │
│    │ ErlangCCalculator.calculate_service_level(...)       │     │
│    │    → service_level_n1                                │     │
│    └─────────────────────────────────────────────────────┘     │
│                 ▼                                                │
│    ┌─────────────────────────────────────────────────────┐     │
│    │ Calculate margin_score:                              │     │
│    │   margin = 1 - P(wait > threshold)                  │     │
│    │          = 1 - wait_prob * exp(-(c-A)*t/μ)          │     │
│    └─────────────────────────────────────────────────────┘     │
│                                                                  │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ margin_results: dict[faculty_id, N1MarginResult]
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. ResilienceService.get_prioritized_vulnerabilities()          │
│    → Sort by margin_score (ascending)                            │
│    → Flag "false pass" scenarios (binary_survives but margin<0.2)│
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Specification

### New Module: `backend/app/resilience/erlang_n1_bridge.py`

```python
"""
Erlang-N1 Bridge: Quantify N-1 safety margins using queuing theory.

Enhances binary N-1 contingency analysis with numerical margin scores.
"""

from dataclasses import dataclass
from uuid import UUID
import logging

from app.resilience.erlang_coverage import ErlangCCalculator
from app.resilience.contingency import Vulnerability

logger = logging.getLogger(__name__)


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
    margin_score: float           # 0.0-1.0 (0=critical, 1=comfortable)
    offered_load_increase: float  # Fractional increase in load per faculty
    wait_probability: float       # P(wait > 0) under N-1
    service_level_n1: float       # P(coverage within target time)

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

    Quantifies safety margins for N-1 scenarios using queuing theory metrics.
    """

    def __init__(
        self,
        target_wait_time: float = 0.25,     # 15 min in hours
        avg_service_time: float = 2.0,      # 2 hour shifts
        margin_thresholds: dict = None,
    ):
        """
        Initialize Erlang-N1 Bridge.

        Args:
            target_wait_time: Acceptable wait time for coverage (hours)
            avg_service_time: Average service/shift duration (hours)
            margin_thresholds: Dict of {"critical": 0.2, "marginal": 0.5}
        """
        self.calculator = ErlangCCalculator()
        self.target_wait_time = target_wait_time
        self.avg_service_time = avg_service_time

        self.thresholds = margin_thresholds or {
            "critical": 0.2,    # < 20% margin = critical
            "marginal": 0.5,    # 20-50% = marginal
            "comfortable": 0.5  # > 50% = comfortable
        }

    def quantify_n1_margins(
        self,
        faculty: list,
        blocks: list,
        assignments: list,
        n1_vulnerabilities: list[Vulnerability],
        coverage_requirements: dict[UUID, int] = None,
    ) -> dict[UUID, N1MarginResult]:
        """
        Quantify safety margins for N-1 scenarios using Erlang C.

        Args:
            faculty: List of faculty members
            blocks: List of scheduling blocks
            assignments: Current assignments
            n1_vulnerabilities: Output from ContingencyAnalyzer.analyze_n1()
            coverage_requirements: Required coverage per block

        Returns:
            Dict mapping faculty_id to N1MarginResult
        """
        results = {}

        # Calculate baseline metrics
        total_servers = len(faculty)
        total_required_blocks = sum(coverage_requirements.values()) if coverage_requirements else len(blocks)

        # Estimate offered load from current assignments
        # Assuming 2 blocks per day, estimate daily workload
        days_in_period = len({b.date for b in blocks}) if blocks else 1
        blocks_per_day = 2  # AM/PM
        offered_load_baseline = self._estimate_offered_load(
            assignments, total_servers, days_in_period, blocks_per_day
        )

        # For each N-1 scenario, calculate margin
        for vuln in n1_vulnerabilities:
            # Calculate load redistribution
            faculty_assignments = [a for a in assignments if a.person_id == vuln.faculty_id]
            faculty_workload_fraction = len(faculty_assignments) / len(assignments) if assignments else 0

            # N-1 scenario parameters
            servers_n1 = total_servers - 1
            offered_load_n1 = offered_load_baseline  # Total load unchanged

            # Check for instability
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
                        "Immediate cross-training or backup hire required"
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

                # Calculate margin score
                # Higher service level = higher margin
                margin_score = service_level

                # Classify severity based on margin
                if margin_score >= self.thresholds["comfortable"]:
                    classification = "comfortable"
                    recommendations = ["N-1 margin is acceptable"]
                elif margin_score >= self.thresholds["marginal"]:
                    classification = "marginal"
                    recommendations = [
                        f"Marginal N-1 margin ({margin_score:.1%})",
                        "Consider cross-training backup for this faculty"
                    ]
                elif margin_score >= self.thresholds["critical"]:
                    classification = "critical"
                    recommendations = [
                        f"CRITICAL: Low N-1 margin ({margin_score:.1%})",
                        "Urgent: Train backup faculty",
                        f"Loss would cause {wait_prob:.0%} chance of coverage delays"
                    ]
                else:
                    classification = "critical"
                    recommendations = [
                        f"CRITICAL: Very low N-1 margin ({margin_score:.1%})",
                        "IMMEDIATE ACTION REQUIRED: This is a single point of failure",
                        f"Loss would cause {wait_prob:.0%} chance of coverage delays"
                    ]

                # Check for false positives (binary pass but low margin)
                if not vuln.is_unique_provider and margin_score < self.thresholds["marginal"]:
                    recommendations.insert(0,
                        "⚠️  FALSE SENSE OF SECURITY: Binary analysis shows 'survives' "
                        "but margin is critically low"
                    )

                # Calculate load increase
                load_per_faculty_before = offered_load_baseline / total_servers
                load_per_faculty_after = offered_load_n1 / servers_n1
                load_increase = (load_per_faculty_after - load_per_faculty_before) / load_per_faculty_before

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

            except ValueError as e:
                # Erlang calculation failed (likely instability)
                logger.error(f"Erlang calculation failed for {vuln.faculty_name}: {e}")
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

        Args:
            margin_results: Output from quantify_n1_margins()

        Returns:
            Sorted list of N1MarginResult (worst first)
        """
        sorted_results = sorted(
            margin_results.values(),
            key=lambda r: (
                0 if r.margin_score < 0 else 1,  # Unstable first
                r.margin_score,                   # Then by margin (ascending)
                -r.affected_blocks                # Break ties by impact
            )
        )
        return sorted_results

    def _estimate_offered_load(
        self,
        assignments: list,
        total_servers: int,
        days_in_period: int,
        blocks_per_day: int = 2,
    ) -> float:
        """
        Estimate offered load from assignment data.

        Offered load A = λ * μ where:
        - λ = arrival rate (blocks per hour)
        - μ = service time (hours per block)

        For scheduling: estimate as total_workload / total_capacity
        """
        if not assignments or total_servers == 0:
            return 0.0

        # Total required coverage-hours
        total_blocks = len(assignments)

        # Assume each block is ~4 hours (half-day)
        hours_per_block = 4.0
        total_coverage_hours = total_blocks * hours_per_block

        # Total available capacity-hours
        # Assume 8 hours per day per faculty
        hours_per_faculty_per_day = 8.0
        total_capacity_hours = total_servers * days_in_period * hours_per_faculty_per_day

        # Offered load = demand / capacity in "servers" units
        # For Erlang, this needs to be in units of servers
        offered_load = (total_coverage_hours / total_capacity_hours) * total_servers

        return offered_load
```

---

## Output Schema

### N1MarginResult

```python
@dataclass
class N1MarginResult:
    """Enhanced N-1 analysis result with quantified margins."""

    # Identity
    faculty_id: UUID
    faculty_name: str

    # Original binary analysis (preserved)
    binary_survives: bool         # True if system survives loss (existing metric)
    affected_blocks: int           # Number of blocks under-covered
    is_unique_provider: bool       # True if sole provider for some service

    # NEW: Queuing-based metrics
    margin_score: float            # 0.0-1.0 (service level under N-1)
                                   # < 0.0 = unstable queue
    offered_load_increase: float   # Fractional load increase per faculty (e.g., 0.15 = +15%)
    wait_probability: float        # P(wait > 0) under N-1 scenario
    service_level_n1: float        # P(coverage within target time)

    # Interpretation
    severity_classification: str   # "comfortable", "marginal", "critical", "unstable"
    recommendations: list[str]     # Action items prioritized by urgency

    # Metadata (for debugging/audit)
    servers_before: int            # Faculty count before loss
    servers_after: int             # Faculty count after loss (servers_before - 1)
    offered_load_before: float     # Baseline offered load
    offered_load_after: float      # Offered load under N-1
```

**Example Output:**

```python
N1MarginResult(
    faculty_id=UUID('550e8400-e29b-41d4-a716-446655440000'),
    faculty_name="Dr. Alice Smith",

    # Binary (existing)
    binary_survives=True,          # ✓ System survives (min coverage met)
    affected_blocks=8,
    is_unique_provider=False,

    # Quantified (NEW)
    margin_score=0.18,             # ⚠️  Only 18% margin - CRITICAL!
    offered_load_increase=0.23,    # 23% more load per remaining faculty
    wait_probability=0.47,         # 47% chance of delayed coverage
    service_level_n1=0.18,         # Only 18% on-time coverage

    severity_classification="critical",
    recommendations=[
        "⚠️  FALSE SENSE OF SECURITY: Binary analysis shows 'survives' but margin is critically low",
        "CRITICAL: Low N-1 margin (18%)",
        "Urgent: Train backup faculty",
        "Loss would cause 47% chance of coverage delays"
    ],

    servers_before=12,
    servers_after=11,
    offered_load_before=9.2,
    offered_load_after=9.2
)
```

---

## Prioritization Logic

### Sorting Algorithm

```python
def get_prioritized_vulnerabilities(margin_results: dict) -> list:
    """Sort vulnerabilities for remediation priority."""

    return sorted(
        margin_results.values(),
        key=lambda r: (
            # 1. Unstable systems first (margin_score < 0)
            0 if r.margin_score < 0 else 1,

            # 2. Then by margin score (ascending = worst first)
            r.margin_score,

            # 3. Break ties by impact (more blocks = higher priority)
            -r.affected_blocks
        )
    )
```

### Priority Tiers

| Tier | Margin Score | Classification | Action Required |
|------|--------------|----------------|-----------------|
| **P0** | < 0.0 | Unstable | IMMEDIATE: System fails under N-1 |
| **P1** | 0.0 - 0.2 | Critical | URGENT: Cross-train backup within 30 days |
| **P2** | 0.2 - 0.5 | Marginal | Plan cross-training within 90 days |
| **P3** | > 0.5 | Comfortable | Monitor, no immediate action |

### Detection of "False Pass" Scenarios

```python
def detect_false_pass(result: N1MarginResult) -> bool:
    """Detect binary pass but critically low margin."""
    return (
        result.binary_survives and           # Binary says "ok"
        result.margin_score < 0.2            # But margin is critical
    )

# Flag in recommendations
if detect_false_pass(result):
    result.recommendations.insert(0,
        "⚠️  FALSE SENSE OF SECURITY: Binary analysis shows 'survives' "
        "but queuing analysis reveals critical margin"
    )
```

---

## Integration with ResilienceService

### New Method

```python
# In backend/app/resilience/service.py

def get_quantified_n1_report(
    self,
    faculty: list,
    blocks: list,
    assignments: list,
    coverage_requirements: dict[UUID, int] = None,
) -> dict:
    """
    Generate N-1 vulnerability report with quantified margins.

    Returns both binary and quantified analysis for comparison.
    """
    from app.resilience.erlang_n1_bridge import ErlangN1Bridge

    # Run binary N-1 analysis
    binary_vulns = self.contingency.analyze_n1(
        faculty, blocks, assignments, coverage_requirements or {}
    )

    # Enhance with Erlang margins
    bridge = ErlangN1Bridge(
        target_wait_time=0.25,      # 15 min
        avg_service_time=2.0,       # 2 hour shifts
    )
    margin_results = bridge.quantify_n1_margins(
        faculty, blocks, assignments, binary_vulns, coverage_requirements
    )

    # Get prioritized list
    prioritized = bridge.get_prioritized_vulnerabilities(margin_results)

    # Detect false positives
    false_pass_count = sum(
        1 for r in margin_results.values()
        if r.binary_survives and r.margin_score < 0.2
    )

    return {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_faculty": len(faculty),
            "binary_critical": sum(1 for v in binary_vulns if v.severity == "critical"),
            "quantified_critical": sum(1 for r in margin_results.values() if r.margin_score < 0.2),
            "false_pass_scenarios": false_pass_count,
            "unstable_scenarios": sum(1 for r in margin_results.values() if r.margin_score < 0),
        },
        "prioritized_vulnerabilities": [
            {
                "faculty_id": str(r.faculty_id),
                "faculty_name": r.faculty_name,
                "binary_survives": r.binary_survives,
                "margin_score": r.margin_score,
                "severity": r.severity_classification,
                "wait_probability": r.wait_probability,
                "load_increase_pct": r.offered_load_increase * 100,
                "recommendations": r.recommendations,
            }
            for r in prioritized[:10]  # Top 10 priorities
        ],
        "margin_distribution": {
            "unstable": sum(1 for r in margin_results.values() if r.margin_score < 0),
            "critical": sum(1 for r in margin_results.values() if 0 <= r.margin_score < 0.2),
            "marginal": sum(1 for r in margin_results.values() if 0.2 <= r.margin_score < 0.5),
            "comfortable": sum(1 for r in margin_results.values() if r.margin_score >= 0.5),
        }
    }
```

---

## Test Cases

### Test Suite: `backend/tests/resilience/test_erlang_n1_bridge.py`

```python
"""Tests for Erlang-N1 Bridge."""
import pytest
from uuid import uuid4
from app.resilience.erlang_n1_bridge import ErlangN1Bridge, N1MarginResult
from app.resilience.contingency import Vulnerability


class TestErlangN1Bridge:
    """Test suite for Erlang-N1 bridge."""

    def test_comfortable_margin(self):
        """Test scenario with comfortable N-1 margin (> 50%)."""
        bridge = ErlangN1Bridge()

        # 12 faculty, losing 1 → 11 remain
        # Offered load = 7.0 (well below 11)
        # Expected: High margin, low wait probability

        faculty = [Mock(id=uuid4(), name=f"Fac{i}") for i in range(12)]
        blocks = [Mock(id=uuid4(), date=date(2025, 1, i % 30 + 1)) for i in range(100)]
        assignments = [Mock(person_id=faculty[i % 12].id, block_id=blocks[i].id) for i in range(100)]

        binary_vuln = Vulnerability(
            faculty_id=faculty[0].id,
            faculty_name="Fac0",
            severity="medium",
            affected_blocks=8,
            is_unique_provider=False
        )

        results = bridge.quantify_n1_margins(faculty, blocks, assignments, [binary_vuln], {})
        result = results[faculty[0].id]

        assert result.margin_score > 0.5, "Should have comfortable margin"
        assert result.severity_classification == "comfortable"
        assert result.wait_probability < 0.1, "Wait probability should be low"

    def test_marginal_margin(self):
        """Test scenario with marginal margin (20-50%)."""
        # 10 faculty, offered load = 8.5 → tight but survivable
        # Expected: Marginal classification, moderate wait probability

        bridge = ErlangN1Bridge()
        # Setup to produce ~40% margin
        # ... (similar to above but tighter capacity)

        assert 0.2 <= result.margin_score < 0.5
        assert result.severity_classification == "marginal"
        assert "Consider cross-training backup" in result.recommendations

    def test_critical_low_margin(self):
        """Test scenario with critical low margin (< 20%)."""
        # 8 faculty, offered load = 7.8 → very tight
        # Expected: Critical classification, high wait probability

        bridge = ErlangN1Bridge()
        # Setup to produce ~10% margin
        # ...

        assert 0 <= result.margin_score < 0.2
        assert result.severity_classification == "critical"
        assert "CRITICAL" in result.recommendations[0]

    def test_false_pass_detection(self):
        """Test detection of binary pass but critically low margin."""
        # Binary says "survives" (not unique provider)
        # But margin < 20% (critical)

        bridge = ErlangN1Bridge()
        binary_vuln = Vulnerability(
            faculty_id=uuid4(),
            faculty_name="Dr. Smith",
            severity="medium",              # Binary says "medium" (not critical)
            affected_blocks=5,
            is_unique_provider=False        # Binary says "survives"
        )

        # Setup to produce low margin despite binary pass
        # ...

        result = results[binary_vuln.faculty_id]

        assert result.binary_survives == True, "Binary should show survives"
        assert result.margin_score < 0.2, "But margin should be critical"
        assert "FALSE SENSE OF SECURITY" in result.recommendations[0]

    def test_unstable_scenario(self):
        """Test scenario where offered load >= servers (unstable queue)."""
        # 5 faculty, offered load = 5.2 → unstable after losing 1 (4 < 5.2)

        bridge = ErlangN1Bridge()
        # Setup to produce instability
        # ...

        assert result.margin_score < 0, "Negative margin indicates instability"
        assert result.severity_classification == "unstable"
        assert "System becomes unstable" in result.recommendations[0]

    def test_prioritization_order(self):
        """Test that vulnerabilities are correctly prioritized."""
        bridge = ErlangN1Bridge()

        # Create scenarios with different margins
        scenarios = {
            "unstable": (margin=-0.5, expected_rank=1),
            "critical1": (margin=0.05, expected_rank=2),
            "critical2": (margin=0.15, expected_rank=3),
            "marginal": (margin=0.35, expected_rank=4),
            "comfortable": (margin=0.80, expected_rank=5),
        }

        # ... generate results for each

        prioritized = bridge.get_prioritized_vulnerabilities(margin_results)

        # Verify unstable comes first
        assert prioritized[0].severity_classification == "unstable"

        # Verify sorted by margin ascending
        for i in range(1, len(prioritized) - 1):
            if prioritized[i].margin_score >= 0 and prioritized[i+1].margin_score >= 0:
                assert prioritized[i].margin_score <= prioritized[i+1].margin_score
```

---

## Usage Examples

### Example 1: Basic Analysis

```python
from app.resilience.contingency import ContingencyAnalyzer
from app.resilience.erlang_n1_bridge import ErlangN1Bridge

# 1. Run binary N-1 analysis
analyzer = ContingencyAnalyzer()
binary_vulns = analyzer.analyze_n1(faculty, blocks, assignments, coverage_reqs)

# 2. Enhance with quantified margins
bridge = ErlangN1Bridge(
    target_wait_time=0.25,    # 15 min acceptable wait
    avg_service_time=2.0      # 2 hour shifts
)
margin_results = bridge.quantify_n1_margins(
    faculty, blocks, assignments, binary_vulns, coverage_reqs
)

# 3. Get prioritized action list
prioritized = bridge.get_prioritized_vulnerabilities(margin_results)

# 4. Report top priorities
for result in prioritized[:5]:
    print(f"\n{result.faculty_name}:")
    print(f"  Binary: {'✓ Survives' if result.binary_survives else '✗ FAILS'}")
    print(f"  Margin: {result.margin_score:.1%} ({result.severity_classification})")
    print(f"  Actions:")
    for rec in result.recommendations:
        print(f"    - {rec}")
```

**Output:**
```
Dr. Johnson:
  Binary: ✓ Survives
  Margin: 12% (critical)
  Actions:
    - ⚠️  FALSE SENSE OF SECURITY: Binary analysis shows 'survives' but margin is critically low
    - CRITICAL: Low N-1 margin (12%)
    - Urgent: Train backup faculty
    - Loss would cause 52% chance of coverage delays

Dr. Patel:
  Binary: ✗ FAILS
  Margin: -5% (unstable)
  Actions:
    - CRITICAL: System becomes unstable if this faculty is lost
    - Immediate cross-training or backup hire required
```

### Example 2: Integration with Dashboard

```python
# Dashboard endpoint: /api/resilience/n1-margins
@router.get("/n1-margins")
async def get_n1_margins(db: Session = Depends(get_db)):
    """Get quantified N-1 margins for dashboard."""

    service = ResilienceService(db)
    report = service.get_quantified_n1_report(
        faculty=await get_all_faculty(db),
        blocks=await get_upcoming_blocks(db),
        assignments=await get_current_assignments(db)
    )

    return {
        "summary": report["summary"],
        "top_priorities": report["prioritized_vulnerabilities"][:10],
        "margin_distribution": report["margin_distribution"]
    }
```

**Dashboard Display:**

```
┌─────────────────────────────────────────────────────────┐
│ N-1 Vulnerability Analysis (Quantified)                 │
├─────────────────────────────────────────────────────────┤
│ Summary:                                                 │
│   Total Faculty: 15                                      │
│   Binary Critical: 3                                     │
│   Quantified Critical: 7  ← MORE ACCURATE!               │
│   False Pass Scenarios: 4  ← Hidden risks detected!     │
├─────────────────────────────────────────────────────────┤
│ Margin Distribution:                                     │
│   ⚠️  Unstable: 1                                        │
│   🔴 Critical (0-20%): 6                                 │
│   🟡 Marginal (20-50%): 5                                │
│   🟢 Comfortable (>50%): 3                               │
├─────────────────────────────────────────────────────────┤
│ Top Priorities:                                          │
│ 1. Dr. Patel     │ Unstable (-5%) │ IMMEDIATE ACTION    │
│ 2. Dr. Johnson   │ Critical (12%) │ FALSE PASS ⚠️       │
│ 3. Dr. Lee       │ Critical (18%) │ Urgent              │
└─────────────────────────────────────────────────────────┘
```

---

## Performance Considerations

### Computational Complexity

- **Erlang C calculation:** O(c) per scenario (where c = servers)
- **Total for N-1:** O(n * c) where n = faculty count
- **For 20 faculty, 15 servers:** ~300 operations (negligible)

### Caching Strategy

```python
class ErlangN1Bridge:
    def __init__(self):
        self._margin_cache = {}  # Cache recent calculations

    def quantify_n1_margins(self, ...):
        # Cache key: hash of (faculty_ids, assignment_count, blocks_count)
        cache_key = self._compute_cache_key(faculty, assignments, blocks)

        if cache_key in self._margin_cache:
            cached_time, cached_result = self._margin_cache[cache_key]
            if datetime.now() - cached_time < timedelta(minutes=15):
                return cached_result

        # Compute...
        results = ...

        self._margin_cache[cache_key] = (datetime.now(), results)
        return results
```

---

## Future Enhancements

### Phase 2: Multi-Faculty Losses (N-2)

Extend to quantify margins for N-2 scenarios:

```python
def quantify_n2_margins(
    self,
    n2_fatal_pairs: list[FatalPair],
) -> dict[tuple[UUID, UUID], N2MarginResult]:
    """Quantify margins for simultaneous 2-faculty losses."""
    # Similar logic but with servers_n2 = servers - 2
```

### Phase 3: Dynamic Margin Monitoring

Real-time margin tracking as assignments change:

```python
@celery_app.task
def monitor_n1_margins():
    """Background task: recompute margins every 4 hours."""
    service = ResilienceService()
    margins = service.get_quantified_n1_report(...)

    # Alert if any margin drops below threshold
    for result in margins["prioritized_vulnerabilities"]:
        if result["margin_score"] < 0.2:
            send_alert(f"N-1 margin critical: {result['faculty_name']}")
```

### Phase 4: Margin-Based Scheduling

Use margins to guide schedule optimization:

```python
# In scheduling solver: add soft constraint to maximize minimum margin
constraint: min_margin >= 0.3
objective: maximize(min(margin_scores))
```

---

## References

### Erlang C Queuing Theory
- Erlang, A.K. (1917). "Solution of some Problems in the Theory of Probabilities"
- Cooper, R.B. (1981). "Introduction to Queueing Theory" (2nd ed.)
- Gross, D. et al. (2008). "Fundamentals of Queueing Theory" (4th ed.)

### Power Grid N-1 Analysis
- NERC Standard TPL-001-4: Transmission System Planning Performance Requirements
- IEEE Std 762-2006: IEEE Standard Definitions for Use in Reporting Electric Generating Unit Reliability

### Existing Implementation
- `/backend/app/resilience/erlang_coverage.py` - Erlang C calculator
- `/backend/app/resilience/contingency.py` - Binary N-1 analyzer
- `/backend/app/resilience/service.py` - Resilience service orchestrator

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-26 | 1.0 | Initial specification |

---

**Status:** Ready for implementation
**Estimated Effort:** 8-12 hours (implementation + tests + integration)
**Dependencies:** None (uses existing Erlang C and N-1 modules)
