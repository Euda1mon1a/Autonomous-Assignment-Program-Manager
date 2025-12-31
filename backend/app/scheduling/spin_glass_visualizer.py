"""
Visualization helpers for Spin Glass energy landscape analysis.

Provides functions to visualize:
- Energy landscapes across replica schedules
- Parisi overlap matrices (RSB structure)
- Frustration cluster diagrams
- Solution basin hierarchies
"""

import logging
from typing import Any

import numpy as np

from app.scheduling.spin_glass_model import (
    LandscapeAnalysis,
    ReplicaSchedule,
    ReplicaSymmetryAnalysis,
)

logger = logging.getLogger(__name__)

# Optional visualization dependencies
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.figure import Figure

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not available - visualization disabled")

try:
    import seaborn as sns

    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False
    logger.warning("seaborn not available - enhanced visualization disabled")


def plot_energy_landscape(
    replicas: list[ReplicaSchedule],
    landscape: LandscapeAnalysis,
    output_path: str | None = None,
) -> Figure | None:
    """
    Plot energy landscape showing replica energies and basin structure.

    Creates a scatter plot of replica energies vs replica index, highlighting
    different solution basins and energy barriers.

    Args:
        replicas: List of replica schedules
        landscape: Landscape analysis results
        output_path: Optional path to save figure (PNG format)

    Returns:
        Matplotlib Figure object if matplotlib available, None otherwise

    Example:
        >>> fig = plot_energy_landscape(replicas, landscape, "energy_landscape.png")
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("matplotlib not available - cannot plot energy landscape")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    # Extract energies
    indices = [r.replica_index for r in replicas]
    energies = [r.energy for r in replicas]

    # Color by basin (if basin info available)
    if landscape.basin_sizes:
        # Assign colors to basins
        basin_colors = plt.cm.tab10(np.linspace(0, 1, len(landscape.basin_sizes)))
        colors = []
        basin_assignments = _assign_replicas_to_basins(replicas, landscape)

        for i in range(len(replicas)):
            basin_id = basin_assignments.get(i, 0)
            colors.append(basin_colors[basin_id % len(basin_colors)])
    else:
        colors = "blue"

    # Scatter plot
    ax.scatter(indices, energies, c=colors, alpha=0.6, s=50)

    # Mark global minimum
    min_idx = np.argmin(energies)
    ax.scatter(
        [indices[min_idx]],
        [energies[min_idx]],
        c="red",
        marker="*",
        s=300,
        label="Global Minimum",
        zorder=10,
    )

    # Mark local minima
    if landscape.local_minima:
        for local_min in landscape.local_minima:
            ax.axhline(
                y=local_min,
                color="orange",
                linestyle="--",
                alpha=0.5,
                linewidth=1,
            )

    ax.set_xlabel("Replica Index", fontsize=12)
    ax.set_ylabel("Energy (Constraint Violations)", fontsize=12)
    ax.set_title("Spin Glass Energy Landscape", fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.legend()

    # Add info text
    info_text = (
        f"Replicas: {len(replicas)}\n"
        f"Basins: {len(landscape.basin_sizes)}\n"
        f"E_min: {landscape.global_minimum_energy:.2f}\n"
        f"T_g: {landscape.glass_transition_temp:.3f}"
    )
    ax.text(
        0.02,
        0.98,
        info_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.5},
    )

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        logger.info(f"Energy landscape plot saved to {output_path}")

    return fig


def plot_parisi_overlap_matrix(
    rsb_analysis: ReplicaSymmetryAnalysis,
    output_path: str | None = None,
) -> Figure | None:
    """
    Plot Parisi overlap matrix as a heatmap.

    The overlap matrix shows similarity between all pairs of replicas.
    Structure in this matrix reveals replica symmetry breaking (RSB).

    Args:
        rsb_analysis: RSB analysis containing overlap matrix
        output_path: Optional path to save figure (PNG format)

    Returns:
        Matplotlib Figure object if matplotlib available, None otherwise

    Example:
        >>> fig = plot_parisi_overlap_matrix(rsb_analysis, "overlap_matrix.png")
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("matplotlib not available - cannot plot overlap matrix")
        return None

    overlap_matrix = rsb_analysis.parisi_overlap_matrix

    if overlap_matrix.size == 0:
        logger.warning("Empty overlap matrix - cannot plot")
        return None

    fig, ax = plt.subplots(figsize=(10, 8))

    # Use seaborn if available for nicer heatmap
    if SEABORN_AVAILABLE:
        sns.heatmap(
            overlap_matrix,
            cmap="RdYlGn",
            vmin=0.0,
            vmax=1.0,
            square=True,
            cbar_kws={"label": "Parisi Overlap"},
            ax=ax,
        )
    else:
        im = ax.imshow(overlap_matrix, cmap="RdYlGn", vmin=0.0, vmax=1.0, aspect="auto")
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label("Parisi Overlap", fontsize=12)

    ax.set_xlabel("Replica Index", fontsize=12)
    ax.set_ylabel("Replica Index", fontsize=12)
    ax.set_title(
        "Parisi Overlap Matrix (RSB Structure)", fontsize=14, fontweight="bold"
    )

    # Add info text
    info_text = (
        f"RSB Parameter: {rsb_analysis.rsb_order_parameter:.3f}\n"
        f"Diversity: {rsb_analysis.diversity_score:.3f}\n"
        f"Mean Overlap: {rsb_analysis.mean_overlap:.3f}"
    )
    fig.text(
        0.02,
        0.98,
        info_text,
        fontsize=10,
        verticalalignment="top",
        bbox={"boxstyle": "round", "facecolor": "lightblue", "alpha": 0.8},
    )

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        logger.info(f"Overlap matrix plot saved to {output_path}")

    return fig


