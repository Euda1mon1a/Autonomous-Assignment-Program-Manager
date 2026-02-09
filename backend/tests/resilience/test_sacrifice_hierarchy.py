"""Tests for Sacrifice Hierarchy (Triage Medicine Load Shedding)."""

from datetime import datetime
from uuid import uuid4

import pytest

from app.resilience.sacrifice_hierarchy import (
    Activity,
    ActivityCategory,
    LoadSheddingLevel,
    LoadSheddingStatus,
    SacrificeDecision,
    SacrificeHierarchy,
)


# ==================== Enums ====================


class TestActivityCategory:
    def test_values_ascending_priority(self):
        assert ActivityCategory.PATIENT_SAFETY < ActivityCategory.ACGME_REQUIREMENTS
        assert ActivityCategory.ACGME_REQUIREMENTS < ActivityCategory.CONTINUITY_OF_CARE
        assert ActivityCategory.CONTINUITY_OF_CARE < ActivityCategory.EDUCATION_CORE
        assert ActivityCategory.EDUCATION_CORE < ActivityCategory.RESEARCH
        assert ActivityCategory.RESEARCH < ActivityCategory.ADMINISTRATION
        assert ActivityCategory.ADMINISTRATION < ActivityCategory.EDUCATION_OPTIONAL

    def test_patient_safety_is_1(self):
        assert ActivityCategory.PATIENT_SAFETY == 1

    def test_education_optional_is_7(self):
        assert ActivityCategory.EDUCATION_OPTIONAL == 7


class TestLoadSheddingLevel:
    def test_normal_is_0(self):
        assert LoadSheddingLevel.NORMAL == 0

    def test_critical_is_5(self):
        assert LoadSheddingLevel.CRITICAL == 5

    def test_ordering(self):
        assert LoadSheddingLevel.NORMAL < LoadSheddingLevel.YELLOW
        assert LoadSheddingLevel.YELLOW < LoadSheddingLevel.ORANGE
        assert LoadSheddingLevel.ORANGE < LoadSheddingLevel.RED
        assert LoadSheddingLevel.RED < LoadSheddingLevel.BLACK
        assert LoadSheddingLevel.BLACK < LoadSheddingLevel.CRITICAL


# ==================== Dataclasses ====================


class TestActivity:
    def test_defaults(self):
        a = Activity(
            id=uuid4(),
            name="Test",
            category=ActivityCategory.RESEARCH,
            faculty_hours=10.0,
        )
        assert a.is_required is False
        assert a.can_be_deferred is True
        assert a.deferral_limit_days == 30


class TestSacrificeDecision:
    def test_creation(self):
        d = SacrificeDecision(
            timestamp=datetime.now(),
            level=LoadSheddingLevel.ORANGE,
            activities_suspended=["admin_meeting"],
            reason="flu outbreak",
            coverage_before=200.0,
            coverage_after=150.0,
            approved_by="Dr. Chief",
        )
        assert d.level == LoadSheddingLevel.ORANGE
        assert d.coverage_before == 200.0


class TestLoadSheddingStatus:
    def test_creation(self):
        s = LoadSheddingStatus(
            level=LoadSheddingLevel.RED,
            level_name="RED",
            active_since=datetime.now(),
            activities_suspended=["research"],
            activities_protected=["icu_coverage"],
            current_coverage=80.0,
            target_coverage=200.0,
        )
        assert s.level == LoadSheddingLevel.RED
        assert len(s.decisions_log) == 0


# ==================== SacrificeHierarchy ====================


class TestSacrificeHierarchyInit:
    def test_defaults(self):
        sh = SacrificeHierarchy()
        assert sh.current_level == LoadSheddingLevel.NORMAL
        assert sh.level_activated_at is None
        assert sh.activities == {}
        assert sh.decisions_log == []

    def test_sacrifice_order_excludes_patient_safety(self):
        assert ActivityCategory.PATIENT_SAFETY not in SacrificeHierarchy.SACRIFICE_ORDER

    def test_sacrifice_order_starts_with_optional(self):
        assert (
            SacrificeHierarchy.SACRIFICE_ORDER[0] == ActivityCategory.EDUCATION_OPTIONAL
        )


class TestRegisterActivity:
    def test_registers(self):
        sh = SacrificeHierarchy()
        aid = uuid4()
        a = Activity(
            id=aid,
            name="ICU",
            category=ActivityCategory.PATIENT_SAFETY,
            faculty_hours=40.0,
        )
        sh.register_activity(a)
        assert aid in sh.activities


