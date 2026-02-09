"""Tests for Propulsion Zone Detection (negative viscosity scheduling optimization)."""

import math
from dataclasses import dataclass
from datetime import date

import pytest

from app.resilience.propulsion_zones import (
    PropulsionAnalysis,
    PropulsionZone,
    _estimate_alignment_from_context,
    _extract_blocks,
    _generate_recommendation,
    calculate_intervention_potential,
    detect_propulsion_zones,
)


# ==================== PropulsionZone ====================


class TestPropulsionZone:
    def test_propulsion_zone_classification(self):
        # Positive alignment + negative energy flow = propulsion
        z = PropulsionZone(
            block_range=(date(2026, 1, 1), date(2026, 1, 31)),
            constraint_alignment=0.5,
            energy_flow=-0.3,
            intervention_potential=0.8,
        )
        assert z.is_propulsion_zone is True
        assert z.is_friction_zone is False

    def test_friction_zone_negative_alignment(self):
        z = PropulsionZone(
            block_range=(date(2026, 1, 1), date(2026, 1, 31)),
            constraint_alignment=-0.5,
            energy_flow=0.1,
            intervention_potential=0.2,
        )
        assert z.is_friction_zone is True
        assert z.is_propulsion_zone is False

    def test_friction_zone_high_energy_dissipation(self):
        z = PropulsionZone(
            block_range=(date(2026, 1, 1), date(2026, 1, 31)),
            constraint_alignment=0.3,
            energy_flow=0.6,
            intervention_potential=0.3,
        )
        assert z.is_friction_zone is True

    def test_neutral_zone(self):
        z = PropulsionZone(
            block_range=(date(2026, 1, 1), date(2026, 1, 31)),
            constraint_alignment=0.1,
            energy_flow=0.1,
            intervention_potential=0.5,
        )
        assert z.is_propulsion_zone is False
        assert z.is_friction_zone is False

    def test_details_default_empty(self):
        z = PropulsionZone(
            block_range=(date(2026, 1, 1), date(2026, 1, 31)),
            constraint_alignment=0.0,
            energy_flow=0.0,
            intervention_potential=0.5,
        )
        assert z.details == {}


# ==================== PropulsionAnalysis ====================


class TestPropulsionAnalysis:
    def test_defaults(self):
        pa = PropulsionAnalysis()
        assert pa.zones == []
        assert pa.overall_propulsion_potential == 0.0
        assert pa.recommendation == ""

    def test_to_dict(self):
        zone = PropulsionZone(
            block_range=(date(2026, 1, 1), date(2026, 1, 31)),
            constraint_alignment=0.5,
            energy_flow=-0.2,
            intervention_potential=0.7,
        )
        pa = PropulsionAnalysis(
            zones=[zone],
            overall_propulsion_potential=0.7,
            propulsion_zone_count=1,
            recommendation="test",
        )
        d = pa.to_dict()
        assert d["overall_propulsion_potential"] == 0.7
        assert d["propulsion_zone_count"] == 1
        assert len(d["zones"]) == 1
        assert d["zones"][0]["constraint_alignment"] == 0.5

    def test_to_dict_dates_are_iso(self):
        zone = PropulsionZone(
            block_range=(date(2026, 3, 1), date(2026, 3, 31)),
            constraint_alignment=0.0,
            energy_flow=0.0,
            intervention_potential=0.5,
        )
        pa = PropulsionAnalysis(zones=[zone])
        d = pa.to_dict()
        assert d["zones"][0]["block_range"] == ("2026-03-01", "2026-03-31")


# ==================== calculate_intervention_potential ====================


class TestCalculateInterventionPotential:
    def test_high_alignment_negative_flow(self):
        # Best case: high alignment + negative energy flow
        p = calculate_intervention_potential(1.0, -2.0)
        assert p > 0.7

    def test_negative_alignment_positive_flow(self):
        # Worst case: negative alignment + positive energy flow
        p = calculate_intervention_potential(-1.0, 2.0)
        assert p < 0.3

    def test_neutral(self):
        p = calculate_intervention_potential(0.0, 0.0)
        assert 0.3 < p < 0.7

    def test_bounded_0_to_1(self):
        # Extreme values
        p1 = calculate_intervention_potential(10.0, -100.0)
        p2 = calculate_intervention_potential(-10.0, 100.0)
        assert 0.0 <= p1 <= 1.0
        assert 0.0 <= p2 <= 1.0

    def test_alignment_dominates(self):
        # alignment_factor has 0.6 weight, energy 0.4
        p_high_align = calculate_intervention_potential(0.8, 0.0)
        p_low_align = calculate_intervention_potential(-0.8, 0.0)
        assert p_high_align > p_low_align


# ==================== _extract_blocks ====================


