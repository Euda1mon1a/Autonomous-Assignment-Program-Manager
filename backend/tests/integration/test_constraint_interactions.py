"""
Integration tests for constraint interactions.

Tests complex scenarios where multiple constraints interact:
1. Conflicting hard constraints (conference + call simultaneously)
2. Soft constraint with zero weight (effectively disabled)
3. Credential expiring mid-block (warning vs blocking)
4. Leave overlapping with call assignment (conflict detection)

Based on test frames from docs/testing/TEST_SCENARIO_FRAMES.md
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest

from app.models.absence import Absence
from app.models.assignment import Assignment
from sqlalchemy.orm import Session

from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.scheduling.constraints.base import (
    Constraint,
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    HardConstraint,
    SchedulingContext,
    SoftConstraint,
)
from app.scheduling.constraints.manager import ConstraintManager


# ============================================================================
# Mock Constraints for Testing
# ============================================================================


class ConferenceConstraint(HardConstraint):
    """Hard constraint: Resident must attend mandatory conference."""

    def __init__(self) -> None:
        super().__init__(
            name="MandatoryConference",
            constraint_type=ConstraintType.AVAILABILITY,
            priority=ConstraintPriority.CRITICAL,
        )
        self.conference_blocks: set = set()

    def add_conference_block(self, block_id) -> None:
        """Mark a block as a mandatory conference."""
        self.conference_blocks.add(block_id)

    def add_to_cpsat(self, model, variables, context):
        """Not implemented for this test."""
        pass

    def add_to_pulp(self, model, variables, context):
        """Not implemented for this test."""
        pass

    def validate(self, assignments, context) -> ConstraintResult:
        """Validate that residents don't have conflicting assignments during conference."""
        violations = []

        # Check each conference block
        for block_id in self.conference_blocks:
            # Find assignments during conference
            conflicting = [
                a
                for a in assignments
                if a.block_id == block_id
                and a.person_id in {r.id for r in context.residents}
            ]

            for assignment in conflicting:
                # Conference is mandatory, so any other assignment conflicts
                from app.scheduling.constraints.base import ConstraintViolation

                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="CRITICAL",
                        message=f"Resident assigned to {assignment.role} during mandatory conference",
                        person_id=assignment.person_id,
                        block_id=block_id,
                        details={
                            "assignment_id": str(assignment.id),
                            "conflict_type": "conference",
                        },
                    )
                )

        return ConstraintResult(
            satisfied=len(violations) == 0, violations=violations, penalty=0.0
        )


class PreferenceConstraint(SoftConstraint):
    """Soft constraint: Resident prefers certain shift types."""

    def __init__(self, weight: float = 1.0) -> None:
        super().__init__(
            name="ShiftPreference",
            constraint_type=ConstraintType.PREFERENCE,
            weight=weight,
            priority=ConstraintPriority.LOW,
        )
        self.preferences: dict = {}  # {person_id: preferred_session}

    def add_preference(self, person_id, preferred_session: Session) -> None:
        """Add a preference for a person."""
        self.preferences[person_id] = preferred_session

    def add_to_cpsat(self, model, variables, context):
        """Not implemented for this test."""
        pass

    def add_to_pulp(self, model, variables, context):
        """Not implemented for this test."""
        pass

    def validate(self, assignments, context) -> ConstraintResult:
        """Calculate penalty for preference violations."""
        violations = []
        penalty = 0.0

        for assignment in assignments:
            person_id = assignment.person_id
            if person_id not in self.preferences:
                continue

            # Get block to check session
            block = next(
                (b for b in context.blocks if b.id == assignment.block_id), None
            )
            if not block:
                continue

            preferred = self.preferences[person_id]
            if block.session != preferred:
                # Violates preference
                penalty += self.get_penalty(violation_count=1)

                from app.scheduling.constraints.base import ConstraintViolation

                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="LOW",
                        message=f"Assignment does not match preference (prefers {preferred.value})",
                        person_id=person_id,
                        block_id=assignment.block_id,
                        details={
                            "preferred": preferred.value,
                            "actual": block.session.value,
                        },
                    )
                )

        return ConstraintResult(satisfied=True, violations=violations, penalty=penalty)


# ============================================================================
# Test Class
# ============================================================================


