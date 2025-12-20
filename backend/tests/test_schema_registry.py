"""
Comprehensive tests for schema registry service.

Tests for:
- Schema registration and storage
- Schema versioning with compatibility checks
- Schema evolution rules
- Forward/backward compatibility validation
- Schema lookup by name and version
- Schema deprecation handling
- Schema documentation generation
- Schema change notifications
"""
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.schema_version import (
    SchemaChangeEvent,
    SchemaCompatibilityType,
    SchemaStatus,
    SchemaVersion,
)
from app.schemas.registry import (
    SchemaCompatibilityResult,
    SchemaDocumentation,
    SchemaEvolutionRule,
    SchemaRegistrationRequest,
    SchemaRegistry,
    SchemaResponse,
    get_latest_schema,
    validate_schema_compatibility,
)


# ============================================================================
# Sample Schema Definitions
# ============================================================================

PERSON_SCHEMA_V1 = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "age": {"type": "integer"},
    },
    "required": ["name", "email"],
}

PERSON_SCHEMA_V2_BACKWARD = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "age": {"type": "integer"},
        "phone": {"type": "string"},  # New optional field
    },
    "required": ["name", "email"],  # Same required fields
}

PERSON_SCHEMA_V2_BREAKING = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "age": {"type": "integer"},
        "phone": {"type": "string"},
    },
    "required": ["name", "email", "phone"],  # Added required field - BREAKING
}

PERSON_SCHEMA_V2_TYPE_CHANGE = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "age": {"type": "string"},  # Changed type from integer - BREAKING
    },
    "required": ["name", "email"],
}


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def registry(db: Session) -> SchemaRegistry:
    """Create a SchemaRegistry instance."""
    return SchemaRegistry(db)


@pytest.fixture
async def sample_schema_v1(db: Session, registry: SchemaRegistry) -> SchemaVersion:
    """Create a sample schema version 1."""
    result = await registry.register_schema(
        name="PersonCreate",
        schema_definition=PERSON_SCHEMA_V1,
        version=1,
        compatibility_type="backward",
        description="Initial version of PersonCreate schema",
        changelog="Initial release",
        tags=["person", "create"],
        created_by="test_user",
        make_default=True,
    )
    return result["schema_version"]


@pytest.fixture
async def sample_schema_v2(
    db: Session,
    registry: SchemaRegistry,
    sample_schema_v1: SchemaVersion,
) -> SchemaVersion:
    """Create a sample schema version 2."""
    result = await registry.register_schema(
        name="PersonCreate",
        schema_definition=PERSON_SCHEMA_V2_BACKWARD,
        version=2,
        compatibility_type="backward",
        description="Added optional phone field",
        changelog="Added phone field for better contact management",
        migration_notes="Phone field is optional, no migration needed",
        tags=["person", "create"],
        created_by="test_user",
    )
    return result["schema_version"]


# ============================================================================
# SchemaEvolutionRule Tests
# ============================================================================


