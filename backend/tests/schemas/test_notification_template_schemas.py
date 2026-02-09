"""Tests for notification template schemas (Pydantic validation and field_validator coverage)."""

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


# ===========================================================================
# TemplateVariableSchema Tests
# ===========================================================================


class TestTemplateVariableSchema:
    def test_valid(self):
        r = TemplateVariableSchema(name="recipient_name")
        assert r.description == ""
        assert r.required is True
        assert r.default_value is None
        assert r.example_value is None

    def test_full(self):
        r = TemplateVariableSchema(
            name="status",
            description="Current swap status",
            required=False,
            default_value="pending",
            example_value="approved",
        )
        assert r.default_value == "pending"

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            TemplateVariableSchema(name="")

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            TemplateVariableSchema(name="x" * 101)

    def test_name_max_length(self):
        r = TemplateVariableSchema(name="x" * 100)
        assert len(r.name) == 100

    def test_description_too_long(self):
        with pytest.raises(ValidationError):
            TemplateVariableSchema(name="test", description="x" * 501)

    def test_description_max_length(self):
        r = TemplateVariableSchema(name="test", description="x" * 500)
        assert len(r.description) == 500


# ===========================================================================
# TemplateCreateSchema Tests
# ===========================================================================


class TestTemplateCreateSchema:
    def _valid_kwargs(self):
        return {
            "template_id": "swap_approved",
            "name": "Swap Approved",
            "subject_template": "Swap Request Approved",
            "html_template": "<p>Your swap has been approved</p>",
            "text_template": "Your swap has been approved",
        }

    def test_valid(self):
        r = TemplateCreateSchema(**self._valid_kwargs())
        assert r.description == ""
        assert r.variables == []
        assert r.locale == "en_US"
        assert r.tags == []
        assert r.metadata == {}

    # --- template_id field_validator ---

    def test_template_id_lowercased(self):
        kw = self._valid_kwargs()
        kw["template_id"] = "Swap_Approved"
        r = TemplateCreateSchema(**kw)
        assert r.template_id == "swap_approved"

    def test_template_id_alphanumeric_with_underscores(self):
        kw = self._valid_kwargs()
        kw["template_id"] = "swap_approved_v2"
        r = TemplateCreateSchema(**kw)
        assert r.template_id == "swap_approved_v2"

    def test_template_id_with_hyphens(self):
        kw = self._valid_kwargs()
        kw["template_id"] = "swap-approved"
        r = TemplateCreateSchema(**kw)
        assert r.template_id == "swap-approved"

    def test_template_id_invalid_chars(self):
        kw = self._valid_kwargs()
        kw["template_id"] = "swap approved!"
        with pytest.raises(ValidationError):
            TemplateCreateSchema(**kw)

    def test_template_id_special_chars(self):
        kw = self._valid_kwargs()
        kw["template_id"] = "swap@approved"
        with pytest.raises(ValidationError):
            TemplateCreateSchema(**kw)

    def test_template_id_empty(self):
        kw = self._valid_kwargs()
        kw["template_id"] = ""
        with pytest.raises(ValidationError):
            TemplateCreateSchema(**kw)

    def test_template_id_too_long(self):
        kw = self._valid_kwargs()
        kw["template_id"] = "a" * 101
        with pytest.raises(ValidationError):
            TemplateCreateSchema(**kw)

    # --- name constraints ---

    def test_name_empty(self):
        kw = self._valid_kwargs()
        kw["name"] = ""
        with pytest.raises(ValidationError):
            TemplateCreateSchema(**kw)

    def test_name_too_long(self):
        kw = self._valid_kwargs()
        kw["name"] = "x" * 201
        with pytest.raises(ValidationError):
            TemplateCreateSchema(**kw)

    # --- description constraints ---

    def test_description_too_long(self):
        kw = self._valid_kwargs()
        kw["description"] = "x" * 1001
        with pytest.raises(ValidationError):
            TemplateCreateSchema(**kw)

    # --- subject_template constraints ---

    def test_subject_template_empty(self):
        kw = self._valid_kwargs()
        kw["subject_template"] = ""
        with pytest.raises(ValidationError):
            TemplateCreateSchema(**kw)

    def test_subject_template_too_long(self):
        kw = self._valid_kwargs()
        kw["subject_template"] = "x" * 501
        with pytest.raises(ValidationError):
            TemplateCreateSchema(**kw)

    # --- html_template constraints ---

    def test_html_template_empty(self):
        kw = self._valid_kwargs()
        kw["html_template"] = ""
        with pytest.raises(ValidationError):
            TemplateCreateSchema(**kw)

    def test_html_template_too_long(self):
        kw = self._valid_kwargs()
        kw["html_template"] = "x" * 50001
        with pytest.raises(ValidationError):
            TemplateCreateSchema(**kw)

    # --- text_template constraints ---

    def test_text_template_empty(self):
        kw = self._valid_kwargs()
        kw["text_template"] = ""
        with pytest.raises(ValidationError):
            TemplateCreateSchema(**kw)

    def test_text_template_too_long(self):
        kw = self._valid_kwargs()
        kw["text_template"] = "x" * 50001
        with pytest.raises(ValidationError):
            TemplateCreateSchema(**kw)

    # --- locale field_validator ---

    def test_locale_default(self):
        r = TemplateCreateSchema(**self._valid_kwargs())
        assert r.locale == "en_US"

    def test_locale_valid_format(self):
        kw = self._valid_kwargs()
        kw["locale"] = "de_DE"
        r = TemplateCreateSchema(**kw)
        assert r.locale == "de_DE"

    def test_locale_invalid_format_three_parts(self):
        kw = self._valid_kwargs()
        kw["locale"] = "en_US_extra"
        with pytest.raises(ValidationError):
            TemplateCreateSchema(**kw)

    def test_locale_invalid_format_wrong_lengths(self):
        kw = self._valid_kwargs()
        kw["locale"] = "eng_U"
        with pytest.raises(ValidationError):
            TemplateCreateSchema(**kw)

    def test_locale_no_underscore_is_valid(self):
        kw = self._valid_kwargs()
        kw["locale"] = "en"
        r = TemplateCreateSchema(**kw)
        assert r.locale == "en"


