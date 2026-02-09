"""Tests for TensegritySolver force density method (pure linear algebra, no DB)."""

import numpy as np
import pytest
from scipy import sparse

from app.scheduling.tensegrity_solver import TensegritySolver


# ==================== Helpers ====================


def _simple_chain() -> TensegritySolver:
    """Build a simple anchor-task-anchor chain."""
    s = TensegritySolver()
    s.add_node("start", initial_position=8.0, is_anchor=True)
    s.add_node("task", initial_position=10.0)
    s.add_node("end", initial_position=17.0, is_anchor=True)
    s.add_tension_element("start", "task", 1.0)
    s.add_tension_element("task", "end", 1.0)
    return s


def _triangle() -> TensegritySolver:
    """Build a 3-node triangle with one anchor."""
    s = TensegritySolver()
    s.add_node("A", initial_position=0.0, is_anchor=True)
    s.add_node("B", initial_position=5.0)
    s.add_node("C", initial_position=10.0)
    s.add_tension_element("A", "B", 1.0)
    s.add_tension_element("B", "C", 1.0)
    s.add_tension_element("A", "C", 0.5)
    return s


# ==================== Initialization Tests ====================


class TestInit:
    """Test TensegritySolver initialization."""

    def test_empty_construction(self):
        s = TensegritySolver()
        assert s.nodes == {}
        assert s.edges == []

    def test_nodes_dict_mutable(self):
        s = TensegritySolver()
        s.add_node("a")
        assert "a" in s.nodes


# ==================== add_node Tests ====================


class TestAddNode:
    """Test add_node method."""

    def test_basic_add(self):
        s = TensegritySolver()
        s.add_node("task1", initial_position=9.0)
        assert "task1" in s.nodes
        assert s.nodes["task1"]["position"] == 9.0
        assert s.nodes["task1"]["is_anchor"] is False

    def test_anchor_node(self):
        s = TensegritySolver()
        s.add_node("fixed", initial_position=8.0, is_anchor=True)
        assert s.nodes["fixed"]["is_anchor"] is True

    def test_default_position_zero(self):
        s = TensegritySolver()
        s.add_node("x")
        assert s.nodes["x"]["position"] == 0.0

    def test_duplicate_node_raises(self):
        s = TensegritySolver()
        s.add_node("dup")
        with pytest.raises(ValueError, match="already exists"):
            s.add_node("dup")

    def test_position_stored_as_float(self):
        s = TensegritySolver()
        s.add_node("int_pos", initial_position=5)
        assert isinstance(s.nodes["int_pos"]["position"], float)


# ==================== add_tension_element Tests ====================


class TestAddTensionElement:
    """Test add_tension_element method."""

    def test_basic_tension(self):
        s = TensegritySolver()
        s.add_node("a")
        s.add_node("b")
        s.add_tension_element("a", "b", 1.5)
        assert len(s.edges) == 1
        assert s.edges[0] == ("a", "b", 1.5, "tension")

    def test_nonexistent_node1_raises(self):
        s = TensegritySolver()
        s.add_node("b")
        with pytest.raises(ValueError, match="does not exist"):
            s.add_tension_element("a", "b", 1.0)

    def test_nonexistent_node2_raises(self):
        s = TensegritySolver()
        s.add_node("a")
        with pytest.raises(ValueError, match="does not exist"):
            s.add_tension_element("a", "b", 1.0)

    def test_negative_force_density_raises(self):
        s = TensegritySolver()
        s.add_node("a")
        s.add_node("b")
        with pytest.raises(ValueError, match="non-negative"):
            s.add_tension_element("a", "b", -1.0)

    def test_zero_force_density_allowed(self):
        s = TensegritySolver()
        s.add_node("a")
        s.add_node("b")
        s.add_tension_element("a", "b", 0.0)
        assert s.edges[0][2] == 0.0


# ==================== add_compression_element Tests ====================


