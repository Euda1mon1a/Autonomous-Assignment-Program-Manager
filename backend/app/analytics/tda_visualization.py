"""
TDA Visualization Helpers.

Provides visualization utilities for persistent homology results:
- Persistence diagrams (birth-death plots)
- Persistence barcodes (feature lifetimes)
- Point cloud visualizations
- Bottleneck distance matching
"""

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Try to import plotting libraries
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    logger.warning(
        "plotly not installed - TDA visualizations will return mock data. "
        "Install with: pip install plotly"
    )

try:
    from persim import plot_diagrams

    HAS_PERSIM = True
except ImportError:
    HAS_PERSIM = False


class BarcodeVisualization:
    """
    Persistence barcode visualization generator.

    Barcodes show feature lifetimes as horizontal bars. Longer bars indicate
    more persistent (significant) features.
    """

    def __init__(self):
        """Initialize barcode visualizer."""
        self.colors = {
            0: "rgb(31, 119, 180)",  # Blue for H0
            1: "rgb(255, 127, 14)",  # Orange for H1
            2: "rgb(44, 160, 44)",  # Green for H2
        }

    def create_barcode(
        self, diagram: Any, title: str = "Persistence Barcode"
    ) -> dict[str, Any] | None:
        """
        Create a persistence barcode plot.

        Args:
            diagram: PersistenceDiagram object
            title: Plot title

        Returns:
            Plotly figure dictionary or None if plotly unavailable
        """
        if not HAS_PLOTLY:
            logger.warning("Plotly not available - cannot create barcode")
            return None

        fig = go.Figure()

        # Collect all features across dimensions
        all_features = []
        for dim in [0, 1, 2]:
            features = diagram.get_features_by_dimension(dim)
            for feature in features:
                all_features.append((dim, feature))

        if not all_features:
            logger.info("No features to plot")
            return None

        # Sort by dimension and then by birth time
        all_features.sort(key=lambda x: (x[0], x[1].birth))

        # Create barcode bars
        for idx, (dim, feature) in enumerate(all_features):
            # Horizontal bar from birth to death
            fig.add_trace(
                go.Scatter(
                    x=[feature.birth, feature.death],
                    y=[idx, idx],
                    mode="lines",
                    line=dict(
                        color=self.colors[dim],
                        width=3 if feature.is_significant else 1,
                    ),
                    name=f"H{dim}",
                    showlegend=False,
                    hovertemplate=(
                        f"<b>H{dim} Feature</b><br>"
                        f"Birth: {feature.birth:.3f}<br>"
                        f"Death: {feature.death:.3f}<br>"
                        f"Persistence: {feature.persistence:.3f}<br>"
                        f"{feature.interpretation}"
                        "<extra></extra>"
                    ),
                )
            )

        # Add legend manually for dimensions
        for dim, color in self.colors.items():
            fig.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None],
                    mode="lines",
                    line=dict(color=color, width=3),
                    name=f"H{dim}",
                    showlegend=True,
                )
            )

        fig.update_layout(
            title=title,
            xaxis_title="Filtration Parameter",
            yaxis_title="Feature Index",
            yaxis=dict(showticklabels=False),
            hovermode="closest",
            template="plotly_white",
        )

        return fig.to_dict()

    def create_persistence_diagram(
        self, diagram: Any, title: str = "Persistence Diagram"
    ) -> dict[str, Any] | None:
        """
        Create a persistence diagram (birth-death plot).

        Points far from the diagonal represent significant features.

        Args:
            diagram: PersistenceDiagram object
            title: Plot title

        Returns:
            Plotly figure dictionary or None if unavailable
        """
        if not HAS_PLOTLY:
            logger.warning("Plotly not available - cannot create diagram")
            return None

        fig = go.Figure()

        # Add diagonal line (birth = death)
        max_val = 0.0

        # Plot features by dimension
        for dim in [0, 1, 2]:
            features = diagram.get_features_by_dimension(dim)

            if not features:
                continue

            births = [f.birth for f in features]
            deaths = [f.death for f in features]
            max_val = max(max_val, max(deaths))

            # Separate significant and insignificant features
            sig_features = [f for f in features if f.is_significant]
            insig_features = [f for f in features if not f.is_significant]

            # Plot significant features (larger markers)
            if sig_features:
                fig.add_trace(
                    go.Scatter(
                        x=[f.birth for f in sig_features],
                        y=[f.death for f in sig_features],
                        mode="markers",
                        marker=dict(
                            color=self.colors[dim],
                            size=10,
                            line=dict(color="white", width=1),
                        ),
                        name=f"H{dim} (significant)",
                        hovertemplate=(
                            f"<b>H{dim} Feature</b><br>"
                            "Birth: %{x:.3f}<br>"
                            "Death: %{y:.3f}<br>"
                            "Persistence: %{customdata:.3f}"
                            "<extra></extra>"
                        ),
                        customdata=[f.persistence for f in sig_features],
                    )
                )

            # Plot insignificant features (smaller markers)
            if insig_features:
                fig.add_trace(
                    go.Scatter(
                        x=[f.birth for f in insig_features],
                        y=[f.death for f in insig_features],
                        mode="markers",
                        marker=dict(
                            color=self.colors[dim],
                            size=5,
                            opacity=0.5,
                        ),
                        name=f"H{dim} (weak)",
                        hovertemplate=(
                            f"<b>H{dim} Feature</b><br>"
                            "Birth: %{x:.3f}<br>"
                            "Death: %{y:.3f}<br>"
                            "Persistence: %{customdata:.3f}"
                            "<extra></extra>"
                        ),
                        customdata=[f.persistence for f in insig_features],
                    )
                )

        # Add diagonal line
        fig.add_trace(
            go.Scatter(
                x=[0, max_val * 1.1],
                y=[0, max_val * 1.1],
                mode="lines",
                line=dict(color="gray", dash="dash"),
                name="Birth = Death",
                showlegend=False,
                hoverinfo="skip",
            )
        )

        fig.update_layout(
            title=title,
            xaxis_title="Birth",
            yaxis_title="Death",
            template="plotly_white",
            hovermode="closest",
            xaxis=dict(range=[0, max_val * 1.1]),
            yaxis=dict(range=[0, max_val * 1.1]),
        )

        return fig.to_dict()

    def create_combined_view(self, diagram: Any) -> dict[str, Any] | None:
        """
        Create a combined view with both barcode and persistence diagram.

        Args:
            diagram: PersistenceDiagram object

        Returns:
            Plotly figure dictionary with subplots
        """
        if not HAS_PLOTLY:
            return None

        # Create subplots
        fig = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=("Persistence Diagram", "Persistence Barcode"),
            horizontal_spacing=0.12,
        )

        # Add persistence diagram to left subplot
        max_val = 0.0
        for dim in [0, 1, 2]:
            features = diagram.get_features_by_dimension(dim)
            if not features:
                continue

            deaths = [f.death for f in features]
            max_val = max(max_val, max(deaths))

            sig_features = [f for f in features if f.is_significant]

            if sig_features:
                fig.add_trace(
                    go.Scatter(
                        x=[f.birth for f in sig_features],
                        y=[f.death for f in sig_features],
                        mode="markers",
                        marker=dict(color=self.colors[dim], size=8),
                        name=f"H{dim}",
                        legendgroup=f"h{dim}",
                    ),
                    row=1,
                    col=1,
                )

        # Add diagonal to persistence diagram
        fig.add_trace(
            go.Scatter(
                x=[0, max_val * 1.1],
                y=[0, max_val * 1.1],
                mode="lines",
                line=dict(color="gray", dash="dash"),
                showlegend=False,
            ),
            row=1,
            col=1,
        )

        # Add barcode to right subplot
        all_features = []
        for dim in [0, 1, 2]:
            features = diagram.get_features_by_dimension(dim)
            for feature in features:
                all_features.append((dim, feature))

        all_features.sort(key=lambda x: (x[0], x[1].birth))

        for idx, (dim, feature) in enumerate(all_features):
            fig.add_trace(
                go.Scatter(
                    x=[feature.birth, feature.death],
                    y=[idx, idx],
                    mode="lines",
                    line=dict(color=self.colors[dim], width=3),
                    showlegend=False,
                    legendgroup=f"h{dim}",
                ),
                row=1,
                col=2,
            )

        fig.update_xaxes(title_text="Birth", row=1, col=1)
        fig.update_yaxes(title_text="Death", row=1, col=1)
        fig.update_xaxes(title_text="Filtration", row=1, col=2)
        fig.update_yaxes(showticklabels=False, row=1, col=2)

        fig.update_layout(
            title_text="Topological Data Analysis - Persistence",
            template="plotly_white",
        )

        return fig.to_dict()


