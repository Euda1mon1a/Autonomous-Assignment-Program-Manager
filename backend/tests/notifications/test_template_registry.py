"""Tests for notification template registry."""

import pytest

from app.notifications.templates.registry import (
    TemplateRegistry,
    TemplateVersion,
    get_template_registry,
)


class TestTemplateRegistry:
    """Test suite for template registry."""

    def test_register_template(self):
        """Test registering a new template."""
        registry = TemplateRegistry()
        template = TemplateVersion(
            template_id="test_template",
            version="1.0.0",
            name="Test Template",
            subject_template="Test Subject",
            html_template="<p>Test HTML</p>",
            text_template="Test Text",
        )

        result = registry.register_template(template)
        assert result.template_id == "test_template"
        assert result.version == "1.0.0"

    def test_get_template_active_version(self):
        """Test retrieving active template version."""
        registry = TemplateRegistry()
        template = TemplateVersion(
            template_id="test_template",
            version="1.0.0",
            name="Test Template",
            subject_template="Test Subject",
            html_template="<p>Test HTML</p>",
            text_template="Test Text",
        )
        registry.register_template(template)

        retrieved = registry.get_template("test_template")
        assert retrieved is not None
        assert retrieved.version == "1.0.0"

    def test_get_template_specific_version(self):
        """Test retrieving specific template version."""
        registry = TemplateRegistry()

        # Register v1.0.0
        template_v1 = TemplateVersion(
            template_id="test_template",
            version="1.0.0",
            name="Test Template v1",
            subject_template="Test Subject v1",
            html_template="<p>Test HTML v1</p>",
            text_template="Test Text v1",
        )
        registry.register_template(template_v1, set_active=False)

        # Register v2.0.0 (active)
        template_v2 = TemplateVersion(
            template_id="test_template",
            version="2.0.0",
            name="Test Template v2",
            subject_template="Test Subject v2",
            html_template="<p>Test HTML v2</p>",
            text_template="Test Text v2",
        )
        registry.register_template(template_v2, set_active=True)

        # Get specific version
        retrieved_v1 = registry.get_template("test_template", version="1.0.0")
        assert retrieved_v1 is not None
        assert retrieved_v1.version == "1.0.0"
        assert "v1" in retrieved_v1.subject_template

        # Get active version (should be v2)
        retrieved_active = registry.get_template("test_template")
        assert retrieved_active is not None
        assert retrieved_active.version == "2.0.0"

    def test_get_all_versions(self):
        """Test getting all versions of a template."""
        registry = TemplateRegistry()

        # Register multiple versions
        for i in range(1, 4):
            template = TemplateVersion(
                template_id="test_template",
                version=f"{i}.0.0",
                name=f"Test Template v{i}",
                subject_template=f"Test Subject v{i}",
                html_template=f"<p>Test HTML v{i}</p>",
                text_template=f"Test Text v{i}",
            )
            registry.register_template(template)

        versions = registry.get_all_versions("test_template")
        assert len(versions) == 3
        # Should be sorted by version descending
        assert versions[0].version == "3.0.0"
        assert versions[1].version == "2.0.0"
        assert versions[2].version == "1.0.0"

    def test_set_active_version(self):
        """Test setting a specific version as active."""
        registry = TemplateRegistry()

        # Register two versions
        template_v1 = TemplateVersion(
            template_id="test_template",
            version="1.0.0",
            name="Test Template v1",
            subject_template="Test Subject v1",
            html_template="<p>Test HTML v1</p>",
            text_template="Test Text v1",
        )
        registry.register_template(template_v1)

        template_v2 = TemplateVersion(
            template_id="test_template",
            version="2.0.0",
            name="Test Template v2",
            subject_template="Test Subject v2",
            html_template="<p>Test HTML v2</p>",
            text_template="Test Text v2",
        )
        registry.register_template(template_v2)

        # v2 should be active
        active = registry.get_template("test_template")
        assert active.version == "2.0.0"

        # Set v1 as active
        success = registry.set_active_version("test_template", "1.0.0")
        assert success is True

        # Now v1 should be active
        active = registry.get_template("test_template")
        assert active.version == "1.0.0"

    def test_deactivate_template(self):
        """Test deactivating a template."""
        registry = TemplateRegistry()
        template = TemplateVersion(
            template_id="test_template",
            version="1.0.0",
            name="Test Template",
            subject_template="Test Subject",
            html_template="<p>Test HTML</p>",
            text_template="Test Text",
        )
        registry.register_template(template)

        # Deactivate
        success = registry.deactivate_template("test_template")
        assert success is True

        # Should not have active version
        active = registry.get_template("test_template")
        assert active is None

    def test_create_new_version(self):
        """Test creating a new version of existing template."""
        registry = TemplateRegistry()

        # Register original version
        template_v1 = TemplateVersion(
            template_id="test_template",
            version="1.0.0",
            name="Test Template",
            subject_template="Test Subject",
            html_template="<p>Test HTML</p>",
            text_template="Test Text",
        )
        registry.register_template(template_v1)

        # Create patch version
        new_version = registry.create_new_version(
            "test_template",
            level="patch",
            subject_template="Updated Subject",
        )

        assert new_version is not None
        assert new_version.version == "1.0.1"
        assert new_version.subject_template == "Updated Subject"
        # Other fields should be inherited
        assert new_version.html_template == "<p>Test HTML</p>"

    def test_create_new_version_minor(self):
        """Test creating a minor version."""
        registry = TemplateRegistry()

        template = TemplateVersion(
            template_id="test_template",
            version="1.0.0",
            name="Test Template",
            subject_template="Test Subject",
            html_template="<p>Test HTML</p>",
            text_template="Test Text",
        )
        registry.register_template(template)

        new_version = registry.create_new_version("test_template", level="minor")
        assert new_version.version == "1.1.0"

    def test_create_new_version_major(self):
        """Test creating a major version."""
        registry = TemplateRegistry()

        template = TemplateVersion(
            template_id="test_template",
            version="1.0.0",
            name="Test Template",
            subject_template="Test Subject",
            html_template="<p>Test HTML</p>",
            text_template="Test Text",
        )
        registry.register_template(template)

        new_version = registry.create_new_version("test_template", level="major")
        assert new_version.version == "2.0.0"

    def test_render_template(self):
        """Test rendering a template."""
        registry = TemplateRegistry()

        template = TemplateVersion(
            template_id="test_template",
            version="1.0.0",
            name="Test Template",
            subject_template="Hello {{ name }}",
            html_template="<p>Welcome {{ name }}!</p>",
            text_template="Welcome {{ name }}!",
        )
        registry.register_template(template)

        result = registry.render_template("test_template", {"name": "Alice"})

        assert result is not None
        assert result["subject"] == "Hello Alice"
        assert result["html"] == "<p>Welcome Alice!</p>"
        assert result["text"] == "Welcome Alice!"

    def test_preview_template(self):
        """Test previewing a template."""
        registry = TemplateRegistry()

        template = TemplateVersion(
            template_id="test_template",
            version="1.0.0",
            name="Test Template",
            subject_template="Preview: {{ title }}",
            html_template="<p>{{ content }}</p>",
            text_template="{{ content }}",
        )
        registry.register_template(template)

        result = registry.preview_template(
            "test_template",
            {"title": "Test", "content": "Sample content"},
        )

        assert result is not None
        assert result["subject"] == "Preview: Test"
        assert result["html"] == "<p>Sample content</p>"

    def test_list_templates_active_only(self):
        """Test listing only active templates."""
        registry = TemplateRegistry()

        # Register active template
        template1 = TemplateVersion(
            template_id="template1",
            version="1.0.0",
            name="Template 1",
            subject_template="Subject 1",
            html_template="<p>HTML 1</p>",
            text_template="Text 1",
        )
        registry.register_template(template1, set_active=True)

        # Register inactive template
        template2 = TemplateVersion(
            template_id="template2",
            version="1.0.0",
            name="Template 2",
            subject_template="Subject 2",
            html_template="<p>HTML 2</p>",
            text_template="Text 2",
        )
        registry.register_template(template2, set_active=False)

        # List active only
        active_templates = registry.list_templates(active_only=True)
        assert len(active_templates) == 1
        assert active_templates[0].template_id == "template1"

    def test_list_templates_by_locale(self):
        """Test listing templates by locale."""
        registry = TemplateRegistry()

        # Register English template
        template_en = TemplateVersion(
            template_id="template1",
            version="1.0.0",
            name="Template 1 EN",
            subject_template="Subject EN",
            html_template="<p>HTML EN</p>",
            text_template="Text EN",
            locale="en_US",
        )
        registry.register_template(template_en)

        # Register Spanish template
        template_es = TemplateVersion(
            template_id="template2",
            version="1.0.0",
            name="Template 2 ES",
            subject_template="Subject ES",
            html_template="<p>HTML ES</p>",
            text_template="Text ES",
            locale="es_ES",
        )
        registry.register_template(template_es)

        # List by locale
        en_templates = registry.list_templates(locale="en_US")
        assert len(en_templates) == 1
        assert en_templates[0].locale == "en_US"

    def test_list_templates_by_tags(self):
        """Test listing templates by tags."""
        registry = TemplateRegistry()

        template1 = TemplateVersion(
            template_id="template1",
            version="1.0.0",
            name="Template 1",
            subject_template="Subject 1",
            html_template="<p>HTML 1</p>",
            text_template="Text 1",
            tags=["urgent", "notification"],
        )
        registry.register_template(template1)

        template2 = TemplateVersion(
            template_id="template2",
            version="1.0.0",
            name="Template 2",
            subject_template="Subject 2",
            html_template="<p>HTML 2</p>",
            text_template="Text 2",
            tags=["reminder", "notification"],
        )
        registry.register_template(template2)

        # List by tag
        urgent_templates = registry.list_templates(tags=["urgent"])
        assert len(urgent_templates) == 1
        assert urgent_templates[0].template_id == "template1"

        # List by multiple tags (any match)
        notification_templates = registry.list_templates(tags=["notification"])
        assert len(notification_templates) == 2

    def test_delete_version(self):
        """Test deleting a template version."""
        registry = TemplateRegistry()

        template = TemplateVersion(
            template_id="test_template",
            version="1.0.0",
            name="Test Template",
            subject_template="Subject",
            html_template="<p>HTML</p>",
            text_template="Text",
        )
        registry.register_template(template)

        # Delete the version
        success = registry.delete_version("test_template", "1.0.0")
        assert success is True

        # Should not be retrievable
        retrieved = registry.get_template("test_template", version="1.0.0")
        assert retrieved is None

    def test_get_template_registry_singleton(self):
        """Test that get_template_registry returns singleton."""
        registry1 = get_template_registry()
        registry2 = get_template_registry()

        assert registry1 is registry2

    def test_register_template_invalid_syntax(self):
        """Test that registering template with invalid syntax raises error."""
        registry = TemplateRegistry()

        template = TemplateVersion(
            template_id="bad_template",
            version="1.0.0",
            name="Bad Template",
            subject_template="Bad {{ syntax",  # Invalid
            html_template="<p>HTML</p>",
            text_template="Text",
        )

        with pytest.raises(ValueError) as exc_info:
            registry.register_template(template)

        assert "validation failed" in str(exc_info.value).lower()
