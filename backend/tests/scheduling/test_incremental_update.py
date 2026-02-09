"""Tests for IncrementalScheduleUpdater (pure dict logic, no DB required)."""

import asyncio
from datetime import date, timedelta

import pytest

from app.scheduling.optimizer.incremental_update import IncrementalScheduleUpdater


# ==================== Helpers ====================


def _run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


def _schedule(
    assignments: list[dict] | None = None,
    rotations: list[dict] | None = None,
) -> dict:
    """Build a minimal schedule dict."""
    s: dict = {"assignments": assignments or []}
    if rotations is not None:
        s["rotations"] = rotations
    return s


def _assign(
    person_id: str,
    block_date: date,
    rotation_id: str,
    priority: int = 5,
) -> dict:
    return {
        "person_id": person_id,
        "block_date": block_date,
        "rotation_id": rotation_id,
        "priority": priority,
    }


def _person(
    pid: str = "p1",
    ptype: str = "resident",
    quals: list[str] | None = None,
) -> dict:
    d: dict = {"id": pid, "type": ptype}
    if quals:
        d["qualifications"] = quals
    return d


# ==================== Constructor Tests ====================


class TestInit:
    """Test IncrementalScheduleUpdater constructor."""

    def test_initial_counters(self):
        u = IncrementalScheduleUpdater()
        assert u.update_count == 0
        assert u.conflict_count == 0


# ==================== remove_person Tests ====================


class TestRemovePerson:
    """Test remove_person method."""

    def test_remove_all_assignments(self):
        s = _schedule(
            [
                _assign("p1", date(2025, 1, 6), "r1"),
                _assign("p1", date(2025, 1, 7), "r1"),
                _assign("p2", date(2025, 1, 6), "r2"),
            ]
        )
        u = IncrementalScheduleUpdater()
        result = _run(u.remove_person(s, "p1"))
        assert len(result["assignments"]) == 1
        assert result["assignments"][0]["person_id"] == "p2"

    def test_remove_with_date_range(self):
        s = _schedule(
            [
                _assign("p1", date(2025, 1, 6), "r1"),
                _assign("p1", date(2025, 1, 7), "r1"),
                _assign("p1", date(2025, 1, 10), "r1"),
            ]
        )
        u = IncrementalScheduleUpdater()
        result = _run(
            u.remove_person(s, "p1", date_range=(date(2025, 1, 6), date(2025, 1, 7)))
        )
        # Only assignments in range removed
        assert len(result["assignments"]) == 1
        assert result["assignments"][0]["block_date"] == date(2025, 1, 10)

    def test_remove_nonexistent_person(self):
        s = _schedule([_assign("p1", date(2025, 1, 6), "r1")])
        u = IncrementalScheduleUpdater()
        result = _run(u.remove_person(s, "p_missing"))
        # Nothing removed
        assert len(result["assignments"]) == 1

    def test_remove_increments_update_count(self):
        u = IncrementalScheduleUpdater()
        _run(u.remove_person(_schedule(), "p1"))
        assert u.update_count == 1

    def test_remove_empty_schedule(self):
        u = IncrementalScheduleUpdater()
        result = _run(u.remove_person(_schedule(), "p1"))
        assert result["assignments"] == []


# ==================== swap_assignments Tests ====================


