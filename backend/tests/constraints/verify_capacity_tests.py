"""
Standalone verification script for capacity constraint tests.
Run without pytest to verify test logic works.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from datetime import date, timedelta
from uuid import uuid4

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.capacity import (
    ClinicCapacityConstraint,
    CoverageConstraint,
    MaxPhysiciansInClinicConstraint,
    OnePersonPerBlockConstraint,
)


# Mock classes (same as in test file)
class MockPerson:
    def __init__(self, person_id=None, name="Test", person_type="resident", pgy_level=None):
        self.id = person_id or uuid4()
        self.name = name
        self.type = person_type
        self.pgy_level = pgy_level


class MockBlock:
    def __init__(self, block_id=None, block_date=None, time_of_day="AM", is_weekend=False):
        self.id = block_id or uuid4()
        self.date = block_date or date.today()
        self.time_of_day = time_of_day
        self.is_weekend = is_weekend


class MockTemplate:
    def __init__(self, template_id=None, name="Test", activity_type="outpatient", max_residents=None):
        self.id = template_id or uuid4()
        self.name = name
        self.activity_type = activity_type
        self.max_residents = max_residents


class MockAssignment:
    def __init__(self, assignment_id=None, person_id=None, block_id=None, rotation_template_id=None, role="primary"):
        self.id = assignment_id or uuid4()
        self.person_id = person_id
        self.block_id = block_id
        self.rotation_template_id = rotation_template_id
        self.role = role


def test_one_person_per_block_basic():
    """Test OnePersonPerBlockConstraint basic validation."""
    print("Testing OnePersonPerBlockConstraint...")

    constraint = OnePersonPerBlockConstraint()
    assert constraint.name == "OnePersonPerBlock"
    assert constraint.constraint_type == ConstraintType.CAPACITY
    assert constraint.priority == ConstraintPriority.CRITICAL

    # Test valid scenario
    blocks = [MockBlock() for _ in range(3)]
    residents = [MockPerson() for _ in range(2)]

    assignments = [
        MockAssignment(person_id=residents[0].id, block_id=blocks[0].id, role="primary"),
        MockAssignment(person_id=residents[1].id, block_id=blocks[1].id, role="primary"),
    ]

    context = SchedulingContext(
        residents=residents,
        faculty=[],
        blocks=blocks,
        templates=[],
    )

    result = constraint.validate(assignments, context)
    assert result.satisfied is True, "Should pass with one primary per block"

    # Test violation scenario
    assignments.append(
        MockAssignment(person_id=residents[1].id, block_id=blocks[0].id, role="primary")
    )

    result = constraint.validate(assignments, context)
    assert result.satisfied is False, "Should fail with two primaries in same block"
    assert len(result.violations) == 1

    print("✓ OnePersonPerBlockConstraint tests passed")


def test_clinic_capacity_basic():
    """Test ClinicCapacityConstraint basic validation."""
    print("Testing ClinicCapacityConstraint...")

    constraint = ClinicCapacityConstraint()
    assert constraint.name == "ClinicCapacity"

    blocks = [MockBlock() for _ in range(2)]
    residents = [MockPerson() for _ in range(5)]
    template = MockTemplate(name="Clinic", max_residents=4)

    # Test within capacity
    assignments = [
        MockAssignment(
            person_id=residents[i].id,
            block_id=blocks[0].id,
            rotation_template_id=template.id
        )
        for i in range(3)
    ]

    context = SchedulingContext(
        residents=residents,
        faculty=[],
        blocks=blocks,
        templates=[template],
    )

    result = constraint.validate(assignments, context)
    assert result.satisfied is True, "Should pass with 3 residents (limit 4)"

    # Test exceeds capacity
    assignments.extend([
        MockAssignment(
            person_id=residents[3].id,
            block_id=blocks[0].id,
            rotation_template_id=template.id
        ),
        MockAssignment(
            person_id=residents[4].id,
            block_id=blocks[0].id,
            rotation_template_id=template.id
        ),
    ])

    result = constraint.validate(assignments, context)
    assert result.satisfied is False, "Should fail with 5 residents (limit 4)"
    assert len(result.violations) == 1
    assert result.violations[0].details["count"] == 5
    assert result.violations[0].details["limit"] == 4

    print("✓ ClinicCapacityConstraint tests passed")


def test_max_physicians_in_clinic_basic():
    """Test MaxPhysiciansInClinicConstraint basic validation."""
    print("Testing MaxPhysiciansInClinicConstraint...")

    constraint = MaxPhysiciansInClinicConstraint(max_physicians=6)
    assert constraint.name == "MaxPhysiciansInClinic"

    blocks = [MockBlock()]
    residents = [MockPerson(person_type="resident") for _ in range(4)]
    faculty = [MockPerson(person_type="faculty") for _ in range(3)]
    template = MockTemplate(activity_type="outpatient")

    # Test at limit (4 residents + 2 faculty = 6, at limit)
    assignments = []
    for r in residents:
        assignments.append(
            MockAssignment(person_id=r.id, block_id=blocks[0].id, rotation_template_id=template.id)
        )
    for f in faculty[:2]:
        assignments.append(
            MockAssignment(person_id=f.id, block_id=blocks[0].id, rotation_template_id=template.id)
        )

    context = SchedulingContext(
        residents=residents,
        faculty=faculty,
        blocks=blocks,
        templates=[template],
    )

    result = constraint.validate(assignments, context)
    assert result.satisfied is True, "Should pass with 6 physicians (limit 6)"

    # Add one more faculty - should exceed
    assignments.append(
        MockAssignment(person_id=faculty[2].id, block_id=blocks[0].id, rotation_template_id=template.id)
    )

    result = constraint.validate(assignments, context)
    assert result.satisfied is False, "Should fail with 7 physicians (limit 6)"
    assert result.violations[0].details["count"] == 7

    print("✓ MaxPhysiciansInClinicConstraint tests passed")


def test_coverage_constraint_basic():
    """Test CoverageConstraint basic validation."""
    print("Testing CoverageConstraint...")

    constraint = CoverageConstraint(weight=1000.0)
    assert constraint.name == "Coverage"

    # Create 5 workday blocks
    blocks = [MockBlock(is_weekend=False) for _ in range(5)]
    residents = [MockPerson() for _ in range(3)]
    template = MockTemplate()

    # Test 100% coverage
    assignments = [
        MockAssignment(
            person_id=residents[i % len(residents)].id,
            block_id=blocks[i].id,
            rotation_template_id=template.id
        )
        for i in range(5)
    ]

    context = SchedulingContext(
        residents=residents,
        faculty=[],
        blocks=blocks,
        templates=[template],
    )

    result = constraint.validate(assignments, context)
    assert result.satisfied is True, "Soft constraints always return satisfied=True"
    assert len(result.violations) == 0, "100% coverage should have no violations"
    assert result.penalty == 0.0, "100% coverage should have 0 penalty"

    # Test partial coverage (50%)
    half_assignments = assignments[:2]  # Only 2 out of 5 blocks

    result = constraint.validate(half_assignments, context)
    assert result.satisfied is True
    assert len(result.violations) == 1, "< 90% coverage should have violation"
    # Penalty should be (1 - 0.4) * 1000 = 600
    assert 500 < result.penalty < 700, f"Expected penalty ~600, got {result.penalty}"

    print("✓ CoverageConstraint tests passed")


def main():
    """Run all basic tests."""
    print("=" * 60)
    print("Verifying Capacity Constraint Tests")
    print("=" * 60)
    print()

    try:
        test_one_person_per_block_basic()
        test_clinic_capacity_basic()
        test_max_physicians_in_clinic_basic()
        test_coverage_constraint_basic()

        print()
        print("=" * 60)
        print("✓ All basic tests passed successfully!")
        print("=" * 60)
        print()
        print("The test file logic is verified and working correctly.")
        print("Full pytest suite can be run once all dependencies are installed.")
        return 0

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
