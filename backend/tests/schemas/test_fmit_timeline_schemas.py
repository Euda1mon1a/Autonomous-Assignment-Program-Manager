"""Tests for FMIT timeline schemas (defaults, nested models, Gantt data)."""

from datetime import date, datetime
from uuid import uuid4

from app.schemas.fmit_timeline import (
    WeekAssignment,
    WorkloadSummary,
    FacultyTimeline,
    LoadDistribution,
    AggregateMetrics,
    TimelineResponse,
    GanttTask,
    GanttGroup,
    GanttDataResponse,
    WeeklyView,
    WeeklyViewResponse,
)


class TestWeekAssignment:
    def test_valid(self):
        r = WeekAssignment(
            week_start=date(2026, 3, 2),
            week_end=date(2026, 3, 8),
            status="scheduled",
        )
        assert r.assignment_count == 0
        assert r.total_blocks == 0

    def test_with_counts(self):
        r = WeekAssignment(
            week_start=date(2026, 3, 2),
            week_end=date(2026, 3, 8),
            status="completed",
            assignment_count=3,
            total_blocks=2,
        )
        assert r.assignment_count == 3


class TestWorkloadSummary:
    def test_defaults(self):
        r = WorkloadSummary()
        assert r.total_weeks == 0
        assert r.target_weeks == 0.0
        assert r.utilization_percent == 0.0
        assert r.is_balanced is True
        assert r.variance_from_target == 0.0

    def test_unbalanced(self):
        r = WorkloadSummary(
            total_weeks=15,
            target_weeks=10.0,
            utilization_percent=150.0,
            is_balanced=False,
            variance_from_target=5.0,
        )
        assert r.is_balanced is False
        assert r.variance_from_target == 5.0


class TestFacultyTimeline:
    def _make_workload(self):
        return WorkloadSummary(total_weeks=10, target_weeks=10.0)

    def test_valid_minimal(self):
        r = FacultyTimeline(
            faculty_id=uuid4(),
            faculty_name="Dr. Smith",
            workload=self._make_workload(),
        )
        assert r.weeks_assigned == []
        assert r.department is None
        assert r.specialty is None

    def test_with_assignments(self):
        wa = WeekAssignment(
            week_start=date(2026, 3, 2),
            week_end=date(2026, 3, 8),
            status="scheduled",
        )
        r = FacultyTimeline(
            faculty_id=uuid4(),
            faculty_name="Dr. Jones",
            weeks_assigned=[wa],
            workload=self._make_workload(),
            department="FM",
            specialty="Sports Medicine",
        )
        assert len(r.weeks_assigned) == 1
        assert r.department == "FM"


class TestLoadDistribution:
    def test_defaults(self):
        r = LoadDistribution()
        assert r.mean == 0.0
        assert r.median == 0.0
        assert r.stdev == 0.0
        assert r.min == 0.0
        assert r.max == 0.0

    def test_with_values(self):
        r = LoadDistribution(mean=8.5, median=8.0, stdev=2.1, min=4.0, max=15.0)
        assert r.mean == 8.5


class TestAggregateMetrics:
    def test_valid(self):
        dist = LoadDistribution(mean=8.0)
        r = AggregateMetrics(load_distribution=dist)
        assert r.fairness_index == 0.0
        assert r.total_faculty == 0
        assert r.total_weeks_scheduled == 0
        assert r.coverage_percentage == 0.0

    def test_full(self):
        dist = LoadDistribution(mean=8.0, median=8.0, stdev=1.0, min=6.0, max=10.0)
        r = AggregateMetrics(
            fairness_index=0.95,
            load_distribution=dist,
            total_faculty=20,
            total_weeks_scheduled=160,
            coverage_percentage=98.5,
        )
        assert r.fairness_index == 0.95


class TestTimelineResponse:
    def test_valid_minimal(self):
        dist = LoadDistribution()
        metrics = AggregateMetrics(load_distribution=dist)
        r = TimelineResponse(
            aggregate_metrics=metrics,
            start_date=date(2025, 7, 1),
            end_date=date(2026, 6, 30),
            generated_at=datetime(2026, 3, 1),
        )
        assert r.timeline_data == []


class TestGanttTask:
    def test_valid_minimal(self):
        r = GanttTask(
            id="task-1",
            name="Dr. Smith",
            start=date(2026, 3, 1),
            end=date(2026, 3, 28),
            resource="Dr. Smith",
        )
        assert r.progress == 0.0
        assert r.dependencies == []
        assert r.type == "task"
        assert r.styles == {}

    def test_full(self):
        r = GanttTask(
            id="task-2",
            name="Dr. Jones",
            start=date(2026, 3, 1),
            end=date(2026, 3, 14),
            progress=50.0,
            dependencies=["task-1"],
            resource="Dr. Jones",
            type="milestone",
            styles={"color": "blue"},
        )
        assert r.progress == 50.0
        assert len(r.dependencies) == 1
        assert r.type == "milestone"


class TestGanttGroup:
    def test_valid_minimal(self):
        r = GanttGroup(id="grp-1", name="Faculty A")
        assert r.tasks == []

    def test_with_tasks(self):
        task = GanttTask(
            id="t1",
            name="T",
            start=date(2026, 3, 1),
            end=date(2026, 3, 7),
            resource="R",
        )
        r = GanttGroup(id="grp-1", name="Faculty A", tasks=[task])
        assert len(r.tasks) == 1


class TestGanttDataResponse:
    def test_valid_minimal(self):
        r = GanttDataResponse(
            date_range={"start": "2026-03-01", "end": "2026-06-30"},
            generated_at=datetime(2026, 3, 1),
        )
        assert r.groups == []
        assert r.all_tasks == []
        assert r.metadata == {}


class TestWeeklyView:
    def test_valid(self):
        r = WeeklyView(
            week_start=date(2026, 3, 2),
            week_end=date(2026, 3, 8),
        )
        assert r.faculty_assignments == []
        assert r.total_slots == 0
        assert r.filled_slots == 0
        assert r.coverage_percentage == 0.0


class TestWeeklyViewResponse:
    def test_valid(self):
        week = WeeklyView(week_start=date(2026, 3, 2), week_end=date(2026, 3, 8))
        r = WeeklyViewResponse(
            week_data=week,
            generated_at=datetime(2026, 3, 1),
        )
        assert r.adjacent_weeks == {}
