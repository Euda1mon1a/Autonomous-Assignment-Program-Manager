"""
Tests for Constraint Rigidity Analysis using the (2,3)-Pebble Game.

Tests cover:
- Graph construction from tasks and constraints
- Pebble game algorithm execution
- Identification of rigid, flexible, and stressed regions
- Degrees of freedom calculation
- Constraint change recommendations
"""
import pytest

from app.scheduling.rigidity_analysis import ConstraintRigidityAnalyzer


class TestGraphConstruction:
    """Test suite for constraint graph construction."""

    def test_build_empty_graph(self):
        """Test building a graph with no tasks or constraints."""
        analyzer = ConstraintRigidityAnalyzer()
        graph = analyzer.build_constraint_graph(tasks=[], constraints=[])

        assert graph.number_of_nodes() == 0
        assert graph.number_of_edges() == 0

    def test_build_graph_single_task(self):
        """Test building a graph with one task and no constraints."""
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [{'id': 'A', 'type': 'shift'}]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=[])

        assert graph.number_of_nodes() == 1
        assert graph.number_of_edges() == 0
        assert 'A' in graph.nodes()

    def test_build_graph_two_tasks_one_constraint(self):
        """Test building a graph with two tasks and one constraint."""
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [
            {'id': 'A', 'type': 'shift'},
            {'id': 'B', 'type': 'shift'}
        ]
        constraints = [
            {'type': 'no_overlap', 'tasks': ['A', 'B']}
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=constraints)

        assert graph.number_of_nodes() == 2
        assert graph.number_of_edges() == 1
        assert graph.has_edge('A', 'B')
        assert graph['A']['B']['constraint_type'] == 'no_overlap'

    def test_build_graph_preserves_task_metadata(self):
        """Test that task metadata is preserved in graph nodes."""
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [
            {'id': 'A', 'type': 'shift', 'duration': 8},
            {'id': 'B', 'type': 'clinic', 'duration': 4}
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=[])

        assert graph.nodes['A']['type'] == 'shift'
        assert graph.nodes['A']['duration'] == 8
        assert graph.nodes['B']['type'] == 'clinic'
        assert graph.nodes['B']['duration'] == 4

    def test_build_graph_multi_task_constraint(self):
        """Test constraint involving more than two tasks creates pairwise edges."""
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [
            {'id': 'A', 'type': 'shift'},
            {'id': 'B', 'type': 'shift'},
            {'id': 'C', 'type': 'shift'}
        ]
        constraints = [
            {'type': 'mutual_exclusion', 'tasks': ['A', 'B', 'C']}
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=constraints)

        assert graph.number_of_nodes() == 3
        # Should create edges A-B, A-C, B-C (3 edges)
        assert graph.number_of_edges() == 3
        assert graph.has_edge('A', 'B')
        assert graph.has_edge('A', 'C')
        assert graph.has_edge('B', 'C')


