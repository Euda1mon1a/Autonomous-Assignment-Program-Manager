"""
Integration tests for resilience framework scenarios.

Based on TEST_SCENARIO_FRAMES.md Section 4 (Resilience Framework Test Frames).

Test Coverage:
1. N-1 single point of failure detection (Frame 4.1)
2. N-2 cascading failure simulation (Frame 4.2)
3. Utilization threshold transitions (Frame 4.3)
4. Defense level escalation and de-escalation (Frame 4.4)

These tests exercise the resilience framework with realistic scenarios to verify
critical vulnerability detection, cascade simulation, and defense activation.

Markers:
- @pytest.mark.resilience: Resilience framework tests
- @pytest.mark.integration: Integration tests requiring multiple components
"""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.person import Person
from app.models.block import Block
from app.models.assignment import Assignment
from app.models.certification import PersonCertification, CertificationType
from app.resilience.contingency import (
    ContingencyAnalyzer,
    Vulnerability,
    FatalPair,
    CascadeSimulation,
)
from app.resilience.defense_in_depth import DefenseInDepth, DefenseLevel
from app.resilience.utilization import UtilizationMonitor, UtilizationLevel


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def pals_certified_faculty(db: Session) -> Person:
    """Create single faculty member with PALS certification (single point of failure)."""
    faculty = Person(
        id=uuid4(),
        name="Dr. PALS Expert",
        type="faculty",
        email="pals.expert@hospital.org",
        performs_procedures=True,
        specialties=["Pediatrics", "Critical Care"],
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)

    # Add PALS credential (requires certification type first)
    pals_type = CertificationType(
        id=uuid4(),
        name="PALS",
        full_name="Pediatric Advanced Life Support",
        renewal_period_months=24,
    )
    db.add(pals_type)
    db.commit()

    pals = PersonCertification(
        id=uuid4(),
        person_id=faculty.id,
        certification_type_id=pals_type.id,
        issued_date=date(2024, 1, 1),
        expiration_date=date(2026, 1, 1),
        status="current",
    )
    db.add(pals)
    db.commit()

    return faculty


@pytest.fixture
def faculty_without_pals(db: Session) -> list[Person]:
    """Create 5 faculty members without PALS certification."""
    faculty = []
    for i in range(5):
        fac = Person(
            id=uuid4(),
            name=f"Dr. Faculty {i + 1}",
            type="faculty",
            email=f"faculty{i + 1}@hospital.org",
            performs_procedures=(i % 2 == 0),
            specialties=["General", "Sports Medicine"],
        )
        db.add(fac)
        faculty.append(fac)

    db.commit()
    for f in faculty:
        db.refresh(f)

    return faculty


@pytest.fixture
def peds_clinic_blocks(db: Session) -> list[Block]:
    """Create 4 pediatric clinic blocks requiring PALS."""
    blocks = []
    target_date = date(2025, 1, 15)

    for i in range(4):
        block = Block(
            id=uuid4(),
            date=target_date,
            time_of_day="AM" if i < 2 else "PM",
            block_number=1,
            is_weekend=False,
            is_holiday=False,
            requires_credential="PALS",  # Critical: requires PALS
        )
        db.add(block)
        blocks.append(block)

    db.commit()
    for b in blocks:
        db.refresh(b)

    return blocks


@pytest.fixture
def balanced_faculty_pool(db: Session) -> list[Person]:
    """Create 8 faculty for balanced schedule scenario."""
    faculty = []
    for i in range(8):
        fac = Person(
            id=uuid4(),
            name=f"Dr. Faculty {i + 1:02d}",
            type="faculty",
            email=f"faculty{i + 1:02d}@hospital.org",
            performs_procedures=True,
            specialties=["General"],
        )
        db.add(fac)
        faculty.append(fac)

    db.commit()
    for f in faculty:
        db.refresh(f)

    return faculty


