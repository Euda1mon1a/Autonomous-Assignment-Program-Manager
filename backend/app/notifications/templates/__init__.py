"""
Notification template system for the Residency Scheduler.

This package provides a comprehensive template system with:
- Jinja2 template rendering
- HTML and plain text templates
- Variable substitution with validation
- Template versioning
- Custom template support
- Preview functionality
- Localization support
"""
from app.notifications.templates.engine import TemplateEngine, TemplateRenderError
from app.notifications.templates.registry import (
    TemplateRegistry,
    TemplateVersion,
    get_template_registry,
)
from app.notifications.templates.validators import (
    TemplateValidator,
    ValidationError,
    validate_template_syntax,
)

__all__ = [
    "TemplateEngine",
    "TemplateRenderError",
    "TemplateRegistry",
    "TemplateVersion",
    "get_template_registry",
    "TemplateValidator",
    "ValidationError",
    "validate_template_syntax",
]
