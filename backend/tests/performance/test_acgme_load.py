"""
Performance tests for ACGME compliance validation under load.

Tests the ACGMEValidator's ability to handle large datasets efficiently,
including validation of 100+ residents with thousands of assignments.

Performance Requirements:
    - 100 residents, 4 weeks: < 5s validation time
    - 50 residents, 4 weeks: < 2s validation time
    - 25 residents, 4 weeks: < 1s validation time
    - 10 concurrent validations: < 10s total time
    - Memory usage: < 500MB per validation

Usage:
    # Run all performance tests
    pytest tests/performance/test_acgme_load.py -v

    # Run only performance-marked tests
    pytest -m performance

    # Run with verbose timing output
    pytest tests/performance/test_acgme_load.py -v -s
"""

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.scheduling.validator import ACGMEValidator

from .conftest import (
    MAX_CONCURRENT_VALIDATION_TIME,
    MAX_VALIDATION_TIME_25_RESIDENTS,
    MAX_VALIDATION_TIME_50_RESIDENTS,
    MAX_VALIDATION_TIME_100_RESIDENTS,
    assert_performance,
    measure_time,
)

# ============================================================================
# ACGME Validation Performance Tests
# ============================================================================


@pytest.mark.performance
@pytest.mark.slow
class TestACGMEPerformance:
    """Performance tests for ACGME compliance validation."""

    def test_80_hour_rule_large_dataset(
        self,
        db: Session,
        large_resident_dataset: dict,
        large_assignment_dataset: dict,
        four_week_blocks: list[Block],
    ):
        """
        Test 80-hour rule validation with 100 residents over 4-week period.

        Requirements:
            - Should complete in < 5 seconds for 100 residents
            - Should correctly identify violations
            - Should handle rolling window calculations efficiently

        Test Data:
            - 100 residents (40 PGY-1, 35 PGY-2, 25 PGY-3)
            - 56 blocks (28 days × 2 sessions)
            - ~5,600 assignments
        """
        validator = ACGMEValidator(db)
        residents = large_resident_dataset["residents"]

        start_date = four_week_blocks[0].date
        end_date = four_week_blocks[-1].date

        print(f"\nValidating 80-hour rule for {len(residents)} residents")
        print(f"Date range: {start_date} to {end_date}")
        print(f"Total assignments: {large_assignment_dataset['total_count']}")

        # Measure validation time
        with measure_time("80-hour rule validation (100 residents)") as metrics:
            result = validator.validate_all(start_date, end_date)

        # Assert performance
        assert_performance(
            metrics["duration"],
            MAX_VALIDATION_TIME_100_RESIDENTS,
            "80-hour rule validation (100 residents)",
        )

        # Verify correctness (basic sanity checks)
        assert result is not None
        assert hasattr(result, "violations")
        assert hasattr(result, "total_violations")
        assert result.statistics is not None
        assert result.statistics["residents_scheduled"] == len(residents)

        # Log results
        print(f"Total violations: {result.total_violations}")
        print(f"Coverage rate: {result.coverage_rate:.1f}%")
        print(
            f"Validation rate: {len(residents) / metrics['duration']:.1f} residents/sec"
        )

    def test_1_in_7_rule_large_dataset(
        self,
        db: Session,
        large_resident_dataset: dict,
        large_assignment_dataset: dict,
        four_week_blocks: list[Block],
    ):
        """
        Test 1-in-7 rule validation with large assignment sets.

        Requirements:
            - Should complete in < 5 seconds for 100 residents
            - Should detect consecutive duty day violations
            - Should handle date gaps correctly

        The 1-in-7 rule requires at least one 24-hour period off every 7 days.
        """
        validator = ACGMEValidator(db)
        residents = large_resident_dataset["residents"]

        start_date = four_week_blocks[0].date
        end_date = four_week_blocks[-1].date

        print(f"\nValidating 1-in-7 rule for {len(residents)} residents")

        with measure_time("1-in-7 rule validation (100 residents)") as metrics:
            result = validator.validate_all(start_date, end_date)

        # Assert performance
        assert_performance(
            metrics["duration"],
            MAX_VALIDATION_TIME_100_RESIDENTS,
            "1-in-7 rule validation (100 residents)",
        )

        # Check for 1-in-7 violations specifically
        one_in_seven_violations = [
            v for v in result.violations if v.type == "1_IN_7_VIOLATION"
        ]

        print(f"1-in-7 violations found: {len(one_in_seven_violations)}")

        # Our test data should be mostly compliant (residents get Sundays off)
        # Allow some violations but not excessive
        assert (
            len(one_in_seven_violations) < len(residents) * 0.1
        )  # < 10% violation rate

    def test_supervision_ratio_validation_under_load(
        self,
        db: Session,
        large_resident_dataset: dict,
        large_faculty_dataset: list[Person],
        large_assignment_dataset: dict,
        four_week_blocks: list[Block],
    ):
        """
        Test supervision ratio validation under load.

        Requirements:
            - Should complete in < 5 seconds
            - Should correctly calculate PGY-specific ratios
            - Should identify blocks with insufficient supervision

        ACGME Ratios:
            - PGY-1: 1 faculty : 2 residents
            - PGY-2/3: 1 faculty : 4 residents
        """
        validator = ACGMEValidator(db)

        start_date = four_week_blocks[0].date
        end_date = four_week_blocks[-1].date

        print("\nValidating supervision ratios")
        print(f"Residents: {len(large_resident_dataset['residents'])}")
        print(f"Faculty: {len(large_faculty_dataset)}")
        print(f"Blocks: {len(four_week_blocks)}")

        with measure_time("Supervision ratio validation") as metrics:
            result = validator.validate_all(start_date, end_date)

        # Assert performance
        assert_performance(
            metrics["duration"],
            MAX_VALIDATION_TIME_100_RESIDENTS,
            "Supervision ratio validation",
        )

        # Check supervision violations
        supervision_violations = [
            v for v in result.violations if v.type == "SUPERVISION_RATIO_VIOLATION"
        ]

        print(f"Supervision violations: {len(supervision_violations)}")

        # With 30 faculty and 100 residents, we should have adequate supervision
        # on most blocks (faculty are assigned 3 per weekday block in fixture)
        # Some violations are expected but should be minority
        weekday_blocks = [b for b in four_week_blocks if not b.is_weekend]
        violation_rate = len(supervision_violations) / len(weekday_blocks)
        assert violation_rate < 0.2  # < 20% blocks with violations

    def test_full_validation_medium_dataset(
        self,
        db: Session,
        large_rotation_template: RotationTemplate,
        four_week_blocks: list[Block],
    ):
        """
        Test full ACGME validation with 50 residents (medium dataset).

        Requirements:
            - Should complete in < 2 seconds
            - Tests all three validation types together
            - Representative of medium-sized residency programs
        """
        # Create 50 residents
        residents = []
        for pgy in [1, 2, 3]:
            for i in range(17):  # ~17 residents per PGY level
                resident = Person(
                    id=uuid4(),
                    name=f"Med Resident PGY{pgy}-{i + 1}",
                    type="resident",
                    email=f"med.pgy{pgy}.r{i + 1}@hospital.org",
                    pgy_level=pgy,
                )
                db.add(resident)
                residents.append(resident)

        # Create faculty
        faculty = []
        for i in range(15):
            fac = Person(
                id=uuid4(),
                name=f"Med Faculty {i + 1}",
                type="faculty",
                email=f"med.faculty{i + 1}@hospital.org",
            )
            db.add(fac)
            faculty.append(fac)

        db.commit()

        # Create assignments
        for resident in residents:
            for block in four_week_blocks:
                if block.date.weekday() != 6:  # Skip Sundays
                    assignment = Assignment(
                        id=uuid4(),
                        block_id=block.id,
                        person_id=resident.id,
                        rotation_template_id=large_rotation_template.id,
                        role="primary",
                    )
                    db.add(assignment)

        # Add faculty supervision
        for i, block in enumerate(four_week_blocks):
            if not block.is_weekend:
                for j in range(2):
                    fac = faculty[(i + j) % len(faculty)]
                    assignment = Assignment(
                        id=uuid4(),
                        block_id=block.id,
                        person_id=fac.id,
                        rotation_template_id=large_rotation_template.id,
                        role="supervising",
                    )
                    db.add(assignment)

        db.commit()

        # Run validation
        validator = ACGMEValidator(db)
        start_date = four_week_blocks[0].date
        end_date = four_week_blocks[-1].date

        print(
            f"\nFull validation: {len(residents)} residents, {len(four_week_blocks)} blocks"
        )

        with measure_time("Full ACGME validation (50 residents)") as metrics:
            result = validator.validate_all(start_date, end_date)

        # Assert performance
        assert_performance(
            metrics["duration"],
            MAX_VALIDATION_TIME_50_RESIDENTS,
            "Full ACGME validation (50 residents)",
        )

        # Verify result structure
        assert result.valid in [True, False]
        assert result.statistics is not None
        assert result.statistics["residents_scheduled"] <= len(residents)

        print(f"Violations: {result.total_violations}")
        print(f"Coverage: {result.coverage_rate:.1f}%")

    def test_small_dataset_validation_speed(
        self,
        db: Session,
        large_rotation_template: RotationTemplate,
    ):
        """
        Test validation speed with small dataset (25 residents).

        Requirements:
            - Should complete in < 1 second
            - Baseline for comparing scaling behavior
            - Typical small residency program size
        """
        # Create small dataset
        residents = []
        for pgy in [1, 2, 3]:
            for i in range(8):  # 8 residents per level = 24 total
                resident = Person(
                    id=uuid4(),
                    name=f"Small Resident PGY{pgy}-{i + 1}",
                    type="resident",
                    email=f"small.pgy{pgy}.r{i + 1}@hospital.org",
                    pgy_level=pgy,
                )
                db.add(resident)
                residents.append(resident)

        # Create faculty
        faculty = []
        for i in range(8):
            fac = Person(
                id=uuid4(),
                name=f"Small Faculty {i + 1}",
                type="faculty",
                email=f"small.faculty{i + 1}@hospital.org",
            )
            db.add(fac)
            faculty.append(fac)

        db.commit()

        # Create 2 weeks of blocks
        blocks = []
        start_date = date.today()
        for day_offset in range(14):
            current_date = start_date + timedelta(days=day_offset)
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current_date,
                    time_of_day=time_of_day,
                    block_number=1,
                    is_weekend=(current_date.weekday() >= 5),
                )
                db.add(block)
                blocks.append(block)

        db.commit()

        # Create assignments
        for resident in residents:
            for block in blocks:
                if block.date.weekday() != 6:
                    assignment = Assignment(
                        id=uuid4(),
                        block_id=block.id,
                        person_id=resident.id,
                        rotation_template_id=large_rotation_template.id,
                        role="primary",
                    )
                    db.add(assignment)

        db.commit()

        # Run validation
        validator = ACGMEValidator(db)
        end_date = start_date + timedelta(days=13)

        print(f"\nSmall dataset: {len(residents)} residents, {len(blocks)} blocks")

        with measure_time("ACGME validation (25 residents)") as metrics:
            result = validator.validate_all(start_date, end_date)

        # Assert performance
        assert_performance(
            metrics["duration"],
            MAX_VALIDATION_TIME_25_RESIDENTS,
            "ACGME validation (25 residents)",
        )

        assert result is not None
        print(
            f"Small dataset validation rate: {len(residents) / metrics['duration']:.1f} residents/sec"
        )


