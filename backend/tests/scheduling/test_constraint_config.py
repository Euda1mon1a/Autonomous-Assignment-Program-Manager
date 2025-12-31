"""
Tests for Constraint Configuration System

Tests the constraint configuration manager, presets, and enable/disable logic.
"""

import pytest

from app.scheduling.constraints.config import (
    ConstraintCategory,
    ConstraintConfig,
    ConstraintConfigManager,
    ConstraintPriorityLevel,
    get_constraint_config,
    reset_constraint_config,
)


class TestConstraintConfig:
    """Test ConstraintConfig dataclass."""

    def test_constraint_config_defaults(self):
        """Test ConstraintConfig default values."""
        config = ConstraintConfig(name="TestConstraint")

        assert config.name == "TestConstraint"
        assert config.enabled is True
        assert config.priority == ConstraintPriorityLevel.MEDIUM
        assert config.weight == 1.0
        assert config.category == ConstraintCategory.COVERAGE
        assert config.dependencies == []
        assert config.conflicts_with == []

    def test_constraint_config_is_active(self):
        """Test is_active() method."""
        enabled = ConstraintConfig(name="Test", enabled=True)
        disabled = ConstraintConfig(name="Test", enabled=False)

        assert enabled.is_active() is True
        assert disabled.is_active() is False

    def test_constraint_config_should_enable(self):
        """Test should_enable() with dependencies."""
        ***REMOVED*** No dependencies - should enable
        config = ConstraintConfig(name="Test", enabled=True)
        assert config.should_enable({}) is True

        ***REMOVED*** With dependencies - enabled
        config = ConstraintConfig(
            name="Test",
            enabled=True,
            dependencies=["Dep1"],
        )
        assert config.should_enable({"Dep1_enabled": True}) is True

        ***REMOVED*** With dependencies - disabled
        assert config.should_enable({"Dep1_enabled": False}) is False

        ***REMOVED*** Disabled constraint
        config = ConstraintConfig(name="Test", enabled=False)
        assert config.should_enable({}) is False


