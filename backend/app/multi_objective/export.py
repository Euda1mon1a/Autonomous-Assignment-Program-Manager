"""
JSON Export for Multi-Objective Optimization Results.

This module provides export functionality for multi-objective optimization
results, designed to integrate with the holographic visualization hub.

Export Formats:
    1. Trade-Off Landscape: Full Pareto front with objectives and metadata
    2. Solution Details: Individual solution with assignments and metrics
    3. Decision Journey: History of exploration and selections
    4. Quality Summary: Indicator values and front characteristics

Holographic Hub Integration:
    The exported JSON is designed for 3D visualization where:
    - Each axis represents an objective
    - Solutions are points in objective space
    - Colors encode additional information (feasibility, rank)
    - Trade-off curves show Pareto front surface

Classes:
    - HolographicExporter: Main export interface
    - TradeOffLandscape: Pareto front visualization data
    - ParetoVisualization: 3D-ready point cloud format
    - DecisionJourneyExport: User decision path
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

import numpy as np

from .core import (
    ObjectiveConfig,
    ObjectiveDirection,
    ObjectiveType,
    ParetoFrontier,
    Solution,
)
from .indicators import QualityEvaluator, QualityReport
from .decision_support import DecisionMaker


class ExportFormat(Enum):
    """Available export formats."""

    FULL = "full"  # Complete data with all details
    COMPACT = "compact"  # Minimal data for visualization
    HOLOGRAPHIC = "holographic"  # Optimized for 3D visualization


@dataclass
class ObjectiveExport:
    """Exported objective configuration."""

    name: str
    display_name: str
    description: str
    direction: str
    type: str
    weight: float
    reference_point: float | None
    nadir_point: float | None


@dataclass
class SolutionExport:
    """Exported solution data."""

    id: str
    objectives: dict[str, float]
    normalized_objectives: dict[str, float]
    is_feasible: bool
    constraint_violations: list[str]
    rank: int
    crowding_distance: float
    generation: int
    position_3d: list[float] | None = None  # For 3D visualization
    color: str = "#3B82F6"  # Tailwind blue-500 default
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TradeOffEdge:
    """Edge connecting two solutions in trade-off space."""

    from_solution: str
    to_solution: str
    objectives_improved: list[str]
    objectives_degraded: list[str]
    trade_off_magnitude: float


@dataclass
class TradeOffLandscape:
    """
    Complete trade-off landscape for visualization.

    Contains the Pareto front, objective configurations, quality metrics,
    and trade-off relationships for holographic rendering.
    """

    # Metadata
    export_id: str
    created_at: str
    format_version: str = "1.0"

    # Objectives
    objectives: list[ObjectiveExport] = field(default_factory=list)
    n_objectives: int = 0

    # Solutions
    solutions: list[SolutionExport] = field(default_factory=list)
    n_solutions: int = 0

    # Pareto front structure
    frontier_indices: list[int] = field(default_factory=list)
    extreme_indices: list[int] = field(default_factory=list)
    knee_index: int | None = None

    # Trade-off edges
    edges: list[TradeOffEdge] = field(default_factory=list)

    # Quality metrics
    hypervolume: float | None = None
    spread: float | None = None
    spacing: float | None = None

    # Bounds
    ideal_point: list[float] = field(default_factory=list)
    nadir_point: list[float] = field(default_factory=list)

    # Visualization hints
    primary_axes: list[str] = field(default_factory=list)
    recommended_view: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParetoVisualization:
    """
    3D-optimized Pareto front visualization.

    Designed for direct rendering in holographic displays or
    3D scatter plots.
    """

    # Point cloud
    points: list[list[float]] = field(default_factory=list)  # [x, y, z] coordinates
    colors: list[str] = field(default_factory=list)  # Hex color codes
    sizes: list[float] = field(default_factory=list)  # Point sizes
    labels: list[str] = field(default_factory=list)  # Hover labels

    # Axes
    x_axis: str = ""
    y_axis: str = ""
    z_axis: str = ""

    # Axis ranges
    x_range: list[float] = field(default_factory=list)
    y_range: list[float] = field(default_factory=list)
    z_range: list[float] = field(default_factory=list)

    # Surface mesh (optional)
    surface_triangles: list[list[int]] = field(default_factory=list)

    # Camera/view settings
    initial_rotation: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    initial_zoom: float = 1.0


@dataclass
class DecisionJourneyExport:
    """Export of user's decision-making journey."""

    session_id: str
    started_at: str
    ended_at: str | None

    # Path through solution space
    exploration_path: list[str] = field(default_factory=list)  # Solution IDs
    bookmarks: list[str] = field(default_factory=list)

    # Preferences
    comparisons: list[dict[str, Any]] = field(default_factory=list)
    inferred_weights: dict[str, float] = field(default_factory=dict)

    # Selection
    selected_solution: str | None = None
    selection_rationale: str = ""


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for multi-objective types."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, Enum):
            return obj.value
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        return super().default(obj)


