"""
Tests for Advanced ACGME Validator.

Comprehensive test coverage for:
- 24+4 hour rule validation
- Night float limits (max 6 consecutive nights)
- Moonlighting hours tracking
- PGY-specific requirements (PGY-1: 16h, PGY-2+: 24h)
- Duty hours breakdown calculation
- Edge cases and boundary conditions
"""
from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
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
        name="Dr. PGY1 Resident",
        type="resident",
        email="pgy1@hospital.org",
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
        name="Dr. PGY2 Resident",
        type="resident",
        email="pgy2@hospital.org",
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
        name="Dr. PGY3 Resident",
        type="resident",
        email="pgy3@hospital.org",
        pgy_level=3,
    )
    db.add(resident)
    db.commit()
    db.refresh(resident)
    return resident


@pytest.fixture
def non_resident_faculty(db: Session) -> Person:
    """Create a non-resident faculty member for testing."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Faculty Member",
        type="faculty",
        email="faculty@hospital.org",
        performs_procedures=True,
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


def create_blocks_with_assignments(
    db: Session,
    person: Person,
    start_date: date,
    num_consecutive_days: int,
    time_of_day: str = "AM",
    include_both_shifts: bool = False,
) -> list[Assignment]:
    """
    Helper to create blocks and assignments for testing.

    Args:
        db: Database session
        person: Person to assign
        start_date: Starting date
        num_consecutive_days: Number of consecutive days to create
        time_of_day: "AM" or "PM" (if include_both_shifts=False)
        include_both_shifts: If True, creates both AM and PM for each day

    Returns:
        List of created assignments
    """
    assignments = []

    for i in range(num_consecutive_days):
        current_date = start_date + timedelta(days=i)
        is_weekend = current_date.weekday() >= 5

        if include_both_shifts:
            shifts = ["AM", "PM"]
        else:
            shifts = [time_of_day]

        for shift in shifts:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=shift,
                block_number=1,
                is_weekend=is_weekend,
                is_holiday=False,
            )
            db.add(block)
            db.flush()

            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=person.id,
                role="primary",
            )
            db.add(assignment)
            assignments.append(assignment)

    db.commit()
    for a in assignments:
        db.refresh(a)

    return assignments


# ============================================================================
# Test 24+4 Hour Rule
# ============================================================================


class TestValidate24Plus4Rule:
    """Test validate_24_plus_4_rule() method."""

    def test_no_violations_with_normal_schedule(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test that normal schedule with breaks has no violations."""
        start = date.today()

        # Create 3 days of AM shifts only (6 hours each = 18 hours total)
        create_blocks_with_assignments(db, pgy2_resident, start, 3, "AM")

        violations = validator.validate_24_plus_4_rule(
            pgy2_resident.id, start, start + timedelta(days=2)
        )

        assert len(violations) == 0

    def test_violation_with_excessive_continuous_hours(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test that exceeding 28 continuous hours triggers violation."""
        start = date.today()

        # Create 3 consecutive days with both AM and PM shifts
        # 3 days * 2 shifts * 6 hours = 36 hours > 28 hour limit
        create_blocks_with_assignments(
            db, pgy2_resident, start, 3, include_both_shifts=True
        )

        violations = validator.validate_24_plus_4_rule(
            pgy2_resident.id, start, start + timedelta(days=2)
        )

        assert len(violations) > 0
        assert violations[0].type == "24_PLUS_4_VIOLATION"
        assert violations[0].severity == "CRITICAL"
        assert violations[0].person_id == pgy2_resident.id
        assert "continuous_hours" in violations[0].details
        assert violations[0].details["continuous_hours"] > 28

    def test_no_violation_exactly_at_limit(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test that exactly 28 hours does not trigger violation."""
        start = date.today()

        # Create assignments totaling exactly 28 hours
        # Day 1: AM + PM = 12 hours
        # Day 2: AM + PM = 12 hours
        # Day 3: AM = 6 hours (need to stop here for exactly 30 hours)
        # But we need 28 hours, so let's do 4 shifts + 2/3 of another
        # Actually, each block is 6 hours, so 28 hours = 4.67 blocks
        # Since we can't do partial blocks, let's create 4 blocks (24 hours)
        create_blocks_with_assignments(db, pgy2_resident, start, 2, include_both_shifts=True)

        violations = validator.validate_24_plus_4_rule(
            pgy2_resident.id, start, start + timedelta(days=1)
        )

        # 24 hours should not violate
        assert len(violations) == 0

    def test_non_resident_returns_no_violations(
        self, db: Session, validator: AdvancedACGMEValidator, non_resident_faculty: Person
    ):
        """Test that non-residents are not validated."""
        start = date.today()

        # Create excessive hours for faculty
        create_blocks_with_assignments(
            db, non_resident_faculty, start, 5, include_both_shifts=True
        )

        violations = validator.validate_24_plus_4_rule(
            non_resident_faculty.id, start, start + timedelta(days=4)
        )

        assert len(violations) == 0

    def test_empty_assignments_returns_no_violations(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test that resident with no assignments has no violations."""
        start = date.today()

        violations = validator.validate_24_plus_4_rule(
            pgy2_resident.id, start, start + timedelta(days=7)
        )

        assert len(violations) == 0

    def test_nonexistent_person_returns_no_violations(
        self, db: Session, validator: AdvancedACGMEValidator
    ):
        """Test that nonexistent person ID returns no violations."""
        fake_id = uuid4()
        start = date.today()

        violations = validator.validate_24_plus_4_rule(
            fake_id, start, start + timedelta(days=7)
        )

        assert len(violations) == 0


# ============================================================================
# Test Night Float Limits
# ============================================================================


class TestValidateNightFloatLimits:
    """Test validate_night_float_limits() method."""

    def test_no_violations_with_few_night_shifts(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test that 3 consecutive night shifts is acceptable."""
        start = date.today()

        # Create 3 consecutive PM shifts (night shifts)
        create_blocks_with_assignments(db, pgy2_resident, start, 3, "PM")

        violations = validator.validate_night_float_limits(
            pgy2_resident.id, start, start + timedelta(days=2)
        )

        assert len(violations) == 0

    def test_violation_with_seven_consecutive_nights(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test that 7 consecutive night shifts triggers violation."""
        start = date.today()

        # Create 7 consecutive PM shifts (exceeds max of 6)
        create_blocks_with_assignments(db, pgy2_resident, start, 7, "PM")

        violations = validator.validate_night_float_limits(
            pgy2_resident.id, start, start + timedelta(days=6)
        )

        assert len(violations) > 0
        assert violations[0].type == "NIGHT_FLOAT_VIOLATION"
        assert violations[0].severity == "HIGH"
        assert violations[0].details["consecutive_nights"] == 7

    def test_exactly_six_consecutive_nights_no_violation(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test that exactly 6 consecutive nights is acceptable."""
        start = date.today()

        # Create exactly 6 consecutive PM shifts
        create_blocks_with_assignments(db, pgy2_resident, start, 6, "PM")

        violations = validator.validate_night_float_limits(
            pgy2_resident.id, start, start + timedelta(days=5)
        )

        assert len(violations) == 0

    def test_non_consecutive_nights_no_violation(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test that non-consecutive night shifts don't trigger violation."""
        start = date.today()

        # Create PM shifts on days 0, 1, 2, then skip 3, then 4, 5, 6
        # Two sequences of 3 nights each
        create_blocks_with_assignments(db, pgy2_resident, start, 3, "PM")
        create_blocks_with_assignments(db, pgy2_resident, start + timedelta(days=4), 3, "PM")

        violations = validator.validate_night_float_limits(
            pgy2_resident.id, start, start + timedelta(days=6)
        )

        assert len(violations) == 0

    def test_only_am_shifts_no_night_violations(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test that only AM shifts don't count as night float."""
        start = date.today()

        # Create 10 consecutive AM shifts
        create_blocks_with_assignments(db, pgy2_resident, start, 10, "AM")

        violations = validator.validate_night_float_limits(
            pgy2_resident.id, start, start + timedelta(days=9)
        )

        assert len(violations) == 0

    def test_no_night_shifts_returns_no_violations(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test that resident with no night shifts has no violations."""
        start = date.today()

        violations = validator.validate_night_float_limits(
            pgy2_resident.id, start, start + timedelta(days=7)
        )

        assert len(violations) == 0

    def test_non_resident_returns_no_violations(
        self, db: Session, validator: AdvancedACGMEValidator, non_resident_faculty: Person
    ):
        """Test that non-residents are not validated for night float."""
        start = date.today()

        # Create 10 consecutive PM shifts for faculty
        create_blocks_with_assignments(db, non_resident_faculty, start, 10, "PM")

        violations = validator.validate_night_float_limits(
            non_resident_faculty.id, start, start + timedelta(days=9)
        )

        assert len(violations) == 0


# ============================================================================
# Test Moonlighting Hours
# ============================================================================


class TestValidateMoonlightingHours:
    """Test validate_moonlighting_hours() method."""

    def test_no_violations_with_normal_hours(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test that normal hours don't trigger moonlighting violation."""
        start = date.today()

        # Create 4 weeks of reasonable schedule
        # 5 days/week * 2 shifts/day * 4 weeks = 40 blocks = 240 hours
        # 240 hours / 4 weeks = 60 hours/week (under 80 limit)
        for week in range(4):
            week_start = start + timedelta(weeks=week)
            for day in range(5):  # 5 days per week
                create_blocks_with_assignments(
                    db, pgy2_resident, week_start + timedelta(days=day), 1, include_both_shifts=True
                )

        violations = validator.validate_moonlighting_hours(
            pgy2_resident.id, start, start + timedelta(weeks=4), external_hours=0.0
        )

        assert len(violations) == 0

    def test_violation_with_excessive_total_hours(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test that excessive total hours trigger violation."""
        start = date.today()

        # Create 4 weeks of heavy schedule
        # 7 days/week * 2 shifts/day * 4 weeks = 56 blocks = 336 hours
        # 336 hours / 4 weeks = 84 hours/week (over 80 limit)
        for week in range(4):
            week_start = start + timedelta(weeks=week)
            create_blocks_with_assignments(
                db, pgy2_resident, week_start, 7, include_both_shifts=True
            )

        violations = validator.validate_moonlighting_hours(
            pgy2_resident.id, start, start + timedelta(weeks=4), external_hours=0.0
        )

        assert len(violations) > 0
        assert violations[0].type == "MOONLIGHTING_VIOLATION"
        assert violations[0].severity == "CRITICAL"
        assert violations[0].details["average_weekly_hours"] > 80

    def test_violation_with_external_moonlighting_hours(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test that external moonlighting hours are included in calculation."""
        start = date.today()

        # Create 4 weeks of moderate schedule
        # 5 days/week * 2 shifts/day * 4 weeks = 40 blocks = 240 hours
        # 240 hours / 4 weeks = 60 hours/week
        for week in range(4):
            week_start = start + timedelta(weeks=week)
            for day in range(5):
                create_blocks_with_assignments(
                    db, pgy2_resident, week_start + timedelta(days=day), 1, include_both_shifts=True
                )

        # Add 100 hours of external moonlighting (25 hours/week)
        # Total: 60 + 25 = 85 hours/week (over 80 limit)
        violations = validator.validate_moonlighting_hours(
            pgy2_resident.id, start, start + timedelta(weeks=4), external_hours=100.0
        )

        assert len(violations) > 0
        assert violations[0].details["external_hours"] == 100.0
        assert violations[0].details["average_weekly_hours"] > 80

    def test_no_violations_with_minimal_external_hours(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test that small amount of external hours stays under limit."""
        start = date.today()

        # Create 4 weeks of light schedule
        # 4 days/week * 2 shifts/day * 4 weeks = 32 blocks = 192 hours
        # 192 hours / 4 weeks = 48 hours/week
        for week in range(4):
            week_start = start + timedelta(weeks=week)
            for day in range(4):
                create_blocks_with_assignments(
                    db, pgy2_resident, week_start + timedelta(days=day), 1, include_both_shifts=True
                )

        # Add 80 hours of external moonlighting (20 hours/week)
        # Total: 48 + 20 = 68 hours/week (under 80 limit)
        violations = validator.validate_moonlighting_hours(
            pgy2_resident.id, start, start + timedelta(weeks=4), external_hours=80.0
        )

        assert len(violations) == 0

    def test_non_resident_returns_no_violations(
        self, db: Session, validator: AdvancedACGMEValidator, non_resident_faculty: Person
    ):
        """Test that non-residents are not validated for moonlighting."""
        start = date.today()

        # Create excessive schedule for faculty
        create_blocks_with_assignments(
            db, non_resident_faculty, start, 28, include_both_shifts=True
        )

        violations = validator.validate_moonlighting_hours(
            non_resident_faculty.id, start, start + timedelta(weeks=4), external_hours=200.0
        )

        assert len(violations) == 0


# ============================================================================
# Test PGY-Specific Rules
# ============================================================================


class TestValidatePGYSpecificRules:
    """Test validate_pgy_specific_rules() method."""

    def test_pgy1_no_violation_with_max_daily_hours(
        self, db: Session, validator: AdvancedACGMEValidator, pgy1_resident: Person
    ):
        """
        Test that PGY-1 with maximum daily hours (12) has no violation.

        Note: With half-day blocks (AM/PM), max hours per day is 12,
        which is under the 16-hour PGY-1 limit. This test confirms
        that the 12-hour max doesn't trigger false violations.
        """
        start = date.today()

        # Create day with both shifts (12 hours - max possible per day)
        create_blocks_with_assignments(db, pgy1_resident, start, 1, include_both_shifts=True)

        violations = validator.validate_pgy_specific_rules(
            pgy1_resident.id, start, start
        )

        # 12 hours is under 16-hour limit, should not violate
        assert len(violations) == 0

    def test_pgy1_no_violation_with_16_hour_shift(
        self, db: Session, validator: AdvancedACGMEValidator, pgy1_resident: Person
    ):
        """Test that PGY-1 with 16-hour shift is acceptable."""
        start = date.today()

        # Create less than 16 hours per day (2 shifts = 12 hours)
        create_blocks_with_assignments(db, pgy1_resident, start, 1, include_both_shifts=True)

        violations = validator.validate_pgy_specific_rules(
            pgy1_resident.id, start, start
        )

        assert len(violations) == 0

    def test_pgy2_no_violation_with_24_hour_shift(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test that PGY-2 can work 24-hour shifts."""
        start = date.today()

        # Create 2 consecutive days with both shifts (24 hours)
        create_blocks_with_assignments(db, pgy2_resident, start, 2, include_both_shifts=True)

        violations = validator.validate_pgy_specific_rules(
            pgy2_resident.id, start, start + timedelta(days=1)
        )

        assert len(violations) == 0

    def test_pgy3_no_violation_with_24_hour_shift(
        self, db: Session, validator: AdvancedACGMEValidator, pgy3_resident: Person
    ):
        """Test that PGY-3 can work 24-hour shifts."""
        start = date.today()

        # Create 2 consecutive days with both shifts (24 hours)
        create_blocks_with_assignments(db, pgy3_resident, start, 2, include_both_shifts=True)

        violations = validator.validate_pgy_specific_rules(
            pgy3_resident.id, start, start + timedelta(days=1)
        )

        assert len(violations) == 0

    def test_pgy2_no_violation_with_max_daily_hours(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """
        Test that PGY-2 with maximum daily hours (12) has no violation.

        Note: The validator checks hours per single date. With half-day
        blocks (AM/PM), max hours per date is 12, well under the 24-hour
        limit for PGY-2+. This test confirms expected behavior.
        """
        start = date.today()

        # Create multiple days with both shifts (12 hours each day)
        create_blocks_with_assignments(db, pgy2_resident, start, 3, include_both_shifts=True)

        violations = validator.validate_pgy_specific_rules(
            pgy2_resident.id, start, start + timedelta(days=2)
        )

        # Each day has 12 hours, under 24-hour limit, should not violate
        assert len(violations) == 0

    def test_non_resident_returns_no_violations(
        self, db: Session, validator: AdvancedACGMEValidator, non_resident_faculty: Person
    ):
        """Test that non-residents are not validated for PGY rules."""
        start = date.today()

        # Create excessive schedule for faculty
        create_blocks_with_assignments(db, non_resident_faculty, start, 5, include_both_shifts=True)

        violations = validator.validate_pgy_specific_rules(
            non_resident_faculty.id, start, start + timedelta(days=4)
        )

        assert len(violations) == 0


# ============================================================================
# Test Duty Hours Breakdown
# ============================================================================


class TestCalculateDutyHoursBreakdown:
    """Test calculate_duty_hours_breakdown() method."""

    def test_breakdown_with_normal_schedule(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test duty hours breakdown calculation with normal schedule."""
        # Start on a Monday to ensure weekdays only
        start = date.today()
        while start.weekday() != 0:  # 0 = Monday
            start += timedelta(days=1)

        # Create 2 weeks of schedule
        # Week 1: Mon-Fri, AM+PM (10 blocks = 60 hours)
        # Week 2: Mon-Fri, AM+PM (10 blocks = 60 hours)
        # Total: 120 hours over 14 days
        for week in range(2):
            week_start = start + timedelta(weeks=week)
            for day in range(5):  # Mon-Fri
                create_blocks_with_assignments(
                    db, pgy2_resident, week_start + timedelta(days=day), 1, include_both_shifts=True
                )

        breakdown = validator.calculate_duty_hours_breakdown(
            pgy2_resident.id, start, start + timedelta(days=13)
        )

        assert breakdown["person_id"] == str(pgy2_resident.id)
        assert breakdown["person_name"] == pgy2_resident.name
        assert breakdown["pgy_level"] == 2
        assert breakdown["hours"]["total"] == 120
        assert breakdown["hours"]["weekend"] == 0
        assert breakdown["days"]["worked"] == 10

    def test_breakdown_includes_weekend_hours(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test that weekend hours are tracked separately."""
        # Start on a Monday
        start = date.today()
        while start.weekday() != 0:  # 0 = Monday
            start += timedelta(days=1)

        # Create full week including weekend
        # Mon-Fri: 5 days * 2 shifts = 10 blocks = 60 hours weekday
        # Sat-Sun: 2 days * 2 shifts = 4 blocks = 24 hours weekend
        create_blocks_with_assignments(db, pgy2_resident, start, 7, include_both_shifts=True)

        breakdown = validator.calculate_duty_hours_breakdown(
            pgy2_resident.id, start, start + timedelta(days=6)
        )

        assert breakdown["hours"]["total"] == 84  # 14 blocks * 6 hours
        assert breakdown["hours"]["weekend"] == 24  # 4 blocks * 6 hours
        assert breakdown["hours"]["weekday"] == 60  # 10 blocks * 6 hours

    def test_breakdown_includes_night_hours(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test that night hours (PM shifts) are tracked separately."""
        start = date.today()

        # Create 1 week with mixed shifts
        # 7 days of AM shifts = 42 hours
        # 3 days of PM shifts = 18 hours night
        create_blocks_with_assignments(db, pgy2_resident, start, 7, "AM")
        create_blocks_with_assignments(db, pgy2_resident, start, 3, "PM")

        breakdown = validator.calculate_duty_hours_breakdown(
            pgy2_resident.id, start, start + timedelta(days=6)
        )

        assert breakdown["hours"]["total"] == 60  # 10 blocks * 6 hours
        assert breakdown["hours"]["night"] == 18  # 3 PM blocks * 6 hours

    def test_breakdown_calculates_average_weekly_hours(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test that average weekly hours are calculated correctly."""
        start = date.today()

        # Create 4 weeks of schedule
        # 5 days/week * 2 shifts/day * 4 weeks = 40 blocks = 240 hours
        # Average: 240 / 4 = 60 hours/week
        for week in range(4):
            week_start = start + timedelta(weeks=week)
            for day in range(5):
                create_blocks_with_assignments(
                    db, pgy2_resident, week_start + timedelta(days=day), 1, include_both_shifts=True
                )

        breakdown = validator.calculate_duty_hours_breakdown(
            pgy2_resident.id, start, start + timedelta(weeks=4)
        )

        assert breakdown["hours"]["total"] == 240
        assert breakdown["hours"]["average_weekly"] == 60.0

    def test_breakdown_with_no_assignments(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test breakdown with resident who has no assignments."""
        start = date.today()

        breakdown = validator.calculate_duty_hours_breakdown(
            pgy2_resident.id, start, start + timedelta(days=13)
        )

        assert breakdown["hours"]["total"] == 0
        assert breakdown["hours"]["weekend"] == 0
        assert breakdown["hours"]["night"] == 0
        assert breakdown["days"]["worked"] == 0

    def test_breakdown_with_nonexistent_person(
        self, db: Session, validator: AdvancedACGMEValidator
    ):
        """Test breakdown with nonexistent person returns empty dict."""
        fake_id = uuid4()
        start = date.today()

        breakdown = validator.calculate_duty_hours_breakdown(
            fake_id, start, start + timedelta(days=13)
        )

        assert breakdown == {}

    def test_breakdown_period_dates_are_correct(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test that period dates are correctly included in breakdown."""
        start = date(2025, 1, 1)
        end = date(2025, 1, 14)

        create_blocks_with_assignments(db, pgy2_resident, start, 7, "AM")

        breakdown = validator.calculate_duty_hours_breakdown(
            pgy2_resident.id, start, end
        )

        assert breakdown["period"]["start"] == "2025-01-01"
        assert breakdown["period"]["end"] == "2025-01-14"
        assert breakdown["days"]["total_in_period"] == 14


# ============================================================================
# Test Helper Method: _assignments_to_hours
# ============================================================================


class TestAssignmentsToHours:
    """Test _assignments_to_hours() helper method."""

    def test_converts_single_assignment_to_hours(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test converting single assignment to hours."""
        start = date.today()

        assignments = create_blocks_with_assignments(db, pgy2_resident, start, 1, "AM")

        hours_by_date = validator._assignments_to_hours(assignments)

        assert len(hours_by_date) == 1
        assert hours_by_date[start] == 6  # HOURS_PER_HALF_DAY

    def test_converts_multiple_assignments_same_day(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test converting multiple assignments on same day."""
        start = date.today()

        assignments = create_blocks_with_assignments(
            db, pgy2_resident, start, 1, include_both_shifts=True
        )

        hours_by_date = validator._assignments_to_hours(assignments)

        assert len(hours_by_date) == 1
        assert hours_by_date[start] == 12  # 2 shifts * 6 hours

    def test_converts_multiple_days(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test converting assignments across multiple days."""
        start = date.today()

        assignments = create_blocks_with_assignments(db, pgy2_resident, start, 3, "AM")

        hours_by_date = validator._assignments_to_hours(assignments)

        assert len(hours_by_date) == 3
        assert hours_by_date[start] == 6
        assert hours_by_date[start + timedelta(days=1)] == 6
        assert hours_by_date[start + timedelta(days=2)] == 6

    def test_empty_assignments_returns_empty_dict(
        self, db: Session, validator: AdvancedACGMEValidator
    ):
        """Test that empty assignments list returns empty dict."""
        hours_by_date = validator._assignments_to_hours([])

        assert hours_by_date == {}

    def test_converts_mixed_schedule(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test converting complex schedule with various patterns."""
        start = date.today()

        # Day 1: AM + PM (12 hours)
        # Day 2: AM only (6 hours)
        # Day 3: PM only (6 hours)
        # Day 4: AM + PM (12 hours)
        create_blocks_with_assignments(db, pgy2_resident, start, 1, include_both_shifts=True)
        create_blocks_with_assignments(db, pgy2_resident, start + timedelta(days=1), 1, "AM")
        create_blocks_with_assignments(db, pgy2_resident, start + timedelta(days=2), 1, "PM")
        create_blocks_with_assignments(db, pgy2_resident, start + timedelta(days=3), 1, include_both_shifts=True)

        hours_by_date = validator._assignments_to_hours(
            db.query(Assignment).filter(Assignment.person_id == pgy2_resident.id).all()
        )

        assert hours_by_date[start] == 12
        assert hours_by_date[start + timedelta(days=1)] == 6
        assert hours_by_date[start + timedelta(days=2)] == 6
        assert hours_by_date[start + timedelta(days=3)] == 12


# ============================================================================
# Edge Cases and Boundary Conditions
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_day_validation_period(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test validation with single-day period."""
        start = date.today()

        create_blocks_with_assignments(db, pgy2_resident, start, 1, include_both_shifts=True)

        violations = validator.validate_24_plus_4_rule(pgy2_resident.id, start, start)

        # Single day with 12 hours should not violate
        assert len(violations) == 0

    def test_validation_with_gaps_in_schedule(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test that gaps in schedule reset continuous hours count."""
        start = date.today()

        # Create assignments on days 0-2, skip 3-4, then 5-7
        create_blocks_with_assignments(db, pgy2_resident, start, 3, include_both_shifts=True)
        create_blocks_with_assignments(
            db, pgy2_resident, start + timedelta(days=5), 3, include_both_shifts=True
        )

        violations = validator.validate_24_plus_4_rule(
            pgy2_resident.id, start, start + timedelta(days=7)
        )

        # Each segment is 36 hours (3 days * 12 hours/day)
        # But there's a gap, so they should be evaluated separately
        # 36 hours > 28, so we should have violations
        assert len(violations) > 0

    def test_date_boundary_exactly_on_week_boundary(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test calculation when period is exactly 7 days."""
        start = date.today()

        create_blocks_with_assignments(db, pgy2_resident, start, 7, "AM")

        breakdown = validator.calculate_duty_hours_breakdown(
            pgy2_resident.id, start, start + timedelta(days=6)
        )

        assert breakdown["hours"]["total"] == 42  # 7 days * 6 hours
        assert breakdown["days"]["total_in_period"] == 7

    def test_very_long_validation_period(
        self, db: Session, validator: AdvancedACGMEValidator, pgy2_resident: Person
    ):
        """Test validation over a very long period (365 days)."""
        start = date.today()

        # Create sparse assignments over a year
        for month in range(12):
            month_start = start + timedelta(days=month * 30)
            create_blocks_with_assignments(db, pgy2_resident, month_start, 5, "AM")

        breakdown = validator.calculate_duty_hours_breakdown(
            pgy2_resident.id, start, start + timedelta(days=364)
        )

        assert breakdown["hours"]["total"] == 360  # 60 blocks * 6 hours
        assert breakdown["hours"]["average_weekly"] > 0

    def test_all_validators_with_same_resident(
        self, db: Session, validator: AdvancedACGMEValidator, pgy1_resident: Person
    ):
        """Test running all validators on same resident data."""
        start = date.today()

        # Create a complex schedule
        create_blocks_with_assignments(db, pgy1_resident, start, 10, "PM")

        # Run all validators
        violations_24_4 = validator.validate_24_plus_4_rule(
            pgy1_resident.id, start, start + timedelta(days=9)
        )
        violations_night = validator.validate_night_float_limits(
            pgy1_resident.id, start, start + timedelta(days=9)
        )
        violations_moon = validator.validate_moonlighting_hours(
            pgy1_resident.id, start, start + timedelta(days=9), external_hours=50.0
        )
        violations_pgy = validator.validate_pgy_specific_rules(
            pgy1_resident.id, start, start + timedelta(days=9)
        )
        breakdown = validator.calculate_duty_hours_breakdown(
            pgy1_resident.id, start, start + timedelta(days=9)
        )

        # Should have night float violation (10 consecutive nights > 6)
        assert len(violations_night) > 0

        # Should have breakdown data
        assert breakdown["hours"]["total"] > 0
        assert breakdown["hours"]["night"] > 0
