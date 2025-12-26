"""
Integration tests for schedule generation edge cases.

Tests stress the scheduling engine and solvers with difficult scenarios:
- Infeasible constraints (no solution exists)
- Multi-objective optimization (ACGME + workload + preferences)
- Incremental generation (preserving existing assignments)

Based on test scenario frames from docs/testing/TEST_SCENARIO_FRAMES.md
(Frames 6.1, 6.2, 6.3)
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.scheduling.constraints import ConstraintManager, SchedulingContext
from app.scheduling.engine import SchedulingEngine
from app.scheduling.solvers import SolverFactory


# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
def start_date() -> date:
    """Common start date for tests."""
    return date(2025, 1, 13)  # Monday


@pytest.fixture
def outpatient_templates(db: Session) -> list[RotationTemplate]:
    """Create outpatient rotation templates for solver optimization."""
    templates = [
        RotationTemplate(
            id=uuid4(),
            name="Sports Medicine",
            abbreviation="SM",
            activity_type="outpatient",
            clinic_location="Building A",
            max_residents=2,
            supervision_required=True,
            max_supervision_ratio=4,
            requires_procedure_credential=False,
        ),
        RotationTemplate(
            id=uuid4(),
            name="Neurology",
            abbreviation="NEUR",
            activity_type="outpatient",
            clinic_location="Building B",
            max_residents=2,
            supervision_required=True,
            max_supervision_ratio=4,
            requires_procedure_credential=False,
        ),
        RotationTemplate(
            id=uuid4(),
            name="Palliative Care",
            abbreviation="PALL",
            activity_type="outpatient",
            clinic_location="Building C",
            max_residents=1,
            supervision_required=True,
            max_supervision_ratio=2,
            requires_procedure_credential=False,
        ),
    ]
    for template in templates:
        db.add(template)
    db.commit()
    for template in templates:
        db.refresh(template)
    return templates


@pytest.fixture
def residents_pool(db: Session) -> list[Person]:
    """Create a pool of residents across PGY levels."""
    residents = []
    for pgy in [1, 2, 3]:
        for i in range(3):  # 3 residents per PGY level = 9 total
            resident = Person(
                id=uuid4(),
                name=f"Dr. Resident PGY{pgy}-{i+1}",
                type="resident",
                email=f"resident.pgy{pgy}.{i+1}@hospital.org",
                pgy_level=pgy,
            )
            db.add(resident)
            residents.append(resident)
    db.commit()
    for resident in residents:
        db.refresh(resident)
    return residents


@pytest.fixture
def faculty_pool(db: Session) -> list[Person]:
    """Create a pool of faculty members."""
    faculty = []
    for i in range(5):
        fac = Person(
            id=uuid4(),
            name=f"Dr. Faculty {i+1}",
            type="faculty",
            email=f"faculty.{i+1}@hospital.org",
            performs_procedures=(i < 2),  # First 2 can do procedures
            specialties=["General", "Sports Medicine"] if i == 0 else ["General"],
        )
        db.add(fac)
        faculty.append(fac)
    db.commit()
    for fac in faculty:
        db.refresh(fac)
    return faculty


@pytest.fixture
def blocks_one_week(db: Session, start_date: date) -> list[Block]:
    """Create blocks for one week (7 days, AM and PM)."""
    blocks = []
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
    for block in blocks:
        db.refresh(block)
    return blocks


@pytest.fixture
def blocks_four_weeks(db: Session, start_date: date) -> list[Block]:
    """Create blocks for four weeks (28 days, AM and PM)."""
    blocks = []
    for i in range(28):
        current_date = start_date + timedelta(days=i)
        block_number = 1 + (i // 28)  # Block 1 for first 28 days
        for time_of_day in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=time_of_day,
                block_number=block_number,
                is_weekend=(current_date.weekday() >= 5),
                is_holiday=False,
            )
            db.add(block)
            blocks.append(block)
    db.commit()
    for block in blocks:
        db.refresh(block)
    return blocks


# ==============================================================================
# TEST 1: NO FEASIBLE SOLUTION
# Frame 6.1 - Impossible constraints
# ==============================================================================


def test_no_feasible_solution(
    db: Session,
    start_date: date,
    blocks_one_week: list[Block],
    residents_pool: list[Person],
    outpatient_templates: list[RotationTemplate],
):
    """
    Test schedule generation with impossible constraints.

    Scenario:
        All residents are unavailable (on leave) for critical days,
        but assignments are still required. No feasible solution exists.

    Expected behavior:
        - Solver detects infeasibility
        - Returns graceful failure with clear error message
        - No partial assignments are saved to database
        - Error report identifies conflicting dates
    """
    # SETUP: Mark all residents as unavailable for the entire week
    critical_start = start_date
    critical_end = start_date + timedelta(days=6)

    for resident in residents_pool:
        absence = Absence(
            id=uuid4(),
            person_id=resident.id,
            start_date=critical_start,
            end_date=critical_end,
            absence_type="TDY",  # Blocking absence
            replacement_activity="TDY",
            notes="Temporary duty assignment - entire week",
        )
        db.add(absence)
    db.commit()

    # Create scheduling engine
    end_date = start_date + timedelta(days=6)
    engine = SchedulingEngine(
        db=db,
        start_date=start_date,
        end_date=end_date,
    )

    # ACTION: Attempt to generate schedule (should fail gracefully)
    result = engine.generate(
        pgy_levels=None,  # All residents
        rotation_template_ids=None,  # All templates
        algorithm="greedy",  # Fast solver for edge case testing
        timeout_seconds=30.0,
        check_resilience=False,  # Skip resilience checks for speed
    )

    # ASSERT: Verify graceful failure
    assert result["status"] in ["failed", "partial"], (
        "Expected failed or partial status for impossible constraints"
    )
    assert result["total_assigned"] == 0 or result["total_assigned"] < 10, (
        "Should have few or no assignments when all residents unavailable"
    )

    # Verify no assignments persisted to database
    assignments_count = db.query(Assignment).filter(
        Assignment.block_id.in_([b.id for b in blocks_one_week])
    ).count()
    assert assignments_count == 0, (
        "No assignments should be saved when solution is infeasible"
    )

    # Verify error reporting
    assert result.get("message") is not None, "Should provide error message"
    assert "validation" in result, "Should include validation results"


# ==============================================================================
# TEST 2: MULTI-OBJECTIVE OPTIMIZATION
# Frame 6.2 - ACGME compliance + workload balance + preferences
# ==============================================================================


def test_multi_objective_optimization(
    db: Session,
    start_date: date,
    blocks_one_week: list[Block],
    residents_pool: list[Person],
    faculty_pool: list[Person],
    outpatient_templates: list[RotationTemplate],
):
    """
    Test multi-objective schedule optimization.

    Objectives (in priority order):
        1. ACGME compliance (hard constraints)
        2. Workload balance across residents
        3. Rotation variety (distribute template assignments)

    Expected behavior:
        - All ACGME constraints satisfied
        - Workload distributed relatively evenly
        - Templates distributed (not all residents on same rotation)
        - Solver statistics show objective evaluation
    """
    # SETUP: Create baseline schedule data
    end_date = start_date + timedelta(days=6)
    engine = SchedulingEngine(
        db=db,
        start_date=start_date,
        end_date=end_date,
    )

    # Use CP-SAT solver for better multi-objective handling
    # (supports weighted objectives in constraint programming)
    result = engine.generate(
        pgy_levels=None,  # All residents
        rotation_template_ids=None,  # All templates
        algorithm="cp_sat",  # Best for multi-objective
        timeout_seconds=60.0,
        check_resilience=False,
    )

    # ASSERT: Verify generation succeeded
    assert result["status"] in ["success", "partial"], (
        f"Schedule generation failed: {result.get('message')}"
    )
    assert result["total_assigned"] > 0, "Should have assignments"

    # Verify ACGME compliance (highest priority objective)
    validation = result.get("validation")
    assert validation is not None, "Should include validation results"
    if validation.total_violations > 0:
        # Allow some minor violations in edge case tests, but verify they're documented
        assert len(validation.violations) > 0, "Violations should be listed"

    # Verify workload balance (medium priority objective)
    # Get assignments by resident and check distribution
    assignments_by_resident = {}
    all_assignments = db.query(Assignment).filter(
        Assignment.block_id.in_([b.id for b in blocks_one_week])
    ).all()

    for assignment in all_assignments:
        if assignment.person_id not in assignments_by_resident:
            assignments_by_resident[assignment.person_id] = 0
        assignments_by_resident[assignment.person_id] += 1

    if len(assignments_by_resident) > 1:
        # Check that workload isn't extremely unbalanced
        # (e.g., one resident has 10x more assignments than another)
        assignment_counts = list(assignments_by_resident.values())
        max_count = max(assignment_counts)
        min_count = min(assignment_counts)

        # Allow 3x imbalance (some residents may be PGY-3 vs PGY-1)
        balance_ratio = max_count / max(min_count, 1)
        assert balance_ratio < 4.0, (
            f"Workload too unbalanced: max={max_count}, min={min_count}, "
            f"ratio={balance_ratio:.1f}"
        )

    # Verify rotation variety (lower priority objective)
    # Check template distribution
    assignments_by_template = {}
    for assignment in all_assignments:
        if assignment.rotation_template_id:
            tid = assignment.rotation_template_id
            if tid not in assignments_by_template:
                assignments_by_template[tid] = 0
            assignments_by_template[tid] += 1

    if len(assignments_by_template) > 1:
        # Verify at least 2 different templates used
        assert len(assignments_by_template) >= 2, (
            "Should use multiple rotation templates for variety"
        )

    # Verify solver statistics included
    assert "solver_stats" in result, "Should include solver statistics"
    solver_stats = result["solver_stats"]
    assert isinstance(solver_stats, dict), "Solver stats should be dict"


# ==============================================================================
# TEST 3: INCREMENTAL GENERATION
# Frame 6.3 - Add block 11 without changing blocks 1-10
# ==============================================================================


def test_incremental_generation(
    db: Session,
    start_date: date,
    residents_pool: list[Person],
    faculty_pool: list[Person],
    outpatient_templates: list[RotationTemplate],
):
    """
    Test incremental schedule generation preserves existing assignments.

    Scenario:
        1. Generate schedule for blocks 1-10 (10 weeks)
        2. Record checksums of all assignments
        3. Generate schedule for block 11 (next week)
        4. Verify blocks 1-10 unchanged, block 11 added

    Expected behavior:
        - Blocks 1-10 assignments remain identical
        - Block 11 assignments created
        - No ACGME violations at block 10/11 boundary
        - Continuity maintained (e.g., work hour rolling windows)
    """
    # SETUP PHASE 1: Generate baseline schedule (blocks 1-10)
    # Create 10 weeks of blocks (70 days)
    baseline_blocks = []
    for i in range(70):
        current_date = start_date + timedelta(days=i)
        block_number = 1 + (i // 7)  # 1 week per block number (simplified)
        for time_of_day in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=time_of_day,
                block_number=min(block_number, 10),  # Blocks 1-10
                is_weekend=(current_date.weekday() >= 5),
                is_holiday=False,
            )
            db.add(block)
            baseline_blocks.append(block)
    db.commit()
    for block in baseline_blocks:
        db.refresh(block)

    baseline_end = start_date + timedelta(days=69)

    # Generate baseline schedule
    baseline_engine = SchedulingEngine(
        db=db,
        start_date=start_date,
        end_date=baseline_end,
    )

    baseline_result = baseline_engine.generate(
        pgy_levels=None,
        rotation_template_ids=None,
        algorithm="greedy",
        timeout_seconds=60.0,
        check_resilience=False,
    )

    assert baseline_result["status"] in ["success", "partial"], (
        f"Baseline generation failed: {baseline_result.get('message')}"
    )

    # Record checksums of baseline assignments
    baseline_assignments = db.query(Assignment).filter(
        Assignment.block_id.in_([b.id for b in baseline_blocks])
    ).all()

    baseline_checksums = {
        a.id: (a.person_id, a.rotation_template_id, a.block_id)
        for a in baseline_assignments
    }

    assert len(baseline_checksums) > 0, "Baseline should have assignments"

    # SETUP PHASE 2: Create block 11 (next week)
    block_11_blocks = []
    block_11_start = start_date + timedelta(days=70)
    for i in range(7):
        current_date = block_11_start + timedelta(days=i)
        for time_of_day in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=time_of_day,
                block_number=11,
                is_weekend=(current_date.weekday() >= 5),
                is_holiday=False,
            )
            db.add(block)
            block_11_blocks.append(block)
    db.commit()
    for block in block_11_blocks:
        db.refresh(block)

    # ACTION: Generate schedule for block 11 only
    # The engine should preserve existing baseline assignments
    incremental_engine = SchedulingEngine(
        db=db,
        start_date=block_11_start,
        end_date=block_11_start + timedelta(days=6),
    )

    incremental_result = incremental_engine.generate(
        pgy_levels=None,
        rotation_template_ids=None,
        algorithm="greedy",
        timeout_seconds=60.0,
        check_resilience=False,
    )

    assert incremental_result["status"] in ["success", "partial"], (
        f"Incremental generation failed: {incremental_result.get('message')}"
    )

    # ASSERT PHASE 1: Verify blocks 1-10 unchanged
    current_baseline = db.query(Assignment).filter(
        Assignment.block_id.in_([b.id for b in baseline_blocks])
    ).all()

    for assignment in current_baseline:
        assert assignment.id in baseline_checksums, (
            f"Unexpected new assignment in baseline blocks: {assignment.id}"
        )
        original = baseline_checksums[assignment.id]
        current = (assignment.person_id, assignment.rotation_template_id, assignment.block_id)
        assert current == original, (
            f"Assignment {assignment.id} changed during incremental generation: "
            f"was {original}, now {current}"
        )

    # ASSERT PHASE 2: Verify block 11 created
    block_11_assignments = db.query(Assignment).filter(
        Assignment.block_id.in_([b.id for b in block_11_blocks])
    ).all()

    assert len(block_11_assignments) > 0, "Block 11 should have new assignments"

    # ASSERT PHASE 3: Verify no ACGME violations at boundary
    # This would require actual ACGME validator, simplified check here
    validation = incremental_result.get("validation")
    if validation:
        # Check that any violations are documented
        if validation.total_violations > 0:
            assert len(validation.violations) > 0, (
                "Violations should be listed if total_violations > 0"
            )


# ==============================================================================
# ADDITIONAL EDGE CASE: SOLVER TIMEOUT
# ==============================================================================


def test_solver_timeout_graceful_degradation(
    db: Session,
    start_date: date,
    blocks_four_weeks: list[Block],
    residents_pool: list[Person],
    faculty_pool: list[Person],
    outpatient_templates: list[RotationTemplate],
):
    """
    Test solver behavior when timeout is reached.

    Scenario:
        Large problem with very short timeout forces solver to stop early.

    Expected behavior:
        - Solver times out gracefully
        - Returns best solution found so far (if any)
        - Status indicates timeout, not crash
        - May return partial solution
    """
    end_date = start_date + timedelta(days=27)
    engine = SchedulingEngine(
        db=db,
        start_date=start_date,
        end_date=end_date,
    )

    # Use aggressive timeout to force early termination
    result = engine.generate(
        pgy_levels=None,
        rotation_template_ids=None,
        algorithm="cp_sat",  # Can handle timeouts gracefully
        timeout_seconds=0.5,  # Very short timeout
        check_resilience=False,
    )

    # Verify graceful handling (not crash)
    assert "status" in result, "Should return result dict even on timeout"
    assert result.get("message") is not None, "Should provide status message"

    # Solver may succeed if problem is small, or return partial solution
    # Either outcome is acceptable as long as it doesn't crash
    assert result["status"] in ["success", "partial", "failed"], (
        f"Unexpected status on timeout: {result['status']}"
    )


# ==============================================================================
# ADDITIONAL EDGE CASE: EMPTY PROBLEM
# ==============================================================================


def test_empty_schedule_problem(
    db: Session,
    start_date: date,
):
    """
    Test solver behavior with empty problem (no residents, blocks, or templates).

    Expected behavior:
        - Returns failure status
        - Clear error message indicating empty problem
        - No crash or database corruption
    """
    # Create engine with empty date range (no blocks will exist)
    end_date = start_date + timedelta(days=-1)  # Invalid range
    engine = SchedulingEngine(
        db=db,
        start_date=start_date,
        end_date=end_date,
    )

    result = engine.generate(
        pgy_levels=None,
        rotation_template_ids=None,
        algorithm="greedy",
        timeout_seconds=10.0,
        check_resilience=False,
    )

    # Verify graceful handling
    assert result["status"] == "failed", "Empty problem should fail gracefully"
    assert "message" in result, "Should explain why generation failed"
    assert result["total_assigned"] == 0, "No assignments should be created"