class HolographicExporter:
    """
    Export multi-objective results for holographic visualization.

    Produces JSON suitable for 3D rendering, trade-off exploration,
    and interactive decision support interfaces.
    """

    def __init__(self, objectives: list[ObjectiveConfig]):
        """
        Initialize exporter.

        Args:
            objectives: List of objective configurations
        """
        self.objectives = objectives
        self.active_objectives = [o for o in objectives if not o.is_constraint]
        self.quality_evaluator = QualityEvaluator()

    def export_landscape(
        self,
        frontier: ParetoFrontier,
        format: ExportFormat = ExportFormat.FULL,
    ) -> str:
        """
        Export complete trade-off landscape.

        Args:
            frontier: Pareto frontier to export
            format: Export format (FULL, COMPACT, or HOLOGRAPHIC)

        Returns:
            JSON string
        """
        landscape = self._build_landscape(frontier, format)
        return json.dumps(asdict(landscape), cls=CustomJSONEncoder, indent=2)

    def export_visualization(
        self,
        frontier: ParetoFrontier,
        x_objective: str | None = None,
        y_objective: str | None = None,
        z_objective: str | None = None,
    ) -> str:
        """
        Export 3D visualization data.

        Args:
            frontier: Pareto frontier
            x_objective: Objective for X axis (default: first)
            y_objective: Objective for Y axis (default: second)
            z_objective: Objective for Z axis (default: third or None)

        Returns:
            JSON string for 3D rendering
        """
        viz = self._build_visualization(frontier, x_objective, y_objective, z_objective)
        return json.dumps(asdict(viz), cls=CustomJSONEncoder, indent=2)

    def export_decision_journey(
        self,
        decision_maker: DecisionMaker,
    ) -> str:
        """
        Export user's decision-making journey.

        Args:
            decision_maker: Decision maker with history

        Returns:
            JSON string
        """
        journey = self._build_journey(decision_maker)
        return json.dumps(asdict(journey), cls=CustomJSONEncoder, indent=2)

    def export_solution(
        self,
        solution: Solution,
        include_assignments: bool = True,
    ) -> str:
        """
        Export a single solution with full details.

        Args:
            solution: Solution to export
            include_assignments: Whether to include decision variables

        Returns:
            JSON string
        """
        export = self._build_solution_export(solution)
        data = asdict(export)

        if include_assignments:
            data["decision_variables"] = solution.decision_variables

        return json.dumps(data, cls=CustomJSONEncoder, indent=2)

    def _build_landscape(
        self,
        frontier: ParetoFrontier,
        format: ExportFormat,
    ) -> TradeOffLandscape:
        """Build trade-off landscape export."""
        # Export objectives
        obj_exports = []
        for obj in self.active_objectives:
            obj_exports.append(
                ObjectiveExport(
                    name=obj.name,
                    display_name=obj.display_name,
                    description=obj.description,
                    direction=obj.direction.value,
                    type=obj.objective_type.value,
                    weight=obj.weight,
                    reference_point=obj.reference_point,
                    nadir_point=obj.nadir_point,
                )
            )

        # Export solutions
        sol_exports = []
        for i, sol in enumerate(frontier.solutions):
            sol_export = self._build_solution_export(sol)

            # Add 3D position if we have 3+ objectives
            if len(self.active_objectives) >= 3:
                sol_export.position_3d = [
                    sol.objective_values.get(self.active_objectives[0].name, 0.0),
                    sol.objective_values.get(self.active_objectives[1].name, 0.0),
                    sol.objective_values.get(self.active_objectives[2].name, 0.0),
                ]

            # Color based on feasibility and rank
            if not sol.is_feasible:
                sol_export.color = "#EF4444"  # Red
            elif sol.rank == 0:
                sol_export.color = "#10B981"  # Green
            else:
                sol_export.color = "#6B7280"  # Gray

            sol_exports.append(sol_export)

        # Find frontier, extremes, knee
        frontier_indices = list(range(len(frontier.solutions)))  # All on Pareto front
        extreme_sols = frontier.get_extreme_solutions()
        extreme_indices = [
            i for i, s in enumerate(frontier.solutions) if s in extreme_sols
        ]
        knee = frontier.get_knee_solution()
        knee_index = (
            next(
                (i for i, s in enumerate(frontier.solutions) if s.id == knee.id),
                None,
            )
            if knee
            else None
        )

        # Build trade-off edges (for FULL format)
        edges = []
        if format == ExportFormat.FULL:
            edges = self._build_tradeoff_edges(frontier)

        # Quality metrics
        quality = self.quality_evaluator.evaluate(frontier)

        # Ideal and nadir
        ideal = (
            frontier.ideal_point.tolist() if frontier.ideal_point is not None else []
        )
        nadir = (
            frontier.nadir_point.tolist() if frontier.nadir_point is not None else []
        )

        return TradeOffLandscape(
            export_id=str(UUID(int=hash(str(datetime.now())) & (2**128 - 1))),
            created_at=datetime.now().isoformat(),
            objectives=obj_exports,
            n_objectives=len(obj_exports),
            solutions=sol_exports,
            n_solutions=len(sol_exports),
            frontier_indices=frontier_indices,
            extreme_indices=extreme_indices,
            knee_index=knee_index,
            edges=edges,
            hypervolume=quality.hypervolume,
            spread=quality.spread,
            spacing=quality.spacing,
            ideal_point=ideal,
            nadir_point=nadir,
            primary_axes=[o.name for o in self.active_objectives[:3]],
            recommended_view={
                "perspective": "isometric",
                "highlight_knee": True,
                "show_trade_off_edges": len(frontier.solutions) < 50,
            },
        )

    def _build_solution_export(self, solution: Solution) -> SolutionExport:
        """Build solution export."""
        return SolutionExport(
            id=str(solution.id),
            objectives=dict(solution.objective_values),
            normalized_objectives=dict(solution.normalized_objectives),
            is_feasible=solution.is_feasible,
            constraint_violations=list(solution.constraint_violations),
            rank=solution.rank,
            crowding_distance=solution.crowding_distance
            if solution.crowding_distance < float("inf")
            else -1,
            generation=solution.generation,
            metadata=dict(solution.metadata),
        )

    def _build_tradeoff_edges(self, frontier: ParetoFrontier) -> list[TradeOffEdge]:
        """Build trade-off edges between solutions."""
        edges = []
        n = len(frontier.solutions)

        # Only for small fronts (edges grow quadratically)
        if n > 100:
            return edges

        for i in range(n):
            for j in range(i + 1, n):
                sol_a = frontier.solutions[i]
                sol_b = frontier.solutions[j]

                improved = []
                degraded = []
                magnitude = 0.0

                for obj in self.active_objectives:
                    val_a = sol_a.objective_values.get(obj.name, 0.0)
                    val_b = sol_b.objective_values.get(obj.name, 0.0)
                    diff = val_b - val_a

                    if obj.direction == ObjectiveDirection.MAXIMIZE:
                        if diff > 0:
                            improved.append(obj.name)
                        elif diff < 0:
                            degraded.append(obj.name)
                    else:
                        if diff < 0:
                            improved.append(obj.name)
                        elif diff > 0:
                            degraded.append(obj.name)

                    magnitude += abs(diff)

                if improved and degraded:
                    edges.append(
                        TradeOffEdge(
                            from_solution=str(sol_a.id),
                            to_solution=str(sol_b.id),
                            objectives_improved=improved,
                            objectives_degraded=degraded,
                            trade_off_magnitude=magnitude,
                        )
                    )

        return edges

    def _build_visualization(
        self,
        frontier: ParetoFrontier,
        x_obj: str | None,
        y_obj: str | None,
        z_obj: str | None,
    ) -> ParetoVisualization:
        """Build 3D visualization data."""
        # Default to first three objectives
        if not x_obj and len(self.active_objectives) >= 1:
            x_obj = self.active_objectives[0].name
        if not y_obj and len(self.active_objectives) >= 2:
            y_obj = self.active_objectives[1].name
        if not z_obj and len(self.active_objectives) >= 3:
            z_obj = self.active_objectives[2].name

        points = []
        colors = []
        sizes = []
        labels = []

        for sol in frontier.solutions:
            x = sol.objective_values.get(x_obj, 0.0) if x_obj else 0.0
            y = sol.objective_values.get(y_obj, 0.0) if y_obj else 0.0
            z = sol.objective_values.get(z_obj, 0.0) if z_obj else 0.0

            points.append([x, y, z])

            # Color
            if not sol.is_feasible:
                colors.append("#EF4444")
            elif sol.rank == 0:
                colors.append("#10B981")
            else:
                colors.append("#6B7280")

            # Size based on crowding distance
            if sol.crowding_distance == float("inf"):
                sizes.append(1.5)  # Boundary solutions larger
            else:
                sizes.append(1.0)

            # Label
            label_parts = [f"ID: {str(sol.id)[:8]}"]
            for obj in self.active_objectives[:3]:
                val = sol.objective_values.get(obj.name, 0.0)
                label_parts.append(f"{obj.display_name}: {val:.3f}")
            labels.append("\n".join(label_parts))

        # Calculate ranges
        if points:
            points_array = np.array(points)
            x_range = [float(points_array[:, 0].min()), float(points_array[:, 0].max())]
            y_range = [float(points_array[:, 1].min()), float(points_array[:, 1].max())]
            z_range = [float(points_array[:, 2].min()), float(points_array[:, 2].max())]
        else:
            x_range = [0.0, 1.0]
            y_range = [0.0, 1.0]
            z_range = [0.0, 1.0]

        return ParetoVisualization(
            points=points,
            colors=colors,
            sizes=sizes,
            labels=labels,
            x_axis=x_obj or "",
            y_axis=y_obj or "",
            z_axis=z_obj or "",
            x_range=x_range,
            y_range=y_range,
            z_range=z_range,
        )

    def _build_journey(self, dm: DecisionMaker) -> DecisionJourneyExport:
        """Build decision journey export."""
        summary = dm.get_decision_summary()

        comparisons = []
        for event in dm.decision_history:
            if event["type"] == "comparison":
                comparisons.append(
                    {
                        "solution_a": event["solution_a"],
                        "solution_b": event["solution_b"],
                        "preferred": event["preferred"],
                        "timestamp": event["timestamp"],
                    }
                )

        return DecisionJourneyExport(
            session_id=str(UUID(int=hash(str(datetime.now())) & (2**128 - 1))),
            started_at=dm.decision_history[0]["timestamp"]
            if dm.decision_history
            else datetime.now().isoformat(),
            ended_at=dm.decision_history[-1]["timestamp"]
            if dm.decision_history
            else None,
            exploration_path=[str(s.id) for s in dm.explorer.exploration_history],
            bookmarks=[str(s.id) for s in dm.explorer.bookmarks],
            comparisons=comparisons,
            inferred_weights=dm.preference_elicitor.inferred_weights,
            selected_solution=str(dm.selected_solution.id)
            if dm.selected_solution
            else None,
            selection_rationale=dm.get_recommendation()[1]
            if dm.selected_solution
            else "",
        )


def export_for_holographic_hub(
    frontier: ParetoFrontier,
    objectives: list[ObjectiveConfig],
    decision_maker: DecisionMaker | None = None,
) -> dict[str, str]:
    """
    Convenience function to export all data for holographic hub.

    Args:
        frontier: Pareto frontier
        objectives: Objective configurations
        decision_maker: Optional decision maker with history

    Returns:
        Dictionary with keys 'landscape', 'visualization', 'journey'
    """
    exporter = HolographicExporter(objectives)

    result = {
        "landscape": exporter.export_landscape(frontier, ExportFormat.HOLOGRAPHIC),
        "visualization": exporter.export_visualization(frontier),
    }

    if decision_maker:
        result["journey"] = exporter.export_decision_journey(decision_maker)

    return result