class TestGetSacrificedCategories:
    def test_normal_returns_empty(self):
        sh = SacrificeHierarchy()
        assert sh.get_sacrificed_categories(LoadSheddingLevel.NORMAL) == []

    def test_yellow_sacrifices_optional_education(self):
        sh = SacrificeHierarchy()
        cats = sh.get_sacrificed_categories(LoadSheddingLevel.YELLOW)
        assert cats == [ActivityCategory.EDUCATION_OPTIONAL]

    def test_orange_adds_admin_research(self):
        sh = SacrificeHierarchy()
        cats = sh.get_sacrificed_categories(LoadSheddingLevel.ORANGE)
        assert ActivityCategory.ADMINISTRATION in cats
        assert ActivityCategory.RESEARCH in cats
        assert ActivityCategory.EDUCATION_OPTIONAL in cats
        assert len(cats) == 3

    def test_red_adds_core_education(self):
        sh = SacrificeHierarchy()
        cats = sh.get_sacrificed_categories(LoadSheddingLevel.RED)
        assert ActivityCategory.EDUCATION_CORE in cats
        assert len(cats) == 4

    def test_black_adds_continuity(self):
        sh = SacrificeHierarchy()
        cats = sh.get_sacrificed_categories(LoadSheddingLevel.BLACK)
        assert ActivityCategory.CONTINUITY_OF_CARE in cats
        assert len(cats) == 5

    def test_critical_adds_acgme(self):
        sh = SacrificeHierarchy()
        cats = sh.get_sacrificed_categories(LoadSheddingLevel.CRITICAL)
        assert ActivityCategory.ACGME_REQUIREMENTS in cats
        assert len(cats) == 6

    def test_critical_still_excludes_patient_safety(self):
        sh = SacrificeHierarchy()
        cats = sh.get_sacrificed_categories(LoadSheddingLevel.CRITICAL)
        assert ActivityCategory.PATIENT_SAFETY not in cats


class TestGetProtectedCategories:
    def test_normal_protects_all(self):
        sh = SacrificeHierarchy()
        protected = sh.get_protected_categories(LoadSheddingLevel.NORMAL)
        assert len(protected) == 7  # All categories

    def test_critical_protects_only_patient_safety(self):
        sh = SacrificeHierarchy()
        protected = sh.get_protected_categories(LoadSheddingLevel.CRITICAL)
        assert protected == [ActivityCategory.PATIENT_SAFETY]

    def test_yellow_protects_6(self):
        sh = SacrificeHierarchy()
        protected = sh.get_protected_categories(LoadSheddingLevel.YELLOW)
        assert len(protected) == 6
        assert ActivityCategory.EDUCATION_OPTIONAL not in protected


class TestCalculateRequiredLevel:
    def _make_hierarchy_with_activities(self):
        sh = SacrificeHierarchy()
        categories_hours = [
            (ActivityCategory.PATIENT_SAFETY, 40.0),
            (ActivityCategory.ACGME_REQUIREMENTS, 30.0),
            (ActivityCategory.CONTINUITY_OF_CARE, 25.0),
            (ActivityCategory.EDUCATION_CORE, 20.0),
            (ActivityCategory.RESEARCH, 15.0),
            (ActivityCategory.ADMINISTRATION, 10.0),
            (ActivityCategory.EDUCATION_OPTIONAL, 10.0),
        ]
        for cat, hours in categories_hours:
            sh.register_activity(
                Activity(
                    id=uuid4(),
                    name=cat.name,
                    category=cat,
                    faculty_hours=hours,
                )
            )
        return sh

    def test_sufficient_capacity_normal(self):
        sh = self._make_hierarchy_with_activities()
        level = sh.calculate_required_level(200.0, 150.0)
        assert level == LoadSheddingLevel.NORMAL

    def test_needs_shedding(self):
        sh = self._make_hierarchy_with_activities()
        # Total = 150. If capacity = 135, need to shed 15h (optional education = 10h not enough)
        level = sh.calculate_required_level(135.0, 150.0)
        assert level.value >= LoadSheddingLevel.YELLOW.value

    def test_severely_limited_escalates(self):
        sh = self._make_hierarchy_with_activities()
        # Only 40 hours available for 150 needed
        level = sh.calculate_required_level(40.0, 150.0)
        assert level.value >= LoadSheddingLevel.BLACK.value


