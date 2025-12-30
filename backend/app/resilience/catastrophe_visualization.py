"""
Catastrophe Theory Visualization.

3D surface plots and 2D contour maps for visualizing catastrophe boundaries
and parameter space exploration.

Generates publication-quality visualizations of:
- Feasibility surface across (demand, strictness) space
- Cusp catastrophe boundaries
- System trajectory through parameter space
- Hysteresis loops
- Critical thresholds

Optional dependencies:
- matplotlib: 2D contour plots
- plotly: Interactive 3D surface plots
- seaborn: Enhanced styling
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from app.resilience.catastrophe_detector import (
    CuspAnalysis,
    FeasibilitySurface,
    ParameterState,
)

logger = logging.getLogger(__name__)

# Try to import optional visualization libraries
try:
    import matplotlib.pyplot as plt
    from matplotlib import cm
    from mpl_toolkits.mplot3d import Axes3D

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    logger.warning("matplotlib not available - 2D/3D plotting disabled")

try:
    import plotly.graph_objects as go

    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    logger.warning("plotly not available - interactive 3D plots disabled")

try:
    import seaborn as sns

    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False


# =============================================================================
# Visualization Functions
# =============================================================================


class CatastropheVisualizer:
    """
    Visualization tools for catastrophe theory analysis.

    Generates plots showing:
    - 3D feasibility surfaces
    - 2D contour maps with catastrophe boundaries
    - Parameter trajectories
    - Cusp points and fold lines
    """

    def __init__(self, style: str = "default"):
        """
        Initialize visualizer.

        Args:
            style: Matplotlib style ('default', 'seaborn', 'ggplot', etc.)
        """
        self.style = style

        if HAS_MATPLOTLIB:
            plt.style.use(style)
            if HAS_SEABORN:
                sns.set_palette("husl")

        logger.info(f"CatastropheVisualizer initialized with style '{style}'")

    def plot_feasibility_surface_3d(
        self,
        surface: FeasibilitySurface,
        cusp_analysis: CuspAnalysis | None = None,
        trajectory: list[ParameterState] | None = None,
        output_path: str | Path | None = None,
        interactive: bool = False,
    ) -> Any:
        """
        Create 3D surface plot of feasibility across parameter space.

        Args:
            surface: FeasibilitySurface to visualize
            cusp_analysis: Optional cusp analysis to overlay
            trajectory: Optional trajectory to plot
            output_path: Path to save plot (PNG/HTML)
            interactive: Use plotly for interactive plot (requires plotly)

        Returns:
            Figure object (matplotlib Figure or plotly Figure)

        Example:
            >>> visualizer = CatastropheVisualizer()
            >>> fig = visualizer.plot_feasibility_surface_3d(
            ...     surface,
            ...     cusp_analysis=analysis,
            ...     output_path="catastrophe_surface.png"
            ... )
        """
        if interactive and HAS_PLOTLY:
            return self._plot_3d_plotly(surface, cusp_analysis, trajectory, output_path)
        elif HAS_MATPLOTLIB:
            return self._plot_3d_matplotlib(
                surface, cusp_analysis, trajectory, output_path
            )
        else:
            logger.error("No visualization library available")
            return None

    def _plot_3d_matplotlib(
        self,
        surface: FeasibilitySurface,
        cusp_analysis: CuspAnalysis | None,
        trajectory: list[ParameterState] | None,
        output_path: str | Path | None,
    ):
        """Create 3D plot using matplotlib."""
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection="3d")

        # Create meshgrid
        D, S = np.meshgrid(surface.demand_values, surface.strictness_values)

        # Plot surface
        surf = ax.plot_surface(
            D,
            S,
            surface.feasibility_grid,
            cmap=cm.viridis,
            alpha=0.8,
            edgecolor="none",
        )

        # Add cusp point if available
        if cusp_analysis and cusp_analysis.cusp_exists and cusp_analysis.cusp_center:
            cusp_d, cusp_s = cusp_analysis.cusp_center
            # Get feasibility at cusp
            cusp_f = surface.get_feasibility(cusp_d, cusp_s)
            if cusp_f is not None:
                ax.scatter(
                    [cusp_d],
                    [cusp_s],
                    [cusp_f],
                    c="red",
                    s=200,
                    marker="*",
                    label="Cusp Point",
                    edgecolor="black",
                    linewidth=2,
                )

        # Add trajectory if available
        if trajectory:
            traj_demands = [p.demand for p in trajectory]
            traj_strictness = [p.strictness for p in trajectory]
            traj_feas = [
                surface.get_feasibility(p.demand, p.strictness) or 0.5
                for p in trajectory
            ]

            ax.plot(
                traj_demands,
                traj_strictness,
                traj_feas,
                c="red",
                linewidth=3,
                marker="o",
                markersize=6,
                label="System Trajectory",
            )

        # Labels and title
        ax.set_xlabel("Coverage Demand", fontsize=12, labelpad=10)
        ax.set_ylabel("Constraint Strictness", fontsize=12, labelpad=10)
        ax.set_zlabel("Feasibility Score", fontsize=12, labelpad=10)
        ax.set_title(
            "Schedule Feasibility Surface\n(Cusp Catastrophe Model)",
            fontsize=14,
            pad=20,
        )

        # Add colorbar
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label="Feasibility")

        # Legend
        if cusp_analysis or trajectory:
            ax.legend(loc="upper left")

        # View angle
        ax.view_init(elev=20, azim=45)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            logger.info(f"Saved 3D surface plot to {output_path}")

        return fig

    def _plot_3d_plotly(
        self,
        surface: FeasibilitySurface,
        cusp_analysis: CuspAnalysis | None,
        trajectory: list[ParameterState] | None,
        output_path: str | Path | None,
    ):
        """Create interactive 3D plot using plotly."""
        # Create meshgrid
        D, S = np.meshgrid(surface.demand_values, surface.strictness_values)

        # Create surface
        fig = go.Figure(
            data=[
                go.Surface(
                    x=D,
                    y=S,
                    z=surface.feasibility_grid,
                    colorscale="Viridis",
                    name="Feasibility Surface",
                    colorbar=dict(title="Feasibility"),
                )
            ]
        )

        # Add cusp point
        if cusp_analysis and cusp_analysis.cusp_exists and cusp_analysis.cusp_center:
            cusp_d, cusp_s = cusp_analysis.cusp_center
            cusp_f = surface.get_feasibility(cusp_d, cusp_s)
            if cusp_f is not None:
                fig.add_trace(
                    go.Scatter3d(
                        x=[cusp_d],
                        y=[cusp_s],
                        z=[cusp_f],
                        mode="markers",
                        marker=dict(size=15, color="red", symbol="diamond"),
                        name="Cusp Point",
                    )
                )

        # Add trajectory
        if trajectory:
            traj_demands = [p.demand for p in trajectory]
            traj_strictness = [p.strictness for p in trajectory]
            traj_feas = [
                surface.get_feasibility(p.demand, p.strictness) or 0.5
                for p in trajectory
            ]

            fig.add_trace(
                go.Scatter3d(
                    x=traj_demands,
                    y=traj_strictness,
                    z=traj_feas,
                    mode="lines+markers",
                    line=dict(color="red", width=4),
                    marker=dict(size=5),
                    name="System Trajectory",
                )
            )

        # Layout
        fig.update_layout(
            title="Schedule Feasibility Surface (Interactive 3D)",
            scene=dict(
                xaxis_title="Coverage Demand",
                yaxis_title="Constraint Strictness",
                zaxis_title="Feasibility Score",
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.3)),
            ),
            width=1000,
            height=700,
        )

        if output_path:
            fig.write_html(str(output_path))
            logger.info(f"Saved interactive 3D plot to {output_path}")

        return fig

    def plot_contour_map_2d(
        self,
        surface: FeasibilitySurface,
        cusp_analysis: CuspAnalysis | None = None,
        trajectory: list[ParameterState] | None = None,
        current_params: ParameterState | None = None,
        output_path: str | Path | None = None,
    ):
        """
        Create 2D contour map of feasibility with catastrophe boundaries.

        Args:
            surface: FeasibilitySurface to visualize
            cusp_analysis: Optional cusp analysis to overlay
            trajectory: Optional trajectory to plot
            current_params: Optional current system state to highlight
            output_path: Path to save plot (PNG)

        Returns:
            matplotlib Figure

        Example:
            >>> fig = visualizer.plot_contour_map_2d(
            ...     surface,
            ...     cusp_analysis=analysis,
            ...     current_params=current_state,
            ...     output_path="contour_map.png"
            ... )
        """
        if not HAS_MATPLOTLIB:
            logger.error("matplotlib required for contour plots")
            return None

        fig, ax = plt.subplots(figsize=(10, 8))

        # Contour plot
        D, S = np.meshgrid(surface.demand_values, surface.strictness_values)
        contour = ax.contourf(
            D, S, surface.feasibility_grid, levels=15, cmap="RdYlGn", alpha=0.8
        )
        contour_lines = ax.contour(
            D, S, surface.feasibility_grid, levels=10, colors="black", linewidths=0.5
        )
        ax.clabel(contour_lines, inline=True, fontsize=8)

        # Add catastrophe boundary
        if cusp_analysis and cusp_analysis.cusp_exists:
            # Plot upper boundary
            if cusp_analysis.upper_boundary:
                upper_d = [p[0] for p in cusp_analysis.upper_boundary]
                upper_s = [p[1] for p in cusp_analysis.upper_boundary]
                ax.plot(
                    upper_d,
                    upper_s,
                    "r--",
                    linewidth=2,
                    label="Upper Fold",
                    alpha=0.7,
                )

            # Plot lower boundary
            if cusp_analysis.lower_boundary:
                lower_d = [p[0] for p in cusp_analysis.lower_boundary]
                lower_s = [p[1] for p in cusp_analysis.lower_boundary]
                ax.plot(
                    lower_d,
                    lower_s,
                    "b--",
                    linewidth=2,
                    label="Lower Fold",
                    alpha=0.7,
                )

            # Mark cusp point
            if cusp_analysis.cusp_center:
                ax.scatter(
                    [cusp_analysis.cusp_center[0]],
                    [cusp_analysis.cusp_center[1]],
                    c="red",
                    s=300,
                    marker="*",
                    edgecolor="black",
                    linewidth=2,
                    label="Cusp Point",
                    zorder=5,
                )

        # Add trajectory
        if trajectory:
            traj_d = [p.demand for p in trajectory]
            traj_s = [p.strictness for p in trajectory]
            ax.plot(
                traj_d,
                traj_s,
                "ko-",
                linewidth=2,
                markersize=6,
                label="Historical Trajectory",
                alpha=0.7,
            )

            # Arrow showing direction
            if len(trajectory) >= 2:
                ax.annotate(
                    "",
                    xy=(trajectory[-1].demand, trajectory[-1].strictness),
                    xytext=(trajectory[-2].demand, trajectory[-2].strictness),
                    arrowprops=dict(arrowstyle="->", lw=2, color="black"),
                )

        # Mark current state
        if current_params:
            ax.scatter(
                [current_params.demand],
                [current_params.strictness],
                c="yellow",
                s=200,
                marker="D",
                edgecolor="black",
                linewidth=2,
                label="Current State",
                zorder=6,
            )

        # Labels and title
        ax.set_xlabel("Coverage Demand", fontsize=12)
        ax.set_ylabel("Constraint Strictness", fontsize=12)
        ax.set_title("Schedule Feasibility Contour Map\n(Catastrophe Boundaries)", fontsize=14)

        # Colorbar
        cbar = plt.colorbar(contour, ax=ax, label="Feasibility Score")

        # Legend
        ax.legend(loc="upper right", fontsize=10)

        # Grid
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            logger.info(f"Saved contour map to {output_path}")

        return fig

    def plot_hysteresis_loop(
        self,
        surface: FeasibilitySurface,
        strictness_level: float,
        output_path: str | Path | None = None,
    ):
        """
        Plot hysteresis loop at a specific strictness level.

        Shows how feasibility changes differently when demand increases vs decreases.

        Args:
            surface: FeasibilitySurface to analyze
            strictness_level: Strictness level to plot (0.0 - 1.0)
            output_path: Path to save plot

        Returns:
            matplotlib Figure
        """
        if not HAS_MATPLOTLIB:
            logger.error("matplotlib required for hysteresis plots")
            return None

        # Find closest strictness index
        s_idx = np.argmin(np.abs(surface.strictness_values - strictness_level))
        actual_strictness = surface.strictness_values[s_idx]

        # Extract feasibility at this strictness level
        feasibility_curve = surface.feasibility_grid[s_idx, :]

        fig, ax = plt.subplots(figsize=(10, 6))

        # Forward path (increasing demand)
        ax.plot(
            surface.demand_values,
            feasibility_curve,
            "b-o",
            linewidth=2,
            markersize=5,
            label="Demand Increasing",
            alpha=0.7,
        )

        # Backward path (would be different in real hysteresis)
        # For visualization, show the same curve but with arrows
        ax.annotate(
            "",
            xy=(surface.demand_values[-1], feasibility_curve[-1]),
            xytext=(surface.demand_values[-2], feasibility_curve[-2]),
            arrowprops=dict(arrowstyle="->", lw=2, color="blue"),
        )

        # Mark critical points
        critical_idx = np.argmin(np.abs(feasibility_curve - 0.5))
        ax.scatter(
            [surface.demand_values[critical_idx]],
            [feasibility_curve[critical_idx]],
            c="red",
            s=200,
            marker="X",
            edgecolor="black",
            linewidth=2,
            label="Critical Point",
            zorder=5,
        )

        # Add regions
        ax.axhline(y=0.7, color="green", linestyle="--", alpha=0.5, label="Safe Threshold")
        ax.axhline(y=0.3, color="red", linestyle="--", alpha=0.5, label="Failure Threshold")

        ax.set_xlabel("Coverage Demand", fontsize=12)
        ax.set_ylabel("Feasibility Score", fontsize=12)
        ax.set_title(
            f"Hysteresis Loop at Strictness = {actual_strictness:.2f}", fontsize=14
        )
        ax.legend(loc="best", fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(-0.05, 1.05)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            logger.info(f"Saved hysteresis plot to {output_path}")

        return fig

    def plot_parameter_evolution(
        self,
        trajectory: list[ParameterState],
        output_path: str | Path | None = None,
    ):
        """
        Plot parameter evolution over time.

        Args:
            trajectory: List of ParameterState over time
            output_path: Path to save plot

        Returns:
            matplotlib Figure
        """
        if not HAS_MATPLOTLIB:
            logger.error("matplotlib required for evolution plots")
            return None

        if not trajectory:
            logger.warning("Empty trajectory provided")
            return None

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 10), sharex=True)

        timestamps = [p.timestamp for p in trajectory]
        demands = [p.demand for p in trajectory]
        strictness = [p.strictness for p in trajectory]
        feasibility = [p.feasibility_score or 0.5 for p in trajectory]

        # Plot demand
        ax1.plot(timestamps, demands, "b-o", linewidth=2, markersize=4)
        ax1.set_ylabel("Coverage Demand", fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.set_title("Parameter Evolution Over Time", fontsize=14)

        # Plot strictness
        ax2.plot(timestamps, strictness, "r-o", linewidth=2, markersize=4)
        ax2.set_ylabel("Constraint Strictness", fontsize=12)
        ax2.grid(True, alpha=0.3)

        # Plot feasibility
        ax3.plot(timestamps, feasibility, "g-o", linewidth=2, markersize=4)
        ax3.axhline(y=0.7, color="green", linestyle="--", alpha=0.5, label="Safe")
        ax3.axhline(y=0.3, color="red", linestyle="--", alpha=0.5, label="Critical")
        ax3.set_ylabel("Feasibility Score", fontsize=12)
        ax3.set_xlabel("Time", fontsize=12)
        ax3.grid(True, alpha=0.3)
        ax3.legend(loc="best")
        ax3.set_ylim(-0.05, 1.05)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            logger.info(f"Saved evolution plot to {output_path}")

        return fig

    def create_dashboard(
        self,
        surface: FeasibilitySurface,
        cusp_analysis: CuspAnalysis,
        trajectory: list[ParameterState],
        current_params: ParameterState,
        output_dir: str | Path,
    ):
        """
        Create comprehensive dashboard with all visualizations.

        Generates:
        - 3D surface plot
        - 2D contour map
        - Hysteresis loop
        - Parameter evolution

        Args:
            surface: FeasibilitySurface
            cusp_analysis: CuspAnalysis results
            trajectory: Historical trajectory
            current_params: Current system state
            output_dir: Directory to save all plots

        Returns:
            Dictionary of figure paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        figures = {}

        # 3D surface
        surface_path = output_dir / "catastrophe_surface_3d.png"
        self.plot_feasibility_surface_3d(
            surface,
            cusp_analysis=cusp_analysis,
            trajectory=trajectory,
            output_path=surface_path,
        )
        figures["surface_3d"] = str(surface_path)

        # 2D contour
        contour_path = output_dir / "catastrophe_contour_2d.png"
        self.plot_contour_map_2d(
            surface,
            cusp_analysis=cusp_analysis,
            trajectory=trajectory,
            current_params=current_params,
            output_path=contour_path,
        )
        figures["contour_2d"] = str(contour_path)

        # Hysteresis loop
        hysteresis_path = output_dir / "hysteresis_loop.png"
        self.plot_hysteresis_loop(
            surface, strictness_level=current_params.strictness, output_path=hysteresis_path
        )
        figures["hysteresis"] = str(hysteresis_path)

        # Parameter evolution
        evolution_path = output_dir / "parameter_evolution.png"
        self.plot_parameter_evolution(trajectory, output_path=evolution_path)
        figures["evolution"] = str(evolution_path)

        logger.info(f"Dashboard created in {output_dir}")
        return figures


