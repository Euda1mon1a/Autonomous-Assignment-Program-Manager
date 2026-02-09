"""Tests for ConflictVisualizer (pure data transformation, no DB required)."""

import asyncio
from datetime import date
from uuid import uuid4

import pytest

from app.scheduling.conflicts.types import (
    Conflict,
    ConflictCategory,
    ConflictSeverity,
    ConflictType,
)
from app.scheduling.conflicts.visualizer import ConflictVisualizer


# ==================== Helpers ====================


def _make_conflict(
    start: str = "2024-06-01",
    end: str = "2024-06-03",
    severity: ConflictSeverity = ConflictSeverity.HIGH,
    category: ConflictCategory = ConflictCategory.ACGME_VIOLATION,
    conflict_type: ConflictType = ConflictType.EIGHTY_HOUR_VIOLATION,
    affected_people: list | None = None,
    **overrides,
) -> Conflict:
    """Build a valid Conflict with sensible defaults."""
    data = {
        "conflict_id": overrides.pop("conflict_id", f"conf_{uuid4().hex[:8]}"),
        "category": category,
        "conflict_type": conflict_type,
        "severity": severity,
        "title": overrides.pop("title", "Test Conflict"),
        "description": "Test description",
        "start_date": start,
        "end_date": end,
        "impact_score": overrides.pop("impact_score", 0.8),
        "urgency_score": overrides.pop("urgency_score", 0.7),
        "complexity_score": overrides.pop("complexity_score", 0.5),
        "affected_people": affected_people or [],
    }
    data.update(overrides)
    return Conflict(**data)


