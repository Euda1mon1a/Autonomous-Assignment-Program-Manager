"""
Unit tests for the Tensegrity Solver.

Tests the Force Density Method implementation for schedule equilibrium
using structural mechanics principles.
"""

import numpy as np
import pytest

from app.scheduling.tensegrity_solver import TensegritySolver


class TestTensegritySolverBasics:
    """Test basic functionality of the tensegrity solver."""

    def test_initialization(self):
        """Test solver initialization."""
        solver = TensegritySolver()
        assert solver.nodes == {}
        assert solver.edges == []

    def test_add_node(self):
        """Test adding nodes to the structure."""
        solver = TensegritySolver()

        solver.add_node("node1", initial_position=10.0, is_anchor=False)
        assert "node1" in solver.nodes
        assert solver.nodes["node1"]["position"] == 10.0
        assert solver.nodes["node1"]["is_anchor"] is False

        solver.add_node("node2", initial_position=15.0, is_anchor=True)
        assert "node2" in solver.nodes
        assert solver.nodes["node2"]["position"] == 15.0
        assert solver.nodes["node2"]["is_anchor"] is True

    def test_add_duplicate_node_raises_error(self):
        """Test that adding duplicate nodes raises an error."""
        solver = TensegritySolver()
        solver.add_node("node1", initial_position=10.0)

        with pytest.raises(ValueError, match="already exists"):
            solver.add_node("node1", initial_position=20.0)

    def test_add_tension_element(self):
        """Test adding tension elements."""
        solver = TensegritySolver()
        solver.add_node("node1", initial_position=10.0)
        solver.add_node("node2", initial_position=15.0)

        solver.add_tension_element("node1", "node2", force_density=1.0)
        assert len(solver.edges) == 1
        assert solver.edges[0] == ("node1", "node2", 1.0, "tension")

    def test_add_compression_element(self):
        """Test adding compression elements."""
        solver = TensegritySolver()
        solver.add_node("node1", initial_position=10.0)
        solver.add_node("node2", initial_position=15.0)

        solver.add_compression_element("node1", "node2", force_density=0.5)
        assert len(solver.edges) == 1
        assert solver.edges[0] == ("node1", "node2", 0.5, "compression")

    def test_add_edge_to_nonexistent_node_raises_error(self):
        """Test that adding edges to non-existent nodes raises an error."""
        solver = TensegritySolver()
        solver.add_node("node1", initial_position=10.0)

        with pytest.raises(ValueError, match="does not exist"):
            solver.add_tension_element("node1", "node2", force_density=1.0)

        with pytest.raises(ValueError, match="does not exist"):
            solver.add_compression_element("node1", "node2", force_density=1.0)

    def test_negative_force_density_raises_error(self):
        """Test that negative force densities raise an error."""
        solver = TensegritySolver()
        solver.add_node("node1", initial_position=10.0)
        solver.add_node("node2", initial_position=15.0)

        with pytest.raises(ValueError, match="must be non-negative"):
            solver.add_tension_element("node1", "node2", force_density=-1.0)

        with pytest.raises(ValueError, match="must be non-negative"):
            solver.add_compression_element("node1", "node2", force_density=-1.0)


