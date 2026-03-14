"""Tests for constraint configuration system (no DB)."""

from __future__ import annotations

import pytest

from app.scheduling.constraints.config import (
    ConstraintCategory,
    ConstraintConfig,
    ConstraintConfigManager,
    ConstraintPriorityLevel,
    get_constraint_config,
    reset_constraint_config,
)


# ---------------------------------------------------------------------------
# ConstraintCategory enum
# ---------------------------------------------------------------------------


class TestConstraintCategory:
    def test_acgme(self):
        assert ConstraintCategory.ACGME.value == "ACGME"

    def test_capacity(self):
        assert ConstraintCategory.CAPACITY.value == "CAPACITY"

    def test_call(self):
        assert ConstraintCategory.CALL.value == "CALL"

    def test_resilience(self):
        assert ConstraintCategory.RESILIENCE.value == "RESILIENCE"

    def test_member_count(self):
        assert len(ConstraintCategory) == 11


# ---------------------------------------------------------------------------
# ConstraintPriorityLevel enum
# ---------------------------------------------------------------------------


class TestConstraintPriorityLevel:
    def test_critical(self):
        assert ConstraintPriorityLevel.CRITICAL == 1

    def test_high(self):
        assert ConstraintPriorityLevel.HIGH == 2

    def test_medium(self):
        assert ConstraintPriorityLevel.MEDIUM == 3

    def test_low(self):
        assert ConstraintPriorityLevel.LOW == 4

    def test_ordering(self):
        assert ConstraintPriorityLevel.CRITICAL < ConstraintPriorityLevel.LOW


# ---------------------------------------------------------------------------
# ConstraintConfig dataclass
# ---------------------------------------------------------------------------


class TestConstraintConfig:
    def test_defaults(self):
        cc = ConstraintConfig(name="test")
        assert cc.enabled is True
        assert cc.priority == ConstraintPriorityLevel.MEDIUM
        assert cc.weight == 1.0
        assert cc.category == ConstraintCategory.COVERAGE
        assert cc.dependencies == []
        assert cc.conflicts_with == []
        assert cc.enable_condition is None
        assert cc.disable_reason is None

    def test_is_active_enabled(self):
        cc = ConstraintConfig(name="test", enabled=True)
        assert cc.is_active() is True

    def test_is_active_disabled(self):
        cc = ConstraintConfig(name="test", enabled=False)
        assert cc.is_active() is False

    def test_should_enable_when_enabled(self):
        cc = ConstraintConfig(name="test", enabled=True)
        assert cc.should_enable({}) is True

    def test_should_enable_when_disabled(self):
        cc = ConstraintConfig(name="test", enabled=False)
        assert cc.should_enable({}) is False

    def test_should_enable_dependency_met(self):
        cc = ConstraintConfig(name="test", enabled=True, dependencies=["base"])
        assert cc.should_enable({"base_enabled": True}) is True

    def test_should_enable_dependency_not_met(self):
        cc = ConstraintConfig(name="test", enabled=True, dependencies=["base"])
        assert cc.should_enable({"base_enabled": False}) is False

    def test_should_enable_dependency_missing(self):
        cc = ConstraintConfig(name="test", enabled=True, dependencies=["base"])
        assert cc.should_enable({}) is False


# ---------------------------------------------------------------------------
# ConstraintConfigManager — initialization
# ---------------------------------------------------------------------------