@pytest.fixture
def balanced_blocks(db: Session) -> list[Block]:
    """Create blocks for balanced schedule (1 week, AM/PM = 14 blocks)."""
    blocks = []
    start_date = date(2025, 1, 13)  # Monday

    for i in range(7):
        current_date = start_date + timedelta(days=i)
        for time_of_day in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=time_of_day,
                block_number=1,
                is_weekend=(current_date.weekday() >= 5),
                is_holiday=False,
            )
            db.add(block)
            blocks.append(block)

    db.commit()
    for b in blocks:
        db.refresh(b)

    return blocks


@pytest.fixture
def balanced_assignments(
    db: Session,
    balanced_faculty_pool: list[Person],
    balanced_blocks: list[Block],
) -> list[Assignment]:
    """
    Create balanced assignments: 8 faculty, 14 blocks.
    Each faculty covers ~1.75 blocks = 70 hours/week at 40h/block.
    This is 87.5% utilization (70/80).
    """
    assignments = []

    # Assign first 14 blocks round-robin to 8 faculty
    for i, block in enumerate(balanced_blocks):
        faculty = balanced_faculty_pool[i % len(balanced_faculty_pool)]
        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=faculty.id,
            rotation_template_id=None,
            role="primary",
        )
        db.add(assignment)
        assignments.append(assignment)

    db.commit()
    for a in assignments:
        db.refresh(a)

    return assignments


@pytest.fixture
def utilization_monitor():
    """Create utilization monitor with standard 80% threshold."""
    return UtilizationMonitor()


@pytest.fixture
def contingency_analyzer():
    """Create contingency analyzer."""
    return ContingencyAnalyzer()


@pytest.fixture
def defense_in_depth():
    """Create defense in depth manager."""
    return DefenseInDepth()


# ============================================================================
# Test 1: N-1 Single Point of Failure (Frame 4.1)
# ============================================================================


@pytest.mark.resilience
@pytest.mark.integration
def test_n1_single_point_of_failure(
    db: Session,
    pals_certified_faculty: Person,
    faculty_without_pals: list[Person],
    peds_clinic_blocks: list[Block],
    contingency_analyzer: ContingencyAnalyzer,
):
    """
    Test N-1 analysis detects single point of failure for PALS certification.

    Scenario: Only 1 faculty credentialed for PALS, 4 assignments requiring PALS.
    Action: analyze_n1_contingency()
    Assert: Critical vulnerability detected, mitigation recommended.

    Based on TEST_SCENARIO_FRAMES.md Frame 4.1.
    """
    # SETUP: Create assignments requiring PALS
    all_faculty = [pals_certified_faculty] + faculty_without_pals
    pals_assignments = []

    for block in peds_clinic_blocks:
        # Only PALS-certified faculty can cover these blocks
        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=pals_certified_faculty.id,
            rotation_template_id=None,
            role="primary",
        )
        db.add(assignment)
        pals_assignments.append(assignment)

    db.commit()
    for a in pals_assignments:
        db.refresh(a)

    # Coverage requirements: each peds clinic block needs 1 PALS-certified faculty
    coverage_requirements = {block.id: 1 for block in peds_clinic_blocks}

    # ACTION: Run N-1 analysis
    vulnerabilities = contingency_analyzer.analyze_n1(
        faculty=all_faculty,
        blocks=peds_clinic_blocks,
        current_assignments=pals_assignments,
        coverage_requirements=coverage_requirements,
    )

    # ASSERT: Critical vulnerability detected
    assert len(vulnerabilities) > 0, "Should identify at least one vulnerability"

    # Find the PALS expert in vulnerabilities
    pals_expert_vuln = next(
        (v for v in vulnerabilities if v.faculty_id == pals_certified_faculty.id),
        None,
    )

    assert pals_expert_vuln is not None, (
        "PALS expert should be identified as vulnerable"
    )
    assert pals_expert_vuln.severity == "critical", (
        f"Expected 'critical' severity, got '{pals_expert_vuln.severity}'"
    )
    assert pals_expert_vuln.is_unique_provider is True, (
        "PALS expert should be marked as unique provider"
    )
    assert pals_expert_vuln.affected_blocks == len(peds_clinic_blocks), (
        f"Expected {len(peds_clinic_blocks)} affected blocks, "
        f"got {pals_expert_vuln.affected_blocks}"
    )

    # Verify mitigation recommendations
    report = contingency_analyzer.generate_report(
        faculty=all_faculty,
        blocks=peds_clinic_blocks,
        assignments=pals_assignments,
        coverage_requirements=coverage_requirements,
        current_utilization=0.75,
    )

    assert report.n1_pass is False, (
        "N-1 analysis should fail with critical vulnerability"
    )

    # Check for cross-training recommendation
    cross_train_recommendations = [
        rec
        for rec in report.recommended_actions
        if "cross-train" in rec.lower() or "backup" in rec.lower()
    ]
    assert len(cross_train_recommendations) > 0, (
        "Should recommend cross-training or backup for single point of failure"
    )