class TestTensegritySolverSimpleSystems:
    """Test simple 2-node systems."""

    def test_two_anchored_nodes(self):
        """Test system with two anchored nodes (trivial case)."""
        solver = TensegritySolver()
        solver.add_node("start", initial_position=8.0, is_anchor=True)
        solver.add_node("end", initial_position=17.0, is_anchor=True)
        solver.add_tension_element("start", "end", force_density=1.0)

        solution = solver.solve()

        # Anchored nodes should stay at their positions
        assert solution["start"] == 8.0
        assert solution["end"] == 17.0

    def test_one_free_node_between_anchors(self):
        """Test one free node pulled between two anchors."""
        solver = TensegritySolver()

        # Anchors at 8.0 and 17.0
        solver.add_node("start", initial_position=8.0, is_anchor=True)
        solver.add_node("task", initial_position=10.0)  # Free node
        solver.add_node("end", initial_position=17.0, is_anchor=True)

        # Equal force densities - should settle in middle
        solver.add_tension_element("start", "task", force_density=1.0)
        solver.add_tension_element("task", "end", force_density=1.0)

        solution = solver.solve()

        # Free node should be pulled to midpoint between anchors
        assert solution["start"] == 8.0
        assert solution["end"] == 17.0
        assert np.isclose(solution["task"], 12.5, atol=0.01)

    def test_asymmetric_force_densities(self):
        """Test one free node with asymmetric tension forces."""
        solver = TensegritySolver()

        solver.add_node("start", initial_position=0.0, is_anchor=True)
        solver.add_node("task", initial_position=5.0)  # Free node
        solver.add_node("end", initial_position=10.0, is_anchor=True)

        # Stronger pull toward start (3x)
        solver.add_tension_element("start", "task", force_density=3.0)
        solver.add_tension_element("task", "end", force_density=1.0)

        solution = solver.solve()

        # Free node should be closer to start due to stronger force
        # Expected: (3*0 + 1*10) / (3+1) = 2.5
        assert solution["start"] == 0.0
        assert solution["end"] == 10.0
        assert np.isclose(solution["task"], 2.5, atol=0.01)

    def test_compression_element_pushes_nodes_apart(self):
        """Test that compression elements create repulsive forces."""
        solver = TensegritySolver()

        # Two free nodes with a compression strut between them
        solver.add_node("anchor_left", initial_position=0.0, is_anchor=True)
        solver.add_node("node1", initial_position=5.0)
        solver.add_node("node2", initial_position=5.0)  # Same initial position
        solver.add_node("anchor_right", initial_position=10.0, is_anchor=True)

        # Tension to anchors (pull toward center)
        solver.add_tension_element("anchor_left", "node1", force_density=1.0)
        solver.add_tension_element("node2", "anchor_right", force_density=1.0)

        # Compression between free nodes (push apart)
        solver.add_compression_element("node1", "node2", force_density=2.0)

        solution = solver.solve()

        # Nodes should separate due to compression
        assert solution["node1"] < solution["node2"]
        assert solution["anchor_left"] == 0.0
        assert solution["anchor_right"] == 10.0


class TestTensegritySolverComplexSystems:
    """Test multi-node systems with anchors."""

    def test_shift_schedule_with_tasks(self):
        """Test realistic shift scheduling scenario."""
        solver = TensegritySolver()

        # Shift boundaries (anchored)
        solver.add_node("shift_start", initial_position=8.0, is_anchor=True)
        solver.add_node("shift_end", initial_position=17.0, is_anchor=True)

        # Tasks (free to move)
        solver.add_node("task_a", initial_position=9.0)
        solver.add_node("task_b", initial_position=12.0)
        solver.add_node("task_c", initial_position=15.0)

        # Tasks pulled toward shift start
        solver.add_tension_element("shift_start", "task_a", force_density=2.0)

        # Sequential task dependencies (tension)
        solver.add_tension_element("task_a", "task_b", force_density=1.0)
        solver.add_tension_element("task_b", "task_c", force_density=1.0)

        # Minimum gaps between tasks (compression)
        solver.add_compression_element("task_a", "task_b", force_density=0.5)
        solver.add_compression_element("task_b", "task_c", force_density=0.5)

        # Pull last task toward shift end
        solver.add_tension_element("task_c", "shift_end", force_density=2.0)

        solution = solver.solve()

        # Verify anchors unchanged
        assert solution["shift_start"] == 8.0
        assert solution["shift_end"] == 17.0

        # Verify tasks are within shift boundaries
        assert 8.0 <= solution["task_a"] <= 17.0
        assert 8.0 <= solution["task_b"] <= 17.0
        assert 8.0 <= solution["task_c"] <= 17.0

        # Verify sequential ordering
        assert solution["task_a"] < solution["task_b"]
        assert solution["task_b"] < solution["task_c"]

    def test_four_node_square_configuration(self):
        """Test a square configuration with anchors at corners."""
        solver = TensegritySolver()

        # Anchors at corners
        solver.add_node("corner1", initial_position=0.0, is_anchor=True)
        solver.add_node("corner2", initial_position=10.0, is_anchor=True)

        # Free nodes
        solver.add_node("node1", initial_position=3.0)
        solver.add_node("node2", initial_position=7.0)

        # Tension elements forming a chain
        solver.add_tension_element("corner1", "node1", force_density=1.0)
        solver.add_tension_element("node1", "node2", force_density=1.0)
        solver.add_tension_element("node2", "corner2", force_density=1.0)

        solution = solver.solve()

        # Free nodes should distribute evenly
        assert solution["corner1"] == 0.0
        assert solution["corner2"] == 10.0

        # With equal force densities, should be evenly spaced
        spacing = solution["node1"] - solution["corner1"]
        assert np.isclose(solution["node2"] - solution["node1"], spacing, atol=0.01)
        assert np.isclose(solution["corner2"] - solution["node2"], spacing, atol=0.01)

    def test_multiple_anchors_no_free_nodes(self):
        """Test system with only anchored nodes."""
        solver = TensegritySolver()

        solver.add_node("a1", initial_position=5.0, is_anchor=True)
        solver.add_node("a2", initial_position=10.0, is_anchor=True)
        solver.add_node("a3", initial_position=15.0, is_anchor=True)

        solver.add_tension_element("a1", "a2", force_density=1.0)
        solver.add_tension_element("a2", "a3", force_density=1.0)

        solution = solver.solve()

        # All anchors should remain at their positions
        assert solution["a1"] == 5.0
        assert solution["a2"] == 10.0
        assert solution["a3"] == 15.0


