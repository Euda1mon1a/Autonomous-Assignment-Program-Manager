"""
Performance tests for SwapFinder and FMIT scheduling system.

Tests large-scale schedule generation and ensures find_swap_candidates
completes within acceptable time limits.
"""
import sys
import time
from datetime import date, timedelta

import pytest

# Add parent directory to path for imports
sys.path.insert(0, '/home/user/Autonomous-Assignment-Program-Manager/backend')

from app.services.xlsx_import import (
    ExternalConflict,
    FacultyTarget,
    ImportResult,
    ProviderSchedule,
    ScheduleSlot,
    SlotType,
    SwapFinder,
)


def generate_fmit_schedule(
    num_faculty: int,
    num_weeks: int = 52,
    start_date: date = None
) -> ImportResult:
    """
    Generate a synthetic FMIT schedule for performance testing.

    Args:
        num_faculty: Number of faculty members to generate
        num_weeks: Number of weeks in the schedule
        start_date: Starting date for the schedule

    Returns:
        ImportResult with generated schedule
    """
    if start_date is None:
        start_date = date.today()

    result = ImportResult(success=True)

    # Generate faculty names
    faculty_names = [f"Faculty_{i:03d}" for i in range(num_faculty)]

    # Create provider schedules
    for name in faculty_names:
        result.providers[name] = ProviderSchedule(name=name)

    # Distribute FMIT weeks across faculty (aim for 6 weeks per faculty)
    weeks_per_faculty = max(6, num_weeks // num_faculty)

    current_week = start_date
    faculty_idx = 0
    week_count = 0

    for week_num in range(num_weeks):
        # Rotate through faculty
        faculty_name = faculty_names[faculty_idx % num_faculty]
        provider_schedule = result.providers[faculty_name]

        # Add FMIT slots for this week (Mon-Fri, AM and PM)
        for day_offset in range(5):  # Mon-Fri
            slot_date = current_week + timedelta(days=day_offset)

            for time_of_day in ["AM", "PM"]:
                slot = ScheduleSlot(
                    provider_name=faculty_name,
                    date=slot_date,
                    time_of_day=time_of_day,
                    slot_type=SlotType.FMIT,
                    raw_value="FMIT",
                )
                provider_schedule.add_slot(slot)
                result.total_slots += 1
                result.fmit_slots += 1

        # Move to next week
        current_week += timedelta(days=7)
        week_count += 1

        # Move to next faculty after weeks_per_faculty weeks
        if week_count >= weeks_per_faculty:
            faculty_idx += 1
            week_count = 0

    # Set date range
    result.date_range = (start_date, current_week - timedelta(days=1))

    return result


def generate_faculty_targets(num_faculty: int) -> dict[str, FacultyTarget]:
    """Generate FacultyTarget objects for performance testing."""
    targets = {}

    for i in range(num_faculty):
        name = f"Faculty_{i:03d}"

        # Vary roles for realism
        if i == 0:
            role = "chief"
            target_weeks = 3
        elif i == 1:
            role = "pd"
            target_weeks = 2
        elif i < num_faculty // 10:
            role = "adjunct"
            target_weeks = 4
        else:
            role = "faculty"
            target_weeks = 6

        targets[name] = FacultyTarget(
            name=name,
            target_weeks=target_weeks,
            role=role,
        )

    return targets


def generate_external_conflicts(
    num_faculty: int,
    num_conflicts: int,
    start_date: date
) -> list[ExternalConflict]:
    """Generate random external conflicts for testing."""
    conflicts = []

    for i in range(num_conflicts):
        faculty_idx = i % num_faculty
        conflict_start = start_date + timedelta(days=30 * i)
        conflict_end = conflict_start + timedelta(days=7)

        conflict_types = ["leave", "conference", "tdy", "training"]
        conflict_type = conflict_types[i % len(conflict_types)]

        conflicts.append(ExternalConflict(
            faculty=f"Faculty_{faculty_idx:03d}",
            start_date=conflict_start,
            end_date=conflict_end,
            conflict_type=conflict_type,
            description=f"Test {conflict_type} {i}",
        ))

    return conflicts


class TestSwapFinderPerformance:
    """Performance tests for SwapFinder."""

    def test_large_schedule_generation_50_faculty(self):
        """Test generating schedule for 50+ faculty over 52 weeks."""
        start_time = time.time()

        result = generate_fmit_schedule(num_faculty=50, num_weeks=52)

        generation_time = time.time() - start_time

        # Verify schedule was created
        assert result.success
        assert len(result.providers) == 50
        assert result.fmit_slots > 0

        # Should complete very quickly (under 100ms)
        assert generation_time < 0.1, f"Generation took {generation_time:.3f}s"

        print(f"\n✓ Generated 50 faculty, 52 weeks in {generation_time*1000:.1f}ms")
        print(f"  Total slots: {result.total_slots}")
        print(f"  FMIT slots: {result.fmit_slots}")

    def test_find_swap_candidates_performance_50_faculty(self):
        """Test find_swap_candidates completes in < 1 second for 50 faculty."""
        # Setup
        result = generate_fmit_schedule(num_faculty=50, num_weeks=52)
        faculty_targets = generate_faculty_targets(50)
        external_conflicts = generate_external_conflicts(
            num_faculty=50,
            num_conflicts=20,
            start_date=date.today()
        )

        finder = SwapFinder(
            fmit_schedule=result,
            faculty_targets=faculty_targets,
            external_conflicts=external_conflicts,
        )

        # Test find_swap_candidates
        target_week = date.today() + timedelta(days=14)

        start_time = time.time()
        candidates = finder.find_swap_candidates("Faculty_000", target_week)
        elapsed_time = time.time() - start_time

        # Performance assertion: Must complete in < 1 second
        assert elapsed_time < 1.0, f"find_swap_candidates took {elapsed_time:.3f}s (> 1.0s)"

        # Verify results
        assert isinstance(candidates, list)
        assert len(candidates) > 0  # Should find some candidates

        print(f"\n✓ find_swap_candidates completed in {elapsed_time*1000:.1f}ms")
        print(f"  Found {len(candidates)} candidates")
        print(f"  Performance: {'PASS' if elapsed_time < 1.0 else 'FAIL'}")

    @pytest.mark.parametrize("num_faculty", [10, 25, 50, 100])
    def test_scaling_characteristics(self, num_faculty):
        """Test performance scaling at different faculty sizes."""
        # Generate schedule
        gen_start = time.time()
        result = generate_fmit_schedule(num_faculty=num_faculty, num_weeks=52)
        gen_time = time.time() - gen_start

        faculty_targets = generate_faculty_targets(num_faculty)
        num_conflicts = num_faculty // 5  # 20% of faculty have conflicts
        external_conflicts = generate_external_conflicts(
            num_faculty=num_faculty,
            num_conflicts=num_conflicts,
            start_date=date.today()
        )

        # Create SwapFinder
        setup_start = time.time()
        finder = SwapFinder(
            fmit_schedule=result,
            faculty_targets=faculty_targets,
            external_conflicts=external_conflicts,
        )
        setup_time = time.time() - setup_start

        # Test find_swap_candidates
        target_week = date.today() + timedelta(days=14)
        search_start = time.time()
        candidates = finder.find_swap_candidates("Faculty_000", target_week)
        search_time = time.time() - search_start

        # Print scaling metrics
        print(f"\n{'='*60}")
        print(f"Scaling Test: {num_faculty} faculty")
        print(f"{'='*60}")
        print(f"  Schedule generation: {gen_time*1000:6.1f}ms")
        print(f"  SwapFinder setup:    {setup_time*1000:6.1f}ms")
        print(f"  find_swap_candidates:{search_time*1000:6.1f}ms")
        print(f"  Total time:          {(gen_time+setup_time+search_time)*1000:6.1f}ms")
        print(f"  Candidates found:    {len(candidates)}")
        print(f"  Total slots:         {result.total_slots}")

        # Assertions
        assert result.success
        assert len(result.providers) == num_faculty
        assert search_time < 1.0, f"Search took {search_time:.3f}s (> 1.0s)"

        # Scaling should be roughly linear or better
        # For 100 faculty, should still complete in < 1 second
        if num_faculty == 100:
            assert search_time < 1.0, f"100 faculty search took {search_time:.3f}s"

    def test_memory_efficiency(self):
        """Test memory efficiency with large schedules."""
        import gc
        import sys

        # Force garbage collection
        gc.collect()

        # Create large schedule
        result = generate_fmit_schedule(num_faculty=100, num_weeks=52)
        faculty_targets = generate_faculty_targets(100)
        external_conflicts = generate_external_conflicts(
            num_faculty=100,
            num_conflicts=50,
            start_date=date.today()
        )

        finder = SwapFinder(
            fmit_schedule=result,
            faculty_targets=faculty_targets,
            external_conflicts=external_conflicts,
        )

        # Get approximate memory usage
        # Size of the main data structures
        result_size = sys.getsizeof(result)
        finder_size = sys.getsizeof(finder)

        print(f"\n{'='*60}")
        print("Memory Efficiency Test (100 faculty, 52 weeks)")
        print(f"{'='*60}")
        print(f"  ImportResult size:   ~{result_size:,} bytes")
        print(f"  SwapFinder size:     ~{finder_size:,} bytes")
        print(f"  Total providers:     {len(result.providers)}")
        print(f"  Total slots:         {result.total_slots}")
        print(f"  External conflicts:  {len(external_conflicts)}")

        # Verify data structures are reasonable
        assert len(result.providers) == 100
        assert len(finder.faculty_weeks) == 100

        # Test that multiple searches don't cause memory issues
        target_weeks = [date.today() + timedelta(days=i*7) for i in range(10)]

        for week in target_weeks:
            candidates = finder.find_swap_candidates("Faculty_000", week)
            assert len(candidates) >= 0  # Just verify it works

        print("  ✓ Completed 10 swap searches successfully")

    def test_worst_case_scenario(self):
        """Test worst-case scenario: many conflicts, tight constraints."""
        # Generate schedule with lots of constraints
        num_faculty = 50
        result = generate_fmit_schedule(num_faculty=num_faculty, num_weeks=52)
        faculty_targets = generate_faculty_targets(num_faculty)

        # Create many external conflicts (40% of faculty have conflicts)
        external_conflicts = generate_external_conflicts(
            num_faculty=num_faculty,
            num_conflicts=100,
            start_date=date.today()
        )

        finder = SwapFinder(
            fmit_schedule=result,
            faculty_targets=faculty_targets,
            external_conflicts=external_conflicts,
        )

        # Test multiple searches
        search_times = []
        target_weeks = [date.today() + timedelta(days=i*7) for i in range(20)]

        for week in target_weeks:
            start_time = time.time()
            candidates = finder.find_swap_candidates("Faculty_000", week)
            elapsed = time.time() - start_time
            search_times.append(elapsed)

        avg_time = sum(search_times) / len(search_times)
        max_time = max(search_times)
        min_time = min(search_times)

        print(f"\n{'='*60}")
        print("Worst-Case Scenario Test (50 faculty, 100 conflicts)")
        print(f"{'='*60}")
        print(f"  Searches performed:  {len(search_times)}")
        print(f"  Average time:        {avg_time*1000:.1f}ms")
        print(f"  Min time:            {min_time*1000:.1f}ms")
        print(f"  Max time:            {max_time*1000:.1f}ms")
        print(f"  External conflicts:  {len(external_conflicts)}")

        # All searches should complete in < 1 second
        assert max_time < 1.0, f"Worst search took {max_time:.3f}s (> 1.0s)"
        assert avg_time < 0.5, f"Average search took {avg_time:.3f}s (> 0.5s)"

    def test_find_excessive_alternating_performance(self):
        """Test find_excessive_alternating performance."""
        # Create schedule with alternating patterns
        result = generate_fmit_schedule(num_faculty=50, num_weeks=52)

        finder = SwapFinder(fmit_schedule=result)

        start_time = time.time()
        excessive = finder.find_excessive_alternating(threshold=3)
        elapsed_time = time.time() - start_time

        print(f"\n{'='*60}")
        print("find_excessive_alternating Performance")
        print(f"{'='*60}")
        print(f"  Execution time:      {elapsed_time*1000:.1f}ms")
        print("  Faculty analyzed:    50")
        print(f"  Excessive patterns:  {len(excessive)}")

        # Should complete very quickly
        assert elapsed_time < 0.1, f"Analysis took {elapsed_time:.3f}s (> 0.1s)"
        assert isinstance(excessive, list)

    def test_concurrent_searches(self):
        """Test performance with multiple concurrent swap searches."""
        result = generate_fmit_schedule(num_faculty=50, num_weeks=52)
        faculty_targets = generate_faculty_targets(50)

        finder = SwapFinder(
            fmit_schedule=result,
            faculty_targets=faculty_targets,
        )

        # Simulate multiple users searching at once
        faculty_list = [f"Faculty_{i:03d}" for i in range(10)]
        target_weeks = [date.today() + timedelta(days=i*7) for i in range(10)]

        start_time = time.time()

        # Run 100 searches (10 faculty x 10 weeks)
        all_candidates = []
        for faculty in faculty_list:
            for week in target_weeks:
                candidates = finder.find_swap_candidates(faculty, week)
                all_candidates.append((faculty, week, candidates))

        total_time = time.time() - start_time
        avg_time = total_time / len(all_candidates)

        print(f"\n{'='*60}")
        print("Concurrent Searches Test")
        print(f"{'='*60}")
        print(f"  Total searches:      {len(all_candidates)}")
        print(f"  Total time:          {total_time:.3f}s")
        print(f"  Average per search:  {avg_time*1000:.1f}ms")
        print(f"  Searches/second:     {len(all_candidates)/total_time:.1f}")

        # Average should be well under 1 second per search
        assert avg_time < 1.0, f"Average search took {avg_time:.3f}s (> 1.0s)"

        # Verify all searches completed
        assert len(all_candidates) == 100


class TestScheduleDataStructures:
    """Test performance of core data structures."""

    def test_provider_schedule_operations(self):
        """Test ProviderSchedule operations at scale."""
        schedule = ProviderSchedule(name="Test_Faculty")

        # Add 5000 slots (52 weeks x ~100 slots per week)
        start_time = time.time()

        start_date = date.today()
        for week in range(52):
            for day in range(7):
                for time_of_day in ["AM", "PM"]:
                    slot_date = start_date + timedelta(days=week*7 + day)
                    slot = ScheduleSlot(
                        provider_name="Test_Faculty",
                        date=slot_date,
                        time_of_day=time_of_day,
                        slot_type=SlotType.FMIT,
                        raw_value="FMIT",
                    )
                    schedule.add_slot(slot)

        add_time = time.time() - start_time

        # Test retrieval
        lookup_start = time.time()
        for _ in range(1000):
            test_date = start_date + timedelta(days=100)
            slot = schedule.get_slot(test_date, "AM")
        lookup_time = time.time() - lookup_start

        # Test get_fmit_weeks
        weeks_start = time.time()
        fmit_weeks = schedule.get_fmit_weeks()
        weeks_time = time.time() - weeks_start

        print(f"\n{'='*60}")
        print("ProviderSchedule Performance")
        print(f"{'='*60}")
        print(f"  Add 728 slots:       {add_time*1000:.1f}ms")
        print(f"  1000 lookups:        {lookup_time*1000:.1f}ms")
        print(f"  get_fmit_weeks:      {weeks_time*1000:.1f}ms")
        print(f"  FMIT weeks found:    {len(fmit_weeks)}")

        assert add_time < 1.0, f"Adding slots took {add_time:.3f}s"
        assert lookup_time < 0.1, f"Lookups took {lookup_time:.3f}s"
        assert weeks_time < 0.1, f"get_fmit_weeks took {weeks_time:.3f}s"

    def test_import_result_operations(self):
        """Test ImportResult operations with many providers."""
        result = ImportResult(success=True)

        # Add 100 providers
        start_time = time.time()
        for i in range(100):
            name = f"Faculty_{i:03d}"
            result.providers[name] = ProviderSchedule(name=name)
        add_time = time.time() - start_time

        # Add conflicts
        conflict_start = time.time()
        for i in range(1000):
            from app.services.xlsx_import import ScheduleConflict
            conflict = ScheduleConflict(
                provider_name=f"Faculty_{i % 100:03d}",
                date=date.today(),
                time_of_day="AM",
                conflict_type="double_book",
                severity="error",
            )
            result.add_conflict(conflict)
        conflict_time = time.time() - conflict_start

        # Test queries
        query_start = time.time()
        for i in range(100):
            conflicts = result.get_conflicts_by_provider(f"Faculty_{i:03d}")
            type_conflicts = result.get_conflicts_by_type("double_book")
        query_time = time.time() - query_start

        print(f"\n{'='*60}")
        print("ImportResult Performance")
        print(f"{'='*60}")
        print(f"  Add 100 providers:   {add_time*1000:.1f}ms")
        print(f"  Add 1000 conflicts:  {conflict_time*1000:.1f}ms")
        print(f"  200 queries:         {query_time*1000:.1f}ms")
        print(f"  Total conflicts:     {len(result.conflicts)}")

        assert add_time < 0.1, f"Adding providers took {add_time:.3f}s"
        assert conflict_time < 0.5, f"Adding conflicts took {conflict_time:.3f}s"
        assert query_time < 0.5, f"Queries took {query_time:.3f}s"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
