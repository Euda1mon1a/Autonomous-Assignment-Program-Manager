"""
Performance test fixtures and configuration.

Provides shared fixtures for creating large-scale test data and measuring
performance metrics across ACGME compliance validation tests.
"""

import time
from collections.abc import Generator
from contextlib import contextmanager
from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.utils.academic_blocks import get_block_number_for_date

# ============================================================================
# Performance Thresholds
# ============================================================================

# ACGME validation should complete quickly even for large datasets
MAX_VALIDATION_TIME_100_RESIDENTS = 5.0  # seconds
MAX_VALIDATION_TIME_50_RESIDENTS = 2.0  # seconds
MAX_VALIDATION_TIME_25_RESIDENTS = 1.0  # seconds

# Concurrent validation should not degrade significantly
MAX_CONCURRENT_VALIDATION_TIME = 10.0  # seconds for 10 concurrent validations

# Memory should remain reasonable (tracked via monitoring, not enforced here)
MAX_MEMORY_MB = 500  # MB per validation operation


# ============================================================================
# Performance Measurement Utilities
# ============================================================================


class PerformanceTimer:
    """Context manager for measuring execution time."""

    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.duration = None

    def __enter__(self):
        """Start timing."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and calculate duration."""
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time
        print(f"\n{self.name}: {self.duration:.3f}s")

    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self.duration is not None:
            return self.duration
        if self.start_time is not None:
            return time.perf_counter() - self.start_time
        return 0.0


@pytest.fixture
def perf_timer():
    """Fixture that provides a performance timer."""

    def _timer(name: str = "Operation") -> PerformanceTimer:
        return PerformanceTimer(name)

    return _timer


@contextmanager
def measure_time(operation_name: str) -> Generator[dict, None, None]:
    """
    Context manager to measure and report execution time.

    Usage:
        with measure_time("My operation") as metrics:
            # ... do work ...
            pass
        print(f"Took {metrics['duration']:.3f}s")
    """
    metrics = {"start": time.perf_counter()}
    try:
        yield metrics
    finally:
        metrics["end"] = time.perf_counter()
        metrics["duration"] = metrics["end"] - metrics["start"]
        print(f"\n{operation_name}: {metrics['duration']:.3f}s")


# ============================================================================
# Large Dataset Fixtures
# ============================================================================


@pytest.fixture
def large_rotation_template(db: Session) -> RotationTemplate:
    """Create a standard rotation template for assignments."""
    template = RotationTemplate(
        id=uuid4(),
        name="Primary Care Clinic",
        activity_type="clinic",
        abbreviation="PC",
        clinic_location="Main Clinic",
        max_residents=8,
        supervision_required=True,
        max_supervision_ratio=4,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@pytest.fixture
def large_resident_dataset(db: Session) -> dict:
    """
    Create 100 residents with realistic PGY distribution.

    Returns:
        dict with:
            - residents: list[Person] - All 100 residents
            - pgy1: list[Person] - PGY-1 residents (~40)
            - pgy2: list[Person] - PGY-2 residents (~35)
            - pgy3: list[Person] - PGY-3 residents (~25)
    """
    residents = []

    # Realistic PGY distribution for a large program
    pgy_distribution = [
        (1, 40),  # PGY-1: 40 residents
        (2, 35),  # PGY-2: 35 residents
        (3, 25),  # PGY-3: 25 residents
    ]

    for pgy_level, count in pgy_distribution:
        for i in range(count):
            resident = Person(
                id=uuid4(),
                name=f"Resident PGY{pgy_level}-{i + 1:03d}",
                type="resident",
                email=f"pgy{pgy_level}.r{i + 1:03d}@hospital.org",
                pgy_level=pgy_level,
                target_clinical_blocks=48,  # ~12 weeks clinical
            )
            db.add(resident)
            residents.append(resident)

    db.commit()
    for r in residents:
        db.refresh(r)

    # Organize by PGY level for easy access
    return {
        "residents": residents,
        "pgy1": [r for r in residents if r.pgy_level == 1],
        "pgy2": [r for r in residents if r.pgy_level == 2],
        "pgy3": [r for r in residents if r.pgy_level == 3],
    }


@pytest.fixture
def large_faculty_dataset(db: Session) -> list[Person]:
    """
    Create 30 faculty members for supervision.

    For 100 residents with proper supervision ratios, we need:
    - ~20 faculty for PGY-1 (1:2 ratio)
    - ~20 faculty for PGY-2/3 (1:4 ratio)
    - Some overlap, so 30 total is reasonable
    """
    faculty = []

    for i in range(30):
        fac = Person(
            id=uuid4(),
            name=f"Faculty {i + 1:03d}",
            type="faculty",
            email=f"faculty{i + 1:03d}@hospital.org",
            performs_procedures=(i % 3 == 0),  # 1/3 perform procedures
            specialties=["Primary Care", "General Medicine"],
            primary_duty="Clinical Education",
        )
        db.add(fac)
        faculty.append(fac)

    db.commit()
    for f in faculty:
        db.refresh(f)

    return faculty


@pytest.fixture
def four_week_blocks(db: Session) -> list[Block]:
    """
    Create 4 weeks of blocks (28 days = 56 blocks).

    Used for testing 80-hour rule rolling window validation.
    """
    blocks = []
    start_date = date.today()

    for day_offset in range(28):
        current_date = start_date + timedelta(days=day_offset)
        is_weekend = current_date.weekday() >= 5

        for time_of_day in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=time_of_day,
                block_number=1,
                is_weekend=is_weekend,
                is_holiday=False,
            )
            db.add(block)
            blocks.append(block)

    db.commit()
    for b in blocks:
        db.refresh(b)

    return blocks


