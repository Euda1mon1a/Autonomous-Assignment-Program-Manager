"""
Penrose Process Visualization for Ergosphere and Energy Extraction.

Provides visualization tools for understanding Penrose efficiency extraction:
- Ergosphere timeline plots
- Energy extraction diagrams
- Swap network graphs
- Phase decomposition visualizations

These visualizations help operators understand where and how efficiency
is being extracted from schedule rotations.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.patches import Rectangle

from app.scheduling.penrose_efficiency import (
    ErgospherePeriod,
    PenroseSwap,
    PhaseComponent,
)

logger = logging.getLogger(__name__)


@dataclass
class VisualizationConfig:
    """Configuration for Penrose visualizations."""

    figsize: tuple[int, int] = (12, 8)
    dpi: int = 100
    color_ergosphere: str = "#FF6B6B"  # Red for high-energy regions
    color_positive: str = "#4ECDC4"  # Cyan for positive energy
    color_negative: str = "#95E1D3"  # Light cyan for negative energy
    color_extraction: str = "#F38181"  # Pink for extraction
    alpha_ergosphere: float = 0.3
    font_size: int = 10


class PenroseVisualizer:
    """
    Visualization tools for Penrose process efficiency extraction.

    Provides methods to visualize:
    - Ergosphere periods on timeline
    - Energy extraction over time
    - Swap networks and dependencies
    - Phase decomposition of assignments

    Example:
        >>> visualizer = PenroseVisualizer()
        >>> fig = visualizer.plot_ergosphere_timeline(ergospheres)
        >>> fig.savefig("ergosphere_timeline.png")
        >>> plt.close(fig)
    """

    def __init__(self, config: VisualizationConfig | None = None) -> None:
        """
        Initialize Penrose visualizer.

        Args:
            config: Visualization configuration (uses defaults if None)
        """
        self.config = config or VisualizationConfig()

    def plot_ergosphere_timeline(
        self, ergospheres: list[ErgospherePeriod], title: str = "Ergosphere Timeline"
    ) -> plt.Figure:
        """
        Plot ergosphere periods on a timeline.

        Shows when and where efficiency extraction opportunities exist.

        Args:
            ergospheres: List of ergosphere periods to visualize
            title: Plot title

        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)

        if not ergospheres:
            ax.text(
                0.5,
                0.5,
                "No ergosphere periods found",
                ha="center",
                va="center",
                fontsize=self.config.font_size,
            )
            ax.set_title(title)
            return fig

            # Sort ergospheres by start time
        sorted_ergospheres = sorted(ergospheres, key=lambda e: e.start_time)

        # Calculate time range
        min_time = min(e.start_time for e in sorted_ergospheres)
        max_time = max(e.end_time for e in sorted_ergospheres)
        time_range = (max_time - min_time).total_seconds() / 3600  # Hours

        # Plot each ergosphere as a rectangle
        y_position = 0
        boundary_type_positions: dict[str, int] = {}

        for ergosphere in sorted_ergospheres:
            # Assign y position based on boundary type
            if ergosphere.boundary_type not in boundary_type_positions:
                boundary_type_positions[ergosphere.boundary_type] = y_position
                y_position += 1

            y_pos = boundary_type_positions[ergosphere.boundary_type]

            # Calculate position and width
            start_offset = (ergosphere.start_time - min_time).total_seconds() / 3600
            width = ergosphere.duration_hours

            # Color intensity based on extraction potential
            alpha = self.config.alpha_ergosphere + (
                ergosphere.extraction_potential
                / 0.29
                * (1 - self.config.alpha_ergosphere)
            )

            # Draw ergosphere rectangle
            rect = Rectangle(
                (start_offset, y_pos - 0.4),
                width,
                0.8,
                facecolor=self.config.color_ergosphere,
                edgecolor="black",
                alpha=alpha,
                linewidth=1,
            )
            ax.add_patch(rect)

            # Add extraction potential label
            label = f"{ergosphere.extraction_potential:.1%}"
            ax.text(
                start_offset + width / 2,
                y_pos,
                label,
                ha="center",
                va="center",
                fontsize=self.config.font_size - 2,
                fontweight="bold",
            )

            # Set axis properties
        ax.set_xlim(0, time_range)
        ax.set_ylim(-0.5, len(boundary_type_positions) - 0.5)
        ax.set_xlabel("Time (hours from start)", fontsize=self.config.font_size)
        ax.set_ylabel("Boundary Type", fontsize=self.config.font_size)

        # Set y-axis labels
        ax.set_yticks(range(len(boundary_type_positions)))
        ax.set_yticklabels(
            [bt.replace("_", " ").title() for bt in boundary_type_positions.keys()]
        )

        ax.set_title(title, fontsize=self.config.font_size + 2)
        ax.grid(True, alpha=0.3, axis="x")

        # Add legend
        legend_elements = [
            Rectangle(
                (0, 0),
                1,
                1,
                facecolor=self.config.color_ergosphere,
                alpha=self.config.alpha_ergosphere,
                label="Low Potential (<10%)",
            ),
            Rectangle(
                (0, 0),
                1,
                1,
                facecolor=self.config.color_ergosphere,
                alpha=0.7,
                label="Medium Potential (10-20%)",
            ),
            Rectangle(
                (0, 0),
                1,
                1,
                facecolor=self.config.color_ergosphere,
                alpha=1.0,
                label="High Potential (>20%)",
            ),
        ]
        ax.legend(handles=legend_elements, loc="upper right")

        plt.tight_layout()
        return fig

    def plot_extraction_efficiency(
        self,
        swaps: list[PenroseSwap],
        title: str = "Penrose Energy Extraction Efficiency",
    ) -> plt.Figure:
        """
        Plot energy extraction over time from executed swaps.

        Shows cumulative efficiency extraction and approach to Penrose limit.

        Args:
            swaps: List of Penrose swaps (executed and proposed)
            title: Plot title

        Returns:
            Matplotlib figure
        """
        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=self.config.figsize, dpi=self.config.dpi, sharex=True
        )

        executed_swaps = [s for s in swaps if s.executed]

        if not executed_swaps:
            ax1.text(
                0.5,
                0.5,
                "No swaps executed yet",
                ha="center",
                va="center",
                fontsize=self.config.font_size,
            )
            ax1.set_title(title)
            return fig

            # Calculate cumulative extraction
        cumulative_extraction = []
        cumulative_value = 0
        swap_numbers = list(range(1, len(executed_swaps) + 1))

        for swap in executed_swaps:
            cumulative_value += swap.net_extraction
            cumulative_extraction.append(cumulative_value)

            # Plot 1: Cumulative extraction
        ax1.plot(
            swap_numbers,
            cumulative_extraction,
            marker="o",
            color=self.config.color_extraction,
            linewidth=2,
            markersize=6,
            label="Cumulative Extraction",
        )

        # Add Penrose limit line
        max_theoretical = (
            cumulative_extraction[-1] / 0.29 if cumulative_extraction else 100
        )
        penrose_limit = [max_theoretical * 0.29] * len(swap_numbers)
        ax1.plot(
            swap_numbers,
            penrose_limit,
            linestyle="--",
            color="red",
            linewidth=2,
            label="Penrose Limit (29%)",
        )

        ax1.set_ylabel("Cumulative Extraction", fontsize=self.config.font_size)
        ax1.set_title(title, fontsize=self.config.font_size + 2)
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # Plot 2: Individual swap contributions
        individual_extractions = [s.net_extraction for s in executed_swaps]
        colors = [
            self.config.color_positive if e > 0 else self.config.color_negative
            for e in individual_extractions
        ]

        ax2.bar(
            swap_numbers,
            individual_extractions,
            color=colors,
            alpha=0.7,
            edgecolor="black",
            linewidth=1,
        )

        ax2.set_xlabel("Swap Number", fontsize=self.config.font_size)
        ax2.set_ylabel("Individual Extraction", fontsize=self.config.font_size)
        ax2.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
        ax2.grid(True, alpha=0.3, axis="y")

        plt.tight_layout()
        return fig

    def plot_swap_network(
        self,
        swaps: list[PenroseSwap],
        title: str = "Penrose Swap Network",
    ) -> plt.Figure:
        """
        Plot network graph of swap relationships.

        Shows how assignments are connected through swaps and identifies
        swap clusters and dependencies.

        Args:
            swaps: List of Penrose swaps
            title: Plot title

        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)

        if not swaps:
            ax.text(
                0.5,
                0.5,
                "No swaps to visualize",
                ha="center",
                va="center",
                fontsize=self.config.font_size,
            )
            ax.set_title(title)
            return fig

            # Build network graph
        G = nx.Graph()

        # Add nodes (assignments)
        assignment_ids = set()
        for swap in swaps:
            assignment_ids.add(swap.assignment_a)
            assignment_ids.add(swap.assignment_b)

        for assignment_id in assignment_ids:
            G.add_node(str(assignment_id)[:8])  # Use first 8 chars for readability

            # Add edges (swaps)
        edge_weights = []
        edge_colors = []

        for swap in swaps:
            node_a = str(swap.assignment_a)[:8]
            node_b = str(swap.assignment_b)[:8]

            # Edge weight = net extraction
            weight = swap.net_extraction
            edge_weights.append(abs(weight) * 5)  # Scale for visibility

            # Color based on execution status
            if swap.executed:
                edge_colors.append(self.config.color_extraction)
            else:
                edge_colors.append(self.config.color_positive)

            G.add_edge(node_a, node_b, weight=weight, swap=swap)

            # Layout
        pos = nx.spring_layout(G, seed=42, k=1.5)

        # Draw network
        nx.draw_networkx_nodes(
            G,
            pos,
            node_color=self.config.color_positive,
            node_size=500,
            alpha=0.7,
            ax=ax,
        )

        nx.draw_networkx_edges(
            G,
            pos,
            width=edge_weights,
            edge_color=edge_colors,
            alpha=0.5,
            ax=ax,
        )

        nx.draw_networkx_labels(
            G,
            pos,
            font_size=self.config.font_size - 2,
            font_weight="bold",
            ax=ax,
        )

        # Add edge labels for executed swaps
        executed_edges = {
            (
                str(s.assignment_a)[:8],
                str(s.assignment_b)[:8],
            ): f"{s.net_extraction:.1f}"
            for s in swaps
            if s.executed
        }

        nx.draw_networkx_edge_labels(
            G,
            pos,
            executed_edges,
            font_size=self.config.font_size - 3,
            ax=ax,
        )

        ax.set_title(title, fontsize=self.config.font_size + 2)
        ax.axis("off")

        # Add legend
        legend_elements = [
            plt.Line2D(
                [0],
                [0],
                color=self.config.color_extraction,
                linewidth=3,
                label="Executed Swap",
            ),
            plt.Line2D(
                [0],
                [0],
                color=self.config.color_positive,
                linewidth=3,
                label="Proposed Swap",
            ),
        ]
        ax.legend(handles=legend_elements, loc="upper left")

        plt.tight_layout()
        return fig

    def plot_phase_decomposition(
        self,
        phases: list[PhaseComponent],
        title: str = "Assignment Phase Decomposition",
    ) -> plt.Figure:
        """
        Plot phase decomposition of assignments.

        Shows how assignments are split into pre-transition, transition,
        and post-transition phases with energy states.

        Args:
            phases: List of phase components
            title: Plot title

        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)

        if not phases:
            ax.text(
                0.5,
                0.5,
                "No phase data to visualize",
                ha="center",
                va="center",
                fontsize=self.config.font_size,
            )
            ax.set_title(title)
            return fig

            # Group phases by assignment
        phases_by_assignment: dict[UUID, list[PhaseComponent]] = {}
        for phase in phases:
            if phase.assignment_id not in phases_by_assignment:
                phases_by_assignment[phase.assignment_id] = []
            phases_by_assignment[phase.assignment_id].append(phase)

            # Sort assignments
        sorted_assignments = sorted(phases_by_assignment.keys())

        # Plot each assignment's phases
        y_position = 0
        phase_type_order = ["pre_transition", "transition", "post_transition"]

        for assignment_id in sorted_assignments:
            assignment_phases = phases_by_assignment[assignment_id]
            assignment_phases.sort(key=lambda p: phase_type_order.index(p.phase_type))

            x_offset = 0
            for phase in assignment_phases:
                # Determine color based on energy state
                if phase.energy_state == "negative":
                    color = self.config.color_negative
                elif phase.energy_state == "positive":
                    color = self.config.color_positive
                else:
                    color = "gray"

                    # Width proportional to phase duration
                duration = (phase.phase_end - phase.phase_start).total_seconds() / 3600
                width = duration / 24  # Normalize to 24-hour scale

                # Draw phase rectangle
                rect = Rectangle(
                    (x_offset, y_position - 0.4),
                    width,
                    0.8,
                    facecolor=color,
                    edgecolor="black",
                    alpha=0.7,
                    linewidth=1,
                )
                ax.add_patch(rect)

                # Add conflict score label
                if phase.conflict_score > 0:
                    ax.text(
                        x_offset + width / 2,
                        y_position,
                        str(phase.conflict_score),
                        ha="center",
                        va="center",
                        fontsize=self.config.font_size - 3,
                        color="red",
                        fontweight="bold",
                    )

                x_offset += width

            y_position += 1

            # Set axis properties
        ax.set_xlim(0, 3)  # Three phases
        ax.set_ylim(-0.5, len(sorted_assignments) - 0.5)
        ax.set_xlabel("Phase Progression", fontsize=self.config.font_size)
        ax.set_ylabel("Assignment", fontsize=self.config.font_size)

        # Set x-axis labels
        ax.set_xticks([0.5, 1.5, 2.5])
        ax.set_xticklabels(["Pre-Transition", "Transition", "Post-Transition"])

        # Set y-axis labels
        ax.set_yticks(range(len(sorted_assignments)))
        ax.set_yticklabels([str(aid)[:8] for aid in sorted_assignments])

        ax.set_title(title, fontsize=self.config.font_size + 2)
        ax.grid(True, alpha=0.3, axis="x")

        # Add legend
        legend_elements = [
            Rectangle(
                (0, 0),
                1,
                1,
                facecolor=self.config.color_negative,
                alpha=0.7,
                label="Negative Energy",
            ),
            Rectangle(
                (0, 0),
                1,
                1,
                facecolor="gray",
                alpha=0.7,
                label="Zero Energy",
            ),
            Rectangle(
                (0, 0),
                1,
                1,
                facecolor=self.config.color_positive,
                alpha=0.7,
                label="Positive Energy",
            ),
        ]
        ax.legend(handles=legend_elements, loc="upper right")

        plt.tight_layout()
        return fig

    def generate_summary_report(
        self,
        ergospheres: list[ErgospherePeriod],
        swaps: list[PenroseSwap],
        efficiency: float,
    ) -> dict[str, Any]:
        """
        Generate text summary report of Penrose extraction.

        Args:
            ergospheres: List of ergosphere periods
            swaps: List of Penrose swaps
            efficiency: Total extraction efficiency

        Returns:
            Dictionary with report sections
        """
        executed_swaps = [s for s in swaps if s.executed]

        report = {
            "summary": {
                "total_ergospheres": len(ergospheres),
                "high_potential_ergospheres": sum(
                    1 for e in ergospheres if e.is_high_potential
                ),
                "total_swaps_proposed": len(swaps),
                "total_swaps_executed": len(executed_swaps),
                "efficiency_extracted": f"{efficiency:.2%}",
                "penrose_limit_usage": f"{(efficiency / 0.29):.1%}",
            },
            "ergosphere_breakdown": {
                boundary_type: len(
                    [e for e in ergospheres if e.boundary_type == boundary_type]
                )
                for boundary_type in set(e.boundary_type for e in ergospheres)
            },
            "top_extractions": [
                {
                    "swap_id": str(s.swap_id)[:8],
                    "extraction": f"{s.net_extraction:.2f}",
                    "local_cost": f"{s.local_cost:.2f}",
                    "global_benefit": f"{s.global_benefit:.2f}",
                    "ratio": f"{s.extraction_ratio:.2f}x",
                }
                for s in sorted(
                    executed_swaps, key=lambda s: s.net_extraction, reverse=True
                )[:10]
            ],
            "recommendations": self._generate_recommendations(
                ergospheres, swaps, efficiency
            ),
        }

        return report

    def _generate_recommendations(
        self,
        ergospheres: list[ErgospherePeriod],
        swaps: list[PenroseSwap],
        efficiency: float,
    ) -> list[str]:
        """
        Generate recommendations based on extraction analysis.

        Args:
            ergospheres: List of ergosphere periods
            swaps: List of Penrose swaps
            efficiency: Total extraction efficiency

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Check if approaching Penrose limit
        if efficiency > 0.25:
            recommendations.append(
                f"⚠️ Approaching Penrose limit ({efficiency:.1%}/29%). "
                "Further optimization may yield diminishing returns."
            )

            # Check for high-potential ergospheres
        high_potential = [e for e in ergospheres if e.is_high_potential]
        if high_potential:
            recommendations.append(
                f"✓ {len(high_potential)} high-potential ergospheres identified. "
                "Focus optimization efforts on these periods."
            )

            # Check for underutilized swaps
        unexecuted = [s for s in swaps if not s.executed and s.is_beneficial]
        if unexecuted:
            total_potential = sum(s.net_extraction for s in unexecuted)
            recommendations.append(
                f"💡 {len(unexecuted)} beneficial swaps not executed. "
                f"Potential additional extraction: {total_potential:.2f}"
            )

            # Check for low extraction efficiency
        if efficiency < 0.05:
            recommendations.append(
                "⚠️ Low extraction efficiency. Consider relaxing constraints "
                "or expanding ergosphere search window."
            )

        return recommendations
