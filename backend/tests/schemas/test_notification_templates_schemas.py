"""Tests for notification template schemas (Field bounds, field_validators, defaults, patterns)."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.notification_templates import (
    TemplateVariableSchema,
    TemplateCreateSchema,
    TemplateUpdateSchema,
    TemplateVersionSchema,
    TemplateListItemSchema,
    TemplateRenderRequestSchema,
    TemplateRenderResponseSchema,
    TemplatePreviewRequestSchema,
    TemplatePreviewResponseSchema,
    TemplateValidationRequestSchema,
    TemplateValidationResponseSchema,
    TemplateActivateRequestSchema,
    TemplateVersionListSchema,
    TemplateErrorSchema,
)


# ── TemplateVariableSchema ──────────────────────────────────────────────


class TestTemplateVariableSchema:
    def test_defaults(self):
        r = TemplateVariableSchema(name="recipient_name")
        assert r.description == ""
        assert r.required is True
        assert r.default_value is None
        assert r.example_value is None

    # --- name min_length=1, max_length=100 ---

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            TemplateVariableSchema(name="")

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            TemplateVariableSchema(name="x" * 101)

    # --- description max_length=500 ---

    def test_description_too_long(self):
        with pytest.raises(ValidationError):
            TemplateVariableSchema(name="test", description="x" * 501)


# ── TemplateCreateSchema ────────────────────────────────────────────────


class TestTemplateCreateSchema:
    def test_defaults(self):
        r = TemplateCreateSchema(
            template_id="welcome_email",
            name="Welcome Email",
            subject_template="Welcome {{ name }}",
            html_template="<h1>Welcome</h1>",
            text_template="Welcome",
        )
        assert r.description == ""
        assert r.variables == []
        assert r.locale == "en_US"
        assert r.tags == []
        assert r.metadata == {}

    # --- template_id min_length=1, max_length=100 ---

    def test_template_id_empty(self):
        with pytest.raises(ValidationError):
            TemplateCreateSchema(
                template_id="",
                name="Test",
                subject_template="subj",
                html_template="html",
                text_template="text",
            )

    # --- template_id validator (alphanumeric + underscore + hyphen) ---

    def test_template_id_valid(self):
        r = TemplateCreateSchema(
            template_id="my-template_v2",
            name="Test",
            subject_template="subj",
            html_template="html",
            text_template="text",
        )
        assert r.template_id == "my-template_v2"

    def test_template_id_lowercased(self):
        r = TemplateCreateSchema(
            template_id="MY_TEMPLATE",
            name="Test",
            subject_template="subj",
            html_template="html",
            text_template="text",
        )
        assert r.template_id == "my_template"

    def test_template_id_invalid_chars(self):
        with pytest.raises(ValidationError, match="alphanumeric"):
            TemplateCreateSchema(
                template_id="my template!",
                name="Test",
                subject_template="subj",
                html_template="html",
                text_template="text",
            )

    # --- locale validator (xx_YY format) ---

    def test_locale_valid(self):
        r = TemplateCreateSchema(
            template_id="test",
            name="Test",
            subject_template="subj",
            html_template="html",
            text_template="text",
            locale="en_US",
        )
        assert r.locale == "en_US"

    def test_locale_invalid_format(self):
        with pytest.raises(ValidationError, match="xx_YY"):
            TemplateCreateSchema(
                template_id="test",
                name="Test",
                subject_template="subj",
                html_template="html",
                text_template="text",
                locale="eng_USA",
            )

    # --- name min_length=1, max_length=200 ---

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            TemplateCreateSchema(
                template_id="test",
                name="",
                subject_template="subj",
                html_template="html",
                text_template="text",
            )

    # --- subject_template max_length=500 ---

    def test_subject_too_long(self):
        with pytest.raises(ValidationError):
            TemplateCreateSchema(
                template_id="test",
                name="Test",
                subject_template="x" * 501,
                html_template="html",
                text_template="text",
            )


# ── TemplateUpdateSchema ────────────────────────────────────────────────


class TestTemplateUpdateSchema:
    def test_all_none(self):
        r = TemplateUpdateSchema()
        assert r.name is None
        assert r.description is None
        assert r.subject_template is None
        assert r.html_template is None
        assert r.text_template is None
        assert r.variables is None
        assert r.locale is None
        assert r.tags is None
        assert r.metadata is None
        assert r.version_increment == "patch"

    # --- version_increment pattern: major|minor|patch ---

    def test_version_increment_major(self):
        r = TemplateUpdateSchema(version_increment="major")
        assert r.version_increment == "major"

    def test_version_increment_minor(self):
        r = TemplateUpdateSchema(version_increment="minor")
        assert r.version_increment == "minor"

    def test_version_increment_invalid(self):
        with pytest.raises(ValidationError):
            TemplateUpdateSchema(version_increment="hotfix")

    def test_name_bounds_on_update(self):
        with pytest.raises(ValidationError):
            TemplateUpdateSchema(name="")


# ── TemplateVersionSchema ───────────────────────────────────────────────


class TestTemplateVersionSchema:
    def test_valid(self):
        r = TemplateVersionSchema(
            id=uuid4(),
            template_id="welcome",
            version="1.0.0",
            name="Welcome",
            description="Welcome email",
            subject_template="Welcome {{ name }}",
            html_template="<h1>Hi</h1>",
            text_template="Hi",
            variables=["name"],
            locale="en_US",
            is_active=True,
            created_at=datetime(2026, 1, 1),
            tags=["onboarding"],
            metadata={},
        )
        assert r.created_by is None
        assert r.is_active is True


# ── TemplateListItemSchema ──────────────────────────────────────────────


class TestTemplateListItemSchema:
    def test_valid(self):
        r = TemplateListItemSchema(
            template_id="welcome",
            name="Welcome",
            description="Welcome email",
            version="1.0.0",
            locale="en_US",
            tags=[],
            is_active=True,
            created_at=datetime(2026, 1, 1),
        )
        assert r.template_id == "welcome"


# ── TemplateRenderRequestSchema ─────────────────────────────────────────


class TestTemplateRenderRequestSchema:
    def test_defaults(self):
        r = TemplateRenderRequestSchema(template_id="welcome")
        assert r.version is None
        assert r.locale is None
        assert r.context == {}

    def test_template_id_empty(self):
        with pytest.raises(ValidationError):
            TemplateRenderRequestSchema(template_id="")


# ── TemplateRenderResponseSchema ────────────────────────────────────────


class TestTemplateRenderResponseSchema:
    def test_valid(self):
        r = TemplateRenderResponseSchema(
            template_id="welcome",
            version="1.0.0",
            subject="Welcome Dr. Smith",
            html="<h1>Welcome</h1>",
            text="Welcome",
            locale="en_US",
        )
        assert r.subject == "Welcome Dr. Smith"


# ── TemplatePreviewRequestSchema ────────────────────────────────────────


class TestTemplatePreviewRequestSchema:
    def test_defaults(self):
        r = TemplatePreviewRequestSchema(
            subject_template="Subj",
            html_template="<p>Hi</p>",
            text_template="Hi",
        )
        assert r.sample_context == {}

    def test_subject_too_long(self):
        with pytest.raises(ValidationError):
            TemplatePreviewRequestSchema(
                subject_template="x" * 501,
                html_template="html",
                text_template="text",
            )


# ── TemplatePreviewResponseSchema ───────────────────────────────────────


class TestTemplatePreviewResponseSchema:
    def test_defaults(self):
        r = TemplatePreviewResponseSchema(subject="S", html="H", text="T")
        assert r.warnings == []


# ── TemplateValidationRequestSchema ─────────────────────────────────────


class TestTemplateValidationRequestSchema:
    def test_defaults(self):
        r = TemplateValidationRequestSchema(
            subject_template="S", html_template="H", text_template="T"
        )
        assert r.required_variables == []


# ── TemplateValidationResponseSchema ────────────────────────────────────


class TestTemplateValidationResponseSchema:
    def test_defaults(self):
        r = TemplateValidationResponseSchema(is_valid=True)
        assert r.errors == []
        assert r.warnings == []
        assert r.detected_variables == []


# ── TemplateActivateRequestSchema ───────────────────────────────────────


class TestTemplateActivateRequestSchema:
    def test_valid(self):
        r = TemplateActivateRequestSchema(template_id="welcome", version="1.0.0")
        assert r.template_id == "welcome"

    def test_template_id_empty(self):
        with pytest.raises(ValidationError):
            TemplateActivateRequestSchema(template_id="", version="1.0.0")

    def test_version_empty(self):
        with pytest.raises(ValidationError):
            TemplateActivateRequestSchema(template_id="welcome", version="")


# ── TemplateVersionListSchema ───────────────────────────────────────────


class TestTemplateVersionListSchema:
    def test_valid(self):
        r = TemplateVersionListSchema(template_id="welcome", versions=[])
        assert r.versions == []


# ── TemplateErrorSchema ─────────────────────────────────────────────────


class TestTemplateErrorSchema:
    def test_defaults(self):
        r = TemplateErrorSchema(error="not_found", message="Template not found")
        assert r.field is None
        assert r.details == {}