class TestSwapAssignments:
    """Test swap_assignments method."""

    def test_basic_swap(self):
        s = _schedule(
            [
                _assign("p1", date(2025, 1, 6), "r1"),
                _assign("p2", date(2025, 1, 7), "r2"),
            ]
        )
        u = IncrementalScheduleUpdater()
        result = _run(
            u.swap_assignments(s, "p1", "p2", date(2025, 1, 6), date(2025, 1, 7), {})
        )
        # Rotations swapped
        a1 = next(a for a in result["assignments"] if a["person_id"] == "p1")
        a2 = next(a for a in result["assignments"] if a["person_id"] == "p2")
        assert a1["rotation_id"] == "r2"
        assert a2["rotation_id"] == "r1"

    def test_swap_increments_update_count(self):
        s = _schedule(
            [
                _assign("p1", date(2025, 1, 6), "r1"),
                _assign("p2", date(2025, 1, 7), "r2"),
            ]
        )
        u = IncrementalScheduleUpdater()
        _run(u.swap_assignments(s, "p1", "p2", date(2025, 1, 6), date(2025, 1, 7), {}))
        assert u.update_count == 1

    def test_swap_missing_assign1(self):
        """If first assignment not found, schedule unchanged."""
        s = _schedule([_assign("p2", date(2025, 1, 7), "r2")])
        u = IncrementalScheduleUpdater()
        result = _run(
            u.swap_assignments(s, "p1", "p2", date(2025, 1, 6), date(2025, 1, 7), {})
        )
        assert result["assignments"][0]["rotation_id"] == "r2"
        assert u.update_count == 0

    def test_swap_missing_assign2(self):
        """If second assignment not found, schedule unchanged."""
        s = _schedule([_assign("p1", date(2025, 1, 6), "r1")])
        u = IncrementalScheduleUpdater()
        result = _run(
            u.swap_assignments(s, "p1", "p2", date(2025, 1, 6), date(2025, 1, 7), {})
        )
        assert result["assignments"][0]["rotation_id"] == "r1"
        assert u.update_count == 0

    def test_swap_same_person(self):
        """Swapping same person on two different dates works."""
        s = _schedule(
            [
                _assign("p1", date(2025, 1, 6), "r1"),
                _assign("p1", date(2025, 1, 7), "r2"),
            ]
        )
        u = IncrementalScheduleUpdater()
        # person1_id and person2_id are both "p1"
        result = _run(
            u.swap_assignments(s, "p1", "p1", date(2025, 1, 6), date(2025, 1, 7), {})
        )
        a1 = next(
            a for a in result["assignments"] if a["block_date"] == date(2025, 1, 6)
        )
        a2 = next(
            a for a in result["assignments"] if a["block_date"] == date(2025, 1, 7)
        )
        assert a1["rotation_id"] == "r2"
        assert a2["rotation_id"] == "r1"

    def test_swap_preserves_other_assignments(self):
        s = _schedule(
            [
                _assign("p1", date(2025, 1, 6), "r1"),
                _assign("p2", date(2025, 1, 7), "r2"),
                _assign("p3", date(2025, 1, 8), "r3"),
            ]
        )
        u = IncrementalScheduleUpdater()
        result = _run(
            u.swap_assignments(s, "p1", "p2", date(2025, 1, 6), date(2025, 1, 7), {})
        )
        p3_assign = next(a for a in result["assignments"] if a["person_id"] == "p3")
        assert p3_assign["rotation_id"] == "r3"


# ==================== update_rotation_capacity Tests ====================