class TestTensegritySolverStability:
    """Test stability checking functionality."""

    def test_is_stable_valid_solution(self):
        """Test stability check on valid solution."""
        solver = TensegritySolver()

        solver.add_node("start", initial_position=8.0, is_anchor=True)
        solver.add_node("task", initial_position=10.0)
        solver.add_node("end", initial_position=17.0, is_anchor=True)

        solver.add_tension_element("start", "task", force_density=1.0)
        solver.add_tension_element("task", "end", force_density=1.0)

        solution = solver.solve()

        assert solver.is_stable(solution) is True

    def test_is_stable_without_solution(self):
        """Test stability check that solves internally."""
        solver = TensegritySolver()

        solver.add_node("start", initial_position=8.0, is_anchor=True)
        solver.add_node("task", initial_position=10.0)
        solver.add_node("end", initial_position=17.0, is_anchor=True)

        solver.add_tension_element("start", "task", force_density=1.0)
        solver.add_tension_element("task", "end", force_density=1.0)

        # Should solve internally and check stability
        assert solver.is_stable() is True

    def test_is_stable_rejects_negative_times(self):
        """Test stability check rejects negative positions."""
        solver = TensegritySolver()

        # Create a solution manually with negative values
        solver.add_node("node1", initial_position=5.0)

        fake_solution = {"node1": -5.0}

        assert solver.is_stable(fake_solution) is False

    def test_is_stable_rejects_nan(self):
        """Test stability check rejects NaN values."""
        solver = TensegritySolver()

        solver.add_node("node1", initial_position=5.0)

        fake_solution = {"node1": np.nan}

        assert solver.is_stable(fake_solution) is False

    def test_is_stable_rejects_infinite(self):
        """Test stability check rejects infinite values."""
        solver = TensegritySolver()

        solver.add_node("node1", initial_position=5.0)

        fake_solution = {"node1": np.inf}

        assert solver.is_stable(fake_solution) is False


