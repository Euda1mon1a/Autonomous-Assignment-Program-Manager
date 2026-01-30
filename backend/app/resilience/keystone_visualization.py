"""
Keystone Dependency Graph Visualization.

Generates visual representations of dependency networks to identify
keystone resources and cascade vulnerabilities.

Visualization types:
1. Dependency graph with keystone highlighting
2. Cascade flow diagram (trophic cascade visualization)
3. Redundancy heatmap (functional backup coverage)
4. Succession plan timeline

Uses NetworkX for graph layout and matplotlib/graphviz for rendering.
"""

import logging
from datetime import date
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)

try:
    import networkx as nx

    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logger.warning("NetworkX not available - graph visualization disabled")

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    logger.warning("matplotlib not available - graph visualization disabled")


class KeystoneVisualizer:
    """
    Visualizes keystone dependencies and cascades.

    Generates publication-quality diagrams showing:
    - Dependency networks with keystone highlighting
    - Cascade propagation animations
    - Functional redundancy matrices
    """

    def __init__(self) -> None:
        self.has_networkx = HAS_NETWORKX
        self.has_matplotlib = HAS_MATPLOTLIB

    def visualize_dependency_graph(
        self,
        graph: "nx.DiGraph",
        keystones: list,
        output_path: str | None = None,
        highlight_entity: UUID | None = None,
    ) -> str | None:
        """
        Visualize dependency graph with keystone highlighting.

        Args:
            graph: NetworkX dependency graph
            keystones: List of KeystoneResource objects
            output_path: Path to save visualization (PNG)
            highlight_entity: Optional entity to highlight for cascade view

        Returns:
            Path to saved image or None
        """
        if not self.has_networkx or not self.has_matplotlib:
            logger.warning("NetworkX and matplotlib required for visualization")
            return None

        if not graph:
            logger.warning("No graph provided for visualization")
            return None

            # Create figure
        fig, ax = plt.subplots(figsize=(16, 12))

        # Build keystone ID set for coloring
        keystone_ids = {str(k.entity_id) for k in keystones}

        # Node colors based on type and keystone status
        node_colors = []
        node_sizes = []

        for node in graph.nodes():
            node_data = graph.nodes[node]
            entity_type = node_data.get("type", "unknown")

            if node in keystone_ids:
                # Keystone - red
                node_colors.append("#FF4444")
                node_sizes.append(800)
            elif entity_type == "faculty":
                # Faculty - blue
                node_colors.append("#4444FF")
                node_sizes.append(500)
            elif entity_type == "resident":
                # Resident - green
                node_colors.append("#44FF44")
                node_sizes.append(500)
            elif entity_type == "service":
                # Service - orange
                node_colors.append("#FF8844")
                node_sizes.append(300)
            elif entity_type == "rotation":
                # Rotation - purple
                node_colors.append("#8844FF")
                node_sizes.append(300)
            else:
                # Unknown - gray
                node_colors.append("#888888")
                node_sizes.append(200)

                # Highlight specific entity if requested
        if highlight_entity:
            highlight_str = str(highlight_entity)
            if highlight_str in graph:
                idx = list(graph.nodes()).index(highlight_str)
                node_colors[idx] = "#FFFF00"  # Yellow
                node_sizes[idx] = 1000

                # Layout
        try:
            pos = nx.spring_layout(graph, k=2, iterations=50, seed=42)
        except Exception:
            pos = nx.circular_layout(graph)

            # Draw edges
        nx.draw_networkx_edges(
            graph,
            pos,
            edge_color="#CCCCCC",
            arrows=True,
            arrowsize=20,
            width=1.5,
            alpha=0.6,
            ax=ax,
        )

        # Draw nodes
        nx.draw_networkx_nodes(
            graph,
            pos,
            node_color=node_colors,
            node_size=node_sizes,
            alpha=0.9,
            ax=ax,
        )

        # Draw labels (only for keystones and highlighted entity)
        label_nodes = keystone_ids.copy()
        if highlight_entity:
            label_nodes.add(str(highlight_entity))

        labels = {}
        for node in label_nodes:
            if node in graph:
                node_data = graph.nodes[node]
                labels[node] = node_data.get("name", node)[:15]  # Truncate long names

        nx.draw_networkx_labels(
            graph,
            pos,
            labels=labels,
            font_size=8,
            font_weight="bold",
            ax=ax,
        )

        # Legend
        legend_elements = [
            mpatches.Patch(color="#FF4444", label="Keystone Resource"),
            mpatches.Patch(color="#4444FF", label="Faculty"),
            mpatches.Patch(color="#44FF44", label="Resident"),
            mpatches.Patch(color="#FF8844", label="Service"),
            mpatches.Patch(color="#8844FF", label="Rotation"),
        ]

        if highlight_entity:
            legend_elements.append(
                mpatches.Patch(color="#FFFF00", label="Cascade Origin")
            )

        ax.legend(handles=legend_elements, loc="upper left", fontsize=10)

        ax.set_title(
            "Keystone Dependency Graph\n"
            f"{len(keystones)} keystone resources identified",
            fontsize=16,
            fontweight="bold",
        )
        ax.axis("off")

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            logger.info(f"Saved dependency graph to {output_path}")
            plt.close()
            return output_path
        else:
            plt.show()
            return None

    def visualize_cascade(
        self,
        cascade_analysis,
        graph: "nx.DiGraph",
        output_path: str | None = None,
    ) -> str | None:
        """
        Visualize cascade propagation as multi-level diagram.

        Shows how removal of keystone triggers cascade through levels:
        Level 0: Keystone removed
        Level 1: Services lost
        Level 2: Rotations affected
        Level 3: Assignments failed

        Args:
            cascade_analysis: CascadeAnalysis object
            graph: Dependency graph
            output_path: Path to save visualization

        Returns:
            Path to saved image or None
        """
        if not self.has_matplotlib:
            logger.warning("matplotlib required for cascade visualization")
            return None

        fig, ax = plt.subplots(figsize=(14, 10))

        # Extract cascade levels from steps
        levels = []
        max_level = cascade_analysis.cascade_depth

        # Level 0: Origin
        levels.append(
            {
                "level": 0,
                "entities": [cascade_analysis.removed_entity_id],
                "label": f"Origin: {cascade_analysis.removed_entity_name}",
                "color": "#FF0000",
            }
        )

        # Subsequent levels from cascade steps
        for step in cascade_analysis.cascade_steps:
            level_num = step["level"]
            affected = step["affected_entities"]
            reason = step["reason"]

            levels.append(
                {
                    "level": level_num,
                    "entities": affected,
                    "label": f"Level {level_num}: {len(affected)} affected\n({reason[:40]}...)",
                    "color": f"#{255 - level_num * 40:02x}4444",
                }
            )

            # Draw cascade levels
        level_height = 0.8 / max(max_level, 1)

        for i, level_data in enumerate(levels):
            y_pos = 0.9 - (i * level_height)
            num_entities = len(level_data["entities"])

            # Draw box for level
            rect = mpatches.Rectangle(
                (0.1, y_pos - level_height * 0.8),
                0.8,
                level_height * 0.7,
                linewidth=2,
                edgecolor=level_data["color"],
                facecolor=level_data["color"],
                alpha=0.3,
            )
            ax.add_patch(rect)

            # Label
            ax.text(
                0.5,
                y_pos - level_height * 0.4,
                level_data["label"],
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold",
            )

            # Entity count
            ax.text(
                0.92,
                y_pos - level_height * 0.4,
                str(num_entities),
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold",
                bbox={"boxstyle": "circle", "facecolor": "white", "edgecolor": "black"},
            )

            # Draw arrows to next level
            if i < len(levels) - 1:
                next_y = y_pos - level_height
                ax.arrow(
                    0.5,
                    y_pos - level_height * 0.8,
                    0,
                    -level_height * 0.15,
                    head_width=0.05,
                    head_length=0.02,
                    fc="black",
                    ec="black",
                )

                # Summary statistics
        summary_text = (
            f"Total Affected: {cascade_analysis.total_affected}\n"
            f"Coverage Loss: {cascade_analysis.coverage_loss:.1%}\n"
            f"Cascade Depth: {cascade_analysis.cascade_depth} levels\n"
            f"Recovery Time: {cascade_analysis.recovery_time_days} days\n"
            f"Status: {'CATASTROPHIC' if cascade_analysis.is_catastrophic else 'Contained'}"
        )

        ax.text(
            0.5,
            0.05,
            summary_text,
            ha="center",
            va="center",
            fontsize=10,
            bbox={
                "boxstyle": "round",
                "facecolor": "lightyellow",
                "edgecolor": "black",
            },
        )

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

        ax.set_title(
            f"Cascade Analysis: {cascade_analysis.removed_entity_name}",
            fontsize=16,
            fontweight="bold",
        )

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            logger.info(f"Saved cascade visualization to {output_path}")
            plt.close()
            return output_path
        else:
            plt.show()
            return None

    def visualize_redundancy_matrix(
        self,
        keystones: list,
        services: dict[UUID, list[UUID]],
        output_path: str | None = None,
    ) -> str | None:
        """
        Visualize functional redundancy as heatmap.

        Rows: Keystone resources
        Columns: Services
        Cell color: How many alternatives exist for that service

        Args:
            keystones: List of KeystoneResource objects
            services: Service capability mapping
            output_path: Path to save visualization

        Returns:
            Path to saved image or None
        """
        if not self.has_matplotlib:
            logger.warning("matplotlib required for redundancy matrix")
            return None

        import numpy as np

        # Build matrix
        num_keystones = len(keystones)
        num_services = len(services)

        if num_keystones == 0 or num_services == 0:
            logger.warning("No keystones or services to visualize")
            return None

        matrix = np.zeros((num_keystones, num_services))
        service_list = list(services.keys())

        for i, keystone in enumerate(keystones):
            for j, service_id in enumerate(service_list):
                providers = services.get(service_id, [])
                if keystone.entity_id in providers:
                    # Count alternatives (exclude keystone itself)
                    alternatives = len(
                        [p for p in providers if p != keystone.entity_id]
                    )
                    matrix[i, j] = alternatives

                    # Create heatmap
        fig, ax = plt.subplots(figsize=(14, max(8, num_keystones * 0.5)))

        im = ax.imshow(matrix, cmap="RdYlGn", aspect="auto", vmin=0, vmax=5)

        # Labels
        ax.set_xticks(range(num_services))
        ax.set_yticks(range(num_keystones))

        service_labels = [f"Svc-{i + 1}" for i in range(num_services)]
        keystone_labels = [k.entity_name[:20] for k in keystones]

        ax.set_xticklabels(service_labels, rotation=45, ha="right", fontsize=8)
        ax.set_yticklabels(keystone_labels, fontsize=9)

        # Colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label("Number of Alternative Providers", rotation=270, labelpad=20)

        # Add text annotations for zero redundancy (critical)
        for i in range(num_keystones):
            for j in range(num_services):
                if matrix[i, j] == 0 and service_list[j] in [
                    UUID(s) for s in keystones[i].unique_capabilities
                ]:
                    ax.text(
                        j,
                        i,
                        "!",
                        ha="center",
                        va="center",
                        color="red",
                        fontsize=14,
                        fontweight="bold",
                    )

        ax.set_title(
            "Functional Redundancy Matrix\n"
            "Red = Single Point of Failure, Green = High Redundancy",
            fontsize=14,
            fontweight="bold",
        )
        ax.set_xlabel("Services", fontsize=12)
        ax.set_ylabel("Keystone Resources", fontsize=12)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            logger.info(f"Saved redundancy matrix to {output_path}")
            plt.close()
            return output_path
        else:
            plt.show()
            return None

    def visualize_succession_timeline(
        self,
        succession_plans: list,
        output_path: str | None = None,
    ) -> str | None:
        """
        Visualize succession plan timelines as Gantt chart.

        Args:
            succession_plans: List of SuccessionPlan objects
            output_path: Path to save visualization

        Returns:
            Path to saved image or None
        """
        if not self.has_matplotlib:
            logger.warning("matplotlib required for timeline visualization")
            return None

        if not succession_plans:
            logger.warning("No succession plans to visualize")
            return None

        fig, ax = plt.subplots(figsize=(14, max(6, len(succession_plans) * 0.8)))

        # Find date range
        all_dates = []
        for plan in succession_plans:
            for milestone_date in plan.timeline.values():
                if isinstance(milestone_date, date):
                    all_dates.append(milestone_date)

        if not all_dates:
            logger.warning("No timeline dates in succession plans")
            return None

        min_date = min(all_dates)
        max_date = max(all_dates)
        date_range = (max_date - min_date).days + 1

        # Draw timeline bars
        for i, plan in enumerate(succession_plans):
            start_date = plan.timeline.get("training_start")
            end_date = plan.timeline.get("training_complete")

            if not start_date or not end_date:
                continue

                # Calculate bar position
            start_offset = (start_date - min_date).days
            duration = (end_date - start_date).days

            # Color by priority
            color_map = {
                "urgent": "#FF4444",
                "high": "#FF8844",
                "medium": "#FFBB44",
                "low": "#88FF88",
            }
            color = color_map.get(plan.training_priority, "#CCCCCC")

            # Draw bar
            ax.barh(
                i,
                duration,
                left=start_offset,
                height=0.6,
                color=color,
                alpha=0.7,
                edgecolor="black",
            )

            # Label
            label = (
                f"{plan.keystone_entity_name[:20]}\n({plan.estimated_training_hours}h)"
            )
            ax.text(
                -5,
                i,
                label,
                ha="right",
                va="center",
                fontsize=8,
            )

            # Milestones
            for milestone, milestone_date in plan.timeline.items():
                if isinstance(milestone_date, date):
                    offset = (milestone_date - min_date).days
                    ax.plot(
                        offset,
                        i,
                        marker="D",
                        markersize=8,
                        color="black",
                    )

                    # X-axis: dates
        ax.set_xlim(-10, date_range + 10)
        ax.set_ylim(-0.5, len(succession_plans) - 0.5)

        # Date labels (monthly)
        num_months = max(1, date_range // 30)
        tick_positions = [i * (date_range / num_months) for i in range(num_months + 1)]
        tick_labels = [
            (min_date + __import__("datetime").timedelta(days=int(pos))).strftime(
                "%b %Y"
            )
            for pos in tick_positions
        ]
        ax.set_xticks(tick_positions)
        ax.set_xticklabels(tick_labels, rotation=45, ha="right")

        ax.set_yticks([])
        ax.set_xlabel("Timeline", fontsize=12)
        ax.set_title(
            f"Succession Plan Timeline\n{len(succession_plans)} plans scheduled",
            fontsize=14,
            fontweight="bold",
        )

        # Legend
        legend_elements = [
            mpatches.Patch(color="#FF4444", label="Urgent Priority"),
            mpatches.Patch(color="#FF8844", label="High Priority"),
            mpatches.Patch(color="#FFBB44", label="Medium Priority"),
            mpatches.Patch(color="#88FF88", label="Low Priority"),
        ]
        ax.legend(handles=legend_elements, loc="upper right")

        ax.grid(axis="x", alpha=0.3)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            logger.info(f"Saved succession timeline to {output_path}")
            plt.close()
            return output_path
        else:
            plt.show()
            return None

    def export_to_graphviz(
        self,
        graph: "nx.DiGraph",
        keystones: list,
        output_path: str,
    ) -> str | None:
        """
        Export dependency graph to Graphviz DOT format.

        Useful for high-quality publication diagrams.

        Args:
            graph: NetworkX dependency graph
            keystones: List of KeystoneResource objects
            output_path: Path to save .dot file

        Returns:
            Path to saved file or None
        """
        if not self.has_networkx:
            logger.warning("NetworkX required for Graphviz export")
            return None

        try:
            from networkx.drawing.nx_pydot import write_dot

            # Add visual attributes to graph
            keystone_ids = {str(k.entity_id) for k in keystones}

            for node in graph.nodes():
                if node in keystone_ids:
                    graph.nodes[node]["color"] = "red"
                    graph.nodes[node]["style"] = "filled"
                    graph.nodes[node]["fillcolor"] = "lightcoral"
                else:
                    node_type = graph.nodes[node].get("type", "unknown")
                    type_colors = {
                        "faculty": "lightblue",
                        "resident": "lightgreen",
                        "service": "lightyellow",
                        "rotation": "plum",
                    }
                    graph.nodes[node]["fillcolor"] = type_colors.get(
                        node_type, "lightgray"
                    )
                    graph.nodes[node]["style"] = "filled"

            write_dot(graph, output_path)
            logger.info(f"Exported graph to Graphviz DOT: {output_path}")
            return output_path

        except ImportError:
            logger.error("pydot required for Graphviz export")
            return None
        except Exception as e:
            logger.error(f"Failed to export to Graphviz: {e}")
            return None