class TestShedLoad:
    def _make_activities(self):
        return [
            Activity(
                id=uuid4(),
                name="ICU",
                category=ActivityCategory.PATIENT_SAFETY,
                faculty_hours=40.0,
                is_required=True,
            ),
            Activity(
                id=uuid4(),
                name="ACGME Rotations",
                category=ActivityCategory.ACGME_REQUIREMENTS,
                faculty_hours=20.0,
                is_required=True,
            ),
            Activity(
                id=uuid4(),
                name="Research",
                category=ActivityCategory.RESEARCH,
                faculty_hours=15.0,
            ),
            Activity(
                id=uuid4(),
                name="Admin Meeting",
                category=ActivityCategory.ADMINISTRATION,
                faculty_hours=10.0,
            ),
            Activity(
                id=uuid4(),
                name="Conference",
                category=ActivityCategory.EDUCATION_OPTIONAL,
                faculty_hours=5.0,
            ),
        ]

    def test_sufficient_capacity_keeps_all(self):
        sh = SacrificeHierarchy()
        activities = self._make_activities()
        kept, sacrificed = sh.shed_load(activities, 100.0)
        assert len(sacrificed) == 0
        assert len(kept) == 5

    def test_insufficient_capacity_sacrifices_lowest(self):
        sh = SacrificeHierarchy()
        activities = self._make_activities()
        # Total = 90, capacity = 70 → need to shed 20h
        kept, sacrificed = sh.shed_load(activities, 70.0, reason="staffing shortage")
        assert len(sacrificed) > 0
        # Patient safety and ACGME should be kept
        kept_names = {a.name for a in kept}
        assert "ICU" in kept_names
        assert "ACGME Rotations" in kept_names

    def test_decision_logged(self):
        sh = SacrificeHierarchy()
        activities = self._make_activities()
        sh.shed_load(activities, 60.0, reason="test", approved_by="Dr. Test")
        assert len(sh.decisions_log) == 1
        assert sh.decisions_log[0].reason == "test"
        assert sh.decisions_log[0].approved_by == "Dr. Test"

    def test_no_sacrifice_no_log(self):
        sh = SacrificeHierarchy()
        activities = self._make_activities()
        sh.shed_load(activities, 200.0)
        assert len(sh.decisions_log) == 0

    def test_suspended_activities_tracked(self):
        sh = SacrificeHierarchy()
        activities = self._make_activities()
        _, sacrificed = sh.shed_load(activities, 60.0)
        for a in sacrificed:
            assert sh.is_activity_suspended(a.id)


class TestActivateLevel:
    def _make_hierarchy_with_activities(self):
        sh = SacrificeHierarchy()
        for cat in ActivityCategory:
            sh.register_activity(
                Activity(
                    id=uuid4(),
                    name=f"act_{cat.name}",
                    category=cat,
                    faculty_hours=10.0,
                )
            )
        return sh

    def test_activates_level(self):
        sh = self._make_hierarchy_with_activities()
        decision = sh.activate_level(LoadSheddingLevel.ORANGE, reason="flu")
        assert sh.current_level == LoadSheddingLevel.ORANGE
        assert sh.level_activated_at is not None
        assert decision.level == LoadSheddingLevel.ORANGE

    def test_same_level_no_op(self):
        sh = SacrificeHierarchy()
        decision = sh.activate_level(LoadSheddingLevel.NORMAL)
        assert "No change" in decision.notes

    def test_suspends_correct_activities(self):
        sh = self._make_hierarchy_with_activities()
        sh.activate_level(LoadSheddingLevel.YELLOW)
        suspended = sh.get_suspended_activities()
        assert len(suspended) == 1
        assert suspended[0].category == ActivityCategory.EDUCATION_OPTIONAL

    def test_decision_logged(self):
        sh = self._make_hierarchy_with_activities()
        sh.activate_level(
            LoadSheddingLevel.RED, reason="emergency", approved_by="Dr. Chief"
        )
        assert len(sh.decisions_log) == 1
        assert "RED" in sh.decisions_log[0].notes


