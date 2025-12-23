"""Template validation utilities."""

import logging
import re
from typing import Any

from jinja2 import Environment, TemplateSyntaxError, meta

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """
    Exception raised when template validation fails.

    Attributes:
        message: Error message
        field: Field that failed validation
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize validation error.

        Args:
            message: Error message
            field: Field that failed validation
            details: Additional error details
        """
        self.message = message
        self.field = field
        self.details = details or {}
        super().__init__(self.message)


class TemplateValidator:
    """
    Validator for notification templates.

    This validator checks:
    - Template syntax (Jinja2)
    - Required variables are present
    - No dangerous operations
    - Character limits
    - HTML safety
    """

    # Maximum lengths for template components
    MAX_SUBJECT_LENGTH = 500
    MAX_TEMPLATE_LENGTH = 50000  # ~50KB

    # Forbidden Jinja2 operations for security
    FORBIDDEN_FILTERS = [
        "exec",
        "eval",
        "compile",
        "__import__",
        "open",
        "file",
    ]

    FORBIDDEN_TAGS = [
        "exec",
        "eval",
        "import",
    ]

    def __init__(self):
        """Initialize the template validator."""
        self.env = Environment()

    def validate_template_syntax(self, template_string: str) -> bool:
        """
        Validate Jinja2 template syntax.

        Args:
            template_string: Template string to validate

        Returns:
            True if syntax is valid

        Raises:
            ValidationError: If syntax is invalid
        """
        try:
            self.env.parse(template_string)
            return True
        except TemplateSyntaxError as e:
            raise ValidationError(
                message=f"Template syntax error at line {e.lineno}: {e.message}",
                field="template_syntax",
                details={"line": e.lineno, "error": e.message},
            ) from e

    def validate_subject_template(self, subject_template: str) -> bool:
        """
        Validate subject template.

        Args:
            subject_template: Subject template string

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        # Check length
        if len(subject_template) > self.MAX_SUBJECT_LENGTH:
            raise ValidationError(
                message=f"Subject template exceeds maximum length of {self.MAX_SUBJECT_LENGTH} characters",
                field="subject_template",
                details={
                    "length": len(subject_template),
                    "max_length": self.MAX_SUBJECT_LENGTH,
                },
            )

        # Validate syntax
        self.validate_template_syntax(subject_template)

        # Check for newlines (subjects should be single line)
        if "\n" in subject_template:
            raise ValidationError(
                message="Subject template should not contain newlines",
                field="subject_template",
            )

        return True

    def validate_body_template(
        self,
        body_template: str,
        template_type: str = "text",
    ) -> bool:
        """
        Validate body template.

        Args:
            body_template: Body template string
            template_type: Type of template ('text' or 'html')

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        # Check length
        if len(body_template) > self.MAX_TEMPLATE_LENGTH:
            raise ValidationError(
                message=f"Body template exceeds maximum length of {self.MAX_TEMPLATE_LENGTH} characters",
                field="body_template",
                details={
                    "length": len(body_template),
                    "max_length": self.MAX_TEMPLATE_LENGTH,
                },
            )

        # Validate syntax
        self.validate_template_syntax(body_template)

        # Validate HTML if needed
        if template_type == "html":
            self._validate_html_safety(body_template)

        return True

    def validate_required_variables(
        self,
        template_string: str,
        required_variables: list[str],
    ) -> bool:
        """
        Validate that all required variables are used in the template.

        Args:
            template_string: Template string to check
            required_variables: List of required variable names

        Returns:
            True if all required variables are present

        Raises:
            ValidationError: If required variables are missing
        """
        # Parse template to extract variables
        ast = self.env.parse(template_string)
        template_vars = meta.find_undeclared_variables(ast)

        # Check for missing required variables
        missing_vars = set(required_variables) - template_vars

        if missing_vars:
            raise ValidationError(
                message=f"Template is missing required variables: {', '.join(sorted(missing_vars))}",
                field="required_variables",
                details={
                    "missing_variables": sorted(list(missing_vars)),
                    "template_variables": sorted(list(template_vars)),
                },
            )

        return True

    def validate_no_forbidden_operations(self, template_string: str) -> bool:
        """
        Validate that template doesn't use forbidden operations.

        Args:
            template_string: Template string to check

        Returns:
            True if no forbidden operations found

        Raises:
            ValidationError: If forbidden operations are found
        """
        # Check for forbidden filters
        for forbidden_filter in self.FORBIDDEN_FILTERS:
            pattern = rf"\|{re.escape(forbidden_filter)}(\s|$|\(|\|)"
            if re.search(pattern, template_string):
                raise ValidationError(
                    message=f"Forbidden filter '{forbidden_filter}' is not allowed",
                    field="security",
                    details={"forbidden_filter": forbidden_filter},
                )

        # Check for forbidden tags
        for forbidden_tag in self.FORBIDDEN_TAGS:
            pattern = rf"{{% *{re.escape(forbidden_tag)} *%}}"
            if re.search(pattern, template_string):
                raise ValidationError(
                    message=f"Forbidden tag '{forbidden_tag}' is not allowed",
                    field="security",
                    details={"forbidden_tag": forbidden_tag},
                )

        return True

    def _validate_html_safety(self, html_template: str) -> bool:
        """
        Validate HTML template for safety issues.

        Args:
            html_template: HTML template string

        Returns:
            True if safe

        Raises:
            ValidationError: If unsafe HTML is found
        """
        # Check for script tags (basic XSS prevention)
        # Note: Jinja2 auto-escaping provides the main protection
        if re.search(r"<script[^>]*>", html_template, re.IGNORECASE):
            # Allow script tags in style blocks only
            if not re.search(
                r"<script[^>]*>\s*(\/\/|\/\*|$)", html_template, re.IGNORECASE
            ):
                logger.warning(
                    "HTML template contains script tags - ensure auto-escaping is enabled"
                )

        # Check for dangerous attributes
        dangerous_attrs = ["onerror", "onload", "onclick", "onmouseover"]
        for attr in dangerous_attrs:
            if re.search(rf"{attr}\s*=", html_template, re.IGNORECASE):
                raise ValidationError(
                    message=f"Dangerous HTML attribute '{attr}' is not allowed",
                    field="html_safety",
                    details={"dangerous_attribute": attr},
                )

        return True

    def validate_complete_template(
        self,
        subject_template: str,
        html_template: str,
        text_template: str,
        required_variables: list[str] | None = None,
    ) -> bool:
        """
        Validate a complete notification template.

        Args:
            subject_template: Subject template string
            html_template: HTML body template string
            text_template: Plain text body template string
            required_variables: Optional list of required variables

        Returns:
            True if all validations pass

        Raises:
            ValidationError: If any validation fails
        """
        # Validate subject
        self.validate_subject_template(subject_template)

        # Validate HTML body
        self.validate_body_template(html_template, template_type="html")

        # Validate text body
        self.validate_body_template(text_template, template_type="text")

        # Check for forbidden operations in all templates
        self.validate_no_forbidden_operations(subject_template)
        self.validate_no_forbidden_operations(html_template)
        self.validate_no_forbidden_operations(text_template)

        # Validate required variables if provided
        if required_variables:
            # Variables should be present in at least one of the templates
            combined_template = f"{subject_template}\n{html_template}\n{text_template}"
            self.validate_required_variables(combined_template, required_variables)

        return True

    def extract_variables(self, template_string: str) -> list[str]:
        """
        Extract all variables used in a template.

        Args:
            template_string: Template string to analyze

        Returns:
            List of variable names used in the template
        """
        try:
            ast = self.env.parse(template_string)
            variables = meta.find_undeclared_variables(ast)
            return sorted(list(variables))
        except TemplateSyntaxError as e:
            logger.error("Failed to extract variables: %s", e, exc_info=True)
            return []


# Convenience function
def validate_template_syntax(template_string: str) -> bool:
    """
    Validate template syntax (convenience function).

    Args:
        template_string: Template string to validate

    Returns:
        True if syntax is valid

    Raises:
        ValidationError: If syntax is invalid
    """
    validator = TemplateValidator()
    return validator.validate_template_syntax(template_string)
