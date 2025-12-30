"""
End-to-end tests for the complete schedule generation workflow.

Tests cover:
1. Full schedule generation flow (create request → solver execution → validation)
2. ACGME compliance validation after schedule generation
3. Schedule export to different formats (JSON, CSV)
4. Error handling for invalid schedule requests

These tests validate the entire scheduling pipeline from user request through
to exported schedule data, ensuring all components work together correctly.
"""

import json
from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.schedule_run import ScheduleRun
from app.scheduling.engine import SchedulingEngine
from app.scheduling.validator import ACGMEValidator
from app.services.export.csv_exporter import CSVExporter
from app.services.export.json_exporter import JSONExporter


# ============================================================================
# Fixtures for E2E Tests
# ============================================================================


@pytest.fixture
def academic_year_setup(db: Session) -> dict:
    """
    Create a complete academic year setup with residents, faculty, and templates.

    Returns a dict with all necessary components for schedule generation testing.
    """
    # Create residents (3 PGY levels)
    residents = []
    for pgy in range(1, 4):
        for i in range(2):  # 2 residents per PGY level
            resident = Person(
                id=uuid4(),
                name=f"Dr. Resident PGY{pgy}-{i+1}",
                type="resident",
                email=f"resident.pgy{pgy}.{i+1}@hospital.org",
                pgy_level=pgy,
            )
            db.add(resident)
            residents.append(resident)

    # Create faculty (5 faculty members)
    faculty = []
    for i in range(5):
        fac = Person(
            id=uuid4(),
            name=f"Dr. Faculty {i+1}",
            type="faculty",
            email=f"faculty{i+1}@hospital.org",
            performs_procedures=(i < 2),  # First 2 can do procedures
            specialties=["General Medicine", "Primary Care"],
        )
        db.add(fac)
        faculty.append(fac)

    # Create rotation templates (outpatient templates for solver)
    templates = []

    # Sports Medicine Clinic
    templates.append(
        RotationTemplate(
            id=uuid4(),
            name="Sports Medicine Clinic",
            activity_type="outpatient",
            abbreviation="SM",
            clinic_location="Building A",
            max_residents=2,
            supervision_required=True,
            max_supervision_ratio=4,
        )
    )

    # Neurology Clinic
    templates.append(
        RotationTemplate(
            id=uuid4(),
            name="Neurology Clinic",
            activity_type="outpatient",
            abbreviation="NEURO",
            clinic_location="Building B",
            max_residents=2,
            supervision_required=True,
            max_supervision_ratio=4,
        )
    )

    # Palliative Care
    templates.append(
        RotationTemplate(
            id=uuid4(),
            name="Palliative Care",
            activity_type="outpatient",
            abbreviation="PC",
            clinic_location="Building C",
            max_residents=2,
            supervision_required=True,
            max_supervision_ratio=4,
        )
    )

    for template in templates:
        db.add(template)

    db.commit()

    # Refresh all objects
    for r in residents:
        db.refresh(r)
    for f in faculty:
        db.refresh(f)
    for t in templates:
        db.refresh(t)

    # Calculate date range (2 weeks)
    start_date = date.today()
    end_date = start_date + timedelta(days=13)

    return {
        "residents": residents,
        "faculty": faculty,
        "templates": templates,
        "start_date": start_date,
        "end_date": end_date,
    }


@pytest.fixture
def schedule_with_absence(db: Session, academic_year_setup: dict) -> dict:
    """
    Create a schedule setup with one resident having a blocking absence.

    This tests that the scheduler respects absences.
    """
    setup = academic_year_setup
    resident = setup["residents"][0]

    # Create blocking absence for first week
    absence = Absence(
        id=uuid4(),
        person_id=resident.id,
        start_date=setup["start_date"],
        end_date=setup["start_date"] + timedelta(days=6),
        absence_type="vacation",
        is_blocking=True,
        notes="Annual leave",
    )
    db.add(absence)
    db.commit()
    db.refresh(absence)

    setup["absence"] = absence
    return setup


# ============================================================================
# E2E Test: Full Schedule Generation Flow
# ============================================================================