class TestUpdateRotationCapacity:
    """Test update_rotation_capacity method."""

    def test_no_excess(self):
        """Within capacity, nothing removed."""
        s = _schedule(
            [
                _assign("p1", date(2025, 1, 6), "r1"),
            ]
        )
        u = IncrementalScheduleUpdater()
        result = _run(
            u.update_rotation_capacity(s, "r1", 2, (date(2025, 1, 6), date(2025, 1, 6)))
        )
        assert len(result["assignments"]) == 1

    def test_removes_excess(self):
        """Over capacity: excess removed by lowest priority."""
        s = _schedule(
            [
                _assign("p1", date(2025, 1, 6), "r1", priority=10),
                _assign("p2", date(2025, 1, 6), "r1", priority=1),
                _assign("p3", date(2025, 1, 6), "r1", priority=5),
            ]
        )
        u = IncrementalScheduleUpdater()
        result = _run(
            u.update_rotation_capacity(s, "r1", 1, (date(2025, 1, 6), date(2025, 1, 6)))
        )
        # Capacity 1 -> remove 2 lowest priority (p2=1, p3=5)
        assert len(result["assignments"]) == 1
        assert result["assignments"][0]["person_id"] == "p1"

    def test_increments_conflict_count(self):
        s = _schedule(
            [
                _assign("p1", date(2025, 1, 6), "r1"),
                _assign("p2", date(2025, 1, 6), "r1"),
            ]
        )
        u = IncrementalScheduleUpdater()
        _run(
            u.update_rotation_capacity(s, "r1", 1, (date(2025, 1, 6), date(2025, 1, 6)))
        )
        assert u.conflict_count == 1  # 1 excess removed

    def test_increments_update_count(self):
        u = IncrementalScheduleUpdater()
        _run(
            u.update_rotation_capacity(
                _schedule(), "r1", 5, (date(2025, 1, 6), date(2025, 1, 6))
            )
        )
        assert u.update_count == 1

    def test_multi_day_range(self):
        """Capacity applied to each day independently."""
        s = _schedule(
            [
                _assign("p1", date(2025, 1, 6), "r1"),
                _assign("p2", date(2025, 1, 6), "r1"),
                _assign("p1", date(2025, 1, 7), "r1"),
            ]
        )
        u = IncrementalScheduleUpdater()
        result = _run(
            u.update_rotation_capacity(s, "r1", 1, (date(2025, 1, 6), date(2025, 1, 7)))
        )
        # Day 6: 2 assignments -> remove 1; Day 7: 1 assignment -> ok
        assert len(result["assignments"]) == 2

    def test_different_rotation_unaffected(self):
        s = _schedule(
            [
                _assign("p1", date(2025, 1, 6), "r1"),
                _assign("p2", date(2025, 1, 6), "r2"),
            ]
        )
        u = IncrementalScheduleUpdater()
        result = _run(
            u.update_rotation_capacity(s, "r1", 0, (date(2025, 1, 6), date(2025, 1, 6)))
        )
        # r1 removed, r2 stays
        assert len(result["assignments"]) == 1
        assert result["assignments"][0]["rotation_id"] == "r2"


# ==================== _find_available_slots Tests ====================


class TestFindAvailableSlots:
    """Test _find_available_slots method."""

    def test_all_dates_available(self):
        s = _schedule()
        u = IncrementalScheduleUpdater()
        slots = u._find_available_slots(
            s, _person("p1"), (date(2025, 1, 6), date(2025, 1, 8)), {}
        )
        assert len(slots) == 3  # 3 days

    def test_excludes_already_assigned_dates(self):
        s = _schedule([_assign("p1", date(2025, 1, 7), "r1")])
        u = IncrementalScheduleUpdater()
        slots = u._find_available_slots(
            s, _person("p1"), (date(2025, 1, 6), date(2025, 1, 8)), {}
        )
        # Day 7 excluded (already assigned)
        assert len(slots) == 2
        dates = [sl["date"] for sl in slots]
        assert date(2025, 1, 7) not in dates

    def test_single_day_range(self):
        u = IncrementalScheduleUpdater()
        slots = u._find_available_slots(
            _schedule(), _person("p1"), (date(2025, 1, 6), date(2025, 1, 6)), {}
        )
        assert len(slots) == 1

    def test_slot_contains_rotations(self):
        """Each slot has a rotations list."""
        s = _schedule(rotations=[{"id": "r1"}, {"id": "r2"}])
        u = IncrementalScheduleUpdater()
        slots = u._find_available_slots(
            s, _person("p1"), (date(2025, 1, 6), date(2025, 1, 6)), {}
        )
        assert "rotations" in slots[0]
        assert isinstance(slots[0]["rotations"], list)


# ==================== _get_available_rotations Tests ====================