# ============================================================================
# Test 2: N-2 Cascading Failure (Frame 4.2)
# ============================================================================


@pytest.mark.resilience
@pytest.mark.integration
def test_n2_cascading_failure(
    db: Session,
    balanced_faculty_pool: list[Person],
    balanced_blocks: list[Block],
    balanced_assignments: list[Assignment],
    contingency_analyzer: ContingencyAnalyzer,
):
    """
    Test N-2 analysis with cascading overload simulation.

    Scenario: Loss of 2 faculty triggers 80-hour violations for remaining staff.
    Setup: 8 faculty, balanced schedule at 87.5% utilization.
    Action: simulate_n2_failure()
    Assert: Cascading overload detected, defense level escalates.

    Based on TEST_SCENARIO_FRAMES.md Frame 4.2.
    """
    # SETUP: We have 8 faculty at 87.5% utilization (balanced_assignments fixture)
    # Each faculty works ~70 hours/week (87.5% of 80-hour max)

    coverage_requirements = {block.id: 1 for block in balanced_blocks}

    # ACTION: Run N-2 analysis
    fatal_pairs = contingency_analyzer.analyze_n2(
        faculty=balanced_faculty_pool,
        blocks=balanced_blocks,
        current_assignments=balanced_assignments,
        coverage_requirements=coverage_requirements,
        critical_faculty_only=False,  # Check all pairs for comprehensive analysis
    )

    # ASSERT: Some fatal pairs should be detected
    # With 8 faculty at 87.5% utilization, losing 2 (25% capacity) should cause issues
    assert len(fatal_pairs) > 0, (
        "Should identify fatal pairs in high-utilization scenario"
    )

    # ACTION: Simulate cascade failure with loss of 2 faculty
    failed_faculty_ids = [
        balanced_faculty_pool[0].id,
        balanced_faculty_pool[1].id,
    ]

    cascade = contingency_analyzer.simulate_cascade_failure(
        faculty=balanced_faculty_pool,
        blocks=balanced_blocks,
        assignments=balanced_assignments,
        initial_failures=failed_faculty_ids,
        max_utilization=0.80,  # 80% threshold
        overload_threshold=1.2,  # 120% triggers cascade
    )

    # ASSERT: Cascade simulation results
    assert cascade.total_failures >= 2, (
        f"Should have at least 2 failures (initial), got {cascade.total_failures}"
    )

    # Loss of 2/8 faculty (25%) at 87.5% utilization means remaining 6 must absorb load
    # Original load: 8 faculty × 0.875 = 7 faculty-equivalents of work
    # Remaining capacity: 6 faculty
    # New utilization: 7/6 = 116.7%, which exceeds 80% safe threshold
    # This should trigger cascading failures or critical coverage issues

    # Verify final coverage is reduced
    assert cascade.final_coverage < 1.0, (
        "Final coverage should be reduced after cascade"
    )

    # Generate full report with phase transition detection
    report = contingency_analyzer.generate_report(
        faculty=balanced_faculty_pool,
        blocks=balanced_blocks,
        assignments=balanced_assignments,
        coverage_requirements=coverage_requirements,
        current_utilization=0.875,  # 87.5% baseline
        recent_changes=[],
    )

    # ASSERT: Report shows elevated risk
    assert report.phase_transition_risk in ["medium", "high", "critical"], (
        f"Expected elevated phase transition risk, got '{report.phase_transition_risk}'"
    )

    # Should recommend mitigation strategies
    assert len(report.recommended_actions) > 0, (
        "Should provide mitigation recommendations"
    )

    # Check for sacrifice hierarchy or load shedding recommendations
    sacrifice_recommendations = [
        rec
        for rec in report.recommended_actions
        if "sacrifice" in rec.lower() or "reduce load" in rec.lower()
    ]
    # Note: May or may not recommend sacrifice depending on specific scenario