class TestConstraintConfigManagerInit:
    def test_has_configs(self):
        mgr = ConstraintConfigManager()
        assert len(mgr._configs) > 0

    def test_acgme_constraints_enabled(self):
        mgr = ConstraintConfigManager()
        for name in [
            "Availability",
            "EightyHourRule",
            "OneInSevenRule",
            "SupervisionRatio",
        ]:
            assert mgr.is_enabled(name), f"{name} should be enabled by default"

    def test_acgme_constraints_critical(self):
        mgr = ConstraintConfigManager()
        for name in [
            "Availability",
            "EightyHourRule",
            "OneInSevenRule",
            "SupervisionRatio",
        ]:
            config = mgr.get(name)
            assert config.priority == ConstraintPriorityLevel.CRITICAL

    def test_call_constraints_disabled_by_default(self):
        mgr = ConstraintConfigManager()
        assert mgr.is_enabled("OvernightCallGeneration") is False

    def test_fmit_constraints_disabled_by_default(self):
        mgr = ConstraintConfigManager()
        for name in ["FMITWeekBlocking", "FMITMandatoryCall"]:
            assert mgr.is_enabled(name) is False

    def test_sm_constraints_disabled_by_default(self):
        mgr = ConstraintConfigManager()
        assert mgr.is_enabled("SMResidentFacultyAlignment") is False
        assert mgr.is_enabled("SMFacultyNoRegularClinic") is False

    def test_resilience_tier1_enabled(self):
        mgr = ConstraintConfigManager()
        assert mgr.is_enabled("HubProtection") is True
        assert mgr.is_enabled("UtilizationBuffer") is True

    def test_resilience_tier2_disabled(self):
        mgr = ConstraintConfigManager()
        for name in ["ZoneBoundary", "PreferenceTrail", "N1Vulnerability"]:
            assert mgr.is_enabled(name) is False


# ---------------------------------------------------------------------------
# ConstraintConfigManager — get/enable/disable
# ---------------------------------------------------------------------------


class TestConstraintConfigManagerOps:
    def test_get_existing(self):
        mgr = ConstraintConfigManager()
        config = mgr.get("Availability")
        assert config is not None
        assert config.name == "Availability"

    def test_get_missing(self):
        mgr = ConstraintConfigManager()
        assert mgr.get("nonexistent") is None

    def test_is_enabled_missing(self):
        mgr = ConstraintConfigManager()
        assert mgr.is_enabled("nonexistent") is False

    def test_enable(self):
        mgr = ConstraintConfigManager()
        mgr.disable("Availability")
        assert mgr.is_enabled("Availability") is False
        assert mgr.enable("Availability") is True
        assert mgr.is_enabled("Availability") is True

    def test_enable_nonexistent(self):
        mgr = ConstraintConfigManager()
        assert mgr.enable("nonexistent") is False

    def test_disable(self):
        mgr = ConstraintConfigManager()
        assert mgr.is_enabled("Availability") is True
        assert mgr.disable("Availability") is True
        assert mgr.is_enabled("Availability") is False

    def test_disable_nonexistent(self):
        mgr = ConstraintConfigManager()
        assert mgr.disable("nonexistent") is False


# ---------------------------------------------------------------------------
# ConstraintConfigManager — queries
# ---------------------------------------------------------------------------


class TestConstraintConfigManagerQueries:
    def test_get_enabled_by_category(self):
        mgr = ConstraintConfigManager()
        acgme = mgr.get_enabled_by_category(ConstraintCategory.ACGME)
        assert len(acgme) >= 4
        for config in acgme:
            assert config.category == ConstraintCategory.ACGME
            assert config.enabled is True

    def test_get_enabled_by_category_empty(self):
        mgr = ConstraintConfigManager()
        # FMIT is all disabled by default
        fmit = mgr.get_enabled_by_category(ConstraintCategory.FMIT)
        assert len(fmit) == 0

    def test_get_all_enabled(self):
        mgr = ConstraintConfigManager()
        enabled = mgr.get_all_enabled()
        assert len(enabled) > 0
        for config in enabled:
            assert config.enabled is True

    def test_get_all_disabled(self):
        mgr = ConstraintConfigManager()
        disabled = mgr.get_all_disabled()
        assert len(disabled) > 0
        for config in disabled:
            assert config.enabled is False

    def test_enabled_plus_disabled_equals_total(self):
        mgr = ConstraintConfigManager()
        enabled = len(mgr.get_all_enabled())
        disabled = len(mgr.get_all_disabled())
        assert enabled + disabled == len(mgr._configs)


# ---------------------------------------------------------------------------
# ConstraintConfigManager — presets
# ---------------------------------------------------------------------------