class TestGetAvailableRotations:
    """Test _get_available_rotations method."""

    def test_all_rotations_available(self):
        s = _schedule(rotations=[{"id": "r1"}, {"id": "r2"}])
        u = IncrementalScheduleUpdater()
        rots = u._get_available_rotations(s, _person(), date(2025, 1, 6), {})
        assert "r1" in rots
        assert "r2" in rots

    def test_capacity_full_excluded(self):
        s = _schedule(
            assignments=[_assign("p_other", date(2025, 1, 6), "r1")],
            rotations=[{"id": "r1", "max_residents": 1}, {"id": "r2"}],
        )
        u = IncrementalScheduleUpdater()
        rots = u._get_available_rotations(s, _person(), date(2025, 1, 6), {})
        assert "r1" not in rots
        assert "r2" in rots

    def test_capacity_from_constraints(self):
        s = _schedule(
            assignments=[_assign("p_other", date(2025, 1, 6), "r1")],
            rotations=[{"id": "r1"}],
        )
        u = IncrementalScheduleUpdater()
        constraints = {"rotation_capacities": {"r1": 1}}
        rots = u._get_available_rotations(s, _person(), date(2025, 1, 6), constraints)
        assert "r1" not in rots

    def test_qualifications_respected(self):
        s = _schedule(rotations=[{"id": "r1", "required_qualifications": ["ICU"]}])
        u = IncrementalScheduleUpdater()
        # Person without quals
        rots = u._get_available_rotations(s, _person(), date(2025, 1, 6), {})
        assert "r1" not in rots
        # Person with quals
        rots = u._get_available_rotations(
            s, _person(quals=["ICU"]), date(2025, 1, 6), {}
        )
        assert "r1" in rots

    def test_fallback_to_existing_assignments(self):
        """No rotations key -> extracts rotation IDs from assignments."""
        s = _schedule(
            assignments=[
                _assign("p_other", date(2025, 1, 5), "r1"),
                _assign("p_other", date(2025, 1, 5), "r2"),
            ]
        )
        u = IncrementalScheduleUpdater()
        rots = u._get_available_rotations(s, _person(), date(2025, 1, 6), {})
        assert set(rots) == {"r1", "r2"}

    def test_empty_schedule_no_rotations(self):
        u = IncrementalScheduleUpdater()
        rots = u._get_available_rotations(_schedule(), _person(), date(2025, 1, 6), {})
        assert rots == []

    def test_default_capacity_allows(self):
        """Default capacity of 999 allows assignment."""
        s = _schedule(rotations=[{"id": "r1"}])
        u = IncrementalScheduleUpdater()
        rots = u._get_available_rotations(s, _person(), date(2025, 1, 6), {})
        assert "r1" in rots

    def test_custom_default_capacity(self):
        s = _schedule(
            assignments=[_assign("p_other", date(2025, 1, 6), "r1")],
            rotations=[{"id": "r1"}],
        )
        u = IncrementalScheduleUpdater()
        constraints = {"default_rotation_capacity": 1}
        rots = u._get_available_rotations(s, _person(), date(2025, 1, 6), constraints)
        assert "r1" not in rots


# ==================== _assign_to_slots Tests ====================


class TestAssignToSlots:
    """Test _assign_to_slots method."""

    def test_assigns_first_rotation(self):
        u = IncrementalScheduleUpdater()
        slots = [{"date": date(2025, 1, 6), "rotations": ["r1", "r2"]}]
        result = u._assign_to_slots(_person("p1"), slots, {})
        assert len(result) == 1
        assert result[0]["rotation_id"] == "r1"
        assert result[0]["person_id"] == "p1"
        assert result[0]["block_date"] == date(2025, 1, 6)

    def test_skips_empty_rotation_slots(self):
        u = IncrementalScheduleUpdater()
        slots = [
            {"date": date(2025, 1, 6), "rotations": ["r1"]},
            {"date": date(2025, 1, 7), "rotations": []},
        ]
        result = u._assign_to_slots(_person("p1"), slots, {})
        assert len(result) == 1
        assert result[0]["block_date"] == date(2025, 1, 6)

    def test_multiple_slots(self):
        u = IncrementalScheduleUpdater()
        slots = [
            {"date": date(2025, 1, 6), "rotations": ["r1"]},
            {"date": date(2025, 1, 7), "rotations": ["r2"]},
            {"date": date(2025, 1, 8), "rotations": ["r3"]},
        ]
        result = u._assign_to_slots(_person("p1"), slots, {})
        assert len(result) == 3

    def test_empty_slots(self):
        u = IncrementalScheduleUpdater()
        result = u._assign_to_slots(_person("p1"), [], {})
        assert result == []

    def test_priority_defaults_to_5(self):
        u = IncrementalScheduleUpdater()
        slots = [{"date": date(2025, 1, 6), "rotations": ["r1"]}]
        result = u._assign_to_slots(_person(), slots, {})
        assert result[0]["priority"] == 5