class TestRigidStructure:
    """Test suite for rigid (fully constrained) structures."""

    def test_triangle_is_rigid(self):
        """
        Test that a triangle (3 nodes, 3 edges) is rigid.

        A triangle is the minimal rigid structure in 2D.
        Expected: 2*3 - 3 = 3 independent edges.
        Remaining DoF = 2*V - E = 2*3 - 3 = 3 (rigid body motions).
        """
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [
            {'id': 'A', 'type': 'shift'},
            {'id': 'B', 'type': 'shift'},
            {'id': 'C', 'type': 'shift'}
        ]
        constraints = [
            {'type': 'constraint1', 'tasks': ['A', 'B']},
            {'type': 'constraint2', 'tasks': ['B', 'C']},
            {'type': 'constraint3', 'tasks': ['C', 'A']}
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=constraints)
        result = analyzer.run_pebble_game(graph)

        assert result['total_nodes'] == 3
        assert result['total_edges'] == 3
        assert result['independent_edges'] == 3
        assert result['redundant_edges'] == 0
        # Minimally rigid structure has 3 DoF (rigid body motions: 2 translations + 1 rotation)
        assert result['degrees_of_freedom'] == 3
        assert result['is_rigid'] is False  # Not fully rigid (still has rigid body DoF)
        assert result['is_stressed'] is False

    def test_identify_rigid_region_triangle(self):
        """Test that a triangle is identified as a rigid region."""
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [
            {'id': 'A', 'type': 'shift'},
            {'id': 'B', 'type': 'shift'},
            {'id': 'C', 'type': 'shift'}
        ]
        constraints = [
            {'type': 'c1', 'tasks': ['A', 'B']},
            {'type': 'c2', 'tasks': ['B', 'C']},
            {'type': 'c3', 'tasks': ['C', 'A']}
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=constraints)
        analyzer.run_pebble_game(graph)

        rigid_regions = analyzer.identify_rigid_regions()

        assert len(rigid_regions) == 1
        assert set(rigid_regions[0]) == {'A', 'B', 'C'}

    def test_square_is_over_rigid(self):
        """
        Test that a complete graph on 4 nodes (6 edges) is over-constrained.

        For 4 nodes: max independent edges = 2*4 - 3 = 5
        With 6 edges total, 1 should be redundant.
        DoF = 2*4 - 5 = 3 (rigid body motions after accounting for independent edges)
        """
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [
            {'id': 'A', 'type': 'shift'},
            {'id': 'B', 'type': 'shift'},
            {'id': 'C', 'type': 'shift'},
            {'id': 'D', 'type': 'shift'}
        ]
        constraints = [
            {'type': 'c1', 'tasks': ['A', 'B']},
            {'type': 'c2', 'tasks': ['B', 'C']},
            {'type': 'c3', 'tasks': ['C', 'D']},
            {'type': 'c4', 'tasks': ['D', 'A']},
            {'type': 'c5', 'tasks': ['A', 'C']},  # Diagonal 1
            {'type': 'c6', 'tasks': ['B', 'D']}   # Diagonal 2 (redundant)
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=constraints)
        result = analyzer.run_pebble_game(graph)

        assert result['total_nodes'] == 4
        assert result['total_edges'] == 6
        # Note: edge ordering can affect which specific edge is redundant
        # but total should be 5 independent, 1 redundant
        assert result['independent_edges'] >= 5
        assert result['redundant_edges'] >= 1
        assert result['is_stressed'] is True


class TestFlexibleStructure:
    """Test suite for flexible (under-constrained) structures."""

    def test_chain_is_flexible(self):
        """
        Test that a chain (3 nodes, 2 edges) is flexible.

        A chain has degrees of freedom remaining.
        DoF = 2*V - E = 2*3 - 2 = 4 (more flexible than a rigid structure)
        """
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [
            {'id': 'A', 'type': 'shift'},
            {'id': 'B', 'type': 'shift'},
            {'id': 'C', 'type': 'shift'}
        ]
        constraints = [
            {'type': 'c1', 'tasks': ['A', 'B']},
            {'type': 'c2', 'tasks': ['B', 'C']}
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=constraints)
        result = analyzer.run_pebble_game(graph)

        assert result['total_nodes'] == 3
        assert result['total_edges'] == 2
        assert result['independent_edges'] == 2
        assert result['redundant_edges'] == 0
        # DoF = 2*V - E = 2*3 - 2 = 4
        assert result['degrees_of_freedom'] == 4
        assert result['is_rigid'] is False
        assert result['is_stressed'] is False

    def test_identify_flexible_region_chain(self):
        """Test that a chain is identified as a flexible region."""
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [
            {'id': 'A', 'type': 'shift'},
            {'id': 'B', 'type': 'shift'},
            {'id': 'C', 'type': 'shift'}
        ]
        constraints = [
            {'type': 'c1', 'tasks': ['A', 'B']},
            {'type': 'c2', 'tasks': ['B', 'C']}
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=constraints)
        analyzer.run_pebble_game(graph)

        flexible_regions = analyzer.identify_flexible_regions()

        assert len(flexible_regions) == 1
        assert set(flexible_regions[0]) == {'A', 'B', 'C'}

    def test_single_edge_is_flexible(self):
        """
        Test that a single edge (2 nodes, 1 edge) is flexible.

        DoF = 2*V - E = 2*2 - 1 = 3
        """
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [
            {'id': 'A', 'type': 'shift'},
            {'id': 'B', 'type': 'shift'}
        ]
        constraints = [
            {'type': 'c1', 'tasks': ['A', 'B']}
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=constraints)
        result = analyzer.run_pebble_game(graph)

        # DoF = 2*V - E = 2*2 - 1 = 3
        assert result['degrees_of_freedom'] == 3
        assert result['is_rigid'] is False