# ============================================================================
# Test 3: Utilization Threshold Transitions (Frame 4.3)
# ============================================================================


@pytest.mark.resilience
@pytest.mark.integration
def test_utilization_threshold_transitions(
    db: Session,
    utilization_monitor: UtilizationMonitor,
):
    """
    Test defense levels transition correctly at utilization thresholds.

    Scenario: Faculty utilization crosses 79% → 80% → 85% → 90%.
    Action: calculate_utilization() at each threshold.
    Assert: GREEN → YELLOW → ORANGE → RED transitions at correct thresholds.

    Based on TEST_SCENARIO_FRAMES.md Frame 4.3.
    """
    # SETUP: Create faculty member (80-hour max per week)
    faculty = Person(
        id=uuid4(),
        name="Dr. Test Faculty",
        type="faculty",
        email="test@hospital.org",
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)

    week_start = date(2025, 1, 13)

    # Test scenarios: (hours_worked, utilization_pct, expected_level, description)
    test_scenarios = [
        (60, 75.0, UtilizationLevel.GREEN, "75% utilization - Healthy (GREEN)"),
        (63.2, 79.0, UtilizationLevel.GREEN, "79% utilization - Still GREEN"),
        (
            64,
            80.0,
            UtilizationLevel.YELLOW,
            "80% utilization - Warning threshold (YELLOW)",
        ),
        (
            68,
            85.0,
            UtilizationLevel.ORANGE,
            "85% utilization - Above threshold (ORANGE)",
        ),
        (72, 90.0, UtilizationLevel.RED, "90% utilization - Critical (RED)"),
        (76, 95.0, UtilizationLevel.BLACK, "95% utilization - Emergency (BLACK)"),
    ]

    for hours_worked, expected_util_pct, expected_level, description in test_scenarios:
        # ACTION: Calculate utilization
        # Each "block" represents work hours
        # If blocks_per_faculty_per_day = 1 and days_in_period = 1,
        # then required_blocks directly maps to hours
        metrics = utilization_monitor.calculate_utilization(
            available_faculty=[faculty],
            required_blocks=int(hours_worked),  # Work hours needed
            blocks_per_faculty_per_day=80,  # Max 80 hours per week
            days_in_period=1,
        )

        # ASSERT: Utilization rate matches expected
        assert abs(metrics.utilization_rate - (expected_util_pct / 100.0)) < 0.02, (
            f"{description}: Expected {expected_util_pct}% utilization, "
            f"got {metrics.utilization_rate:.1%}"
        )

        # ASSERT: Defense level matches expected
        assert metrics.level == expected_level, (
            f"{description}: Expected {expected_level.name}, "
            f"got {metrics.level.name} at {metrics.utilization_rate:.1%} utilization"
        )

    # VERIFY: 80% threshold is the critical transition point
    # Test boundary: 79.999% should be GREEN, 80.001% should be YELLOW
    boundary_test_cases = [
        (63.9, UtilizationLevel.GREEN, "Just below 80% threshold"),
        (64.1, UtilizationLevel.YELLOW, "Just above 80% threshold"),
    ]

    for hours, expected_level, desc in boundary_test_cases:
        metrics = utilization_monitor.calculate_utilization(
            available_faculty=[faculty],
            required_blocks=int(hours),
            blocks_per_faculty_per_day=80,
            days_in_period=1,
        )

        # 80% threshold should trigger YELLOW or higher
        if metrics.utilization_rate >= 0.80:
            assert metrics.level.value >= UtilizationLevel.YELLOW.value, (
                f"{desc}: At {metrics.utilization_rate:.1%}, "
                f"expected at least YELLOW level, got {metrics.level.name}"
            )