class TestAddCompressionElement:
    """Test add_compression_element method."""

    def test_basic_compression(self):
        s = TensegritySolver()
        s.add_node("a")
        s.add_node("b")
        s.add_compression_element("a", "b", 2.0)
        assert len(s.edges) == 1
        assert s.edges[0] == ("a", "b", 2.0, "compression")

    def test_nonexistent_node_raises(self):
        s = TensegritySolver()
        s.add_node("a")
        with pytest.raises(ValueError, match="does not exist"):
            s.add_compression_element("a", "missing", 1.0)

    def test_negative_force_density_raises(self):
        s = TensegritySolver()
        s.add_node("a")
        s.add_node("b")
        with pytest.raises(ValueError, match="non-negative"):
            s.add_compression_element("a", "b", -0.5)


# ==================== build_force_density_matrix Tests ====================


class TestBuildForceDensityMatrix:
    """Test build_force_density_matrix."""

    def test_empty_graph(self):
        s = TensegritySolver()
        s.add_node("a")
        F = s.build_force_density_matrix()
        assert F.shape == (1, 1)
        assert F[0, 0] == 0.0

    def test_single_tension_edge(self):
        s = TensegritySolver()
        s.add_node("a")
        s.add_node("b")
        s.add_tension_element("a", "b", 2.0)
        F = s.build_force_density_matrix()
        assert F.shape == (2, 2)
        # Diagonal = sum of incident q
        assert F[0, 0] == pytest.approx(2.0)
        assert F[1, 1] == pytest.approx(2.0)
        # Off-diagonal = -q
        assert F[0, 1] == pytest.approx(-2.0)
        assert F[1, 0] == pytest.approx(-2.0)

    def test_compression_negates_force_density(self):
        s = TensegritySolver()
        s.add_node("a")
        s.add_node("b")
        s.add_compression_element("a", "b", 3.0)
        F = s.build_force_density_matrix()
        # Compression: q_effective = -3.0
        # F[i,j] -= (-3.0) => F[i,j] += 3.0
        # F[i,i] += (-3.0) => F[i,i] -= 3.0
        assert F[0, 0] == pytest.approx(-3.0)
        assert F[0, 1] == pytest.approx(3.0)

    def test_returns_sparse_csr(self):
        s = TensegritySolver()
        s.add_node("a")
        F = s.build_force_density_matrix()
        assert sparse.issparse(F)
        assert isinstance(F, sparse.csr_matrix)

    def test_matrix_symmetry(self):
        s = _simple_chain()
        F = s.build_force_density_matrix()
        diff = F - F.T
        assert np.allclose(diff.toarray(), 0.0)

    def test_chain_matrix_structure(self):
        s = _simple_chain()
        F = s.build_force_density_matrix()
        dense = F.toarray()
        # 3 nodes: start, task, end; 2 tension edges q=1.0 each
        # Node ordering: start(0), task(1), end(2)
        # start connected to task: q=1
        # task connected to end: q=1
        assert dense[0, 0] == pytest.approx(1.0)  # start: 1 edge
        assert dense[1, 1] == pytest.approx(2.0)  # task: 2 edges
        assert dense[2, 2] == pytest.approx(1.0)  # end: 1 edge
        assert dense[0, 1] == pytest.approx(-1.0)
        assert dense[1, 2] == pytest.approx(-1.0)
        assert dense[0, 2] == pytest.approx(0.0)  # Not connected


# ==================== build_anchor_vector Tests ====================


class TestBuildAnchorVector:
    """Test build_anchor_vector."""

    def test_returns_zeros(self):
        s = TensegritySolver()
        s.add_node("a")
        s.add_node("b")
        p = s.build_anchor_vector()
        assert p.shape == (2,)
        assert np.allclose(p, 0.0)


# ==================== solve Tests ====================


