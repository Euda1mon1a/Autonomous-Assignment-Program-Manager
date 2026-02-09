"""Tests for optimizer.constraint_pruning (pure dict logic, no DB required)."""

from datetime import date

import pytest

from app.scheduling.optimizer.constraint_pruning import (
    ConstraintPruner,
    prune_infeasible_assignments,
)


# ==================== Helpers ====================


def _person(
    pid: str = "p1",
    ptype: str = "resident",
    pgy: int = 2,
    specialties: list[str] | None = None,
    unavailable: list[date] | None = None,
) -> dict:
    d = {"id": pid, "type": ptype, "pgy_level": pgy}
    if specialties:
        d["specialties"] = specialties
    if unavailable:
        d["unavailable_dates"] = unavailable
    return d


def _rotation(
    rid: str = "r1",
    allowed_types: list[str] | None = None,
    min_pgy: int | None = None,
    max_pgy: int | None = None,
    required_specs: list[str] | None = None,
    time_of_day: str | None = None,
    max_people: int | None = None,
) -> dict:
    d: dict = {"id": rid}
    if allowed_types is not None:
        d["allowed_person_types"] = allowed_types
    if min_pgy is not None:
        d["min_pgy_level"] = min_pgy
    if max_pgy is not None:
        d["max_pgy_level"] = max_pgy
    if required_specs is not None:
        d["required_specialties"] = required_specs
    if time_of_day is not None:
        d["time_of_day"] = time_of_day
    if max_people is not None:
        d["max_people"] = max_people
    return d


def _block(bid: str = "b1", d: date | None = None, is_am: bool = True) -> dict:
    return {"id": bid, "date": d or date(2025, 1, 6), "is_am": is_am}


# ==================== ConstraintPruner Init ====================


class TestConstraintPrunerInit:
    """Test ConstraintPruner constructor."""

    def test_initial_counters(self):
        pruner = ConstraintPruner()
        assert pruner.pruned_count == 0
        assert pruner.total_evaluated == 0


# ==================== _check_feasibility Tests ====================


