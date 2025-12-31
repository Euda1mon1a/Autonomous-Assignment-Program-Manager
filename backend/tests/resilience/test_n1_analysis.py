"""
Tests for N-1 contingency analysis.

Tests single-component failure detection (power grid standard).
"""

import pytest
from datetime import date

from app.resilience.contingency.n1_analyzer import N1Analyzer


class TestN1Analyzer:
    """Test suite for N-1 contingency analysis."""

    def test_analyze_person_with_backup(self):
        """Test analyzing person with available backup."""
        analyzer = N1Analyzer()

        assigned_slots = [
            (date(2024, 1, 1), "clinic"),
            (date(2024, 1, 2), "inpatient"),
        ]

        scenario = analyzer.analyze_person_failure(
            person_id="resident1",
            assigned_slots=assigned_slots,
            available_backups=["backup1", "backup2"],
            backup_capacity={"backup1": 5, "backup2": 3},
        )

        assert scenario.component_id == "resident1"
        assert scenario.affected_slots == 2
        assert scenario.backup_available
        assert scenario.criticality_score < 0.7  # Low criticality with backup

    def test_analyze_person_without_backup(self):
        """Test analyzing person without backup (SPOF)."""
        analyzer = N1Analyzer()

        assigned_slots = [(date(2024, 1, i), "clinic") for i in range(1, 11)]  # 10 slots

        scenario = analyzer.analyze_person_failure(
            person_id="critical_resident",
            assigned_slots=assigned_slots,
            available_backups=[],
            backup_capacity={},
        )

        assert not scenario.backup_available
        assert scenario.criticality_score >= 0.5  # High criticality without backup
        assert scenario.cascade_potential > 0

    def test_analyze_specialty_single_specialist(self):
        """Test analyzing specialty with single specialist (SPOF)."""
        analyzer = N1Analyzer()

        scenario = analyzer.analyze_specialty_failure(
            specialty="ultrasound",
            required_slots=20,
            available_specialists=["specialist1"],  # Only one!
            cross_trained=[],
        )

        assert scenario.component_type == "specialty"
        assert scenario.criticality_score >= 0.8  # Very high criticality
        assert not scenario.backup_available

    def test_analyze_specialty_multiple_specialists(self):
        """Test analyzing specialty with multiple specialists."""
        analyzer = N1Analyzer()

        scenario = analyzer.analyze_specialty_failure(
            specialty="procedures",
            required_slots=15,
            available_specialists=["spec1", "spec2", "spec3"],
            cross_trained=["trainee1"],
        )

        assert scenario.backup_available
        assert scenario.criticality_score < 0.5  # Lower criticality with redundancy

    def test_find_single_points_of_failure(self):
        """Test finding SPOFs."""
        analyzer = N1Analyzer()

        # Create several scenarios
        analyzer.analyze_person_failure(
            "person1",
            [(date(2024, 1, 1), "clinic")],
            [],
            {},  # SPOF
        )

        analyzer.analyze_person_failure(
            "person2",
            [(date(2024, 1, 1), "clinic")],
            ["backup1"],
            {"backup1": 5},  # Not SPOF
        )

        analyzer.analyze_specialty_failure(
            "critical_skill",
            required_slots=50,
            available_specialists=["only_one"],
            cross_trained=[],  # SPOF
        )

        spofs = analyzer.find_single_points_of_failure(min_criticality=0.7)

        assert len(spofs) >= 2  # At least 2 SPOFs identified
        assert all(s.criticality_score >= 0.7 for s in spofs)

    def test_calculate_redundancy_score(self):
        """Test redundancy score calculation."""
        analyzer = N1Analyzer()

        # High redundancy
        score_high = analyzer.calculate_redundancy_score(
            person_id="person1",
            assignments=[(date(2024, 1, i), "clinic") for i in range(1, 6)],  # 5 assignments
            available_backups=3,
        )

        # Low redundancy
        score_low = analyzer.calculate_redundancy_score(
            person_id="person2",
            assignments=[(date(2024, 1, i), "clinic") for i in range(1, 21)],  # 20 assignments
            available_backups=1,
        )

        assert score_high > score_low
        assert 0 <= score_high <= 1.0
        assert 0 <= score_low <= 1.0

    def test_get_summary(self):
        """Test summary statistics."""
        analyzer = N1Analyzer()

        # Add various scenarios
        analyzer.analyze_person_failure("p1", [(date(2024, 1, 1), "c")], ["b1"], {"b1": 1})
        analyzer.analyze_person_failure("p2", [(date(2024, 1, 1), "c")] * 10, [], {})
        analyzer.analyze_specialty_failure("s1", 5, ["spec1"], [])

        summary = analyzer.get_summary()

        assert summary["total_scenarios"] == 3
        assert "critical_scenarios" in summary
        assert "avg_criticality" in summary
        assert "spof_count" in summary

    def test_no_assignments_edge_case(self):
        """Test edge case with no assignments."""
        analyzer = N1Analyzer()

        scenario = analyzer.analyze_person_failure(
            person_id="unassigned",
            assigned_slots=[],
            available_backups=[],
            backup_capacity={},
        )

        assert scenario.affected_slots == 0
        assert scenario.criticality_score == 0.0

    def test_mitigation_strategy_generation(self):
        """Test that mitigation strategies are generated."""
        analyzer = N1Analyzer()

        scenario = analyzer.analyze_person_failure(
            person_id="resident1",
            assigned_slots=[(date(2024, 1, 1), "clinic")],
            available_backups=["backup1"],
            backup_capacity={"backup1": 5},
        )

        assert scenario.mitigation_strategy != ""
        assert "backup" in scenario.mitigation_strategy.lower()
