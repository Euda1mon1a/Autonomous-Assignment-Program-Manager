"""Tests for unified heatmap schemas (defaults, Field bounds, nested models)."""

from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.unified_heatmap import (
    UnifiedCoverageRequest,
    UnifiedCoverageResponse,
    PersonCoverageRequest,
    PersonCoverageResponse,
    WeeklyFMITRequest,
    WeeklyFMITResponse,
    HeatmapExportRequest,
    HeatmapRenderRequest,
)


class TestUnifiedCoverageRequest:
    def test_valid_defaults(self):
        r = UnifiedCoverageRequest(
            start_date=date(2026, 1, 1), end_date=date(2026, 3, 31)
        )
        assert r.include_fmit is True
        assert r.include_residency is True

    def test_custom(self):
        r = UnifiedCoverageRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            include_fmit=False,
            include_residency=True,
        )
        assert r.include_fmit is False


class TestUnifiedCoverageResponse:
    def test_valid(self):
        r = UnifiedCoverageResponse(
            x_labels=["2026-01-01", "2026-01-02"],
            y_labels=["FMIT", "Clinic"],
            z_values=[[2, 1], [3, 2]],
            color_scale="Viridis",
            metadata={"total_assignments": 8},
        )
        assert r.color_scale == "Viridis"
        assert r.generated_at is not None


class TestPersonCoverageRequest:
    def test_valid_defaults(self):
        r = PersonCoverageRequest(
            start_date=date(2026, 1, 1), end_date=date(2026, 1, 31)
        )
        assert r.person_ids is None
        assert r.include_call is False

    def test_with_person_ids(self):
        ids = [uuid4(), uuid4()]
        r = PersonCoverageRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            person_ids=ids,
            include_call=True,
        )
        assert len(r.person_ids) == 2
        assert r.include_call is True


class TestPersonCoverageResponse:
    def test_valid(self):
        r = PersonCoverageResponse(
            x_labels=["2026-01-01"],
            y_labels=["Dr. Smith"],
            z_values=[[2]],
            color_scale="Blues",
            metadata={"people_count": 1},
        )
        assert r.color_scale == "Blues"


class TestWeeklyFMITRequest:
    def test_valid(self):
        r = WeeklyFMITRequest(start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        assert r.start_date == date(2026, 1, 1)


class TestWeeklyFMITResponse:
    def test_valid(self):
        r = WeeklyFMITResponse(
            x_labels=["2026-01-01", "2026-01-08"],
            y_labels=["Dr. Adams", "Dr. Brown"],
            z_values=[[1, 0], [0, 1]],
            color_scale="RdYlGn",
            metadata={"total_weeks": 2, "faculty_count": 2},
        )
        assert r.generated_at is not None


class TestHeatmapExportRequest:
    def test_defaults(self):
        r = HeatmapExportRequest(
            start_date=date(2026, 1, 1), end_date=date(2026, 3, 31)
        )
        assert r.format == "png"
        assert r.include_fmit is True
        assert r.include_residency is True
        assert r.width == 1200
        assert r.height == 800

    # --- width gt=0, le=4000 ---

    def test_width_zero(self):
        with pytest.raises(ValidationError):
            HeatmapExportRequest(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 3, 31),
                width=0,
            )

    def test_width_above_max(self):
        with pytest.raises(ValidationError):
            HeatmapExportRequest(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 3, 31),
                width=4001,
            )

    # --- height gt=0, le=4000 ---

    def test_height_zero(self):
        with pytest.raises(ValidationError):
            HeatmapExportRequest(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 3, 31),
                height=0,
            )

    def test_height_above_max(self):
        with pytest.raises(ValidationError):
            HeatmapExportRequest(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 3, 31),
                height=4001,
            )

    def test_boundaries(self):
        r = HeatmapExportRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            width=1,
            height=1,
        )
        assert r.width == 1
        r = HeatmapExportRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            width=4000,
            height=4000,
        )
        assert r.width == 4000


class TestHeatmapRenderRequest:
    def test_defaults(self):
        r = HeatmapRenderRequest(
            start_date=date(2026, 1, 1), end_date=date(2026, 3, 31)
        )
        assert r.include_fmit is True
        assert r.include_residency is True

    def test_custom(self):
        r = HeatmapRenderRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            include_fmit=False,
            include_residency=False,
        )
        assert r.include_fmit is False