def visualize_point_cloud(
    point_cloud: np.ndarray,
    labels: list[str] | None = None,
    title: str = "Schedule Point Cloud",
) -> dict[str, Any] | None:
    """
    Visualize a point cloud in 2D or 3D.

    Args:
        point_cloud: Point cloud array (n_points, 2 or 3)
        labels: Optional labels for points
        title: Plot title

    Returns:
        Plotly figure dictionary or None if unavailable
    """
    if not HAS_PLOTLY:
        logger.warning("Plotly not available - cannot visualize point cloud")
        return None

    n_dims = point_cloud.shape[1]

    if n_dims == 2:
        # 2D scatter plot
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=point_cloud[:, 0],
                y=point_cloud[:, 1],
                mode="markers",
                marker=dict(
                    size=8,
                    color=np.arange(len(point_cloud)),
                    colorscale="Viridis",
                    showscale=True,
                ),
                text=labels if labels else None,
                hovertemplate="<b>Point %{pointNumber}</b><br>"
                "X: %{x:.3f}<br>"
                "Y: %{y:.3f}<br>"
                "%{text}"
                "<extra></extra>",
            )
        )

        fig.update_layout(
            title=title,
            xaxis_title="Component 1",
            yaxis_title="Component 2",
            template="plotly_white",
        )

    elif n_dims >= 3:
        # 3D scatter plot
        fig = go.Figure()

        fig.add_trace(
            go.Scatter3d(
                x=point_cloud[:, 0],
                y=point_cloud[:, 1],
                z=point_cloud[:, 2],
                mode="markers",
                marker=dict(
                    size=5,
                    color=np.arange(len(point_cloud)),
                    colorscale="Viridis",
                    showscale=True,
                ),
                text=labels if labels else None,
                hovertemplate="<b>Point %{pointNumber}</b><br>"
                "X: %{x:.3f}<br>"
                "Y: %{y:.3f}<br>"
                "Z: %{z:.3f}<br>"
                "%{text}"
                "<extra></extra>",
            )
        )

        fig.update_layout(
            title=title,
            scene=dict(
                xaxis_title="Component 1",
                yaxis_title="Component 2",
                zaxis_title="Component 3",
            ),
            template="plotly_white",
        )
    else:
        logger.warning(f"Cannot visualize {n_dims}D point cloud")
        return None

    return fig.to_dict()


