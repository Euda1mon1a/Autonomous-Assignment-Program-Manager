"""Tests for email notification schemas (Pydantic validation and field_validator)."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.email import (
    EmailLogBase,
    EmailLogCreate,
    EmailLogUpdate,
    EmailLogListResponse,
    EmailTemplateBase,
    EmailTemplateCreate,
    EmailTemplateUpdate,
    EmailTemplateListResponse,
    EmailTemplateSummary,
    EmailSendRequest,
)


# ===========================================================================
# EmailLogBase Tests
# ===========================================================================


class TestEmailLogBase:
    def _valid_kwargs(self):
        return {
            "recipient_email": "test@example.com",
            "subject": "Schedule Update",
        }

    def test_valid_minimal(self):
        r = EmailLogBase(**self._valid_kwargs())
        assert r.body_html is None
        assert r.body_text is None

    def test_full(self):
        r = EmailLogBase(
            recipient_email="test@example.com",
            subject="Schedule Changed",
            body_html="<p>Your schedule has been updated.</p>",
            body_text="Your schedule has been updated.",
        )
        assert r.body_html is not None

    # --- recipient_email: EmailStr ---

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            EmailLogBase(recipient_email="not-an-email", subject="Test")

    def test_missing_domain(self):
        with pytest.raises(ValidationError):
            EmailLogBase(recipient_email="user@", subject="Test")

    # --- subject field_validator (non-empty, <=500) ---

    def test_subject_empty(self):
        with pytest.raises(ValidationError):
            EmailLogBase(recipient_email="test@example.com", subject="")

    def test_subject_whitespace_only(self):
        with pytest.raises(ValidationError):
            EmailLogBase(recipient_email="test@example.com", subject="   ")

    def test_subject_too_long(self):
        with pytest.raises(ValidationError):
            EmailLogBase(recipient_email="test@example.com", subject="x" * 501)

    def test_subject_max_length(self):
        r = EmailLogBase(recipient_email="test@example.com", subject="x" * 500)
        assert len(r.subject) == 500


# ===========================================================================
# EmailLogCreate Tests
# ===========================================================================


class TestEmailLogCreate:
    def test_valid(self):
        r = EmailLogCreate(
            recipient_email="test@example.com",
            subject="Test",
        )
        assert r.notification_id is None
        assert r.template_id is None

    def test_with_ids(self):
        r = EmailLogCreate(
            recipient_email="test@example.com",
            subject="Test",
            notification_id=uuid4(),
            template_id=uuid4(),
        )
        assert r.notification_id is not None


# ===========================================================================
# EmailLogUpdate Tests
# ===========================================================================


class TestEmailLogUpdate:
    def test_all_none(self):
        r = EmailLogUpdate()
        assert r.status is None
        assert r.error_message is None
        assert r.sent_at is None
        assert r.retry_count is None

    # --- status field_validator ---

    def test_valid_statuses(self):
        for s in ["queued", "sent", "failed", "bounced"]:
            r = EmailLogUpdate(status=s)
            assert r.status == s

    def test_status_none_allowed(self):
        r = EmailLogUpdate(status=None)
        assert r.status is None

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            EmailLogUpdate(status="delivered")

    # --- retry_count field_validator (>=0) ---

    def test_retry_count_zero(self):
        r = EmailLogUpdate(retry_count=0)
        assert r.retry_count == 0

    def test_retry_count_positive(self):
        r = EmailLogUpdate(retry_count=5)
        assert r.retry_count == 5

    def test_retry_count_negative(self):
        with pytest.raises(ValidationError):
            EmailLogUpdate(retry_count=-1)


# ===========================================================================
# EmailLogListResponse Tests
# ===========================================================================


class TestEmailLogListResponse:
    def test_valid(self):
        r = EmailLogListResponse(items=[], total=0)
        assert r.items == []


# ===========================================================================
# EmailTemplateBase Tests
# ===========================================================================


class TestEmailTemplateBase:
    def _valid_kwargs(self):
        return {
            "name": "Schedule Change",
            "template_type": "schedule_change",
            "subject_template": "Your schedule has changed - {{date}}",
            "body_html_template": "<p>Hello {{name}}</p>",
            "body_text_template": "Hello {{name}}",
        }

    def test_valid(self):
        r = EmailTemplateBase(**self._valid_kwargs())
        assert r.is_active is True

    # --- name field_validator (non-empty, <=100) ---

    def test_name_empty(self):
        kw = self._valid_kwargs()
        kw["name"] = ""
        with pytest.raises(ValidationError):
            EmailTemplateBase(**kw)

    def test_name_whitespace_only(self):
        kw = self._valid_kwargs()
        kw["name"] = "   "
        with pytest.raises(ValidationError):
            EmailTemplateBase(**kw)

    def test_name_too_long(self):
        kw = self._valid_kwargs()
        kw["name"] = "x" * 101
        with pytest.raises(ValidationError):
            EmailTemplateBase(**kw)

    # --- template_type field_validator ---

    def test_all_valid_template_types(self):
        for tt in [
            "schedule_change",
            "swap_notification",
            "certification_expiry",
            "absence_reminder",
            "compliance_alert",
        ]:
            kw = self._valid_kwargs()
            kw["template_type"] = tt
            r = EmailTemplateBase(**kw)
            assert r.template_type == tt

    def test_invalid_template_type(self):
        kw = self._valid_kwargs()
        kw["template_type"] = "marketing"
        with pytest.raises(ValidationError):
            EmailTemplateBase(**kw)

    # --- subject_template field_validator (non-empty, <=500) ---

    def test_subject_template_empty(self):
        kw = self._valid_kwargs()
        kw["subject_template"] = ""
        with pytest.raises(ValidationError):
            EmailTemplateBase(**kw)

    def test_subject_template_too_long(self):
        kw = self._valid_kwargs()
        kw["subject_template"] = "x" * 501
        with pytest.raises(ValidationError):
            EmailTemplateBase(**kw)

    # --- body_html_template / body_text_template field_validator (non-empty) ---

    def test_body_html_template_empty(self):
        kw = self._valid_kwargs()
        kw["body_html_template"] = ""
        with pytest.raises(ValidationError):
            EmailTemplateBase(**kw)

    def test_body_text_template_empty(self):
        kw = self._valid_kwargs()
        kw["body_text_template"] = ""
        with pytest.raises(ValidationError):
            EmailTemplateBase(**kw)

    def test_body_html_whitespace_only(self):
        kw = self._valid_kwargs()
        kw["body_html_template"] = "   "
        with pytest.raises(ValidationError):
            EmailTemplateBase(**kw)


# ===========================================================================
# EmailTemplateCreate Tests
# ===========================================================================


class TestEmailTemplateCreate:
    def test_valid(self):
        r = EmailTemplateCreate(
            name="Test",
            template_type="schedule_change",
            subject_template="Subject",
            body_html_template="<p>Body</p>",
            body_text_template="Body",
        )
        assert r.created_by_id is None


# ===========================================================================
# EmailTemplateUpdate Tests
# ===========================================================================


class TestEmailTemplateUpdate:
    def test_all_none(self):
        r = EmailTemplateUpdate()
        assert r.name is None
        assert r.template_type is None
        assert r.subject_template is None
        assert r.body_html_template is None
        assert r.body_text_template is None
        assert r.is_active is None

    # --- template_type field_validator (None allowed) ---

    def test_template_type_valid(self):
        r = EmailTemplateUpdate(template_type="swap_notification")
        assert r.template_type == "swap_notification"

    def test_template_type_none_allowed(self):
        r = EmailTemplateUpdate(template_type=None)
        assert r.template_type is None

    def test_template_type_invalid(self):
        with pytest.raises(ValidationError):
            EmailTemplateUpdate(template_type="marketing")


# ===========================================================================
# EmailTemplateListResponse Tests
# ===========================================================================


class TestEmailTemplateListResponse:
    def test_valid(self):
        r = EmailTemplateListResponse(items=[], total=0)
        assert r.items == []


# ===========================================================================
# EmailTemplateSummary Tests
# ===========================================================================


class TestEmailTemplateSummary:
    def test_valid(self):
        r = EmailTemplateSummary(
            id=uuid4(),
            name="Swap Notification",
            template_type="swap_notification",
            is_active=True,
        )
        assert r.is_active is True


# ===========================================================================
# EmailSendRequest Tests
# ===========================================================================


class TestEmailSendRequest:
    def test_valid_minimal(self):
        r = EmailSendRequest(
            recipient_email="test@example.com",
            subject="Test Email",
        )
        assert r.body_html is None
        assert r.body_text is None
        assert r.template_id is None
        assert r.template_variables is None

    # --- subject field_validator (non-empty, <=500) ---

    def test_subject_empty(self):
        with pytest.raises(ValidationError):
            EmailSendRequest(recipient_email="test@example.com", subject="")

    def test_subject_too_long(self):
        with pytest.raises(ValidationError):
            EmailSendRequest(recipient_email="test@example.com", subject="x" * 501)

    # --- recipient_email: EmailStr ---

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            EmailSendRequest(recipient_email="bad", subject="Test")

    def test_with_template(self):
        r = EmailSendRequest(
            recipient_email="test@example.com",
            subject="Test",
            template_id=uuid4(),
            template_variables={"name": "Dr. Smith"},
        )
        assert r.template_variables is not None
