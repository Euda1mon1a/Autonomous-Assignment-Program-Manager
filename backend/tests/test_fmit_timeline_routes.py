"""Comprehensive tests for FMIT Timeline API routes.

Tests all endpoints for faculty assignment timeline visualization:
- Academic year overview endpoint
- Individual faculty timeline endpoint
- Weekly view endpoint
- Gantt chart data endpoint
- Helper functions and calculations
- Error handling and edge cases
"""
from datetime import date, datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.fmit_timeline import (
    calculate_jains_fairness_index,
    calculate_workload_summary,
    get_academic_year_dates,
    get_week_bounds,
)
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


# ============================================================================
# Fixtures for FMIT Timeline Tests
# ============================================================================


@pytest.fixture
def sample_fmit_rotation(db: Session) -> RotationTemplate:
    """Create a sample FMIT rotation template."""
    template = RotationTemplate(
        id=uuid4(),
        name="FMIT Block",
        activity_type="clinic",
        abbreviation="FMIT",
        clinic_location="Main Campus",
        max_residents=2,
        supervision_required=True,
        max_supervision_ratio=2,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@pytest.fixture
def fmit_faculty_members(db: Session) -> list[Person]:
    """Create multiple faculty members for FMIT testing."""
    faculty = []
    names = ["Dr. Alice Johnson", "Dr. Bob Smith", "Dr. Carol White"]
    specialties = [["Sports Medicine"], ["Primary Care"], ["Pediatrics"]]

    for i, (name, spec) in enumerate(zip(names, specialties)):
        fac = Person(
            id=uuid4(),
            name=name,
            type="faculty",
            email=f"faculty{i+1}@test.org",
            performs_procedures=True,
            specialties=spec,
            primary_duty="FMIT Supervision"
        )
        db.add(fac)
        faculty.append(fac)

    db.commit()
    for f in faculty:
        db.refresh(f)
    return faculty


@pytest.fixture
def academic_year_blocks(db: Session) -> list[Block]:
    """Create blocks spanning an academic year for timeline testing."""
    blocks = []
    # Get academic year dates
    start_date, end_date = get_academic_year_dates()

    # Create blocks for every week (just one day per week to keep it manageable)
    current_date = start_date
    while current_date <= end_date:
        # Create AM and PM blocks for the first day of each week
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

        # Move to next week
        current_date += timedelta(days=7)

    db.commit()
    for b in blocks:
        db.refresh(b)
    return blocks


@pytest.fixture
def faculty_with_assignments(
    db: Session,
    fmit_faculty_members: list[Person],
    academic_year_blocks: list[Block],
    sample_fmit_rotation: RotationTemplate
) -> tuple[list[Person], list[Assignment]]:
    """Create faculty with varied FMIT assignments across the academic year."""
    assignments = []

    # Distribute assignments: faculty[0] gets 60%, faculty[1] gets 30%, faculty[2] gets 10%
    total_blocks = len(academic_year_blocks)
    for i, block in enumerate(academic_year_blocks):
        # Determine which faculty gets this block
        if i % 10 < 6:
            faculty_idx = 0
        elif i % 10 < 9:
            faculty_idx = 1
        else:
            faculty_idx = 2

        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=fmit_faculty_members[faculty_idx].id,
            rotation_template_id=sample_fmit_rotation.id,
            role="supervisor",
        )
        db.add(assignment)
        assignments.append(assignment)

    db.commit()
    for a in assignments:
        db.refresh(a)

    return fmit_faculty_members, assignments


# ============================================================================
# Helper Function Tests
# ============================================================================