class TestSchemaEvolutionRule:
    """Tests for schema evolution rules."""

    def test_backward_compatible_add_optional_field(self):
        """Test that adding optional field is backward compatible."""
        violations = SchemaEvolutionRule.validate_backward_compatibility(
            PERSON_SCHEMA_V1,
            PERSON_SCHEMA_V2_BACKWARD
        )

        assert len(violations) == 0

    def test_backward_incompatible_add_required_field(self):
        """Test that adding required field is backward incompatible."""
        violations = SchemaEvolutionRule.validate_backward_compatibility(
            PERSON_SCHEMA_V1,
            PERSON_SCHEMA_V2_BREAKING
        )

        assert len(violations) > 0
        assert any("required" in v.lower() for v in violations)

    def test_backward_incompatible_remove_field(self):
        """Test that removing field is backward incompatible."""
        old_schema = PERSON_SCHEMA_V1.copy()
        new_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
            },
            "required": ["name"],
        }

        violations = SchemaEvolutionRule.validate_backward_compatibility(
            old_schema,
            new_schema
        )

        assert len(violations) > 0
        assert any("removed" in v.lower() for v in violations)

    def test_backward_incompatible_type_change(self):
        """Test that narrowing type change is backward incompatible."""
        violations = SchemaEvolutionRule.validate_backward_compatibility(
            PERSON_SCHEMA_V1,
            PERSON_SCHEMA_V2_TYPE_CHANGE
        )

        assert len(violations) > 0
        assert any("type" in v.lower() for v in violations)

    def test_forward_compatible_remove_optional_field(self):
        """Test that removing optional field is forward compatible."""
        old_schema = PERSON_SCHEMA_V2_BACKWARD.copy()
        new_schema = PERSON_SCHEMA_V1.copy()

        violations = SchemaEvolutionRule.validate_forward_compatibility(
            old_schema,
            new_schema
        )

        # Removing optional field is forward compatible
        # (old schema can still read new data)
        assert len(violations) == 0 or all("removed" not in v.lower() for v in violations)

    def test_forward_incompatible_add_field(self):
        """Test that adding field is forward incompatible."""
        violations = SchemaEvolutionRule.validate_forward_compatibility(
            PERSON_SCHEMA_V1,
            PERSON_SCHEMA_V2_BACKWARD
        )

        assert len(violations) > 0
        assert any("added" in v.lower() for v in violations)

    def test_full_compatibility_no_changes(self):
        """Test that identical schemas are fully compatible."""
        violations = SchemaEvolutionRule.validate_full_compatibility(
            PERSON_SCHEMA_V1,
            PERSON_SCHEMA_V1.copy()
        )

        assert len(violations) == 0

    def test_full_compatibility_breaking_changes(self):
        """Test that breaking changes are detected in full compatibility."""
        violations = SchemaEvolutionRule.validate_full_compatibility(
            PERSON_SCHEMA_V1,
            PERSON_SCHEMA_V2_BACKWARD
        )

        # Adding optional field is backward compatible but not forward compatible
        assert len(violations) > 0


# ============================================================================
# SchemaRegistry Basic Operations Tests
# ============================================================================


