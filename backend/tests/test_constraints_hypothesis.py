"""Property-based tests for scheduling constraints using Hypothesis."""

from datetime import date, timedelta
from uuid import uuid4

from hypothesis import given, settings
from hypothesis import strategies as st

from app.scheduling.constraints import (
    EightyHourRuleConstraint,
    OneInSevenRuleConstraint,
    SchedulingContext,
)

# Strategy to generate a list of daily work hours (0-12 hours per day)
daily_hours_strategy = st.lists(
    st.integers(min_value=0, max_value=12), min_size=28, max_size=56
)


class MockPerson:
    def __init__(self):
        self.id = uuid4()
        self.name = "Test Resident"
        self.type = "resident"
        self.pgy_level = 2


class MockBlock:
    def __init__(self, block_date, hours):
        self.id = uuid4()
        self.date = block_date
        self.time_of_day = "AM"
        self.is_weekend = block_date.weekday() >= 5


class MockAssignment:
    def __init__(self, person_id, block_id):
        self.id = uuid4()
        self.person_id = person_id
        self.block_id = block_id
        self.role = "primary"


@given(daily_hours=daily_hours_strategy)
@settings(max_examples=100)
def test_80_hour_rule_catches_all_violations(daily_hours):
    """
    Property: If any 4-week window has >80 hours average,
    the constraint must report a violation.
    """
    constraint = EightyHourRuleConstraint()

    # Create mock data
    resident = MockPerson()
    start_date = date(2024, 1, 1)

    # Build blocks and assignments based on hours
    blocks = []
    assignments = []

    for day_idx, hours in enumerate(daily_hours):
        block_date = start_date + timedelta(days=day_idx)
        # Create blocks proportional to hours (each block = 6 hours)
        num_blocks = hours // 6
        for _ in range(num_blocks):
            block = MockBlock(block_date, 6)
            blocks.append(block)
            assignments.append(MockAssignment(resident.id, block.id))

    # Create context
    context = SchedulingContext(
        residents=[resident],
        faculty=[],
        blocks=blocks,
        templates=[],
        start_date=start_date,
        end_date=start_date + timedelta(days=len(daily_hours) - 1),
    )
    context.availability = {resident.id: {b.id: {"available": True} for b in blocks}}

    # Check for actual violations (manual calculation)
    has_violation = False
    for window_start in range(len(daily_hours) - 27):
        window_hours = sum(daily_hours[window_start : window_start + 28])
        weekly_avg = window_hours / 4
        if weekly_avg > 80:
            has_violation = True
            break

    # Validate constraint
    result = constraint.validate(assignments, context)

    # Property: constraint should find violation if one exists
    if has_violation:
        assert (
            not result.satisfied or len(result.violations) > 0
        ), f"Constraint missed violation in window with {weekly_avg} hours/week avg"


@given(st.lists(st.booleans(), min_size=7, max_size=14))
@settings(max_examples=100)
def test_one_in_seven_rule_property(work_days):
    """
    Property: If someone works 7+ consecutive days,
    the 1-in-7 rule must report a violation.
    """
    # Count max consecutive True values
    max_consecutive = 0
    current_consecutive = 0
    for worked in work_days:
        if worked:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 0

    has_violation = max_consecutive >= 7

    # Build mock schedule
    constraint = OneInSevenRuleConstraint()
    resident = MockPerson()
    start_date = date(2024, 1, 1)

    blocks = []
    assignments = []
    for day_idx, worked in enumerate(work_days):
        if worked:
            block_date = start_date + timedelta(days=day_idx)
            block = MockBlock(block_date, 6)
            blocks.append(block)
            assignments.append(MockAssignment(resident.id, block.id))

    if not blocks:
        return  # Skip if no work days

    context = SchedulingContext(
        residents=[resident],
        faculty=[],
        blocks=blocks,
        templates=[],
        start_date=start_date,
        end_date=start_date + timedelta(days=len(work_days) - 1),
    )
    context.availability = {resident.id: {b.id: {"available": True} for b in blocks}}

    result = constraint.validate(assignments, context)

    if has_violation:
        assert (
            not result.satisfied or len(result.violations) > 0
        ), f"Constraint missed {max_consecutive} consecutive work days"
