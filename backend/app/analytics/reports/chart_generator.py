"""Chart Generator - Generates charts for reports."""

from typing import Any, Dict, List
import logging
import base64
from io import BytesIO

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generates charts for reports."""

    def generate_line_chart(self, data: dict[str, list[float]], title: str = "") -> str:
        """Generate line chart (returns base64 encoded image or SVG)."""
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            plt.figure(figsize=(10, 6))
            for label, values in data.items():
                plt.plot(values, label=label)

            plt.title(title)
            plt.legend()
            plt.grid(True)

            buffer = BytesIO()
            plt.savefig(buffer, format="png", bbox_inches="tight")
            plt.close()

            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            return f"data:image/png;base64,{image_base64}"

        except ImportError:
            logger.warning("matplotlib not available, using SVG fallback")
            return self._generate_line_chart_svg(data, title)

    def generate_bar_chart(
        self, categories: list[str], values: list[float], title: str = ""
    ) -> str:
        """Generate bar chart (returns base64 encoded image or SVG)."""
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            plt.figure(figsize=(10, 6))
            plt.bar(categories, values)
            plt.title(title)
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()

            buffer = BytesIO()
            plt.savefig(buffer, format="png", bbox_inches="tight")
            plt.close()

            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            return f"data:image/png;base64,{image_base64}"

        except ImportError:
            logger.warning("matplotlib not available, using SVG fallback")
            return self._generate_bar_chart_svg(categories, values, title)

    def generate_pie_chart(
        self, labels: list[str], values: list[float], title: str = ""
    ) -> str:
        """Generate pie chart (returns base64 encoded image or SVG)."""
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            plt.figure(figsize=(8, 8))
            plt.pie(values, labels=labels, autopct="%1.1f%%")
            plt.title(title)

            buffer = BytesIO()
            plt.savefig(buffer, format="png", bbox_inches="tight")
            plt.close()

            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            return f"data:image/png;base64,{image_base64}"

        except ImportError:
            logger.warning("matplotlib not available, using SVG fallback")
            return self._generate_pie_chart_svg(labels, values, title)

    # =========================================================================
    # SVG Fallback Methods (when matplotlib is not available)
    # =========================================================================

    def _generate_line_chart_svg(
        self, data: dict[str, list[float]], title: str = ""
    ) -> str:
        """
        Generate simple SVG line chart without matplotlib.

        Args:
            data: Dictionary mapping series names to value lists
            title: Chart title

        Returns:
            SVG markup as data URI
        """
        if not data:
            return self._generate_error_svg("No data provided")

        # SVG dimensions
        width, height = 800, 400
        margin = 50
        plot_width = width - 2 * margin
        plot_height = height - 2 * margin

        # Find data range
        all_values = [v for series in data.values() for v in series]
        if not all_values:
            return self._generate_error_svg("Empty data series")

        min_val = min(all_values)
        max_val = max(all_values)
        val_range = max_val - min_val if max_val != min_val else 1

        # Build SVG
        svg_lines = [
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
            f'<rect width="{width}" height="{height}" fill="white"/>',
            f'<text x="{width / 2}" y="25" text-anchor="middle" font-size="16" font-weight="bold">{title}</text>',
        ]

        # Draw axes
        svg_lines.extend(
            [
                f'<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" stroke="black" stroke-width="2"/>',
                f'<line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" stroke="black" stroke-width="2"/>',
            ]
        )

        # Plot each series
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
        legend_y = margin + 20

        for idx, (label, values) in enumerate(data.items()):
            color = colors[idx % len(colors)]
            points = []

            for i, val in enumerate(values):
                x = (
                    margin
                    + (i / (len(values) - 1 if len(values) > 1 else 1)) * plot_width
                )
                y = height - margin - ((val - min_val) / val_range) * plot_height
                points.append(f"{x:.1f},{y:.1f}")

            polyline = " ".join(points)
            svg_lines.append(
                f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="2"/>'
            )

            # Legend
            svg_lines.extend(
                [
                    f'<rect x="{width - margin + 10}" y="{legend_y - 10}" width="15" height="15" fill="{color}"/>',
                    f'<text x="{width - margin + 30}" y="{legend_y}" font-size="12">{label}</text>',
                ]
            )
            legend_y += 25

        svg_lines.append("</svg>")
        svg_content = "\n".join(svg_lines)

        # Convert to data URI
        svg_base64 = base64.b64encode(svg_content.encode()).decode()
        return f"data:image/svg+xml;base64,{svg_base64}"

    def _generate_bar_chart_svg(
        self, categories: list[str], values: list[float], title: str = ""
    ) -> str:
        """
        Generate simple SVG bar chart without matplotlib.

        Args:
            categories: Category labels
            values: Bar heights
            title: Chart title

        Returns:
            SVG markup as data URI
        """
        if not categories or not values or len(categories) != len(values):
            return self._generate_error_svg("Invalid bar chart data")

        # SVG dimensions
        width, height = 800, 400
        margin = 60
        plot_width = width - 2 * margin
        plot_height = height - 2 * margin

        # Find value range
        max_val = max(values) if values else 1
        min_val = min(0, min(values)) if values else 0
        val_range = max_val - min_val if max_val != min_val else 1

        bar_width = plot_width / len(categories) * 0.8
        bar_spacing = plot_width / len(categories)

        # Build SVG
        svg_lines = [
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
            f'<rect width="{width}" height="{height}" fill="white"/>',
            f'<text x="{width / 2}" y="25" text-anchor="middle" font-size="16" font-weight="bold">{title}</text>',
        ]

        # Draw axes
        svg_lines.extend(
            [
                f'<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" stroke="black" stroke-width="2"/>',
                f'<line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" stroke="black" stroke-width="2"/>',
            ]
        )

        # Draw bars
        for i, (cat, val) in enumerate(zip(categories, values)):
            x = margin + i * bar_spacing + (bar_spacing - bar_width) / 2
            bar_height = (val - min_val) / val_range * plot_height
            y = height - margin - bar_height

            svg_lines.extend(
                [
                    f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" fill="#1f77b4"/>',
                    f'<text x="{x + bar_width / 2:.1f}" y="{height - margin + 20}" text-anchor="middle" font-size="10" transform="rotate(45 {x + bar_width / 2:.1f} {height - margin + 20})">{cat}</text>',
                ]
            )

        svg_lines.append("</svg>")
        svg_content = "\n".join(svg_lines)

        # Convert to data URI
        svg_base64 = base64.b64encode(svg_content.encode()).decode()
        return f"data:image/svg+xml;base64,{svg_base64}"

    def _generate_pie_chart_svg(
        self, labels: list[str], values: list[float], title: str = ""
    ) -> str:
        """
        Generate simple SVG pie chart without matplotlib.

        Args:
            labels: Slice labels
            values: Slice sizes
            title: Chart title

        Returns:
            SVG markup as data URI
        """
        import math

        if not labels or not values or len(labels) != len(values):
            return self._generate_error_svg("Invalid pie chart data")

        # SVG dimensions
        width, height = 600, 600
        cx, cy = width / 2, height / 2 + 20
        radius = min(width, height) / 3

        # Calculate percentages
        total = sum(values)
        if total == 0:
            return self._generate_error_svg("Sum of values is zero")

        percentages = [(v / total) * 100 for v in values]

        # Build SVG
        svg_lines = [
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
            f'<rect width="{width}" height="{height}" fill="white"/>',
            f'<text x="{width / 2}" y="25" text-anchor="middle" font-size="16" font-weight="bold">{title}</text>',
        ]

        # Draw pie slices
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
        start_angle = -90  # Start at top

        for idx, (label, pct) in enumerate(zip(labels, percentages)):
            color = colors[idx % len(colors)]
            slice_angle = (pct / 100) * 360

            # Calculate arc path
            end_angle = start_angle + slice_angle
            start_rad = math.radians(start_angle)
            end_rad = math.radians(end_angle)

            x1 = cx + radius * math.cos(start_rad)
            y1 = cy + radius * math.sin(start_rad)
            x2 = cx + radius * math.cos(end_rad)
            y2 = cy + radius * math.sin(end_rad)

            large_arc = 1 if slice_angle > 180 else 0

            path = f"M {cx},{cy} L {x1:.1f},{y1:.1f} A {radius},{radius} 0 {large_arc},1 {x2:.1f},{y2:.1f} Z"
            svg_lines.append(
                f'<path d="{path}" fill="{color}" stroke="white" stroke-width="2"/>'
            )

            # Legend
            legend_x = 20
            legend_y = 100 + idx * 30
            svg_lines.extend(
                [
                    f'<rect x="{legend_x}" y="{legend_y - 10}" width="15" height="15" fill="{color}"/>',
                    f'<text x="{legend_x + 20}" y="{legend_y}" font-size="12">{label}: {pct:.1f}%</text>',
                ]
            )

            start_angle = end_angle

        svg_lines.append("</svg>")
        svg_content = "\n".join(svg_lines)

        # Convert to data URI
        svg_base64 = base64.b64encode(svg_content.encode()).decode()
        return f"data:image/svg+xml;base64,{svg_base64}"

    def _generate_error_svg(self, error_msg: str) -> str:
        """
        Generate error message SVG.

        Args:
            error_msg: Error message to display

        Returns:
            SVG markup as data URI
        """
        svg_content = f"""
        <svg width="400" height="100" xmlns="http://www.w3.org/2000/svg">
            <rect width="400" height="100" fill="#ffeeee" stroke="#ff0000" stroke-width="2"/>
            <text x="200" y="50" text-anchor="middle" font-size="14" fill="#cc0000">
                Chart Error: {error_msg}
            </text>
        </svg>
        """
        svg_base64 = base64.b64encode(svg_content.encode()).decode()
        return f"data:image/svg+xml;base64,{svg_base64}"
