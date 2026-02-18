"""
LangGraph StateGraph definition for the scheduling pipeline.

Converts the monolithic SchedulingEngine.generate() into a graph of
independently testable, traceable nodes with conditional routing for
failure paths.

Usage::

    from app.scheduling.graph import generate_via_graph

    engine = SchedulingEngine(db, start_date, end_date)
    result = generate_via_graph(engine, algorithm="cp_sat", timeout_seconds=60.0)

Or via the engine method::

    result = engine.generate_via_graph(algorithm="cp_sat")
"""

from __future__ import annotations

import time
from typing import Any

from langgraph.graph import END, StateGraph

from app.core.logging import get_logger
from app.scheduling.graph_nodes import (
    activity_solver_node,
    backfill_node,
    build_context_node,
    check_residents_node,
    finalize_node,
    init_node,
    load_data_node,
    persist_and_call_node,
    persist_draft_or_live_node,
    pre_validate_node,
    solve_node,
    validate_node,
)
from app.scheduling.graph_state import ScheduleGraphState

logger = get_logger(__name__)


def _route_after_failure_check(state: ScheduleGraphState) -> str:
    """Route to END if the pipeline has failed, else continue."""
    if state.get("failed"):
        return "end"
    return "continue"


def build_scheduling_graph() -> Any:
    """Build and compile the scheduling pipeline graph.

    Graph topology::

        init → load_data → check_residents ─?→ build_context → pre_validate
          ─?→ solve ─?→ persist_and_call ─?→ activity_solver → backfill
          → persist_draft_or_live → validate → finalize → END

    Where ─?→ indicates a conditional edge that routes to END on failure.
    """
    graph = StateGraph(ScheduleGraphState)

    # Add all nodes
    graph.add_node("init", init_node)
    graph.add_node("load_data", load_data_node)
    graph.add_node("check_residents", check_residents_node)
    graph.add_node("build_context", build_context_node)
    graph.add_node("pre_validate", pre_validate_node)
    graph.add_node("solve", solve_node)
    graph.add_node("persist_and_call", persist_and_call_node)
    graph.add_node("activity_solver", activity_solver_node)
    graph.add_node("backfill", backfill_node)
    graph.add_node("persist_draft_or_live", persist_draft_or_live_node)
    graph.add_node("validate", validate_node)
    graph.add_node("finalize", finalize_node)

    # Set entry point
    graph.set_entry_point("init")

    # Linear edges (no failure possible)
    graph.add_edge("init", "load_data")
    graph.add_edge("load_data", "check_residents")

    # Conditional: check_residents may fail (no residents found)
    graph.add_conditional_edges(
        "check_residents",
        _route_after_failure_check,
        {"continue": "build_context", "end": END},
    )

    graph.add_edge("build_context", "pre_validate")

    # Conditional: pre_validate may fail (infeasible)
    graph.add_conditional_edges(
        "pre_validate",
        _route_after_failure_check,
        {"continue": "solve", "end": END},
    )

    # Conditional: solve may fail
    graph.add_conditional_edges(
        "solve",
        _route_after_failure_check,
        {"continue": "persist_and_call", "end": END},
    )

    # Conditional: PCAT/DO validation may fail in persist_and_call
    graph.add_conditional_edges(
        "persist_and_call",
        _route_after_failure_check,
        {"continue": "activity_solver", "end": END},
    )

    # Linear: activity_solver → backfill → persist → validate → finalize
    graph.add_edge("activity_solver", "backfill")
    graph.add_edge("backfill", "persist_draft_or_live")
    graph.add_edge("persist_draft_or_live", "validate")
    graph.add_edge("validate", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()


# Module-level singleton (compiled once, reused across invocations)
scheduling_graph = build_scheduling_graph()


def generate_via_graph(engine: Any, **params: Any) -> dict[str, Any]:
    """Run the scheduling pipeline via the LangGraph StateGraph.

    This is a standalone function that packages the engine instance
    and parameters into a LangGraph config and invokes the graph.

    Args:
        engine: A SchedulingEngine instance (carries db, constraints, etc.)
        **params: All generate() keyword arguments (algorithm, timeout_seconds, etc.)

    Returns:
        Result dict identical to SchedulingEngine.generate() output.

    Raises:
        RuntimeError: If the graph completes without producing a result.
        Exception: Re-raises any exception after rolling back the DB.
    """
    config = {
        "configurable": {
            "engine": engine,
            "pgy_levels": params.get("pgy_levels"),
            "rotation_template_ids": params.get("rotation_template_ids"),
            "algorithm": params.get("algorithm", "greedy"),
            "timeout_seconds": params.get("timeout_seconds", 60.0),
            "check_resilience": params.get("check_resilience", True),
            "preserve_fmit": params.get("preserve_fmit", True),
            "preserve_resident_inpatient": params.get(
                "preserve_resident_inpatient", True
            ),
            "preserve_absence": params.get("preserve_absence", True),
            "block_number": params.get("block_number"),
            "academic_year": params.get("academic_year"),
            "create_draft": params.get("create_draft", False),
            "created_by_id": params.get("created_by_id"),
            "validate_pcat_do": params.get("validate_pcat_do", True),
        }
    }

    final_state = None
    try:
        final_state = scheduling_graph.invoke({}, config=config)

        if final_state.get("result"):
            return final_state["result"]

        raise RuntimeError("Graph completed without producing a result")

    except Exception as e:
        logger.error(f"Graph execution failed: {e}")
        engine.db.rollback()

        # Update run record to "failed" (mirrors engine.generate() lines 872-879)
        try:
            if final_state and final_state.get("run"):
                run = final_state["run"]
                start_time = final_state.get("start_time", time.time())
                engine.db.refresh(run)
                engine._update_run_status(run, "failed", 0, 0, time.time() - start_time)
                engine.db.commit()
        except Exception:
            logger.error("Failed to update run status after graph failure")
            engine.db.rollback()

        raise