class TestCheckFeasibility:
    """Test _check_feasibility method."""

    def test_no_constraints_feasible(self):
        pruner = ConstraintPruner()
        result = pruner._check_feasibility(_person(), _rotation(), _block())
        assert result is None

    def test_person_type_match(self):
        pruner = ConstraintPruner()
        result = pruner._check_feasibility(
            _person(ptype="resident"),
            _rotation(allowed_types=["resident", "faculty"]),
            _block(),
        )
        assert result is None

    def test_person_type_mismatch(self):
        pruner = ConstraintPruner()
        result = pruner._check_feasibility(
            _person(ptype="resident"),
            _rotation(allowed_types=["faculty"]),
            _block(),
        )
        assert result == "person_type_mismatch"

    def test_pgy_level_too_low(self):
        pruner = ConstraintPruner()
        result = pruner._check_feasibility(
            _person(pgy=1), _rotation(min_pgy=2), _block()
        )
        assert result == "pgy_level_too_low"

    def test_pgy_level_meets_minimum(self):
        pruner = ConstraintPruner()
        result = pruner._check_feasibility(
            _person(pgy=3), _rotation(min_pgy=3), _block()
        )
        assert result is None

    def test_pgy_level_too_high(self):
        pruner = ConstraintPruner()
        result = pruner._check_feasibility(
            _person(pgy=5), _rotation(max_pgy=4), _block()
        )
        assert result == "pgy_level_too_high"

    def test_pgy_level_within_max(self):
        pruner = ConstraintPruner()
        result = pruner._check_feasibility(
            _person(pgy=3), _rotation(max_pgy=4), _block()
        )
        assert result is None

    def test_pgy_range_valid(self):
        pruner = ConstraintPruner()
        result = pruner._check_feasibility(
            _person(pgy=3), _rotation(min_pgy=2, max_pgy=4), _block()
        )
        assert result is None

    def test_pgy_range_below(self):
        pruner = ConstraintPruner()
        result = pruner._check_feasibility(
            _person(pgy=1), _rotation(min_pgy=2, max_pgy=4), _block()
        )
        assert result == "pgy_level_too_low"

    def test_pgy_range_above(self):
        pruner = ConstraintPruner()
        result = pruner._check_feasibility(
            _person(pgy=5), _rotation(min_pgy=2, max_pgy=4), _block()
        )
        assert result == "pgy_level_too_high"

    def test_specialty_match(self):
        pruner = ConstraintPruner()
        result = pruner._check_feasibility(
            _person(specialties=["surgery", "EM"]),
            _rotation(required_specs=["EM"]),
            _block(),
        )
        assert result is None

    def test_specialty_mismatch(self):
        pruner = ConstraintPruner()
        result = pruner._check_feasibility(
            _person(specialties=["FM"]),
            _rotation(required_specs=["surgery"]),
            _block(),
        )
        assert result == "specialty_mismatch"

    def test_no_specialties_mismatch(self):
        """Person with no specialties fails specialty requirement."""
        pruner = ConstraintPruner()
        result = pruner._check_feasibility(
            _person(),  # No specialties key
            _rotation(required_specs=["surgery"]),
            _block(),
        )
        assert result == "specialty_mismatch"

    def test_person_unavailable(self):
        pruner = ConstraintPruner()
        d = date(2025, 1, 6)
        result = pruner._check_feasibility(
            _person(unavailable=[d]),
            _rotation(),
            _block(d=d),
        )
        assert result == "person_unavailable"

    def test_person_available_different_date(self):
        pruner = ConstraintPruner()
        result = pruner._check_feasibility(
            _person(unavailable=[date(2025, 1, 7)]),
            _rotation(),
            _block(d=date(2025, 1, 6)),
        )
        assert result is None

    def test_time_of_day_am_match(self):
        pruner = ConstraintPruner()
        result = pruner._check_feasibility(
            _person(), _rotation(time_of_day="AM"), _block(is_am=True)
        )
        assert result is None

    def test_time_of_day_am_mismatch(self):
        pruner = ConstraintPruner()
        result = pruner._check_feasibility(
            _person(), _rotation(time_of_day="AM"), _block(is_am=False)
        )
        assert result == "time_of_day_mismatch"

    def test_time_of_day_pm_match(self):
        pruner = ConstraintPruner()
        result = pruner._check_feasibility(
            _person(), _rotation(time_of_day="PM"), _block(is_am=False)
        )
        assert result is None

    def test_time_of_day_pm_mismatch(self):
        pruner = ConstraintPruner()
        result = pruner._check_feasibility(
            _person(), _rotation(time_of_day="PM"), _block(is_am=True)
        )
        assert result == "time_of_day_mismatch"

    def test_max_people_does_not_prune(self):
        """max_people is not enforced during feasibility check."""
        pruner = ConstraintPruner()
        result = pruner._check_feasibility(_person(), _rotation(max_people=1), _block())
        assert result is None

    def test_multiple_constraints_first_failure_wins(self):
        """Checks are ordered; first failure returned."""
        pruner = ConstraintPruner()
        # Person type checked before PGY level
        result = pruner._check_feasibility(
            _person(ptype="resident", pgy=1),
            _rotation(allowed_types=["faculty"], min_pgy=3),
            _block(),
        )
        assert result == "person_type_mismatch"


# ==================== _get_feasible_rotations Tests ====================


class TestGetFeasibleRotations:
    """Test _get_feasible_rotations method."""

    def test_all_rotations_feasible(self):
        pruner = ConstraintPruner()
        reasons: dict = {}
        rotations = [_rotation("r1"), _rotation("r2")]
        result = pruner._get_feasible_rotations(_person(), _block(), rotations, reasons)
        assert len(result) == 2

    def test_some_rotations_pruned(self):
        pruner = ConstraintPruner()
        reasons: dict = {}
        rotations = [
            _rotation("r1"),
            _rotation("r2", min_pgy=5),  # PGY-2 person can't do this
        ]
        result = pruner._get_feasible_rotations(
            _person(pgy=2), _block(), rotations, reasons
        )
        assert len(result) == 1
        assert result[0]["id"] == "r1"

    def test_all_rotations_pruned(self):
        pruner = ConstraintPruner()
        reasons: dict = {}
        rotations = [_rotation("r1", min_pgy=5)]
        result = pruner._get_feasible_rotations(
            _person(pgy=1), _block(), rotations, reasons
        )
        assert len(result) == 0

    def test_pruned_count_incremented(self):
        pruner = ConstraintPruner()
        reasons: dict = {}
        rotations = [_rotation("r1", min_pgy=5), _rotation("r2", min_pgy=5)]
        pruner._get_feasible_rotations(_person(pgy=1), _block(), rotations, reasons)
        assert pruner.pruned_count == 2

    def test_pruning_reasons_accumulated(self):
        pruner = ConstraintPruner()
        reasons: dict = {}
        rotations = [
            _rotation("r1", min_pgy=5),
            _rotation("r2", allowed_types=["faculty"]),
        ]
        pruner._get_feasible_rotations(
            _person(pgy=1, ptype="resident"), _block(), rotations, reasons
        )
        assert "pgy_level_too_low" in reasons
        assert "person_type_mismatch" in reasons