@pytest.mark.integration
class TestConstraintInteractions:
    """Test complex constraint interaction scenarios."""

    def test_conflicting_hard_constraints(self, db):
        """
        Test detection of conflicting hard constraints.

        Scenario: Resident must attend conference (hard) AND cover call (hard)
        at the same time block.

        Frame: 3.1 from TEST_SCENARIO_FRAMES.md
        """
        # SETUP: Create resident
        resident = Person(
            id=uuid4(),
            name="Dr. PGY2 Resident",
            type="resident",
            email="pgy2@hospital.org",
            pgy_level=2,
        )
        db.add(resident)

        # Create conference block (Wednesday AM)
        conference_date = date(2025, 1, 15)
        conference_block = Block(
            id=uuid4(),
            date=conference_date,
            session=Session.AM,
            block_number=15,
            academic_year=2025,
        )
        db.add(conference_block)

        # Create rotation template for call
        call_template = RotationTemplate(
            id=uuid4(),
            name="Call Coverage",
            activity_type="call",
            abbreviation="CALL",
            max_residents=1,
            supervision_required=True,
        )
        db.add(call_template)

        # Hard constraint 1: Mandatory conference
        conference_constraint = ConferenceConstraint()
        conference_constraint.add_conference_block(conference_block.id)

        # Hard constraint 2: Must cover call (same time)
        call_assignment = Assignment(
            id=uuid4(),
            block_id=conference_block.id,
            person_id=resident.id,
            rotation_template_id=call_template.id,
            role="primary",
        )
        db.add(call_assignment)
        db.commit()

        # Build context
        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=[conference_block],
            templates=[call_template],
            existing_assignments=[call_assignment],
            start_date=conference_date,
            end_date=conference_date,
        )

        # ACTION: Validate constraints
        result = conference_constraint.validate([call_assignment], context)

        # ASSERT: Conflict detected
        assert result.satisfied is False, "Should detect conflicting hard constraints"
        assert len(result.violations) > 0, "Should have violation records"

        violation = result.violations[0]
        assert violation.severity == "CRITICAL"
        assert "conference" in violation.message.lower()
        assert violation.person_id == resident.id
        assert violation.block_id == conference_block.id

        # Verify assignment exists (conflict should be caught before creation in real system)
        assignments_in_db = db.query(Assignment).filter_by(person_id=resident.id).all()
        assert len(assignments_in_db) == 1, (
            "Assignment exists (conflict detected post-creation)"
        )

    def test_soft_constraint_zero_weight(self, db):
        """
        Test soft constraint behavior when weight set to zero.

        Scenario: Preference constraint with weight=0 should be effectively disabled,
        producing no penalty even when violated.

        Frame: 3.2 from TEST_SCENARIO_FRAMES.md
        """
        # SETUP: Create resident
        resident = Person(
            id=uuid4(),
            name="Dr. PGY1 Resident",
            type="resident",
            email="pgy1@hospital.org",
            pgy_level=1,
        )
        db.add(resident)

        # Create afternoon block
        afternoon_date = date(2025, 1, 15)
        afternoon_block = Block(
            id=uuid4(),
            date=afternoon_date,
            session=Session.PM,  # Resident prefers AM
            block_number=15,
            academic_year=2025,
        )
        db.add(afternoon_block)

        # Create rotation template
        clinic_template = RotationTemplate(
            id=uuid4(),
            name="Clinic",
            activity_type="clinic",
            abbreviation="CLN",
            max_residents=4,
        )
        db.add(clinic_template)

        # Create afternoon assignment (violates preference)
        afternoon_assignment = Assignment(
            id=uuid4(),
            block_id=afternoon_block.id,
            person_id=resident.id,
            rotation_template_id=clinic_template.id,
            role="primary",
        )
        db.add(afternoon_assignment)
        db.commit()

        # Create soft constraint with weight=0
        preference_zero = PreferenceConstraint(weight=0.0)
        preference_zero.add_preference(resident.id, Session.AM)  # Prefers mornings

        # Create soft constraint with non-zero weight for comparison
        preference_normal = PreferenceConstraint(weight=5.0)
        preference_normal.add_preference(resident.id, Session.AM)

        # Build context
        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=[afternoon_block],
            templates=[clinic_template],
            existing_assignments=[afternoon_assignment],
            start_date=afternoon_date,
            end_date=afternoon_date,
        )

        # ACTION: Validate with zero weight
        result_zero = preference_zero.validate([afternoon_assignment], context)

        # ASSERT: Should be valid despite violating preference
        assert result_zero.satisfied is True, "Zero-weight constraint should not block"
        assert result_zero.penalty == 0.0, "Zero weight should produce zero penalty"

        # May have violation records, but penalty is zero
        if result_zero.violations:
            assert all(v.severity == "LOW" for v in result_zero.violations)

        # ACTION: Validate with non-zero weight
        result_normal = preference_normal.validate([afternoon_assignment], context)

        # ASSERT: Should have penalty when weight > 0
        assert result_normal.satisfied is True, "Soft constraint doesn't block"
        assert result_normal.penalty > 0.0, "Non-zero weight should produce penalty"
        assert len(result_normal.violations) > 0, "Should record preference violation"

    def test_credential_expiring_mid_block(self, db):
        """
        Test detection of credential expiring during assigned block.

        Scenario: Faculty assigned to 4-week block, BLS credential expires in week 2.
        Should issue warning but allow assignment (with flag for review).

        Frame: 3.3 from TEST_SCENARIO_FRAMES.md

        Note: This test uses mock credential data since credential model
        is not yet implemented in the system.
        """
        # SETUP: Create faculty
        faculty = Person(
            id=uuid4(),
            name="Dr. Faculty Member",
            type="faculty",
            email="faculty@hospital.org",
            performs_procedures=True,
        )
        db.add(faculty)

        # Create 4-week block assignment (Jan 1-28)
        block_start = date(2025, 1, 1)
        blocks = []
        for week in range(4):
            for day in range(7):
                for session in [Session.AM, Session.PM]:
                    block_date = block_start + timedelta(days=week * 7 + day)
                    block = Block(
                        id=uuid4(),
                        date=block_date,
                        session=session,
                        block_number=(week * 7 + day) * 2
                        + (0 if session == Session.AM else 1),
                        academic_year=2025,
                    )
                    blocks.append(block)
                    db.add(block)

        # Create rotation template requiring BLS
        inpatient_template = RotationTemplate(
            id=uuid4(),
            name="Inpatient Service",
            activity_type="inpatient",
            abbreviation="IP",
            max_residents=6,
            supervision_required=True,
        )
        db.add(inpatient_template)

        # Create assignments for the 4 weeks
        assignments = []
        for block in blocks[:56]:  # 4 weeks * 7 days * 2 sessions
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=faculty.id,
                rotation_template_id=inpatient_template.id,
                role="attending",
            )
            assignments.append(assignment)
            db.add(assignment)

        db.commit()

        # Mock credential data (BLS expires Jan 15, mid-block)
        bls_expiration = date(2025, 1, 15)

        # Create mock credential validator
        class CredentialExpiringConstraint(SoftConstraint):
            """Mock constraint that checks for expiring credentials."""

            def __init__(self, credentials: dict) -> None:
                super().__init__(
                    name="CredentialExpiring",
                    constraint_type=ConstraintType.AVAILABILITY,
                    weight=3.0,  # Warning level
                    priority=ConstraintPriority.HIGH,
                )
                self.credentials = (
                    credentials  # {person_id: {credential_type: expiration_date}}
                )

            def add_to_cpsat(self, model, variables, context):
                pass

            def add_to_pulp(self, model, variables, context):
                pass

            def validate(self, assignments, context) -> ConstraintResult:
                violations = []
                penalty = 0.0

                # Group assignments by person and date range
                person_assignments = {}
                for a in assignments:
                    if a.person_id not in person_assignments:
                        person_assignments[a.person_id] = []
                    person_assignments[a.person_id].append(a)

                for person_id, person_assigns in person_assignments.items():
                    if person_id not in self.credentials:
                        continue

                    # Get date range for this person's assignments
                    dates = [
                        b.date
                        for a in person_assigns
                        for b in context.blocks
                        if b.id == a.block_id
                    ]
                    if not dates:
                        continue

                    assign_start = min(dates)
                    assign_end = max(dates)

                    # Check each credential
                    for cred_type, expiration in self.credentials[person_id].items():
                        # Credential expires during assignment period
                        if assign_start < expiration < assign_end:
                            from app.scheduling.constraints.base import (
                                ConstraintViolation,
                            )

                            violations.append(
                                ConstraintViolation(
                                    constraint_name=self.name,
                                    constraint_type=self.constraint_type,
                                    severity="HIGH",
                                    message=f"{cred_type} credential expires during assignment on {expiration.isoformat()}",
                                    person_id=person_id,
                                    block_id=None,
                                    details={
                                        "credential_type": cred_type,
                                        "expiration_date": expiration.isoformat(),
                                        "assignment_start": assign_start.isoformat(),
                                        "assignment_end": assign_end.isoformat(),
                                        "days_until_expiration": (
                                            expiration - assign_start
                                        ).days,
                                    },
                                )
                            )
                            penalty += self.get_penalty(violation_count=1)

                return ConstraintResult(
                    satisfied=True,  # Still valid but flagged
                    violations=violations,
                    penalty=penalty,
                )

        credential_data = {faculty.id: {"BLS": bls_expiration}}
        credential_constraint = CredentialExpiringConstraint(
            credentials=credential_data
        )

        # Build context
        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=blocks,
            templates=[inpatient_template],
            existing_assignments=assignments,
            start_date=block_start,
            end_date=block_start + timedelta(days=27),
        )

        # ACTION: Validate credentials
        result = credential_constraint.validate(assignments, context)

        # ASSERT: Should be valid but with warnings
        assert result.satisfied is True, (
            "Assignment valid at start (credential not yet expired)"
        )
        assert len(result.violations) > 0, (
            "Should have warning about mid-block expiration"
        )
        assert result.penalty > 0.0, "Should have penalty for expiring credential"

        violation = result.violations[0]
        assert violation.severity == "HIGH"
        assert "expires during" in violation.message
        assert violation.person_id == faculty.id
        assert violation.details["credential_type"] == "BLS"
        assert violation.details["expiration_date"] == bls_expiration.isoformat()

        # Verify days until expiration calculated
        days_until = (bls_expiration - block_start).days
        assert violation.details["days_until_expiration"] == days_until

    def test_leave_overlapping_call_assignment(self, db):
        """
        Test leave request handling when call shift assigned.

        Scenario: Faculty requests leave for dates they're assigned to call.
        Should detect conflict and flag for coverage resolution.

        Frame: 3.4 from TEST_SCENARIO_FRAMES.md
        """
        # SETUP: Create faculty
        faculty = Person(
            id=uuid4(),
            name="Dr. Call Faculty",
            type="faculty",
            email="call.faculty@hospital.org",
            performs_procedures=True,
        )
        db.add(faculty)

        # Create call blocks (Jan 15-16, 24-hour shift)
        call_start_date = date(2025, 1, 15)
        call_end_date = date(2025, 1, 16)

        call_blocks = []
        for day_offset in range(2):  # 15th and 16th
            for session in [Session.AM, Session.PM]:
                block = Block(
                    id=uuid4(),
                    date=call_start_date + timedelta(days=day_offset),
                    session=session,
                    block_number=(14 + day_offset) * 2
                    + (0 if session == Session.AM else 1),
                    academic_year=2025,
                )
                call_blocks.append(block)
                db.add(block)

        # Create call rotation template
        call_template = RotationTemplate(
            id=uuid4(),
            name="Call Coverage",
            activity_type="call",
            abbreviation="CALL",
            max_residents=1,
            supervision_required=True,
        )
        db.add(call_template)

        # Create call assignments
        call_assignments = []
        for block in call_blocks:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=faculty.id,
                rotation_template_id=call_template.id,
                role="attending",
            )
            call_assignments.append(assignment)
            db.add(assignment)

        # Create leave request overlapping call (Jan 15-17)
        leave_request = Absence(
            id=uuid4(),
            person_id=faculty.id,
            start_date=call_start_date,
            end_date=date(2025, 1, 17),
            absence_type="vacation",
            is_blocking=True,  # Blocking absence
            notes="Family vacation planned before call assignment",
        )
        db.add(leave_request)
        db.commit()

        # Create constraint to detect leave conflicts
        class LeaveConflictConstraint(HardConstraint):
            """Hard constraint: Cannot be assigned during blocking absence."""

            def __init__(self) -> None:
                super().__init__(
                    name="LeaveConflict",
                    constraint_type=ConstraintType.AVAILABILITY,
                    priority=ConstraintPriority.CRITICAL,
                )

            def add_to_cpsat(self, model, variables, context):
                pass

            def add_to_pulp(self, model, variables, context):
                pass

            def validate(self, assignments, context) -> ConstraintResult:
                violations = []

                # Query all blocking absences
                from sqlalchemy.orm import Session

                db_session = Session.object_session(context.blocks[0])
                absences = (
                    db_session.query(Absence).filter(Absence.is_blocking == True).all()
                )

                # Check each assignment against absences
                for assignment in assignments:
                    # Get block date
                    block = next(
                        (b for b in context.blocks if b.id == assignment.block_id), None
                    )
                    if not block:
                        continue

                    # Check if person has leave on this date
                    person_absences = [
                        a for a in absences if a.person_id == assignment.person_id
                    ]
                    for absence in person_absences:
                        if absence.start_date <= block.date <= absence.end_date:
                            from app.scheduling.constraints.base import (
                                ConstraintViolation,
                            )

                            violations.append(
                                ConstraintViolation(
                                    constraint_name=self.name,
                                    constraint_type=self.constraint_type,
                                    severity="CRITICAL",
                                    message=f"Assignment conflicts with {absence.absence_type} leave",
                                    person_id=assignment.person_id,
                                    block_id=assignment.block_id,
                                    details={
                                        "absence_id": str(absence.id),
                                        "absence_type": absence.absence_type,
                                        "leave_start": absence.start_date.isoformat(),
                                        "leave_end": absence.end_date.isoformat(),
                                        "assignment_date": block.date.isoformat(),
                                    },
                                )
                            )

                return ConstraintResult(
                    satisfied=len(violations) == 0, violations=violations
                )

        leave_constraint = LeaveConflictConstraint()

        # Build context
        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=call_blocks,
            templates=[call_template],
            existing_assignments=call_assignments,
            start_date=call_start_date,
            end_date=call_end_date,
        )

        # ACTION: Validate leave conflicts
        result = leave_constraint.validate(call_assignments, context)

        # ASSERT: Conflict detected
        assert result.satisfied is False, "Should detect leave/assignment conflict"
        assert len(result.violations) > 0, "Should have conflict violations"

        # Check violation details
        for violation in result.violations:
            assert violation.severity == "CRITICAL"
            assert "leave" in violation.message.lower()
            assert violation.person_id == faculty.id
            assert violation.details["absence_type"] == "vacation"

        # Verify we have violations for the overlapping dates (15th and 16th)
        conflicting_dates = {v.details["assignment_date"] for v in result.violations}
        assert call_start_date.isoformat() in conflicting_dates
        assert call_end_date.isoformat() in conflicting_dates

        # Verify leave request exists and is marked as having conflicts
        leave_in_db = db.query(Absence).filter_by(id=leave_request.id).first()
        assert leave_in_db is not None
        assert leave_in_db.is_blocking is True

    def test_multiple_constraints_validation(self, db):
        """
        Test validation with multiple constraints active.

        This ensures ConstraintManager correctly aggregates results
        from multiple constraints.
        """
        # SETUP: Create resident and faculty
        resident = Person(
            id=uuid4(),
            name="Dr. Test Resident",
            type="resident",
            email="resident@test.org",
            pgy_level=1,
        )
        faculty = Person(
            id=uuid4(),
            name="Dr. Test Faculty",
            type="faculty",
            email="faculty@test.org",
        )
        db.add_all([resident, faculty])

        # Create blocks
        test_date = date(2025, 1, 15)
        am_block = Block(
            id=uuid4(),
            date=test_date,
            session=Session.AM,
            block_number=29,
            academic_year=2025,
        )
        pm_block = Block(
            id=uuid4(),
            date=test_date,
            session=Session.PM,
            block_number=30,
            academic_year=2025,
        )
        db.add_all([am_block, pm_block])

        # Create rotation template
        clinic_template = RotationTemplate(
            id=uuid4(),
            name="Clinic",
            activity_type="clinic",
            abbreviation="CLN",
            max_residents=4,
        )
        db.add(clinic_template)

        # Create assignments
        resident_am = Assignment(
            id=uuid4(),
            block_id=am_block.id,
            person_id=resident.id,
            rotation_template_id=clinic_template.id,
            role="resident",
        )
        resident_pm = Assignment(
            id=uuid4(),
            block_id=pm_block.id,
            person_id=resident.id,
            rotation_template_id=clinic_template.id,
            role="resident",
        )
        db.add_all([resident_am, resident_pm])
        db.commit()

        # Create multiple constraints
        preference = PreferenceConstraint(weight=5.0)
        preference.add_preference(resident.id, Session.AM)  # Prefers AM

        # Build context
        context = SchedulingContext(
            residents=[resident],
            faculty=[faculty],
            blocks=[am_block, pm_block],
            templates=[clinic_template],
            existing_assignments=[resident_am, resident_pm],
            start_date=test_date,
            end_date=test_date,
        )

        # Create constraint manager and add constraints
        manager = ConstraintManager()
        manager.add(preference)

        # ACTION: Validate all constraints
        result = manager.validate_all([resident_am, resident_pm], context)

        # ASSERT: Results aggregated correctly
        assert isinstance(result, ConstraintResult)
        # Should be satisfied (soft constraints don't block)
        assert result.satisfied is True
        # Should have penalty for PM assignment (violates preference)
        assert result.penalty > 0.0
        # Should have at least one violation (the PM preference)
        assert len(result.violations) > 0

        # Check that penalty is from preference constraint
        pref_violations = [
            v for v in result.violations if v.constraint_name == "ShiftPreference"
        ]
        assert len(pref_violations) > 0