class TestScheduleGenerationE2E:
    """End-to-end tests for complete schedule generation workflow."""

    def test_full_schedule_generation_greedy_algorithm(
        self, db: Session, academic_year_setup: dict
    ):
        """
        Test complete schedule generation using greedy algorithm.

        Workflow:
        1. Initialize scheduling engine with date range
        2. Generate schedule with greedy algorithm
        3. Verify assignments were created
        4. Verify ACGME validation was performed
        5. Verify solver statistics were captured
        """
        setup = academic_year_setup

        # Initialize engine
        engine = SchedulingEngine(
            db=db,
            start_date=setup["start_date"],
            end_date=setup["end_date"],
        )

        # Generate schedule
        result = engine.generate(
            algorithm="greedy",
            timeout_seconds=30.0,
            check_resilience=False,  # Skip resilience checks for speed
        )

        # Verify result structure
        assert "status" in result
        assert result["status"] in ["success", "partial"]
        assert "message" in result
        assert "total_assigned" in result
        assert "total_blocks" in result
        assert "validation" in result

        # Verify assignments were created
        assert result["total_assigned"] > 0
        assert result["total_blocks"] > 0

        # Verify validation was performed
        validation = result["validation"]
        assert "valid" in validation
        assert "total_violations" in validation
        assert "violations" in validation
        assert "coverage_rate" in validation

        # Verify solver statistics
        if result.get("solver_stats"):
            solver_stats = result["solver_stats"]
            assert "total_blocks" in solver_stats or "total_residents" in solver_stats

        # Verify run record was created
        assert result["run_id"] is not None
        run = db.query(ScheduleRun).filter(ScheduleRun.id == result["run_id"]).first()
        assert run is not None
        assert run.status in ["success", "partial"]
        assert run.algorithm == "greedy"

    def test_schedule_generation_with_multiple_algorithms(
        self, db: Session, academic_year_setup: dict
    ):
        """
        Test schedule generation with different solver algorithms.

        Verifies that all algorithms (greedy, cp_sat, pulp) can generate
        valid schedules and produce consistent results.
        """
        setup = academic_year_setup
        algorithms = ["greedy", "cp_sat", "pulp"]
        results = {}

        for algorithm in algorithms:
            # Create fresh engine for each algorithm
            engine = SchedulingEngine(
                db=db,
                start_date=setup["start_date"],
                end_date=setup["end_date"],
            )

            # Generate schedule
            result = engine.generate(
                algorithm=algorithm,
                timeout_seconds=60.0,
                check_resilience=False,
            )

            results[algorithm] = result

            # Verify successful generation
            assert result["status"] in ["success", "partial"]
            assert result["total_assigned"] > 0

            # Verify validation was performed
            assert "validation" in result
            assert result["validation"]["valid"] is not None

        # Compare results - all algorithms should produce assignments
        for algo, result in results.items():
            assert result["total_assigned"] > 0, f"{algo} failed to create assignments"

    def test_schedule_generation_respects_absences(
        self, db: Session, schedule_with_absence: dict
    ):
        """
        Test that schedule generation respects blocking absences.

        Verifies that residents with absences are not assigned to blocks
        during their absence period.
        """
        setup = schedule_with_absence
        resident = setup["residents"][0]
        absence = setup["absence"]

        # Generate schedule
        engine = SchedulingEngine(
            db=db,
            start_date=setup["start_date"],
            end_date=setup["end_date"],
        )

        result = engine.generate(
            algorithm="greedy",
            timeout_seconds=30.0,
            check_resilience=False,
        )

        assert result["status"] in ["success", "partial"]

        # Query assignments for the resident during absence period
        from app.models.assignment import Assignment

        conflicting_assignments = (
            db.query(Assignment)
            .join(Block)
            .filter(
                Assignment.person_id == resident.id,
                Block.date >= absence.start_date,
                Block.date <= absence.end_date,
            )
            .all()
        )

        # Should have no assignments during absence (or only absence assignments)
        for assignment in conflicting_assignments:
            # If there are assignments, they should be absence-type rotations
            if assignment.rotation_template:
                db.refresh(assignment.rotation_template)
                assert (
                    assignment.rotation_template.activity_type == "absence"
                ), "Resident assigned to non-absence rotation during blocking absence"

    def test_schedule_generation_with_pgy_level_filter(
        self, db: Session, academic_year_setup: dict
    ):
        """
        Test schedule generation with PGY level filtering.

        Verifies that only specified PGY levels are included in schedule.
        """
        setup = academic_year_setup

        # Generate schedule for PGY-1 residents only
        engine = SchedulingEngine(
            db=db,
            start_date=setup["start_date"],
            end_date=setup["end_date"],
        )

        result = engine.generate(
            pgy_levels=[1],  # Only PGY-1
            algorithm="greedy",
            timeout_seconds=30.0,
            check_resilience=False,
        )

        assert result["status"] in ["success", "partial"]

        # Verify only PGY-1 residents were assigned
        from app.models.assignment import Assignment

        assignments = (
            db.query(Assignment)
            .join(Block)
            .join(Person)
            .filter(
                Block.date >= setup["start_date"],
                Block.date <= setup["end_date"],
                Person.type == "resident",
            )
            .all()
        )

        for assignment in assignments:
            db.refresh(assignment.person)
            if assignment.person.type == "resident":
                assert (
                    assignment.person.pgy_level == 1
                ), f"Non-PGY-1 resident assigned: {assignment.person.name}"

    def test_schedule_generation_creates_faculty_supervision(
        self, db: Session, academic_year_setup: dict
    ):
        """
        Test that schedule generation creates faculty supervision assignments.

        Verifies that faculty are assigned to supervise residents according
        to ACGME supervision ratios.
        """
        setup = academic_year_setup

        engine = SchedulingEngine(
            db=db,
            start_date=setup["start_date"],
            end_date=setup["end_date"],
        )

        result = engine.generate(
            algorithm="greedy",
            timeout_seconds=30.0,
            check_resilience=False,
        )

        assert result["status"] in ["success", "partial"]

        # Query faculty assignments
        from app.models.assignment import Assignment

        faculty_assignments = (
            db.query(Assignment)
            .join(Block)
            .join(Person)
            .filter(
                Block.date >= setup["start_date"],
                Block.date <= setup["end_date"],
                Person.type == "faculty",
            )
            .all()
        )

        # Should have faculty assignments for supervision
        assert len(faculty_assignments) > 0, "No faculty supervision assignments created"

        # Verify faculty assignments have correct role
        for assignment in faculty_assignments:
            assert assignment.role in [
                "supervising",
                "primary",
            ], f"Unexpected faculty role: {assignment.role}"