class TestExtractBlocks:
    def test_from_schedule_blocks(self):
        @dataclass
        class MockSchedule:
            blocks: list

        schedule = MockSchedule(blocks=["b1", "b2"])
        assert _extract_blocks(schedule, None) == ["b1", "b2"]

    def test_from_context_blocks(self):
        @dataclass
        class MockContext:
            blocks: list

        context = MockContext(blocks=["c1"])
        assert _extract_blocks(None, context) == ["c1"]

    def test_from_assignments(self):
        @dataclass(frozen=True)
        class MockBlock:
            name: str

        @dataclass
        class MockAssignment:
            block: MockBlock

        @dataclass
        class MockSchedule:
            assignments: list

        b1 = MockBlock(name="b1")
        schedule = MockSchedule(assignments=[MockAssignment(block=b1)])
        blocks = _extract_blocks(schedule, None)
        assert len(blocks) == 1

    def test_no_blocks_returns_empty(self):
        assert _extract_blocks(object(), object()) == []


# ==================== _estimate_alignment_from_context ====================


class TestEstimateAlignment:
    def test_no_constraints_returns_zero(self):
        assert _estimate_alignment_from_context(object()) == 0.0

    def test_all_soft_returns_positive(self):
        @dataclass
        class Constraint:
            is_hard: bool

        @dataclass
        class Context:
            constraints: list

        ctx = Context(constraints=[Constraint(is_hard=False) for _ in range(10)])
        alignment = _estimate_alignment_from_context(ctx)
        assert alignment > 0.0

    def test_all_hard_returns_negative(self):
        @dataclass
        class Constraint:
            is_hard: bool

        @dataclass
        class Context:
            constraints: list

        ctx = Context(constraints=[Constraint(is_hard=True) for _ in range(10)])
        alignment = _estimate_alignment_from_context(ctx)
        assert alignment < 0.0

    def test_balanced_returns_near_zero(self):
        @dataclass
        class Constraint:
            is_hard: bool

        @dataclass
        class Context:
            constraints: list

        ctx = Context(
            constraints=[
                Constraint(is_hard=True),
                Constraint(is_hard=False),
            ]
        )
        alignment = _estimate_alignment_from_context(ctx)
        assert abs(alignment) < 0.01

    def test_empty_constraints_returns_zero(self):
        @dataclass
        class Context:
            constraints: list

        ctx = Context(constraints=[])
        assert _estimate_alignment_from_context(ctx) == 0.0


# ==================== _generate_recommendation ====================


class TestGenerateRecommendation:
    def test_high_opportunity(self):
        rec = _generate_recommendation(0.8, 3, 0, [])
        assert "HIGH OPPORTUNITY" in rec

    def test_moderate_opportunity(self):
        rec = _generate_recommendation(0.5, 1, 1, [])
        assert "MODERATE OPPORTUNITY" in rec

    def test_high_friction(self):
        friction_zone = PropulsionZone(
            block_range=(date(2026, 1, 1), date(2026, 1, 31)),
            constraint_alignment=-0.5,
            energy_flow=0.3,
            intervention_potential=0.2,
        )
        rec = _generate_recommendation(0.2, 0, 3, [friction_zone])
        assert "FRICTION" in rec

    def test_low_opportunity(self):
        rec = _generate_recommendation(0.3, 1, 0, [])
        assert "LOW OPPORTUNITY" in rec


# ==================== detect_propulsion_zones ====================


class TestDetectPropulsionZones:
    def _make_schedule_and_context(self):
        @dataclass
        class MockBlock:
            start_date: date
            end_date: date

        @dataclass
        class MockSchedule:
            blocks: list

        blocks = [
            MockBlock(start_date=date(2026, 1, 1), end_date=date(2026, 1, 31)),
            MockBlock(start_date=date(2026, 2, 1), end_date=date(2026, 2, 28)),
        ]
        return MockSchedule(blocks=blocks), None

    def test_returns_analysis(self):
        schedule, context = self._make_schedule_and_context()
        result = detect_propulsion_zones(schedule, context)
        assert isinstance(result, PropulsionAnalysis)

    def test_zone_count(self):
        schedule, context = self._make_schedule_and_context()
        result = detect_propulsion_zones(schedule, context)
        # Currently treats entire schedule as one zone
        assert len(result.zones) == 1

    def test_with_energy_history(self):
        schedule, context = self._make_schedule_and_context()
        result = detect_propulsion_zones(
            schedule, context, energy_history=[-0.5, -0.3, -0.4]
        )
        # Negative energy = propulsion potential
        assert result.zones[0].energy_flow < 0

    def test_no_blocks_returns_empty(self):
        result = detect_propulsion_zones(object(), object())
        assert result.zones == []
        assert result.recommendation != ""

    def test_recommendation_populated(self):
        schedule, context = self._make_schedule_and_context()
        result = detect_propulsion_zones(schedule, context)
        assert len(result.recommendation) > 0

    def test_with_alignment_matrix(self):
        schedule, context = self._make_schedule_and_context()

        @dataclass
        class MockMatrix:
            overall_alignment: float

        matrix = MockMatrix(overall_alignment=0.8)
        result = detect_propulsion_zones(schedule, context, alignment_matrix=matrix)
        assert result.zones[0].constraint_alignment == 0.8
