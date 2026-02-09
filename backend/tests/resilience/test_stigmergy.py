"""Tests for Stigmergy and Swarm Intelligence (pheromone-based preference tracking)."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.resilience.stigmergy import (
    CollectivePreference,
    PreferenceTrail,
    SignalType,
    StigmergicScheduler,
    StigmergyStatus,
    SwapNetwork,
    TrailStrength,
    TrailType,
)


# ==================== Enums ====================


class TestTrailType:
    def test_values(self):
        assert TrailType.PREFERENCE == "preference"
        assert TrailType.AVOIDANCE == "avoidance"
        assert TrailType.SWAP_AFFINITY == "swap_affinity"
        assert TrailType.WORKLOAD == "workload"
        assert TrailType.SEQUENCE == "sequence"


class TestTrailStrength:
    def test_values(self):
        assert TrailStrength.VERY_WEAK == "very_weak"
        assert TrailStrength.STRONG == "strong"
        assert TrailStrength.VERY_STRONG == "very_strong"


class TestSignalType:
    def test_values(self):
        assert SignalType.EXPLICIT_PREFERENCE == "explicit_preference"
        assert SignalType.COMPLETED_SWAP == "completed_swap"
        assert SignalType.LOW_SATISFACTION == "low_satisfaction"


# ==================== PreferenceTrail ====================


class TestPreferenceTrail:
    def _make_trail(self, strength=0.5, evaporation_rate=0.1):
        return PreferenceTrail(
            id=uuid4(),
            faculty_id=uuid4(),
            trail_type=TrailType.PREFERENCE,
            strength=strength,
            evaporation_rate=evaporation_rate,
        )

    def test_defaults(self):
        t = self._make_trail()
        assert t.strength == 0.5
        assert t.peak_strength == 0.5
        assert t.reinforcement_count == 0
        assert t.min_strength == 0.01
        assert t.max_strength == 1.0

    def test_reinforce_increases_strength(self):
        t = self._make_trail(strength=0.5)
        t.reinforce(SignalType.EXPLICIT_PREFERENCE, 0.2)
        assert t.strength == 0.7

    def test_reinforce_capped_at_max(self):
        t = self._make_trail(strength=0.9)
        t.reinforce(SignalType.EXPLICIT_PREFERENCE, 0.5)
        assert t.strength == 1.0

    def test_reinforce_updates_peak(self):
        t = self._make_trail(strength=0.5)
        t.reinforce(SignalType.HIGH_SATISFACTION, 0.3)
        assert t.peak_strength == 0.8

    def test_reinforce_increments_count(self):
        t = self._make_trail()
        t.reinforce(SignalType.ACCEPTED_ASSIGNMENT, 0.1)
        t.reinforce(SignalType.ACCEPTED_ASSIGNMENT, 0.1)
        assert t.reinforcement_count == 2

    def test_reinforce_adds_to_signal_history(self):
        t = self._make_trail()
        t.reinforce(SignalType.EXPLICIT_PREFERENCE, 0.1)
        assert len(t.signal_history) == 1
        assert t.signal_history[0][1] == SignalType.EXPLICIT_PREFERENCE

    def test_signal_history_trimmed_at_100(self):
        t = self._make_trail()
        for _ in range(110):
            t.reinforce(SignalType.ACCEPTED_ASSIGNMENT, 0.001)
        assert len(t.signal_history) == 100

    def test_weaken_decreases_strength(self):
        t = self._make_trail(strength=0.5)
        t.weaken(SignalType.LOW_SATISFACTION, 0.2)
        assert t.strength == 0.3

    def test_weaken_capped_at_min(self):
        t = self._make_trail(strength=0.05)
        t.weaken(SignalType.REQUESTED_SWAP, 0.5)
        assert t.strength == 0.01

    def test_evaporate_reduces_strength(self):
        t = self._make_trail(strength=0.8, evaporation_rate=0.1)
        t.evaporate(days_elapsed=5.0)
        # exp(-0.1 * 5) = exp(-0.5) ≈ 0.607
        assert t.strength < 0.8
        assert t.strength > 0.01

    def test_evaporate_zero_days_no_change(self):
        t = self._make_trail(strength=0.5)
        t.evaporate(days_elapsed=0)
        assert t.strength == 0.5

    def test_evaporate_negative_days_no_change(self):
        t = self._make_trail(strength=0.5)
        t.evaporate(days_elapsed=-1)
        assert t.strength == 0.5

    def test_evaporate_never_below_min(self):
        t = self._make_trail(strength=0.1, evaporation_rate=1.0)
        t.evaporate(days_elapsed=100)
        assert t.strength == t.min_strength

    def test_strength_category_very_weak(self):
        t = self._make_trail(strength=0.1)
        assert t.strength_category == TrailStrength.VERY_WEAK

    def test_strength_category_weak(self):
        t = self._make_trail(strength=0.3)
        assert t.strength_category == TrailStrength.WEAK

    def test_strength_category_moderate(self):
        t = self._make_trail(strength=0.5)
        assert t.strength_category == TrailStrength.MODERATE

    def test_strength_category_strong(self):
        t = self._make_trail(strength=0.7)
        assert t.strength_category == TrailStrength.STRONG

    def test_strength_category_very_strong(self):
        t = self._make_trail(strength=0.9)
        assert t.strength_category == TrailStrength.VERY_STRONG

    def test_age_days(self):
        t = self._make_trail()
        t.created_at = datetime.now() - timedelta(days=3)
        assert abs(t.age_days - 3.0) < 0.1

    def test_days_since_reinforced(self):
        t = self._make_trail()
        t.last_reinforced = datetime.now() - timedelta(days=2)
        assert abs(t.days_since_reinforced - 2.0) < 0.1


# ==================== CollectivePreference ====================


class TestCollectivePreference:
    def _make_collective(self, net_preference=0.0):
        return CollectivePreference(
            slot_type="monday_am",
            total_preference_strength=0.5,
            total_avoidance_strength=0.5 - net_preference,
            net_preference=net_preference,
            faculty_count=5,
            confidence=0.8,
            trails=[],
        )

    def test_is_popular(self):
        cp = self._make_collective(net_preference=0.5)
        assert cp.is_popular is True
        assert cp.is_unpopular is False

    def test_is_unpopular(self):
        cp = self._make_collective(net_preference=-0.5)
        assert cp.is_unpopular is True
        assert cp.is_popular is False

    def test_neutral(self):
        cp = self._make_collective(net_preference=0.0)
        assert cp.is_popular is False
        assert cp.is_unpopular is False


# ==================== SwapNetwork ====================


class TestSwapNetwork:
    def test_get_best_partners(self):
        f1, f2, f3 = uuid4(), uuid4(), uuid4()
        sn = SwapNetwork(
            edges={(f1, f2): 0.9, (f1, f3): 0.5},
            successful_swaps={(f1, f2): 3, (f1, f3): 1},
            failed_swaps={},
        )
        partners = sn.get_best_partners(f1, top_n=2)
        assert len(partners) == 2
        assert partners[0][0] == f2  # Highest affinity first
        assert partners[0][1] == 0.9

    def test_get_best_partners_no_matches(self):
        sn = SwapNetwork(edges={}, successful_swaps={}, failed_swaps={})
        assert sn.get_best_partners(uuid4()) == []

    def test_top_n_limits(self):
        f1, f2, f3, f4 = uuid4(), uuid4(), uuid4(), uuid4()
        sn = SwapNetwork(
            edges={(f1, f2): 0.5, (f1, f3): 0.7, (f1, f4): 0.3},
            successful_swaps={},
            failed_swaps={},
        )
        partners = sn.get_best_partners(f1, top_n=2)
        assert len(partners) == 2


# ==================== StigmergicScheduler ====================


class TestStigmergicSchedulerInit:
    def test_defaults(self):
        ss = StigmergicScheduler()
        assert ss.evaporation_rate == 0.1
        assert ss.reinforcement_amount == 0.1
        assert ss.evaporation_interval_hours == 24.0
        assert ss.trails == {}

    def test_custom(self):
        ss = StigmergicScheduler(
            evaporation_rate=0.2,
            reinforcement_amount=0.05,
            evaporation_interval_hours=12.0,
        )
        assert ss.evaporation_rate == 0.2
        assert ss.reinforcement_amount == 0.05


class TestRecordPreference:
    def test_creates_new_trail(self):
        ss = StigmergicScheduler()
        fid = uuid4()
        trail = ss.record_preference(
            faculty_id=fid,
            trail_type=TrailType.PREFERENCE,
            slot_type="monday_am",
            strength=0.7,
        )
        assert trail.faculty_id == fid
        assert trail.strength == 0.7
        assert len(ss.trails) == 1

    def test_reinforces_existing_trail(self):
        ss = StigmergicScheduler()
        fid = uuid4()
        t1 = ss.record_preference(fid, TrailType.PREFERENCE, slot_type="monday_am")
        t2 = ss.record_preference(fid, TrailType.PREFERENCE, slot_type="monday_am")
        assert t1.id == t2.id  # Same trail
        assert t2.reinforcement_count == 1  # Was reinforced
        assert len(ss.trails) == 1  # No duplicate

    def test_different_types_create_separate_trails(self):
        ss = StigmergicScheduler()
        fid = uuid4()
        ss.record_preference(fid, TrailType.PREFERENCE, slot_type="monday_am")
        ss.record_preference(fid, TrailType.AVOIDANCE, slot_type="monday_am")
        assert len(ss.trails) == 2


class TestRecordSignal:
    def test_preference_signal(self):
        ss = StigmergicScheduler()
        fid = uuid4()
        ss.record_signal(fid, SignalType.EXPLICIT_PREFERENCE, slot_type="monday_am")
        trails = ss.get_faculty_preferences(fid)
        assert len(trails) == 1
        assert trails[0].trail_type == TrailType.PREFERENCE

    def test_avoidance_signal(self):
        ss = StigmergicScheduler()
        fid = uuid4()
        ss.record_signal(fid, SignalType.LOW_SATISFACTION, slot_type="friday_pm")
        trails = ss.get_faculty_preferences(fid)
        assert len(trails) == 1
        assert trails[0].trail_type == TrailType.AVOIDANCE

    def test_swap_signal(self):
        ss = StigmergicScheduler()
        f1, f2 = uuid4(), uuid4()
        ss.record_signal(f1, SignalType.COMPLETED_SWAP, target_faculty_id=f2)
        trails = ss.get_faculty_preferences(f1)
        assert len(trails) == 1
        assert trails[0].trail_type == TrailType.SWAP_AFFINITY


class TestEvaporateTrails:
    def test_force_evaporation(self):
        ss = StigmergicScheduler(evaporation_rate=0.5)
        fid = uuid4()
        ss.record_preference(fid, TrailType.PREFERENCE, strength=0.8)
        # Move last evaporation back
        ss.last_evaporation = datetime.now() - timedelta(days=5)
        ss.evaporate_trails(force=True)
        trail = list(ss.trails.values())[0]
        assert trail.strength < 0.8

    def test_skip_if_not_due(self):
        ss = StigmergicScheduler(evaporation_interval_hours=24.0)
        fid = uuid4()
        ss.record_preference(fid, TrailType.PREFERENCE, strength=0.8)
        ss.evaporate_trails()  # Should not evaporate (just created)
        trail = list(ss.trails.values())[0]
        assert trail.strength == 0.8


class TestGetFacultyPreferences:
    def test_returns_sorted_by_strength(self):
        ss = StigmergicScheduler()
        fid = uuid4()
        ss.record_preference(fid, TrailType.PREFERENCE, slot_type="a", strength=0.3)
        ss.record_preference(fid, TrailType.PREFERENCE, slot_type="b", strength=0.9)
        trails = ss.get_faculty_preferences(fid)
        assert trails[0].strength >= trails[1].strength

    def test_filter_by_type(self):
        ss = StigmergicScheduler()
        fid = uuid4()
        ss.record_preference(fid, TrailType.PREFERENCE, slot_type="a")
        ss.record_preference(fid, TrailType.AVOIDANCE, slot_type="b")
        prefs = ss.get_faculty_preferences(fid, trail_type=TrailType.PREFERENCE)
        assert all(t.trail_type == TrailType.PREFERENCE for t in prefs)

    def test_filter_by_min_strength(self):
        ss = StigmergicScheduler()
        fid = uuid4()
        ss.record_preference(fid, TrailType.PREFERENCE, slot_type="a", strength=0.05)
        ss.record_preference(fid, TrailType.PREFERENCE, slot_type="b", strength=0.5)
        trails = ss.get_faculty_preferences(fid, min_strength=0.1)
        assert len(trails) == 1
        assert trails[0].slot_type == "b"

    def test_unknown_faculty_returns_empty(self):
        ss = StigmergicScheduler()
        assert ss.get_faculty_preferences(uuid4()) == []


class TestGetSwapNetwork:
    def test_empty_network(self):
        ss = StigmergicScheduler()
        sn = ss.get_swap_network()
        assert sn.edges == {}

    def test_swap_affinity_creates_edge(self):
        ss = StigmergicScheduler()
        f1, f2 = uuid4(), uuid4()
        ss.record_preference(
            f1, TrailType.SWAP_AFFINITY, target_faculty_id=f2, strength=0.8
        )
        sn = ss.get_swap_network()
        assert len(sn.edges) == 1


class TestSuggestAssignments:
    def test_base_score_without_trails(self):
        ss = StigmergicScheduler()
        slot_id = uuid4()
        faculty = [uuid4(), uuid4()]
        suggestions = ss.suggest_assignments(slot_id, "monday_am", faculty)
        assert len(suggestions) == 2
        # Base score is 0.5
        for _, score, _ in suggestions:
            assert abs(score - 0.5) < 0.01

    def test_preference_boosts_score(self):
        ss = StigmergicScheduler()
        slot_id = uuid4()
        f1, f2 = uuid4(), uuid4()
        ss.record_preference(
            f1, TrailType.PREFERENCE, slot_type="monday_am", strength=0.9
        )
        suggestions = ss.suggest_assignments(slot_id, "monday_am", [f1, f2])
        # f1 should score higher than f2
        scores = {s[0]: s[1] for s in suggestions}
        assert scores[f1] > scores[f2]

    def test_avoidance_lowers_score(self):
        ss = StigmergicScheduler()
        slot_id = uuid4()
        f1 = uuid4()
        ss.record_preference(
            f1, TrailType.AVOIDANCE, slot_type="monday_am", strength=0.9
        )
        suggestions = ss.suggest_assignments(slot_id, "monday_am", [f1])
        assert suggestions[0][1] < 0.5  # Below base

    def test_sorted_by_score_descending(self):
        ss = StigmergicScheduler()
        slot_id = uuid4()
        f1, f2, f3 = uuid4(), uuid4(), uuid4()
        ss.record_preference(f1, TrailType.PREFERENCE, slot_type="x", strength=0.9)
        ss.record_preference(f3, TrailType.PREFERENCE, slot_type="x", strength=0.5)
        suggestions = ss.suggest_assignments(slot_id, "x", [f1, f2, f3])
        scores = [s[1] for s in suggestions]
        assert scores == sorted(scores, reverse=True)


class TestDetectPatterns:
    def test_empty_scheduler(self):
        ss = StigmergicScheduler()
        patterns = ss.detect_patterns()
        assert patterns["total_patterns"] == 0

    def test_detects_popular_slots(self):
        ss = StigmergicScheduler()
        for _ in range(5):
            fid = uuid4()
            ss.record_preference(
                fid, TrailType.PREFERENCE, slot_type="monday_am", strength=0.8
            )
        patterns = ss.detect_patterns()
        popular_names = [s[0] for s in patterns["popular_slots"]]
        assert "monday_am" in popular_names

    def test_detects_unpopular_slots(self):
        ss = StigmergicScheduler()
        for _ in range(5):
            fid = uuid4()
            ss.record_preference(
                fid, TrailType.AVOIDANCE, slot_type="friday_night", strength=0.8
            )
        patterns = ss.detect_patterns()
        unpopular_names = [s[0] for s in patterns["unpopular_slots"]]
        assert "friday_night" in unpopular_names


class TestPruneWeakTrails:
    def test_prunes_below_threshold(self):
        ss = StigmergicScheduler()
        fid = uuid4()
        ss.record_preference(fid, TrailType.PREFERENCE, slot_type="a", strength=0.02)
        ss.record_preference(fid, TrailType.PREFERENCE, slot_type="b", strength=0.5)
        pruned = ss.prune_weak_trails(threshold=0.05)
        assert pruned == 1
        assert len(ss.trails) == 1

    def test_nothing_to_prune(self):
        ss = StigmergicScheduler()
        fid = uuid4()
        ss.record_preference(fid, TrailType.PREFERENCE, strength=0.5)
        assert ss.prune_weak_trails() == 0


class TestGetCollectivePreference:
    def test_no_trails_returns_none(self):
        ss = StigmergicScheduler()
        assert ss.get_collective_preference(slot_type="monday_am") is None

    def test_returns_collective(self):
        ss = StigmergicScheduler()
        for _ in range(3):
            fid = uuid4()
            ss.record_preference(
                fid, TrailType.PREFERENCE, slot_type="monday_am", strength=0.7
            )
        cp = ss.get_collective_preference(slot_type="monday_am")
        assert cp is not None
        assert isinstance(cp, CollectivePreference)
        assert cp.faculty_count == 3

    def test_by_slot_id(self):
        ss = StigmergicScheduler()
        sid = uuid4()
        fid = uuid4()
        ss.record_preference(fid, TrailType.PREFERENCE, slot_id=sid, strength=0.6)
        cp = ss.get_collective_preference(slot_id=sid)
        assert cp is not None


class TestGetStatus:
    def test_empty_status(self):
        ss = StigmergicScheduler()
        status = ss.get_status()
        assert isinstance(status, StigmergyStatus)
        assert status.total_trails == 0
        assert status.active_trails == 0
        assert status.average_strength == 0.0

    def test_status_with_trails(self):
        ss = StigmergicScheduler()
        for _ in range(5):
            fid = uuid4()
            ss.record_preference(
                fid, TrailType.PREFERENCE, slot_type="am", strength=0.6
            )
        status = ss.get_status()
        assert status.total_trails == 5
        assert status.active_trails == 5
        assert status.average_strength > 0.5
        assert len(status.recommendations) > 0