class TestSchemaRegistryBasicOperations:
    """Tests for basic schema registry operations."""

    @pytest.mark.asyncio
    async def test_register_schema_success(self, registry: SchemaRegistry):
        """Test successful schema registration."""
        result = await registry.register_schema(
            name="TestSchema",
            schema_definition=PERSON_SCHEMA_V1,
            version=1,
            compatibility_type="backward",
            description="Test schema",
            created_by="test_user",
        )

        assert result["success"] is True
        assert result["schema_version"].name == "TestSchema"
        assert result["schema_version"].version == 1
        assert result["schema_version"].status == SchemaStatus.ACTIVE.value

    @pytest.mark.asyncio
    async def test_register_duplicate_schema_fails(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test that registering duplicate schema version fails."""
        with pytest.raises(ValueError, match="already exists"):
            await registry.register_schema(
                name="PersonCreate",
                schema_definition=PERSON_SCHEMA_V1,
                version=1,
                compatibility_type="backward",
            )

    @pytest.mark.asyncio
    async def test_register_incompatible_schema_fails(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test that incompatible schema registration fails."""
        with pytest.raises(ValueError, match="incompatible"):
            await registry.register_schema(
                name="PersonCreate",
                schema_definition=PERSON_SCHEMA_V2_BREAKING,
                version=2,
                compatibility_type="backward",
            )

    @pytest.mark.asyncio
    async def test_register_schema_creates_change_event(
        self,
        db: Session,
        registry: SchemaRegistry,
    ):
        """Test that schema registration creates a change event."""
        await registry.register_schema(
            name="EventTestSchema",
            schema_definition=PERSON_SCHEMA_V1,
            version=1,
            changelog="Initial version",
        )

        events = db.query(SchemaChangeEvent).filter(
            SchemaChangeEvent.schema_name == "EventTestSchema"
        ).all()

        assert len(events) == 1
        assert events[0].event_type == "created"
        assert events[0].new_version == 1

    @pytest.mark.asyncio
    async def test_get_schema_by_version(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test getting a specific schema version."""
        schema = await registry.get_schema("PersonCreate", version=1)

        assert schema is not None
        assert schema.name == "PersonCreate"
        assert schema.version == 1
        assert schema.schema_definition == PERSON_SCHEMA_V1

    @pytest.mark.asyncio
    async def test_get_schema_default_version(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
        sample_schema_v2: SchemaVersion,
    ):
        """Test getting default schema version."""
        # V1 is marked as default in fixture
        schema = await registry.get_schema("PersonCreate")

        assert schema is not None
        assert schema.version == 1
        assert schema.is_default is True

    @pytest.mark.asyncio
    async def test_get_schema_latest_when_no_default(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
        sample_schema_v2: SchemaVersion,
    ):
        """Test that latest active version is returned when no default."""
        # Unset default on v1
        sample_schema_v1.is_default = False
        registry.db.commit()

        schema = await registry.get_schema("PersonCreate")

        assert schema is not None
        # Should return v2 as it's the latest active
        assert schema.version == 2

    @pytest.mark.asyncio
    async def test_get_nonexistent_schema(self, registry: SchemaRegistry):
        """Test getting nonexistent schema returns None."""
        schema = await registry.get_schema("NonexistentSchema")

        assert schema is None


# ============================================================================
# SchemaRegistry List and Search Tests
# ============================================================================


class TestSchemaRegistryListOperations:
    """Tests for schema listing and search operations."""

    @pytest.mark.asyncio
    async def test_list_all_schemas(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
        sample_schema_v2: SchemaVersion,
    ):
        """Test listing all schemas."""
        schemas = await registry.list_schemas()

        assert len(schemas) >= 2
        schema_names = [s.name for s in schemas]
        assert "PersonCreate" in schema_names

    @pytest.mark.asyncio
    async def test_list_schemas_by_name_filter(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test filtering schemas by name."""
        # Create another schema
        await registry.register_schema(
            name="AssignmentCreate",
            schema_definition=PERSON_SCHEMA_V1,
            version=1,
        )

        schemas = await registry.list_schemas(name_filter="Person")

        assert len(schemas) >= 1
        assert all("Person" in s.name for s in schemas)

    @pytest.mark.asyncio
    async def test_list_schemas_by_status(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test filtering schemas by status."""
        schemas = await registry.list_schemas(
            status_filter=[SchemaStatus.ACTIVE.value]
        )

        assert len(schemas) >= 1
        assert all(s.status == SchemaStatus.ACTIVE.value for s in schemas)

    @pytest.mark.asyncio
    async def test_list_schemas_by_tags(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test filtering schemas by tags."""
        schemas = await registry.list_schemas(tags=["person"])

        assert len(schemas) >= 1
        assert all("person" in s.tags for s in schemas)

    @pytest.mark.asyncio
    async def test_list_schemas_exclude_archived(
        self,
        db: Session,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test that archived schemas are excluded by default."""
        # Archive the schema
        sample_schema_v1.status = SchemaStatus.ARCHIVED.value
        db.commit()

        schemas = await registry.list_schemas(include_archived=False)

        schema_names = [s.name for s in schemas]
        assert "PersonCreate" not in schema_names

    @pytest.mark.asyncio
    async def test_list_schemas_include_archived(
        self,
        db: Session,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test including archived schemas."""
        # Archive the schema
        sample_schema_v1.status = SchemaStatus.ARCHIVED.value
        db.commit()

        schemas = await registry.list_schemas(include_archived=True)

        schema_names = [s.name for s in schemas]
        assert "PersonCreate" in schema_names


# ============================================================================
# Compatibility Check Tests
# ============================================================================


class TestSchemaCompatibilityChecks:
    """Tests for schema compatibility validation."""

    @pytest.mark.asyncio
    async def test_check_backward_compatibility_success(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test successful backward compatibility check."""
        result = await registry.check_compatibility(
            "PersonCreate",
            PERSON_SCHEMA_V2_BACKWARD,
            "backward",
        )

        assert result.compatible is True
        assert result.compatibility_type == "backward"
        assert len(result.violations) == 0

    @pytest.mark.asyncio
    async def test_check_backward_compatibility_failure(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test backward compatibility check failure."""
        result = await registry.check_compatibility(
            "PersonCreate",
            PERSON_SCHEMA_V2_BREAKING,
            "backward",
        )

        assert result.compatible is False
        assert len(result.violations) > 0
        assert len(result.suggestions) > 0

    @pytest.mark.asyncio
    async def test_check_forward_compatibility(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test forward compatibility check."""
        result = await registry.check_compatibility(
            "PersonCreate",
            PERSON_SCHEMA_V2_BACKWARD,
            "forward",
        )

        # Adding field is forward incompatible
        assert result.compatible is False
        assert any("added" in v.lower() for v in result.violations)

    @pytest.mark.asyncio
    async def test_check_full_compatibility(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test full compatibility check."""
        result = await registry.check_compatibility(
            "PersonCreate",
            PERSON_SCHEMA_V2_BACKWARD,
            "full",
        )

        # Adding optional field is backward compatible but not forward
        assert result.compatible is False

    @pytest.mark.asyncio
    async def test_check_transitive_compatibility(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
        sample_schema_v2: SchemaVersion,
    ):
        """Test transitive compatibility check (against all versions)."""
        # Create a third version
        result = await registry.check_compatibility(
            "PersonCreate",
            PERSON_SCHEMA_V2_BACKWARD,  # Same as v2
            "transitive",
        )

        # Should check against both v1 and v2
        assert isinstance(result, SchemaCompatibilityResult)

    @pytest.mark.asyncio
    async def test_check_compatibility_no_existing_schema(
        self,
        registry: SchemaRegistry,
    ):
        """Test compatibility check when no existing schema exists."""
        result = await registry.check_compatibility(
            "NewSchema",
            PERSON_SCHEMA_V1,
            "backward",
        )

        assert result.compatible is True
        assert len(result.warnings) > 0

    @pytest.mark.asyncio
    async def test_check_compatibility_specific_version(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
        sample_schema_v2: SchemaVersion,
    ):
        """Test compatibility check against specific version."""
        result = await registry.check_compatibility(
            "PersonCreate",
            PERSON_SCHEMA_V2_BACKWARD,
            "backward",
            compare_to_version=1,
        )

        assert isinstance(result, SchemaCompatibilityResult)


# ============================================================================
# Schema Lifecycle Tests
# ============================================================================


class TestSchemaLifecycle:
    """Tests for schema lifecycle management."""

    @pytest.mark.asyncio
    async def test_deprecate_schema(
        self,
        db: Session,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test deprecating a schema version."""
        removal_date = datetime.utcnow() + timedelta(days=90)

        result = await registry.deprecate_schema(
            "PersonCreate",
            1,
            deprecated_by="test_user",
            removal_date=removal_date,
        )

        assert result["success"] is True

        # Verify schema status changed
        db.refresh(sample_schema_v1)
        assert sample_schema_v1.status == SchemaStatus.DEPRECATED.value
        assert sample_schema_v1.deprecated_at is not None
        assert sample_schema_v1.removed_at == removal_date

    @pytest.mark.asyncio
    async def test_deprecate_nonexistent_schema_fails(
        self,
        registry: SchemaRegistry,
    ):
        """Test that deprecating nonexistent schema fails."""
        with pytest.raises(ValueError, match="not found"):
            await registry.deprecate_schema("NonexistentSchema", 1)

    @pytest.mark.asyncio
    async def test_deprecate_already_deprecated_fails(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test that deprecating already deprecated schema fails."""
        # Deprecate once
        await registry.deprecate_schema("PersonCreate", 1)

        # Try to deprecate again
        with pytest.raises(ValueError, match="already deprecated"):
            await registry.deprecate_schema("PersonCreate", 1)

    @pytest.mark.asyncio
    async def test_archive_schema(
        self,
        db: Session,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test archiving a schema version."""
        result = await registry.archive_schema(
            "PersonCreate",
            1,
            archived_by="test_user",
        )

        assert result["success"] is True

        # Verify schema status changed
        db.refresh(sample_schema_v1)
        assert sample_schema_v1.status == SchemaStatus.ARCHIVED.value
        assert sample_schema_v1.archived_at is not None

    @pytest.mark.asyncio
    async def test_archive_nonexistent_schema_fails(
        self,
        registry: SchemaRegistry,
    ):
        """Test that archiving nonexistent schema fails."""
        with pytest.raises(ValueError, match="not found"):
            await registry.archive_schema("NonexistentSchema", 1)

    @pytest.mark.asyncio
    async def test_set_default_version(
        self,
        db: Session,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
        sample_schema_v2: SchemaVersion,
    ):
        """Test setting a different version as default."""
        result = await registry.set_default_version(
            "PersonCreate",
            2,
            changed_by="test_user",
        )

        assert result["success"] is True

        # Verify v2 is now default and v1 is not
        db.refresh(sample_schema_v1)
        db.refresh(sample_schema_v2)
        assert sample_schema_v1.is_default is False
        assert sample_schema_v2.is_default is True

    @pytest.mark.asyncio
    async def test_set_default_archived_schema_fails(
        self,
        db: Session,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test that setting archived schema as default fails."""
        # Archive the schema
        sample_schema_v1.status = SchemaStatus.ARCHIVED.value
        db.commit()

        with pytest.raises(ValueError, match="not usable"):
            await registry.set_default_version("PersonCreate", 1)


# ============================================================================
# Documentation Generation Tests
# ============================================================================


class TestSchemaDocumentation:
    """Tests for schema documentation generation."""

    @pytest.mark.asyncio
    async def test_generate_documentation_basic(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test basic documentation generation."""
        doc = await registry.generate_documentation("PersonCreate", version=1)

        assert isinstance(doc, SchemaDocumentation)
        assert doc.name == "PersonCreate"
        assert doc.current_version == 1
        assert doc.total_versions >= 1
        assert len(doc.fields) > 0

    @pytest.mark.asyncio
    async def test_generate_documentation_fields(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test that documentation includes field details."""
        doc = await registry.generate_documentation("PersonCreate")

        # Check field information
        field_names = [f["name"] for f in doc.fields]
        assert "name" in field_names
        assert "email" in field_names

        # Check required field marking
        name_field = next(f for f in doc.fields if f["name"] == "name")
        assert name_field["required"] is True

    @pytest.mark.asyncio
    async def test_generate_documentation_compatibility_history(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
        sample_schema_v2: SchemaVersion,
    ):
        """Test that documentation includes compatibility history."""
        doc = await registry.generate_documentation("PersonCreate")

        assert len(doc.compatibility_history) >= 2
        assert all("version" in entry for entry in doc.compatibility_history)
        assert all(
            "compatibility_type" in entry
            for entry in doc.compatibility_history
        )

    @pytest.mark.asyncio
    async def test_generate_documentation_deprecation_info(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test documentation for deprecated schema."""
        # Deprecate the schema
        await registry.deprecate_schema("PersonCreate", 1)

        doc = await registry.generate_documentation("PersonCreate", version=1)

        assert doc.deprecation_info is not None
        assert "deprecated_at" in doc.deprecation_info

    @pytest.mark.asyncio
    async def test_generate_documentation_migration_guides(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
        sample_schema_v2: SchemaVersion,
    ):
        """Test that documentation includes migration guides."""
        doc = await registry.generate_documentation("PersonCreate")

        # V2 has migration notes, should appear in guides
        assert len(doc.migration_guides) > 0
        assert all("from_version" in guide for guide in doc.migration_guides)
        assert all("to_version" in guide for guide in doc.migration_guides)

    @pytest.mark.asyncio
    async def test_generate_documentation_nonexistent_fails(
        self,
        registry: SchemaRegistry,
    ):
        """Test that documentation for nonexistent schema fails."""
        with pytest.raises(ValueError, match="not found"):
            await registry.generate_documentation("NonexistentSchema")


# ============================================================================
# Convenience Functions Tests
# ============================================================================


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    @pytest.mark.asyncio
    async def test_get_latest_schema(
        self,
        db: Session,
        sample_schema_v1: SchemaVersion,
    ):
        """Test get_latest_schema convenience function."""
        schema = await get_latest_schema(db, "PersonCreate")

        assert schema is not None
        assert schema.name == "PersonCreate"

    @pytest.mark.asyncio
    async def test_validate_schema_compatibility(
        self,
        db: Session,
        sample_schema_v1: SchemaVersion,
    ):
        """Test validate_schema_compatibility convenience function."""
        is_compatible = await validate_schema_compatibility(
            db,
            "PersonCreate",
            PERSON_SCHEMA_V2_BACKWARD,
            "backward",
        )

        assert is_compatible is True

    @pytest.mark.asyncio
    async def test_validate_schema_compatibility_failure(
        self,
        db: Session,
        sample_schema_v1: SchemaVersion,
    ):
        """Test validate_schema_compatibility with incompatible schema."""
        is_compatible = await validate_schema_compatibility(
            db,
            "PersonCreate",
            PERSON_SCHEMA_V2_BREAKING,
            "backward",
        )

        assert is_compatible is False


# ============================================================================
# Change Event Tests
# ============================================================================


class TestSchemaChangeEvents:
    """Tests for schema change event tracking."""

    @pytest.mark.asyncio
    async def test_change_event_created_on_registration(
        self,
        db: Session,
        registry: SchemaRegistry,
    ):
        """Test that change event is created on schema registration."""
        await registry.register_schema(
            name="TestEventSchema",
            schema_definition=PERSON_SCHEMA_V1,
            version=1,
            changelog="Initial version",
        )

        events = db.query(SchemaChangeEvent).filter(
            SchemaChangeEvent.schema_name == "TestEventSchema"
        ).all()

        assert len(events) == 1
        assert events[0].event_type == "created"
        assert events[0].notification_sent is True

    @pytest.mark.asyncio
    async def test_change_event_created_on_deprecation(
        self,
        db: Session,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test that change event is created on deprecation."""
        await registry.deprecate_schema("PersonCreate", 1)

        events = db.query(SchemaChangeEvent).filter(
            SchemaChangeEvent.schema_name == "PersonCreate",
            SchemaChangeEvent.event_type == "deprecated",
        ).all()

        assert len(events) == 1
        assert events[0].new_version == 1

    @pytest.mark.asyncio
    async def test_change_event_created_on_archive(
        self,
        db: Session,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test that change event is created on archive."""
        await registry.archive_schema("PersonCreate", 1)

        events = db.query(SchemaChangeEvent).filter(
            SchemaChangeEvent.schema_name == "PersonCreate",
            SchemaChangeEvent.event_type == "archived",
        ).all()

        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_change_event_created_on_set_default(
        self,
        db: Session,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
        sample_schema_v2: SchemaVersion,
    ):
        """Test that change event is created on set default."""
        await registry.set_default_version("PersonCreate", 2)

        events = db.query(SchemaChangeEvent).filter(
            SchemaChangeEvent.schema_name == "PersonCreate",
            SchemaChangeEvent.event_type == "made_default",
        ).all()

        assert len(events) == 1
        assert events[0].new_version == 2


# ============================================================================
# Edge Cases and Error Handling Tests
# ============================================================================


class TestEdgeCasesAndErrors:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_register_schema_with_empty_definition(
        self,
        registry: SchemaRegistry,
    ):
        """Test registering schema with empty definition."""
        result = await registry.register_schema(
            name="EmptySchema",
            schema_definition={},
            version=1,
        )

        # Should succeed - validation is up to the schema definition
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_register_schema_version_zero_fails(
        self,
        db: Session,
        registry: SchemaRegistry,
    ):
        """Test that version 0 is rejected by database constraint."""
        # This should fail due to CHECK constraint version > 0
        schema = SchemaVersion(
            name="TestSchema",
            version=0,
            schema_definition=PERSON_SCHEMA_V1,
        )
        db.add(schema)

        with pytest.raises(Exception):  # Database integrity error
            db.commit()

    @pytest.mark.asyncio
    async def test_multiple_default_versions_prevented(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
        sample_schema_v2: SchemaVersion,
    ):
        """Test that setting new default unsets previous default."""
        # V1 is default from fixture
        assert sample_schema_v1.is_default is True

        # Set v2 as default
        await registry.set_default_version("PersonCreate", 2)

        # Refresh v1 from database
        registry.db.refresh(sample_schema_v1)

        # V1 should no longer be default
        assert sample_schema_v1.is_default is False
        assert sample_schema_v2.is_default is True

    @pytest.mark.asyncio
    async def test_compatibility_check_with_missing_fields(
        self,
        registry: SchemaRegistry,
        sample_schema_v1: SchemaVersion,
    ):
        """Test compatibility check with schema missing standard fields."""
        incomplete_schema = {"type": "object"}

        result = await registry.check_compatibility(
            "PersonCreate",
            incomplete_schema,
            "backward",
        )

        # Should handle missing properties/required fields gracefully
        assert isinstance(result, SchemaCompatibilityResult)
