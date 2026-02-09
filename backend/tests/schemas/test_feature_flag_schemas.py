"""Tests for feature flag schemas (Pydantic validation and field_validator coverage)."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.feature_flag import (
    FeatureFlagBase,
    FeatureFlagCreate,
    FeatureFlagUpdate,
    FeatureFlagResponse,
    FeatureFlagEvaluationRequest,
    FeatureFlagEvaluationResponse,
    FeatureFlagBulkEvaluationRequest,
    FeatureFlagBulkEvaluationResponse,
    FeatureFlagAuditResponse,
    FeatureFlagStatsResponse,
    FeatureFlagListResponse,
)


# ===========================================================================
# FeatureFlagBase Tests
# ===========================================================================


class TestFeatureFlagBase:
    def _valid_kwargs(self):
        return {"key": "dark_mode", "name": "Dark Mode"}

    def test_valid_minimal(self):
        r = FeatureFlagBase(**self._valid_kwargs())
        assert r.flag_type == "boolean"
        assert r.enabled is False
        assert r.rollout_percentage is None
        assert r.environments is None
        assert r.target_user_ids is None
        assert r.target_roles is None
        assert r.variants is None
        assert r.dependencies is None
        assert r.custom_attributes is None

    def test_key_empty(self):
        with pytest.raises(ValidationError):
            FeatureFlagBase(key="", name="Test")

    def test_key_too_long(self):
        with pytest.raises(ValidationError):
            FeatureFlagBase(key="x" * 101, name="Test")

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            FeatureFlagBase(key="test", name="")

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            FeatureFlagBase(key="test", name="x" * 256)

    # --- flag_type validator ---

    def test_valid_flag_types(self):
        for ft in ["boolean", "percentage", "variant"]:
            r = FeatureFlagBase(key="test", name="Test", flag_type=ft)
            assert r.flag_type == ft

    def test_invalid_flag_type(self):
        with pytest.raises(ValidationError):
            FeatureFlagBase(key="test", name="Test", flag_type="toggle")

    # --- rollout_percentage ---

    def test_rollout_percentage_boundaries(self):
        r = FeatureFlagBase(key="test", name="Test", rollout_percentage=0.0)
        assert r.rollout_percentage == 0.0
        r = FeatureFlagBase(key="test", name="Test", rollout_percentage=1.0)
        assert r.rollout_percentage == 1.0

    def test_rollout_percentage_above_one(self):
        with pytest.raises(ValidationError):
            FeatureFlagBase(key="test", name="Test", rollout_percentage=1.1)

    def test_rollout_percentage_negative(self):
        with pytest.raises(ValidationError):
            FeatureFlagBase(key="test", name="Test", rollout_percentage=-0.1)

    # --- variants validator ---

    def test_valid_variants(self):
        r = FeatureFlagBase(
            key="test",
            name="Test",
            flag_type="variant",
            variants={"control": 0.5, "treatment": 0.5},
        )
        assert r.variants == {"control": 0.5, "treatment": 0.5}

    def test_variants_sum_not_one(self):
        with pytest.raises(ValidationError):
            FeatureFlagBase(
                key="test",
                name="Test",
                variants={"a": 0.3, "b": 0.3},
            )

    def test_variants_weight_above_one(self):
        with pytest.raises(ValidationError):
            FeatureFlagBase(
                key="test",
                name="Test",
                variants={"a": 1.5, "b": -0.5},
            )

    def test_variants_none_is_valid(self):
        r = FeatureFlagBase(key="test", name="Test", variants=None)
        assert r.variants is None

    def test_variants_three_way_split(self):
        r = FeatureFlagBase(
            key="test",
            name="Test",
            variants={"a": 0.34, "b": 0.33, "c": 0.33},
        )
        assert len(r.variants) == 3

    # --- environments validator ---

    def test_valid_environments(self):
        for env in ["development", "staging", "production", "test"]:
            r = FeatureFlagBase(key="test", name="Test", environments=[env])
            assert r.environments == [env]

    def test_invalid_environment(self):
        with pytest.raises(ValidationError):
            FeatureFlagBase(key="test", name="Test", environments=["alpha"])

    def test_multiple_environments(self):
        r = FeatureFlagBase(
            key="test",
            name="Test",
            environments=["development", "staging"],
        )
        assert len(r.environments) == 2

    def test_environments_none_is_valid(self):
        r = FeatureFlagBase(key="test", name="Test", environments=None)
        assert r.environments is None

    # --- target_roles validator ---

    def test_valid_roles(self):
        valid_roles = [
            "admin",
            "coordinator",
            "faculty",
            "clinical_staff",
            "rn",
            "lpn",
            "msa",
            "resident",
        ]
        for role in valid_roles:
            r = FeatureFlagBase(key="test", name="Test", target_roles=[role])
            assert r.target_roles == [role]

    def test_invalid_role(self):
        with pytest.raises(ValidationError):
            FeatureFlagBase(key="test", name="Test", target_roles=["superadmin"])

    def test_multiple_roles(self):
        r = FeatureFlagBase(
            key="test",
            name="Test",
            target_roles=["admin", "coordinator"],
        )
        assert len(r.target_roles) == 2


# ===========================================================================
# FeatureFlagCreate Tests
# ===========================================================================


class TestFeatureFlagCreate:
    def test_inherits_from_base(self):
        r = FeatureFlagCreate(key="new_feature", name="New Feature")
        assert r.flag_type == "boolean"
        assert r.enabled is False

    def test_full_create(self):
        r = FeatureFlagCreate(
            key="ab_test",
            name="A/B Test",
            flag_type="variant",
            enabled=True,
            variants={"control": 0.5, "treatment": 0.5},
            environments=["production"],
            target_roles=["faculty", "resident"],
        )
        assert r.enabled is True


# ===========================================================================
# FeatureFlagUpdate Tests
# ===========================================================================


class TestFeatureFlagUpdate:
    def test_all_none(self):
        r = FeatureFlagUpdate()
        assert r.name is None
        assert r.flag_type is None
        assert r.enabled is None

    def test_name_validation(self):
        r = FeatureFlagUpdate(name="Valid Name")
        assert r.name == "Valid Name"

        with pytest.raises(ValidationError):
            FeatureFlagUpdate(name="")

    def test_rollout_percentage_boundaries(self):
        r = FeatureFlagUpdate(rollout_percentage=0.0)
        assert r.rollout_percentage == 0.0
        r = FeatureFlagUpdate(rollout_percentage=1.0)
        assert r.rollout_percentage == 1.0

    def test_rollout_percentage_above_one(self):
        with pytest.raises(ValidationError):
            FeatureFlagUpdate(rollout_percentage=1.1)

    def test_flag_type_validator(self):
        r = FeatureFlagUpdate(flag_type="percentage")
        assert r.flag_type == "percentage"

        with pytest.raises(ValidationError):
            FeatureFlagUpdate(flag_type="invalid")

    def test_flag_type_none_is_valid(self):
        r = FeatureFlagUpdate(flag_type=None)
        assert r.flag_type is None

    def test_variants_validator(self):
        r = FeatureFlagUpdate(variants={"a": 0.5, "b": 0.5})
        assert r.variants is not None

        with pytest.raises(ValidationError):
            FeatureFlagUpdate(variants={"a": 0.3, "b": 0.3})

    def test_environments_validator(self):
        r = FeatureFlagUpdate(environments=["production"])
        assert r.environments == ["production"]

        with pytest.raises(ValidationError):
            FeatureFlagUpdate(environments=["invalid"])


# ===========================================================================
# FeatureFlagResponse Tests
# ===========================================================================


class TestFeatureFlagResponse:
    def test_valid(self):
        r = FeatureFlagResponse(
            id=uuid4(),
            key="dark_mode",
            name="Dark Mode",
            created_by=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert r.flag_type == "boolean"


# ===========================================================================
# Evaluation Schemas Tests
# ===========================================================================


class TestFeatureFlagEvaluationRequest:
    def test_valid(self):
        r = FeatureFlagEvaluationRequest(flag_key="dark_mode")
        assert r.user_id is None
        assert r.user_role is None
        assert r.environment is None
        assert r.context is None

    def test_with_context(self):
        r = FeatureFlagEvaluationRequest(
            flag_key="experiment",
            user_id="user123",
            user_role="faculty",
            environment="production",
            context={"department": "medicine"},
        )
        assert r.context["department"] == "medicine"


class TestFeatureFlagEvaluationResponse:
    def test_valid(self):
        r = FeatureFlagEvaluationResponse(
            enabled=True,
            flag_type="boolean",
        )
        assert r.variant is None
        assert r.reason is None

    def test_variant_response(self):
        r = FeatureFlagEvaluationResponse(
            enabled=True,
            variant="treatment",
            flag_type="variant",
            reason="User in treatment group",
        )
        assert r.variant == "treatment"


class TestFeatureFlagBulkEvaluationRequest:
    def test_valid(self):
        r = FeatureFlagBulkEvaluationRequest(flag_keys=["dark_mode", "new_scheduler"])
        assert len(r.flag_keys) == 2


class TestFeatureFlagBulkEvaluationResponse:
    def test_valid(self):
        eval_result = FeatureFlagEvaluationResponse(enabled=True, flag_type="boolean")
        r = FeatureFlagBulkEvaluationResponse(flags={"dark_mode": eval_result})
        assert r.flags["dark_mode"].enabled is True


# ===========================================================================
# Audit and Stats Tests
# ===========================================================================


class TestFeatureFlagAuditResponse:
    def test_valid(self):
        r = FeatureFlagAuditResponse(
            id=uuid4(),
            flag_id=uuid4(),
            user_id=uuid4(),
            username="admin",
            action="enable",
            changes={"enabled": True},
            reason="Rolling out to production",
            created_at=datetime.now(),
        )
        assert r.action == "enable"


class TestFeatureFlagStatsResponse:
    def test_valid(self):
        r = FeatureFlagStatsResponse(
            total_flags=10,
            enabled_flags=7,
            disabled_flags=3,
            percentage_rollout_flags=2,
            variant_flags=1,
            flags_by_environment={"production": 5, "staging": 3},
            recent_evaluations=1000,
            unique_users=50,
        )
        assert r.total_flags == 10


class TestFeatureFlagListResponse:
    def test_valid(self):
        r = FeatureFlagListResponse(
            flags=[],
            total=0,
            page=1,
            page_size=20,
            total_pages=0,
        )
        assert r.total == 0