class TestConstraintConfigManager:
    """Test ConstraintConfigManager."""

    @pytest.fixture(autouse=True)
    def reset_config(self):
        """Reset configuration before each test."""
        reset_constraint_config()
        yield
        reset_constraint_config()

    def test_manager_initialization(self):
        """Test manager initializes with default configs."""
        manager = ConstraintConfigManager()

        ***REMOVED*** Check ACGME constraints are initialized
        assert manager.get("Availability") is not None
        assert manager.get("EightyHourRule") is not None
        assert manager.get("OneInSevenRule") is not None
        assert manager.get("SupervisionRatio") is not None

        ***REMOVED*** Check they are enabled by default
        assert manager.is_enabled("Availability") is True
        assert manager.is_enabled("EightyHourRule") is True

    def test_get_constraint_config(self):
        """Test get() method."""
        manager = ConstraintConfigManager()

        ***REMOVED*** Get existing constraint
        config = manager.get("Availability")
        assert config is not None
        assert config.name == "Availability"

        ***REMOVED*** Get non-existent constraint
        config = manager.get("NonExistent")
        assert config is None

    def test_is_enabled(self):
        """Test is_enabled() method."""
        manager = ConstraintConfigManager()

        ***REMOVED*** Enabled constraint
        assert manager.is_enabled("Availability") is True

        ***REMOVED*** Disabled constraint
        assert manager.is_enabled("OvernightCallGeneration") is False

        ***REMOVED*** Non-existent constraint
        assert manager.is_enabled("NonExistent") is False

    def test_enable_constraint(self):
        """Test enable() method."""
        manager = ConstraintConfigManager()

        ***REMOVED*** Initially disabled
        assert manager.is_enabled("OvernightCallGeneration") is False

        ***REMOVED*** Enable it
        result = manager.enable("OvernightCallGeneration")
        assert result is True
        assert manager.is_enabled("OvernightCallGeneration") is True

        ***REMOVED*** Enable non-existent constraint
        result = manager.enable("NonExistent")
        assert result is False

    def test_disable_constraint(self):
        """Test disable() method."""
        manager = ConstraintConfigManager()

        ***REMOVED*** Initially enabled
        assert manager.is_enabled("Availability") is True

        ***REMOVED*** Disable it
        result = manager.disable("Availability")
        assert result is True
        assert manager.is_enabled("Availability") is False

        ***REMOVED*** Disable non-existent constraint
        result = manager.disable("NonExistent")
        assert result is False

    def test_get_enabled_by_category(self):
        """Test get_enabled_by_category() method."""
        manager = ConstraintConfigManager()

        ***REMOVED*** Get ACGME constraints
        acgme = manager.get_enabled_by_category(ConstraintCategory.ACGME)
        assert len(acgme) == 4  ***REMOVED*** All 4 ACGME constraints enabled by default
        assert all(c.category == ConstraintCategory.ACGME for c in acgme)
        assert all(c.enabled for c in acgme)

        ***REMOVED*** Get CALL constraints (should be empty - all disabled by default)
        call = manager.get_enabled_by_category(ConstraintCategory.CALL)
        assert len(call) == 0

    def test_get_all_enabled(self):
        """Test get_all_enabled() method."""
        manager = ConstraintConfigManager()

        enabled = manager.get_all_enabled()

        ***REMOVED*** Should have at least ACGME, CAPACITY, COVERAGE, EQUITY enabled
        assert len(enabled) >= 10

        ***REMOVED*** All should be enabled
        assert all(c.enabled for c in enabled)

    def test_get_all_disabled(self):
        """Test get_all_disabled() method."""
        manager = ConstraintConfigManager()

        disabled = manager.get_all_disabled()

        ***REMOVED*** Should have call, FMIT, SM, and tier 2 resilience disabled
        assert len(disabled) >= 7

        ***REMOVED*** All should be disabled
        assert all(not c.enabled for c in disabled)

    def test_apply_minimal_preset(self):
        """Test minimal preset."""
        manager = ConstraintConfigManager()

        ***REMOVED*** Apply minimal preset
        manager.apply_preset("minimal")

        ***REMOVED*** ACGME should still be enabled
        assert manager.is_enabled("Availability") is True
        assert manager.is_enabled("EightyHourRule") is True

        ***REMOVED*** Continuity should be disabled in minimal
        assert manager.is_enabled("Continuity") is False

        ***REMOVED*** Optional constraints should be disabled
        assert manager.is_enabled("OvernightCallGeneration") is False

    def test_apply_strict_preset(self):
        """Test strict preset."""
        manager = ConstraintConfigManager()

        ***REMOVED*** Get original weight
        original_weight = manager.get("Equity").weight

        ***REMOVED*** Apply strict preset
        manager.apply_preset("strict")

        ***REMOVED*** All constraints should be enabled
        assert manager.is_enabled("OvernightCallGeneration") is True
        assert manager.is_enabled("SMResidentFacultyAlignment") is True

        ***REMOVED*** Weights should be doubled
        assert manager.get("Equity").weight == original_weight * 2

    def test_apply_resilience_tier1_preset(self):
        """Test resilience tier 1 preset."""
        manager = ConstraintConfigManager()

        manager.apply_preset("resilience_tier1")

        ***REMOVED*** Tier 1 resilience should be enabled
        assert manager.is_enabled("HubProtection") is True
        assert manager.is_enabled("UtilizationBuffer") is True

        ***REMOVED*** Tier 2 should be disabled
        assert manager.is_enabled("ZoneBoundary") is False
        assert manager.is_enabled("N1Vulnerability") is False

    def test_apply_resilience_tier2_preset(self):
        """Test resilience tier 2 preset."""
        manager = ConstraintConfigManager()

        manager.apply_preset("resilience_tier2")

        ***REMOVED*** All resilience constraints should be enabled
        assert manager.is_enabled("HubProtection") is True
        assert manager.is_enabled("UtilizationBuffer") is True
        assert manager.is_enabled("ZoneBoundary") is True
        assert manager.is_enabled("PreferenceTrail") is True
        assert manager.is_enabled("N1Vulnerability") is True

    def test_apply_call_scheduling_preset(self):
        """Test call scheduling preset."""
        manager = ConstraintConfigManager()

        manager.apply_preset("call_scheduling")

        ***REMOVED*** Call constraints should be enabled
        assert manager.is_enabled("OvernightCallGeneration") is True
        assert manager.is_enabled("PostCallAutoAssignment") is True

    def test_apply_sports_medicine_preset(self):
        """Test sports medicine preset."""
        manager = ConstraintConfigManager()

        manager.apply_preset("sports_medicine")

        ***REMOVED*** SM constraints should be enabled
        assert manager.is_enabled("SMResidentFacultyAlignment") is True
        assert manager.is_enabled("SMFacultyNoRegularClinic") is True

    def test_apply_invalid_preset(self):
        """Test applying invalid preset."""
        manager = ConstraintConfigManager()

        ***REMOVED*** Should not raise exception
        manager.apply_preset("invalid_preset")

        ***REMOVED*** State should be unchanged
        assert manager.is_enabled("Availability") is True

    def test_get_status_report(self):
        """Test status report generation."""
        manager = ConstraintConfigManager()

        report = manager.get_status_report()

        ***REMOVED*** Should be a string
        assert isinstance(report, str)

        ***REMOVED*** Should contain key information
        assert "Constraint Configuration Status Report" in report
        assert "ACGME" in report
        assert "Availability" in report
        assert "Total Constraints:" in report