def _run(coro):
    """Run async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ==================== Severity Helper Tests ====================


class TestSeverityToLevel:
    """Test _severity_to_level discrete mapping."""

    def test_zero_returns_0(self):
        viz = ConflictVisualizer()
        assert viz._severity_to_level(0.0) == 0

    def test_low_returns_1(self):
        viz = ConflictVisualizer()
        assert viz._severity_to_level(0.25) == 1

    def test_medium_returns_2(self):
        viz = ConflictVisualizer()
        assert viz._severity_to_level(0.5) == 2

    def test_high_returns_3(self):
        viz = ConflictVisualizer()
        assert viz._severity_to_level(0.75) == 3

    def test_critical_returns_4(self):
        viz = ConflictVisualizer()
        assert viz._severity_to_level(1.0) == 4

    def test_boundary_just_above_025(self):
        viz = ConflictVisualizer()
        assert viz._severity_to_level(0.26) == 2

    def test_boundary_just_above_075(self):
        viz = ConflictVisualizer()
        assert viz._severity_to_level(0.76) == 4


class TestSeverityColor:
    """Test _get_severity_color hex codes."""

    def test_critical_is_red(self):
        viz = ConflictVisualizer()
        assert viz._get_severity_color(ConflictSeverity.CRITICAL) == "#DC2626"

    def test_high_is_orange(self):
        viz = ConflictVisualizer()
        assert viz._get_severity_color(ConflictSeverity.HIGH) == "#EA580C"

    def test_medium_is_amber(self):
        viz = ConflictVisualizer()
        assert viz._get_severity_color(ConflictSeverity.MEDIUM) == "#F59E0B"

    def test_low_is_light_amber(self):
        viz = ConflictVisualizer()
        assert viz._get_severity_color(ConflictSeverity.LOW) == "#FCD34D"


class TestSeverityScores:
    """Test SEVERITY_SCORES class attribute."""

    def test_all_four_severities_mapped(self):
        assert len(ConflictVisualizer.SEVERITY_SCORES) == 4

    def test_critical_is_1(self):
        assert ConflictVisualizer.SEVERITY_SCORES[ConflictSeverity.CRITICAL] == 1.0

    def test_low_is_025(self):
        assert ConflictVisualizer.SEVERITY_SCORES[ConflictSeverity.LOW] == 0.25


# ==================== Timeline Tests ====================


class TestGenerateTimeline:
    """Test generate_timeline async method."""

    def test_empty_conflicts(self):
        viz = ConflictVisualizer()
        timeline = _run(viz.generate_timeline([]))
        assert timeline.timeline_entries == []
        assert timeline.severity_by_date == {}

    def test_empty_with_custom_dates(self):
        viz = ConflictVisualizer()
        timeline = _run(
            viz.generate_timeline(
                [],
                start_date=date(2024, 6, 1),
                end_date=date(2024, 6, 3),
            )
        )
        assert timeline.start_date == date(2024, 6, 1)
        assert timeline.end_date == date(2024, 6, 3)

    def test_single_conflict_creates_entries(self):
        viz = ConflictVisualizer()
        c = _make_conflict(start="2024-06-01", end="2024-06-03")
        timeline = _run(viz.generate_timeline([c]))
        # 3 days: June 1, 2, 3
        assert len(timeline.timeline_entries) == 3
        assert all(e["conflict_count"] == 1 for e in timeline.timeline_entries)

    def test_severity_by_date_populated(self):
        viz = ConflictVisualizer()
        c = _make_conflict(
            start="2024-06-01",
            end="2024-06-01",
            severity=ConflictSeverity.CRITICAL,
        )
        timeline = _run(viz.generate_timeline([c]))
        assert timeline.severity_by_date["2024-06-01"] == 1.0

    def test_count_by_date_populated(self):
        viz = ConflictVisualizer()
        c = _make_conflict(start="2024-06-01", end="2024-06-01")
        timeline = _run(viz.generate_timeline([c]))
        assert timeline.count_by_date["2024-06-01"] == 1

    def test_overlapping_conflicts_max_severity(self):
        viz = ConflictVisualizer()
        c_low = _make_conflict(
            start="2024-06-01",
            end="2024-06-01",
            severity=ConflictSeverity.LOW,
        )
        c_crit = _make_conflict(
            start="2024-06-01",
            end="2024-06-01",
            severity=ConflictSeverity.CRITICAL,
        )
        timeline = _run(viz.generate_timeline([c_low, c_crit]))
        # Max severity should be critical (1.0)
        assert timeline.severity_by_date["2024-06-01"] == 1.0
        assert timeline.count_by_date["2024-06-01"] == 2

    def test_date_range_auto_detected(self):
        viz = ConflictVisualizer()
        c = _make_conflict(start="2024-06-05", end="2024-06-10")
        timeline = _run(viz.generate_timeline([c]))
        assert timeline.start_date == date(2024, 6, 5)
        assert timeline.end_date == date(2024, 6, 10)

    def test_custom_date_range_clips(self):
        viz = ConflictVisualizer()
        c = _make_conflict(start="2024-06-01", end="2024-06-10")
        timeline = _run(
            viz.generate_timeline(
                [c],
                start_date=date(2024, 6, 3),
                end_date=date(2024, 6, 5),
            )
        )
        assert len(timeline.timeline_entries) == 3  # June 3, 4, 5

    def test_conflicts_by_person_populated(self):
        viz = ConflictVisualizer()
        person_id = uuid4()
        c = _make_conflict(
            start="2024-06-01",
            end="2024-06-02",
            affected_people=[person_id],
        )
        timeline = _run(viz.generate_timeline([c]))
        pid_str = str(person_id)
        assert pid_str in timeline.conflicts_by_person
        assert "2024-06-01" in timeline.conflicts_by_person[pid_str]
        assert "2024-06-02" in timeline.conflicts_by_person[pid_str]

    def test_category_timeline_generated(self):
        viz = ConflictVisualizer()
        c = _make_conflict(start="2024-06-01", end="2024-06-07")
        timeline = _run(viz.generate_timeline([c]))
        assert len(timeline.category_timeline) > 0
        entry = timeline.category_timeline[0]
        assert "week_start" in entry
        assert "week_end" in entry
        assert "total_conflicts" in entry
        assert "by_category" in entry

    def test_timeline_entry_structure(self):
        viz = ConflictVisualizer()
        c = _make_conflict(
            start="2024-06-01",
            end="2024-06-01",
            conflict_type=ConflictType.EIGHTY_HOUR_VIOLATION,
        )
        timeline = _run(viz.generate_timeline([c]))
        entry = timeline.timeline_entries[0]
        assert entry["date"] == "2024-06-01"
        assert entry["conflict_count"] == 1
        assert entry["severity_score"] > 0
        assert len(entry["conflicts"]) == 1
        assert entry["conflicts"][0]["type"] == "eighty_hour_violation"


# ==================== Heatmap Tests ====================


class TestGenerateHeatmapData:
    """Test generate_heatmap_data async method."""

    def test_empty_conflicts(self):
        viz = ConflictVisualizer()
        result = _run(viz.generate_heatmap_data([]))
        assert result["data"] == []
        assert result["min_value"] == 0.0
        assert result["max_value"] == 0.0

    def test_single_conflict(self):
        viz = ConflictVisualizer()
        c = _make_conflict(
            start="2024-06-01",
            end="2024-06-02",
            severity=ConflictSeverity.HIGH,
        )
        result = _run(viz.generate_heatmap_data([c]))
        assert len(result["data"]) == 2
        assert result["max_value"] == 0.75  # HIGH severity score

    def test_data_sorted_by_date(self):
        viz = ConflictVisualizer()
        c = _make_conflict(start="2024-06-01", end="2024-06-03")
        result = _run(viz.generate_heatmap_data([c]))
        dates = [d["date"] for d in result["data"]]
        assert dates == sorted(dates)

    def test_heatmap_level_field(self):
        viz = ConflictVisualizer()
        c = _make_conflict(
            start="2024-06-01",
            end="2024-06-01",
            severity=ConflictSeverity.CRITICAL,
        )
        result = _run(viz.generate_heatmap_data([c]))
        assert result["data"][0]["level"] == 4  # CRITICAL -> level 4

    def test_overlapping_uses_max_severity(self):
        viz = ConflictVisualizer()
        c_low = _make_conflict(
            start="2024-06-01",
            end="2024-06-01",
            severity=ConflictSeverity.LOW,
        )
        c_high = _make_conflict(
            start="2024-06-01",
            end="2024-06-01",
            severity=ConflictSeverity.HIGH,
        )
        result = _run(viz.generate_heatmap_data([c_low, c_high]))
        assert result["data"][0]["value"] == 0.75  # max(LOW=0.25, HIGH=0.75)

    def test_color_scale_is_red(self):
        viz = ConflictVisualizer()
        c = _make_conflict()
        result = _run(viz.generate_heatmap_data([c]))
        assert result["color_scale"] == "red"


# ==================== Gantt Tests ====================


class TestGenerateGanttData:
    """Test generate_gantt_data async method."""

    def test_empty_conflicts(self):
        viz = ConflictVisualizer()
        result = _run(viz.generate_gantt_data([]))
        assert result == []

    def test_single_conflict_entry(self):
        viz = ConflictVisualizer()
        c = _make_conflict(
            start="2024-06-01",
            end="2024-06-05",
            severity=ConflictSeverity.CRITICAL,
            conflict_id="test-001",
            title="Hour Violation",
            impact_score=0.9,
            urgency_score=0.8,
        )
        result = _run(viz.generate_gantt_data([c]))
        assert len(result) == 1
        entry = result[0]
        assert entry["id"] == "test-001"
        assert entry["title"] == "Hour Violation"
        assert entry["start"] == "2024-06-01"
        assert entry["end"] == "2024-06-05"
        assert entry["severity"] == "critical"
        assert entry["impact_score"] == 0.9
        assert entry["color"] == "#DC2626"

    def test_sorted_by_start_date(self):
        viz = ConflictVisualizer()
        c1 = _make_conflict(start="2024-06-05", end="2024-06-06")
        c2 = _make_conflict(start="2024-06-01", end="2024-06-02")
        result = _run(viz.generate_gantt_data([c1, c2]))
        assert result[0]["start"] == "2024-06-01"
        assert result[1]["start"] == "2024-06-05"

    def test_same_start_sorted_by_severity_desc(self):
        viz = ConflictVisualizer()
        c_low = _make_conflict(
            start="2024-06-01",
            end="2024-06-02",
            severity=ConflictSeverity.LOW,
        )
        c_crit = _make_conflict(
            start="2024-06-01",
            end="2024-06-02",
            severity=ConflictSeverity.CRITICAL,
        )
        result = _run(viz.generate_gantt_data([c_low, c_crit]))
        assert result[0]["severity"] == "critical"
        assert result[1]["severity"] == "low"

    def test_affected_people_count(self):
        viz = ConflictVisualizer()
        c = _make_conflict(affected_people=[uuid4(), uuid4()])
        result = _run(viz.generate_gantt_data([c]))
        assert result[0]["affected_people_count"] == 2


# ==================== Distribution Chart Tests ====================


class TestGenerateDistributionChart:
    """Test generate_distribution_chart async method."""

    def test_empty_conflicts(self):
        viz = ConflictVisualizer()
        result = _run(viz.generate_distribution_chart([]))
        assert result["total"] == 0
        assert result["by_severity"] == {}
        assert result["by_category"] == {}

    def test_counts_by_severity(self):
        viz = ConflictVisualizer()
        conflicts = [
            _make_conflict(severity=ConflictSeverity.CRITICAL),
            _make_conflict(severity=ConflictSeverity.CRITICAL),
            _make_conflict(severity=ConflictSeverity.LOW),
        ]
        result = _run(viz.generate_distribution_chart(conflicts))
        assert result["by_severity"]["critical"] == 2
        assert result["by_severity"]["low"] == 1

    def test_counts_by_category(self):
        viz = ConflictVisualizer()
        conflicts = [
            _make_conflict(category=ConflictCategory.ACGME_VIOLATION),
            _make_conflict(category=ConflictCategory.TIME_OVERLAP),
        ]
        result = _run(viz.generate_distribution_chart(conflicts))
        assert result["by_category"]["acgme_violation"] == 1
        assert result["by_category"]["time_overlap"] == 1

    def test_total_count(self):
        viz = ConflictVisualizer()
        conflicts = [_make_conflict() for _ in range(5)]
        result = _run(viz.generate_distribution_chart(conflicts))
        assert result["total"] == 5

    def test_severity_chart_has_color(self):
        viz = ConflictVisualizer()
        conflicts = [_make_conflict(severity=ConflictSeverity.HIGH)]
        result = _run(viz.generate_distribution_chart(conflicts))
        assert len(result["severity_chart"]) == 1
        assert result["severity_chart"][0]["color"] == "#EA580C"
        assert result["severity_chart"][0]["count"] == 1


# ==================== Person Impact Chart Tests ====================


class TestGeneratePersonImpactChart:
    """Test generate_person_impact_chart async method."""

    def test_empty_conflicts(self):
        viz = ConflictVisualizer()
        result = _run(viz.generate_person_impact_chart([]))
        assert result == []

    def test_single_person_single_conflict(self):
        viz = ConflictVisualizer()
        pid = uuid4()
        c = _make_conflict(
            severity=ConflictSeverity.HIGH,
            affected_people=[pid],
        )
        result = _run(viz.generate_person_impact_chart([c]))
        assert len(result) == 1
        assert result[0]["person_id"] == str(pid)
        assert result[0]["conflict_count"] == 1
        assert result[0]["average_severity"] == 0.75
        assert result[0]["max_severity"] == 0.75

    def test_multiple_conflicts_per_person(self):
        viz = ConflictVisualizer()
        pid = uuid4()
        c1 = _make_conflict(
            severity=ConflictSeverity.CRITICAL,
            affected_people=[pid],
        )
        c2 = _make_conflict(
            severity=ConflictSeverity.LOW,
            affected_people=[pid],
        )
        result = _run(viz.generate_person_impact_chart([c1, c2]))
        assert len(result) == 1
        assert result[0]["conflict_count"] == 2
        # avg of 1.0 + 0.25 = 0.625
        assert result[0]["average_severity"] == 0.62  # rounded to 2 dp
        assert result[0]["max_severity"] == 1.0

    def test_sorted_by_conflict_count_desc(self):
        viz = ConflictVisualizer()
        pid_a = uuid4()
        pid_b = uuid4()
        c1 = _make_conflict(affected_people=[pid_a])
        c2 = _make_conflict(affected_people=[pid_a])
        c3 = _make_conflict(affected_people=[pid_b])
        result = _run(viz.generate_person_impact_chart([c1, c2, c3]))
        assert result[0]["person_id"] == str(pid_a)
        assert result[0]["conflict_count"] == 2
        assert result[1]["person_id"] == str(pid_b)
        assert result[1]["conflict_count"] == 1

    def test_no_affected_people_returns_empty(self):
        viz = ConflictVisualizer()
        c = _make_conflict(affected_people=[])
        result = _run(viz.generate_person_impact_chart([c]))
        assert result == []


# ==================== Category Timeline Tests ====================


class TestCategoryTimeline:
    """Test _generate_category_timeline weekly aggregation."""

    def test_single_week(self):
        viz = ConflictVisualizer()
        # Mon Jun 3 to Sun Jun 9
        c = _make_conflict(start="2024-06-03", end="2024-06-07")
        result = viz._generate_category_timeline(
            [c],
            date(2024, 6, 3),
            date(2024, 6, 9),
        )
        assert len(result) >= 1
        assert result[0]["total_conflicts"] == 1

    def test_multi_week_spans(self):
        viz = ConflictVisualizer()
        c = _make_conflict(start="2024-06-01", end="2024-06-14")
        result = viz._generate_category_timeline(
            [c],
            date(2024, 6, 1),
            date(2024, 6, 14),
        )
        assert len(result) >= 2
        # Conflict spans both weeks
        assert all(w["total_conflicts"] >= 1 for w in result)

    def test_category_counts(self):
        viz = ConflictVisualizer()
        c1 = _make_conflict(
            start="2024-06-03",
            end="2024-06-05",
            category=ConflictCategory.ACGME_VIOLATION,
        )
        c2 = _make_conflict(
            start="2024-06-04",
            end="2024-06-06",
            category=ConflictCategory.TIME_OVERLAP,
        )
        result = viz._generate_category_timeline(
            [c1, c2],
            date(2024, 6, 3),
            date(2024, 6, 9),
        )
        week = result[0]
        assert week["by_category"]["acgme_violation"] == 1
        assert week["by_category"]["time_overlap"] == 1

    def test_week_entries_have_required_keys(self):
        viz = ConflictVisualizer()
        c = _make_conflict(start="2024-06-03", end="2024-06-05")
        result = viz._generate_category_timeline(
            [c],
            date(2024, 6, 3),
            date(2024, 6, 9),
        )
        entry = result[0]
        assert "week_start" in entry
        assert "week_end" in entry
        assert "total_conflicts" in entry
        assert "by_category" in entry