class TestStressedStructure:
    """Test suite for over-constrained (stressed) structures."""

    def test_complete_graph_is_stressed(self):
        """
        Test that a complete graph on 4 nodes (K4) is over-constrained.

        K4 has 6 edges, but max independent edges = 2*4 - 3 = 5
        So 1 edge must be redundant.
        """
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [
            {'id': 'A', 'type': 'shift'},
            {'id': 'B', 'type': 'shift'},
            {'id': 'C', 'type': 'shift'},
            {'id': 'D', 'type': 'shift'}
        ]
        # Create complete graph: all pairs connected
        constraints = [
            {'type': 'c1', 'tasks': ['A', 'B', 'C', 'D']}  # Creates 6 edges
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=constraints)
        result = analyzer.run_pebble_game(graph)

        # 4 nodes: expect 2*4 - 3 = 5 independent edges, 1 redundant
        assert result['total_edges'] == 6
        assert result['independent_edges'] >= 5
        assert result['redundant_edges'] >= 1
        assert result['is_stressed'] is True

    def test_identify_stressed_region(self):
        """Test identification of over-constrained regions."""
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [
            {'id': 'A', 'type': 'shift'},
            {'id': 'B', 'type': 'shift'},
            {'id': 'C', 'type': 'shift'},
            {'id': 'D', 'type': 'shift'}
        ]
        # Create complete graph (all pairs)
        constraints = [
            {'type': 'c1', 'tasks': ['A', 'B', 'C', 'D']}
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=constraints)
        analyzer.run_pebble_game(graph)

        stressed_regions = analyzer.identify_stressed_regions()

        assert len(stressed_regions) == 1
        assert set(stressed_regions[0]) == {'A', 'B', 'C', 'D'}


class TestDegreesOfFreedom:
    """Test suite for degrees of freedom calculations."""

    def test_degrees_of_freedom_unconstrained(self):
        """Test DoF for completely unconstrained nodes."""
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [
            {'id': 'A', 'type': 'shift'},
            {'id': 'B', 'type': 'shift'}
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=[])
        analyzer.run_pebble_game(graph)

        dof = analyzer.get_degrees_of_freedom()
        # 2 nodes × 2 pebbles each = 4 DoF
        assert dof == 4

    def test_degrees_of_freedom_partial(self):
        """Test DoF for partially constrained structure."""
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [
            {'id': 'A', 'type': 'shift'},
            {'id': 'B', 'type': 'shift'},
            {'id': 'C', 'type': 'shift'}
        ]
        constraints = [
            {'type': 'c1', 'tasks': ['A', 'B']}
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=constraints)
        analyzer.run_pebble_game(graph)

        dof = analyzer.get_degrees_of_freedom()
        # Started with 6 pebbles, used 1 for edge → 5 remaining
        assert dof == 5

    def test_degrees_of_freedom_minimally_rigid(self):
        """
        Test DoF for minimally rigid structure.

        A minimally rigid structure (triangle) has 3 DoF (rigid body motions).
        """
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [
            {'id': 'A', 'type': 'shift'},
            {'id': 'B', 'type': 'shift'},
            {'id': 'C', 'type': 'shift'}
        ]
        constraints = [
            {'type': 'c1', 'tasks': ['A', 'B']},
            {'type': 'c2', 'tasks': ['B', 'C']},
            {'type': 'c3', 'tasks': ['C', 'A']}
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=constraints)
        analyzer.run_pebble_game(graph)

        dof = analyzer.get_degrees_of_freedom()
        # DoF = 2*V - E = 2*3 - 3 = 3
        assert dof == 3


