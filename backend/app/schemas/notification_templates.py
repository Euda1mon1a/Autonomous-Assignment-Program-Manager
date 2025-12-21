"""Pydantic schemas for notification templates."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TemplateVariableSchema(BaseModel):
    """
    Schema for a template variable.

    Attributes:
        name: Variable name
        description: Variable description
        required: Whether this variable is required
        default_value: Default value if not provided
        example_value: Example value for preview
    """

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    required: bool = Field(default=True)
    default_value: Any = Field(default=None)
    example_value: Any = Field(default=None)


class TemplateCreateSchema(BaseModel):
    """
    Schema for creating a new notification template.

    Attributes:
        template_id: Unique template identifier
        name: Template name
        description: Template description
        subject_template: Subject line template (Jinja2)
        html_template: HTML body template (Jinja2)
        text_template: Plain text body template (Jinja2)
        variables: List of required variables
        locale: Template locale (default: en_US)
        tags: Tags for categorization
        metadata: Additional metadata
    """

    template_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    subject_template: str = Field(..., min_length=1, max_length=500)
    html_template: str = Field(..., min_length=1, max_length=50000)
    text_template: str = Field(..., min_length=1, max_length=50000)
    variables: list[str] = Field(default_factory=list)
    locale: str = Field(default="en_US", max_length=10)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("template_id")
    @classmethod
    def validate_template_id(cls, v: str) -> str:
        """
        Validate template ID format.

        Args:
            v: Template ID to validate

        Returns:
            Validated template ID

        Raises:
            ValueError: If template ID is invalid
        """
        # Template ID should be lowercase with underscores
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Template ID must contain only alphanumeric characters, underscores, and hyphens"
            )
        return v.lower()

    @field_validator("locale")
    @classmethod
    def validate_locale(cls, v: str) -> str:
        """
        Validate locale format.

        Args:
            v: Locale string to validate

        Returns:
            Validated locale

        Raises:
            ValueError: If locale format is invalid
        """
        # Basic locale validation (language_COUNTRY)
        if "_" in v:
            parts = v.split("_")
            if len(parts) != 2 or len(parts[0]) != 2 or len(parts[1]) != 2:
                raise ValueError("Locale must be in format: xx_YY (e.g., en_US)")
        return v


class TemplateUpdateSchema(BaseModel):
    """
    Schema for updating an existing notification template.

    All fields are optional to allow partial updates.

    Attributes:
        name: Template name
        description: Template description
        subject_template: Subject line template (Jinja2)
        html_template: HTML body template (Jinja2)
        text_template: Plain text body template (Jinja2)
        variables: List of required variables
        locale: Template locale
        tags: Tags for categorization
        metadata: Additional metadata
        version_increment: How to increment version (major, minor, patch)
    """

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    subject_template: str | None = Field(default=None, min_length=1, max_length=500)
    html_template: str | None = Field(default=None, min_length=1, max_length=50000)
    text_template: str | None = Field(default=None, min_length=1, max_length=50000)
    variables: list[str] | None = Field(default=None)
    locale: str | None = Field(default=None, max_length=10)
    tags: list[str] | None = Field(default=None)
    metadata: dict[str, Any] | None = Field(default=None)
    version_increment: str = Field(default="patch", pattern="^(major|minor|patch)$")


class TemplateVersionSchema(BaseModel):
    """
    Schema for a template version response.

    Attributes:
        id: Unique version identifier
        template_id: Parent template identifier
        version: Version number (semantic versioning)
        name: Template name
        description: Template description
        subject_template: Subject line template
        html_template: HTML body template
        text_template: Plain text body template
        variables: List of required variables
        locale: Template locale
        is_active: Whether this version is active
        created_at: Creation timestamp
        created_by: User who created this version
        tags: Tags for categorization
        metadata: Additional metadata
    """

    id: UUID
    template_id: str
    version: str
    name: str
    description: str
    subject_template: str
    html_template: str
    text_template: str
    variables: list[str]
    locale: str
    is_active: bool
    created_at: datetime
    created_by: str | None = None
    tags: list[str]
    metadata: dict[str, Any]

    class Config:
        """Pydantic config."""

        from_attributes = True


class TemplateListItemSchema(BaseModel):
    """
    Schema for a template list item (summary view).

    Attributes:
        template_id: Template identifier
        name: Template name
        description: Template description
        version: Current active version
        locale: Template locale
        tags: Tags for categorization
        is_active: Whether template has an active version
        created_at: Creation timestamp
    """

    template_id: str
    name: str
    description: str
    version: str
    locale: str
    tags: list[str]
    is_active: bool
    created_at: datetime


class TemplateRenderRequestSchema(BaseModel):
    """
    Schema for a template render request.

    Attributes:
        template_id: Template identifier
        version: Specific version (None for active)
        locale: Preferred locale
        context: Context data for rendering
    """

    template_id: str = Field(..., min_length=1, max_length=100)
    version: str | None = Field(default=None, max_length=20)
    locale: str | None = Field(default=None, max_length=10)
    context: dict[str, Any] = Field(default_factory=dict)


class TemplateRenderResponseSchema(BaseModel):
    """
    Schema for a template render response.

    Attributes:
        template_id: Template identifier
        version: Version that was rendered
        subject: Rendered subject
        html: Rendered HTML body
        text: Rendered plain text body
        locale: Locale used for rendering
    """

    template_id: str
    version: str
    subject: str
    html: str
    text: str
    locale: str


class TemplatePreviewRequestSchema(BaseModel):
    """
    Schema for a template preview request.

    Attributes:
        subject_template: Subject template to preview
        html_template: HTML template to preview
        text_template: Text template to preview
        sample_context: Sample context data
    """

    subject_template: str = Field(..., min_length=1, max_length=500)
    html_template: str = Field(..., min_length=1, max_length=50000)
    text_template: str = Field(..., min_length=1, max_length=50000)
    sample_context: dict[str, Any] = Field(default_factory=dict)


class TemplatePreviewResponseSchema(BaseModel):
    """
    Schema for a template preview response.

    Attributes:
        subject: Rendered subject
        html: Rendered HTML body
        text: Rendered plain text body
        warnings: Any validation warnings
    """

    subject: str
    html: str
    text: str
    warnings: list[str] = Field(default_factory=list)


class TemplateValidationRequestSchema(BaseModel):
    """
    Schema for a template validation request.

    Attributes:
        subject_template: Subject template to validate
        html_template: HTML template to validate
        text_template: Text template to validate
        required_variables: Required variables that must be present
    """

    subject_template: str = Field(..., min_length=1, max_length=500)
    html_template: str = Field(..., min_length=1, max_length=50000)
    text_template: str = Field(..., min_length=1, max_length=50000)
    required_variables: list[str] = Field(default_factory=list)


class TemplateValidationResponseSchema(BaseModel):
    """
    Schema for a template validation response.

    Attributes:
        is_valid: Whether all templates are valid
        errors: List of validation errors
        warnings: List of validation warnings
        detected_variables: Variables detected in templates
    """

    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    detected_variables: list[str] = Field(default_factory=list)


class TemplateActivateRequestSchema(BaseModel):
    """
    Schema for activating a template version.

    Attributes:
        template_id: Template identifier
        version: Version to activate
    """

    template_id: str = Field(..., min_length=1, max_length=100)
    version: str = Field(..., min_length=1, max_length=20)


class TemplateVersionListSchema(BaseModel):
    """
    Schema for listing template versions.

    Attributes:
        template_id: Template identifier
        versions: List of version information
    """

    template_id: str
    versions: list[TemplateVersionSchema]


class TemplateErrorSchema(BaseModel):
    """
    Schema for template-related errors.

    Attributes:
        error: Error type
        message: Error message
        field: Field that caused the error (if applicable)
        details: Additional error details
    """

    error: str
    message: str
    field: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