class TestHelperFunctions:
    """Tests for timeline helper functions."""

    def test_get_academic_year_dates_july_onwards(self):
        """Test academic year calculation for dates from July onwards."""
        with patch('app.api.routes.fmit_timeline.date') as mock_date:
            mock_date.today.return_value = date(2024, 9, 15)
            start, end = get_academic_year_dates()

            assert start == date(2024, 7, 1)
            assert end == date(2025, 6, 30)

    def test_get_academic_year_dates_before_july(self):
        """Test academic year calculation for dates before July."""
        with patch('app.api.routes.fmit_timeline.date') as mock_date:
            mock_date.today.return_value = date(2024, 3, 15)
            start, end = get_academic_year_dates()

            assert start == date(2023, 7, 1)
            assert end == date(2024, 6, 30)

    def test_get_academic_year_dates_july_boundary(self):
        """Test academic year calculation on July 1st boundary."""
        with patch('app.api.routes.fmit_timeline.date') as mock_date:
            mock_date.today.return_value = date(2024, 7, 1)
            start, end = get_academic_year_dates()

            assert start == date(2024, 7, 1)
            assert end == date(2025, 6, 30)

    def test_get_week_bounds_monday(self):
        """Test week bounds when date is already Monday."""
        monday = date(2024, 1, 8)  # A Monday
        start, end = get_week_bounds(monday)

        assert start == monday
        assert end == date(2024, 1, 14)
        assert (end - start).days == 6

    def test_get_week_bounds_wednesday(self):
        """Test week bounds for a Wednesday (mid-week)."""
        wednesday = date(2024, 1, 10)
        start, end = get_week_bounds(wednesday)

        assert start == date(2024, 1, 8)  # Previous Monday
        assert end == date(2024, 1, 14)    # Following Sunday
        assert start.weekday() == 0  # Monday
        assert end.weekday() == 6    # Sunday

    def test_get_week_bounds_sunday(self):
        """Test week bounds when date is Sunday."""
        sunday = date(2024, 1, 14)
        start, end = get_week_bounds(sunday)

        assert start == date(2024, 1, 8)
        assert end == sunday
        assert start.weekday() == 0
        assert end.weekday() == 6

    def test_calculate_jains_fairness_index_perfect_fairness(self):
        """Test Jain's fairness index with perfectly equal distribution."""
        values = [5.0, 5.0, 5.0, 5.0]
        fairness = calculate_jains_fairness_index(values)

        assert fairness == 1.0  # Perfect fairness

    def test_calculate_jains_fairness_index_unequal_distribution(self):
        """Test Jain's fairness index with unequal distribution."""
        values = [1.0, 2.0, 3.0, 10.0]
        fairness = calculate_jains_fairness_index(values)

        assert 0.0 < fairness < 1.0  # Not perfectly fair
        assert fairness < 0.8  # Should be relatively unfair

    def test_calculate_jains_fairness_index_empty_list(self):
        """Test Jain's fairness index with empty list."""
        fairness = calculate_jains_fairness_index([])
        assert fairness == 1.0

    def test_calculate_jains_fairness_index_all_zeros(self):
        """Test Jain's fairness index when all values are zero."""
        values = [0.0, 0.0, 0.0]
        fairness = calculate_jains_fairness_index(values)
        assert fairness == 1.0

    def test_calculate_jains_fairness_index_single_value(self):
        """Test Jain's fairness index with single value."""
        fairness = calculate_jains_fairness_index([5.0])
        assert fairness == 1.0

    def test_calculate_workload_summary_at_target(self):
        """Test workload summary when at target."""
        from app.schemas.fmit_timeline import WeekAssignment

        weeks = [
            WeekAssignment(
                week_start=date(2024, 1, 1) + timedelta(weeks=i),
                week_end=date(2024, 1, 7) + timedelta(weeks=i),
                status="scheduled",
                assignment_count=5,
                total_blocks=10
            )
            for i in range(5)  # 5 weeks
        ]

        summary = calculate_workload_summary(weeks, target_weeks=5.0)

        assert summary.total_weeks == 5
        assert summary.target_weeks == 5.0
        assert summary.utilization_percent == 100.0
        assert summary.is_balanced is True
        assert summary.variance_from_target == 0.0

    def test_calculate_workload_summary_over_target(self):
        """Test workload summary when over target."""
        from app.schemas.fmit_timeline import WeekAssignment

        weeks = [
            WeekAssignment(
                week_start=date(2024, 1, 1) + timedelta(weeks=i),
                week_end=date(2024, 1, 7) + timedelta(weeks=i),
                status="scheduled",
                assignment_count=5,
                total_blocks=10
            )
            for i in range(7)  # 7 weeks
        ]

        summary = calculate_workload_summary(weeks, target_weeks=4.0)

        assert summary.total_weeks == 7
        assert summary.target_weeks == 4.0
        assert summary.utilization_percent == 175.0
        assert summary.is_balanced is False  # 3 weeks over = 75% variance
        assert summary.variance_from_target == 3.0

    def test_calculate_workload_summary_under_target(self):
        """Test workload summary when under target."""
        from app.schemas.fmit_timeline import WeekAssignment

        weeks = [
            WeekAssignment(
                week_start=date(2024, 1, 1) + timedelta(weeks=i),
                week_end=date(2024, 1, 7) + timedelta(weeks=i),
                status="scheduled",
                assignment_count=5,
                total_blocks=10
            )
            for i in range(3)  # 3 weeks
        ]

        summary = calculate_workload_summary(weeks, target_weeks=5.0)

        assert summary.total_weeks == 3
        assert summary.utilization_percent == 60.0
        assert summary.variance_from_target == -2.0

    def test_calculate_workload_summary_zero_target(self):
        """Test workload summary with zero target."""
        from app.schemas.fmit_timeline import WeekAssignment

        weeks = []
        summary = calculate_workload_summary(weeks, target_weeks=0.0)

        assert summary.total_weeks == 0
        assert summary.utilization_percent == 0.0
        assert summary.is_balanced is True
        assert summary.variance_from_target == 0.0