class TestRecommendations:
    """Test suite for constraint change recommendations."""

    def test_recommend_remove_from_stressed_region(self):
        """Test recommendations to remove constraints from stressed regions."""
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [
            {'id': 'A', 'type': 'shift'},
            {'id': 'B', 'type': 'shift'},
            {'id': 'C', 'type': 'shift'},
            {'id': 'D', 'type': 'shift'}
        ]
        constraints = [
            {'type': 'complete', 'tasks': ['A', 'B', 'C', 'D']}  # Creates 6 edges
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=constraints)
        analyzer.run_pebble_game(graph)

        recommendations = analyzer.recommend_constraint_changes()

        # Should recommend removing at least one redundant edge
        remove_recommendations = [r for r in recommendations if r['action'] == 'remove']
        assert len(remove_recommendations) >= 1
        assert remove_recommendations[0]['severity'] == 'high'
        assert 'redundant' in remove_recommendations[0]['reason'].lower()

    def test_recommend_add_to_flexible_region(self):
        """
        Test recommendations to add constraints to flexible regions.

        For 4 nodes forming a connected path A-B-C-D (3 edges):
        Expected for rigidity: 2*4 - 3 = 5
        Actual edges: 3
        Deficit: 2
        """
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [
            {'id': 'A', 'type': 'shift'},
            {'id': 'B', 'type': 'shift'},
            {'id': 'C', 'type': 'shift'},
            {'id': 'D', 'type': 'shift'}
        ]
        constraints = [
            {'type': 'c1', 'tasks': ['A', 'B']},
            {'type': 'c2', 'tasks': ['B', 'C']},
            {'type': 'c3', 'tasks': ['C', 'D']}  # 3 edges total, needs 5 for rigidity
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=constraints)
        analyzer.run_pebble_game(graph)

        recommendations = analyzer.recommend_constraint_changes()

        # Should recommend adding constraints
        add_recommendations = [r for r in recommendations if r['action'] == 'add']
        assert len(add_recommendations) >= 1
        # Needs 2 more edges for rigidity (5 total - 3 current = 2)
        assert add_recommendations[0]['missing_constraints'] == 2

    def test_no_recommendations_for_perfect_structure(self):
        """Test no recommendations for a perfectly rigid structure."""
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [
            {'id': 'A', 'type': 'shift'},
            {'id': 'B', 'type': 'shift'},
            {'id': 'C', 'type': 'shift'}
        ]
        constraints = [
            {'type': 'c1', 'tasks': ['A', 'B']},
            {'type': 'c2', 'tasks': ['B', 'C']},
            {'type': 'c3', 'tasks': ['C', 'A']}
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=constraints)
        analyzer.run_pebble_game(graph)

        recommendations = analyzer.recommend_constraint_changes()

        # Rigid triangle is perfect - no changes needed
        assert len(recommendations) == 0


class TestSummary:
    """Test suite for comprehensive graph summary."""

    def test_summary_includes_all_metrics(self):
        """Test that summary includes all expected metrics."""
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [
            {'id': 'A', 'type': 'shift'},
            {'id': 'B', 'type': 'shift'},
            {'id': 'C', 'type': 'shift'}
        ]
        constraints = [
            {'type': 'c1', 'tasks': ['A', 'B']},
            {'type': 'c2', 'tasks': ['B', 'C']}
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=constraints)
        analyzer.run_pebble_game(graph)

        summary = analyzer.get_constraint_graph_summary()

        assert 'total_nodes' in summary
        assert 'total_edges' in summary
        assert 'degrees_of_freedom' in summary
        assert 'num_rigid_regions' in summary
        assert 'num_flexible_regions' in summary
        assert 'num_stressed_regions' in summary
        assert 'recommendations' in summary
        assert 'edge_breakdown' in summary

        assert summary['total_nodes'] == 3
        assert summary['total_edges'] == 2
        # DoF = 2*V - E = 2*3 - 2 = 4
        assert summary['degrees_of_freedom'] == 4

    def test_summary_before_analysis_returns_error(self):
        """Test that summary returns error if no analysis has been run."""
        analyzer = ConstraintRigidityAnalyzer()
        summary = analyzer.get_constraint_graph_summary()

        assert 'error' in summary


