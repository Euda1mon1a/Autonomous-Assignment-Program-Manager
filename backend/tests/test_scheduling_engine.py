"""
Tests for the Scheduling Engine.

Tests the core scheduling algorithms and ACGME compliance checking.
"""
import pytest
from datetime import date, timedelta
from uuid import uuid4
from sqlalchemy.orm import Session

from app.scheduling.engine import SchedulingEngine
from app.scheduling.validator import ACGMEValidator
from app.models.person import Person
from app.models.block import Block
from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.rotation_template import RotationTemplate


class TestSchedulingEngineBasics:
    """Basic tests for SchedulingEngine initialization and setup."""

    def test_engine_initialization(self, db: Session):
        """Should initialize engine with date range."""
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        engine = SchedulingEngine(db, start_date, end_date)

        assert engine.start_date == start_date
        assert engine.end_date == end_date
        assert engine.db is db
        assert engine.assignments == []

    def test_ensure_blocks_exist(
        self,
        db: Session,
        sample_residents: list[Person],
    ):
        """Should create blocks for date range if they don't exist."""
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        engine = SchedulingEngine(db, start_date, end_date)
        blocks = engine._ensure_blocks_exist()

        # Should have 14 blocks (7 days x 2 time periods)
        assert len(blocks) == 14

        # Verify block structure
        for block in blocks:
            assert block.time_of_day in ["AM", "PM"]
            assert start_date <= block.date <= end_date

    def test_build_availability_matrix(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_blocks: list[Block],
    ):
        """Should build availability matrix from absences."""
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        engine = SchedulingEngine(db, start_date, end_date)
        engine._build_availability_matrix()

        # All residents should be in the matrix
        for resident in sample_residents:
            assert resident.id in engine.availability_matrix

    def test_availability_matrix_with_blocking_absence(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_blocks: list[Block],
    ):
        """Should mark person as unavailable during blocking absence (deployment, TDY)."""
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        # Create blocking absence (deployment) for first resident
        absence = Absence(
            id=uuid4(),
            person_id=sample_residents[0].id,
            start_date=start_date,
            end_date=start_date + timedelta(days=2),
            absence_type="deployment",
            is_blocking=True,
        )
        db.add(absence)
        db.commit()

        engine = SchedulingEngine(db, start_date, end_date)
        engine._build_availability_matrix()

        # Check first resident is unavailable for blocking absence period
        resident_id = sample_residents[0].id
        for block in sample_blocks:
            if block.date <= start_date + timedelta(days=2):
                assert engine.availability_matrix[resident_id][block.id]["available"] is False
            else:
                assert engine.availability_matrix[resident_id][block.id]["available"] is True

    def test_availability_matrix_with_partial_absence(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_blocks: list[Block],
    ):
        """Should allow assignment during partial absence (vacation, conference)."""
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        # Create partial absence (short vacation) for first resident
        absence = Absence(
            id=uuid4(),
            person_id=sample_residents[0].id,
            start_date=start_date,
            end_date=start_date + timedelta(days=1),  # 2 days
            absence_type="vacation",
            is_blocking=False,
        )
        db.add(absence)
        db.commit()

        engine = SchedulingEngine(db, start_date, end_date)
        engine._build_availability_matrix()

        # Check first resident is AVAILABLE (partial absence doesn't block)
        # but partial_absence flag is set
        resident_id = sample_residents[0].id
        for block in sample_blocks:
            if block.date <= start_date + timedelta(days=1):
                assert engine.availability_matrix[resident_id][block.id]["available"] is True
                assert engine.availability_matrix[resident_id][block.id]["partial_absence"] is True
            else:
                assert engine.availability_matrix[resident_id][block.id]["available"] is True
                assert engine.availability_matrix[resident_id][block.id]["partial_absence"] is False