class TestConstraintPresets:
    def test_minimal_disables_optional(self):
        mgr = ConstraintConfigManager()
        mgr.apply_preset("minimal")
        assert mgr.is_enabled("Continuity") is False
        assert mgr.is_enabled("OvernightCallGeneration") is False
        assert mgr.is_enabled("ZoneBoundary") is False
        # ACGME should remain enabled
        assert mgr.is_enabled("Availability") is True
        assert mgr.is_enabled("EightyHourRule") is True

    def test_strict_enables_all(self):
        mgr = ConstraintConfigManager()
        mgr.apply_preset("strict")
        for config in mgr._configs.values():
            assert config.enabled is True

    def test_strict_doubles_weights(self):
        mgr = ConstraintConfigManager()
        original_weight = mgr.get("Equity").weight
        mgr.apply_preset("strict")
        assert mgr.get("Equity").weight == original_weight * 2

    def test_resilience_tier1(self):
        mgr = ConstraintConfigManager()
        mgr.apply_preset("resilience_tier1")
        assert mgr.is_enabled("HubProtection") is True
        assert mgr.is_enabled("UtilizationBuffer") is True
        assert mgr.is_enabled("ZoneBoundary") is False
        assert mgr.is_enabled("N1Vulnerability") is False

    def test_resilience_tier2(self):
        mgr = ConstraintConfigManager()
        mgr.apply_preset("resilience_tier2")
        assert mgr.is_enabled("HubProtection") is True
        assert mgr.is_enabled("UtilizationBuffer") is True
        assert mgr.is_enabled("ZoneBoundary") is True
        assert mgr.is_enabled("PreferenceTrail") is True
        assert mgr.is_enabled("N1Vulnerability") is True

    def test_call_scheduling(self):
        mgr = ConstraintConfigManager()
        mgr.apply_preset("call_scheduling")
        assert mgr.is_enabled("OvernightCallGeneration") is True
        assert mgr.is_enabled("PostCallAutoAssignment") is True

    def test_sports_medicine(self):
        mgr = ConstraintConfigManager()
        mgr.apply_preset("sports_medicine")
        assert mgr.is_enabled("SMResidentFacultyAlignment") is True
        assert mgr.is_enabled("SMFacultyNoRegularClinic") is True

    def test_unknown_preset(self):
        mgr = ConstraintConfigManager()
        enabled_before = len(mgr.get_all_enabled())
        mgr.apply_preset("unknown_preset")
        enabled_after = len(mgr.get_all_enabled())
        assert enabled_before == enabled_after


# ---------------------------------------------------------------------------
# ConstraintConfigManager — status report
# ---------------------------------------------------------------------------


class TestStatusReport:
    def test_returns_string(self):
        mgr = ConstraintConfigManager()
        report = mgr.get_status_report()
        assert isinstance(report, str)
        assert len(report) > 0

    def test_contains_title(self):
        mgr = ConstraintConfigManager()
        report = mgr.get_status_report()
        assert "Constraint Configuration Status Report" in report

    def test_contains_counts(self):
        mgr = ConstraintConfigManager()
        report = mgr.get_status_report()
        assert "Enabled:" in report
        assert "Disabled:" in report

    def test_contains_categories(self):
        mgr = ConstraintConfigManager()
        report = mgr.get_status_report()
        assert "ACGME" in report
        assert "RESILIENCE" in report

    def test_contains_constraint_names(self):
        mgr = ConstraintConfigManager()
        report = mgr.get_status_report()
        assert "Availability" in report
        assert "EightyHourRule" in report


# ---------------------------------------------------------------------------
# Singleton functions
# ---------------------------------------------------------------------------


class TestSingleton:
    def test_get_returns_manager(self):
        reset_constraint_config()
        mgr = get_constraint_config()
        assert isinstance(mgr, ConstraintConfigManager)

    def test_get_returns_same_instance(self):
        reset_constraint_config()
        mgr1 = get_constraint_config()
        mgr2 = get_constraint_config()
        assert mgr1 is mgr2

    def test_reset_creates_new_instance(self):
        reset_constraint_config()
        mgr1 = get_constraint_config()
        reset_constraint_config()
        mgr2 = get_constraint_config()
        assert mgr1 is not mgr2