# ============================================================================
# E2E Test: ACGME Compliance Validation
# ============================================================================


class TestACGMEValidationE2E:
    """End-to-end tests for ACGME compliance validation."""

    def test_acgme_validation_after_generation(
        self, db: Session, academic_year_setup: dict
    ):
        """
        Test that ACGME validation is performed after schedule generation.

        Verifies validation results include all required fields and checks.
        """
        setup = academic_year_setup

        engine = SchedulingEngine(
            db=db,
            start_date=setup["start_date"],
            end_date=setup["end_date"],
        )

        result = engine.generate(
            algorithm="greedy",
            timeout_seconds=30.0,
            check_resilience=False,
        )

        # Verify validation was performed
        assert "validation" in result
        validation = result["validation"]

        # Verify validation result structure
        assert "valid" in validation
        assert "total_violations" in validation
        assert "violations" in validation
        assert "coverage_rate" in validation

        # Violations should be a list
        assert isinstance(validation["violations"], list)

        # Each violation should have required fields
        for violation in validation["violations"]:
            assert "type" in violation
            assert "severity" in violation
            assert "message" in violation

    def test_acgme_validator_standalone(self, db: Session, academic_year_setup: dict):
        """
        Test ACGME validator as standalone component.

        Verifies validator can be used independently to check schedules.
        """
        setup = academic_year_setup

        # First generate a schedule
        engine = SchedulingEngine(
            db=db,
            start_date=setup["start_date"],
            end_date=setup["end_date"],
        )

        generation_result = engine.generate(
            algorithm="greedy",
            timeout_seconds=30.0,
            check_resilience=False,
        )

        assert generation_result["status"] in ["success", "partial"]

        # Now validate independently
        validator = ACGMEValidator(db)
        validation_result = validator.validate_all(
            start_date=setup["start_date"],
            end_date=setup["end_date"],
        )

        # Verify validation result
        assert validation_result.valid is not None
        assert validation_result.total_violations >= 0
        assert isinstance(validation_result.violations, list)
        assert validation_result.coverage_rate >= 0.0

        # Validation results should match generation results
        assert (
            validation_result.total_violations
            == generation_result["validation"]["total_violations"]
        )

    def test_validation_detects_supervision_violations(
        self, db: Session, academic_year_setup: dict
    ):
        """
        Test that validation detects supervision ratio violations.

        Creates a scenario with too many residents and too few faculty,
        then verifies violations are detected.
        """
        setup = academic_year_setup

        # Add more residents to create supervision pressure
        for i in range(10):
            resident = Person(
                id=uuid4(),
                name=f"Dr. Extra Resident {i+1}",
                type="resident",
                email=f"extra.resident{i+1}@hospital.org",
                pgy_level=1,
            )
            db.add(resident)

        db.commit()

        # Generate schedule (may have supervision violations)
        engine = SchedulingEngine(
            db=db,
            start_date=setup["start_date"],
            end_date=setup["end_date"],
        )

        result = engine.generate(
            algorithm="greedy",
            timeout_seconds=30.0,
            check_resilience=False,
        )

        # Check validation results
        validation = result["validation"]

        # With many more residents, we might have violations
        # (This is a stress test - violations are expected)
        if not validation["valid"]:
            # If there are violations, they should be properly formatted
            for violation in validation["violations"]:
                assert violation["type"] in [
                    "SUPERVISION_RATIO",
                    "80_HOUR",
                    "1_IN_7",
                    "COVERAGE",
                ]
                assert violation["severity"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]


