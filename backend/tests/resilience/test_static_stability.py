"""Tests for Static Stability (AWS architecture pattern for fallback scheduling)."""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest

from app.resilience.static_stability import (
    FallbackSchedule,
    FallbackScheduler,
    FallbackScenario,
    SchedulingZone,
)


# ==================== Enums ====================


class TestFallbackScenario:
    def test_values(self):
        assert FallbackScenario.SINGLE_FACULTY_LOSS.value == "1_faculty_loss"
        assert FallbackScenario.DOUBLE_FACULTY_LOSS.value == "2_faculty_loss"
        assert FallbackScenario.MASS_CASUALTY.value == "mass_casualty_event"

    def test_all_scenarios(self):
        assert len(FallbackScenario) == 7


# ==================== FallbackSchedule ====================


class TestFallbackSchedule:
    def test_defaults(self):
        fs = FallbackSchedule(
            id=uuid4(),
            scenario=FallbackScenario.HOLIDAY_SKELETON,
            name="Holiday",
            description="Test",
            created_at=datetime.now(),
            valid_from=date(2026, 1, 1),
            valid_until=date(2026, 1, 31),
        )
        assert fs.is_active is False
        assert fs.activation_count == 0
        assert fs.assignments == []
        assert fs.coverage_rate == 0.0


# ==================== SchedulingZone ====================


class TestSchedulingZone:
    def test_is_self_sufficient(self):
        f1, f2 = uuid4(), uuid4()
        zone = SchedulingZone(
            id=uuid4(),
            name="ICU",
            services=["icu_coverage"],
            dedicated_faculty=[f1, f2],
            minimum_coverage=1,
        )
        assert zone.is_self_sufficient({f1}) is True

    def test_not_self_sufficient(self):
        f1, f2 = uuid4(), uuid4()
        zone = SchedulingZone(
            id=uuid4(),
            name="ICU",
            services=["icu_coverage"],
            dedicated_faculty=[f1],
            minimum_coverage=2,
        )
        assert zone.is_self_sufficient({f1}) is False

    def test_self_sufficient_with_all_available(self):
        f1, f2, f3 = uuid4(), uuid4(), uuid4()
        zone = SchedulingZone(
            id=uuid4(),
            name="OR",
            services=["or_coverage"],
            dedicated_faculty=[f1, f2, f3],
            minimum_coverage=2,
        )
        assert zone.is_self_sufficient({f1, f2, f3}) is True

    def test_unavailable_faculty_not_counted(self):
        f1, f2 = uuid4(), uuid4()
        f_other = uuid4()
        zone = SchedulingZone(
            id=uuid4(),
            name="Clinic",
            services=["clinic"],
            dedicated_faculty=[f1, f2],
            minimum_coverage=2,
        )
        # Only f_other is available, but not dedicated
        assert zone.is_self_sufficient({f_other}) is False


# ==================== FallbackScheduler ====================


class TestFallbackSchedulerInit:
    def test_defaults(self):
        fs = FallbackScheduler()
        assert fs.fallback_schedules == {}
        assert fs.zones == {}
        assert fs._schedule_generator is None


class TestRegisterScheduleGenerator:
    def test_registers(self):
        fs = FallbackScheduler()

        def gen(scenario, start, end):
            return [{"block": "test"}]

        fs.register_schedule_generator(gen)
        assert fs._schedule_generator is not None


class TestCreateZone:
    def test_creates_zone(self):
        fs = FallbackScheduler()
        f1, f2 = uuid4(), uuid4()
        zone = fs.create_zone("ICU", ["icu_coverage"], [f1, f2])
        assert zone.name == "ICU"
        assert len(fs.zones) == 1
        assert f1 in zone.dedicated_faculty


