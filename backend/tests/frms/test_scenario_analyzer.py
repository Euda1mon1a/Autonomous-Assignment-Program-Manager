"""Tests for what-if scenario analysis (no DB)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest

from app.frms.scenario_analyzer import (
    FatigueImpactReport,
    ScenarioAnalyzer,
    WhatIfScenario,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _person(name: str = "Dr. Smith") -> dict:
    return {"id": str(uuid4()), "name": name}


def _block(
    d: date, block_id: str | None = None, rotation_type: str = "general"
) -> dict:
    return {
        "id": block_id or str(uuid4()),
        "date": d,
        "rotation_type": rotation_type,
    }


def _assignment(person_id: str, block_id: str, d: date, aid: str | None = None) -> dict:
    return {
        "id": aid or str(uuid4()),
        "person_id": person_id,
        "block_id": block_id,
        "rotation_type": "general",
        "date": d,
    }


# ---------------------------------------------------------------------------
# WhatIfScenario — construction
# ---------------------------------------------------------------------------


class TestWhatIfScenarioConstruction:
    def test_basic_fields(self):
        s = WhatIfScenario(
            scenario_id="s1",
            name="Test",
            description="Test scenario",
            changes=[],
        )
        assert s.scenario_id == "s1"
        assert s.name == "Test"
        assert s.description == "Test scenario"
        assert s.changes == []

    def test_created_at_auto(self):
        before = datetime.now()
        s = WhatIfScenario(scenario_id="s1", name="T", description="D", changes=[])
        after = datetime.now()
        assert before <= s.created_at <= after

    def test_changes_stored(self):
        changes = [{"action": "add", "person_id": "p1", "block_id": "b1"}]
        s = WhatIfScenario(scenario_id="s2", name="T", description="D", changes=changes)
        assert len(s.changes) == 1
        assert s.changes[0]["action"] == "add"


# ---------------------------------------------------------------------------
# WhatIfScenario — to_dict
# ---------------------------------------------------------------------------


class TestWhatIfScenarioToDict:
    def test_keys(self):
        s = WhatIfScenario(scenario_id="s1", name="T", description="D", changes=[])
        d = s.to_dict()
        assert set(d.keys()) == {
            "scenario_id",
            "name",
            "description",
            "changes",
            "created_at",
        }

    def test_scenario_id(self):
        s = WhatIfScenario(scenario_id="abc", name="T", description="D", changes=[])
        assert s.to_dict()["scenario_id"] == "abc"

    def test_created_at_is_iso(self):
        s = WhatIfScenario(scenario_id="s1", name="T", description="D", changes=[])
        d = s.to_dict()
        # Should be parseable as ISO datetime
        datetime.fromisoformat(d["created_at"])

    def test_changes_preserved(self):
        changes = [{"action": "remove", "assignment_id": "a1"}]
        s = WhatIfScenario(scenario_id="s1", name="T", description="D", changes=changes)
        assert s.to_dict()["changes"] == changes


# ---------------------------------------------------------------------------
# FatigueImpactReport — construction
# ---------------------------------------------------------------------------


class TestFatigueImpactReportConstruction:
    def test_basic_fields(self):
        now = datetime.now()
        r = FatigueImpactReport(
            scenario_id="s1",
            scenario_name="Test",
            analysis_time=now,
        )
        assert r.scenario_id == "s1"
        assert r.scenario_name == "Test"
        assert r.analysis_time == now

    def test_defaults_are_empty(self):
        r = FatigueImpactReport(
            scenario_id="s1",
            scenario_name="Test",
            analysis_time=datetime.now(),
        )
        assert r.baseline_metrics == {}
        assert r.proposed_metrics == {}
        assert r.impact_summary == {}
        assert r.person_impacts == []
        assert r.recommendations == []
        assert r.visualization_data == {}

    def test_custom_metrics(self):
        r = FatigueImpactReport(
            scenario_id="s1",
            scenario_name="Test",
            analysis_time=datetime.now(),
            baseline_metrics={"avg": 80},
            proposed_metrics={"avg": 75},
        )
        assert r.baseline_metrics["avg"] == 80
        assert r.proposed_metrics["avg"] == 75


# ---------------------------------------------------------------------------
# FatigueImpactReport — to_dict
# ---------------------------------------------------------------------------


class TestFatigueImpactReportToDict:
    def test_keys(self):
        r = FatigueImpactReport(
            scenario_id="s1",
            scenario_name="Test",
            analysis_time=datetime.now(),
        )
        d = r.to_dict()
        expected_keys = {
            "scenario_id",
            "scenario_name",
            "analysis_time",
            "baseline_metrics",
            "proposed_metrics",
            "impact_summary",
            "person_impacts",
            "recommendations",
            "visualization_data",
        }
        assert set(d.keys()) == expected_keys

    def test_analysis_time_is_iso(self):
        r = FatigueImpactReport(
            scenario_id="s1",
            scenario_name="T",
            analysis_time=datetime(2026, 1, 15, 10, 30),
        )
        d = r.to_dict()
        datetime.fromisoformat(d["analysis_time"])

    def test_preserves_all_data(self):
        r = FatigueImpactReport(
            scenario_id="s1",
            scenario_name="T",
            analysis_time=datetime.now(),
            recommendations=["Do X", "Do Y"],
            person_impacts=[{"person_id": "p1", "change": 1}],
        )
        d = r.to_dict()
        assert len(d["recommendations"]) == 2
        assert len(d["person_impacts"]) == 1


# ---------------------------------------------------------------------------
# ScenarioAnalyzer — construction
# ---------------------------------------------------------------------------


class TestScenarioAnalyzerInit:
    def test_has_model(self):
        analyzer = ScenarioAnalyzer()
        assert analyzer.model is not None

    def test_has_predictor(self):
        analyzer = ScenarioAnalyzer()
        assert analyzer.predictor is not None


# ---------------------------------------------------------------------------
# ScenarioAnalyzer._apply_changes — add
# ---------------------------------------------------------------------------


class TestApplyChangesAdd:
    def setup_method(self):
        self.analyzer = ScenarioAnalyzer()

    def test_add_increases_count(self):
        blocks = [_block(date(2026, 1, 5), block_id="b1")]
        result = self.analyzer._apply_changes(
            assignments=[],
            changes=[{"action": "add", "person_id": "p1", "block_id": "b1"}],
            blocks=blocks,
        )
        assert len(result) == 1

    def test_add_preserves_existing(self):
        existing = [_assignment("p1", "b0", date(2026, 1, 1))]
        blocks = [_block(date(2026, 1, 5), block_id="b1")]
        result = self.analyzer._apply_changes(
            assignments=existing,
            changes=[{"action": "add", "person_id": "p2", "block_id": "b1"}],
            blocks=blocks,
        )
        assert len(result) == 2

    def test_add_sets_person_id(self):
        blocks = [_block(date(2026, 1, 5), block_id="b1")]
        result = self.analyzer._apply_changes(
            assignments=[],
            changes=[{"action": "add", "person_id": "p1", "block_id": "b1"}],
            blocks=blocks,
        )
        assert result[0]["person_id"] == "p1"

    def test_add_sets_block_id(self):
        blocks = [_block(date(2026, 1, 5), block_id="b1")]
        result = self.analyzer._apply_changes(
            assignments=[],
            changes=[{"action": "add", "person_id": "p1", "block_id": "b1"}],
            blocks=blocks,
        )
        assert result[0]["block_id"] == "b1"

    def test_add_looks_up_date_from_block(self):
        blocks = [_block(date(2026, 1, 5), block_id="b1")]
        result = self.analyzer._apply_changes(
            assignments=[],
            changes=[{"action": "add", "person_id": "p1", "block_id": "b1"}],
            blocks=blocks,
        )
        assert result[0]["date"] == date(2026, 1, 5)

    def test_add_custom_rotation_type(self):
        blocks = [_block(date(2026, 1, 5), block_id="b1")]
        result = self.analyzer._apply_changes(
            assignments=[],
            changes=[
                {
                    "action": "add",
                    "person_id": "p1",
                    "block_id": "b1",
                    "rotation_type": "night",
                }
            ],
            blocks=blocks,
        )
        assert result[0]["rotation_type"] == "night"

    def test_add_default_rotation_type(self):
        blocks = [_block(date(2026, 1, 5), block_id="b1")]
        result = self.analyzer._apply_changes(
            assignments=[],
            changes=[{"action": "add", "person_id": "p1", "block_id": "b1"}],
            blocks=blocks,
        )
        assert result[0]["rotation_type"] == "general"


# ---------------------------------------------------------------------------
# ScenarioAnalyzer._apply_changes — remove
# ---------------------------------------------------------------------------


class TestApplyChangesRemove:
    def setup_method(self):
        self.analyzer = ScenarioAnalyzer()

    def test_remove_by_id(self):
        assignments = [_assignment("p1", "b1", date(2026, 1, 1), aid="a1")]
        result = self.analyzer._apply_changes(
            assignments=assignments,
            changes=[{"action": "remove", "assignment_id": "a1"}],
            blocks=[],
        )
        assert len(result) == 0

    def test_remove_preserves_others(self):
        assignments = [
            _assignment("p1", "b1", date(2026, 1, 1), aid="a1"),
            _assignment("p2", "b2", date(2026, 1, 2), aid="a2"),
        ]
        result = self.analyzer._apply_changes(
            assignments=assignments,
            changes=[{"action": "remove", "assignment_id": "a1"}],
            blocks=[],
        )
        assert len(result) == 1
        assert result[0]["id"] == "a2"

    def test_remove_nonexistent_no_error(self):
        assignments = [_assignment("p1", "b1", date(2026, 1, 1), aid="a1")]
        result = self.analyzer._apply_changes(
            assignments=assignments,
            changes=[{"action": "remove", "assignment_id": "nonexistent"}],
            blocks=[],
        )
        assert len(result) == 1


# ---------------------------------------------------------------------------
# ScenarioAnalyzer._apply_changes — move
# ---------------------------------------------------------------------------


class TestApplyChangesMove:
    def setup_method(self):
        self.analyzer = ScenarioAnalyzer()

    def test_move_changes_block_id(self):
        assignments = [_assignment("p1", "b1", date(2026, 1, 1), aid="a1")]
        blocks = [_block(date(2026, 1, 10), block_id="b2")]
        result = self.analyzer._apply_changes(
            assignments=assignments,
            changes=[{"action": "move", "assignment_id": "a1", "new_block_id": "b2"}],
            blocks=blocks,
        )
        assert result[0]["block_id"] == "b2"

    def test_move_updates_date(self):
        assignments = [_assignment("p1", "b1", date(2026, 1, 1), aid="a1")]
        blocks = [_block(date(2026, 1, 10), block_id="b2")]
        result = self.analyzer._apply_changes(
            assignments=assignments,
            changes=[{"action": "move", "assignment_id": "a1", "new_block_id": "b2"}],
            blocks=blocks,
        )
        assert result[0]["date"] == date(2026, 1, 10)

    def test_move_preserves_person_id(self):
        assignments = [_assignment("p1", "b1", date(2026, 1, 1), aid="a1")]
        blocks = [_block(date(2026, 1, 10), block_id="b2")]
        result = self.analyzer._apply_changes(
            assignments=assignments,
            changes=[{"action": "move", "assignment_id": "a1", "new_block_id": "b2"}],
            blocks=blocks,
        )
        assert result[0]["person_id"] == "p1"


# ---------------------------------------------------------------------------
# ScenarioAnalyzer._apply_changes — swap
# ---------------------------------------------------------------------------


class TestApplyChangesSwap:
    def setup_method(self):
        self.analyzer = ScenarioAnalyzer()

    def test_swap_exchanges_person_ids(self):
        assignments = [
            _assignment("p1", "b1", date(2026, 1, 1), aid="a1"),
            _assignment("p2", "b2", date(2026, 1, 2), aid="a2"),
        ]
        result = self.analyzer._apply_changes(
            assignments=assignments,
            changes=[
                {"action": "swap", "assignment1_id": "a1", "assignment2_id": "a2"}
            ],
            blocks=[],
        )
        a1 = next(a for a in result if a["id"] == "a1")
        a2 = next(a for a in result if a["id"] == "a2")
        assert a1["person_id"] == "p2"
        assert a2["person_id"] == "p1"

    def test_swap_preserves_blocks(self):
        assignments = [
            _assignment("p1", "b1", date(2026, 1, 1), aid="a1"),
            _assignment("p2", "b2", date(2026, 1, 2), aid="a2"),
        ]
        result = self.analyzer._apply_changes(
            assignments=assignments,
            changes=[
                {"action": "swap", "assignment1_id": "a1", "assignment2_id": "a2"}
            ],
            blocks=[],
        )
        a1 = next(a for a in result if a["id"] == "a1")
        a2 = next(a for a in result if a["id"] == "a2")
        assert a1["block_id"] == "b1"
        assert a2["block_id"] == "b2"

    def test_swap_nonexistent_no_error(self):
        assignments = [_assignment("p1", "b1", date(2026, 1, 1), aid="a1")]
        result = self.analyzer._apply_changes(
            assignments=assignments,
            changes=[
                {"action": "swap", "assignment1_id": "a1", "assignment2_id": "missing"}
            ],
            blocks=[],
        )
        # Should not crash
        assert len(result) == 1


# ---------------------------------------------------------------------------
# ScenarioAnalyzer._get_block_date
# ---------------------------------------------------------------------------


class TestGetBlockDate:
    def setup_method(self):
        self.analyzer = ScenarioAnalyzer()

    def test_found_by_id(self):
        blocks = [_block(date(2026, 3, 15), block_id="b1")]
        result = self.analyzer._get_block_date(blocks, "b1")
        assert result == date(2026, 3, 15)

    def test_not_found_returns_none(self):
        blocks = [_block(date(2026, 3, 15), block_id="b1")]
        result = self.analyzer._get_block_date(blocks, "missing")
        assert result is None

    def test_string_date_parsed(self):
        blocks = [{"id": "b1", "date": "2026-06-01"}]
        result = self.analyzer._get_block_date(blocks, "b1")
        assert result == date(2026, 6, 1)

    def test_date_object_returned(self):
        blocks = [{"id": "b1", "date": date(2026, 6, 1)}]
        result = self.analyzer._get_block_date(blocks, "b1")
        assert isinstance(result, date)

    def test_empty_blocks(self):
        result = self.analyzer._get_block_date([], "b1")
        assert result is None


# ---------------------------------------------------------------------------
# ScenarioAnalyzer._calculate_impact
# ---------------------------------------------------------------------------


class TestCalculateImpact:
    def setup_method(self):
        self.analyzer = ScenarioAnalyzer()

    def test_improvement(self):
        baseline = {
            "avg_fatigue_score": 20,
            "avg_effectiveness": 80,
            "min_effectiveness": 70,
            "highest_risk_level": "moderate",
        }
        proposed = {
            "avg_fatigue_score": 10,
            "avg_effectiveness": 90,
            "min_effectiveness": 80,
            "highest_risk_level": "low",
        }
        result = self.analyzer._calculate_impact(baseline, proposed)
        assert result["overall_change"] == "IMPROVEMENT"

    def test_degradation(self):
        baseline = {
            "avg_fatigue_score": 10,
            "avg_effectiveness": 90,
            "min_effectiveness": 80,
            "highest_risk_level": "low",
        }
        proposed = {
            "avg_fatigue_score": 20,
            "avg_effectiveness": 80,
            "min_effectiveness": 70,
            "highest_risk_level": "moderate",
        }
        result = self.analyzer._calculate_impact(baseline, proposed)
        assert result["overall_change"] == "DEGRADATION"

    def test_no_change(self):
        metrics = {
            "avg_fatigue_score": 15,
            "avg_effectiveness": 85,
            "min_effectiveness": 75,
            "highest_risk_level": "low",
        }
        result = self.analyzer._calculate_impact(metrics, metrics)
        assert result["overall_change"] == "NO_CHANGE"

    def test_fatigue_change_calculated(self):
        baseline = {
            "avg_fatigue_score": 20,
            "avg_effectiveness": 80,
            "min_effectiveness": 70,
            "highest_risk_level": "low",
        }
        proposed = {
            "avg_fatigue_score": 15,
            "avg_effectiveness": 85,
            "min_effectiveness": 75,
            "highest_risk_level": "low",
        }
        result = self.analyzer._calculate_impact(baseline, proposed)
        assert result["fatigue_change"] == -5

    def test_effectiveness_change_calculated(self):
        baseline = {
            "avg_fatigue_score": 20,
            "avg_effectiveness": 80,
            "min_effectiveness": 70,
            "highest_risk_level": "low",
        }
        proposed = {
            "avg_fatigue_score": 15,
            "avg_effectiveness": 85,
            "min_effectiveness": 75,
            "highest_risk_level": "low",
        }
        result = self.analyzer._calculate_impact(baseline, proposed)
        assert result["effectiveness_change"] == 5

    def test_min_effectiveness_change(self):
        baseline = {
            "avg_fatigue_score": 20,
            "avg_effectiveness": 80,
            "min_effectiveness": 70,
            "highest_risk_level": "low",
        }
        proposed = {
            "avg_fatigue_score": 15,
            "avg_effectiveness": 85,
            "min_effectiveness": 65,
            "highest_risk_level": "low",
        }
        result = self.analyzer._calculate_impact(baseline, proposed)
        assert result["min_effectiveness_change"] == -5

    def test_risk_level_change_string(self):
        baseline = {
            "avg_fatigue_score": 10,
            "highest_risk_level": "low",
            "avg_effectiveness": 90,
            "min_effectiveness": 80,
        }
        proposed = {
            "avg_fatigue_score": 20,
            "highest_risk_level": "high",
            "avg_effectiveness": 80,
            "min_effectiveness": 70,
        }
        result = self.analyzer._calculate_impact(baseline, proposed)
        assert "low" in result["risk_level_change"]
        assert "high" in result["risk_level_change"]

    def test_empty_dicts_use_defaults(self):
        result = self.analyzer._calculate_impact({}, {})
        assert result["fatigue_change"] == 0
        assert result["effectiveness_change"] == 0
        assert result["overall_change"] == "NO_CHANGE"


# ---------------------------------------------------------------------------
# ScenarioAnalyzer._calculate_person_impacts
# ---------------------------------------------------------------------------


class TestCalculatePersonImpacts:
    def setup_method(self):
        self.analyzer = ScenarioAnalyzer()

    def test_unchanged_person(self):
        p = _person("Dr. A")
        a = _assignment(p["id"], "b1", date(2026, 1, 1))
        result = self.analyzer._calculate_person_impacts([a], [a], [p], [])
        assert len(result) == 1
        assert result[0]["impact"] == "unchanged"
        assert result[0]["change"] == 0

    def test_increased_assignments(self):
        p = _person("Dr. B")
        baseline_a = [_assignment(p["id"], "b1", date(2026, 1, 1))]
        proposed_a = [
            _assignment(p["id"], "b1", date(2026, 1, 1)),
            _assignment(p["id"], "b2", date(2026, 1, 2)),
        ]
        result = self.analyzer._calculate_person_impacts(
            baseline_a, proposed_a, [p], []
        )
        assert result[0]["impact"] == "increased"
        assert result[0]["change"] == 1

    def test_decreased_assignments(self):
        p = _person("Dr. C")
        baseline_a = [
            _assignment(p["id"], "b1", date(2026, 1, 1)),
            _assignment(p["id"], "b2", date(2026, 1, 2)),
        ]
        proposed_a = [_assignment(p["id"], "b1", date(2026, 1, 1))]
        result = self.analyzer._calculate_person_impacts(
            baseline_a, proposed_a, [p], []
        )
        assert result[0]["impact"] == "decreased"
        assert result[0]["change"] == -1

    def test_person_name_included(self):
        p = _person("Dr. Specific")
        result = self.analyzer._calculate_person_impacts([], [], [p], [])
        assert result[0]["person_name"] == "Dr. Specific"

    def test_person_id_included(self):
        p = _person("Dr. X")
        result = self.analyzer._calculate_person_impacts([], [], [p], [])
        assert result[0]["person_id"] == p["id"]

    def test_multiple_persons(self):
        p1 = _person("Dr. A")
        p2 = _person("Dr. B")
        result = self.analyzer._calculate_person_impacts([], [], [p1, p2], [])
        assert len(result) == 2

    def test_counts_only_matching_person(self):
        p1 = _person("Dr. A")
        p2 = _person("Dr. B")
        a1 = _assignment(p1["id"], "b1", date(2026, 1, 1))
        a2 = _assignment(p2["id"], "b2", date(2026, 1, 2))
        result = self.analyzer._calculate_person_impacts(
            [a1, a2], [a1, a2], [p1, p2], []
        )
        assert result[0]["baseline_assignments"] == 1
        assert result[1]["baseline_assignments"] == 1


# ---------------------------------------------------------------------------
# ScenarioAnalyzer._generate_recommendations
# ---------------------------------------------------------------------------


class TestGenerateRecommendations:
    def setup_method(self):
        self.analyzer = ScenarioAnalyzer()

    def test_improvement(self):
        impact = {
            "overall_change": "IMPROVEMENT",
            "fatigue_change": -10,
            "min_effectiveness_change": 5,
        }
        result = self.analyzer._generate_recommendations(impact, [])
        assert any("IMPROVES" in r for r in result)

    def test_degradation(self):
        impact = {
            "overall_change": "DEGRADATION",
            "fatigue_change": 10,
            "min_effectiveness_change": -5,
        }
        result = self.analyzer._generate_recommendations(impact, [])
        assert any("INCREASES" in r or "WARNING" in r for r in result)

    def test_high_fatigue_increase_warns(self):
        impact = {
            "overall_change": "DEGRADATION",
            "fatigue_change": 6,
            "min_effectiveness_change": 0,
        }
        result = self.analyzer._generate_recommendations(impact, [])
        assert any("consider alternatives" in r for r in result)

    def test_large_fatigue_decrease_positive(self):
        impact = {
            "overall_change": "IMPROVEMENT",
            "fatigue_change": -6,
            "min_effectiveness_change": 5,
        }
        result = self.analyzer._generate_recommendations(impact, [])
        assert any("positive impact" in r for r in result)

    def test_large_min_effectiveness_drop_alerts(self):
        impact = {
            "overall_change": "DEGRADATION",
            "fatigue_change": 3,
            "min_effectiveness_change": -15,
        }
        result = self.analyzer._generate_recommendations(impact, [])
        assert any("ALERT" in r for r in result)

    def test_no_change_minimal_impact(self):
        impact = {
            "overall_change": "NO_CHANGE",
            "fatigue_change": 0,
            "min_effectiveness_change": 0,
        }
        result = self.analyzer._generate_recommendations(impact, [])
        assert any("minimal" in r for r in result)

    def test_always_returns_list(self):
        impact = {
            "overall_change": "NO_CHANGE",
            "fatigue_change": 0,
            "min_effectiveness_change": 0,
        }
        result = self.analyzer._generate_recommendations(impact, [])
        assert isinstance(result, list)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# ScenarioAnalyzer._generate_visualization_data
# ---------------------------------------------------------------------------


class TestGenerateVisualizationData:
    def setup_method(self):
        self.analyzer = ScenarioAnalyzer()

    def test_has_comparison_chart(self):
        result = self.analyzer._generate_visualization_data(
            {"avg_effectiveness": 80, "min_effectiveness": 70, "avg_fatigue_score": 20},
            {"avg_effectiveness": 85, "min_effectiveness": 75, "avg_fatigue_score": 15},
            [],
        )
        assert "comparison_chart" in result
        assert "baseline" in result["comparison_chart"]
        assert "proposed" in result["comparison_chart"]

    def test_has_risk_distribution(self):
        result = self.analyzer._generate_visualization_data(
            {"risk_distribution": {"low": 5}},
            {"risk_distribution": {"low": 3, "moderate": 2}},
            [],
        )
        assert "risk_distribution" in result
        assert "baseline" in result["risk_distribution"]
        assert "proposed" in result["risk_distribution"]

    def test_has_person_heatmap(self):
        impacts = [
            {"person_id": "p1", "change": 2, "impact": "increased"},
            {"person_id": "p2", "change": -1, "impact": "decreased"},
        ]
        result = self.analyzer._generate_visualization_data({}, {}, impacts)
        assert "person_heatmap" in result
        assert len(result["person_heatmap"]) == 2

    def test_heatmap_change_magnitude(self):
        impacts = [{"person_id": "p1", "change": -3, "impact": "decreased"}]
        result = self.analyzer._generate_visualization_data({}, {}, impacts)
        assert result["person_heatmap"][0]["change_magnitude"] == 3

    def test_heatmap_direction(self):
        impacts = [{"person_id": "p1", "change": 1, "impact": "increased"}]
        result = self.analyzer._generate_visualization_data({}, {}, impacts)
        assert result["person_heatmap"][0]["direction"] == "increased"

    def test_comparison_chart_values(self):
        result = self.analyzer._generate_visualization_data(
            {"avg_effectiveness": 80, "min_effectiveness": 70, "avg_fatigue_score": 20},
            {"avg_effectiveness": 85, "min_effectiveness": 75, "avg_fatigue_score": 15},
            [],
        )
        assert result["comparison_chart"]["baseline"]["avg_effectiveness"] == 80
        assert result["comparison_chart"]["proposed"]["fatigue_score"] == 15

    def test_empty_inputs(self):
        result = self.analyzer._generate_visualization_data({}, {}, [])
        assert "comparison_chart" in result
        assert "risk_distribution" in result
        assert result["person_heatmap"] == []


# ---------------------------------------------------------------------------
# ScenarioAnalyzer._apply_changes — multiple changes
# ---------------------------------------------------------------------------


class TestApplyChangesMultiple:
    def setup_method(self):
        self.analyzer = ScenarioAnalyzer()

    def test_add_then_remove(self):
        blocks = [_block(date(2026, 1, 5), block_id="b1")]
        # Start empty, add one, remove it
        result = self.analyzer._apply_changes(
            assignments=[],
            changes=[
                {"action": "add", "person_id": "p1", "block_id": "b1"},
            ],
            blocks=blocks,
        )
        # The added assignment has a random ID; remove would need that ID
        # Just verify add worked
        assert len(result) == 1

    def test_multiple_adds(self):
        blocks = [
            _block(date(2026, 1, 5), block_id="b1"),
            _block(date(2026, 1, 6), block_id="b2"),
        ]
        result = self.analyzer._apply_changes(
            assignments=[],
            changes=[
                {"action": "add", "person_id": "p1", "block_id": "b1"},
                {"action": "add", "person_id": "p2", "block_id": "b2"},
            ],
            blocks=blocks,
        )
        assert len(result) == 2

    def test_remove_then_add(self):
        assignments = [_assignment("p1", "b1", date(2026, 1, 1), aid="a1")]
        blocks = [_block(date(2026, 1, 5), block_id="b2")]
        result = self.analyzer._apply_changes(
            assignments=assignments,
            changes=[
                {"action": "remove", "assignment_id": "a1"},
                {"action": "add", "person_id": "p2", "block_id": "b2"},
            ],
            blocks=blocks,
        )
        assert len(result) == 1
        assert result[0]["person_id"] == "p2"


# ---------------------------------------------------------------------------
# ScenarioAnalyzer.analyze — integration
# ---------------------------------------------------------------------------


class TestAnalyzeIntegration:
    def test_returns_report(self):
        analyzer = ScenarioAnalyzer()
        p = _person("Dr. Test")
        b = _block(date(2026, 1, 5), block_id="b1")
        scenario = WhatIfScenario(
            scenario_id="s1",
            name="Test",
            description="Add shift",
            changes=[{"action": "add", "person_id": p["id"], "block_id": "b1"}],
        )
        report = analyzer.analyze(
            baseline_assignments=[],
            scenario=scenario,
            persons=[p],
            blocks=[b],
        )
        assert isinstance(report, FatigueImpactReport)
        assert report.scenario_id == "s1"

    def test_report_has_impact_summary(self):
        analyzer = ScenarioAnalyzer()
        p = _person("Dr. Test")
        b = _block(date(2026, 1, 5), block_id="b1")
        scenario = WhatIfScenario(
            scenario_id="s1",
            name="Test",
            description="Add shift",
            changes=[{"action": "add", "person_id": p["id"], "block_id": "b1"}],
        )
        report = analyzer.analyze([], scenario, [p], [b])
        assert "overall_change" in report.impact_summary

    def test_report_has_recommendations(self):
        analyzer = ScenarioAnalyzer()
        p = _person("Dr. Test")
        b = _block(date(2026, 1, 5), block_id="b1")
        scenario = WhatIfScenario(
            scenario_id="s1",
            name="Test",
            description="Add shift",
            changes=[{"action": "add", "person_id": p["id"], "block_id": "b1"}],
        )
        report = analyzer.analyze([], scenario, [p], [b])
        assert isinstance(report.recommendations, list)

    def test_report_has_visualization_data(self):
        analyzer = ScenarioAnalyzer()
        p = _person("Dr. Test")
        b = _block(date(2026, 1, 5), block_id="b1")
        scenario = WhatIfScenario(
            scenario_id="s1",
            name="Test",
            description="Add shift",
            changes=[{"action": "add", "person_id": p["id"], "block_id": "b1"}],
        )
        report = analyzer.analyze([], scenario, [p], [b])
        assert "comparison_chart" in report.visualization_data

    def test_empty_scenario_no_crash(self):
        analyzer = ScenarioAnalyzer()
        p = _person("Dr. Test")
        scenario = WhatIfScenario(
            scenario_id="s1",
            name="Empty",
            description="No changes",
            changes=[],
        )
        report = analyzer.analyze([], scenario, [p], [])
        assert report.impact_summary["overall_change"] == "NO_CHANGE"


# ---------------------------------------------------------------------------
# ScenarioAnalyzer.compare_scenarios
# ---------------------------------------------------------------------------


class TestCompareScenarios:
    def test_returns_list(self):
        analyzer = ScenarioAnalyzer()
        p = _person("Dr. Test")
        s1 = WhatIfScenario(scenario_id="s1", name="A", description="A", changes=[])
        s2 = WhatIfScenario(scenario_id="s2", name="B", description="B", changes=[])
        result = analyzer.compare_scenarios([], [s1, s2], [p], [])
        assert isinstance(result, list)
        assert len(result) == 2

    def test_reports_sorted_by_fatigue(self):
        analyzer = ScenarioAnalyzer()
        p = _person("Dr. Test")
        b = _block(date(2026, 1, 5), block_id="b1")
        # One scenario adds work, the other doesn't
        s1 = WhatIfScenario(
            scenario_id="s1", name="No change", description="D", changes=[]
        )
        s2 = WhatIfScenario(
            scenario_id="s2",
            name="Add shift",
            description="D",
            changes=[{"action": "add", "person_id": p["id"], "block_id": "b1"}],
        )
        result = analyzer.compare_scenarios([], [s1, s2], [p], [b])
        # First should have lower fatigue score
        first_fatigue = result[0].proposed_metrics.get("avg_fatigue_score", 0)
        second_fatigue = result[1].proposed_metrics.get("avg_fatigue_score", 0)
        assert first_fatigue <= second_fatigue

    def test_each_report_is_fatigue_impact_report(self):
        analyzer = ScenarioAnalyzer()
        s1 = WhatIfScenario(scenario_id="s1", name="A", description="A", changes=[])
        result = analyzer.compare_scenarios([], [s1], [], [])
        assert all(isinstance(r, FatigueImpactReport) for r in result)


# ---------------------------------------------------------------------------
# ScenarioAnalyzer.find_best_coverage
# ---------------------------------------------------------------------------


class TestFindBestCoverage:
    def test_returns_list(self):
        analyzer = ScenarioAnalyzer()
        p1 = _person("Dr. A")
        p2 = _person("Dr. B")
        b = _block(date(2026, 1, 5), block_id="b1")
        result = analyzer.find_best_coverage(
            baseline_assignments=[],
            block_to_cover=b,
            eligible_persons=[p1, p2],
            blocks=[b],
        )
        assert isinstance(result, list)
        assert len(result) == 2

    def test_each_result_has_recommendation(self):
        analyzer = ScenarioAnalyzer()
        p = _person("Dr. A")
        b = _block(date(2026, 1, 5), block_id="b1")
        result = analyzer.find_best_coverage([], b, [p], [b])
        assert result[0]["recommendation"] in {"SAFE", "CAUTION", "NOT RECOMMENDED"}

    def test_each_result_has_person_info(self):
        analyzer = ScenarioAnalyzer()
        p = _person("Dr. A")
        b = _block(date(2026, 1, 5), block_id="b1")
        result = analyzer.find_best_coverage([], b, [p], [b])
        assert "person_id" in result[0]
        assert "person_name" in result[0]

    def test_sorted_by_fatigue_impact(self):
        analyzer = ScenarioAnalyzer()
        p1 = _person("Dr. A")
        p2 = _person("Dr. B")
        b = _block(date(2026, 1, 5), block_id="b1")
        result = analyzer.find_best_coverage([], b, [p1, p2], [b])
        if len(result) >= 2:
            assert result[0]["fatigue_impact"] <= result[1]["fatigue_impact"]

    def test_empty_eligible_returns_empty(self):
        analyzer = ScenarioAnalyzer()
        b = _block(date(2026, 1, 5), block_id="b1")
        result = analyzer.find_best_coverage([], b, [], [b])
        assert result == []
