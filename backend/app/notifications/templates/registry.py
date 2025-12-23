"""Template registry with versioning support."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from app.notifications.templates.engine import TemplateEngine, get_template_engine

logger = logging.getLogger(__name__)


@dataclass
class TemplateVersion:
    """
    A versioned notification template.

    Attributes:
        id: Unique identifier for this version
        template_id: ID of the parent template
        version: Version number (semantic versioning: major.minor.patch)
        name: Template name
        description: Template description
        subject_template: Subject line template
        html_template: HTML body template
        text_template: Plain text body template
        variables: Required variables for this template
        locale: Locale for this template (e.g., 'en_US', 'es_ES')
        is_active: Whether this version is active
        created_at: Creation timestamp
        created_by: User who created this version
        tags: Tags for categorization
        metadata: Additional metadata
    """

    id: UUID = field(default_factory=uuid4)
    template_id: str = ""
    version: str = "1.0.0"
    name: str = ""
    description: str = ""
    subject_template: str = ""
    html_template: str = ""
    text_template: str = ""
    variables: list[str] = field(default_factory=list)
    locale: str = "en_US"
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def increment_version(self, level: str = "patch") -> str:
        """
        Increment the version number.

        Args:
            level: Which version level to increment (major, minor, patch)

        Returns:
            New version string
        """
        parts = self.version.split(".")
        if len(parts) != 3:
            parts = ["1", "0", "0"]

        major, minor, patch = map(int, parts)

        if level == "major":
            major += 1
            minor = 0
            patch = 0
        elif level == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1

        return f"{major}.{minor}.{patch}"


class TemplateRegistry:
    """
    Central registry for notification templates with versioning support.

    This registry manages:
    - Template storage and retrieval
    - Version management
    - Template activation/deactivation
    - Locale support
    - Custom template registration
    """

    def __init__(self, engine: TemplateEngine | None = None):
        """
        Initialize the template registry.

        Args:
            engine: Template rendering engine (creates default if not provided)
        """
        self.engine = engine or get_template_engine()
        self._templates: dict[str, list[TemplateVersion]] = {}
        self._active_versions: dict[str, TemplateVersion] = {}

    def register_template(
        self,
        template: TemplateVersion,
        set_active: bool = True,
    ) -> TemplateVersion:
        """
        Register a new template or version.

        Args:
            template: Template version to register
            set_active: Whether to set this as the active version

        Returns:
            Registered template version

        Raises:
            ValueError: If template validation fails
        """
        # Validate template syntax
        try:
            self.engine.validate_syntax(template.subject_template)
            self.engine.validate_syntax(template.html_template)
            self.engine.validate_syntax(template.text_template)
        except Exception as e:
            raise ValueError(f"Template validation failed: {str(e)}") from e

        # Add to registry
        if template.template_id not in self._templates:
            self._templates[template.template_id] = []

        self._templates[template.template_id].append(template)

        # Set as active if requested
        if set_active:
            self._active_versions[template.template_id] = template

        logger.info(
            "Registered template %s version %s (active: %s)",
            template.template_id,
            template.version,
            set_active,
        )

        return template

    def get_template(
        self,
        template_id: str,
        version: str | None = None,
        locale: str | None = None,
    ) -> TemplateVersion | None:
        """
        Retrieve a template by ID and optional version.

        Args:
            template_id: Template identifier
            version: Specific version (None for active version)
            locale: Preferred locale (falls back to default)

        Returns:
            Template version or None if not found
        """
        if template_id not in self._templates:
            return None

        # Get all versions for this template
        versions = self._templates[template_id]

        # Filter by locale if specified
        if locale:
            locale_versions = [v for v in versions if v.locale == locale]
            if locale_versions:
                versions = locale_versions

        # If no version specified, return active version
        if version is None:
            return self._active_versions.get(template_id)

        # Find specific version
        for template_version in versions:
            if template_version.version == version:
                return template_version

        return None

    def get_all_versions(self, template_id: str) -> list[TemplateVersion]:
        """
        Get all versions of a template.

        Args:
            template_id: Template identifier

        Returns:
            List of template versions (sorted by version descending)
        """
        versions = self._templates.get(template_id, [])

        # Sort by version (newest first)
        def version_key(v: TemplateVersion) -> tuple[int, int, int]:
            parts = v.version.split(".")
            return tuple(map(int, parts))

        return sorted(versions, key=version_key, reverse=True)

    def list_templates(
        self,
        active_only: bool = False,
        locale: str | None = None,
        tags: list[str] | None = None,
    ) -> list[TemplateVersion]:
        """
        List all registered templates.

        Args:
            active_only: Only return active versions
            locale: Filter by locale
            tags: Filter by tags (templates matching any tag)

        Returns:
            List of template versions
        """
        if active_only:
            templates = list(self._active_versions.values())
        else:
            templates = [v for versions in self._templates.values() for v in versions]

        # Filter by locale
        if locale:
            templates = [t for t in templates if t.locale == locale]

        # Filter by tags
        if tags:
            templates = [t for t in templates if any(tag in t.tags for tag in tags)]

        return templates

    def set_active_version(self, template_id: str, version: str) -> bool:
        """
        Set a specific version as active.

        Args:
            template_id: Template identifier
            version: Version to activate

        Returns:
            True if successful, False otherwise
        """
        template = self.get_template(template_id, version=version)
        if not template:
            return False

        self._active_versions[template_id] = template
        logger.info("Set template %s version %s as active", template_id, version)
        return True

    def deactivate_template(self, template_id: str) -> bool:
        """
        Deactivate a template (no active version).

        Args:
            template_id: Template identifier

        Returns:
            True if successful, False otherwise
        """
        if template_id in self._active_versions:
            del self._active_versions[template_id]
            logger.info("Deactivated template %s", template_id)
            return True
        return False

    def create_new_version(
        self,
        template_id: str,
        level: str = "patch",
        **updates: Any,
    ) -> TemplateVersion | None:
        """
        Create a new version of an existing template.

        Args:
            template_id: Template identifier
            level: Version increment level (major, minor, patch)
            **updates: Fields to update in the new version

        Returns:
            New template version or None if template not found
        """
        current = self.get_template(template_id)
        if not current:
            return None

        # Create new version
        new_version = TemplateVersion(
            id=uuid4(),
            template_id=current.template_id,
            version=current.increment_version(level),
            name=updates.get("name", current.name),
            description=updates.get("description", current.description),
            subject_template=updates.get("subject_template", current.subject_template),
            html_template=updates.get("html_template", current.html_template),
            text_template=updates.get("text_template", current.text_template),
            variables=updates.get("variables", current.variables.copy()),
            locale=updates.get("locale", current.locale),
            is_active=True,
            created_at=datetime.utcnow(),
            created_by=updates.get("created_by"),
            tags=updates.get("tags", current.tags.copy()),
            metadata=updates.get("metadata", current.metadata.copy()),
        )

        # Register the new version
        return self.register_template(new_version, set_active=True)

    def render_template(
        self,
        template_id: str,
        context: dict[str, Any],
        version: str | None = None,
        locale: str | None = None,
    ) -> dict[str, str] | None:
        """
        Render a template with context data.

        Args:
            template_id: Template identifier
            context: Context data for rendering
            version: Specific version (None for active)
            locale: Preferred locale

        Returns:
            Dictionary with 'subject', 'html', and 'text' keys, or None if template not found
        """
        template = self.get_template(template_id, version=version, locale=locale)
        if not template:
            logger.warning("Template %s not found", template_id)
            return None

        try:
            result = {
                "subject": self.engine.render_string(
                    template.subject_template, context, autoescape=False
                ),
                "html": self.engine.render_string(
                    template.html_template, context, autoescape=True
                ),
                "text": self.engine.render_string(
                    template.text_template, context, autoescape=False
                ),
            }
            return result

        except Exception as e:
            logger.error(
                "Failed to render template %s: %s",
                template_id,
                str(e),
                exc_info=True,
            )
            return None

    def preview_template(
        self,
        template_id: str,
        sample_context: dict[str, Any],
        version: str | None = None,
    ) -> dict[str, str] | None:
        """
        Preview a template with sample data.

        Args:
            template_id: Template identifier
            sample_context: Sample context data
            version: Specific version (None for active)

        Returns:
            Dictionary with rendered subject, html, and text, or None if template not found
        """
        return self.render_template(template_id, sample_context, version=version)

    def delete_version(self, template_id: str, version: str) -> bool:
        """
        Delete a specific template version.

        Args:
            template_id: Template identifier
            version: Version to delete

        Returns:
            True if successful, False otherwise
        """
        if template_id not in self._templates:
            return False

        # Find and remove the version
        versions = self._templates[template_id]
        for i, template_version in enumerate(versions):
            if template_version.version == version:
                del versions[i]

                # If this was the active version, clear it
                if (
                    template_id in self._active_versions
                    and self._active_versions[template_id].version == version
                ):
                    del self._active_versions[template_id]
                    # Optionally activate the latest version
                    if versions:
                        self._active_versions[template_id] = versions[0]

                logger.info("Deleted template %s version %s", template_id, version)
                return True

        return False


# Global registry instance
_global_registry: TemplateRegistry | None = None


def get_template_registry() -> TemplateRegistry:
    """
    Get or create the global template registry.

    Returns:
        TemplateRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = TemplateRegistry()
    return _global_registry
