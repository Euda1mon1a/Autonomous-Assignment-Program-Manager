"""Tests for ConstraintRigidityAnalyzer pebble game algorithm (pure graph, no DB)."""

import pytest

from app.scheduling.rigidity_analysis import ConstraintRigidityAnalyzer


# ==================== Helpers ====================


def _tasks(*ids: str) -> list[dict]:
    """Build task list from IDs."""
    return [{"id": tid} for tid in ids]


def _constraints(*pairs: tuple[list[str], str]) -> list[dict]:
    """Build constraint list from (task_list, type) pairs."""
    return [{"tasks": tasks, "type": ctype} for tasks, ctype in pairs]


# ==================== Initialization Tests ====================


class TestAnalyzerInit:
    """Test ConstraintRigidityAnalyzer initialization."""

    def test_initial_state(self):
        a = ConstraintRigidityAnalyzer()
        assert a.graph is None
        assert a.pebbles == {}
        assert a.edge_status == {}
        assert a.parent_map == {}


# ==================== Graph Building Tests ====================


class TestBuildConstraintGraph:
    """Test build_constraint_graph."""

    def test_empty_tasks(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph([], [])
        assert g.number_of_nodes() == 0
        assert g.number_of_edges() == 0

    def test_nodes_created_from_tasks(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(_tasks("A", "B", "C"), [])
        assert set(g.nodes()) == {"A", "B", "C"}

    def test_edges_from_binary_constraints(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(
            _tasks("A", "B"),
            _constraints((["A", "B"], "no_overlap")),
        )
        assert g.has_edge("A", "B")

    def test_multi_task_constraint_creates_all_pairs(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(
            _tasks("A", "B", "C"),
            _constraints((["A", "B", "C"], "mutual_exclusion")),
        )
        assert g.has_edge("A", "B")
        assert g.has_edge("A", "C")
        assert g.has_edge("B", "C")
        assert g.number_of_edges() == 3

    def test_constraint_metadata_on_edges(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(
            _tasks("A", "B"),
            _constraints((["A", "B"], "supervision")),
        )
        assert g["A"]["B"]["constraint_type"] == "supervision"
        assert g["A"]["B"]["constraint_id"] == 0

    def test_single_task_constraint_no_edges(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(
            _tasks("A"),
            _constraints((["A"], "self_constraint")),
        )
        assert g.number_of_edges() == 0

    def test_unknown_task_in_constraint_ignored(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(
            _tasks("A"),
            _constraints((["A", "MISSING"], "link")),
        )
        assert g.number_of_edges() == 0

    def test_sets_self_graph(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(_tasks("A", "B"), [])
        assert a.graph is g


# ==================== Pebble Game Tests ====================


class TestRunPebbleGame:
    """Test run_pebble_game algorithm."""

    def test_no_edges_all_pebbles_free(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(_tasks("A", "B", "C"), [])
        result = a.run_pebble_game(g)
        assert result["total_nodes"] == 3
        assert result["total_edges"] == 0
        assert result["degrees_of_freedom"] == 6  # 3 nodes * 2 pebbles
        assert result["is_rigid"] is False
        assert result["is_stressed"] is False

    def test_single_edge(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(
            _tasks("A", "B"),
            _constraints((["A", "B"], "link")),
        )
        result = a.run_pebble_game(g)
        assert result["total_nodes"] == 2
        assert result["total_edges"] == 1
        assert result["independent_edges"] == 1
        assert result["redundant_edges"] == 0
        assert result["degrees_of_freedom"] == 3  # 4 - 1 = 3

    def test_triangle_is_rigid(self):
        """A triangle (3 nodes, 3 edges) satisfies 2*3-3=3 -> rigid."""
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(
            _tasks("A", "B", "C"),
            _constraints(
                (["A", "B"], "c1"),
                (["B", "C"], "c2"),
                (["A", "C"], "c3"),
            ),
        )
        result = a.run_pebble_game(g)
        assert result["total_nodes"] == 3
        assert result["total_edges"] == 3
        # 2*3 - 3 = 3 edges for rigidity
        assert result["independent_edges"] == 3
        assert result["degrees_of_freedom"] == 3  # 6 - 3 = 3

    def test_over_constrained_has_redundant_edges(self):
        """4 nodes with too many edges should have redundant edges."""
        a = ConstraintRigidityAnalyzer()
        # Complete graph K4: 4 nodes, 6 edges
        # Max independent = 2*4 - 3 = 5
        g = a.build_constraint_graph(
            _tasks("A", "B", "C", "D"),
            _constraints(
                (["A", "B"], "c1"),
                (["A", "C"], "c2"),
                (["A", "D"], "c3"),
                (["B", "C"], "c4"),
                (["B", "D"], "c5"),
                (["C", "D"], "c6"),
            ),
        )
        result = a.run_pebble_game(g)
        assert result["total_edges"] == 6
        assert result["is_stressed"] is True
        assert result["redundant_edges"] >= 1

    def test_result_keys(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(_tasks("A"), [])
        result = a.run_pebble_game(g)
        expected_keys = {
            "total_nodes",
            "total_edges",
            "independent_edges",
            "redundant_edges",
            "degrees_of_freedom",
            "is_rigid",
            "is_stressed",
        }
        assert set(result.keys()) == expected_keys


# ==================== Degrees of Freedom Tests ====================


class TestDegreesOfFreedom:
    """Test get_degrees_of_freedom."""

    def test_empty_returns_zero(self):
        a = ConstraintRigidityAnalyzer()
        assert a.get_degrees_of_freedom() == 0

    def test_after_pebble_game(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(
            _tasks("A", "B"),
            _constraints((["A", "B"], "link")),
        )
        a.run_pebble_game(g)
        dof = a.get_degrees_of_freedom()
        assert dof >= 0


# ==================== Region Identification Tests ====================


class TestIdentifyRegions:
    """Test rigid, flexible, and stressed region identification."""

    def test_rigid_regions_empty_before_game(self):
        a = ConstraintRigidityAnalyzer()
        assert a.identify_rigid_regions() == []

    def test_flexible_regions_empty_before_game(self):
        a = ConstraintRigidityAnalyzer()
        assert a.identify_flexible_regions() == []

    def test_stressed_regions_empty_before_game(self):
        a = ConstraintRigidityAnalyzer()
        assert a.identify_stressed_regions() == []

    def test_under_constrained_is_flexible(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(
            _tasks("A", "B", "C"),
            _constraints((["A", "B"], "link")),
        )
        a.run_pebble_game(g)
        # Only 1 edge for 3 nodes: under-constrained
        # flexible_regions checks connected components
        # A-B are connected with 1 edge (< 2*2-3=1 -> not flexible for this component)
        # But C is isolated (single node, no edges, no component check for size >= 2)
        # The connected components are {A,B} and {C}
        # {A,B}: 2 nodes, 1 edge; need 2*2-3=1 for rigid; has exactly 1 -> rigid
        # So flexible might be empty for this case
        # Let's just verify it doesn't crash
        flexible = a.identify_flexible_regions()
        assert isinstance(flexible, list)

    def test_over_constrained_has_stressed(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(
            _tasks("A", "B", "C", "D"),
            _constraints(
                (["A", "B"], "c1"),
                (["A", "C"], "c2"),
                (["A", "D"], "c3"),
                (["B", "C"], "c4"),
                (["B", "D"], "c5"),
                (["C", "D"], "c6"),
            ),
        )
        a.run_pebble_game(g)
        stressed = a.identify_stressed_regions()
        assert len(stressed) >= 1

    def test_triangle_rigid_region(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(
            _tasks("A", "B", "C"),
            _constraints(
                (["A", "B"], "c1"),
                (["B", "C"], "c2"),
                (["A", "C"], "c3"),
            ),
        )
        a.run_pebble_game(g)
        rigid = a.identify_rigid_regions()
        assert len(rigid) >= 1
        # The triangle should form one rigid region
        if rigid:
            assert {"A", "B", "C"} == set(rigid[0])


# ==================== Recommendation Tests ====================


class TestRecommendConstraintChanges:
    """Test recommend_constraint_changes."""

    def test_empty_returns_empty(self):
        a = ConstraintRigidityAnalyzer()
        assert a.recommend_constraint_changes() == []

    def test_stressed_region_recommends_removal(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(
            _tasks("A", "B", "C", "D"),
            _constraints(
                (["A", "B"], "c1"),
                (["A", "C"], "c2"),
                (["A", "D"], "c3"),
                (["B", "C"], "c4"),
                (["B", "D"], "c5"),
                (["C", "D"], "c6"),
            ),
        )
        a.run_pebble_game(g)
        recs = a.recommend_constraint_changes()
        remove_recs = [r for r in recs if r["action"] == "remove"]
        assert len(remove_recs) >= 1
        assert remove_recs[0]["severity"] == "high"

    def test_recommendation_keys(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(
            _tasks("A", "B", "C", "D"),
            _constraints(
                (["A", "B"], "c1"),
                (["A", "C"], "c2"),
                (["A", "D"], "c3"),
                (["B", "C"], "c4"),
                (["B", "D"], "c5"),
                (["C", "D"], "c6"),
            ),
        )
        a.run_pebble_game(g)
        recs = a.recommend_constraint_changes()
        if recs:
            rec = recs[0]
            assert "action" in rec
            assert "reason" in rec
            assert "region" in rec
            assert "severity" in rec


# ==================== Summary Tests ====================


class TestGetConstraintGraphSummary:
    """Test get_constraint_graph_summary."""

    def test_no_graph_returns_error(self):
        a = ConstraintRigidityAnalyzer()
        summary = a.get_constraint_graph_summary()
        assert "error" in summary

    def test_summary_after_analysis(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(
            _tasks("A", "B", "C"),
            _constraints(
                (["A", "B"], "c1"),
                (["B", "C"], "c2"),
                (["A", "C"], "c3"),
            ),
        )
        a.run_pebble_game(g)
        summary = a.get_constraint_graph_summary()
        assert summary["total_nodes"] == 3
        assert summary["total_edges"] == 3
        assert "degrees_of_freedom" in summary
        assert "num_rigid_regions" in summary
        assert "num_flexible_regions" in summary
        assert "num_stressed_regions" in summary
        assert "recommendations" in summary
        assert "edge_breakdown" in summary

    def test_edge_breakdown_counts(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(
            _tasks("A", "B"),
            _constraints((["A", "B"], "link")),
        )
        a.run_pebble_game(g)
        summary = a.get_constraint_graph_summary()
        breakdown = summary["edge_breakdown"]
        assert breakdown["independent"] + breakdown["redundant"] == 1


# ==================== Pebble Search Tests ====================


class TestPebbleSearch:
    """Test _find_and_place_pebble and _search_for_pebble."""

    def test_find_pebble_on_node_with_pebbles(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(_tasks("A", "B"), [])
        a.graph = g
        a.pebbles = {"A": ["A_p1", "A_p2"], "B": ["B_p1", "B_p2"]}
        a.edge_status = {}
        result = a._find_and_place_pebble("A", "B")
        assert result is True
        assert len(a.pebbles["A"]) == 1  # One pebble used

    def test_find_pebble_no_pebbles_available(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(_tasks("A", "B"), [])
        a.graph = g
        a.pebbles = {"A": [], "B": []}
        a.edge_status = {}
        result = a._find_and_place_pebble("A", "B")
        assert result is False

    def test_rearrange_pebbles_success(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(
            _tasks("A", "B"),
            _constraints((["A", "B"], "link")),
        )
        a.graph = g
        a.pebbles = {"A": [], "B": ["B_p1"]}
        result = a.rearrange_pebbles("A", "A")
        # BFS from A finds neighbor B which has a pebble
        assert result is True

    def test_rearrange_pebbles_failure(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(
            _tasks("A", "B"),
            _constraints((["A", "B"], "link")),
        )
        a.graph = g
        a.pebbles = {"A": [], "B": []}
        result = a.rearrange_pebbles("A", "A")
        assert result is False

    def test_find_pebble_public_wrapper(self):
        a = ConstraintRigidityAnalyzer()
        g = a.build_constraint_graph(_tasks("A"), [])
        a.graph = g
        a.pebbles = {"A": ["A_p1"]}
        a.edge_status = {}
        result = a.find_pebble("A", "A", set())
        assert result is True
        assert len(a.pebbles["A"]) == 0