class TestDeactivateLevel:
    def _make_hierarchy_with_activities(self):
        sh = SacrificeHierarchy()
        for cat in ActivityCategory:
            sh.register_activity(
                Activity(
                    id=uuid4(),
                    name=f"act_{cat.name}",
                    category=cat,
                    faculty_hours=10.0,
                )
            )
        return sh

    def test_deactivate_restores_activities(self):
        sh = self._make_hierarchy_with_activities()
        sh.activate_level(LoadSheddingLevel.ORANGE)
        suspended_before = len(sh.get_suspended_activities())
        sh.deactivate_level(LoadSheddingLevel.NORMAL)
        assert sh.current_level == LoadSheddingLevel.NORMAL
        assert len(sh.get_suspended_activities()) == 0

    def test_partial_deactivation(self):
        sh = self._make_hierarchy_with_activities()
        sh.activate_level(LoadSheddingLevel.RED)
        sh.deactivate_level(LoadSheddingLevel.YELLOW)
        assert sh.current_level == LoadSheddingLevel.YELLOW
        # Only optional education should remain suspended
        suspended = sh.get_suspended_activities()
        for a in suspended:
            assert a.category == ActivityCategory.EDUCATION_OPTIONAL

    def test_deactivate_to_higher_level_noop(self):
        sh = SacrificeHierarchy()
        sh.activate_level(LoadSheddingLevel.YELLOW)
        sh.deactivate_level(LoadSheddingLevel.RED)
        # Should stay at YELLOW since RED >= YELLOW
        assert sh.current_level == LoadSheddingLevel.YELLOW


class TestGetStatus:
    def test_initial_status(self):
        sh = SacrificeHierarchy()
        status = sh.get_status()
        assert status.level == LoadSheddingLevel.NORMAL
        assert status.level_name == "NORMAL"
        assert len(status.activities_suspended) == 0

    def test_status_after_activation(self):
        sh = SacrificeHierarchy()
        for cat in ActivityCategory:
            sh.register_activity(
                Activity(
                    id=uuid4(),
                    name=f"act_{cat.name}",
                    category=cat,
                    faculty_hours=10.0,
                )
            )
        sh.activate_level(LoadSheddingLevel.ORANGE)
        status = sh.get_status()
        assert status.level == LoadSheddingLevel.ORANGE
        assert len(status.activities_suspended) == 3  # optional edu + admin + research


class TestGetRecoveryPlan:
    def test_empty_when_normal(self):
        sh = SacrificeHierarchy()
        assert sh.get_recovery_plan() == []

    def test_recovery_plan_ordered_by_priority(self):
        sh = SacrificeHierarchy()
        activities = [
            Activity(
                id=uuid4(),
                name="Admin",
                category=ActivityCategory.ADMINISTRATION,
                faculty_hours=10.0,
            ),
            Activity(
                id=uuid4(),
                name="Research",
                category=ActivityCategory.RESEARCH,
                faculty_hours=15.0,
            ),
            Activity(
                id=uuid4(),
                name="Conf",
                category=ActivityCategory.EDUCATION_OPTIONAL,
                faculty_hours=5.0,
            ),
        ]
        for a in activities:
            sh.register_activity(a)
        sh.activate_level(LoadSheddingLevel.ORANGE)
        plan = sh.get_recovery_plan()
        assert len(plan) == 3
        # Should be ordered by priority (most important first)
        assert plan[0]["category"] == "RESEARCH"
        assert plan[1]["category"] == "ADMINISTRATION"
        assert plan[2]["category"] == "EDUCATION_OPTIONAL"


class TestGetCategorySummary:
    def test_all_categories_present(self):
        sh = SacrificeHierarchy()
        summary = sh.get_category_summary()
        assert len(summary) == 7  # All ActivityCategory values

    def test_counts_correct(self):
        sh = SacrificeHierarchy()
        for i in range(3):
            sh.register_activity(
                Activity(
                    id=uuid4(),
                    name=f"research_{i}",
                    category=ActivityCategory.RESEARCH,
                    faculty_hours=5.0,
                )
            )
        summary = sh.get_category_summary()
        assert summary["RESEARCH"]["total_activities"] == 3
        assert summary["RESEARCH"]["total_hours"] == 15.0

    def test_suspended_counts(self):
        sh = SacrificeHierarchy()
        sh.register_activity(
            Activity(
                id=uuid4(),
                name="conf",
                category=ActivityCategory.EDUCATION_OPTIONAL,
                faculty_hours=5.0,
            )
        )
        sh.activate_level(LoadSheddingLevel.YELLOW)
        summary = sh.get_category_summary()
        assert summary["EDUCATION_OPTIONAL"]["suspended_count"] == 1

    def test_patient_safety_always_protected(self):
        sh = SacrificeHierarchy()
        sh.register_activity(
            Activity(
                id=uuid4(),
                name="icu",
                category=ActivityCategory.PATIENT_SAFETY,
                faculty_hours=40.0,
            )
        )
        sh.activate_level(LoadSheddingLevel.CRITICAL)
        summary = sh.get_category_summary()
        assert summary["PATIENT_SAFETY"]["is_protected"] is True
        assert summary["PATIENT_SAFETY"]["sacrifice_order"] == -1