class TestSolve:
    """Test solve method."""

    def test_empty_raises(self):
        s = TensegritySolver()
        with pytest.raises(ValueError, match="No nodes"):
            s.solve()

    def test_all_anchors(self):
        s = TensegritySolver()
        s.add_node("a", 5.0, is_anchor=True)
        s.add_node("b", 10.0, is_anchor=True)
        solution = s.solve()
        assert solution["a"] == 5.0
        assert solution["b"] == 10.0

    def test_single_anchor_no_edges(self):
        s = TensegritySolver()
        s.add_node("anchor", 8.0, is_anchor=True)
        solution = s.solve()
        assert solution["anchor"] == 8.0

    def test_chain_midpoint(self):
        """Free node between two equal-tension anchors should go to midpoint."""
        s = TensegritySolver()
        s.add_node("left", 0.0, is_anchor=True)
        s.add_node("mid", 5.0)
        s.add_node("right", 10.0, is_anchor=True)
        s.add_tension_element("left", "mid", 1.0)
        s.add_tension_element("mid", "right", 1.0)
        solution = s.solve()
        assert solution["left"] == 0.0
        assert solution["right"] == 10.0
        assert solution["mid"] == pytest.approx(5.0)

    def test_asymmetric_tension(self):
        """Stronger tension pulls free node closer to that anchor."""
        s = TensegritySolver()
        s.add_node("left", 0.0, is_anchor=True)
        s.add_node("mid", 5.0)
        s.add_node("right", 10.0, is_anchor=True)
        s.add_tension_element("left", "mid", 3.0)  # 3x stronger
        s.add_tension_element("mid", "right", 1.0)
        solution = s.solve()
        # Weighted average: (3*0 + 1*10) / (3+1) = 2.5
        assert solution["mid"] == pytest.approx(2.5)

    def test_two_free_nodes(self):
        """Two free nodes between anchors with equal tension."""
        s = TensegritySolver()
        s.add_node("start", 0.0, is_anchor=True)
        s.add_node("a", 3.0)
        s.add_node("b", 7.0)
        s.add_node("end", 12.0, is_anchor=True)
        s.add_tension_element("start", "a", 1.0)
        s.add_tension_element("a", "b", 1.0)
        s.add_tension_element("b", "end", 1.0)
        solution = s.solve()
        # Equal tension: nodes should be evenly spaced 0, 4, 8, 12
        assert solution["a"] == pytest.approx(4.0)
        assert solution["b"] == pytest.approx(8.0)

    def test_solution_keys_match_nodes(self):
        s = _simple_chain()
        solution = s.solve()
        assert set(solution.keys()) == {"start", "task", "end"}

    def test_anchors_unchanged(self):
        s = _simple_chain()
        solution = s.solve()
        assert solution["start"] == 8.0
        assert solution["end"] == 17.0

    def test_free_node_between_anchors(self):
        s = _simple_chain()
        solution = s.solve()
        # Equal tension => midpoint = (8+17)/2 = 12.5
        assert solution["task"] == pytest.approx(12.5)


# ==================== is_stable Tests ====================


class TestIsStable:
    """Test is_stable method."""

    def test_valid_solution_stable(self):
        s = _simple_chain()
        solution = s.solve()
        assert s.is_stable(solution) is True

    def test_nan_is_unstable(self):
        s = _simple_chain()
        solution = {"start": 8.0, "task": float("nan"), "end": 17.0}
        assert s.is_stable(solution) is False

    def test_inf_is_unstable(self):
        s = _simple_chain()
        solution = {"start": 8.0, "task": float("inf"), "end": 17.0}
        assert s.is_stable(solution) is False

    def test_negative_position_unstable(self):
        s = _simple_chain()
        solution = {"start": 8.0, "task": -1.0, "end": 17.0}
        assert s.is_stable(solution) is False

    def test_extreme_spread_unstable(self):
        """Nodes more than 24h apart should be unstable."""
        s = TensegritySolver()
        s.add_node("a", 0.0)
        s.add_node("b", 50.0)
        s.add_tension_element("a", "b", 1.0)
        solution = {"a": 0.0, "b": 50.0}
        assert s.is_stable(solution) is False

    def test_all_anchors_stable(self):
        s = TensegritySolver()
        s.add_node("a", 5.0, is_anchor=True)
        s.add_node("b", 10.0, is_anchor=True)
        solution = s.solve()
        assert s.is_stable(solution) is True

    def test_solve_called_if_no_solution(self):
        s = _simple_chain()
        assert s.is_stable() is True

    def test_unsolvable_returns_false(self):
        s = TensegritySolver()
        # No nodes => solve will raise => is_stable returns False
        assert s.is_stable() is False


