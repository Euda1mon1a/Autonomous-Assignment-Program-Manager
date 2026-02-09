"""Tests for behavioral network schemas (enums, Field bounds, defaults, patterns)."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.behavioral_network import (
    BehavioralRole,
    BurdenCategory,
    EquityStatus,
    ProtectionLevel,
    BurdenCalculationRequest,
    SwapRecordInput,
    MartyrProtectionCheckRequest,
    SwapBlockCheckRequest,
    ShiftBurdenResponse,
    FacultyBurdenProfileResponse,
    SwapNetworkNodeResponse,
    SwapNetworkAnalysisResponse,
    MartyrProtectionResponse,
    SwapBlockDecisionResponse,
    BurdenEquityAnalysisResponse,
    RecommendationItem,
    ShadowOrgChartReportResponse,
)


class TestBehavioralRole:
    def test_values(self):
        assert BehavioralRole.NEUTRAL == "neutral"
        assert BehavioralRole.POWER_BROKER == "power_broker"
        assert BehavioralRole.MARTYR == "martyr"
        assert BehavioralRole.EVADER == "evader"
        assert BehavioralRole.ISOLATE == "isolate"
        assert BehavioralRole.STABILIZER == "stabilizer"

    def test_count(self):
        assert len(BehavioralRole) == 6


class TestBurdenCategory:
    def test_values(self):
        assert BurdenCategory.MINIMAL == "minimal"
        assert BurdenCategory.EXTREME == "extreme"

    def test_count(self):
        assert len(BurdenCategory) == 6


class TestEquityStatus:
    def test_count(self):
        assert len(EquityStatus) == 5


class TestProtectionLevel:
    def test_count(self):
        assert len(ProtectionLevel) == 4


class TestBurdenCalculationRequest:
    def test_valid_defaults(self):
        r = BurdenCalculationRequest(
            shift_id=uuid4(),
            faculty_id=uuid4(),
            date=datetime(2026, 1, 15),
            shift_type="clinic",
            hours=8.0,
        )
        assert r.is_weekend is False
        assert r.is_holiday is False
        assert r.is_night is False
        assert r.custom_factors == []

    # --- shift_type min_length=1, max_length=50 ---

    def test_shift_type_empty(self):
        with pytest.raises(ValidationError):
            BurdenCalculationRequest(
                shift_id=uuid4(),
                faculty_id=uuid4(),
                date=datetime(2026, 1, 15),
                shift_type="",
                hours=8.0,
            )

    def test_shift_type_too_long(self):
        with pytest.raises(ValidationError):
            BurdenCalculationRequest(
                shift_id=uuid4(),
                faculty_id=uuid4(),
                date=datetime(2026, 1, 15),
                shift_type="x" * 51,
                hours=8.0,
            )

    # --- hours gt=0, le=24 ---

    def test_hours_zero(self):
        with pytest.raises(ValidationError):
            BurdenCalculationRequest(
                shift_id=uuid4(),
                faculty_id=uuid4(),
                date=datetime(2026, 1, 15),
                shift_type="clinic",
                hours=0,
            )

    def test_hours_above_max(self):
        with pytest.raises(ValidationError):
            BurdenCalculationRequest(
                shift_id=uuid4(),
                faculty_id=uuid4(),
                date=datetime(2026, 1, 15),
                shift_type="clinic",
                hours=25,
            )


class TestSwapRecordInput:
    def test_defaults(self):
        r = SwapRecordInput(
            source_id=uuid4(),
            source_name="Dr. Smith",
            target_id=uuid4(),
            target_name="Dr. Jones",
            initiated_by=uuid4(),
        )
        assert r.source_burden == 10.0
        assert r.target_burden == 0.0
        assert r.was_successful is True

    # --- source_name min_length=1, max_length=200 ---

    def test_source_name_empty(self):
        with pytest.raises(ValidationError):
            SwapRecordInput(
                source_id=uuid4(),
                source_name="",
                target_id=uuid4(),
                target_name="Dr. Jones",
                initiated_by=uuid4(),
            )

    # --- source_burden ge=0, le=100 ---

    def test_source_burden_negative(self):
        with pytest.raises(ValidationError):
            SwapRecordInput(
                source_id=uuid4(),
                source_name="Dr. Smith",
                target_id=uuid4(),
                target_name="Dr. Jones",
                initiated_by=uuid4(),
                source_burden=-1,
            )

    def test_source_burden_above_max(self):
        with pytest.raises(ValidationError):
            SwapRecordInput(
                source_id=uuid4(),
                source_name="Dr. Smith",
                target_id=uuid4(),
                target_name="Dr. Jones",
                initiated_by=uuid4(),
                source_burden=101,
            )


class TestMartyrProtectionCheckRequest:
    def test_defaults(self):
        r = MartyrProtectionCheckRequest(faculty_id=uuid4())
        assert r.current_allostatic_load == 0.0

    def test_load_bounds(self):
        with pytest.raises(ValidationError):
            MartyrProtectionCheckRequest(
                faculty_id=uuid4(), current_allostatic_load=101
            )


class TestSwapBlockCheckRequest:
    def test_defaults(self):
        r = SwapBlockCheckRequest(target_id=uuid4(), source_burden=50.0)
        assert r.target_current_load == 0.0

    def test_target_load_above_max(self):
        with pytest.raises(ValidationError):
            SwapBlockCheckRequest(
                target_id=uuid4(), source_burden=10, target_current_load=101
            )


class TestShiftBurdenResponse:
    def test_valid(self):
        r = ShiftBurdenResponse(
            shift_id=uuid4(),
            faculty_id=uuid4(),
            date=datetime(2026, 1, 15),
            shift_type="clinic",
            raw_hours=8.0,
            burden_weight=1.5,
            weighted_burden=12.0,
            category=BurdenCategory.MODERATE,
            factors=["weekend"],
        )
        assert r.category == BurdenCategory.MODERATE


class TestFacultyBurdenProfileResponse:
    def test_valid(self):
        r = FacultyBurdenProfileResponse(
            faculty_id=uuid4(),
            faculty_name="Dr. Smith",
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
            calculated_at=datetime(2026, 4, 1),
            total_hours=160.0,
            total_shifts=20,
            shift_breakdown={"clinic": 15, "call": 5},
            total_burden=200.0,
            burden_per_hour=1.25,
            high_burden_shifts=3,
            equity_status=EquityStatus.BALANCED,
            std_devs_from_mean=0.5,
            behavioral_role=BehavioralRole.NEUTRAL,
            protection_level=ProtectionLevel.NONE,
        )
        assert r.equity_status == EquityStatus.BALANCED


class TestRecommendationItem:
    def test_valid_priorities(self):
        for p in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            r = RecommendationItem(priority=p, action="Do X", details="Details")
            assert r.priority == p

    def test_invalid_priority(self):
        with pytest.raises(ValidationError):
            RecommendationItem(priority="URGENT", action="Do X", details="Details")


class TestSwapBlockDecisionResponse:
    def test_valid(self):
        r = SwapBlockDecisionResponse(should_block=True, reason="Martyr protection")
        assert r.should_block is True


class TestBurdenEquityAnalysisResponse:
    def test_valid(self):
        r = BurdenEquityAnalysisResponse(
            mean_burden=50.0,
            std_burden=10.0,
            mean_hours=40.0,
            std_hours=5.0,
            gini_coefficient=0.15,
            equity_grade="A",
            distribution={"balanced": 8, "heavy": 2},
            crushing_faculty=[],
            very_light_faculty=[],
            recommendations=[],
        )
        assert r.gini_coefficient == 0.15


class TestShadowOrgChartReportResponse:
    def test_valid(self):
        r = ShadowOrgChartReportResponse(
            generated_at=datetime(2026, 1, 1),
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
            network_summary={},
            behavioral_roles={},
            risk_flags={},
            detailed_roles={},
            recommendations=[],
        )
        assert r.burden_equity is None