# ==================== _would_violate_constraints Tests ====================


class TestWouldViolateConstraints:
    """Test _would_violate_constraints method."""

    def test_always_returns_false(self):
        """Current implementation is simplified and always returns False."""
        u = IncrementalScheduleUpdater()
        result = u._would_violate_constraints(
            _schedule(),
            _assign("p1", date(2025, 1, 6), "r1"),
            _assign("p2", date(2025, 1, 7), "r2"),
            {},
        )
        assert result is False


# ==================== add_person Tests ====================


class TestAddPerson:
    """Test add_person method."""

    def test_adds_to_empty_schedule(self):
        s = _schedule(rotations=[{"id": "r1"}])
        u = IncrementalScheduleUpdater()
        result = _run(
            u.add_person(s, _person("p1"), (date(2025, 1, 6), date(2025, 1, 8)), {})
        )
        # 3 days available, rotation r1 available -> 3 new assignments
        assert len(result["assignments"]) == 3
        assert all(a["person_id"] == "p1" for a in result["assignments"])

    def test_skips_already_assigned_dates(self):
        s = _schedule(
            assignments=[_assign("p1", date(2025, 1, 7), "r1")],
            rotations=[{"id": "r1"}],
        )
        u = IncrementalScheduleUpdater()
        result = _run(
            u.add_person(s, _person("p1"), (date(2025, 1, 6), date(2025, 1, 8)), {})
        )
        # Original 1 + 2 new (day 6, day 8)
        assert len(result["assignments"]) == 3

    def test_increments_update_count(self):
        u = IncrementalScheduleUpdater()
        _run(
            u.add_person(
                _schedule(rotations=[{"id": "r1"}]),
                _person("p1"),
                (date(2025, 1, 6), date(2025, 1, 6)),
                {},
            )
        )
        assert u.update_count == 1

    def test_no_rotations_adds_nothing(self):
        s = _schedule()  # No rotations
        u = IncrementalScheduleUpdater()
        result = _run(
            u.add_person(s, _person("p1"), (date(2025, 1, 6), date(2025, 1, 8)), {})
        )
        assert len(result["assignments"]) == 0


# ==================== get_stats Tests ====================


class TestGetStats:
    """Test get_stats method."""

    def test_initial_stats(self):
        u = IncrementalScheduleUpdater()
        stats = _run(u.get_stats())
        assert stats["total_updates"] == 0
        assert stats["conflicts"] == 0
        assert stats["conflict_rate"] == 0.0

    def test_stats_after_operations(self):
        s = _schedule(
            [
                _assign("p1", date(2025, 1, 6), "r1"),
                _assign("p2", date(2025, 1, 6), "r1"),
            ]
        )
        u = IncrementalScheduleUpdater()
        # Remove -> 1 update
        _run(u.remove_person(s, "p1"))
        # Capacity reduce -> 1 update + conflicts
        s2 = _schedule(
            [
                _assign("p1", date(2025, 1, 6), "r1"),
                _assign("p2", date(2025, 1, 6), "r1"),
            ]
        )
        _run(
            u.update_rotation_capacity(
                s2, "r1", 1, (date(2025, 1, 6), date(2025, 1, 6))
            )
        )
        stats = _run(u.get_stats())
        assert stats["total_updates"] == 2
        assert stats["conflicts"] == 1
        assert stats["conflict_rate"] == pytest.approx(50.0)

    def test_stats_keys(self):
        u = IncrementalScheduleUpdater()
        stats = _run(u.get_stats())
        assert set(stats.keys()) == {"total_updates", "conflicts", "conflict_rate"}