# ============================================================================
# Authentication Tests
# ============================================================================


class TestFMITTimelineAuthentication:
    """Tests for FMIT timeline API authentication requirements."""

    def test_academic_year_requires_authentication(self, client: TestClient):
        """Test that academic year endpoint requires authentication."""
        response = client.get("/api/fmit-timeline/academic-year")
        assert response.status_code == 401

    def test_faculty_timeline_requires_authentication(self, client: TestClient):
        """Test that faculty timeline endpoint requires authentication."""
        response = client.get(f"/api/fmit-timeline/faculty/{uuid4()}")
        assert response.status_code == 401

    def test_weekly_view_requires_authentication(self, client: TestClient):
        """Test that weekly view endpoint requires authentication."""
        response = client.get(f"/api/fmit-timeline/week/{date.today().isoformat()}")
        assert response.status_code == 401

    def test_gantt_data_requires_authentication(self, client: TestClient):
        """Test that Gantt data endpoint requires authentication."""
        response = client.get("/api/fmit-timeline/gantt-data")
        assert response.status_code == 401


# ============================================================================
# Academic Year Timeline Tests
# ============================================================================


class TestAcademicYearTimeline:
    """Tests for GET /api/fmit-timeline/academic-year endpoint."""

    def test_get_academic_year_timeline_empty(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test academic year timeline with no assignments."""
        response = client.get(
            "/api/fmit-timeline/academic-year",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "timeline_data" in data
        assert "aggregate_metrics" in data
        assert "start_date" in data
        assert "end_date" in data
        assert "generated_at" in data

        # Empty timeline
        assert isinstance(data["timeline_data"], list)
        assert len(data["timeline_data"]) == 0

        # Check aggregate metrics for empty case
        metrics = data["aggregate_metrics"]
        assert metrics["total_faculty"] == 0
        assert metrics["fairness_index"] == 1.0
        assert metrics["coverage_percentage"] == 0.0

    def test_get_academic_year_timeline_with_assignments(
        self,
        client: TestClient,
        auth_headers: dict,
        faculty_with_assignments: tuple[list[Person], list[Assignment]]
    ):
        """Test academic year timeline with actual assignments."""
        response = client.get(
            "/api/fmit-timeline/academic-year",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should have faculty timelines
        assert len(data["timeline_data"]) > 0

        # Check faculty timeline structure
        timeline = data["timeline_data"][0]
        assert "faculty_id" in timeline
        assert "faculty_name" in timeline
        assert "weeks_assigned" in timeline
        assert "workload" in timeline
        assert "department" in timeline
        assert "specialty" in timeline

        # Check workload structure
        workload = timeline["workload"]
        assert "total_weeks" in workload
        assert "target_weeks" in workload
        assert "utilization_percent" in workload
        assert "is_balanced" in workload
        assert "variance_from_target" in workload

        # Check aggregate metrics
        metrics = data["aggregate_metrics"]
        assert metrics["total_faculty"] > 0
        assert 0.0 <= metrics["fairness_index"] <= 1.0
        assert "load_distribution" in metrics

        # Check load distribution
        dist = metrics["load_distribution"]
        assert "mean" in dist
        assert "median" in dist
        assert "stdev" in dist
        assert "min" in dist
        assert "max" in dist

    def test_academic_year_date_range(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test that academic year returns correct date range."""
        response = client.get(
            "/api/fmit-timeline/academic-year",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        start = date.fromisoformat(data["start_date"])
        end = date.fromisoformat(data["end_date"])

        # Academic year should start July 1
        assert start.month == 7
        assert start.day == 1

        # And end June 30
        assert end.month == 6
        assert end.day == 30

        # Should span approximately one year
        days_span = (end - start).days
        assert 360 <= days_span <= 370

    def test_academic_year_fairness_with_unequal_load(
        self,
        client: TestClient,
        auth_headers: dict,
        faculty_with_assignments: tuple[list[Person], list[Assignment]]
    ):
        """Test fairness index calculation with unequal workload distribution."""
        response = client.get(
            "/api/fmit-timeline/academic-year",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        metrics = data["aggregate_metrics"]

        # With unequal distribution (60%, 30%, 10%), fairness should be less than 1.0
        assert metrics["fairness_index"] < 1.0

        # Distribution stats should reflect inequality
        dist = metrics["load_distribution"]
        assert dist["max"] > dist["mean"]
        assert dist["min"] < dist["mean"]
        assert dist["stdev"] > 0


# ============================================================================
***REMOVED*** Timeline Tests
# ============================================================================


class TestFacultyTimeline:
    """Tests for GET /api/fmit-timeline/faculty/{faculty_id} endpoint."""

    def test_get_faculty_timeline_not_found(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test faculty timeline with non-existent faculty ID."""
        fake_id = uuid4()
        response = client.get(
            f"/api/fmit-timeline/faculty/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_faculty_timeline_no_assignments(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_faculty: Person
    ):
        """Test faculty timeline for faculty with no assignments."""
        response = client.get(
            f"/api/fmit-timeline/faculty/{sample_faculty.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should have one timeline entry with empty weeks
        assert len(data["timeline_data"]) == 1
        timeline = data["timeline_data"][0]
        assert timeline["faculty_id"] == str(sample_faculty.id)
        assert timeline["faculty_name"] == sample_faculty.name
        assert len(timeline["weeks_assigned"]) == 0
        assert timeline["workload"]["total_weeks"] == 0

    def test_get_faculty_timeline_with_assignments(
        self,
        client: TestClient,
        auth_headers: dict,
        faculty_with_assignments: tuple[list[Person], list[Assignment]]
    ):
        """Test faculty timeline with assignments."""
        faculty_list, _ = faculty_with_assignments
        faculty = faculty_list[0]  ***REMOVED*** with most assignments

        response = client.get(
            f"/api/fmit-timeline/faculty/{faculty.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["timeline_data"]) == 1
        timeline = data["timeline_data"][0]

        # Should have weeks assigned
        assert len(timeline["weeks_assigned"]) > 0
        assert timeline["workload"]["total_weeks"] > 0

        # Check week assignment structure
        week = timeline["weeks_assigned"][0]
        assert "week_start" in week
        assert "week_end" in week
        assert "status" in week
        assert "assignment_count" in week
        assert "total_blocks" in week
        assert week["status"] in ["completed", "in_progress", "scheduled"]

    def test_get_faculty_timeline_custom_date_range(
        self,
        client: TestClient,
        auth_headers: dict,
        faculty_with_assignments: tuple[list[Person], list[Assignment]]
    ):
        """Test faculty timeline with custom date range."""
        faculty_list, _ = faculty_with_assignments
        faculty = faculty_list[0]

        start = date.today()
        end = start + timedelta(days=30)

        response = client.get(
            f"/api/fmit-timeline/faculty/{faculty.id}",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Check that date range matches
        assert data["start_date"] == start.isoformat()
        assert data["end_date"] == end.isoformat()

    def test_get_faculty_timeline_default_date_range(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_faculty: Person
    ):
        """Test that faculty timeline defaults to academic year."""
        response = client.get(
            f"/api/fmit-timeline/faculty/{sample_faculty.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should use academic year dates
        start = date.fromisoformat(data["start_date"])
        end = date.fromisoformat(data["end_date"])

        assert start.month == 7
        assert start.day == 1
        assert end.month == 6
        assert end.day == 30


# ============================================================================
# Weekly View Tests
# ============================================================================


class TestWeeklyView:
    """Tests for GET /api/fmit-timeline/week/{week_start} endpoint."""

    def test_get_weekly_view_empty_week(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test weekly view for a week with no assignments."""
        # Use a date far in the future with no data
        future_date = date.today() + timedelta(days=365)

        response = client.get(
            f"/api/fmit-timeline/week/{future_date.isoformat()}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Check structure
        assert "week_data" in data
        assert "adjacent_weeks" in data
        assert "generated_at" in data

        week = data["week_data"]
        assert "week_start" in week
        assert "week_end" in week
        assert "faculty_assignments" in week
        assert "total_slots" in week
        assert "filled_slots" in week
        assert "coverage_percentage" in week

        # Empty week
        assert len(week["faculty_assignments"]) == 0
        assert week["filled_slots"] == 0

    def test_get_weekly_view_normalizes_to_monday(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test that weekly view normalizes any date to Monday."""
        # Use a Wednesday
        wednesday = date(2024, 1, 10)
        expected_monday = date(2024, 1, 8)
        expected_sunday = date(2024, 1, 14)

        response = client.get(
            f"/api/fmit-timeline/week/{wednesday.isoformat()}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        week = data["week_data"]
        assert week["week_start"] == expected_monday.isoformat()
        assert week["week_end"] == expected_sunday.isoformat()

    def test_get_weekly_view_with_assignments(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        fmit_faculty_members: list[Person],
        sample_fmit_rotation: RotationTemplate
    ):
        """Test weekly view with actual assignments."""
        # Create blocks for this week
        today = date.today()
        week_start, week_end = get_week_bounds(today)

        blocks = []
        current = week_start
        while current <= week_end:
            for time in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current,
                    time_of_day=time,
                    block_number=1,
                    is_weekend=(current.weekday() >= 5),
                )
                db.add(block)
                blocks.append(block)
            current += timedelta(days=1)
        db.commit()

        # Create assignments
        for block in blocks[:5]:  # Assign some blocks
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=fmit_faculty_members[0].id,
                rotation_template_id=sample_fmit_rotation.id,
                role="supervisor",
            )
            db.add(assignment)
        db.commit()

        response = client.get(
            f"/api/fmit-timeline/week/{today.isoformat()}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        week = data["week_data"]
        assert week["filled_slots"] > 0
        assert len(week["faculty_assignments"]) > 0

        # Check faculty assignment structure
        fac_assign = week["faculty_assignments"][0]
        assert "faculty_id" in fac_assign
        assert "faculty_name" in fac_assign
        assert "assignments" in fac_assign

        # Check individual assignment structure
        if fac_assign["assignments"]:
            assign = fac_assign["assignments"][0]
            assert "date" in assign
            assert "time_of_day" in assign
            assert "block_id" in assign
            assert "assignment_id" in assign
            assert "role" in assign

    def test_get_weekly_view_coverage_calculation(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        fmit_faculty_members: list[Person],
        sample_fmit_rotation: RotationTemplate
    ):
        """Test weekly view coverage percentage calculation."""
        # Create exactly 10 blocks
        today = date.today()
        week_start, week_end = get_week_bounds(today)

        blocks = []
        for i in range(10):
            block = Block(
                id=uuid4(),
                date=week_start + timedelta(days=i % 7),
                time_of_day="AM" if i < 5 else "PM",
                block_number=1,
                is_weekend=False,
            )
            db.add(block)
            blocks.append(block)
        db.commit()

        # Assign 5 out of 10 blocks (50% coverage)
        for block in blocks[:5]:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=fmit_faculty_members[0].id,
                rotation_template_id=sample_fmit_rotation.id,
                role="supervisor",
            )
            db.add(assignment)
        db.commit()

        response = client.get(
            f"/api/fmit-timeline/week/{today.isoformat()}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        week = data["week_data"]
        assert week["total_slots"] == 10
        assert week["filled_slots"] == 5
        assert week["coverage_percentage"] == 50.0

    def test_get_weekly_view_adjacent_weeks(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test weekly view includes adjacent week information."""
        today = date.today()

        response = client.get(
            f"/api/fmit-timeline/week/{today.isoformat()}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        adjacent = data["adjacent_weeks"]
        assert "previous_week" in adjacent
        assert "next_week" in adjacent

        # Check previous week structure
        prev = adjacent["previous_week"]
        assert "week_start" in prev
        assert "assignment_count" in prev

        # Check next week structure
        next_week = adjacent["next_week"]
        assert "week_start" in next_week
        assert "assignment_count" in next_week


# ============================================================================
# Gantt Data Tests
# ============================================================================


class TestGanttData:
    """Tests for GET /api/fmit-timeline/gantt-data endpoint."""

    def test_get_gantt_data_empty(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test Gantt data with no assignments."""
        response = client.get(
            "/api/fmit-timeline/gantt-data",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Check structure
        assert "groups" in data
        assert "all_tasks" in data
        assert "date_range" in data
        assert "metadata" in data
        assert "generated_at" in data

        # Empty data
        assert len(data["groups"]) == 0
        assert len(data["all_tasks"]) == 0

        # Metadata should still be present
        assert "total_faculty" in data["metadata"]
        assert "total_tasks" in data["metadata"]
        assert data["metadata"]["total_faculty"] == 0
        assert data["metadata"]["total_tasks"] == 0

    def test_get_gantt_data_with_assignments(
        self,
        client: TestClient,
        auth_headers: dict,
        faculty_with_assignments: tuple[list[Person], list[Assignment]]
    ):
        """Test Gantt data with actual assignments."""
        response = client.get(
            "/api/fmit-timeline/gantt-data",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should have groups and tasks
        assert len(data["groups"]) > 0
        assert len(data["all_tasks"]) > 0

        # Check group structure
        group = data["groups"][0]
        assert "id" in group
        assert "name" in group
        assert "tasks" in group
        assert isinstance(group["tasks"], list)

        # Check task structure
        if data["all_tasks"]:
            task = data["all_tasks"][0]
            assert "id" in task
            assert "name" in task
            assert "start" in task
            assert "end" in task
            assert "progress" in task
            assert "dependencies" in task
            assert "resource" in task
            assert "type" in task
            assert "styles" in task

            # Progress should be 0-100
            assert 0 <= task["progress"] <= 100

    def test_get_gantt_data_custom_date_range(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test Gantt data with custom date range."""
        start = date(2024, 1, 1)
        end = date(2024, 3, 31)

        response = client.get(
            "/api/fmit-timeline/gantt-data",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Check date range
        date_range = data["date_range"]
        assert date_range["start"] == start.isoformat()
        assert date_range["end"] == end.isoformat()

    def test_get_gantt_data_faculty_filter(
        self,
        client: TestClient,
        auth_headers: dict,
        faculty_with_assignments: tuple[list[Person], list[Assignment]]
    ):
        """Test Gantt data filtered by specific faculty IDs."""
        faculty_list, _ = faculty_with_assignments
        target_faculty = faculty_list[0]

        response = client.get(
            "/api/fmit-timeline/gantt-data",
            params={"faculty_ids": [str(target_faculty.id)]},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should only have one group for the specified faculty
        if len(data["groups"]) > 0:
            assert len(data["groups"]) == 1
            assert data["groups"][0]["name"] == target_faculty.name

    def test_get_gantt_data_task_styling_by_workload(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_faculty: Person,
        sample_fmit_rotation: RotationTemplate
    ):
        """Test that Gantt tasks have different styles based on workload."""
        # Create a week with heavy workload (>8 blocks)
        today = date.today()
        week_start, _ = get_week_bounds(today)

        # Create 10 blocks in one week (heavy load)
        for i in range(10):
            block = Block(
                id=uuid4(),
                date=week_start + timedelta(days=i % 7),
                time_of_day="AM" if i < 5 else "PM",
                block_number=1,
                is_weekend=False,
            )
            db.add(block)
            db.flush()

            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_faculty.id,
                rotation_template_id=sample_fmit_rotation.id,
                role="supervisor",
            )
            db.add(assignment)
        db.commit()

        response = client.get(
            "/api/fmit-timeline/gantt-data",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Find tasks and check they have styling
        if data["all_tasks"]:
            task = data["all_tasks"][0]
            assert "styles" in task
            assert isinstance(task["styles"], dict)

            # Heavy workload should have red background
            if task["styles"]:
                assert "backgroundColor" in task["styles"]

    def test_get_gantt_data_progress_indicators(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_faculty: Person,
        sample_fmit_rotation: RotationTemplate
    ):
        """Test that Gantt tasks have correct progress based on status."""
        # Create past, present, and future assignments
        today = date.today()

        # Past week (should be completed = 100% progress)
        past_start = today - timedelta(days=14)
        past_end = past_start + timedelta(days=6)

        for i in range(2):
            block = Block(
                id=uuid4(),
                date=past_start + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
                is_weekend=False,
            )
            db.add(block)
            db.flush()

            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_faculty.id,
                rotation_template_id=sample_fmit_rotation.id,
                role="supervisor",
            )
            db.add(assignment)
        db.commit()

        response = client.get(
            "/api/fmit-timeline/gantt-data",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Check that tasks have progress values
        if data["all_tasks"]:
            task = data["all_tasks"][0]
            assert "progress" in task
            # Past tasks should have 100% progress
            if date.fromisoformat(task["end"]) < today:
                assert task["progress"] == 100.0


# ============================================================================
# Edge Cases and Error Handling Tests
# ============================================================================


class TestEdgeCasesAndErrors:
    """Tests for edge cases and error handling."""

    def test_timeline_with_single_faculty_perfect_fairness(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_faculty: Person,
        academic_year_blocks: list[Block],
        sample_fmit_rotation: RotationTemplate
    ):
        """Test that single faculty results in perfect fairness index."""
        # Assign all blocks to one faculty
        for block in academic_year_blocks[:10]:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_faculty.id,
                rotation_template_id=sample_fmit_rotation.id,
                role="supervisor",
            )
            db.add(assignment)
        db.commit()

        response = client.get(
            "/api/fmit-timeline/academic-year",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Single faculty should have perfect fairness
        assert data["aggregate_metrics"]["fairness_index"] == 1.0

    def test_timeline_week_status_determination(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_faculty: Person,
        sample_fmit_rotation: RotationTemplate
    ):
        """Test that week status is correctly determined (completed, in_progress, scheduled)."""
        today = date.today()

        # Create past, present, and future assignments
        dates = [
            today - timedelta(days=14),  # Past (completed)
            today,                        # Present (in_progress)
            today + timedelta(days=14),   # Future (scheduled)
        ]

        for test_date in dates:
            block = Block(
                id=uuid4(),
                date=test_date,
                time_of_day="AM",
                block_number=1,
                is_weekend=False,
            )
            db.add(block)
            db.flush()

            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_faculty.id,
                rotation_template_id=sample_fmit_rotation.id,
                role="supervisor",
            )
            db.add(assignment)
        db.commit()

        response = client.get(
            f"/api/fmit-timeline/faculty/{sample_faculty.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        timeline = data["timeline_data"][0]
        weeks = timeline["weeks_assigned"]

        # Should have different statuses
        statuses = {week["status"] for week in weeks}
        assert len(statuses) > 0

        # All statuses should be valid
        valid_statuses = {"completed", "in_progress", "scheduled"}
        assert all(status in valid_statuses for status in statuses)

    def test_invalid_uuid_format(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test that invalid UUID format is handled properly."""
        response = client.get(
            "/api/fmit-timeline/faculty/not-a-uuid",
            headers=auth_headers
        )

        # Should return 422 for validation error
        assert response.status_code == 422

    def test_coverage_percentage_with_no_blocks(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test coverage percentage calculation when there are no blocks."""
        # Use a date range with no blocks
        future_date = date.today() + timedelta(days=365)

        response = client.get(
            f"/api/fmit-timeline/week/{future_date.isoformat()}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        week = data["week_data"]
        assert week["total_slots"] == 0
        assert week["coverage_percentage"] == 0.0

    def test_timeline_generated_timestamp(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test that all timeline responses include generated_at timestamp."""
        endpoints = [
            "/api/fmit-timeline/academic-year",
            f"/api/fmit-timeline/week/{date.today().isoformat()}",
            "/api/fmit-timeline/gantt-data",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code == 200
            data = response.json()

            assert "generated_at" in data
            # Should be valid ISO format timestamp
            timestamp = data["generated_at"]
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
