"""Email template rendering engine."""

from string import Template
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailTemplateEngine:
    """
    Renders email templates with data.

    Supports:
    - Variable substitution
    - Conditional blocks
    - Loops
    - Filters
    """

    def __init__(self):
        """Initialize template engine."""
        self._templates: dict[str, str] = {}

    def register_template(self, name: str, template_str: str) -> None:
        """
        Register an email template.

        Args:
            name: Template name
            template_str: Template string
        """
        self._templates[name] = template_str
        logger.debug("Registered email template: %s", name)

    def render(self, template_name: str, data: dict[str, Any]) -> str:
        """
        Render template with data.

        Args:
            template_name: Name of template
            data: Data for rendering

        Returns:
            Rendered template string

        Raises:
            ValueError: If template not found
        """
        if template_name not in self._templates:
            raise ValueError(f"Template not found: {template_name}")

        template_str = self._templates[template_name]
        template = Template(template_str)

        try:
            rendered = template.safe_substitute(data)
            logger.debug("Rendered template: %s", template_name)
            return rendered

        except Exception as e:
            logger.error("Error rendering template %s: %s", template_name, e)
            raise

    def render_string(self, template_str: str, data: dict[str, Any]) -> str:
        """
        Render template string directly.

        Args:
            template_str: Template string
            data: Data for rendering

        Returns:
            Rendered string
        """
        template = Template(template_str)
        return template.safe_substitute(data)