# ==================== prune_assignments Tests ====================


class TestPruneAssignments:
    """Test prune_assignments end-to-end."""

    def test_all_feasible(self):
        pruner = ConstraintPruner()
        result = pruner.prune_assignments(
            persons=[_person("p1"), _person("p2")],
            rotations=[_rotation("r1")],
            blocks=[_block("b1")],
        )
        assert len(result["feasible_assignments"]) == 2
        assert result["pruned_count"] == 0
        assert result["total_evaluated"] == 2
        assert result["reduction_ratio"] == 0.0

    def test_some_pruned(self):
        pruner = ConstraintPruner()
        result = pruner.prune_assignments(
            persons=[_person("p1", pgy=1), _person("p2", pgy=3)],
            rotations=[_rotation("r1", min_pgy=2)],
            blocks=[_block("b1")],
        )
        # p1 (PGY-1) pruned, p2 (PGY-3) feasible
        assert len(result["feasible_assignments"]) == 1
        assert result["feasible_assignments"][0]["person_id"] == "p2"

    def test_all_pruned(self):
        pruner = ConstraintPruner()
        result = pruner.prune_assignments(
            persons=[_person("p1", pgy=1)],
            rotations=[_rotation("r1", min_pgy=5)],
            blocks=[_block("b1")],
        )
        assert len(result["feasible_assignments"]) == 0
        assert result["reduction_ratio"] == 1.0

    def test_existing_assignments_skipped(self):
        """Already assigned person-block pairs are not re-evaluated."""
        pruner = ConstraintPruner()
        result = pruner.prune_assignments(
            persons=[_person("p1")],
            rotations=[_rotation("r1")],
            blocks=[_block("b1")],
            existing_assignments=[{"person_id": "p1", "block_id": "b1"}],
        )
        # The person-block is skipped entirely
        assert len(result["feasible_assignments"]) == 0
        assert result["total_evaluated"] == 1

    def test_multiple_rotations_per_person_block(self):
        """Each person-block combination evaluates all rotations."""
        pruner = ConstraintPruner()
        result = pruner.prune_assignments(
            persons=[_person("p1")],
            rotations=[_rotation("r1"), _rotation("r2"), _rotation("r3")],
            blocks=[_block("b1")],
        )
        # 1 person * 1 block evaluates 3 rotations -> 3 feasible
        assert len(result["feasible_assignments"]) == 3

    def test_result_keys(self):
        pruner = ConstraintPruner()
        result = pruner.prune_assignments(
            persons=[_person()], rotations=[_rotation()], blocks=[_block()]
        )
        expected_keys = {
            "feasible_assignments",
            "total_evaluated",
            "pruned_count",
            "pruning_reasons",
            "reduction_ratio",
        }
        assert set(result.keys()) == expected_keys

    def test_feasible_assignment_format(self):
        """Each feasible assignment has person_id, block_id, rotation_id."""
        pruner = ConstraintPruner()
        result = pruner.prune_assignments(
            persons=[_person("p1")],
            rotations=[_rotation("r1")],
            blocks=[_block("b1")],
        )
        assign = result["feasible_assignments"][0]
        assert assign["person_id"] == "p1"
        assert assign["block_id"] == "b1"
        assert assign["rotation_id"] == "r1"

    def test_updates_instance_counters(self):
        pruner = ConstraintPruner()
        pruner.prune_assignments(
            persons=[_person("p1"), _person("p2")],
            rotations=[_rotation("r1", min_pgy=5)],
            blocks=[_block("b1")],
        )
        assert pruner.total_evaluated == 2
        assert pruner.pruned_count == 2

    def test_counters_reset_between_calls(self):
        pruner = ConstraintPruner()
        pruner.prune_assignments(
            persons=[_person()], rotations=[_rotation()], blocks=[_block()]
        )
        assert pruner.total_evaluated == 1
        # Second call resets
        pruner.prune_assignments(
            persons=[_person(), _person("p2")],
            rotations=[_rotation()],
            blocks=[_block()],
        )
        assert pruner.total_evaluated == 2

    def test_many_persons_many_blocks(self):
        """Combinatorial: 3 persons * 4 blocks = 12 evaluations."""
        pruner = ConstraintPruner()
        persons = [_person(f"p{i}") for i in range(3)]
        blocks = [_block(f"b{i}") for i in range(4)]
        result = pruner.prune_assignments(
            persons=persons, rotations=[_rotation()], blocks=blocks
        )
        assert result["total_evaluated"] == 12
        assert len(result["feasible_assignments"]) == 12

    def test_pruning_reasons_counts(self):
        pruner = ConstraintPruner()
        result = pruner.prune_assignments(
            persons=[
                _person("p1", pgy=1),
                _person("p2", ptype="staff"),
            ],
            rotations=[
                _rotation("r1", min_pgy=3, allowed_types=["resident"]),
            ],
            blocks=[_block("b1")],
        )
        reasons = result["pruning_reasons"]
        # p1: pgy_level_too_low (person_type ok since 'resident')
        # p2: person_type_mismatch (checked first)
        assert reasons.get("pgy_level_too_low", 0) >= 1
        assert reasons.get("person_type_mismatch", 0) >= 1


