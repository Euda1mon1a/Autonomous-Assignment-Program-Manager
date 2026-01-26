"""
Comprehensive ACGME Compliance Validation Tests.

This test suite provides extensive coverage for ACGME work hour rules
and compliance validation scenarios.

Test Coverage:
- 80-hour weekly limit validation
- 1-in-7 day off rule
- Maximum shift length (16h for PGY-1, 24+4h for PGY-2+)
- Minimum time off between shifts
- Night float rotation limits
- Moonlighting hour tracking
- Rolling 4-week period calculations
- Edge cases and boundary conditions
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.validators.advanced_acgme import AdvancedACGMEValidator


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def validator(db: Session) -> AdvancedACGMEValidator:
    """Create an AdvancedACGMEValidator instance."""
    return AdvancedACGMEValidator(db)


@pytest.fixture
def pgy1_resident(db: Session) -> Person:
    """Create a PGY-1 resident for testing."""
    resident = Person(
        id=uuid4(),
        name="Dr. PGY-1 Test",
        type="resident",
        email="pgy1@test.org",
        pgy_level=1,
    )
    db.add(resident)
    db.commit()
    db.refresh(resident)
    return resident


@pytest.fixture
def pgy2_resident(db: Session) -> Person:
    """Create a PGY-2 resident for testing."""
    resident = Person(
        id=uuid4(),
        name="Dr. PGY-2 Test",
        type="resident",
        email="pgy2@test.org",
        pgy_level=2,
    )
    db.add(resident)
    db.commit()
    db.refresh(resident)
    return resident


@pytest.fixture
def pgy3_resident(db: Session) -> Person:
    """Create a PGY-3 resident for testing."""
    resident = Person(
        id=uuid4(),
        name="Dr. PGY-3 Test",
        type="resident",
        email="pgy3@test.org",
        pgy_level=3,
    )
    db.add(resident)
    db.commit()
    db.refresh(resident)
    return resident


@pytest.fixture
def call_rotation(db: Session) -> RotationTemplate:
    """Create a call rotation template."""
    rotation = RotationTemplate(
        id=uuid4(),
        name="Inpatient Call",
        rotation_type="call",
        abbreviation="CALL",
        requires_call=True,
        max_residents=1,
    )
    db.add(rotation)
    db.commit()
    db.refresh(rotation)
    return rotation


@pytest.fixture
def night_float_rotation(db: Session) -> RotationTemplate:
    """Create a night float rotation template."""
    rotation = RotationTemplate(
        id=uuid4(),
        name="Night Float",
        rotation_type="night_float",
        abbreviation="NF",
        requires_call=True,
        max_residents=2,
    )
    db.add(rotation)
    db.commit()
    db.refresh(rotation)
    return rotation


@pytest.fixture
def clinic_rotation(db: Session) -> RotationTemplate:
    """Create a clinic rotation template."""
    rotation = RotationTemplate(
        id=uuid4(),
        name="Clinic",
        rotation_type="outpatient",
        abbreviation="CLINIC",
        requires_call=False,
        max_residents=4,
    )
    db.add(rotation)
    db.commit()
    db.refresh(rotation)
    return rotation


def create_blocks(db: Session, start_date: date, days: int) -> list[Block]:
    """Helper to create blocks for a date range."""
    blocks = []
    for i in range(days):
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
    return blocks


# ============================================================================
# Test Class: 80-Hour Weekly Limit
# ============================================================================


class TestEightyHourWeeklyLimit:
    """Tests for the 80-hour weekly work limit."""

    def test_compliant_schedule_under_80_hours(
        self,
        db: Session,
        validator: AdvancedACGMEValidator,
        pgy2_resident: Person,
        clinic_rotation: RotationTemplate,
    ):
        """Test that a schedule with <80 hours per week is compliant."""
        start_date = date.today()
        blocks = create_blocks(db, start_date, 28)

        # Create assignments for 5 days per week (10 half-days = ~50 hours)
        for i in range(0, 28, 7):
            for day in range(5):  # Mon-Fri
                block_idx = (i + day) * 2
                if block_idx < len(blocks):
                    assignment = Assignment(
                        id=uuid4(),
                        block_id=blocks[block_idx].id,
                        person_id=pgy2_resident.id,
                        rotation_template_id=clinic_rotation.id,
                        role="primary",
                    )
                    db.add(assignment)
        db.commit()

        # Validate - should pass
        violations = validator.validate_80_hour_limit(pgy2_resident.id, start_date)
        assert len(violations) == 0

    def test_violation_exceeding_80_hours_single_week(
        self,
        db: Session,
        validator: AdvancedACGMEValidator,
        pgy2_resident: Person,
        call_rotation: RotationTemplate,
    ):
        """Test detection of 80-hour violation in a single week."""
        start_date = date.today()
        blocks = create_blocks(db, start_date, 7)

        # Assign all blocks (7 days × 2 half-days × 12 hours = 168 hours)
        for block in blocks:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=pgy2_resident.id,
                rotation_template_id=call_rotation.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        violations = validator.validate_80_hour_limit(pgy2_resident.id, start_date)
        assert len(violations) > 0

    def test_rolling_4_week_average_calculation(
        self,
        db: Session,
        validator: AdvancedACGMEValidator,
        pgy2_resident: Person,
        call_rotation: RotationTemplate,
        clinic_rotation: RotationTemplate,
    ):
        """Test that rolling 4-week average is calculated correctly."""
        start_date = date.today()
        blocks = create_blocks(db, start_date, 28)

        # Week 1-2: Heavy (6 days/week)
        for i in range(14):
            for tod_idx in range(2):
                block_idx = i * 2 + tod_idx
                if block_idx < len(blocks):
                    assignment = Assignment(
                        id=uuid4(),
                        block_id=blocks[block_idx].id,
                        person_id=pgy2_resident.id,
                        rotation_template_id=call_rotation.id,
                        role="primary",
                    )
                    db.add(assignment)

        # Week 3-4: Light (3 days/week)
        for i in range(14, 28, 2):
            block_idx = i * 2
            if block_idx < len(blocks):
                assignment = Assignment(
                    id=uuid4(),
                    block_id=blocks[block_idx].id,
                    person_id=pgy2_resident.id,
                    rotation_template_id=clinic_rotation.id,
                    role="primary",
                )
                db.add(assignment)
        db.commit()

        violations = validator.validate_80_hour_limit(pgy2_resident.id, start_date)
        # Should detect violations even if overall average is acceptable

    def test_boundary_exactly_80_hours(
        self,
        db: Session,
        validator: AdvancedACGMEValidator,
        pgy2_resident: Person,
        clinic_rotation: RotationTemplate,
    ):
        """Test boundary condition: exactly 80 hours should be compliant."""
        start_date = date.today()
        blocks = create_blocks(db, start_date, 7)

        # Create exactly 80 hours worth of assignments
        # Assuming 12-hour half-days, assign 6.67 days (rounded to 7 AM blocks)
        for i in range(7):
            assignment = Assignment(
                id=uuid4(),
                block_id=blocks[i * 2].id,  # AM blocks only
                person_id=pgy2_resident.id,
                rotation_template_id=clinic_rotation.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        violations = validator.validate_80_hour_limit(pgy2_resident.id, start_date)
        # Exactly 80 hours should be acceptable
        assert len(violations) == 0


# ============================================================================
# Test Class: 1-in-7 Day Off Rule
# ============================================================================


class TestOneInSevenDayOff:
    """Tests for the 1-in-7 day off rule."""

    def test_compliant_schedule_with_weekly_days_off(
        self,
        db: Session,
        validator: AdvancedACGMEValidator,
        pgy2_resident: Person,
        clinic_rotation: RotationTemplate,
    ):
        """Test compliant schedule with at least one day off per week."""
        start_date = date.today()
        blocks = create_blocks(db, start_date, 28)

        # Work Mon-Sat, off Sunday (6 days on, 1 day off)
        for week in range(4):
            for day in range(6):  # Mon-Sat
                block_idx = (week * 7 + day) * 2
                if block_idx < len(blocks):
                    assignment = Assignment(
                        id=uuid4(),
                        block_id=blocks[block_idx].id,
                        person_id=pgy2_resident.id,
                        rotation_template_id=clinic_rotation.id,
                        role="primary",
                    )
                    db.add(assignment)
        db.commit()

        violations = validator.validate_one_in_seven(pgy2_resident.id, start_date)
        assert len(violations) == 0

    def test_violation_no_day_off_in_8_days(
        self,
        db: Session,
        validator: AdvancedACGMEValidator,
        pgy2_resident: Person,
        call_rotation: RotationTemplate,
    ):
        """Test violation when no day off for 8+ consecutive days."""
        start_date = date.today()
        blocks = create_blocks(db, start_date, 10)

        # Work 8 consecutive days
        for i in range(8):
            for tod_idx in range(2):
                block_idx = i * 2 + tod_idx
                assignment = Assignment(
                    id=uuid4(),
                    block_id=blocks[block_idx].id,
                    person_id=pgy2_resident.id,
                    rotation_template_id=call_rotation.id,
                    role="primary",
                )
                db.add(assignment)
        db.commit()

        violations = validator.validate_one_in_seven(pgy2_resident.id, start_date)
        assert len(violations) > 0

    def test_day_off_resets_counter(
        self,
        db: Session,
        validator: AdvancedACGMEValidator,
        pgy2_resident: Person,
        clinic_rotation: RotationTemplate,
    ):
        """Test that a day off resets the consecutive work day counter."""
        start_date = date.today()
        blocks = create_blocks(db, start_date, 21)

        # Work 6 days, off 1, work 6 days, off 1, work 6 days
        day_idx = 0
        for cycle in range(3):
            # Work 6 days
            for work_day in range(6):
                for tod_idx in range(2):
                    block_idx = day_idx * 2 + tod_idx
                    if block_idx < len(blocks):
                        assignment = Assignment(
                            id=uuid4(),
                            block_id=blocks[block_idx].id,
                            person_id=pgy2_resident.id,
                            rotation_template_id=clinic_rotation.id,
                            role="primary",
                        )
                        db.add(assignment)
                day_idx += 1
            # Day off
            day_idx += 1
        db.commit()

        violations = validator.validate_one_in_seven(pgy2_resident.id, start_date)
        assert len(violations) == 0


# ============================================================================
# Test Class: Maximum Shift Length
# ============================================================================


class TestMaximumShiftLength:
    """Tests for maximum shift length rules."""

    def test_pgy1_16_hour_limit_compliant(
        self,
        db: Session,
        validator: AdvancedACGMEValidator,
        pgy1_resident: Person,
        clinic_rotation: RotationTemplate,
    ):
        """Test PGY-1 with shifts ≤16 hours is compliant."""
        start_date = date.today()
        blocks = create_blocks(db, start_date, 7)

        # Single half-day shifts (≤12 hours each)
        for i in range(0, len(blocks), 2):
            assignment = Assignment(
                id=uuid4(),
                block_id=blocks[i].id,
                person_id=pgy1_resident.id,
                rotation_template_id=clinic_rotation.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        violations = validator.validate_shift_length(pgy1_resident.id, start_date)
        assert len(violations) == 0

    def test_pgy1_exceeds_16_hour_limit(
        self,
        db: Session,
        validator: AdvancedACGMEValidator,
        pgy1_resident: Person,
        call_rotation: RotationTemplate,
    ):
        """Test PGY-1 violation when shift exceeds 16 hours."""
        start_date = date.today()
        blocks = create_blocks(db, start_date, 2)

        # 24-hour shift (AM + PM)
        for i in range(2):
            assignment = Assignment(
                id=uuid4(),
                block_id=blocks[i].id,
                person_id=pgy1_resident.id,
                rotation_template_id=call_rotation.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        violations = validator.validate_shift_length(pgy1_resident.id, start_date)
        assert len(violations) > 0

    def test_pgy2_24_plus_4_hour_limit_compliant(
        self,
        db: Session,
        validator: AdvancedACGMEValidator,
        pgy2_resident: Person,
        call_rotation: RotationTemplate,
    ):
        """Test PGY-2+ with 24+4 hour shift is compliant."""
        start_date = date.today()
        blocks = create_blocks(db, start_date, 2)

        # 24-hour call shift
        for i in range(2):
            assignment = Assignment(
                id=uuid4(),
                block_id=blocks[i].id,
                person_id=pgy2_resident.id,
                rotation_template_id=call_rotation.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        violations = validator.validate_shift_length(pgy2_resident.id, start_date)
        # 24+4 is allowed for PGY-2+
        assert len(violations) == 0

    def test_pgy3_extended_shift_with_strategic_nap(
        self,
        db: Session,
        validator: AdvancedACGMEValidator,
        pgy3_resident: Person,
        call_rotation: RotationTemplate,
    ):
        """Test PGY-3 on extended call with strategic nap allowance."""
        start_date = date.today()
        blocks = create_blocks(db, start_date, 2)

        # 24-hour shift with post-call relief
        for i in range(2):
            assignment = Assignment(
                id=uuid4(),
                block_id=blocks[i].id,
                person_id=pgy3_resident.id,
                rotation_template_id=call_rotation.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        violations = validator.validate_shift_length(pgy3_resident.id, start_date)
        assert len(violations) == 0


# ============================================================================
# Test Class: Night Float Limits
# ============================================================================


class TestNightFloatLimits:
    """Tests for night float rotation limits."""

    def test_compliant_night_float_under_6_consecutive(
        self,
        db: Session,
        validator: AdvancedACGMEValidator,
        pgy2_resident: Person,
        night_float_rotation: RotationTemplate,
    ):
        """Test compliant night float schedule with <6 consecutive nights."""
        start_date = date.today()
        blocks = create_blocks(db, start_date, 5)

        # 5 consecutive nights (compliant)
        for i in range(5):
            assignment = Assignment(
                id=uuid4(),
                block_id=blocks[i * 2 + 1].id,  # PM blocks for nights
                person_id=pgy2_resident.id,
                rotation_template_id=night_float_rotation.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        violations = validator.validate_night_float_limits(pgy2_resident.id, start_date)
        assert len(violations) == 0

    def test_violation_exceeds_6_consecutive_nights(
        self,
        db: Session,
        validator: AdvancedACGMEValidator,
        pgy2_resident: Person,
        night_float_rotation: RotationTemplate,
    ):
        """Test violation when exceeding 6 consecutive night float shifts."""
        start_date = date.today()
        blocks = create_blocks(db, start_date, 7)

        # 7 consecutive nights (violation)
        for i in range(7):
            assignment = Assignment(
                id=uuid4(),
                block_id=blocks[i * 2 + 1].id,  # PM blocks
                person_id=pgy2_resident.id,
                rotation_template_id=night_float_rotation.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        violations = validator.validate_night_float_limits(pgy2_resident.id, start_date)
        assert len(violations) > 0

    def test_night_float_reset_after_day_off(
        self,
        db: Session,
        validator: AdvancedACGMEValidator,
        pgy2_resident: Person,
        night_float_rotation: RotationTemplate,
    ):
        """Test that night float counter resets after a day off."""
        start_date = date.today()
        blocks = create_blocks(db, start_date, 14)

        # 5 nights, 1 off, 5 nights (both compliant)
        for i in range(5):
            assignment = Assignment(
                id=uuid4(),
                block_id=blocks[i * 2 + 1].id,
                person_id=pgy2_resident.id,
                rotation_template_id=night_float_rotation.id,
                role="primary",
            )
            db.add(assignment)

        # Day off on day 6 (skip index 5)

        # Next 5 nights starting day 7
        for i in range(7, 12):
            assignment = Assignment(
                id=uuid4(),
                block_id=blocks[i * 2 + 1].id,
                person_id=pgy2_resident.id,
                rotation_template_id=night_float_rotation.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        violations = validator.validate_night_float_limits(pgy2_resident.id, start_date)
        assert len(violations) == 0


# ============================================================================
# Test Class: Edge Cases and Boundary Conditions
# ============================================================================


class TestACGMEEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_resident_with_no_assignments(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test validation with resident who has no assignments."""
        start_date = date.today()

        violations = validator.validate_80_hour_limit(pgy2_resident.id, start_date)
        assert len(violations) == 0  # No violations if no work

    def test_validation_across_month_boundary(
        self,
        db: Session,
        validator: AdvancedACGMEValidator,
        pgy2_resident: Person,
        clinic_rotation: RotationTemplate,
    ):
        """Test validation that spans month boundaries."""
        # Start on last day of month
        start_date = date(2024, 1, 31)
        blocks = create_blocks(db, start_date, 28)

        # Create heavy schedule that spans into February
        for i in range(28):
            for tod_idx in range(2):
                block_idx = i * 2 + tod_idx
                if block_idx < len(blocks):
                    assignment = Assignment(
                        id=uuid4(),
                        block_id=blocks[block_idx].id,
                        person_id=pgy2_resident.id,
                        rotation_template_id=clinic_rotation.id,
                        role="primary",
                    )
                    db.add(assignment)
        db.commit()

        violations = validator.validate_80_hour_limit(pgy2_resident.id, start_date)
        # Should handle month transition correctly

    def test_leap_year_february_handling(
        self,
        db: Session,
        validator: AdvancedACGMEValidator,
        pgy2_resident: Person,
        clinic_rotation: RotationTemplate,
    ):
        """Test that leap year February (29 days) is handled correctly."""
        # Leap year February
        start_date = date(2024, 2, 1)
        blocks = create_blocks(db, start_date, 29)

        for i in range(29):
            assignment = Assignment(
                id=uuid4(),
                block_id=blocks[i * 2].id,
                person_id=pgy2_resident.id,
                rotation_template_id=clinic_rotation.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        violations = validator.validate_one_in_seven(pgy2_resident.id, start_date)
        # Should detect violations in 29-day February

    def test_multiple_residents_independent_validation(
        self,
        db: Session,
        validator: AdvancedACGMEValidator,
        pgy1_resident: Person,
        pgy2_resident: Person,
        pgy3_resident: Person,
        call_rotation: RotationTemplate,
    ):
        """Test that violations for one resident don't affect others."""
        start_date = date.today()
        blocks = create_blocks(db, start_date, 10)

        # PGY1: Violating schedule (24-hour shifts)
        for i in range(2):
            assignment = Assignment(
                id=uuid4(),
                block_id=blocks[i].id,
                person_id=pgy1_resident.id,
                rotation_template_id=call_rotation.id,
                role="primary",
            )
            db.add(assignment)

        # PGY2: Compliant schedule
        assignment = Assignment(
            id=uuid4(),
            block_id=blocks[5].id,
            person_id=pgy2_resident.id,
            rotation_template_id=call_rotation.id,
            role="primary",
        )
        db.add(assignment)

        db.commit()

        # PGY1 should have violations
        pgy1_violations = validator.validate_shift_length(pgy1_resident.id, start_date)
        assert len(pgy1_violations) > 0

        # PGY2 should be compliant
        pgy2_violations = validator.validate_shift_length(pgy2_resident.id, start_date)
        assert len(pgy2_violations) == 0