class TestConstraintConfigSingleton:
    """Test singleton pattern for global config."""

    @pytest.fixture(autouse=True)
    def reset_config(self):
        """Reset configuration before each test."""
        reset_constraint_config()
        yield
        reset_constraint_config()

    def test_get_constraint_config_singleton(self):
        """Test get_constraint_config() returns singleton."""
        config1 = get_constraint_config()
        config2 = get_constraint_config()

        ***REMOVED*** Should be same instance
        assert config1 is config2

    def test_reset_constraint_config(self):
        """Test reset_constraint_config()."""
        config1 = get_constraint_config()
        config1.disable("Availability")

        ***REMOVED*** Reset
        reset_constraint_config()

        config2 = get_constraint_config()

        ***REMOVED*** Should be new instance with defaults
        assert config1 is not config2
        assert config2.is_enabled("Availability") is True


class TestConstraintCategories:
    """Test constraint categorization."""

    @pytest.fixture(autouse=True)
    def reset_config(self):
        """Reset configuration before each test."""
        reset_constraint_config()
        yield
        reset_constraint_config()

    def test_acgme_constraints_all_enabled(self):
        """Test all ACGME constraints are enabled by default."""
        manager = ConstraintConfigManager()

        acgme = manager.get_enabled_by_category(ConstraintCategory.ACGME)

        ***REMOVED*** Should have 4 ACGME constraints
        assert len(acgme) == 4

        ***REMOVED*** All should be CRITICAL priority
        assert all(c.priority == ConstraintPriorityLevel.CRITICAL for c in acgme)

    def test_capacity_constraints_all_enabled(self):
        """Test all CAPACITY constraints are enabled by default."""
        manager = ConstraintConfigManager()

        capacity = manager.get_enabled_by_category(ConstraintCategory.CAPACITY)

        ***REMOVED*** Should have 3 capacity constraints
        assert len(capacity) == 3

    def test_call_constraints_disabled_by_default(self):
        """Test CALL constraints are disabled by default."""
        manager = ConstraintConfigManager()

        call = manager.get_enabled_by_category(ConstraintCategory.CALL)

        ***REMOVED*** Should have 0 enabled call constraints
        assert len(call) == 0

    def test_fmit_constraints_disabled_by_default(self):
        """Test FMIT constraints are disabled by default."""
        manager = ConstraintConfigManager()

        fmit = manager.get_enabled_by_category(ConstraintCategory.FMIT)

        ***REMOVED*** Should have 0 enabled FMIT constraints
        assert len(fmit) == 0

    def test_specialty_constraints_disabled_by_default(self):
        """Test SPECIALTY constraints are disabled by default."""
        manager = ConstraintConfigManager()

        specialty = manager.get_enabled_by_category(ConstraintCategory.SPECIALTY)

        ***REMOVED*** Should have 0 enabled specialty constraints
        assert len(specialty) == 0


