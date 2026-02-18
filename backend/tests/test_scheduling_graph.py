"""Tests for the LangGraph scheduling pipeline.

Tests individual graph nodes in isolation using mocks,
plus graph compilation and topology integration tests.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest


def _make_config(engine_mock: MagicMock, **overrides) -> dict:
    """Build a LangGraph RunnableConfig dict with a mock engine."""
    defaults = {
        "engine": engine_mock,
        "algorithm": "cp_sat",
        "timeout_seconds": 60.0,
        "check_resilience": True,
        "preserve_fmit": True,
        "preserve_resident_inpatient": True,
        "preserve_absence": True,
        "create_draft": False,
        "block_number": None,
        "academic_year": None,
        "validate_pcat_do": True,
        "pgy_levels": None,
        "rotation_template_ids": None,
        "created_by_id": None,
    }
    defaults.update(overrides)
    return {"configurable": defaults}


def _make_engine_mock() -> MagicMock:
    """Create a mock SchedulingEngine with common attributes."""
    engine = MagicMock()
    engine.ALGORITHMS = ["greedy", "cp_sat", "pulp", "hybrid"]
    engine.start_date = MagicMock()
    engine.start_date.month = 8
    engine.start_date.year = 2025
    engine.end_date = MagicMock()
    engine.assignments = []
    engine._empty_validation.return_value = MagicMock()
    return engine


# ─── Node Unit Tests ──────────────────────────────────────────────────


class TestInitNode:
    def test_creates_run_and_sets_start_time(self):
        from app.scheduling.graph_nodes import init_node

        engine = _make_engine_mock()
        mock_run = MagicMock()
        mock_run.id = uuid4()
        engine._create_initial_run.return_value = mock_run
        engine._check_pre_generation_resilience.return_value = None

        config = _make_config(engine)
        result = init_node({}, config)

        assert result["run_id"] == mock_run.id
        assert result["failed"] is False
        assert "start_time" in result
        assert isinstance(result["start_time"], float)
        engine._create_initial_run.assert_called_once_with("cp_sat")

    def test_forces_cp_sat_algorithm(self):
        from app.scheduling.graph_nodes import init_node

        engine = _make_engine_mock()
        mock_run = MagicMock()
        mock_run.id = uuid4()
        engine._create_initial_run.return_value = mock_run

        config = _make_config(engine, algorithm="greedy")
        init_node({}, config)

        engine._create_initial_run.assert_called_once_with("cp_sat")

    def test_skips_resilience_when_disabled(self):
        from app.scheduling.graph_nodes import init_node

        engine = _make_engine_mock()
        mock_run = MagicMock()
        mock_run.id = uuid4()
        engine._create_initial_run.return_value = mock_run

        config = _make_config(engine, check_resilience=False)
        init_node({}, config)

        engine._check_pre_generation_resilience.assert_not_called()


class TestCheckResidentsNode:
    def test_fails_when_no_residents(self):
        from app.scheduling.graph_nodes import check_residents_node

        engine = _make_engine_mock()
        config = _make_config(engine)

        state = {
            "residents": [],
            "blocks": [],
            "run": MagicMock(),
            "run_id": uuid4(),
            "start_time": time.time(),
        }
        result = check_residents_node(state, config)

        assert result["failed"] is True
        assert result["result"]["status"] == "failed"
        assert "No residents" in result["result"]["message"]

    def test_passes_when_residents_exist(self):
        from app.scheduling.graph_nodes import check_residents_node

        engine = _make_engine_mock()
        config = _make_config(engine)

        state = {
            "residents": [MagicMock()],
            "blocks": [],
            "run": MagicMock(),
            "run_id": uuid4(),
            "start_time": time.time(),
        }
        result = check_residents_node(state, config)

        assert result["failed"] is False


class TestPreValidateNode:
    def test_fails_when_infeasible(self):
        from app.scheduling.graph_nodes import pre_validate_node

        engine = _make_engine_mock()
        config = _make_config(engine)

        mock_validation = MagicMock()
        mock_validation.feasible = False
        mock_validation.issues = ["Not enough residents"]
        mock_validation.recommendations = ["Add more residents"]
        mock_validation.statistics = {"complexity_level": "HIGH"}
        mock_validation.warnings = []

        with patch(
            "app.scheduling.pre_solver_validator.PreSolverValidator"
        ) as MockValidator:
            MockValidator.return_value.validate_saturation.return_value = (
                mock_validation
            )

            state = {
                "context": MagicMock(),
                "blocks": [],
                "run": MagicMock(),
                "run_id": uuid4(),
                "start_time": time.time(),
            }
            result = pre_validate_node(state, config)

        assert result["failed"] is True
        assert result["pre_validation_passed"] is False
        assert result["result"]["status"] == "failed"

    def test_passes_when_feasible(self):
        from app.scheduling.graph_nodes import pre_validate_node

        engine = _make_engine_mock()
        config = _make_config(engine)

        mock_validation = MagicMock()
        mock_validation.feasible = True
        mock_validation.issues = []
        mock_validation.recommendations = []
        mock_validation.statistics = {
            "complexity_level": "LOW",
            "num_variables": 100,
            "estimated_runtime": "< 1s",
        }
        mock_validation.warnings = []

        with patch(
            "app.scheduling.pre_solver_validator.PreSolverValidator"
        ) as MockValidator:
            MockValidator.return_value.validate_saturation.return_value = (
                mock_validation
            )

            state = {
                "context": MagicMock(),
                "blocks": [],
                "run": MagicMock(),
                "run_id": uuid4(),
                "start_time": time.time(),
            }
            result = pre_validate_node(state, config)

        assert result["failed"] is False
        assert result["pre_validation_passed"] is True


class TestSolveNode:
    def test_fails_on_solver_error(self):
        from app.scheduling.graph_nodes import solve_node

        engine = _make_engine_mock()
        config = _make_config(engine)

        mock_solver_result = MagicMock()
        mock_solver_result.success = False
        mock_solver_result.solver_status = "INFEASIBLE"
        mock_solver_result.statistics = {}
        engine._run_solver.return_value = mock_solver_result

        state = {
            "context": MagicMock(),
            "blocks": [],
            "run": MagicMock(),
            "run_id": uuid4(),
            "start_time": time.time(),
        }
        result = solve_node(state, config)

        assert result["failed"] is True
        assert result["result"]["status"] == "failed"
        assert "INFEASIBLE" in result["result"]["message"]

    def test_passes_on_solver_success(self):
        from app.scheduling.graph_nodes import solve_node

        engine = _make_engine_mock()
        config = _make_config(engine)

        mock_solver_result = MagicMock()
        mock_solver_result.success = True
        mock_solver_result.assignments = [(uuid4(), uuid4(), uuid4())]
        mock_solver_result.call_assignments = []
        engine._run_solver.return_value = mock_solver_result

        state = {
            "context": MagicMock(),
            "blocks": [],
            "run": MagicMock(),
            "run_id": uuid4(),
            "start_time": time.time(),
        }
        result = solve_node(state, config)

        assert result["failed"] is False
        assert result["solver_result"] == mock_solver_result


class TestBackfillNode:
    def test_skips_in_draft_mode(self):
        from app.scheduling.graph_nodes import backfill_node

        engine = _make_engine_mock()
        config = _make_config(engine, create_draft=True)

        state = {"residents": [MagicMock()], "blocks": [MagicMock()]}
        backfill_node(state, config)

        engine._backfill_weekend_slots.assert_not_called()
        engine._backfill_virtual_clinic.assert_not_called()

    def test_runs_backfill_in_live_mode(self):
        from app.scheduling.graph_nodes import backfill_node

        engine = _make_engine_mock()
        config = _make_config(engine, create_draft=False)

        residents = [MagicMock()]
        blocks = [MagicMock()]
        state = {"residents": residents, "blocks": blocks}
        backfill_node(state, config)

        engine._backfill_weekend_slots.assert_called_once_with(residents, blocks)
        engine._backfill_virtual_clinic.assert_called_once_with(residents)


# ─── Graph Integration Tests ─────────────────────────────────────────


class TestGraphCompilation:
    def test_graph_compiles(self):
        """Verify the graph compiles without errors."""
        from app.scheduling.graph import build_scheduling_graph

        graph = build_scheduling_graph()
        assert graph is not None

    def test_graph_has_expected_nodes(self):
        """Verify all expected nodes are present."""
        from app.scheduling.graph import build_scheduling_graph

        graph = build_scheduling_graph()
        graph_def = graph.get_graph()
        # LangGraph returns node IDs as strings directly
        node_ids = set(graph_def.nodes)

        expected_nodes = {
            "__start__",
            "init",
            "load_data",
            "check_residents",
            "build_context",
            "pre_validate",
            "solve",
            "persist_and_call",
            "activity_solver",
            "backfill",
            "persist_draft_or_live",
            "validate",
            "finalize",
            "__end__",
        }
        assert expected_nodes == node_ids

    def test_singleton_is_compiled(self):
        """Verify module-level singleton exists."""
        from app.scheduling.graph import scheduling_graph

        assert scheduling_graph is not None


class TestRouteAfterFailureCheck:
    def test_routes_to_end_when_failed(self):
        from app.scheduling.graph import _route_after_failure_check

        state = {"failed": True}
        assert _route_after_failure_check(state) == "end"

    def test_routes_to_continue_when_not_failed(self):
        from app.scheduling.graph import _route_after_failure_check

        state = {"failed": False}
        assert _route_after_failure_check(state) == "continue"

    def test_routes_to_continue_when_failed_missing(self):
        from app.scheduling.graph import _route_after_failure_check

        state = {}
        assert _route_after_failure_check(state) == "continue"