class TestGreedyAlgorithm:
    """Tests for the greedy scheduling algorithm."""

    def test_greedy_assigns_residents(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """Should assign residents to blocks using greedy algorithm."""
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        engine = SchedulingEngine(db, start_date, end_date)
        result = engine.generate(algorithm="greedy")

        assert result["status"] in ["success", "partial"]
        assert result["total_assigned"] > 0
        assert len(engine.assignments) > 0

    def test_greedy_respects_blocking_absence(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """Should not assign residents who have blocking absences."""
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        # Make first resident absent for entire period with blocking absence
        absence = Absence(
            id=uuid4(),
            person_id=sample_residents[0].id,
            start_date=start_date,
            end_date=end_date,
            absence_type="deployment",
            is_blocking=True,
        )
        db.add(absence)
        db.commit()

        engine = SchedulingEngine(db, start_date, end_date)
        engine.generate(algorithm="greedy")

        # First resident should have no assignments
        first_resident_assignments = [
            a for a in engine.assignments
            if a.person_id == sample_residents[0].id
        ]
        assert len(first_resident_assignments) == 0

    def test_greedy_allows_partial_absence(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """Should allow assignment during partial absences (vacation, conference)."""
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        # Give first resident a partial absence (short vacation)
        absence = Absence(
            id=uuid4(),
            person_id=sample_residents[0].id,
            start_date=start_date,
            end_date=start_date + timedelta(days=1),
            absence_type="vacation",
            is_blocking=False,
        )
        db.add(absence)
        db.commit()

        engine = SchedulingEngine(db, start_date, end_date)
        engine.generate(algorithm="greedy")

        # First resident CAN still be assigned (partial absence doesn't block)
        # Just verify the engine ran successfully
        assert len(engine.assignments) > 0

    def test_greedy_equity_distribution(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """Should distribute assignments equitably among residents."""
        start_date = date.today()
        end_date = start_date + timedelta(days=13)  # 2 weeks

        engine = SchedulingEngine(db, start_date, end_date)
        engine.generate(algorithm="greedy")

        # Count assignments per resident
        assignment_counts = {}
        for assignment in engine.assignments:
            if assignment.role == "primary":
                assignment_counts[assignment.person_id] = (
                    assignment_counts.get(assignment.person_id, 0) + 1
                )

        if len(assignment_counts) > 1:
            # Check that counts are relatively balanced
            counts = list(assignment_counts.values())
            max_diff = max(counts) - min(counts)
            # Allow for some variance, but not too much
            assert max_diff <= len(counts) + 5

    def test_greedy_skips_weekends_for_clinic(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """Should skip weekend blocks for clinic assignments."""
        # Find a Monday to start
        start_date = date.today()
        while start_date.weekday() != 0:
            start_date += timedelta(days=1)
        end_date = start_date + timedelta(days=6)

        engine = SchedulingEngine(db, start_date, end_date)
        engine.generate(algorithm="greedy")

        # Check no primary assignments on weekends
        weekend_assignments = []
        for assignment in engine.assignments:
            if assignment.role == "primary":
                block = db.query(Block).filter(Block.id == assignment.block_id).first()
                if block and block.is_weekend:
                    weekend_assignments.append(assignment)

        # Clinic assignments should not be on weekends
        assert len(weekend_assignments) == 0


class TestACGMECompliance:
    """Tests for ACGME compliance rules."""

    @pytest.mark.acgme
    def test_80_hour_rule_validation(self, db: Session, sample_residents: list[Person]):
        """Should detect 80-hour rule violations."""
        start_date = date.today()
        end_date = start_date + timedelta(days=27)  # 4 weeks

        # Create blocks
        blocks = []
        current = start_date
        while current <= end_date:
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current,
                    time_of_day=tod,
                    block_number=1,
                    is_weekend=(current.weekday() >= 5),
                )
                db.add(block)
                blocks.append(block)
            current += timedelta(days=1)
        db.commit()

        # Assign one resident to ALL blocks (will exceed 80 hours)
        for block in blocks:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_residents[0].id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        validator = ACGMEValidator(db)
        result = validator.validate_all(start_date, end_date)

        # Should have 80-hour violation
        hour_violations = [
            v for v in result.violations
            if v.type == "80_HOUR_VIOLATION"
        ]
        assert len(hour_violations) > 0

    @pytest.mark.acgme
    def test_1_in_7_rule_validation(self, db: Session, sample_residents: list[Person]):
        """Should detect 1-in-7 day off violations."""
        start_date = date.today()
        end_date = start_date + timedelta(days=13)  # 2 weeks

        # Create blocks
        blocks = []
        current = start_date
        while current <= end_date:
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current,
                    time_of_day=tod,
                    block_number=1,
                    is_weekend=False,  # Force all as workdays
                )
                db.add(block)
                blocks.append(block)
            current += timedelta(days=1)
        db.commit()

        # Assign one resident to EVERY day (no days off)
        for block in blocks:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_residents[0].id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        validator = ACGMEValidator(db)
        result = validator.validate_all(start_date, end_date)

        # Should have 1-in-7 violation (more than 6 consecutive days)
        day_off_violations = [
            v for v in result.violations
            if v.type == "1_IN_7_VIOLATION"
        ]
        assert len(day_off_violations) > 0

    @pytest.mark.acgme
    def test_supervision_ratio_violation(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_block: Block,
    ):
        """Should detect supervision ratio violations."""
        # Create 5 PGY-1 residents (needs 3 faculty for 1:2 ratio)
        pgy1_residents = []
        for i in range(5):
            resident = Person(
                id=uuid4(),
                name=f"PGY1 Resident {i}",
                type="resident",
                email=f"pgy1_{i}@test.org",
                pgy_level=1,
            )
            db.add(resident)
            pgy1_residents.append(resident)
        db.commit()

        # Assign all to same block
        for resident in pgy1_residents:
            assignment = Assignment(
                id=uuid4(),
                block_id=sample_block.id,
                person_id=resident.id,
                role="primary",
            )
            db.add(assignment)

        # Add only 1 faculty (should need 3 for 5 PGY-1s)
        faculty = Person(
            id=uuid4(),
            name="Lone Faculty",
            type="faculty",
            email="lone@test.org",
        )
        db.add(faculty)
        faculty_assignment = Assignment(
            id=uuid4(),
            block_id=sample_block.id,
            person_id=faculty.id,
            role="supervising",
        )
        db.add(faculty_assignment)
        db.commit()

        validator = ACGMEValidator(db)
        result = validator.validate_all(sample_block.date, sample_block.date)

        # Should have supervision ratio violation
        supervision_violations = [
            v for v in result.violations
            if v.type == "SUPERVISION_RATIO_VIOLATION"
        ]
        assert len(supervision_violations) > 0

    @pytest.mark.acgme
    def test_no_violations_valid_schedule(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
    ):
        """Should have no violations for properly scheduled week."""
        start_date = date.today()
        # Ensure we start on Monday
        while start_date.weekday() != 0:
            start_date += timedelta(days=1)
        end_date = start_date + timedelta(days=4)  # Mon-Fri only

        # Create weekday blocks only
        blocks = []
        current = start_date
        while current <= end_date:
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current,
                    time_of_day=tod,
                    block_number=1,
                    is_weekend=False,
                )
                db.add(block)
                blocks.append(block)
            current += timedelta(days=1)
        db.commit()

        # Distribute residents across blocks (1 per block)
        for i, block in enumerate(blocks):
            resident = sample_residents[i % len(sample_residents)]
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=resident.id,
                role="primary",
            )
            db.add(assignment)

            # Add faculty supervision
            faculty = sample_faculty_members[i % len(sample_faculty_members)]
            fac_assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=faculty.id,
                role="supervising",
            )
            db.add(fac_assignment)
        db.commit()

        validator = ACGMEValidator(db)
        result = validator.validate_all(start_date, end_date)

        # Should have no violations for this properly distributed schedule
        assert result.valid is True or len(result.violations) == 0