@pytest.fixture
def large_assignment_dataset(
    db: Session,
    large_resident_dataset: dict,
    large_faculty_dataset: list[Person],
    four_week_blocks: list[Block],
    large_rotation_template: RotationTemplate,
) -> dict:
    """
    Create assignments for 100 residents over 4 weeks.

    This generates ~5,600 assignments (100 residents × 56 blocks).
    Each block also gets faculty supervision assignments.

    Returns:
        dict with:
            - assignments: list[Assignment] - All assignments
            - resident_assignments: list[Assignment] - Only resident assignments
            - faculty_assignments: list[Assignment] - Only faculty assignments
            - total_count: int - Total assignment count
    """
    assignments = []
    residents = large_resident_dataset["residents"]

    # Assign each resident to most blocks (simulating full clinical schedule)
    # Skip some weekend blocks to allow for 1-in-7 compliance
    for resident in residents:
        resident_block_count = 0
        consecutive_days = 0

        for i, block in enumerate(four_week_blocks):
            # Implement 1-in-7 rule: give residents at least 1 day off per week
            # Skip blocks to create rest days
            day_of_week = block.date.weekday()

            # Give each resident Sunday off (day 6)
            if day_of_week == 6:
                consecutive_days = 0
                continue

            # Occasionally skip a Saturday to provide variety
            if day_of_week == 5 and resident_block_count % 7 == 0:
                consecutive_days = 0
                continue

            consecutive_days += 1

            # Create assignment
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=resident.id,
                rotation_template_id=large_rotation_template.id,
                role="primary",
            )
            db.add(assignment)
            assignments.append(assignment)
            resident_block_count += 1

    # Add faculty supervision for weekday blocks
    faculty_idx = 0
    for block in four_week_blocks:
        if not block.is_weekend:
            # Assign 2-3 faculty per weekday block for supervision
            for _ in range(3):
                faculty = large_faculty_dataset[
                    faculty_idx % len(large_faculty_dataset)
                ]
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=faculty.id,
                    rotation_template_id=large_rotation_template.id,
                    role="supervising",
                )
                db.add(assignment)
                assignments.append(assignment)
                faculty_idx += 1

    db.commit()
    for a in assignments:
        db.refresh(a)

    resident_assignments = [a for a in assignments if a.role == "primary"]
    faculty_assignments = [a for a in assignments if a.role == "supervising"]

    return {
        "assignments": assignments,
        "resident_assignments": resident_assignments,
        "faculty_assignments": faculty_assignments,
        "total_count": len(assignments),
    }


@pytest.fixture
def huge_dataset(
    db: Session,
    large_resident_dataset: dict,
    large_faculty_dataset: list[Person],
    large_rotation_template: RotationTemplate,
) -> dict:
    """
    Create 12 weeks of blocks and assignments for extreme load testing.

    This generates ~16,800 assignments (100 residents × 168 blocks).
    Used for testing memory efficiency and very large dataset performance.

    Returns:
        dict with blocks, assignments, and residents

    Block numbers use Thursday-Wednesday alignment via get_block_number_for_date.
    """
    blocks = []
    start_date = date.today()

    # Create 12 weeks (84 days = 168 blocks)
    for day_offset in range(84):
        current_date = start_date + timedelta(days=day_offset)
        is_weekend = current_date.weekday() >= 5
        # Use Thursday-Wednesday aligned block number calculation
        block_number, _ = get_block_number_for_date(current_date)

        for time_of_day in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=time_of_day,
                block_number=block_number,
                is_weekend=is_weekend,
                is_holiday=False,
            )
            db.add(block)
            blocks.append(block)

    db.commit()

    # Create assignments (similar pattern to large_assignment_dataset)
    assignments = []
    residents = large_resident_dataset["residents"]

    for resident in residents:
        for block in blocks:
            # Skip Sundays
            if block.date.weekday() == 6:
                continue

            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=resident.id,
                rotation_template_id=large_rotation_template.id,
                role="primary",
            )
            db.add(assignment)
            assignments.append(assignment)

    db.commit()

    return {
        "blocks": blocks,
        "assignments": assignments,
        "residents": residents,
        "start_date": start_date,
        "end_date": start_date + timedelta(days=83),
    }


# ============================================================================
# Performance Assertion Helpers
# ============================================================================


def assert_performance(duration: float, max_duration: float, operation: str):
    """
    Assert that an operation completed within the performance threshold.

    Args:
        duration: Actual duration in seconds
        max_duration: Maximum allowed duration in seconds
        operation: Name of the operation for error message

    Raises:
        AssertionError if performance threshold exceeded
    """
    assert duration <= max_duration, (
        f"{operation} took {duration:.3f}s, "
        f"exceeding threshold of {max_duration:.3f}s "
        f"(slowdown: {((duration / max_duration - 1) * 100):.1f}%)"
    )
    print(
        f"✓ {operation} completed in {duration:.3f}s (threshold: {max_duration:.3f}s)"
    )
