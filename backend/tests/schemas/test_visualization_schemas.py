"""Tests for visualization schemas (defaults, Field bounds, nested models)."""

import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.visualization import (
    HeatmapRequest,
    HeatmapData,
    HeatmapResponse,
    CoverageGap,
    CoverageHeatmapResponse,
    WorkloadRequest,
    ExportRequest,
    TimeRangeType,
    UnifiedHeatmapRequest,
)


class TestHeatmapRequest:
    def test_defaults(self):
        r = HeatmapRequest(
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 3, 31),
        )
        assert r.person_ids is None
        assert r.rotation_ids is None
        assert r.include_fmit is True
        assert r.group_by == "person"

    def test_custom(self):
        ids = [uuid4(), uuid4()]
        r = HeatmapRequest(
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 3, 31),
            person_ids=ids,
            include_fmit=False,
            group_by="rotation",
        )
        assert len(r.person_ids) == 2
        assert r.include_fmit is False
        assert r.group_by == "rotation"


class TestHeatmapData:
    def test_defaults(self):
        r = HeatmapData(
            x_labels=["2026-01-01"],
            y_labels=["Dr. Smith"],
            z_values=[[1.0]],
        )
        assert r.color_scale == "Viridis"
        assert r.annotations is None

    def test_with_annotations(self):
        r = HeatmapData(
            x_labels=["2026-01-01"],
            y_labels=["Dr. Smith"],
            z_values=[[1.0]],
            annotations=[{"text": "Note"}],
        )
        assert len(r.annotations) == 1


class TestHeatmapResponse:
    def _make_data(self):
        return HeatmapData(
            x_labels=["2026-01-01"],
            y_labels=["Dr. Smith"],
            z_values=[[1.0]],
        )

    def test_valid(self):
        r = HeatmapResponse(data=self._make_data(), title="Test Heatmap")
        assert r.generated_at is not None
        assert r.metadata is None

    def test_with_metadata(self):
        r = HeatmapResponse(
            data=self._make_data(),
            title="Test Heatmap",
            metadata={"count": 5},
        )
        assert r.metadata["count"] == 5


class TestCoverageGap:
    def test_valid(self):
        r = CoverageGap(
            date=datetime.date(2026, 1, 15),
            time_of_day="PM",
            severity="high",
        )
        assert r.rotation is None

    def test_with_rotation(self):
        r = CoverageGap(
            date=datetime.date(2026, 1, 15),
            time_of_day="AM",
            rotation="FMIT Inpatient",
            severity="medium",
        )
        assert r.rotation == "FMIT Inpatient"


class TestCoverageHeatmapResponse:
    def _make_data(self):
        return HeatmapData(
            x_labels=["2026-01-01"],
            y_labels=["FMIT"],
            z_values=[[1.0]],
        )

    def test_defaults(self):
        r = CoverageHeatmapResponse(
            data=self._make_data(),
            coverage_percentage=95.0,
            title="Coverage",
        )
        assert r.gaps == []
        assert r.generated_at is not None

    # --- coverage_percentage ge=0, le=100 ---

    def test_coverage_percentage_zero(self):
        r = CoverageHeatmapResponse(
            data=self._make_data(),
            coverage_percentage=0,
            title="Coverage",
        )
        assert r.coverage_percentage == 0

    def test_coverage_percentage_hundred(self):
        r = CoverageHeatmapResponse(
            data=self._make_data(),
            coverage_percentage=100,
            title="Coverage",
        )
        assert r.coverage_percentage == 100

    def test_coverage_percentage_below_min(self):
        with pytest.raises(ValidationError):
            CoverageHeatmapResponse(
                data=self._make_data(),
                coverage_percentage=-1,
                title="Coverage",
            )

    def test_coverage_percentage_above_max(self):
        with pytest.raises(ValidationError):
            CoverageHeatmapResponse(
                data=self._make_data(),
                coverage_percentage=101,
                title="Coverage",
            )


class TestWorkloadRequest:
    def test_defaults(self):
        r = WorkloadRequest(
            person_ids=[uuid4()],
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 3, 31),
        )
        assert r.include_weekends is False

    def test_with_weekends(self):
        r = WorkloadRequest(
            person_ids=[uuid4()],
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 3, 31),
            include_weekends=True,
        )
        assert r.include_weekends is True


class TestExportRequest:
    def test_defaults(self):
        r = ExportRequest(
            heatmap_type="unified",
            request_params={"start_date": "2026-01-01"},
        )
        assert r.format == "png"
        assert r.width == 1200
        assert r.height == 800

    # --- width gt=0 ---

    def test_width_zero(self):
        with pytest.raises(ValidationError):
            ExportRequest(
                heatmap_type="unified",
                width=0,
                request_params={},
            )

    # --- height gt=0 ---

    def test_height_zero(self):
        with pytest.raises(ValidationError):
            ExportRequest(
                heatmap_type="unified",
                height=0,
                request_params={},
            )


class TestTimeRangeType:
    def test_defaults(self):
        r = TimeRangeType(range_type="month")
        assert r.reference_date is None
        assert r.start_date is None
        assert r.end_date is None

    def test_custom(self):
        r = TimeRangeType(
            range_type="custom",
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 3, 31),
        )
        assert r.range_type == "custom"


class TestUnifiedHeatmapRequest:
    def test_defaults(self):
        tr = TimeRangeType(
            range_type="month", reference_date=datetime.date(2026, 1, 15)
        )
        r = UnifiedHeatmapRequest(time_range=tr)
        assert r.person_ids is None
        assert r.rotation_ids is None
        assert r.include_fmit is True
        assert r.group_by == "person"

    def test_custom(self):
        tr = TimeRangeType(range_type="week")
        r = UnifiedHeatmapRequest(
            time_range=tr,
            person_ids=[uuid4()],
            include_fmit=False,
            group_by="daily",
        )
        assert r.include_fmit is False
        assert r.group_by == "daily"