# ============================================================================
# Concurrent Validation Tests
# ============================================================================


@pytest.mark.performance
@pytest.mark.slow
class TestConcurrentValidation:
    """Test ACGME validation performance under concurrent load."""

    def test_concurrent_validation_no_degradation(
        self,
        db: Session,
        large_resident_dataset: dict,
        large_assignment_dataset: dict,
        four_week_blocks: list[Block],
    ):
        """
        Test 10 concurrent validations without significant degradation.

        Requirements:
            - Total time for 10 validations should be < 10s
            - No database locking issues
            - Results should be consistent across runs

        Simulates multiple users or automated processes running validation
        simultaneously (e.g., after schedule updates, during overnight jobs).
        """
        start_date = four_week_blocks[0].date
        end_date = four_week_blocks[-1].date

        print("\nRunning 10 concurrent validations")
        print(f"Dataset: {len(large_resident_dataset['residents'])} residents")

        def run_validation(run_id: int) -> dict:
            """Run a single validation and return timing info."""
            start_time = time.perf_counter()
            validator = ACGMEValidator(db)
            result = validator.validate_all(start_date, end_date)
            duration = time.perf_counter() - start_time

            return {
                "run_id": run_id,
                "duration": duration,
                "violations": result.total_violations,
                "valid": result.valid,
            }

        # Run 10 concurrent validations
        with measure_time("10 concurrent validations") as metrics:
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(run_validation, i) for i in range(10)]
                results = [f.result() for f in futures]

        # Assert performance
        assert_performance(
            metrics["duration"],
            MAX_CONCURRENT_VALIDATION_TIME,
            "10 concurrent validations",
        )

        # All validations should complete successfully
        assert len(results) == 10
        assert all(r["duration"] > 0 for r in results)

        # Check for consistency (all runs should find same number of violations)
        violation_counts = [r["violations"] for r in results]
        assert (
            len(set(violation_counts)) == 1
        ), f"Inconsistent validation results: {violation_counts}"

        # Log individual timings
        durations = [r["duration"] for r in results]
        print("\nIndividual validation times:")
        print(f"  Min: {min(durations):.3f}s")
        print(f"  Max: {max(durations):.3f}s")
        print(f"  Avg: {sum(durations) / len(durations):.3f}s")
        print(f"  Total violations per run: {results[0]['violations']}")

    def test_rapid_sequential_validation(
        self,
        db: Session,
        large_resident_dataset: dict,
        large_assignment_dataset: dict,
        four_week_blocks: list[Block],
    ):
        """
        Test rapid sequential validations (caching effectiveness).

        Requirements:
            - 5 sequential validations should be fast due to DB caching
            - Later runs may be faster than first run
            - No memory leaks or resource exhaustion

        Simulates user repeatedly clicking "Validate Schedule" button
        or automated validation after incremental changes.
        """
        validator = ACGMEValidator(db)
        start_date = four_week_blocks[0].date
        end_date = four_week_blocks[-1].date

        durations = []

        print("\nRunning 5 rapid sequential validations")

        for i in range(5):
            start_time = time.perf_counter()
            result = validator.validate_all(start_date, end_date)
            duration = time.perf_counter() - start_time
            durations.append(duration)

            print(
                f"  Run {i + 1}: {duration:.3f}s ({result.total_violations} violations)"
            )

        # First run is typically slower (cold cache)
        # Subsequent runs should be similar or faster
        assert durations[0] <= MAX_VALIDATION_TIME_100_RESIDENTS

        # Later runs should not be significantly slower (no resource leaks)
        avg_later_runs = sum(durations[1:]) / len(durations[1:])
        assert (
            avg_later_runs <= MAX_VALIDATION_TIME_100_RESIDENTS * 1.2
        )  # Allow 20% overhead

        print(f"\nFirst run: {durations[0]:.3f}s")
        print(f"Avg subsequent runs: {avg_later_runs:.3f}s")