class TestPrecomputeFallback:
    def test_with_custom_assignments(self):
        fs = FallbackScheduler()
        assignments = [{"block": i, "faculty": "test"} for i in range(10)]
        fallback = fs.precompute_fallback(
            FallbackScenario.HOLIDAY_SKELETON,
            date(2026, 12, 20),
            date(2026, 12, 31),
            custom_assignments=assignments,
        )
        assert fallback.scenario == FallbackScenario.HOLIDAY_SKELETON
        assert len(fallback.assignments) == 10
        assert fallback.coverage_rate > 0

    def test_with_generator(self):
        fs = FallbackScheduler()

        def gen(scenario, start, end):
            return [{"block": "generated"}]

        fs.register_schedule_generator(gen)
        fallback = fs.precompute_fallback(
            FallbackScenario.SINGLE_FACULTY_LOSS,
            date(2026, 1, 1),
            date(2026, 1, 31),
        )
        assert len(fallback.assignments) == 1

    def test_no_generator_empty_assignments(self):
        fs = FallbackScheduler()
        fallback = fs.precompute_fallback(
            FallbackScenario.WEATHER_EMERGENCY,
            date(2026, 1, 1),
            date(2026, 1, 31),
        )
        assert fallback.assignments == []
        assert fallback.coverage_rate == 0.0

    def test_stores_in_dict(self):
        fs = FallbackScheduler()
        fs.precompute_fallback(
            FallbackScenario.PANDEMIC_ESSENTIAL,
            date(2026, 1, 1),
            date(2026, 1, 31),
        )
        assert FallbackScenario.PANDEMIC_ESSENTIAL in fs.fallback_schedules

    def test_assumptions_stored(self):
        fs = FallbackScheduler()
        fallback = fs.precompute_fallback(
            FallbackScenario.PCS_SEASON_50_PERCENT,
            date(2026, 6, 1),
            date(2026, 8, 31),
            assumptions=["50% faculty available"],
        )
        assert "50% faculty available" in fallback.assumptions

    def test_scenario_names(self):
        fs = FallbackScheduler()
        fallback = fs.precompute_fallback(
            FallbackScenario.MASS_CASUALTY,
            date(2026, 1, 1),
            date(2026, 1, 7),
        )
        assert fallback.name == "Mass Casualty Event"

    def test_reduced_services(self):
        fs = FallbackScheduler()
        fallback = fs.precompute_fallback(
            FallbackScenario.HOLIDAY_SKELETON,
            date(2026, 12, 20),
            date(2026, 12, 31),
        )
        assert len(fallback.services_reduced) > 0


class TestPrecomputeAllFallbacks:
    def test_computes_all_scenarios(self):
        fs = FallbackScheduler()
        results = fs.precompute_all_fallbacks(date(2026, 1, 1), date(2026, 12, 31))
        assert len(results) == 7  # All scenarios

    def test_handles_generator_errors(self):
        fs = FallbackScheduler()

        def bad_gen(scenario, start, end):
            if scenario == FallbackScenario.MASS_CASUALTY:
                raise RuntimeError("generation failed")
            return []

        fs.register_schedule_generator(bad_gen)
        results = fs.precompute_all_fallbacks(date(2026, 1, 1), date(2026, 12, 31))
        assert FallbackScenario.MASS_CASUALTY not in results
        assert len(results) == 6  # All except the failed one


class TestActivateFallback:
    def test_activates(self):
        fs = FallbackScheduler()
        fs.precompute_fallback(
            FallbackScenario.SINGLE_FACULTY_LOSS,
            date(2026, 1, 1),
            date(2026, 12, 31),
        )
        fallback = fs.activate_fallback(FallbackScenario.SINGLE_FACULTY_LOSS)
        assert fallback is not None
        assert fallback.is_active is True
        assert fallback.activation_count == 1
        assert fallback.last_activated is not None

    def test_no_fallback_returns_none(self):
        fs = FallbackScheduler()
        assert fs.activate_fallback(FallbackScenario.MASS_CASUALTY) is None

    def test_multiple_activations_increment_count(self):
        fs = FallbackScheduler()
        fs.precompute_fallback(
            FallbackScenario.HOLIDAY_SKELETON,
            date(2026, 1, 1),
            date(2026, 12, 31),
        )
        fs.activate_fallback(FallbackScenario.HOLIDAY_SKELETON)
        fs.activate_fallback(FallbackScenario.HOLIDAY_SKELETON)
        assert (
            fs.fallback_schedules[FallbackScenario.HOLIDAY_SKELETON].activation_count
            == 2
        )


class TestDeactivateFallback:
    def test_deactivates(self):
        fs = FallbackScheduler()
        fs.precompute_fallback(
            FallbackScenario.WEATHER_EMERGENCY,
            date(2026, 1, 1),
            date(2026, 12, 31),
        )
        fs.activate_fallback(FallbackScenario.WEATHER_EMERGENCY)
        fs.deactivate_fallback(FallbackScenario.WEATHER_EMERGENCY)
        assert (
            fs.fallback_schedules[FallbackScenario.WEATHER_EMERGENCY].is_active is False
        )


