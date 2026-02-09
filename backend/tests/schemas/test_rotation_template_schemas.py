"""Tests for rotation template schemas (Field validators, model_validators, enums, batch ops)."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.rotation_template import (
    TemplateCategory,
    VALID_TEMPLATE_CATEGORIES,
    RotationTemplateBase,
    RotationTemplateCreate,
    RotationTemplateUpdate,
    RotationTemplateResponse,
    RotationTemplateListResponse,
    BatchTemplateDeleteRequest,
    BatchTemplateUpdateItem,
    BatchTemplateUpdateRequest,
    BatchOperationResult,
    BatchTemplateResponse,
    BatchTemplateCreateRequest,
    BatchArchiveRequest,
    BatchRestoreRequest,
    TemplateExportRequest,
    TemplateExportResponse,
    ConflictCheckRequest,
    TemplateConflict,
    ConflictCheckResponse,
)


# ── TemplateCategory enum ──────────────────────────────────────────────


class TestTemplateCategory:
    def test_values(self):
        assert TemplateCategory.ROTATION == "rotation"
        assert TemplateCategory.TIME_OFF == "time_off"
        assert TemplateCategory.ABSENCE == "absence"
        assert TemplateCategory.EDUCATIONAL == "educational"

    def test_count(self):
        assert len(TemplateCategory) == 4

    def test_valid_categories_tuple(self):
        assert set(VALID_TEMPLATE_CATEGORIES) == {
            "rotation",
            "time_off",
            "absence",
            "educational",
        }


# ── RotationTemplateBase ──────────────────────────────────────────────


class TestRotationTemplateBase:
    def test_defaults(self):
        r = RotationTemplateBase(name="ICU", rotation_type="inpatient")
        assert r.template_category == "rotation"
        assert r.abbreviation is None
        assert r.display_abbreviation is None
        assert r.font_color is None
        assert r.background_color is None
        assert r.clinic_location is None
        assert r.max_residents is None
        assert r.requires_specialty is None
        assert r.requires_procedure_credential is False
        assert r.supervision_required is True
        assert r.max_supervision_ratio == 4

    # --- name validator (not empty) ---

    def test_name_empty(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            RotationTemplateBase(name="", rotation_type="inpatient")

    def test_name_whitespace_only(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            RotationTemplateBase(name="   ", rotation_type="inpatient")

    def test_name_stripped(self):
        r = RotationTemplateBase(name="  ICU  ", rotation_type="inpatient")
        assert r.name == "ICU"

    # --- rotation_type validator (canonical + aliases) ---

    def test_rotation_type_valid_canonical(self):
        for rt in (
            "inpatient",
            "outpatient",
            "conference",
            "education",
            "lecture",
            "absence",
            "off",
            "recovery",
        ):
            # non-rotation types need matching category
            cat = "rotation" if rt in ("inpatient", "outpatient") else "time_off"
            if rt in ("conference", "education", "lecture"):
                cat = "educational"
            elif rt == "absence":
                cat = "absence"
            r = RotationTemplateBase(
                name="Test", rotation_type=rt, template_category=cat
            )
            assert r.rotation_type == rt

    def test_rotation_type_alias_clinic(self):
        r = RotationTemplateBase(name="FM", rotation_type="clinic")
        assert r.rotation_type == "outpatient"

    def test_rotation_type_alias_procedure(self):
        r = RotationTemplateBase(name="Proc", rotation_type="procedure")
        assert r.rotation_type == "outpatient"

    def test_rotation_type_alias_procedures(self):
        r = RotationTemplateBase(name="Proc", rotation_type="procedures")
        assert r.rotation_type == "outpatient"

    def test_rotation_type_invalid(self):
        with pytest.raises(ValidationError, match="rotation_type must be one of"):
            RotationTemplateBase(name="Test", rotation_type="surgery")

    # --- template_category validator ---

    def test_template_category_invalid(self):
        with pytest.raises(ValidationError, match="template_category must be"):
            RotationTemplateBase(
                name="Test", rotation_type="inpatient", template_category="clinical"
            )

    # --- model_validator: rotation category must use inpatient/outpatient ---

    def test_rotation_category_must_use_inpatient_or_outpatient(self):
        with pytest.raises(ValidationError, match="inpatient or outpatient"):
            RotationTemplateBase(
                name="Test",
                rotation_type="conference",
                template_category="rotation",
            )

    # --- max_residents validator (>= 1) ---

    def test_max_residents_zero(self):
        with pytest.raises(ValidationError, match="at least 1"):
            RotationTemplateBase(
                name="Test", rotation_type="inpatient", max_residents=0
            )

    def test_max_residents_valid(self):
        r = RotationTemplateBase(
            name="Test", rotation_type="inpatient", max_residents=5
        )
        assert r.max_residents == 5

    # --- max_supervision_ratio validator (1-10) ---

    def test_supervision_ratio_below_min(self):
        with pytest.raises(ValidationError, match="between 1 and 10"):
            RotationTemplateBase(
                name="Test", rotation_type="inpatient", max_supervision_ratio=0
            )

    def test_supervision_ratio_above_max(self):
        with pytest.raises(ValidationError, match="between 1 and 10"):
            RotationTemplateBase(
                name="Test", rotation_type="inpatient", max_supervision_ratio=11
            )


# ── RotationTemplateUpdate ─────────────────────────────────────────────


class TestRotationTemplateUpdate:
    def test_all_none(self):
        r = RotationTemplateUpdate()
        assert r.name is None
        assert r.rotation_type is None
        assert r.template_category is None

    def test_name_empty_rejected(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            RotationTemplateUpdate(name="")

    def test_name_none_ok(self):
        r = RotationTemplateUpdate(name=None)
        assert r.name is None

    def test_rotation_type_alias_on_update(self):
        r = RotationTemplateUpdate(rotation_type="clinic")
        assert r.rotation_type == "outpatient"

    def test_rotation_type_invalid_on_update(self):
        with pytest.raises(ValidationError, match="rotation_type must be one of"):
            RotationTemplateUpdate(rotation_type="surgery")

    def test_rotation_type_none_ok(self):
        r = RotationTemplateUpdate(rotation_type=None)
        assert r.rotation_type is None

    def test_template_category_invalid_on_update(self):
        with pytest.raises(ValidationError, match="template_category must be"):
            RotationTemplateUpdate(template_category="clinical")

    def test_max_residents_zero_on_update(self):
        with pytest.raises(ValidationError, match="at least 1"):
            RotationTemplateUpdate(max_residents=0)

    def test_supervision_ratio_bounds_on_update(self):
        with pytest.raises(ValidationError, match="between 1 and 10"):
            RotationTemplateUpdate(max_supervision_ratio=11)

    # --- model_validator on update (rotation category + type) ---

    def test_rotation_category_with_non_rotation_type(self):
        with pytest.raises(ValidationError, match="inpatient or outpatient"):
            RotationTemplateUpdate(
                template_category="rotation", rotation_type="conference"
            )


# ── RotationTemplateResponse ──────────────────────────────────────────


class TestRotationTemplateResponse:
    def test_defaults(self):
        r = RotationTemplateResponse(
            id=uuid4(),
            created_at=datetime(2026, 1, 15),
            name="ICU",
            rotation_type="inpatient",
        )
        assert r.is_archived is False
        assert r.archived_at is None
        assert r.archived_by is None


# ── Batch Operations ───────────────────────────────────────────────────


class TestBatchTemplateDeleteRequest:
    def test_valid(self):
        r = BatchTemplateDeleteRequest(template_ids=[uuid4()])
        assert r.dry_run is False

    def test_empty_ids(self):
        with pytest.raises(ValidationError):
            BatchTemplateDeleteRequest(template_ids=[])

    def test_too_many_ids(self):
        with pytest.raises(ValidationError):
            BatchTemplateDeleteRequest(template_ids=[uuid4() for _ in range(101)])


class TestBatchTemplateUpdateRequest:
    def test_valid(self):
        item = BatchTemplateUpdateItem(
            template_id=uuid4(), updates=RotationTemplateUpdate(name="Updated")
        )
        r = BatchTemplateUpdateRequest(templates=[item])
        assert r.dry_run is False

    def test_empty_templates(self):
        with pytest.raises(ValidationError):
            BatchTemplateUpdateRequest(templates=[])

    def test_too_many_templates(self):
        items = [
            BatchTemplateUpdateItem(
                template_id=uuid4(), updates=RotationTemplateUpdate()
            )
            for _ in range(101)
        ]
        with pytest.raises(ValidationError):
            BatchTemplateUpdateRequest(templates=items)


class TestBatchTemplateCreateRequest:
    def test_valid(self):
        tpl = RotationTemplateCreate(name="ICU", rotation_type="inpatient")
        r = BatchTemplateCreateRequest(templates=[tpl])
        assert r.dry_run is False

    def test_empty_templates(self):
        with pytest.raises(ValidationError):
            BatchTemplateCreateRequest(templates=[])


class TestBatchArchiveRequest:
    def test_valid(self):
        r = BatchArchiveRequest(template_ids=[uuid4()])
        assert r.dry_run is False

    def test_empty_ids(self):
        with pytest.raises(ValidationError):
            BatchArchiveRequest(template_ids=[])


class TestBatchRestoreRequest:
    def test_valid(self):
        r = BatchRestoreRequest(template_ids=[uuid4()])
        assert r.dry_run is False

    def test_empty_ids(self):
        with pytest.raises(ValidationError):
            BatchRestoreRequest(template_ids=[])


class TestBatchOperationResult:
    def test_defaults(self):
        r = BatchOperationResult(index=0, template_id=uuid4(), success=True)
        assert r.error is None


class TestBatchTemplateResponse:
    def test_defaults(self):
        r = BatchTemplateResponse(
            operation_type="delete", total=5, succeeded=4, failed=1
        )
        assert r.results == []
        assert r.dry_run is False
        assert r.created_ids is None


# ── Export ──────────────────────────────────────────────────────────────


class TestTemplateExportRequest:
    def test_defaults(self):
        r = TemplateExportRequest(template_ids=[uuid4()])
        assert r.include_patterns is True
        assert r.include_preferences is True

    def test_empty_ids(self):
        with pytest.raises(ValidationError):
            TemplateExportRequest(template_ids=[])


# ── Conflict Check ─────────────────────────────────────────────────────


class TestConflictCheckRequest:
    def test_valid(self):
        r = ConflictCheckRequest(template_ids=[uuid4()], operation="delete")
        assert r.operation == "delete"

    def test_empty_ids(self):
        with pytest.raises(ValidationError):
            ConflictCheckRequest(template_ids=[], operation="delete")


class TestTemplateConflict:
    def test_defaults(self):
        r = TemplateConflict(
            template_id=uuid4(),
            template_name="ICU",
            conflict_type="has_assignments",
            description="Has active assignments",
        )
        assert r.severity == "warning"
        assert r.blocking is False
