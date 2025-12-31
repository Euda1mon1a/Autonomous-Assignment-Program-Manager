"""Chart Generator - Generates charts for reports."""

from typing import Any, Dict, List
import logging
import base64
from io import BytesIO

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generates charts for reports."""

    def generate_line_chart(self, data: dict[str, list[float]], title: str = "") -> str:
        """Generate line chart (returns base64 encoded image)."""
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
            logger.warning("matplotlib not available, returning placeholder")
            return "chart_placeholder"

    def generate_bar_chart(
        self, categories: list[str], values: list[float], title: str = ""
    ) -> str:
        """Generate bar chart."""
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
            logger.warning("matplotlib not available, returning placeholder")
            return "chart_placeholder"

    def generate_pie_chart(
        self, labels: list[str], values: list[float], title: str = ""
    ) -> str:
        """Generate pie chart."""
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
            logger.warning("matplotlib not available, returning placeholder")
            return "chart_placeholder"