# ==================== estimate_search_space_reduction Tests ====================


class TestEstimateSearchSpaceReduction:
    """Test estimate_search_space_reduction method."""

    def test_no_pruning(self):
        pruner = ConstraintPruner()
        result = pruner.estimate_search_space_reduction(
            {"total_evaluated": 100, "pruned_count": 0}
        )
        assert result["total_combinations"] == 100
        assert result["pruned_combinations"] == 0
        assert result["remaining_combinations"] == 100
        assert result["reduction_ratio"] == 0.0
        assert result["estimated_search_space_reduction_factor"] == pytest.approx(1.0)

    def test_half_pruned(self):
        pruner = ConstraintPruner()
        result = pruner.estimate_search_space_reduction(
            {"total_evaluated": 100, "pruned_count": 50}
        )
        assert result["remaining_combinations"] == 50
        assert result["reduction_ratio"] == 0.5
        # 2^(50/100) = 2^0.5 ≈ 1.414
        assert result["estimated_search_space_reduction_factor"] == pytest.approx(
            2**0.5, rel=1e-3
        )

    def test_all_pruned(self):
        pruner = ConstraintPruner()
        result = pruner.estimate_search_space_reduction(
            {"total_evaluated": 100, "pruned_count": 100}
        )
        assert result["remaining_combinations"] == 0
        assert result["reduction_ratio"] == 1.0
        # 2^(100/100) = 2
        assert result["estimated_search_space_reduction_factor"] == pytest.approx(2.0)

    def test_zero_total(self):
        pruner = ConstraintPruner()
        result = pruner.estimate_search_space_reduction(
            {"total_evaluated": 0, "pruned_count": 0}
        )
        assert result["reduction_ratio"] == 0
        assert result["estimated_search_space_reduction_factor"] == 1

    def test_result_keys(self):
        pruner = ConstraintPruner()
        result = pruner.estimate_search_space_reduction(
            {"total_evaluated": 10, "pruned_count": 3}
        )
        expected_keys = {
            "total_combinations",
            "pruned_combinations",
            "remaining_combinations",
            "reduction_ratio",
            "estimated_search_space_reduction_factor",
            "estimated_solver_speedup",
        }
        assert set(result.keys()) == expected_keys

    def test_speedup_equals_reduction_factor(self):
        pruner = ConstraintPruner()
        result = pruner.estimate_search_space_reduction(
            {"total_evaluated": 200, "pruned_count": 80}
        )
        assert (
            result["estimated_solver_speedup"]
            == result["estimated_search_space_reduction_factor"]
        )


# ==================== prune_infeasible_assignments wrapper Tests ====================


class TestPruneInfeasibleAssignmentsWrapper:
    """Test the module-level convenience function."""

    def test_returns_same_format(self):
        result = prune_infeasible_assignments(
            persons=[_person()], rotations=[_rotation()], blocks=[_block()]
        )
        assert "feasible_assignments" in result
        assert "total_evaluated" in result
        assert "pruned_count" in result

    def test_basic_pruning(self):
        result = prune_infeasible_assignments(
            persons=[_person("p1", pgy=1)],
            rotations=[_rotation("r1", min_pgy=3)],
            blocks=[_block("b1")],
        )
        assert len(result["feasible_assignments"]) == 0
        assert result["pruned_count"] == 1


# ==================== Integration / Edge Case Tests ====================


