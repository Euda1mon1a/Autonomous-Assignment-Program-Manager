"""
Tests for Constraint Registry

Tests for constraint registration, discovery, versioning, and deprecation.
"""

import pytest

from app.scheduling.constraint_registry import (
    ConstraintMetadata,
    ConstraintRegistry,
)
from app.scheduling.constraints.acgme import AvailabilityConstraint
from app.scheduling.constraints.base import ConstraintType, HardConstraint


class TestConstraintMetadata:
    """Tests for ConstraintMetadata."""

    def test_metadata_initialization(self):
        """Test metadata initializes correctly."""
        metadata = ConstraintMetadata(
            name="TestConstraint",
            version="1.0",
            constraint_class=AvailabilityConstraint,
            category="CUSTOM",
        )

        assert metadata.name == "TestConstraint"
        assert metadata.version == "1.0"
        assert metadata.category == "CUSTOM"
        assert not metadata.is_deprecated
        assert metadata.is_enabled

    def test_metadata_is_active(self):
        """Test is_active method."""
        metadata = ConstraintMetadata(
            name="Test",
            version="1.0",
            constraint_class=AvailabilityConstraint,
            category="CUSTOM",
        )

        assert metadata.is_active()

        # Deprecate
        metadata.is_deprecated = True
        assert not metadata.is_active()

        # Re-enable
        metadata.is_deprecated = False
        assert metadata.is_active()

        # Disable
        metadata.is_enabled = False
        assert not metadata.is_active()

    def test_metadata_get_deprecation_info(self):
        """Test getting deprecation information."""
        metadata = ConstraintMetadata(
            name="OldConstraint",
            version="1.0",
            constraint_class=AvailabilityConstraint,
            category="CUSTOM",
            is_deprecated=True,
            deprecation_message="Use NewConstraint instead",
            replacement_constraint="NewConstraint",
        )

        info = metadata.get_deprecation_info()
        assert info is not None
        assert info["message"] == "Use NewConstraint instead"
        assert info["replacement"] == "NewConstraint"