# ==================== get_internal_forces Tests ====================


class TestGetInternalForces:
    """Test get_internal_forces calculation."""

    def test_chain_forces(self):
        s = _simple_chain()
        solution = s.solve()
        forces = s.get_internal_forces(solution)
        assert ("start", "task") in forces
        assert ("task", "end") in forces

    def test_equal_tension_equal_forces(self):
        s = _simple_chain()
        solution = s.solve()
        forces = s.get_internal_forces(solution)
        # F = q * (x2 - x1); q=1 for both
        # task is at midpoint 12.5
        f1 = forces[("start", "task")]  # 1 * (12.5 - 8.0) = 4.5
        f2 = forces[("task", "end")]  # 1 * (17.0 - 12.5) = 4.5
        assert f1 == pytest.approx(4.5)
        assert f2 == pytest.approx(4.5)

    def test_compression_force_negative(self):
        s = TensegritySolver()
        s.add_node("a", 0.0, is_anchor=True)
        s.add_node("b", 10.0, is_anchor=True)
        s.add_compression_element("a", "b", 2.0)
        solution = s.solve()
        forces = s.get_internal_forces(solution)
        # q_effective = -2 for compression, (x2 - x1) = 10
        # F = -2 * 10 = -20
        assert forces[("a", "b")] == pytest.approx(-20.0)

    def test_solve_called_if_no_solution(self):
        s = _simple_chain()
        forces = s.get_internal_forces()
        assert len(forces) == 2

    def test_force_count_matches_edges(self):
        s = _triangle()
        solution = s.solve()
        forces = s.get_internal_forces(solution)
        assert len(forces) == 3


# ==================== to_schedule Tests ====================


class TestToSchedule:
    """Test to_schedule conversion."""

    def test_sorted_by_time(self):
        s = _simple_chain()
        solution = s.solve()
        schedule = s.to_schedule(solution)
        times = [entry["scheduled_time"] for entry in schedule]
        assert times == sorted(times)

    def test_includes_all_nodes(self):
        s = _simple_chain()
        solution = s.solve()
        schedule = s.to_schedule(solution)
        assert len(schedule) == 3

    def test_fixed_flag_for_anchors(self):
        s = _simple_chain()
        solution = s.solve()
        schedule = s.to_schedule(solution)
        by_id = {entry["task_id"]: entry for entry in schedule}
        assert by_id["start"]["is_fixed"] is True
        assert by_id["end"]["is_fixed"] is True
        assert by_id["task"]["is_fixed"] is False

    def test_task_id_preserved(self):
        s = _simple_chain()
        solution = s.solve()
        schedule = s.to_schedule(solution)
        ids = {entry["task_id"] for entry in schedule}
        assert ids == {"start", "task", "end"}

    def test_scheduled_time_matches_solution(self):
        s = _simple_chain()
        solution = s.solve()
        schedule = s.to_schedule(solution)
        by_id = {entry["task_id"]: entry for entry in schedule}
        assert by_id["task"]["scheduled_time"] == pytest.approx(solution["task"])


# ==================== visualize Tests ====================