class TestEdgeCases:
    """Test edge cases and integration scenarios."""

    def test_person_missing_type_field(self):
        """Person without 'type' field doesn't match allowed types."""
        pruner = ConstraintPruner()
        person = {"id": "p1", "pgy_level": 2}  # No 'type' key
        result = pruner._check_feasibility(
            person, _rotation(allowed_types=["resident"]), _block()
        )
        assert result == "person_type_mismatch"

    def test_person_missing_pgy_defaults_low(self):
        """Person without 'pgy_level' defaults to 0 for min check."""
        pruner = ConstraintPruner()
        person = {"id": "p1", "type": "resident"}
        result = pruner._check_feasibility(person, _rotation(min_pgy=1), _block())
        assert result == "pgy_level_too_low"

    def test_person_missing_pgy_defaults_high(self):
        """Person without 'pgy_level' defaults to 999 for max check."""
        pruner = ConstraintPruner()
        person = {"id": "p1", "type": "resident"}
        result = pruner._check_feasibility(person, _rotation(max_pgy=5), _block())
        assert result == "pgy_level_too_high"

    def test_block_missing_is_am_defaults_true(self):
        """Block without 'is_am' defaults to True."""
        pruner = ConstraintPruner()
        block = {"id": "b1", "date": date(2025, 1, 6)}
        result = pruner._check_feasibility(
            _person(), _rotation(time_of_day="AM"), block
        )
        assert result is None  # AM rotation + default is_am=True -> match

    def test_specialty_any_match_sufficient(self):
        """Any one matching specialty is sufficient."""
        pruner = ConstraintPruner()
        result = pruner._check_feasibility(
            _person(specialties=["FM", "EM", "surgery"]),
            _rotation(required_specs=["peds", "surgery"]),
            _block(),
        )
        assert result is None  # surgery matches

    def test_empty_persons_list_raises(self):
        """Known bug: ZeroDivisionError in log message when no evaluations."""
        pruner = ConstraintPruner()
        with pytest.raises(ZeroDivisionError):
            pruner.prune_assignments(
                persons=[], rotations=[_rotation()], blocks=[_block()]
            )

    def test_empty_rotations_list(self):
        pruner = ConstraintPruner()
        result = pruner.prune_assignments(
            persons=[_person()], rotations=[], blocks=[_block()]
        )
        # 1 person * 1 block evaluated, but 0 rotations -> 0 feasible
        assert result["total_evaluated"] == 1
        assert result["feasible_assignments"] == []

    def test_empty_blocks_list_raises(self):
        """Known bug: ZeroDivisionError in log message when no evaluations."""
        pruner = ConstraintPruner()
        with pytest.raises(ZeroDivisionError):
            pruner.prune_assignments(
                persons=[_person()], rotations=[_rotation()], blocks=[]
            )

    def test_full_scenario(self):
        """Realistic scenario: 3 residents, 2 rotations, 2 blocks."""
        persons = [
            _person("res1", ptype="resident", pgy=1, specialties=["FM"]),
            _person("res2", ptype="resident", pgy=3, specialties=["surgery"]),
            _person("fac1", ptype="faculty", pgy=0, specialties=["FM"]),
        ]
        rotations = [
            _rotation(
                "ICU",
                allowed_types=["resident"],
                min_pgy=2,
                required_specs=["surgery", "EM"],
            ),
            _rotation("FM_Clinic", allowed_types=["resident", "faculty"]),
        ]
        blocks = [
            _block("b1", d=date(2025, 1, 6)),
            _block("b2", d=date(2025, 1, 7)),
        ]
        pruner = ConstraintPruner()
        result = pruner.prune_assignments(persons, rotations, blocks)

        # res1 (PGY-1, FM): ICU needs PGY-2+ -> pruned. FM_Clinic -> feasible.
        # res2 (PGY-3, surgery): ICU -> feasible. FM_Clinic -> feasible.
        # fac1 (faculty, FM): ICU allowed_types=resident -> pruned. FM_Clinic -> feasible.
        # Per block: res1=1 feasible, res2=2 feasible, fac1=1 feasible = 4 per block
        # 2 blocks -> 8 feasible
        assert result["total_evaluated"] == 6  # 3 persons * 2 blocks
        assert len(result["feasible_assignments"]) == 8
        assert result["pruned_count"] == 4  # 2 per block * 2 blocks

    def test_unavailable_on_specific_block(self):
        """Person unavailable on one block but available on another."""
        persons = [_person("p1", unavailable=[date(2025, 1, 6)])]
        blocks = [
            _block("b1", d=date(2025, 1, 6)),
            _block("b2", d=date(2025, 1, 7)),
        ]
        pruner = ConstraintPruner()
        result = pruner.prune_assignments(persons, [_rotation()], blocks)
        # b1 pruned (unavailable), b2 feasible
        assert len(result["feasible_assignments"]) == 1
        assert result["feasible_assignments"][0]["block_id"] == "b2"