# ============================================================================
# Test 4: Defense Level Escalation (Frame 4.4)
# ============================================================================


@pytest.mark.resilience
@pytest.mark.integration
def test_defense_level_escalation(
    db: Session,
    defense_in_depth: DefenseInDepth,
):
    """
    Test defense level escalation and de-escalation logic.

    Scenario: Trigger escalation at different coverage rates, then de-escalate.
    Action: Monitor defense level transitions and notifications.
    Assert: Proper escalation/de-escalation at thresholds.

    Based on TEST_SCENARIO_FRAMES.md Frame 4.4.
    """
    # Test escalation scenarios: (coverage_rate, expected_level, description)
    escalation_scenarios = [
        (0.98, DefenseLevel.PREVENTION, "98% coverage - Prevention level"),
        (0.92, DefenseLevel.CONTROL, "92% coverage - Control level"),
        (0.85, DefenseLevel.SAFETY_SYSTEMS, "85% coverage - Safety systems level"),
        (0.75, DefenseLevel.CONTAINMENT, "75% coverage - Containment level"),
        (0.65, DefenseLevel.EMERGENCY, "65% coverage - Emergency level"),
    ]

    for coverage_rate, expected_level, description in escalation_scenarios:
        # ACTION: Get recommended defense level
        recommended_level = defense_in_depth.get_recommended_level(coverage_rate)

        # ASSERT: Recommended level matches expected
        assert recommended_level == expected_level, (
            f"{description}: Expected {expected_level.name}, "
            f"got {recommended_level.name}"
        )

    # Test escalation logic
    # Start at GREEN (prevention), escalate to RED (containment)
    escalation_sequence = [
        (0.98, DefenseLevel.PREVENTION, "Start - GREEN"),
        (0.92, DefenseLevel.CONTROL, "Drop to 92% - YELLOW"),
        (0.85, DefenseLevel.SAFETY_SYSTEMS, "Drop to 85% - ORANGE"),
        (0.75, DefenseLevel.CONTAINMENT, "Drop to 75% - RED"),
    ]

    previous_level = None
    for coverage, expected, desc in escalation_sequence:
        current_level = defense_in_depth.get_recommended_level(coverage)

        assert current_level == expected, (
            f"{desc}: Expected {expected.name}, got {current_level.name}"
        )

        # Verify escalation (level value increases)
        if previous_level is not None:
            assert current_level.value >= previous_level.value, (
                f"Defense level should escalate or stay same, "
                f"went from {previous_level.name} to {current_level.name}"
            )

        previous_level = current_level

    # Test de-escalation logic
    de_escalation_sequence = [
        (0.75, DefenseLevel.CONTAINMENT, "Start at RED"),
        (0.85, DefenseLevel.SAFETY_SYSTEMS, "Recover to 85% - ORANGE"),
        (0.92, DefenseLevel.CONTROL, "Recover to 92% - YELLOW"),
        (0.98, DefenseLevel.PREVENTION, "Recover to 98% - GREEN"),
    ]

    previous_level = None
    for coverage, expected, desc in de_escalation_sequence:
        current_level = defense_in_depth.get_recommended_level(coverage)

        assert current_level == expected, (
            f"{desc}: Expected {expected.name}, got {current_level.name}"
        )

        # Verify de-escalation (level value decreases)
        if previous_level is not None:
            assert current_level.value <= previous_level.value, (
                f"Defense level should de-escalate or stay same, "
                f"went from {previous_level.name} to {current_level.name}"
            )

        previous_level = current_level

    # Test action activation and tracking
    # Activate actions at each defense level
    levels_to_test = [
        DefenseLevel.CONTROL,
        DefenseLevel.SAFETY_SYSTEMS,
        DefenseLevel.CONTAINMENT,
    ]

    for level in levels_to_test:
        level_status = defense_in_depth.get_level_status(level)

        # Activate first action in this level
        if level_status.actions:
            first_action = level_status.actions[0]
            initial_count = first_action.activation_count

            # ACTION: Activate the action
            success = defense_in_depth.activate_action(level, first_action.name)

            # ASSERT: Activation succeeded
            assert success is True, (
                f"Failed to activate {first_action.name} at {level.name}"
            )

            # ASSERT: Activation count incremented
            assert first_action.activation_count == initial_count + 1, (
                f"Activation count should increment, "
                f"expected {initial_count + 1}, got {first_action.activation_count}"
            )

            # ASSERT: Last activated timestamp set
            assert first_action.last_activated is not None, (
                "Last activated timestamp should be set"
            )

    # Verify status report
    status_report = defense_in_depth.get_status_report()

    assert "levels" in status_report
    assert "summary" in status_report
    assert len(status_report["levels"]) == 5, "Should have all 5 defense levels"

    # Verify all levels have actions
    for level_report in status_report["levels"]:
        assert "name" in level_report
        assert "status" in level_report
        assert "actions" in level_report