def plot_overlap_distribution(
    rsb_analysis: ReplicaSymmetryAnalysis,
    output_path: str | None = None,
) -> Figure | None:
    """
    Plot histogram of overlap values.

    Shows the distribution of pairwise overlaps between replicas.
    - Peaked near 1.0: Replica symmetry (few solutions)
    - Broad distribution: Replica symmetry breaking (many solutions)

    Args:
        rsb_analysis: RSB analysis containing overlap distribution
        output_path: Optional path to save figure (PNG format)

    Returns:
        Matplotlib Figure object if matplotlib available, None otherwise
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("matplotlib not available - cannot plot distribution")
        return None

    overlap_dist = rsb_analysis.overlap_distribution

    if not overlap_dist:
        logger.warning("No overlap distribution data - cannot plot")
        return None

    fig, ax = plt.subplots(figsize=(8, 6))

    # Extract bin centers and counts
    bins = ["0.00-0.25", "0.25-0.50", "0.50-0.75", "0.75-1.00"]
    counts = [overlap_dist.get(b, 0) for b in bins]

    # Bar plot
    colors = ["red", "orange", "yellow", "green"]
    ax.bar(bins, counts, color=colors, alpha=0.7, edgecolor="black")

    ax.set_xlabel("Overlap Range", fontsize=12)
    ax.set_ylabel("Number of Replica Pairs", fontsize=12)
    ax.set_title("Parisi Overlap Distribution", fontsize=14, fontweight="bold")
    ax.grid(True, axis="y", alpha=0.3)

    # Add info text
    total_pairs = sum(counts)
    info_text = (
        f"Total Pairs: {total_pairs}\nDiversity: {rsb_analysis.diversity_score:.3f}"
    )
    ax.text(
        0.98,
        0.98,
        info_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        horizontalalignment="right",
        bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.5},
    )

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        logger.info(f"Overlap distribution plot saved to {output_path}")

    return fig


def plot_frustration_network(
    landscape: LandscapeAnalysis,
    output_path: str | None = None,
) -> Figure | None:
    """
    Plot frustration clusters as a network diagram.

    Shows which constraints conflict with each other (antiferromagnetic bonds).

    Args:
        landscape: Landscape analysis with frustration clusters
        output_path: Optional path to save figure (PNG format)

    Returns:
        Matplotlib Figure object if matplotlib available, None otherwise

    Note:
        This is a simplified visualization. For complex networks, consider
        using networkx with specialized graph layout algorithms.
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("matplotlib not available - cannot plot frustration network")
        return None

    frustration_clusters = landscape.frustration_clusters

    if not frustration_clusters:
        logger.info("No frustration clusters to plot")
        return None

    fig, ax = plt.subplots(figsize=(10, 8))

    # Extract constraint names from clusters
    all_constraints = set()
    edges = []

    for cluster in frustration_clusters:
        constraints = cluster.constraints
        all_constraints.update(constraints)

        # Create edges between conflicting constraints
        for i, c1 in enumerate(constraints):
            for c2 in constraints[i + 1 :]:
                edges.append((c1, c2, cluster.frustration_index))

    # Simple circular layout
    n = len(all_constraints)
    constraint_list = list(all_constraints)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    positions = {
        constraint_list[i]: (np.cos(angles[i]), np.sin(angles[i])) for i in range(n)
    }

    # Draw nodes
    for constraint, (x, y) in positions.items():
        ax.scatter(
            [x], [y], s=500, c="lightblue", edgecolor="black", linewidth=2, zorder=3
        )
        ax.text(
            x,
            y,
            constraint[:15],
            fontsize=8,
            ha="center",
            va="center",
            zorder=4,
        )

    # Draw edges (frustration bonds)
    for c1, c2, frustration in edges:
        x1, y1 = positions[c1]
        x2, y2 = positions[c2]

        # Line width proportional to frustration
        linewidth = 1 + 3 * frustration
        ax.plot([x1, x2], [y1, y2], "r-", linewidth=linewidth, alpha=0.6, zorder=1)

    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Constraint Frustration Network", fontsize=14, fontweight="bold")

    # Legend
    red_patch = mpatches.Patch(color="red", label="Conflicting Constraints")
    ax.legend(handles=[red_patch], loc="upper right")

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        logger.info(f"Frustration network plot saved to {output_path}")

    return fig


