"""Tests to verify all exported constraints are registered in ConstraintManager.

This test suite prevents the "implemented but not registered" bug where constraints
are created, tested, and exported but never added to the ConstraintManager factory
methods.

The test compares exported constraints in __init__.py against registered constraints
in ConstraintManager.create_default() and create_resilience_aware().
"""

import pytest

from app.scheduling.constraints import (
    # Block 10 call equity constraints
    CallSpacingConstraint,
    SundayCallEquityConstraint,
    TuesdayCallPreferenceConstraint,
    WeekdayCallEquityConstraint,
    # Block 10 inpatient constraints
    ResidentInpatientHeadcountConstraint,
    # FMIT constraints
    PostFMITSundayBlockingConstraint,
    # Manager
    ConstraintManager,
)


class TestConstraintRegistration:
    """Verify constraints are properly registered in manager factory methods."""

    def test_block10_hard_constraints_in_default_manager(self):
        """Test Block 10 hard constraints are registered in create_default()."""
        manager = ConstraintManager.create_default()
        constraint_names = {c.name for c in manager.constraints}

        # Block 10 hard constraints
        assert "ResidentInpatientHeadcount" in constraint_names, (
            "ResidentInpatientHeadcountConstraint not registered in create_default()"
        )
        assert "PostFMITSundayBlocking" in constraint_names, (
            "PostFMITSundayBlockingConstraint not registered in create_default()"
        )

    def test_block10_soft_constraints_in_default_manager(self):
        """Test Block 10 soft constraints are registered in create_default()."""
        manager = ConstraintManager.create_default()
        constraint_names = {c.name for c in manager.constraints}

        # Block 10 soft constraints - call equity
        assert "SundayCallEquity" in constraint_names, (
            "SundayCallEquityConstraint not registered in create_default()"
        )
        assert "CallSpacing" in constraint_names, (
            "CallSpacingConstraint not registered in create_default()"
        )
        assert "WeekdayCallEquity" in constraint_names, (
            "WeekdayCallEquityConstraint not registered in create_default()"
        )
        assert "TuesdayCallPreference" in constraint_names, (
            "TuesdayCallPreferenceConstraint not registered in create_default()"
        )

    def test_block10_constraints_in_resilience_manager(self):
        """Test Block 10 constraints are also in create_resilience_aware()."""
        manager = ConstraintManager.create_resilience_aware()
        constraint_names = {c.name for c in manager.constraints}

        # Hard constraints
        assert "ResidentInpatientHeadcount" in constraint_names
        assert "PostFMITSundayBlocking" in constraint_names

        # Soft constraints
        assert "SundayCallEquity" in constraint_names
        assert "CallSpacing" in constraint_names
        assert "WeekdayCallEquity" in constraint_names
        assert "TuesdayCallPreference" in constraint_names

    def test_call_equity_weight_hierarchy(self):
        """Test call equity constraints follow the specified weight hierarchy.

        Weight order (highest to lowest impact):
        - Sunday equity: 10.0 (worst call day)
        - Call spacing: 8.0 (burnout prevention)
        - Weekday equity: 5.0 (balance Mon-Thu)
        - Tuesday preference: 2.0 (academic scheduling)
        """
        manager = ConstraintManager.create_default()
        constraint_by_name = {c.name: c for c in manager.constraints}

        sunday = constraint_by_name["SundayCallEquity"]
        spacing = constraint_by_name["CallSpacing"]
        weekday = constraint_by_name["WeekdayCallEquity"]
        tuesday = constraint_by_name["TuesdayCallPreference"]

        # Verify weight hierarchy
        assert sunday.weight > spacing.weight, "Sunday should have highest weight"
        assert spacing.weight > weekday.weight, "Spacing should beat weekday"
        assert weekday.weight > tuesday.weight, "Weekday should beat tuesday"

        # Verify exact weights
        assert sunday.weight == 10.0
        assert spacing.weight == 8.0
        assert weekday.weight == 5.0
        assert tuesday.weight == 2.0

    def test_constraint_enabled_by_default(self):
        """Test Block 10 constraints are enabled by default."""
        manager = ConstraintManager.create_default()
        constraint_by_name = {c.name: c for c in manager.constraints}

        block10_constraints = [
            "ResidentInpatientHeadcount",
            "PostFMITSundayBlocking",
            "SundayCallEquity",
            "CallSpacing",
            "WeekdayCallEquity",
            "TuesdayCallPreference",
        ]

        for name in block10_constraints:
            constraint = constraint_by_name.get(name)
            assert constraint is not None, f"{name} not found in manager"
            assert constraint.enabled, f"{name} should be enabled by default"


class TestConstraintExportIntegrity:
    """Test that exported constraints match registered constraints."""

    def test_all_call_equity_exports_registered(self):
        """Verify all exported call_equity constraints are registered."""
        # These are all the call_equity exports from __init__.py
        exported_classes = [
            CallSpacingConstraint,
            SundayCallEquityConstraint,
            TuesdayCallPreferenceConstraint,
            WeekdayCallEquityConstraint,
        ]

        manager = ConstraintManager.create_default()
        registered_types = {type(c) for c in manager.constraints}

        for cls in exported_classes:
            assert cls in registered_types, (
                f"{cls.__name__} is exported but not registered in create_default(). "
                f"Add manager.add({cls.__name__}()) to manager.py"
            )

    def test_inpatient_constraint_registered(self):
        """Verify ResidentInpatientHeadcountConstraint is registered."""
        manager = ConstraintManager.create_default()
        registered_types = {type(c) for c in manager.constraints}

        assert ResidentInpatientHeadcountConstraint in registered_types, (
            "ResidentInpatientHeadcountConstraint is exported but not registered"
        )

    def test_post_fmit_sunday_blocking_registered(self):
        """Verify PostFMITSundayBlockingConstraint is registered."""
        manager = ConstraintManager.create_default()
        registered_types = {type(c) for c in manager.constraints}

        assert PostFMITSundayBlockingConstraint in registered_types, (
            "PostFMITSundayBlockingConstraint is exported but not registered"
        )


class TestConstraintManagerConsistency:
    """Test consistency between different manager factory methods."""

    def test_default_and_resilience_have_same_base_constraints(self):
        """Test create_default() and create_resilience_aware() share base constraints."""
        default_manager = ConstraintManager.create_default()
        resilience_manager = ConstraintManager.create_resilience_aware()

        default_names = {c.name for c in default_manager.constraints}
        resilience_names = {c.name for c in resilience_manager.constraints}

        # Base constraints that should be in both
        base_constraints = {
            # ACGME compliance
            "Availability",
            "OnePersonPerBlock",
            "80HourRule",
            "1in7Rule",
            "SupervisionRatio",
            # Block 10
            "ResidentInpatientHeadcount",
            "PostFMITSundayBlocking",
            "SundayCallEquity",
            "CallSpacing",
            "WeekdayCallEquity",
            "TuesdayCallPreference",
        }

        for name in base_constraints:
            assert name in default_names, f"{name} missing from create_default()"
            assert name in resilience_names, (
                f"{name} missing from create_resilience_aware()"
            )

    def test_constraint_count_reasonable(self):
        """Test that manager has a reasonable number of constraints."""
        manager = ConstraintManager.create_default()

        # Should have at least 15 constraints (11 ACGME + 4 resilience + Block 10)
        assert len(manager.constraints) >= 15, (
            f"Expected at least 15 constraints, got {len(manager.constraints)}"
        )

        # Should have both hard and soft constraints
        assert len(manager.get_hard_constraints()) > 0, "No hard constraints found"
        assert len(manager.get_soft_constraints()) > 0, "No soft constraints found"