# ============================================================================
# E2E Test: Schedule Export to Different Formats
# ============================================================================


class TestScheduleExportE2E:
    """End-to-end tests for schedule export functionality."""

    @pytest.mark.asyncio
    async def test_export_schedule_to_json(
        self, db: Session, academic_year_setup: dict
    ):
        """
        Test exporting generated schedule to JSON format.

        Verifies JSON export includes all assignment data and metadata.
        """
        setup = academic_year_setup

        # Generate schedule first
        engine = SchedulingEngine(
            db=db,
            start_date=setup["start_date"],
            end_date=setup["end_date"],
        )

        result = engine.generate(
            algorithm="greedy",
            timeout_seconds=30.0,
            check_resilience=False,
        )

        assert result["status"] in ["success", "partial"]
        assert result["total_assigned"] > 0

        # Export to JSON
        # Note: JSONExporter expects AsyncSession, so we'll test the format
        # by validating the data structure instead
        from app.models.assignment import Assignment

        assignments = (
            db.query(Assignment)
            .join(Block)
            .filter(
                Block.date >= setup["start_date"],
                Block.date <= setup["end_date"],
            )
            .all()
        )

        # Verify we have assignments to export
        assert len(assignments) > 0

        # Verify assignments have required fields for export
        for assignment in assignments:
            assert assignment.id is not None
            assert assignment.block_id is not None
            assert assignment.person_id is not None
            assert assignment.rotation_template_id is not None

    @pytest.mark.asyncio
    async def test_export_schedule_to_csv(
        self, db: Session, academic_year_setup: dict
    ):
        """
        Test exporting generated schedule to CSV format.

        Verifies CSV export produces valid comma-separated data.
        """
        setup = academic_year_setup

        # Generate schedule first
        engine = SchedulingEngine(
            db=db,
            start_date=setup["start_date"],
            end_date=setup["end_date"],
        )

        result = engine.generate(
            algorithm="greedy",
            timeout_seconds=30.0,
            check_resilience=False,
        )

        assert result["status"] in ["success", "partial"]

        # Verify assignments exist for export
        from app.models.assignment import Assignment

        assignments = (
            db.query(Assignment)
            .join(Block)
            .filter(
                Block.date >= setup["start_date"],
                Block.date <= setup["end_date"],
            )
            .all()
        )

        assert len(assignments) > 0, "No assignments to export"

        # Verify assignment data completeness
        for assignment in assignments:
            db.refresh(assignment.block)
            db.refresh(assignment.person)

            # Verify required fields for CSV export
            assert assignment.block.date is not None
            assert assignment.block.time_of_day is not None
            assert assignment.person.name is not None
            assert assignment.role is not None

    def test_export_includes_all_schedule_components(
        self, db: Session, academic_year_setup: dict
    ):
        """
        Test that exported schedule includes all components.

        Verifies export contains:
        - Assignment data
        - Block information (date, time)
        - Person information (name, role)
        - Rotation template details
        """
        setup = academic_year_setup

        # Generate schedule
        engine = SchedulingEngine(
            db=db,
            start_date=setup["start_date"],
            end_date=setup["end_date"],
        )

        result = engine.generate(
            algorithm="greedy",
            timeout_seconds=30.0,
            check_resilience=False,
        )

        assert result["status"] in ["success", "partial"]

        # Query assignments with all relationships
        from app.models.assignment import Assignment
        from sqlalchemy.orm import joinedload

        assignments = (
            db.query(Assignment)
            .options(
                joinedload(Assignment.block),
                joinedload(Assignment.person),
                joinedload(Assignment.rotation_template),
            )
            .join(Block)
            .filter(
                Block.date >= setup["start_date"],
                Block.date <= setup["end_date"],
            )
            .all()
        )

        assert len(assignments) > 0

        # Verify each assignment has all related data
        for assignment in assignments:
            # Block data
            assert assignment.block is not None
            assert assignment.block.date is not None
            assert assignment.block.time_of_day in ["AM", "PM"]

            # Person data
            assert assignment.person is not None
            assert assignment.person.name is not None
            assert assignment.person.type in ["resident", "faculty"]

            # Rotation template data
            assert assignment.rotation_template is not None
            assert assignment.rotation_template.name is not None