class TestTensegritySolverInternalForces:
    """Test internal force calculations."""

    def test_get_internal_forces_tension_only(self):
        """Test internal force calculation for tension elements."""
        solver = TensegritySolver()

        solver.add_node("start", initial_position=0.0, is_anchor=True)
        solver.add_node("end", initial_position=10.0, is_anchor=True)

        solver.add_tension_element("start", "end", force_density=2.0)

        solution = solver.solve()
        forces = solver.get_internal_forces(solution)

        # Force = q * (x_end - x_start) = 2.0 * (10.0 - 0.0) = 20.0
        assert ("start", "end") in forces
        assert np.isclose(forces[("start", "end")], 20.0, atol=0.01)

    def test_get_internal_forces_compression_element(self):
        """Test internal force calculation for compression elements."""
        solver = TensegritySolver()

        solver.add_node("node1", initial_position=0.0, is_anchor=True)
        solver.add_node("node2", initial_position=10.0, is_anchor=True)

        solver.add_compression_element("node1", "node2", force_density=1.0)

        solution = solver.solve()
        forces = solver.get_internal_forces(solution)

        # Compression force should be negative (q is negated for compression)
        # Force = -q * (x2 - x1) = -1.0 * (10.0 - 0.0) = -10.0
        assert ("node1", "node2") in forces
        assert forces[("node1", "node2")] < 0  # Compression is negative

    def test_get_internal_forces_mixed_system(self):
        """Test internal forces in mixed tension/compression system."""
        solver = TensegritySolver()

        solver.add_node("anchor_left", initial_position=0.0, is_anchor=True)
        solver.add_node("center", initial_position=5.0)
        solver.add_node("anchor_right", initial_position=10.0, is_anchor=True)

        solver.add_tension_element("anchor_left", "center", force_density=1.0)
        solver.add_compression_element("center", "anchor_right", force_density=1.0)

        solution = solver.solve()
        forces = solver.get_internal_forces(solution)

        # Should have forces for both edges
        assert ("anchor_left", "center") in forces
        assert ("center", "anchor_right") in forces


class TestTensegritySolverUtilities:
    """Test utility functions (to_schedule, visualize)."""

    def test_to_schedule_basic(self):
        """Test conversion to schedule format."""
        solver = TensegritySolver()

        solver.add_node("shift_start", initial_position=8.0, is_anchor=True)
        solver.add_node("task_a", initial_position=10.0)
        solver.add_node("task_b", initial_position=12.0)
        solver.add_node("shift_end", initial_position=17.0, is_anchor=True)

        solver.add_tension_element("shift_start", "task_a", force_density=1.0)
        solver.add_tension_element("task_a", "task_b", force_density=1.0)
        solver.add_tension_element("task_b", "shift_end", force_density=1.0)

        solution = solver.solve()
        schedule = solver.to_schedule(solution)

        # Should have 4 entries
        assert len(schedule) == 4

        # Should be sorted by time
        times = [entry["scheduled_time"] for entry in schedule]
        assert times == sorted(times)

        # Check structure
        for entry in schedule:
            assert "task_id" in entry
            assert "scheduled_time" in entry
            assert "is_fixed" in entry

        # Anchors should be marked as fixed
        anchor_entries = [e for e in schedule if e["is_fixed"]]
        assert len(anchor_entries) == 2
        assert any(e["task_id"] == "shift_start" for e in anchor_entries)
        assert any(e["task_id"] == "shift_end" for e in anchor_entries)

    def test_visualize_basic(self):
        """Test ASCII visualization generation."""
        solver = TensegritySolver()

        solver.add_node("start", initial_position=8.0, is_anchor=True)
        solver.add_node("task", initial_position=12.0)
        solver.add_node("end", initial_position=17.0, is_anchor=True)

        solver.add_tension_element("start", "task", force_density=1.0)
        solver.add_tension_element("task", "end", force_density=1.0)

        solution = solver.solve()
        viz = solver.visualize(solution)

        # Check that visualization contains expected elements
        assert "Tensegrity Structure Visualization" in viz
        assert "start" in viz
        assert "task" in viz
        assert "end" in viz
        assert "ANCHOR" in viz  # Should mark anchored nodes
        assert "Nodes" in viz
        assert "Connections" in viz
        assert "Timeline" in viz

    def test_visualize_empty_structure(self):
        """Test visualization of empty structure."""
        solver = TensegritySolver()
        solution = {}

        viz = solver.visualize(solution)
        assert "Empty structure" in viz