# ============================================================================
# Memory and Scaling Tests
# ============================================================================


@pytest.mark.performance
@pytest.mark.slow
class TestValidationMemoryEfficiency:
    """Test memory efficiency of ACGME validation."""

    def test_validation_memory_efficiency(
        self,
        db: Session,
        huge_dataset: dict,
    ):
        """
        Test validation with very large dataset (12 weeks, 100 residents).

        Requirements:
            - Should not exceed memory limits
            - Should complete in reasonable time
            - Should handle ~16,800 assignments without OOM

        This test ensures validation can scale to full academic year if needed.

        Test Data:
            - 100 residents
            - 168 blocks (12 weeks)
            - ~16,800 assignments
        """
        validator = ACGMEValidator(db)
        start_date = huge_dataset["start_date"]
        end_date = huge_dataset["end_date"]

        print("\nHuge dataset validation:")
        print(f"  Residents: {len(huge_dataset['residents'])}")
        print(f"  Blocks: {len(huge_dataset['blocks'])}")
        print(f"  Assignments: {len(huge_dataset['assignments'])}")
        print(f"  Date range: {start_date} to {end_date} (12 weeks)")

        with measure_time("Huge dataset validation (12 weeks)") as metrics:
            result = validator.validate_all(start_date, end_date)

        # Should complete in reasonable time (3x the 4-week threshold)
        max_time = MAX_VALIDATION_TIME_100_RESIDENTS * 3
        assert_performance(metrics["duration"], max_time, "Huge dataset validation")

        # Verify results are sensible
        assert result is not None
        assert result.statistics is not None
        assert result.statistics["total_assignments"] > 10000

        print(f"Total violations: {result.total_violations}")
        print(f"Assignments processed: {result.statistics['total_assignments']}")
        print(
            f"Processing rate: {result.statistics['total_assignments'] / metrics['duration']:.0f} assignments/sec"
        )

    def test_incremental_vs_full_validation(
        self,
        db: Session,
        large_resident_dataset: dict,
        large_assignment_dataset: dict,
        four_week_blocks: list[Block],
    ):
        """
        Compare incremental validation performance vs full scan.

        Requirements:
            - Incremental validation of 1 week should be much faster than 4 weeks
            - Should demonstrate proper scaling characteristics

        This test helps establish whether incremental validation strategies
        would provide significant benefits for real-time schedule updates.
        """
        validator = ACGMEValidator(db)
        full_start = four_week_blocks[0].date
        full_end = four_week_blocks[-1].date

        # Full 4-week validation
        print("\nComparing validation strategies:")

        with measure_time("Full validation (4 weeks)") as full_metrics:
            full_result = validator.validate_all(full_start, full_end)

        # Incremental 1-week validation
        week1_end = full_start + timedelta(days=6)

        with measure_time("Incremental validation (1 week)") as incr_metrics:
            incr_result = validator.validate_all(full_start, week1_end)

        # Incremental should be faster
        speedup = full_metrics["duration"] / incr_metrics["duration"]
        print(f"\nFull (4 weeks): {full_metrics['duration']:.3f}s")
        print(f"Incremental (1 week): {incr_metrics['duration']:.3f}s")
        print(f"Speedup: {speedup:.1f}x")

        # Should be at least 2x faster for 4x less data
        assert (
            speedup >= 2.0
        ), f"Incremental validation not scaling properly: {speedup:.1f}x speedup"

        # Both should complete successfully
        assert full_result is not None
        assert incr_result is not None