class TestConstraintRegistry:
    """Tests for ConstraintRegistry."""

    def setup_method(self):
        """Clear registry before each test."""
        ConstraintRegistry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        ConstraintRegistry.clear()

    def test_registry_singleton(self):
        """Test registry is singleton."""
        registry1 = ConstraintRegistry()
        registry2 = ConstraintRegistry()
        assert registry1 is registry2

    def test_register_constraint(self):
        """Test registering a constraint."""
        @ConstraintRegistry.register(
            name="TestConstraint",
            version="1.0",
            category="CUSTOM",
        )
        class TestConstraint(HardConstraint):
            pass

        # Should be registered
        constraint_class = ConstraintRegistry.get("TestConstraint")
        assert constraint_class is TestConstraint

    def test_get_by_latest_version(self):
        """Test getting constraint by latest version."""
        @ConstraintRegistry.register(
            name="Versioned",
            version="1.0",
            category="CUSTOM",
        )
        class VersionedV1(HardConstraint):
            pass

        @ConstraintRegistry.register(
            name="Versioned",
            version="2.0",
            category="CUSTOM",
        )
        class VersionedV2(HardConstraint):
            pass

        # Get without version should return latest (2.0)
        constraint_class = ConstraintRegistry.get("Versioned")
        assert constraint_class is VersionedV2

    def test_get_specific_version(self):
        """Test getting constraint by specific version."""
        @ConstraintRegistry.register(
            name="Versioned",
            version="1.0",
            category="CUSTOM",
        )
        class VersionedV1(HardConstraint):
            pass

        @ConstraintRegistry.register(
            name="Versioned",
            version="2.0",
            category="CUSTOM",
        )
        class VersionedV2(HardConstraint):
            pass

        # Get v1.0 specifically
        constraint_class = ConstraintRegistry.get("Versioned", "1.0")
        assert constraint_class is VersionedV1

    def test_get_metadata(self):
        """Test getting constraint metadata."""
        @ConstraintRegistry.register(
            name="Test",
            version="1.0",
            category="CUSTOM",
            description="Test constraint",
        )
        class TestConstraint(HardConstraint):
            pass

        metadata = ConstraintRegistry.get_metadata("Test")
        assert metadata is not None
        assert metadata.name == "Test"
        assert metadata.description == "Test constraint"

    def test_get_all_constraints(self):
        """Test getting all constraints."""
        @ConstraintRegistry.register(
            name="Constraint1",
            version="1.0",
            category="CUSTOM",
        )
        class Constraint1(HardConstraint):
            pass

        @ConstraintRegistry.register(
            name="Constraint2",
            version="1.0",
            category="CUSTOM",
        )
        class Constraint2(HardConstraint):
            pass

        all_constraints = ConstraintRegistry.get_all()
        assert len(all_constraints) >= 2

    def test_get_all_active_only(self):
        """Test getting only active constraints."""
        @ConstraintRegistry.register(
            name="Active",
            version="1.0",
            category="CUSTOM",
        )
        class ActiveConstraint(HardConstraint):
            pass

        @ConstraintRegistry.register(
            name="Deprecated",
            version="1.0",
            category="CUSTOM",
        )
        class DeprecatedConstraint(HardConstraint):
            pass

        # Deprecate one
        ConstraintRegistry.deprecate("Deprecated", "Use Active instead")

        active = ConstraintRegistry.get_all(active_only=True)
        deprecated = ConstraintRegistry.get_all(active_only=False)

        assert len(deprecated) > len(active)

    def test_find_by_category(self):
        """Test finding constraints by category."""
        @ConstraintRegistry.register(
            name="CustomConstraint",
            version="1.0",
            category="CUSTOM",
        )
        class CustomConstraint(HardConstraint):
            pass

        results = ConstraintRegistry.find(category="CUSTOM")
        assert any(m.name == "CustomConstraint" for m in results)

    def test_find_by_tag(self):
        """Test finding constraints by tag."""
        @ConstraintRegistry.register(
            name="Tagged",
            version="1.0",
            category="CUSTOM",
            tags=["test", "experimental"],
        )
        class TaggedConstraint(HardConstraint):
            pass

        results = ConstraintRegistry.find(tag="experimental")
        assert any(m.name == "Tagged" for m in results)

    def test_find_by_constraint_type(self):
        """Test finding constraints by type."""
        @ConstraintRegistry.register(
            name="CapacityConstraint",
            version="1.0",
            category="CUSTOM",
            constraint_types=[ConstraintType.CAPACITY],
        )
        class CapacityConstraint(HardConstraint):
            pass

        results = ConstraintRegistry.find(constraint_type=ConstraintType.CAPACITY)
        assert any(m.name == "CapacityConstraint" for m in results)

    def test_deprecate_constraint(self):
        """Test deprecating a constraint."""
        @ConstraintRegistry.register(
            name="OldConstraint",
            version="1.0",
            category="CUSTOM",
        )
        class OldConstraint(HardConstraint):
            pass

        ConstraintRegistry.deprecate(
            "OldConstraint",
            "Use NewConstraint instead",
            replacement="NewConstraint",
        )

        metadata = ConstraintRegistry.get_metadata("OldConstraint")
        assert metadata.is_deprecated
        assert metadata.replacement_constraint == "NewConstraint"

    def test_enable_disable_constraint(self):
        """Test enabling and disabling constraints."""
        @ConstraintRegistry.register(
            name="Toggle",
            version="1.0",
            category="CUSTOM",
        )
        class ToggleConstraint(HardConstraint):
            pass

        # Disable
        ConstraintRegistry.disable("Toggle")
        metadata = ConstraintRegistry.get_metadata("Toggle")
        assert not metadata.is_enabled

        # Enable
        ConstraintRegistry.enable("Toggle")
        metadata = ConstraintRegistry.get_metadata("Toggle")
        assert metadata.is_enabled

    def test_list_by_category(self):
        """Test listing constraints by category."""
        @ConstraintRegistry.register(
            name="Acgme",
            version="1.0",
            category="ACGME",
        )
        class AcgmeConstraint(HardConstraint):
            pass

        @ConstraintRegistry.register(
            name="Capacity",
            version="1.0",
            category="CAPACITY",
        )
        class CapacityConstraint(HardConstraint):
            pass

        by_category = ConstraintRegistry.list_by_category()
        assert "ACGME" in by_category
        assert "CAPACITY" in by_category

    def test_get_category_stats(self):
        """Test getting category statistics."""
        @ConstraintRegistry.register(
            name="Constraint1",
            version="1.0",
            category="CUSTOM",
        )
        class Constraint1(HardConstraint):
            pass

        @ConstraintRegistry.register(
            name="Constraint2",
            version="1.0",
            category="CUSTOM",
        )
        class Constraint2(HardConstraint):
            pass

        stats = ConstraintRegistry.get_category_stats()
        assert "CUSTOM" in stats
        assert stats["CUSTOM"] >= 2

    def test_get_status_report(self):
        """Test getting status report."""
        @ConstraintRegistry.register(
            name="ReportTest",
            version="1.0",
            category="CUSTOM",
        )
        class ReportTestConstraint(HardConstraint):
            pass

        report = ConstraintRegistry.get_status_report()
        assert "Constraint Registry Status Report" in report
        assert "Total Constraints" in report

    def test_clear_registry(self):
        """Test clearing registry."""
        @ConstraintRegistry.register(
            name="ToClear",
            version="1.0",
            category="CUSTOM",
        )
        class ToClearConstraint(HardConstraint):
            pass

        ConstraintRegistry.clear()

        # Should be empty
        all_constraints = ConstraintRegistry.get_all()
        assert len(all_constraints) == 0

    def test_multiple_versions_tracking(self):
        """Test tracking multiple constraint versions."""
        @ConstraintRegistry.register(
            name="Evolving",
            version="1.0",
            category="CUSTOM",
        )
        class EvolvedV1(HardConstraint):
            pass

        @ConstraintRegistry.register(
            name="Evolving",
            version="2.0",
            category="CUSTOM",
        )
        class EvolvedV2(HardConstraint):
            pass

        @ConstraintRegistry.register(
            name="Evolving",
            version="3.0",
            category="CUSTOM",
        )
        class EvolvedV3(HardConstraint):
            pass

        # All should be retrievable
        assert ConstraintRegistry.get("Evolving", "1.0") is EvolvedV1
        assert ConstraintRegistry.get("Evolving", "2.0") is EvolvedV2
        assert ConstraintRegistry.get("Evolving", "3.0") is EvolvedV3

        # Latest should be v3
        assert ConstraintRegistry.get("Evolving") is EvolvedV3