def create_tda_summary_report(analysis_result: dict[str, Any]) -> dict[str, Any]:
    """
    Create a summary report from TDA analysis results.

    Args:
        analysis_result: Output from PersistentScheduleAnalyzer.analyze_schedule()

    Returns:
        Formatted summary report dictionary
    """
    report = {
        "title": "Topological Data Analysis - Schedule Structure Report",
        "generated_at": analysis_result.get("computed_at"),
        "overview": {
            "total_assignments": analysis_result.get("total_assignments", 0),
            "embedding_dimensions": (
                analysis_result.get("point_cloud_shape", [0, 0])[1]
            ),
            "anomaly_score": analysis_result.get("anomaly_score", 0.0),
        },
        "topological_features": analysis_result.get("persistence_diagram", {}),
        "findings": [],
        "recommendations": [],
    }

    # Generate findings based on results
    anomaly_score = analysis_result.get("anomaly_score", 0.0)

    if anomaly_score < 0.3:
        report["findings"].append(
            "Schedule structure is topologically normal - no significant anomalies detected."
        )
    elif anomaly_score < 0.6:
        report["findings"].append(
            "Moderate topological anomalies detected - review coverage voids and cyclic patterns."
        )
    else:
        report["findings"].append(
            "High topological anomaly score - significant structural issues detected."
        )

    # Coverage voids
    voids = analysis_result.get("coverage_voids", [])
    if voids:
        report["findings"].append(
            f"Found {len(voids)} coverage voids (gaps in schedule structure)."
        )
        high_severity_voids = [v for v in voids if v["severity"] > 0.7]
        if high_severity_voids:
            report["recommendations"].append(
                f"Address {len(high_severity_voids)} high-severity coverage voids immediately."
            )

    # Cyclic patterns
    cycles = analysis_result.get("cyclic_patterns", [])
    if cycles:
        report["findings"].append(f"Detected {len(cycles)} cyclic rotation patterns.")
        strong_cycles = [c for c in cycles if c["strength"] > 0.7]
        if strong_cycles:
            report["recommendations"].append(
                f"Leverage {len(strong_cycles)} strong cyclic patterns for predictability."
            )
    else:
        report["recommendations"].append(
            "No cyclic patterns detected - consider establishing regular rotation cycles."
        )

    # Feature counts
    h0 = analysis_result.get("persistence_diagram", {}).get("h0_features", 0)
    h1 = analysis_result.get("persistence_diagram", {}).get("h1_features", 0)
    h2 = analysis_result.get("persistence_diagram", {}).get("h2_features", 0)

    report["findings"].append(
        f"Topological summary: {h0} connected components (H0), "
        f"{h1} loops (H1), {h2} voids (H2)."
    )

    return report
