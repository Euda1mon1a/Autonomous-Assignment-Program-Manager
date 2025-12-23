"""Tests for SwapRequestService."""

from datetime import date, timedelta
from uuid import uuid4

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.swap import SwapRecord, SwapStatus
from app.services.swap_request_service import SwapRequestService


class TestIsWeekAssignedToFaculty:
    """Tests for _is_week_assigned_to_faculty method."""

    def test_returns_true_when_faculty_has_fmit_assignment_for_week(self, db):
        """Should return True when faculty has FMIT assignments in the week."""
        # Create FMIT rotation template
        fmit_template = RotationTemplate(
            id=uuid4(),
            name="FMIT",
            activity_type="inpatient",
            abbreviation="FMIT",
            supervision_required=True,
        )
        db.add(fmit_template)

        # Create faculty
        faculty = Person(
            id=uuid4(),
            name="Dr. Test Faculty",
            first_name="Test",
            last_name="Faculty",
            type="faculty",
            role="faculty",
        )
        db.add(faculty)

        # Create blocks for a week (Monday to Sunday)
        week_start = date(2024, 1, 1)  # Monday
        blocks = []
        for day_offset in range(7):
            current_date = week_start + timedelta(days=day_offset)
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current_date,
                    time_of_day=time_of_day,
                    block_number=1,
                )
                blocks.append(block)
                db.add(block)

        db.commit()

        # Create FMIT assignment for the week
        assignment = Assignment(
            id=uuid4(),
            block_id=blocks[0].id,
            person_id=faculty.id,
            rotation_template_id=fmit_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        # Test the method
        service = SwapRequestService(db)
        result = service._is_week_assigned_to_faculty(faculty.id, week_start)

        assert result is True

    def test_returns_false_when_faculty_has_no_fmit_assignment_for_week(self, db):
        """Should return False when faculty has no FMIT assignments in the week."""
        # Create FMIT rotation template
        fmit_template = RotationTemplate(
            id=uuid4(),
            name="FMIT",
            activity_type="inpatient",
            abbreviation="FMIT",
            supervision_required=True,
        )
        db.add(fmit_template)

        # Create faculty
        faculty = Person(
            id=uuid4(),
            name="Dr. Test Faculty",
            first_name="Test",
            last_name="Faculty",
            type="faculty",
            role="faculty",
        )
        db.add(faculty)
        db.commit()

        # Test with a week that has no assignments
        week_start = date(2024, 1, 1)
        service = SwapRequestService(db)
        result = service._is_week_assigned_to_faculty(faculty.id, week_start)

        assert result is False

    def test_returns_false_when_no_fmit_template_exists(self, db):
        """Should return False when no FMIT rotation template is configured."""
        # Create faculty
        faculty = Person(
            id=uuid4(),
            name="Dr. Test Faculty",
            first_name="Test",
            last_name="Faculty",
            type="faculty",
            role="faculty",
        )
        db.add(faculty)
        db.commit()

        # Test without FMIT template
        week_start = date(2024, 1, 1)
        service = SwapRequestService(db)
        result = service._is_week_assigned_to_faculty(faculty.id, week_start)

        assert result is False

    def test_returns_false_when_faculty_has_non_fmit_assignment_for_week(self, db):
        """Should return False when faculty has clinic but not FMIT assignments."""
        # Create FMIT rotation template
        fmit_template = RotationTemplate(
            id=uuid4(),
            name="FMIT",
            activity_type="inpatient",
            abbreviation="FMIT",
            supervision_required=True,
        )
        db.add(fmit_template)

        # Create clinic rotation template (not FMIT)
        clinic_template = RotationTemplate(
            id=uuid4(),
            name="PGY-1 Clinic",
            activity_type="clinic",
            abbreviation="C",
            supervision_required=True,
        )
        db.add(clinic_template)

        # Create faculty
        faculty = Person(
            id=uuid4(),
            name="Dr. Test Faculty",
            first_name="Test",
            last_name="Faculty",
            type="faculty",
            role="faculty",
        )
        db.add(faculty)

        # Create blocks for a week
        week_start = date(2024, 1, 1)
        blocks = []
        for day_offset in range(7):
            current_date = week_start + timedelta(days=day_offset)
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current_date,
                    time_of_day=time_of_day,
                    block_number=1,
                )
                blocks.append(block)
                db.add(block)

        db.commit()

        # Create clinic assignment (not FMIT) for the week
        assignment = Assignment(
            id=uuid4(),
            block_id=blocks[0].id,
            person_id=faculty.id,
            rotation_template_id=clinic_template.id,  # Clinic, not FMIT
            role="primary",
        )
        db.add(assignment)
        db.commit()

        # Test the method
        service = SwapRequestService(db)
        result = service._is_week_assigned_to_faculty(faculty.id, week_start)

        assert result is False

    def test_returns_true_with_multiple_fmit_blocks_in_week(self, db):
        """Should return True when faculty has multiple FMIT blocks in the week."""
        # Create FMIT rotation template
        fmit_template = RotationTemplate(
            id=uuid4(),
            name="FMIT",
            activity_type="inpatient",
            abbreviation="FMIT",
            supervision_required=True,
        )
        db.add(fmit_template)

        # Create faculty
        faculty = Person(
            id=uuid4(),
            name="Dr. Test Faculty",
            first_name="Test",
            last_name="Faculty",
            type="faculty",
            role="faculty",
        )
        db.add(faculty)

        # Create blocks for a week
        week_start = date(2024, 1, 1)
        blocks = []
        for day_offset in range(7):
            current_date = week_start + timedelta(days=day_offset)
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current_date,
                    time_of_day=time_of_day,
                    block_number=1,
                )
                blocks.append(block)
                db.add(block)

        db.commit()

        # Create multiple FMIT assignments for the week
        for i in range(5):
            assignment = Assignment(
                id=uuid4(),
                block_id=blocks[i].id,
                person_id=faculty.id,
                rotation_template_id=fmit_template.id,
                role="primary",
            )
            db.add(assignment)

        db.commit()

        # Test the method
        service = SwapRequestService(db)
        result = service._is_week_assigned_to_faculty(faculty.id, week_start)

        assert result is True

    def test_returns_false_for_different_faculty(self, db):
        """Should return False when checking a different faculty's assignments."""
        # Create FMIT rotation template
        fmit_template = RotationTemplate(
            id=uuid4(),
            name="FMIT",
            activity_type="inpatient",
            abbreviation="FMIT",
            supervision_required=True,
        )
        db.add(fmit_template)

        # Create two faculty members
        faculty1 = Person(
            id=uuid4(),
            name="Dr. Faculty One",
            first_name="Faculty",
            last_name="One",
            type="faculty",
            role="faculty",
        )
        faculty2 = Person(
            id=uuid4(),
            name="Dr. Faculty Two",
            first_name="Faculty",
            last_name="Two",
            type="faculty",
            role="faculty",
        )
        db.add_all([faculty1, faculty2])

        # Create blocks for a week
        week_start = date(2024, 1, 1)
        blocks = []
        for day_offset in range(7):
            current_date = week_start + timedelta(days=day_offset)
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current_date,
                    time_of_day=time_of_day,
                    block_number=1,
                )
                blocks.append(block)
                db.add(block)

        db.commit()

        # Create FMIT assignment for faculty1
        assignment = Assignment(
            id=uuid4(),
            block_id=blocks[0].id,
            person_id=faculty1.id,
            rotation_template_id=fmit_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        # Test with faculty2 (who has no assignments)
        service = SwapRequestService(db)
        result = service._is_week_assigned_to_faculty(faculty2.id, week_start)

        assert result is False

    def test_week_boundary_checking(self, db):
        """Should correctly check week boundaries."""
        # Create FMIT rotation template
        fmit_template = RotationTemplate(
            id=uuid4(),
            name="FMIT",
            activity_type="inpatient",
            abbreviation="FMIT",
            supervision_required=True,
        )
        db.add(fmit_template)

        # Create faculty
        faculty = Person(
            id=uuid4(),
            name="Dr. Test Faculty",
            first_name="Test",
            last_name="Faculty",
            type="faculty",
            role="faculty",
        )
        db.add(faculty)

        # Create blocks for week 1 (Jan 1-7)
        week1_start = date(2024, 1, 1)
        week1_blocks = []
        for day_offset in range(7):
            current_date = week1_start + timedelta(days=day_offset)
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current_date,
                    time_of_day=time_of_day,
                    block_number=1,
                )
                week1_blocks.append(block)
                db.add(block)

        # Create blocks for week 2 (Jan 8-14)
        week2_start = date(2024, 1, 8)
        week2_blocks = []
        for day_offset in range(7):
            current_date = week2_start + timedelta(days=day_offset)
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current_date,
                    time_of_day=time_of_day,
                    block_number=1,
                )
                week2_blocks.append(block)
                db.add(block)

        db.commit()

        # Create FMIT assignment for week 1 only
        assignment = Assignment(
            id=uuid4(),
            block_id=week1_blocks[0].id,
            person_id=faculty.id,
            rotation_template_id=fmit_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        # Test the method
        service = SwapRequestService(db)

        # Should return True for week 1
        result_week1 = service._is_week_assigned_to_faculty(faculty.id, week1_start)
        assert result_week1 is True

        # Should return False for week 2
        result_week2 = service._is_week_assigned_to_faculty(faculty.id, week2_start)
        assert result_week2 is False


class TestCreateRequest:
    """Tests for create_request method with FMIT verification."""

    def test_create_request_fails_when_week_not_assigned(self, db):
        """Should fail when trying to create swap request for unassigned week."""
        # Create FMIT rotation template (but no assignments)
        fmit_template = RotationTemplate(
            id=uuid4(),
            name="FMIT",
            activity_type="inpatient",
            abbreviation="FMIT",
            supervision_required=True,
        )
        db.add(fmit_template)

        # Create faculty
        faculty = Person(
            id=uuid4(),
            name="Dr. Test Faculty",
            first_name="Test",
            last_name="Faculty",
            type="faculty",
            role="faculty",
        )
        db.add(faculty)
        db.commit()

        # Try to create swap request for unassigned week
        service = SwapRequestService(db)
        week_start = date(2024, 1, 1)
        result = service.create_request(
            requester_id=faculty.id,
            source_week=week_start,
            reason="Need to swap",
        )

        assert result.success is False
        assert "not assigned to you" in result.message.lower()
        assert any(e.code == "WEEK_NOT_ASSIGNED" for e in result.errors)

    def test_create_request_succeeds_when_week_is_assigned(self, db):
        """Should succeed when creating swap request for assigned FMIT week."""
        # Create FMIT rotation template
        fmit_template = RotationTemplate(
            id=uuid4(),
            name="FMIT",
            activity_type="inpatient",
            abbreviation="FMIT",
            supervision_required=True,
        )
        db.add(fmit_template)

        # Create faculty
        faculty = Person(
            id=uuid4(),
            name="Dr. Test Faculty",
            first_name="Test",
            last_name="Faculty",
            type="faculty",
            role="faculty",
        )
        db.add(faculty)

        # Create blocks and assignments for the week
        week_start = date(2024, 1, 1)
        blocks = []
        for day_offset in range(7):
            current_date = week_start + timedelta(days=day_offset)
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current_date,
                    time_of_day=time_of_day,
                    block_number=1,
                )
                blocks.append(block)
                db.add(block)

        db.commit()

        # Create FMIT assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=blocks[0].id,
            person_id=faculty.id,
            rotation_template_id=fmit_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        # Create swap request
        service = SwapRequestService(db)
        result = service.create_request(
            requester_id=faculty.id,
            source_week=week_start,
            reason="Need to swap",
            auto_find_candidates=False,
        )

        assert result.success is True
        assert result.request_id is not None

        # Verify swap record was created
        swap_record = (
            db.query(SwapRecord).filter(SwapRecord.id == result.request_id).first()
        )
        assert swap_record is not None
        assert swap_record.source_faculty_id == faculty.id
        assert swap_record.source_week == week_start
        assert swap_record.status == SwapStatus.PENDING