class TestGetActiveFallbacks:
    def test_returns_only_active(self):
        fs = FallbackScheduler()
        fs.precompute_fallback(
            FallbackScenario.HOLIDAY_SKELETON, date(2026, 1, 1), date(2026, 12, 31)
        )
        fs.precompute_fallback(
            FallbackScenario.WEATHER_EMERGENCY, date(2026, 1, 1), date(2026, 12, 31)
        )
        fs.activate_fallback(FallbackScenario.HOLIDAY_SKELETON)
        active = fs.get_active_fallbacks()
        assert len(active) == 1
        assert active[0].scenario == FallbackScenario.HOLIDAY_SKELETON


class TestCheckZoneHealth:
    def test_healthy_zone(self):
        fs = FallbackScheduler()
        f1, f2 = uuid4(), uuid4()
        fs.create_zone("ICU", ["icu"], [f1, f2], minimum_coverage=1)
        health = fs.check_zone_health({f1, f2})
        assert health["ICU"]["healthy"] is True
        assert health["ICU"]["status"] == "GREEN"

    def test_unhealthy_zone(self):
        fs = FallbackScheduler()
        f1, f2 = uuid4(), uuid4()
        fs.create_zone("ICU", ["icu"], [f1, f2], minimum_coverage=2)
        health = fs.check_zone_health(set())  # nobody available
        assert health["ICU"]["healthy"] is False
        assert health["ICU"]["status"] == "RED"

    def test_yellow_zone_with_backup(self):
        fs = FallbackScheduler()
        f1 = uuid4()
        f_backup = uuid4()
        zone = fs.create_zone("Clinic", ["clinic"], [f1], minimum_coverage=1)
        zone.backup_faculty = [f_backup]
        # Dedicated not available but backup is
        health = fs.check_zone_health({f_backup})
        assert health["Clinic"]["healthy"] is False
        assert health["Clinic"]["status"] == "YELLOW"


class TestGetBestFallbackForSituation:
    def test_emergency(self):
        fs = FallbackScheduler()
        assert (
            fs.get_best_fallback_for_situation(0, is_emergency=True)
            == FallbackScenario.MASS_CASUALTY
        )

    def test_pcs_season_heavy_loss(self):
        fs = FallbackScheduler()
        assert (
            fs.get_best_fallback_for_situation(5, is_pcs_season=True)
            == FallbackScenario.PCS_SEASON_50_PERCENT
        )

    def test_holiday(self):
        fs = FallbackScheduler()
        assert (
            fs.get_best_fallback_for_situation(0, is_holiday=True)
            == FallbackScenario.HOLIDAY_SKELETON
        )

    def test_double_loss(self):
        fs = FallbackScheduler()
        assert (
            fs.get_best_fallback_for_situation(2)
            == FallbackScenario.DOUBLE_FACULTY_LOSS
        )

    def test_single_loss(self):
        fs = FallbackScheduler()
        assert (
            fs.get_best_fallback_for_situation(1)
            == FallbackScenario.SINGLE_FACULTY_LOSS
        )

    def test_no_issues(self):
        fs = FallbackScheduler()
        assert fs.get_best_fallback_for_situation(0) is None


class TestGetStatusReport:
    def test_initial_report(self):
        fs = FallbackScheduler()
        report = fs.get_status_report()
        assert report["summary"]["total_fallbacks_available"] == 0
        assert report["summary"]["active_fallbacks"] == 0
        assert len(report["fallbacks"]) == 7  # All scenarios listed

    def test_with_fallbacks(self):
        fs = FallbackScheduler()
        fs.precompute_fallback(
            FallbackScenario.HOLIDAY_SKELETON, date(2026, 1, 1), date(2026, 12, 31)
        )
        report = fs.get_status_report()
        assert report["summary"]["total_fallbacks_available"] == 1
        assert report["fallbacks"]["holiday_skeleton"]["available"] is True


class TestCalculateCoverageRate:
    def test_full_coverage(self):
        fs = FallbackScheduler()
        # 5 weekdays * 2 blocks = 10 expected
        start = date(2026, 1, 5)  # Monday
        end = date(2026, 1, 9)  # Friday
        assignments = [{"block": i} for i in range(10)]
        rate = fs._calculate_coverage_rate(assignments, start, end)
        assert abs(rate - 1.0) < 0.01

    def test_empty_assignments(self):
        fs = FallbackScheduler()
        rate = fs._calculate_coverage_rate([], date(2026, 1, 1), date(2026, 1, 31))
        assert rate == 0.0

    def test_partial_coverage(self):
        fs = FallbackScheduler()
        start = date(2026, 1, 5)  # Monday
        end = date(2026, 1, 9)  # Friday
        # 5 of 10 expected blocks
        assignments = [{"block": i} for i in range(5)]
        rate = fs._calculate_coverage_rate(assignments, start, end)
        assert abs(rate - 0.5) < 0.01