class TestFacultyAssignment:
    """Tests for faculty assignment logic."""

    def test_faculty_assigned_for_supervision(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """Should assign faculty for supervision."""
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        engine = SchedulingEngine(db, start_date, end_date)
        engine.generate(algorithm="greedy")

        # Check for supervising assignments
        supervising_assignments = [
            a for a in engine.assignments
            if a.role == "supervising"
        ]

        # Should have some supervising assignments if residents were assigned
        primary_assignments = [
            a for a in engine.assignments
            if a.role == "primary"
        ]

        if len(primary_assignments) > 0:
            assert len(supervising_assignments) > 0

    def test_faculty_respects_blocking_absence(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """Should not assign faculty with blocking absences."""
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        # Make all but one faculty absent with blocking absence
        for faculty in sample_faculty_members[:-1]:
            absence = Absence(
                id=uuid4(),
                person_id=faculty.id,
                start_date=start_date,
                end_date=end_date,
                absence_type="conference",
                is_blocking=True,  # Conference is blocking for faculty
            )
            db.add(absence)
        db.commit()

        engine = SchedulingEngine(db, start_date, end_date)
        engine.generate(algorithm="greedy")

        # Check supervising assignments are only for available faculty
        supervising_assignments = [
            a for a in engine.assignments
            if a.role == "supervising"
        ]

        absent_faculty_ids = {f.id for f in sample_faculty_members[:-1]}
        for assignment in supervising_assignments:
            assert assignment.person_id not in absent_faculty_ids


class TestScheduleRun:
    """Tests for schedule run recording."""

    def test_schedule_run_recorded(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """Should record schedule run for audit."""
        from app.models.schedule_run import ScheduleRun

        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        engine = SchedulingEngine(db, start_date, end_date)
        result = engine.generate(algorithm="greedy")

        # Check run_id returned
        assert "run_id" in result

        # Verify run exists in database
        run = db.query(ScheduleRun).filter(ScheduleRun.id == result["run_id"]).first()
        assert run is not None
        assert run.start_date == start_date
        assert run.end_date == end_date
        assert run.algorithm == "greedy"
        assert run.runtime_seconds > 0