class TestTensegritySolverEdgeCases:
    """Test edge cases and error conditions."""

    def test_solve_empty_structure_raises_error(self):
        """Test that solving an empty structure raises an error."""
        solver = TensegritySolver()

        with pytest.raises(ValueError, match="No nodes"):
            solver.solve()

    def test_solve_only_free_nodes_no_constraints(self):
        """Test solving with only free nodes and no edges."""
        solver = TensegritySolver()

        solver.add_node("node1", initial_position=5.0)
        solver.add_node("node2", initial_position=10.0)

        # With no constraints, positions should remain at initial values
        # (zero force system)
        solution = solver.solve()

        # Should succeed with initial positions
        assert "node1" in solution
        assert "node2" in solution

    def test_tension_only_structure(self):
        """Test structure with only tension elements (cable net)."""
        solver = TensegritySolver()

        solver.add_node("anchor1", initial_position=0.0, is_anchor=True)
        solver.add_node("anchor2", initial_position=20.0, is_anchor=True)
        solver.add_node("node1", initial_position=5.0)
        solver.add_node("node2", initial_position=15.0)

        # Create a cable net
        solver.add_tension_element("anchor1", "node1", force_density=1.0)
        solver.add_tension_element("node1", "node2", force_density=1.0)
        solver.add_tension_element("node2", "anchor2", force_density=1.0)
        solver.add_tension_element("anchor1", "node2", force_density=0.5)
        solver.add_tension_element("node1", "anchor2", force_density=0.5)

        solution = solver.solve()

        # Should produce valid solution
        assert solver.is_stable(solution)
        assert 0.0 <= solution["node1"] <= 20.0
        assert 0.0 <= solution["node2"] <= 20.0

    def test_mixed_tension_compression(self):
        """Test structure with both tension and compression elements."""
        solver = TensegritySolver()

        # Create a simple tensegrity structure
        solver.add_node("base1", initial_position=0.0, is_anchor=True)
        solver.add_node("base2", initial_position=10.0, is_anchor=True)
        solver.add_node("top", initial_position=5.0)

        # Tension cables to anchors (pull down)
        solver.add_tension_element("base1", "top", force_density=1.0)
        solver.add_tension_element("base2", "top", force_density=1.0)

        # Compression strut (push up)
        # Note: In 1D, compression is less intuitive, but mathematically valid
        solver.add_compression_element("base1", "base2", force_density=0.5)

        solution = solver.solve()

        # Should produce valid equilibrium
        assert solver.is_stable(solution)
        assert 0.0 <= solution["top"] <= 10.0

    def test_build_force_density_matrix_structure(self):
        """Test force density matrix has correct structure."""
        solver = TensegritySolver()

        solver.add_node("node1", initial_position=0.0)
        solver.add_node("node2", initial_position=5.0)
        solver.add_node("node3", initial_position=10.0)

        solver.add_tension_element("node1", "node2", force_density=1.0)
        solver.add_tension_element("node2", "node3", force_density=2.0)

        F = solver.build_force_density_matrix()

        # Check matrix is square
        assert F.shape[0] == F.shape[1] == 3

        # Check matrix is symmetric
        F_dense = F.toarray()
        assert np.allclose(F_dense, F_dense.T)

        # Check diagonal elements (sum of incident force densities)
        assert np.isclose(F_dense[0, 0], 1.0)  # node1: only edge to node2
        assert np.isclose(F_dense[1, 1], 3.0)  # node2: edges to node1 (1) and node3 (2)
        assert np.isclose(F_dense[2, 2], 2.0)  # node3: only edge to node2

        # Check off-diagonal elements
        assert np.isclose(F_dense[0, 1], -1.0)
        assert np.isclose(F_dense[1, 0], -1.0)
        assert np.isclose(F_dense[1, 2], -2.0)
        assert np.isclose(F_dense[2, 1], -2.0)