# =============================================================================
# Convenience Functions
# =============================================================================


def visualize_catastrophe_surface(
    surface: FeasibilitySurface,
    cusp_analysis: CuspAnalysis | None = None,
    output_path: str | Path | None = None,
    style: str = "default",
) -> Any:
    """
    Quick function to visualize catastrophe surface.

    Args:
        surface: FeasibilitySurface to plot
        cusp_analysis: Optional cusp analysis
        output_path: Optional save path
        style: Plot style

    Returns:
        Figure object
    """
    viz = CatastropheVisualizer(style=style)
    return viz.plot_feasibility_surface_3d(
        surface, cusp_analysis=cusp_analysis, output_path=output_path
    )


def visualize_system_trajectory(
    surface: FeasibilitySurface,
    trajectory: list[ParameterState],
    cusp_analysis: CuspAnalysis | None = None,
    output_path: str | Path | None = None,
) -> Any:
    """
    Visualize system trajectory through parameter space.

    Args:
        surface: FeasibilitySurface
        trajectory: List of ParameterState
        cusp_analysis: Optional cusp analysis
        output_path: Optional save path

    Returns:
        Figure object
    """
    viz = CatastropheVisualizer()
    return viz.plot_contour_map_2d(
        surface, cusp_analysis=cusp_analysis, trajectory=trajectory, output_path=output_path
    )