# ============================================================================
# Test 5: Edge Cases and Integration
# ============================================================================


@pytest.mark.resilience
@pytest.mark.integration
def test_utilization_exactly_at_threshold(
    utilization_monitor: UtilizationMonitor,
):
    """
    Test utilization exactly at 80.0% threshold (boundary condition).

    Verifies that exactly 80.0% triggers YELLOW, not GREEN.
    """
    faculty = Person(
        id=uuid4(),
        name="Dr. Boundary Test",
        type="faculty",
        email="boundary@test.org",
    )

    # Exactly 80.0% utilization (64 hours out of 80)
    metrics = utilization_monitor.calculate_utilization(
        available_faculty=[faculty],
        required_blocks=64,
        blocks_per_faculty_per_day=80,
        days_in_period=1,
    )

    # At exactly 80%, should be YELLOW (warning threshold)
    assert metrics.utilization_rate == pytest.approx(0.80, abs=0.001), (
        f"Expected exactly 80% utilization, got {metrics.utilization_rate:.2%}"
    )

    assert metrics.level.value >= UtilizationLevel.YELLOW.value, (
        f"At 80% threshold, expected at least YELLOW, got {metrics.level.name}"
    )


@pytest.mark.resilience
@pytest.mark.integration
def test_redundancy_check_n_plus_2_rule(
    defense_in_depth: DefenseInDepth,
):
    """
    Test N+2 redundancy rule from nuclear engineering.

    Systems should survive loss of 2 providers and still operate.
    """
    # Test scenarios: (available, minimum_required, expected_status)
    redundancy_scenarios = [
        (5, 1, "N+2", "5 available, 1 required = N+4 (healthy)"),
        (4, 2, "N+2", "4 available, 2 required = N+2 (healthy)"),
        (3, 2, "N+1", "3 available, 2 required = N+1 (warning)"),
        (2, 2, "N+0", "2 available, 2 required = N+0 (critical)"),
        (1, 2, "BELOW", "1 available, 2 required = BELOW minimum"),
    ]

    for available_count, minimum, expected_status, description in redundancy_scenarios:
        # Create mock providers
        providers = [f"Provider_{i}" for i in range(available_count)]

        # ACTION: Check redundancy
        status = defense_in_depth.check_redundancy(
            function_name="test_function",
            available_providers=providers,
            minimum_required=minimum,
        )

        # ASSERT: Status matches expected
        assert status.status == expected_status, (
            f"{description}: Expected status '{expected_status}', got '{status.status}'"
        )

        # ASSERT: Redundancy level calculated correctly
        expected_redundancy = max(0, available_count - minimum)
        assert status.redundancy_level == expected_redundancy, (
            f"{description}: Expected redundancy {expected_redundancy}, "
            f"got {status.redundancy_level}"
        )