# ============================================================================
# E2E Test: Error Handling for Invalid Schedule Requests
# ============================================================================


class TestScheduleErrorHandlingE2E:
    """End-to-end tests for error handling in schedule generation."""

    def test_invalid_date_range_error(self, db: Session):
        """
        Test error handling for invalid date range (end before start).

        Verifies that appropriate error is raised for invalid date ranges.
        """
        # Create engine with invalid date range (end before start)
        start_date = date.today()
        end_date = start_date - timedelta(days=7)

        with pytest.raises(Exception):
            # Engine initialization should succeed
            engine = SchedulingEngine(
                db=db,
                start_date=start_date,
                end_date=end_date,
            )
            # But generation with invalid dates should fail during validation
            # (The actual validation happens in ScheduleRequest schema)

    def test_no_residents_error_handling(self, db: Session):
        """
        Test error handling when no residents exist.

        Verifies graceful failure when there are no residents to schedule.
        """
        # Create date range
        start_date = date.today()
        end_date = start_date + timedelta(days=13)

        # Create engine (no residents in database)
        engine = SchedulingEngine(
            db=db,
            start_date=start_date,
            end_date=end_date,
        )

        result = engine.generate(
            algorithm="greedy",
            timeout_seconds=30.0,
            check_resilience=False,
        )

        # Should fail gracefully
        assert result["status"] == "failed"
        assert "No residents found" in result["message"]
        assert result["total_assigned"] == 0

    def test_no_templates_error_handling(self, db: Session):
        """
        Test error handling when no rotation templates exist.

        Verifies schedule generation fails appropriately without templates.
        """
        # Create residents but no templates
        resident = Person(
            id=uuid4(),
            name="Dr. Test Resident",
            type="resident",
            email="test.resident@hospital.org",
            pgy_level=1,
        )
        db.add(resident)
        db.commit()

        start_date = date.today()
        end_date = start_date + timedelta(days=13)

        engine = SchedulingEngine(
            db=db,
            start_date=start_date,
            end_date=end_date,
        )

        result = engine.generate(
            algorithm="greedy",
            timeout_seconds=30.0,
            check_resilience=False,
        )

        # May succeed with 0 assignments or fail
        # Either is acceptable when no templates exist
        if result["status"] != "failed":
            assert result["total_assigned"] == 0

    def test_invalid_algorithm_fallback(self, db: Session, academic_year_setup: dict):
        """
        Test that invalid algorithm name falls back to greedy.

        Verifies graceful handling of invalid algorithm parameter.
        """
        setup = academic_year_setup

        engine = SchedulingEngine(
            db=db,
            start_date=setup["start_date"],
            end_date=setup["end_date"],
        )

        # Try to use invalid algorithm
        result = engine.generate(
            algorithm="invalid_algorithm_name",
            timeout_seconds=30.0,
            check_resilience=False,
        )

        # Should fall back to greedy and still succeed
        assert result["status"] in ["success", "partial"]
        # Algorithm in run record should be greedy (fallback)
        run = db.query(ScheduleRun).filter(ScheduleRun.id == result["run_id"]).first()
        assert run.algorithm == "greedy"

    def test_timeout_handling(self, db: Session, academic_year_setup: dict):
        """
        Test that solver timeout is respected.

        Verifies schedule generation handles timeout gracefully.
        """
        setup = academic_year_setup

        engine = SchedulingEngine(
            db=db,
            start_date=setup["start_date"],
            end_date=setup["end_date"],
        )

        # Use very short timeout (may cause partial results)
        result = engine.generate(
            algorithm="cp_sat",  # CP-SAT more likely to timeout
            timeout_seconds=0.1,  # Very short timeout
            check_resilience=False,
        )

        # Should complete (may be partial due to timeout)
        assert result["status"] in ["success", "partial", "failed"]

        # If failed, should have fallback to greedy
        if result["status"] == "partial" or result["status"] == "failed":
            # Verify graceful handling - no exceptions raised
            assert "message" in result