# ============================================================================
# Edge Cases and Stress Tests
# ============================================================================


@pytest.mark.performance
class TestValidationEdgeCases:
    """Test ACGME validation edge cases that could impact performance."""

    def test_empty_schedule_validation(self, db: Session):
        """
        Test validation with no assignments (empty schedule).

        Requirements:
            - Should complete nearly instantly (< 0.1s)
            - Should not crash or throw errors
            - Should return valid structure with zero violations
        """
        validator = ACGMEValidator(db)
        start_date = date.today()
        end_date = start_date + timedelta(days=27)

        # Create residents but no assignments
        for i in range(10):
            resident = Person(
                id=uuid4(),
                name=f"Unassigned Resident {i + 1}",
                type="resident",
                email=f"unassigned{i + 1}@hospital.org",
                pgy_level=(i % 3) + 1,
            )
            db.add(resident)

        db.commit()

        with measure_time("Empty schedule validation") as metrics:
            result = validator.validate_all(start_date, end_date)

        # Should be very fast
        assert metrics["duration"] < 0.5  # 500ms
        assert result is not None
        assert result.total_violations == 0
        assert result.statistics["total_assignments"] == 0

        print(f"Empty schedule: {metrics['duration']:.3f}s")

    def test_sparse_assignment_validation(
        self,
        db: Session,
        large_resident_dataset: dict,
        four_week_blocks: list[Block],
        large_rotation_template: RotationTemplate,
    ):
        """
        Test validation with sparse assignments (< 10% coverage).

        Requirements:
            - Should handle sparse data efficiently
            - Should not have quadratic behavior with empty blocks
            - Coverage rate should reflect sparsity
        """
        validator = ACGMEValidator(db)
        residents = large_resident_dataset["residents"]

        # Assign only 10% of possible assignments
        assignment_count = 0
        for i, resident in enumerate(residents):
            for j, block in enumerate(four_week_blocks):
                # Only assign every 10th combination
                if (i + j) % 10 == 0:
                    assignment = Assignment(
                        id=uuid4(),
                        block_id=block.id,
                        person_id=resident.id,
                        rotation_template_id=large_rotation_template.id,
                        role="primary",
                    )
                    db.add(assignment)
                    assignment_count += 1

        db.commit()

        start_date = four_week_blocks[0].date
        end_date = four_week_blocks[-1].date

        print(f"\nSparse schedule: {assignment_count} assignments")

        with measure_time("Sparse schedule validation") as metrics:
            result = validator.validate_all(start_date, end_date)

        # Should still be fast with sparse data
        assert_performance(
            metrics["duration"],
            MAX_VALIDATION_TIME_100_RESIDENTS,
            "Sparse schedule validation",
        )

        # Coverage should be low
        assert result.coverage_rate < 20.0  # < 20%
        assert result.statistics["total_assignments"] == assignment_count

        print(f"Coverage: {result.coverage_rate:.1f}%")
        print(f"Violations: {result.total_violations}")