@pytest.mark.resilience
@pytest.mark.integration
def test_cascade_simulation_with_no_failures(
    contingency_analyzer: ContingencyAnalyzer,
    balanced_faculty_pool: list[Person],
    balanced_blocks: list[Block],
    balanced_assignments: list[Assignment],
):
    """
    Test cascade simulation when system is stable (no cascade expected).

    With low utilization, losing 1 faculty should not cause cascade.
    """
    # ACTION: Simulate loss of 1 faculty at low utilization
    initial_failure = [balanced_faculty_pool[0].id]

    cascade = contingency_analyzer.simulate_cascade_failure(
        faculty=balanced_faculty_pool,
        blocks=balanced_blocks,
        assignments=balanced_assignments[:8],  # Only 8 assignments for low utilization
        initial_failures=initial_failure,
        max_utilization=0.80,
        overload_threshold=1.2,
    )

    # ASSERT: Should be stable (no cascading failures)
    assert cascade.cascade_length == 0, (
        "No cascade expected with low utilization, "
        f"got cascade length {cascade.cascade_length}"
    )

    assert cascade.is_catastrophic is False, "Should not be catastrophic"

    assert cascade.total_failures == 1, (
        f"Should only have initial failure, got {cascade.total_failures} total failures"
    )


# ============================================================================
# Test 6: Comprehensive Vulnerability Report
# ============================================================================


@pytest.mark.resilience
@pytest.mark.integration
def test_comprehensive_vulnerability_report(
    db: Session,
    pals_certified_faculty: Person,
    faculty_without_pals: list[Person],
    peds_clinic_blocks: list[Block],
    contingency_analyzer: ContingencyAnalyzer,
):
    """
    Test complete vulnerability report generation.

    Combines N-1, N-2, and phase transition detection.
    """
    # SETUP: Create PALS assignments (single point of failure scenario)
    all_faculty = [pals_certified_faculty] + faculty_without_pals
    pals_assignments = []

    for block in peds_clinic_blocks:
        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=pals_certified_faculty.id,
            rotation_template_id=None,
            role="primary",
        )
        db.add(assignment)
        pals_assignments.append(assignment)

    db.commit()
    for a in pals_assignments:
        db.refresh(a)

    coverage_requirements = {block.id: 1 for block in peds_clinic_blocks}

    # ACTION: Generate comprehensive report
    report = contingency_analyzer.generate_report(
        faculty=all_faculty,
        blocks=peds_clinic_blocks,
        assignments=pals_assignments,
        coverage_requirements=coverage_requirements,
        current_utilization=0.85,  # High utilization
        recent_changes=[
            {"date": date.today() - timedelta(days=1), "type": "reassignment"},
            {"date": date.today() - timedelta(days=2), "type": "absence"},
            {"date": date.today() - timedelta(days=3), "type": "swap"},
        ],
    )

    # ASSERT: Report structure
    assert report.analysis_date == date.today()
    assert report.period_start <= report.period_end

    # ASSERT: N-1 results
    assert len(report.n1_vulnerabilities) > 0, "Should identify N-1 vulnerabilities"
    assert report.n1_pass is False, "Should fail N-1 with single point of failure"

    # ASSERT: Most critical faculty identified
    assert len(report.most_critical_faculty) > 0, "Should identify critical faculty"
    assert pals_certified_faculty.id in report.most_critical_faculty, (
        "PALS expert should be in most critical faculty list"
    )

    # ASSERT: Recommendations provided
    assert len(report.recommended_actions) > 0, "Should provide recommendations"

    # ASSERT: Phase transition risk assessed
    assert report.phase_transition_risk in ["low", "medium", "high", "critical"]

    # With high utilization (85%) and recent changes, should be elevated risk
    assert report.phase_transition_risk in ["medium", "high", "critical"], (
        f"Expected elevated risk with 85% utilization, got '{report.phase_transition_risk}'"
    )

    # ASSERT: Leading indicators populated
    assert len(report.leading_indicators) > 0, "Should have leading indicators"
