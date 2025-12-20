"""Tests for email service."""

import os
from datetime import date, timedelta
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest

from app.models.certification import CertificationType, PersonCertification
from app.models.person import Person
from app.services.email_service import EmailConfig, EmailService


class TestEmailConfig:
    """Test suite for EmailConfig."""

    def test_default_initialization(self):
        """Test EmailConfig with default parameters."""
        config = EmailConfig()

        assert config.host == "localhost"
        assert config.port == 587
        assert config.user is None
        assert config.password is None
        assert config.from_email == "noreply@hospital.org"
        assert config.from_name == "Residency Scheduler"
        assert config.use_tls is True
        assert config.enabled is True

    def test_custom_initialization(self):
        """Test EmailConfig with custom parameters."""
        config = EmailConfig(
            host="smtp.example.com",
            port=465,
            user="user@example.com",
            password="secret123",
            from_email="scheduler@example.com",
            from_name="Custom Scheduler",
            use_tls=False,
            enabled=False,
        )

        assert config.host == "smtp.example.com"
        assert config.port == 465
        assert config.user == "user@example.com"
        assert config.password == "secret123"
        assert config.from_email == "scheduler@example.com"
        assert config.from_name == "Custom Scheduler"
        assert config.use_tls is False
        assert config.enabled is False

    def test_from_env_with_defaults(self):
        """Test EmailConfig.from_env() with default values."""
        with patch.dict(os.environ, {}, clear=True):
            config = EmailConfig.from_env()

            assert config.host == "localhost"
            assert config.port == 587
            assert config.user is None
            assert config.password is None
            assert config.from_email == "noreply@hospital.org"
            assert config.from_name == "Residency Scheduler"
            assert config.use_tls is True
            assert config.enabled is True

    def test_from_env_with_custom_values(self):
        """Test EmailConfig.from_env() with custom environment variables."""
        env_vars = {
            "SMTP_HOST": "smtp.gmail.com",
            "SMTP_PORT": "465",
            "SMTP_USER": "test@gmail.com",
            "SMTP_PASSWORD": "mypassword",
            "SMTP_FROM_EMAIL": "noreply@example.com",
            "SMTP_FROM_NAME": "Test Mailer",
            "SMTP_USE_TLS": "false",
            "SMTP_ENABLED": "false",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = EmailConfig.from_env()

            assert config.host == "smtp.gmail.com"
            assert config.port == 465
            assert config.user == "test@gmail.com"
            assert config.password == "mypassword"
            assert config.from_email == "noreply@example.com"
            assert config.from_name == "Test Mailer"
            assert config.use_tls is False
            assert config.enabled is False

    def test_from_env_with_tls_enabled_variations(self):
        """Test EmailConfig.from_env() with various TLS enabled values."""
        # Test "true"
        with patch.dict(os.environ, {"SMTP_USE_TLS": "true"}, clear=True):
            config = EmailConfig.from_env()
            assert config.use_tls is True

        # Test "TRUE"
        with patch.dict(os.environ, {"SMTP_USE_TLS": "TRUE"}, clear=True):
            config = EmailConfig.from_env()
            assert config.use_tls is True

        # Test "false"
        with patch.dict(os.environ, {"SMTP_USE_TLS": "false"}, clear=True):
            config = EmailConfig.from_env()
            assert config.use_tls is False

        # Test "FALSE"
        with patch.dict(os.environ, {"SMTP_USE_TLS": "FALSE"}, clear=True):
            config = EmailConfig.from_env()
            assert config.use_tls is False

        # Test other values (should be False)
        with patch.dict(os.environ, {"SMTP_USE_TLS": "yes"}, clear=True):
            config = EmailConfig.from_env()
            assert config.use_tls is False

    def test_from_env_with_enabled_variations(self):
        """Test EmailConfig.from_env() with various enabled values."""
        # Test "true"
        with patch.dict(os.environ, {"SMTP_ENABLED": "true"}, clear=True):
            config = EmailConfig.from_env()
            assert config.enabled is True

        # Test "false"
        with patch.dict(os.environ, {"SMTP_ENABLED": "false"}, clear=True):
            config = EmailConfig.from_env()
            assert config.enabled is False


class TestEmailServiceSendEmail:
    """Test suite for EmailService.send_email()."""

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_email_success(self, mock_smtp):
        """Test sending email successfully."""
        # Setup mock
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        config = EmailConfig(
            host="smtp.example.com",
            port=587,
            user="user@example.com",
            password="password123",
            from_email="sender@example.com",
            from_name="Test Sender",
        )
        service = EmailService(config)

        # Send email
        result = service.send_email(
            to_email="recipient@example.com",
            subject="Test Subject",
            body_html="<h1>Test HTML</h1>",
            body_text="Test Text",
        )

        # Assertions
        assert result is True
        mock_smtp.assert_called_once_with("smtp.example.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user@example.com", "password123")
        mock_server.sendmail.assert_called_once()

        # Verify sendmail was called with correct arguments
        call_args = mock_server.sendmail.call_args
        assert call_args[0][0] == "sender@example.com"
        assert call_args[0][1] == "recipient@example.com"
        assert "Test Subject" in call_args[0][2]

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_email_without_tls(self, mock_smtp):
        """Test sending email without TLS."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        config = EmailConfig(use_tls=False)
        service = EmailService(config)

        result = service.send_email(
            to_email="recipient@example.com",
            subject="Test",
            body_html="<p>Test</p>",
        )

        assert result is True
        mock_server.starttls.assert_not_called()

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_email_without_auth(self, mock_smtp):
        """Test sending email without authentication."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        config = EmailConfig(user=None, password=None)
        service = EmailService(config)

        result = service.send_email(
            to_email="recipient@example.com",
            subject="Test",
            body_html="<p>Test</p>",
        )

        assert result is True
        mock_server.login.assert_not_called()

    def test_send_email_when_disabled(self):
        """Test sending email when SMTP is disabled."""
        config = EmailConfig(enabled=False)
        service = EmailService(config)

        result = service.send_email(
            to_email="recipient@example.com",
            subject="Test",
            body_html="<p>Test</p>",
        )

        # Should return True but not actually send
        assert result is True

    def test_send_email_with_empty_recipient(self):
        """Test sending email with empty recipient."""
        config = EmailConfig()
        service = EmailService(config)

        result = service.send_email(
            to_email="",
            subject="Test",
            body_html="<p>Test</p>",
        )

        assert result is False

    def test_send_email_with_none_recipient(self):
        """Test sending email with None recipient."""
        config = EmailConfig()
        service = EmailService(config)

        result = service.send_email(
            to_email=None,  # type: ignore
            subject="Test",
            body_html="<p>Test</p>",
        )

        assert result is False

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_email_smtp_exception(self, mock_smtp):
        """Test handling SMTP exceptions."""
        mock_smtp.side_effect = Exception("SMTP connection failed")

        config = EmailConfig()
        service = EmailService(config)

        result = service.send_email(
            to_email="recipient@example.com",
            subject="Test",
            body_html="<p>Test</p>",
        )

        assert result is False

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_email_html_only(self, mock_smtp):
        """Test sending email with HTML only (no text)."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        config = EmailConfig()
        service = EmailService(config)

        result = service.send_email(
            to_email="recipient@example.com",
            subject="Test",
            body_html="<h1>HTML Only</h1>",
            body_text=None,
        )

        assert result is True
        mock_server.sendmail.assert_called_once()


class TestEmailServiceCertificationReminder:
    """Test suite for EmailService.send_certification_reminder()."""

    def create_person_with_cert(
        self,
        days_until_expiration: int,
        email: str | None = "test@example.com",
    ) -> tuple[Person, PersonCertification]:
        """Helper to create a person with certification."""
        person = Person(
            id=uuid4(),
            name="Dr. Test Person",
            type="faculty",
            email=email,
        )

        cert_type = CertificationType(
            id=uuid4(),
            name="BLS",
            full_name="Basic Life Support",
        )

        cert = PersonCertification(
            id=uuid4(),
            person=person,
            certification_type=cert_type,
            issued_date=date.today() - timedelta(days=365),
            expiration_date=date.today() + timedelta(days=days_until_expiration),
        )

        return person, cert

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_reminder_7_days_urgent(self, mock_smtp):
        """Test sending reminder for certification expiring in 7 days (URGENT)."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        person, cert = self.create_person_with_cert(7)
        service = EmailService(EmailConfig())

        result = service.send_certification_reminder(person, cert, 7)

        assert result is True
        mock_server.sendmail.assert_called_once()

        # Verify email content
        call_args = mock_server.sendmail.call_args[0]
        email_content = call_args[2]
        assert "[URGENT]" in email_content
        assert "7 days" in email_content
        assert "Dr. Test Person" in email_content
        assert "Basic Life Support" in email_content
        assert "#dc3545" in email_content  # Red color

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_reminder_30_days_action_required(self, mock_smtp):
        """Test sending reminder for certification expiring in 30 days (ACTION REQUIRED)."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        person, cert = self.create_person_with_cert(30)
        service = EmailService(EmailConfig())

        result = service.send_certification_reminder(person, cert, 30)

        assert result is True

        # Verify email content
        call_args = mock_server.sendmail.call_args[0]
        email_content = call_args[2]
        assert "[ACTION REQUIRED]" in email_content
        assert "30 days" in email_content
        assert "#fd7e14" in email_content  # Orange color

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_reminder_90_days_reminder(self, mock_smtp):
        """Test sending reminder for certification expiring in 90 days (REMINDER)."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        person, cert = self.create_person_with_cert(90)
        service = EmailService(EmailConfig())

        result = service.send_certification_reminder(person, cert, 90)

        assert result is True

        # Verify email content
        call_args = mock_server.sendmail.call_args[0]
        email_content = call_args[2]
        assert "[REMINDER]" in email_content
        assert "90 days" in email_content
        assert "#ffc107" in email_content  # Yellow color

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_reminder_180_days_notice(self, mock_smtp):
        """Test sending reminder for certification expiring in 180 days (NOTICE)."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        person, cert = self.create_person_with_cert(180)
        service = EmailService(EmailConfig())

        result = service.send_certification_reminder(person, cert, 180)

        assert result is True

        # Verify email content
        call_args = mock_server.sendmail.call_args[0]
        email_content = call_args[2]
        assert "[NOTICE]" in email_content
        assert "180 days" in email_content
        assert "#17a2b8" in email_content  # Blue color

    def test_send_reminder_missing_email(self):
        """Test sending reminder when person has no email."""
        person, cert = self.create_person_with_cert(7, email=None)
        service = EmailService(EmailConfig())

        result = service.send_certification_reminder(person, cert, 7)

        assert result is False

    def test_send_reminder_empty_email(self):
        """Test sending reminder when person has empty email."""
        person, cert = self.create_person_with_cert(7, email="")
        service = EmailService(EmailConfig())

        result = service.send_certification_reminder(person, cert, 7)

        assert result is False

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_reminder_includes_both_html_and_text(self, mock_smtp):
        """Test that reminder includes both HTML and text versions."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        person, cert = self.create_person_with_cert(30)
        service = EmailService(EmailConfig())

        result = service.send_certification_reminder(person, cert, 30)

        assert result is True

        # The email should contain both HTML and text
        call_args = mock_server.sendmail.call_args[0]
        email_content = call_args[2]
        assert "<!DOCTYPE html>" in email_content
        assert "Content-Type: text/plain" in email_content
        assert "Content-Type: text/html" in email_content

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_reminder_disabled_smtp(self, mock_smtp):
        """Test sending reminder when SMTP is disabled."""
        person, cert = self.create_person_with_cert(7)
        service = EmailService(EmailConfig(enabled=False))

        result = service.send_certification_reminder(person, cert, 7)

        # Should return True but not actually send
        assert result is True
        mock_smtp.assert_not_called()


class TestEmailServiceComplianceSummary:
    """Test suite for EmailService.send_compliance_summary()."""

    def create_cert_list(
        self,
        count: int,
        days_offset: int,
        name_prefix: str = "Person",
    ) -> list[PersonCertification]:
        """Helper to create a list of certifications."""
        certs = []
        for i in range(count):
            person = Person(
                id=uuid4(),
                name=f"Dr. {name_prefix} {i+1}",
                type="faculty",
                email=f"{name_prefix.lower()}{i+1}@example.com",
            )

            cert_type = CertificationType(
                id=uuid4(),
                name=f"CERT{i+1}",
                full_name=f"Certification Type {i+1}",
            )

            cert = PersonCertification(
                id=uuid4(),
                person=person,
                certification_type=cert_type,
                issued_date=date.today() - timedelta(days=365),
                expiration_date=date.today() + timedelta(days=days_offset),
            )

            certs.append(cert)

        return certs

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_compliance_summary_with_expiring_and_expired(self, mock_smtp):
        """Test sending compliance summary with both expiring and expired certs."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        expiring = self.create_cert_list(2, 30, "Expiring")
        expired = self.create_cert_list(1, -10, "Expired")

        service = EmailService(EmailConfig())
        result = service.send_compliance_summary(
            "admin@example.com",
            expiring,
            expired,
        )

        assert result is True
        mock_server.sendmail.assert_called_once()

        # Verify email content
        call_args = mock_server.sendmail.call_args[0]
        email_content = call_args[2]
        assert "Certification Compliance Summary" in email_content
        assert "Dr. Expiring 1" in email_content
        assert "Dr. Expiring 2" in email_content
        assert "Dr. Expired 1" in email_content
        assert "2 certifications are expiring" in email_content
        assert "1 certifications have EXPIRED" in email_content

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_compliance_summary_expiring_only(self, mock_smtp):
        """Test sending compliance summary with expiring certs only."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        expiring = self.create_cert_list(3, 60, "Expiring")

        service = EmailService(EmailConfig())
        result = service.send_compliance_summary(
            "admin@example.com",
            expiring,
            [],
        )

        assert result is True

        # Verify email content
        call_args = mock_server.sendmail.call_args[0]
        email_content = call_args[2]
        assert "3 certifications are expiring" in email_content
        assert "Dr. Expiring 1" in email_content
        assert "Dr. Expiring 2" in email_content
        assert "Dr. Expiring 3" in email_content
        # Should not show expired section
        assert "Expired Certifications" not in email_content or "Expired Certifications (0)" in email_content

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_compliance_summary_expired_only(self, mock_smtp):
        """Test sending compliance summary with expired certs only."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        expired = self.create_cert_list(2, -5, "Expired")

        service = EmailService(EmailConfig())
        result = service.send_compliance_summary(
            "admin@example.com",
            [],
            expired,
        )

        assert result is True

        # Verify email content
        call_args = mock_server.sendmail.call_args[0]
        email_content = call_args[2]
        assert "2 certifications have EXPIRED" in email_content
        assert "Dr. Expired 1" in email_content
        assert "Dr. Expired 2" in email_content
        assert "EXPIRED" in email_content

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_compliance_summary_empty_lists(self, mock_smtp):
        """Test sending compliance summary with no certs."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        service = EmailService(EmailConfig())
        result = service.send_compliance_summary(
            "admin@example.com",
            [],
            [],
        )

        assert result is True

        # Verify email content shows "all current"
        call_args = mock_server.sendmail.call_args[0]
        email_content = call_args[2]
        assert "All certifications are current!" in email_content

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_compliance_summary_includes_today_date(self, mock_smtp):
        """Test that compliance summary includes today's date."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        service = EmailService(EmailConfig())
        result = service.send_compliance_summary(
            "admin@example.com",
            [],
            [],
        )

        assert result is True

        # Verify today's date is in subject and body
        call_args = mock_server.sendmail.call_args[0]
        email_content = call_args[2]
        today_str = date.today().strftime("%B %d, %Y")
        assert today_str in email_content

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_compliance_summary_table_structure(self, mock_smtp):
        """Test that compliance summary has proper HTML table structure."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        expiring = self.create_cert_list(1, 30)

        service = EmailService(EmailConfig())
        result = service.send_compliance_summary(
            "admin@example.com",
            expiring,
            [],
        )

        assert result is True

        # Verify HTML structure
        call_args = mock_server.sendmail.call_args[0]
        email_content = call_args[2]
        assert "<table>" in email_content
        assert "<thead>" in email_content
        assert "<tbody>" in email_content
        assert "<th>Person</th>" in email_content
        assert "<th>Certification</th>" in email_content
        assert "<th>Expiration Date</th>" in email_content

    def test_send_compliance_summary_disabled_smtp(self):
        """Test sending compliance summary when SMTP is disabled."""
        service = EmailService(EmailConfig(enabled=False))
        result = service.send_compliance_summary(
            "admin@example.com",
            [],
            [],
        )

        # Should return True but not actually send
        assert result is True

    def test_send_compliance_summary_empty_recipient(self):
        """Test sending compliance summary with empty recipient."""
        service = EmailService(EmailConfig())
        result = service.send_compliance_summary(
            "",
            [],
            [],
        )

        assert result is False


class TestEmailServiceIntegration:
    """Integration tests for EmailService."""

    @patch("app.services.email_service.smtplib.SMTP")
    def test_service_uses_config_from_env(self, mock_smtp):
        """Test that EmailService uses config from environment."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        env_vars = {
            "SMTP_HOST": "smtp.test.com",
            "SMTP_PORT": "2525",
            "SMTP_FROM_EMAIL": "test@test.com",
            "SMTP_FROM_NAME": "Test Name",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            service = EmailService()  # Should load from env

            result = service.send_email(
                to_email="recipient@example.com",
                subject="Test",
                body_html="<p>Test</p>",
            )

            assert result is True
            mock_smtp.assert_called_once_with("smtp.test.com", 2525)

            # Check the From header
            call_args = mock_server.sendmail.call_args[0]
            email_content = call_args[2]
            assert "Test Name <test@test.com>" in email_content

    @patch("app.services.email_service.smtplib.SMTP")
    def test_multiple_emails_sent_successfully(self, mock_smtp):
        """Test sending multiple emails in sequence."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        service = EmailService(EmailConfig())

        # Send multiple emails
        result1 = service.send_email(
            "user1@example.com",
            "Subject 1",
            "<p>Body 1</p>",
        )
        result2 = service.send_email(
            "user2@example.com",
            "Subject 2",
            "<p>Body 2</p>",
        )

        assert result1 is True
        assert result2 is True
        assert mock_server.sendmail.call_count == 2
