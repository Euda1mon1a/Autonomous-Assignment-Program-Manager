"""Tests for registry schemas and SchemaEvolutionRule (pure logic, no DB)."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.registry import (
    SchemaRegistrationRequest,
    SchemaResponse,
    SchemaCompatibilityResult,
    SchemaDocumentation,
    SchemaEvolutionRule,
)


# ── SchemaRegistrationRequest ────────────────────────────────────────


class TestSchemaRegistrationRequest:
    def test_defaults(self):
        r = SchemaRegistrationRequest(
            name="PersonCreate",
            version=1,
            schema_definition={"type": "object", "properties": {}},
        )
        assert r.compatibility_type == "backward"
        assert r.description is None
        assert r.changelog is None
        assert r.migration_notes is None
        assert r.tags == []
        assert r.created_by is None

    # --- version (gt=0) ---

    def test_version_zero(self):
        with pytest.raises(ValidationError):
            SchemaRegistrationRequest(
                name="Test",
                version=0,
                schema_definition={"type": "object"},
            )

    def test_version_negative(self):
        with pytest.raises(ValidationError):
            SchemaRegistrationRequest(
                name="Test",
                version=-1,
                schema_definition={"type": "object"},
            )


# ── SchemaResponse ───────────────────────────────────────────────────


class TestSchemaResponse:
    def test_defaults(self):
        r = SchemaResponse(
            id=uuid4(),
            name="PersonCreate",
            version=1,
            schema_definition={"type": "object"},
            compatibility_type="backward",
            status="active",
            is_default=True,
            tags=["core"],
            created_at=datetime(2026, 1, 15),
            updated_at=datetime(2026, 1, 15),
        )
        assert r.deprecated_at is None
        assert r.archived_at is None
        assert r.removed_at is None
        assert r.description is None
        assert r.changelog is None
        assert r.migration_notes is None
        assert r.created_by is None


# ── SchemaCompatibilityResult ────────────────────────────────────────


class TestSchemaCompatibilityResult:
    def test_defaults(self):
        r = SchemaCompatibilityResult(compatible=True, compatibility_type="backward")
        assert r.violations == []
        assert r.warnings == []
        assert r.suggestions == []


# ── SchemaDocumentation ──────────────────────────────────────────────


class TestSchemaDocumentation:
    def test_defaults(self):
        r = SchemaDocumentation(
            name="PersonCreate",
            current_version=2,
            total_versions=2,
            description="Person schema",
            fields=[],
            compatibility_history=[],
            deprecation_info=None,
        )
        assert r.examples == []
        assert r.migration_guides == []


# ── SchemaEvolutionRule (pure logic) ─────────────────────────────────


class TestSchemaEvolutionRuleBackward:
    """Test backward compatibility validation."""

    def test_identical_schemas_compatible(self):
        schema = {
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            "required": ["name"],
        }
        violations = SchemaEvolutionRule.validate_backward_compatibility(schema, schema)
        assert violations == []

    def test_adding_optional_field_compatible(self):
        old = {
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        new = {
            "properties": {"name": {"type": "string"}, "email": {"type": "string"}},
            "required": ["name"],
        }
        violations = SchemaEvolutionRule.validate_backward_compatibility(old, new)
        assert violations == []

    def test_removing_field_incompatible(self):
        old = {
            "properties": {"name": {"type": "string"}, "email": {"type": "string"}},
            "required": ["name"],
        }
        new = {
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        violations = SchemaEvolutionRule.validate_backward_compatibility(old, new)
        assert len(violations) == 1
        assert "Removed fields" in violations[0]

    def test_adding_required_field_incompatible(self):
        old = {
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        new = {
            "properties": {"name": {"type": "string"}, "email": {"type": "string"}},
            "required": ["name", "email"],
        }
        violations = SchemaEvolutionRule.validate_backward_compatibility(old, new)
        assert len(violations) == 1
        assert "Added required fields" in violations[0]

    def test_type_narrowing_incompatible(self):
        old = {
            "properties": {"score": {"type": "number"}},
            "required": [],
        }
        new = {
            "properties": {"score": {"type": "integer"}},
            "required": [],
        }
        violations = SchemaEvolutionRule.validate_backward_compatibility(old, new)
        assert len(violations) == 1
        assert "Type changed" in violations[0]

    def test_type_widening_compatible(self):
        old = {
            "properties": {"score": {"type": "integer"}},
            "required": [],
        }
        new = {
            "properties": {"score": {"type": "number"}},
            "required": [],
        }
        violations = SchemaEvolutionRule.validate_backward_compatibility(old, new)
        assert violations == []


class TestSchemaEvolutionRuleForward:
    """Test forward compatibility validation."""

    def test_identical_schemas_compatible(self):
        schema = {
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        violations = SchemaEvolutionRule.validate_forward_compatibility(schema, schema)
        assert violations == []

    def test_adding_field_incompatible(self):
        old = {
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        new = {
            "properties": {"name": {"type": "string"}, "email": {"type": "string"}},
            "required": ["name"],
        }
        violations = SchemaEvolutionRule.validate_forward_compatibility(old, new)
        assert len(violations) == 1
        assert "Added fields" in violations[0]

    def test_removing_required_constraint_incompatible(self):
        old = {
            "properties": {"name": {"type": "string"}, "email": {"type": "string"}},
            "required": ["name", "email"],
        }
        new = {
            "properties": {"name": {"type": "string"}, "email": {"type": "string"}},
            "required": ["name"],
        }
        violations = SchemaEvolutionRule.validate_forward_compatibility(old, new)
        assert len(violations) == 1
        assert "Removed required constraints" in violations[0]


class TestSchemaEvolutionRuleFull:
    """Test full (backward + forward) compatibility."""

    def test_identical_schemas_compatible(self):
        schema = {
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        violations = SchemaEvolutionRule.validate_full_compatibility(schema, schema)
        assert violations == []

    def test_adding_field_shows_forward_violation(self):
        old = {"properties": {"name": {"type": "string"}}, "required": []}
        new = {
            "properties": {"name": {"type": "string"}, "email": {"type": "string"}},
            "required": [],
        }
        violations = SchemaEvolutionRule.validate_full_compatibility(old, new)
        assert any("Forward incompatible" in v for v in violations)

    def test_removing_field_shows_backward_violation(self):
        old = {
            "properties": {"name": {"type": "string"}, "email": {"type": "string"}},
            "required": [],
        }
        new = {"properties": {"name": {"type": "string"}}, "required": []}
        violations = SchemaEvolutionRule.validate_full_compatibility(old, new)
        assert any("Backward incompatible" in v for v in violations)


class TestSchemaEvolutionRuleTypeWidening:
    """Test _is_type_widening static method."""

    def test_integer_to_number_is_widening(self):
        assert SchemaEvolutionRule._is_type_widening("integer", "number") is True

    def test_number_to_integer_is_not_widening(self):
        assert SchemaEvolutionRule._is_type_widening("number", "integer") is False

    def test_string_to_number_is_not_widening(self):
        assert SchemaEvolutionRule._is_type_widening("string", "number") is False

    def test_same_type_is_not_widening(self):
        assert SchemaEvolutionRule._is_type_widening("string", "string") is False

    def test_unknown_type_is_not_widening(self):
        assert SchemaEvolutionRule._is_type_widening("unknown", "string") is False