class TestComplexScenarios:
    """Test suite for complex multi-component scenarios."""

    def test_disconnected_components(self):
        """Test analysis of graph with multiple disconnected components."""
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [
            # Component 1: Triangle (rigid)
            {'id': 'A', 'type': 'shift'},
            {'id': 'B', 'type': 'shift'},
            {'id': 'C', 'type': 'shift'},
            # Component 2: Chain (flexible)
            {'id': 'D', 'type': 'shift'},
            {'id': 'E', 'type': 'shift'},
            {'id': 'F', 'type': 'shift'}
        ]
        constraints = [
            # Triangle
            {'type': 'c1', 'tasks': ['A', 'B']},
            {'type': 'c2', 'tasks': ['B', 'C']},
            {'type': 'c3', 'tasks': ['C', 'A']},
            # Chain
            {'type': 'c4', 'tasks': ['D', 'E']},
            {'type': 'c5', 'tasks': ['E', 'F']}
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=constraints)
        result = analyzer.run_pebble_game(graph)

        assert result['total_nodes'] == 6
        assert result['total_edges'] == 5

        rigid_regions = analyzer.identify_rigid_regions()
        flexible_regions = analyzer.identify_flexible_regions()

        # Should identify triangle as rigid
        assert len(rigid_regions) >= 1
        # Should identify chain as flexible
        assert len(flexible_regions) >= 1

    def test_large_rigid_structure(self):
        """
        Test analysis of a larger rigid structure (5-node minimally rigid).

        For 5 nodes: max independent edges = 2*5 - 3 = 7
        DoF = 2*V - E = 2*5 - 7 = 3 (rigid body motions)
        """
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [
            {'id': 'A', 'type': 'shift'},
            {'id': 'B', 'type': 'shift'},
            {'id': 'C', 'type': 'shift'},
            {'id': 'D', 'type': 'shift'},
            {'id': 'E', 'type': 'shift'}
        ]
        # For 5 nodes: 2*5 - 3 = 7 edges needed for minimal rigidity
        constraints = [
            {'type': 'c1', 'tasks': ['A', 'B']},
            {'type': 'c2', 'tasks': ['B', 'C']},
            {'type': 'c3', 'tasks': ['C', 'D']},
            {'type': 'c4', 'tasks': ['D', 'E']},
            {'type': 'c5', 'tasks': ['E', 'A']},
            {'type': 'c6', 'tasks': ['A', 'C']},
            {'type': 'c7', 'tasks': ['C', 'E']}
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=constraints)
        result = analyzer.run_pebble_game(graph)

        assert result['total_edges'] == 7
        assert result['independent_edges'] == 7
        assert result['redundant_edges'] == 0
        # DoF = 2*V - E = 2*5 - 7 = 3 (rigid body motions)
        assert result['degrees_of_freedom'] == 3
        assert result['is_rigid'] is False  # Has rigid body DoF
        assert result['is_stressed'] is False


class TestEdgeCases:
    """Test suite for edge cases and error handling."""

    def test_empty_analysis(self):
        """Test analysis with empty graph."""
        analyzer = ConstraintRigidityAnalyzer()
        graph = analyzer.build_constraint_graph(tasks=[], constraints=[])
        result = analyzer.run_pebble_game(graph)

        assert result['total_nodes'] == 0
        assert result['total_edges'] == 0
        assert result['degrees_of_freedom'] == 0

    def test_constraint_with_nonexistent_task(self):
        """Test constraint referencing non-existent task is ignored."""
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [{'id': 'A', 'type': 'shift'}]
        constraints = [
            {'type': 'c1', 'tasks': ['A', 'Z']}  # Z doesn't exist
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=constraints)

        # Should only have node A, no edges
        assert graph.number_of_nodes() == 1
        assert graph.number_of_edges() == 0

    def test_constraint_with_single_task(self):
        """Test constraint with only one task (no edge created)."""
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [
            {'id': 'A', 'type': 'shift'},
            {'id': 'B', 'type': 'shift'}
        ]
        constraints = [
            {'type': 'c1', 'tasks': ['A']}  # Only one task
        ]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=constraints)

        assert graph.number_of_nodes() == 2
        assert graph.number_of_edges() == 0

    def test_pebble_game_on_single_node(self):
        """Test pebble game on graph with single isolated node."""
        analyzer = ConstraintRigidityAnalyzer()
        tasks = [{'id': 'A', 'type': 'shift'}]
        graph = analyzer.build_constraint_graph(tasks=tasks, constraints=[])
        result = analyzer.run_pebble_game(graph)

        # Single node keeps all pebbles
        assert result['degrees_of_freedom'] == 2
        assert result['is_rigid'] is False