# ===========================================================================
# TemplateUpdateSchema Tests
# ===========================================================================


class TestTemplateUpdateSchema:
    def test_all_defaults(self):
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

    # --- version_increment pattern ---

    def test_version_increment_valid(self):
        for vi in ["major", "minor", "patch"]:
            r = TemplateUpdateSchema(version_increment=vi)
            assert r.version_increment == vi

    def test_version_increment_invalid(self):
        with pytest.raises(ValidationError):
            TemplateUpdateSchema(version_increment="hotfix")

    def test_version_increment_uppercase(self):
        with pytest.raises(ValidationError):
            TemplateUpdateSchema(version_increment="Major")

    # --- name constraints ---

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            TemplateUpdateSchema(name="")

    def test_name_valid(self):
        r = TemplateUpdateSchema(name="Updated Template")
        assert r.name == "Updated Template"

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            TemplateUpdateSchema(name="x" * 201)

    # --- description constraints ---

    def test_description_too_long(self):
        with pytest.raises(ValidationError):
            TemplateUpdateSchema(description="x" * 1001)

    # --- subject_template constraints ---

    def test_subject_template_empty(self):
        with pytest.raises(ValidationError):
            TemplateUpdateSchema(subject_template="")

    def test_subject_template_too_long(self):
        with pytest.raises(ValidationError):
            TemplateUpdateSchema(subject_template="x" * 501)

    # --- html_template constraints ---

    def test_html_template_empty(self):
        with pytest.raises(ValidationError):
            TemplateUpdateSchema(html_template="")

    def test_html_template_too_long(self):
        with pytest.raises(ValidationError):
            TemplateUpdateSchema(html_template="x" * 50001)

    # --- text_template constraints ---

    def test_text_template_empty(self):
        with pytest.raises(ValidationError):
            TemplateUpdateSchema(text_template="")

    def test_text_template_too_long(self):
        with pytest.raises(ValidationError):
            TemplateUpdateSchema(text_template="x" * 50001)


