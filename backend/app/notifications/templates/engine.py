"""Template rendering engine using Jinja2."""
import logging
from typing import Any

from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    Template,
    TemplateSyntaxError,
    UndefinedError,
)
from jinja2.sandbox import SandboxedEnvironment

logger = logging.getLogger(__name__)


class TemplateRenderError(Exception):
    """
    Exception raised when template rendering fails.

    Attributes:
        message: Error message
        template_name: Name of the template that failed
        context: Template context data
    """

    def __init__(
        self,
        message: str,
        template_name: str | None = None,
        context: dict[str, Any] | None = None,
    ):
        """
        Initialize the template render error.

        Args:
            message: Error message
            template_name: Name of the template that failed
            context: Template context data
        """
        self.message = message
        self.template_name = template_name
        self.context = context
        super().__init__(self.message)


class TemplateEngine:
    """
    Template rendering engine using Jinja2.

    This engine provides:
    - Safe, sandboxed template rendering
    - HTML and plain text template support
    - Custom filters and functions
    - Localization support
    - Auto-escaping for HTML templates
    - Strict undefined variable checking
    """

    def __init__(
        self,
        template_dirs: list[str] | None = None,
        enable_sandbox: bool = True,
        locale: str = "en_US",
    ):
        """
        Initialize the template engine.

        Args:
            template_dirs: List of directories to search for templates
            enable_sandbox: Whether to use sandboxed environment (recommended)
            locale: Default locale for localization
        """
        self.locale = locale
        self.enable_sandbox = enable_sandbox

        # Create Jinja2 environment
        if enable_sandbox:
            # Use sandboxed environment for security
            self.env = SandboxedEnvironment(
                loader=FileSystemLoader(template_dirs or []),
                autoescape=True,
                undefined=StrictUndefined,
            )
        else:
            self.env = Environment(
                loader=FileSystemLoader(template_dirs or []),
                autoescape=True,
                undefined=StrictUndefined,
            )

        # Register custom filters and functions
        self._register_custom_filters()
        self._register_custom_functions()

    def render_string(
        self,
        template_string: str,
        context: dict[str, Any],
        autoescape: bool = True,
    ) -> str:
        """
        Render a template from a string.

        Args:
            template_string: The template string to render
            context: Context data for template rendering
            autoescape: Whether to auto-escape HTML (default: True)

        Returns:
            Rendered template string

        Raises:
            TemplateRenderError: If rendering fails
        """
        try:
            # Create template from string
            if self.enable_sandbox:
                # Create temporary environment for this template
                env = SandboxedEnvironment(
                    autoescape=autoescape,
                    undefined=StrictUndefined,
                )
                env.filters.update(self.env.filters)
                env.globals.update(self.env.globals)
                template = env.from_string(template_string)
            else:
                template = self.env.from_string(template_string)

            # Add locale to context
            context_with_locale = {"locale": self.locale, **context}

            # Render template
            return template.render(context_with_locale)

        except TemplateSyntaxError as e:
            logger.error(
                "Template syntax error at line %d: %s",
                e.lineno,
                e.message,
                exc_info=True,
            )
            raise TemplateRenderError(
                message=f"Template syntax error: {e.message}",
                context=context,
            ) from e
        except UndefinedError as e:
            logger.error("Undefined variable in template: %s", str(e), exc_info=True)
            raise TemplateRenderError(
                message=f"Undefined variable: {str(e)}",
                context=context,
            ) from e
        except Exception as e:
            logger.error("Template rendering failed: %s", str(e), exc_info=True)
            raise TemplateRenderError(
                message=f"Template rendering failed: {str(e)}",
                context=context,
            ) from e

    def render_template(
        self,
        template_name: str,
        context: dict[str, Any],
    ) -> str:
        """
        Render a template from a file.

        Args:
            template_name: Name of the template file
            context: Context data for template rendering

        Returns:
            Rendered template string

        Raises:
            TemplateRenderError: If rendering fails
        """
        try:
            template = self.env.get_template(template_name)
            context_with_locale = {"locale": self.locale, **context}
            return template.render(context_with_locale)

        except TemplateSyntaxError as e:
            logger.error(
                "Template syntax error in %s at line %d: %s",
                template_name,
                e.lineno,
                e.message,
                exc_info=True,
            )
            raise TemplateRenderError(
                message=f"Template syntax error: {e.message}",
                template_name=template_name,
                context=context,
            ) from e
        except UndefinedError as e:
            logger.error(
                "Undefined variable in template %s: %s",
                template_name,
                str(e),
                exc_info=True,
            )
            raise TemplateRenderError(
                message=f"Undefined variable: {str(e)}",
                template_name=template_name,
                context=context,
            ) from e
        except Exception as e:
            logger.error(
                "Template rendering failed for %s: %s",
                template_name,
                str(e),
                exc_info=True,
            )
            raise TemplateRenderError(
                message=f"Template rendering failed: {str(e)}",
                template_name=template_name,
                context=context,
            ) from e

    def render_html_and_text(
        self,
        html_template: str,
        text_template: str,
        context: dict[str, Any],
    ) -> dict[str, str]:
        """
        Render both HTML and plain text versions of a template.

        Args:
            html_template: HTML template string
            text_template: Plain text template string
            context: Context data for template rendering

        Returns:
            Dictionary with 'html' and 'text' keys

        Raises:
            TemplateRenderError: If rendering fails
        """
        return {
            "html": self.render_string(html_template, context, autoescape=True),
            "text": self.render_string(text_template, context, autoescape=False),
        }

    def preview_template(
        self,
        template_string: str,
        sample_context: dict[str, Any],
    ) -> str:
        """
        Preview a template with sample data.

        Args:
            template_string: The template string to preview
            sample_context: Sample context data

        Returns:
            Rendered preview string

        Raises:
            TemplateRenderError: If rendering fails
        """
        return self.render_string(template_string, sample_context)

    def validate_syntax(self, template_string: str) -> bool:
        """
        Validate template syntax without rendering.

        Args:
            template_string: The template string to validate

        Returns:
            True if syntax is valid

        Raises:
            TemplateRenderError: If syntax is invalid
        """
        try:
            # Parse template to check syntax
            if self.enable_sandbox:
                env = SandboxedEnvironment(undefined=StrictUndefined)
                env.parse(template_string)
            else:
                self.env.parse(template_string)
            return True
        except TemplateSyntaxError as e:
            raise TemplateRenderError(
                message=f"Template syntax error at line {e.lineno}: {e.message}"
            ) from e

    def _register_custom_filters(self) -> None:
        """Register custom Jinja2 filters for template rendering."""

        def format_date(value: Any, format: str = "%Y-%m-%d") -> str:
            """
            Format a date value.

            Args:
                value: Date value to format
                format: strftime format string

            Returns:
                Formatted date string
            """
            from datetime import date, datetime

            if isinstance(value, (date, datetime)):
                return value.strftime(format)
            return str(value)

        def format_datetime(value: Any, format: str = "%Y-%m-%d %H:%M:%S") -> str:
            """
            Format a datetime value.

            Args:
                value: Datetime value to format
                format: strftime format string

            Returns:
                Formatted datetime string
            """
            from datetime import datetime

            if isinstance(value, datetime):
                return value.strftime(format)
            return str(value)

        def pluralize(count: int, singular: str, plural: str | None = None) -> str:
            """
            Pluralize a word based on count.

            Args:
                count: Number to check
                singular: Singular form
                plural: Plural form (defaults to singular + 's')

            Returns:
                Singular or plural form based on count
            """
            if count == 1:
                return singular
            return plural if plural else f"{singular}s"

        # Register filters
        self.env.filters["format_date"] = format_date
        self.env.filters["format_datetime"] = format_datetime
        self.env.filters["pluralize"] = pluralize

    def _register_custom_functions(self) -> None:
        """Register custom Jinja2 global functions."""

        def localize(key: str, **kwargs) -> str:
            """
            Localize a string (placeholder for i18n).

            Args:
                key: Localization key
                **kwargs: Variables for string formatting

            Returns:
                Localized string
            """
            # TODO: Implement proper i18n lookup
            # For now, return the key with variables substituted
            result = key
            for k, v in kwargs.items():
                result = result.replace(f"{{{k}}}", str(v))
            return result

        # Register global functions
        self.env.globals["localize"] = localize
        self.env.globals["locale"] = self.locale


# Default global instance
_default_engine: TemplateEngine | None = None


def get_template_engine(
    template_dirs: list[str] | None = None,
    enable_sandbox: bool = True,
    locale: str = "en_US",
) -> TemplateEngine:
    """
    Get or create the default template engine instance.

    Args:
        template_dirs: List of directories to search for templates
        enable_sandbox: Whether to use sandboxed environment
        locale: Default locale for localization

    Returns:
        TemplateEngine instance
    """
    global _default_engine
    if _default_engine is None:
        _default_engine = TemplateEngine(
            template_dirs=template_dirs,
            enable_sandbox=enable_sandbox,
            locale=locale,
        )
    return _default_engine
