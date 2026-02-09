"""Tests for academic blocks schemas (Field bounds, model/field validators, nested)."""

from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.academic_blocks import (
    AcademicBlock,
    ResidentRow,
    ACGMEStatus,
    MatrixCell,
    BlockMatrixResponse,
    BlockSummary,
    BlockListResponse,
)
from app.validators.common import ValidationError as AppValidationError


class TestAcademicBlock:
    def _valid_kwargs(self):
        return {
            "block_number": 1,
            "start_date": date.today(),
            "end_date": date.today(),
        }

    def test_valid_minimal(self):
        r = AcademicBlock(**self._valid_kwargs())
        assert r.name is None

    # --- block_number ge=1, le=13 ---

    def test_block_number_boundaries(self):
        kw = self._valid_kwargs()
        kw["block_number"] = 1
        r = AcademicBlock(**kw)
        assert r.block_number == 1
        kw["block_number"] = 13
        r = AcademicBlock(**kw)
        assert r.block_number == 13

    def test_block_number_below_min(self):
        kw = self._valid_kwargs()
        kw["block_number"] = 0
        with pytest.raises(ValidationError):
            AcademicBlock(**kw)

    def test_block_number_above_max(self):
        kw = self._valid_kwargs()
        kw["block_number"] = 14
        with pytest.raises(ValidationError):
            AcademicBlock(**kw)

    # --- name min_length=1, max_length=50 ---

    def test_name_empty(self):
        kw = self._valid_kwargs()
        kw["name"] = ""
        with pytest.raises(ValidationError):
            AcademicBlock(**kw)

    def test_name_too_long(self):
        kw = self._valid_kwargs()
        kw["name"] = "x" * 51
        with pytest.raises(ValidationError):
            AcademicBlock(**kw)

    # --- model_validator: start_date <= end_date ---

    def test_start_after_end(self):
        kw = self._valid_kwargs()
        kw["start_date"] = date.today()
        from datetime import timedelta

        kw["end_date"] = date.today() - timedelta(days=1)
        with pytest.raises(
            ValidationError, match="start_date.*must be before or equal"
        ):
            AcademicBlock(**kw)


class TestResidentRow:
    def test_valid(self):
        r = ResidentRow(resident_id=uuid4(), name="Dr. Smith", pgy_level=2)
        assert r.pgy_level == 2

    # --- name min_length=1, max_length=100 ---

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            ResidentRow(resident_id=uuid4(), name="", pgy_level=1)

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            ResidentRow(resident_id=uuid4(), name="x" * 101, pgy_level=1)

    # --- pgy_level ge=1, le=3 ---

    def test_pgy_level_boundaries(self):
        r = ResidentRow(resident_id=uuid4(), name="A", pgy_level=1)
        assert r.pgy_level == 1
        r = ResidentRow(resident_id=uuid4(), name="A", pgy_level=3)
        assert r.pgy_level == 3

    def test_pgy_level_below_min(self):
        with pytest.raises(ValidationError):
            ResidentRow(resident_id=uuid4(), name="A", pgy_level=0)

    def test_pgy_level_above_max(self):
        with pytest.raises(ValidationError):
            ResidentRow(resident_id=uuid4(), name="A", pgy_level=4)


class TestACGMEStatus:
    def test_valid(self):
        r = ACGMEStatus(is_compliant=True, hours_worked=60.0)
        assert r.warnings == []
        assert r.violations == []
        assert r.max_hours_allowed == 80.0

    def test_with_violations(self):
        r = ACGMEStatus(
            is_compliant=False,
            hours_worked=85.0,
            warnings=["Approaching limit"],
            violations=["80-hour exceeded"],
        )
        assert len(r.violations) == 1


class TestMatrixCell:
    def _make_acgme(self):
        return ACGMEStatus(is_compliant=True, hours_worked=40.0)

    def test_valid(self):
        r = MatrixCell(
            row_index=0,
            column_index=0,
            hours=40.0,
            acgme_status=self._make_acgme(),
        )
        assert r.rotation is None
        assert r.rotation_full_name is None

    # --- row_index ge=0, column_index ge=0, hours ge=0 ---

    def test_row_index_negative(self):
        with pytest.raises(ValidationError):
            MatrixCell(
                row_index=-1,
                column_index=0,
                hours=0,
                acgme_status=self._make_acgme(),
            )

    def test_column_index_negative(self):
        with pytest.raises(ValidationError):
            MatrixCell(
                row_index=0,
                column_index=-1,
                hours=0,
                acgme_status=self._make_acgme(),
            )

    def test_hours_negative(self):
        with pytest.raises(ValidationError):
            MatrixCell(
                row_index=0,
                column_index=0,
                hours=-1.0,
                acgme_status=self._make_acgme(),
            )


class TestBlockSummary:
    def test_valid(self):
        r = BlockSummary(
            block_number=5,
            name="Block 5",
            start_date=date.today(),
            end_date=date.today(),
            total_assignments=50,
            total_residents=20,
            compliance_rate=95.0,
            average_hours=60.0,
        )
        assert r.compliance_rate == 95.0

    # --- compliance_rate ge=0, le=100 ---

    def test_compliance_rate_negative(self):
        with pytest.raises(ValidationError):
            BlockSummary(
                block_number=1,
                name="B1",
                start_date=date.today(),
                end_date=date.today(),
                total_assignments=0,
                total_residents=0,
                compliance_rate=-1.0,
                average_hours=0.0,
            )

    def test_compliance_rate_above_max(self):
        with pytest.raises(ValidationError):
            BlockSummary(
                block_number=1,
                name="B1",
                start_date=date.today(),
                end_date=date.today(),
                total_assignments=0,
                total_residents=0,
                compliance_rate=101.0,
                average_hours=0.0,
            )


class TestBlockListResponse:
    def test_valid(self):
        r = BlockListResponse(blocks=[], academic_year="2025-2026", total_blocks=0)
        assert r.blocks == []