# ===========================================================================
# TemplateVersionSchema Tests
# ===========================================================================


class TestTemplateVersionSchema:
    def test_valid(self):
        r = TemplateVersionSchema(
            id=uuid4(),
            template_id="swap_approved",
            version="1.0.0",
            name="Swap Approved",
            description="Notification for approved swaps",
            subject_template="Swap Approved",
            html_template="<p>Approved</p>",
            text_template="Approved",
            variables=["recipient"],
            locale="en_US",
            is_active=True,
            created_at=datetime.now(),
            tags=["swap"],
            metadata={"priority": "high"},
        )
        assert r.created_by is None

    def test_with_created_by(self):
        r = TemplateVersionSchema(
            id=uuid4(),
            template_id="test",
            version="1.0.0",
            name="Test",
            description="",
            subject_template="Test",
            html_template="<p>Test</p>",
            text_template="Test",
            variables=[],
            locale="en_US",
            is_active=False,
            created_at=datetime.now(),
            created_by="admin",
            tags=[],
            metadata={},
        )
        assert r.created_by == "admin"


# ===========================================================================
# TemplateListItemSchema Tests
# ===========================================================================


class TestTemplateListItemSchema:
    def test_valid(self):
        r = TemplateListItemSchema(
            template_id="swap_approved",
            name="Swap Approved",
            description="Notification for approved swaps",
            version="1.0.0",
            locale="en_US",
            tags=["swap"],
            is_active=True,
            created_at=datetime.now(),
        )
        assert r.template_id == "swap_approved"


# ===========================================================================
# TemplateRenderRequestSchema Tests
# ===========================================================================


class TestTemplateRenderRequestSchema:
    def test_valid(self):
        r = TemplateRenderRequestSchema(template_id="swap_approved")
        assert r.version is None
        assert r.locale is None
        assert r.context == {}

    def test_template_id_empty(self):
        with pytest.raises(ValidationError):
            TemplateRenderRequestSchema(template_id="")

    def test_template_id_too_long(self):
        with pytest.raises(ValidationError):
            TemplateRenderRequestSchema(template_id="a" * 101)

    def test_with_context(self):
        r = TemplateRenderRequestSchema(
            template_id="swap_approved",
            version="1.0.0",
            locale="en_US",
            context={"name": "Dr. Alpha"},
        )
        assert r.context["name"] == "Dr. Alpha"


# ===========================================================================
# TemplateRenderResponseSchema Tests
# ===========================================================================


class TestTemplateRenderResponseSchema:
    def test_valid(self):
        r = TemplateRenderResponseSchema(
            template_id="swap_approved",
            version="1.0.0",
            subject="Swap Approved",
            html="<p>Approved</p>",
            text="Approved",
            locale="en_US",
        )
        assert r.template_id == "swap_approved"


# ===========================================================================
# TemplatePreviewRequestSchema Tests
# ===========================================================================


class TestTemplatePreviewRequestSchema:
    def test_valid(self):
        r = TemplatePreviewRequestSchema(
            subject_template="Subject",
            html_template="<p>HTML</p>",
            text_template="Text",
        )
        assert r.sample_context == {}

    def test_subject_template_empty(self):
        with pytest.raises(ValidationError):
            TemplatePreviewRequestSchema(
                subject_template="",
                html_template="<p>HTML</p>",
                text_template="Text",
            )

    def test_subject_template_too_long(self):
        with pytest.raises(ValidationError):
            TemplatePreviewRequestSchema(
                subject_template="x" * 501,
                html_template="<p>HTML</p>",
                text_template="Text",
            )

    def test_html_template_empty(self):
        with pytest.raises(ValidationError):
            TemplatePreviewRequestSchema(
                subject_template="Subject",
                html_template="",
                text_template="Text",
            )

    def test_html_template_too_long(self):
        with pytest.raises(ValidationError):
            TemplatePreviewRequestSchema(
                subject_template="Subject",
                html_template="x" * 50001,
                text_template="Text",
            )

    def test_text_template_empty(self):
        with pytest.raises(ValidationError):
            TemplatePreviewRequestSchema(
                subject_template="Subject",
                html_template="<p>HTML</p>",
                text_template="",
            )

    def test_text_template_too_long(self):
        with pytest.raises(ValidationError):
            TemplatePreviewRequestSchema(
                subject_template="Subject",
                html_template="<p>HTML</p>",
                text_template="x" * 50001,
            )