class TestVisualize:
    """Test visualize ASCII output."""

    def test_empty_solution(self):
        s = TensegritySolver()
        result = s.visualize({})
        assert result == "Empty structure"

    def test_contains_header(self):
        s = _simple_chain()
        solution = s.solve()
        result = s.visualize(solution)
        assert "Tensegrity Structure Visualization" in result

    def test_contains_node_listing(self):
        s = _simple_chain()
        solution = s.solve()
        result = s.visualize(solution)
        assert "start" in result
        assert "task" in result
        assert "end" in result

    def test_anchor_marked(self):
        s = _simple_chain()
        solution = s.solve()
        result = s.visualize(solution)
        assert "[ANCHOR]" in result

    def test_connections_shown(self):
        s = _simple_chain()
        solution = s.solve()
        result = s.visualize(solution)
        assert "(T)" in result  # Tension symbol

    def test_timeline_shown(self):
        s = _simple_chain()
        solution = s.solve()
        result = s.visualize(solution)
        assert "Timeline:" in result

    def test_compression_symbol(self):
        s = TensegritySolver()
        s.add_node("a", 0.0, is_anchor=True)
        s.add_node("b", 10.0, is_anchor=True)
        s.add_compression_element("a", "b", 1.0)
        solution = s.solve()
        result = s.visualize(solution)
        assert "(C)" in result


# ==================== Integration Tests ====================


class TestIntegration:
    """End-to-end integration tests."""

    def test_full_workflow(self):
        """Complete workflow: build, solve, validate, convert, visualize."""
        s = _simple_chain()
        solution = s.solve()
        assert s.is_stable(solution)
        schedule = s.to_schedule(solution)
        assert len(schedule) == 3
        viz = s.visualize(solution)
        assert len(viz) > 0

    def test_mixed_tension_compression(self):
        """System with both tension and compression elements."""
        s = TensegritySolver()
        s.add_node("start", 0.0, is_anchor=True)
        s.add_node("a", 4.0)
        s.add_node("b", 8.0)
        s.add_node("end", 12.0, is_anchor=True)
        s.add_tension_element("start", "a", 2.0)
        s.add_tension_element("a", "b", 1.0)  # Keep system well-conditioned
        s.add_compression_element("a", "b", 0.3)  # Weaker compression
        s.add_tension_element("b", "end", 2.0)
        solution = s.solve()
        # a should be close to start, b close to end
        assert solution["a"] < solution["b"]
        assert s.is_stable(solution)

    def test_many_nodes_chain(self):
        """Large chain with 10 free nodes between anchors."""
        s = TensegritySolver()
        s.add_node("start", 0.0, is_anchor=True)
        for i in range(10):
            s.add_node(f"n{i}", float(i + 1))
        s.add_node("end", 11.0, is_anchor=True)

        # Chain connections
        s.add_tension_element("start", "n0", 1.0)
        for i in range(9):
            s.add_tension_element(f"n{i}", f"n{i + 1}", 1.0)
        s.add_tension_element("n9", "end", 1.0)

        solution = s.solve()
        # Equal tension => evenly spaced
        for i in range(10):
            expected = (i + 1) * 11.0 / 11.0
            assert solution[f"n{i}"] == pytest.approx(expected, abs=0.01)

    def test_two_anchors_strong_compression(self):
        """Compression between anchors produces valid force computation."""
        s = TensegritySolver()
        s.add_node("a", 0.0, is_anchor=True)
        s.add_node("b", 10.0, is_anchor=True)
        s.add_compression_element("a", "b", 5.0)
        solution = s.solve()
        forces = s.get_internal_forces(solution)
        # Compression pushes apart: q_eff=-5, (10-0)=10 => F = -50
        assert forces[("a", "b")] == pytest.approx(-50.0)

    def test_triangle_equilibrium(self):
        """Triangle with one anchor reaches equilibrium."""
        s = _triangle()
        solution = s.solve()
        assert s.is_stable(solution)
        # All positions should be finite
        for pos in solution.values():
            assert np.isfinite(pos)