class TestConstraintDependencies:
    """Test constraint dependency handling."""

    @pytest.fixture(autouse=True)
    def reset_config(self):
        """Reset configuration before each test."""
        reset_constraint_config()
        yield
        reset_constraint_config()

    def test_post_call_depends_on_overnight_call(self):
        """Test PostCallAutoAssignment depends on OvernightCallGeneration."""
        manager = ConstraintConfigManager()

        post_call = manager.get("PostCallAutoAssignment")

        assert "OvernightCallGeneration" in post_call.dependencies

    def test_sm_faculty_depends_on_sm_alignment(self):
        """Test SMFacultyNoRegularClinic depends on SMResidentFacultyAlignment."""
        manager = ConstraintConfigManager()

        sm_faculty = manager.get("SMFacultyNoRegularClinic")

        assert "SMResidentFacultyAlignment" in sm_faculty.dependencies


class TestConstraintWeights:
    """Test constraint weight configuration."""

    @pytest.fixture(autouse=True)
    def reset_config(self):
        """Reset configuration before each test."""
        reset_constraint_config()
        yield
        reset_constraint_config()

    def test_acgme_constraints_high_weight(self):
        """Test ACGME constraints have high weights."""
        manager = ConstraintConfigManager()

        ***REMOVED*** Soft ACGME constraints should have high weights
        eighty_hour = manager.get("EightyHourRule")
        assert eighty_hour.weight == 1000.0

    def test_coverage_constraint_high_weight(self):
        """Test Coverage constraint has high weight."""
        manager = ConstraintConfigManager()

        coverage = manager.get("Coverage")
        assert coverage.weight == 1000.0

    def test_equity_constraints_lower_weight(self):
        """Test equity constraints have lower weights than coverage."""
        manager = ConstraintConfigManager()

        equity = manager.get("Equity")
        coverage = manager.get("Coverage")

        assert equity.weight < coverage.weight


@pytest.mark.integration
class TestConstraintConfigIntegration:
    """Integration tests for constraint configuration."""

    @pytest.fixture(autouse=True)
    def reset_config(self):
        """Reset configuration before each test."""
        reset_constraint_config()
        yield
        reset_constraint_config()

    def test_all_disabled_constraints_can_be_enabled(self):
        """Test that all disabled constraints can be enabled."""
        manager = ConstraintConfigManager()

        disabled = manager.get_all_disabled()

        for constraint in disabled:
            ***REMOVED*** Should be able to enable
            result = manager.enable(constraint.name)
            assert result is True

            ***REMOVED*** Should now be enabled
            assert manager.is_enabled(constraint.name) is True

    def test_all_enabled_constraints_can_be_disabled(self):
        """Test that all enabled constraints can be disabled."""
        manager = ConstraintConfigManager()

        enabled = manager.get_all_enabled()

        for constraint in enabled:
            ***REMOVED*** Should be able to disable
            result = manager.disable(constraint.name)
            assert result is True

            ***REMOVED*** Should now be disabled
            assert manager.is_enabled(constraint.name) is False

    def test_preset_combinations(self):
        """Test applying multiple presets in sequence."""
        manager = ConstraintConfigManager()

        ***REMOVED*** Start with minimal
        manager.apply_preset("minimal")
        assert manager.is_enabled("Continuity") is False

        ***REMOVED*** Switch to strict
        manager.apply_preset("strict")
        assert manager.is_enabled("Continuity") is True
        assert manager.is_enabled("OvernightCallGeneration") is True

        ***REMOVED*** Switch to minimal again
        manager.apply_preset("minimal")
        assert manager.is_enabled("Continuity") is False

    def test_manual_overrides_after_preset(self):
        """Test manual enable/disable after preset."""
        manager = ConstraintConfigManager()

        ***REMOVED*** Apply minimal preset
        manager.apply_preset("minimal")
        assert manager.is_enabled("OvernightCallGeneration") is False

        ***REMOVED*** Manually enable
        manager.enable("OvernightCallGeneration")
        assert manager.is_enabled("OvernightCallGeneration") is True

        ***REMOVED*** Manual enable should persist (not reset by preset unless applied again)
        assert manager.is_enabled("OvernightCallGeneration") is True