# ===========================================================================
# TemplatePreviewResponseSchema Tests
# ===========================================================================


class TestTemplatePreviewResponseSchema:
    def test_valid(self):
        r = TemplatePreviewResponseSchema(
            subject="Preview Subject",
            html="<p>Preview</p>",
            text="Preview",
        )
        assert r.warnings == []


# ===========================================================================
# TemplateValidationRequestSchema Tests
# ===========================================================================


class TestTemplateValidationRequestSchema:
    def test_valid(self):
        r = TemplateValidationRequestSchema(
            subject_template="Subject",
            html_template="<p>HTML</p>",
            text_template="Text",
        )
        assert r.required_variables == []

    def test_subject_template_empty(self):
        with pytest.raises(ValidationError):
            TemplateValidationRequestSchema(
                subject_template="",
                html_template="<p>HTML</p>",
                text_template="Text",
            )

    def test_subject_template_too_long(self):
        with pytest.raises(ValidationError):
            TemplateValidationRequestSchema(
                subject_template="x" * 501,
                html_template="<p>HTML</p>",
                text_template="Text",
            )

    def test_html_template_empty(self):
        with pytest.raises(ValidationError):
            TemplateValidationRequestSchema(
                subject_template="Subject",
                html_template="",
                text_template="Text",
            )

    def test_text_template_empty(self):
        with pytest.raises(ValidationError):
            TemplateValidationRequestSchema(
                subject_template="Subject",
                html_template="<p>HTML</p>",
                text_template="",
            )


# ===========================================================================
# TemplateValidationResponseSchema Tests
# ===========================================================================


class TestTemplateValidationResponseSchema:
    def test_valid(self):
        r = TemplateValidationResponseSchema(is_valid=True)
        assert r.errors == []
        assert r.warnings == []
        assert r.detected_variables == []

    def test_with_errors(self):
        r = TemplateValidationResponseSchema(
            is_valid=False,
            errors=["Missing variable: name"],
            detected_variables=["status"],
        )
        assert len(r.errors) == 1


# ===========================================================================
# TemplateActivateRequestSchema Tests
# ===========================================================================


class TestTemplateActivateRequestSchema:
    def test_valid(self):
        r = TemplateActivateRequestSchema(
            template_id="swap_approved",
            version="1.0.0",
        )
        assert r.template_id == "swap_approved"

    def test_template_id_empty(self):
        with pytest.raises(ValidationError):
            TemplateActivateRequestSchema(template_id="", version="1.0.0")

    def test_template_id_too_long(self):
        with pytest.raises(ValidationError):
            TemplateActivateRequestSchema(template_id="a" * 101, version="1.0.0")

    def test_version_empty(self):
        with pytest.raises(ValidationError):
            TemplateActivateRequestSchema(template_id="swap_approved", version="")

    def test_version_too_long(self):
        with pytest.raises(ValidationError):
            TemplateActivateRequestSchema(template_id="swap_approved", version="x" * 21)


# ===========================================================================
# TemplateVersionListSchema Tests
# ===========================================================================


class TestTemplateVersionListSchema:
    def test_valid(self):
        r = TemplateVersionListSchema(
            template_id="swap_approved",
            versions=[],
        )
        assert r.versions == []


# ===========================================================================
# TemplateErrorSchema Tests
# ===========================================================================


class TestTemplateErrorSchema:
    def test_valid(self):
        r = TemplateErrorSchema(
            error="not_found",
            message="Template not found",
        )
        assert r.field is None
        assert r.details == {}

    def test_with_field_and_details(self):
        r = TemplateErrorSchema(
            error="validation_error",
            message="Invalid template ID",
            field="template_id",
            details={"pattern": "alphanumeric"},
        )
        assert r.field == "template_id"
        assert r.details["pattern"] == "alphanumeric"