def plot_solution_basins(
    replicas: list[ReplicaSchedule],
    landscape: LandscapeAnalysis,
    output_path: str | None = None,
) -> Figure | None:
    """
    Plot solution basins using 2D projection.

    Projects high-dimensional schedule space into 2D using energy and
    magnetization, coloring by basin membership.

    Args:
        replicas: List of replica schedules
        landscape: Landscape analysis with basin information
        output_path: Optional path to save figure (PNG format)

    Returns:
        Matplotlib Figure object if matplotlib available, None otherwise
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("matplotlib not available - cannot plot solution basins")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    # Extract coordinates
    energies = [r.energy for r in replicas]
    magnetizations = [r.magnetization for r in replicas]

    # Assign colors by basin
    basin_assignments = _assign_replicas_to_basins(replicas, landscape)
    n_basins = len(landscape.basin_sizes)

    if n_basins > 0:
        colors = plt.cm.tab10(np.linspace(0, 1, n_basins))
        replica_colors = [
            colors[basin_assignments.get(i, 0) % len(colors)]
            for i in range(len(replicas))
        ]
    else:
        replica_colors = "blue"

    # Scatter plot
    ax.scatter(
        magnetizations, energies, c=replica_colors, alpha=0.6, s=50, edgecolor="black"
    )

    ax.set_xlabel("Magnetization (Soft Constraint Alignment)", fontsize=12)
    ax.set_ylabel("Energy (Total Violations)", fontsize=12)
    ax.set_title("Solution Basins (2D Projection)", fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3)

    # Add info text
    info_text = f"Basins: {n_basins}\nReplicas: {len(replicas)}"
    ax.text(
        0.02,
        0.98,
        info_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.5},
    )

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        logger.info(f"Solution basins plot saved to {output_path}")

    return fig


def export_landscape_summary(
    replicas: list[ReplicaSchedule],
    landscape: LandscapeAnalysis,
    rsb_analysis: ReplicaSymmetryAnalysis,
    output_path: str,
) -> None:
    """
    Export comprehensive landscape summary as JSON.

    Args:
        replicas: List of replica schedules
        landscape: Landscape analysis
        rsb_analysis: RSB analysis
        output_path: Path to save JSON file
    """
    import json

    summary = {
        "n_replicas": len(replicas),
        "energy_statistics": {
            "global_minimum": landscape.global_minimum_energy,
            "local_minima": landscape.local_minima,
            "mean_energy": float(np.mean([r.energy for r in replicas])),
            "std_energy": float(np.std([r.energy for r in replicas])),
        },
        "basin_structure": {
            "n_basins": len(landscape.basin_sizes),
            "basin_sizes": {str(k): v for k, v in landscape.basin_sizes.items()},
            "energy_barriers": landscape.energy_barrier_heights,
        },
        "replica_symmetry_breaking": {
            "rsb_parameter": rsb_analysis.rsb_order_parameter,
            "diversity_score": rsb_analysis.diversity_score,
            "mean_overlap": rsb_analysis.mean_overlap,
            "overlap_distribution": rsb_analysis.overlap_distribution,
        },
        "frustration": {
            "n_clusters": len(landscape.frustration_clusters),
            "clusters": [
                {
                    "constraints": c.constraints,
                    "frustration_index": c.frustration_index,
                    "conflict_type": c.conflict_type,
                }
                for c in landscape.frustration_clusters
            ],
        },
        "glass_transition": {"temperature": landscape.glass_transition_temp},
    }

    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Landscape summary exported to {output_path}")


# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------


def _assign_replicas_to_basins(
    replicas: list[ReplicaSchedule],
    landscape: LandscapeAnalysis,
) -> dict[int, int]:
    """
    Assign each replica to its basin.

    Returns:
        Dictionary mapping replica_index -> basin_id
    """
    replica_to_basin: dict[int, int] = {}

    for basin_id, replica_indices in landscape.basin_sizes.items():
        # Note: basin_sizes stores (basin_id -> count), not (basin_id -> indices)
        # For proper implementation, would need to store basin membership in LandscapeAnalysis
        # For now, use simple heuristic based on energy proximity
        pass

    # Fallback: assign all to basin 0
    for i in range(len(replicas)):
        replica_to_basin[i] = 0

    return replica_to_basin
