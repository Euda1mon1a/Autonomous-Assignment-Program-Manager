"""Email service for sending notifications.

This service handles sending email notifications for:
- User invitation emails (new user onboarding)
- Password reset emails (self-service recovery)
- Certification expiration reminders (6 months, 3 months, 1 month, 2 weeks, 1 week)
- Compliance summary reports

Configuration is done via environment variables:
- SMTP_HOST: SMTP server hostname
- SMTP_PORT: SMTP server port (default: 587)
- SMTP_USER: SMTP username
- SMTP_PASSWORD: SMTP password
- SMTP_FROM_EMAIL: From email address
- SMTP_FROM_NAME: From name (default: "Residency Scheduler")
- SMTP_USE_TLS: Use TLS (default: True)
"""

import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import cast

from app.core.logging import get_logger
from app.models.certification import PersonCertification
from app.models.person import Person

logger = get_logger(__name__)


class EmailConfig:
    """Email configuration from environment variables."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 587,
        user: str | None = None,
        password: str | None = None,
        from_email: str = "noreply@hospital.org",
        from_name: str = "Residency Scheduler",
        use_tls: bool = True,
        enabled: bool = True,
    ) -> None:
        """Initialize email configuration.

        Args:
            host: SMTP server hostname.
            port: SMTP server port.
            user: SMTP authentication username (optional).
            password: SMTP authentication password (optional).
            from_email: Email address to use as sender.
            from_name: Display name for sender.
            use_tls: Whether to use TLS encryption.
            enabled: Whether email sending is enabled globally.
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.from_email = from_email
        self.from_name = from_name
        self.use_tls = use_tls
        self.enabled = enabled

    @classmethod
    def from_env(cls) -> "EmailConfig":
        """Load email configuration from environment variables.

        Reads the following environment variables:
        - SMTP_HOST: SMTP server hostname (default: localhost)
        - SMTP_PORT: SMTP server port (default: 587)
        - SMTP_USER: SMTP username (optional)
        - SMTP_PASSWORD: SMTP password (optional)
        - SMTP_FROM_EMAIL: From email address (default: noreply@hospital.org)
        - SMTP_FROM_NAME: From name (default: Residency Scheduler)
        - SMTP_USE_TLS: Use TLS (default: true)
        - SMTP_ENABLED: Enable email sending (default: true)

        Returns:
            EmailConfig instance populated from environment variables.
        """
        import os

        return cls(
            host=os.getenv("SMTP_HOST", "localhost"),
            port=int(os.getenv("SMTP_PORT", "587")),
            user=os.getenv("SMTP_USER"),
            password=os.getenv("SMTP_PASSWORD"),
            from_email=os.getenv("SMTP_FROM_EMAIL", "noreply@hospital.org"),
            from_name=os.getenv("SMTP_FROM_NAME", "Residency Scheduler"),
            use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
            enabled=os.getenv("SMTP_ENABLED", "true").lower() == "true",
        )


class EmailService:
    """Service for sending emails."""

    def __init__(self, config: EmailConfig | None = None) -> None:
        """Initialize email service.

        Args:
            config: Email configuration. If None, loads from environment variables.
        """
        self.config = config or EmailConfig.from_env()

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str | None = None,
    ) -> bool:
        """Send an email via SMTP.

        Args:
            to_email: Recipient email address.
            subject: Email subject line.
            body_html: HTML version of email body.
            body_text: Plain text version of email body (optional but recommended for accessibility).

        Returns:
            True if email was sent successfully, False otherwise.

        Note:
            If email is disabled in configuration, logs the message and returns True without sending.
            Always prefers HTML body, falls back to plain text if provided.
        """
        if not self.config.enabled:
            logger.info(f"Email disabled. Would send to [EMAIL REDACTED]: {subject}")
            return True

        if not to_email:
            logger.warning("No email address provided, skipping send")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.config.from_name} <{self.config.from_email}>"
            msg["To"] = to_email

            # Attach text and HTML versions
            if body_text:
                msg.attach(MIMEText(body_text, "plain"))
            msg.attach(MIMEText(body_html, "html"))

            # Connect and send
            with smtplib.SMTP(self.config.host, self.config.port) as server:
                if self.config.use_tls:
                    server.starttls()
                if self.config.user and self.config.password:
                    server.login(self.config.user, self.config.password)
                server.sendmail(self.config.from_email, to_email, msg.as_string())

            logger.info("Email sent successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_certification_reminder(
        self,
        person: Person,
        certification: PersonCertification,
        days_until_expiration: int,
    ) -> bool:
        """Send a certification expiration reminder email with urgency-based styling.

        Args:
            person: Person object with email address and name.
            certification: PersonCertification object containing expiration details.
            days_until_expiration: Number of days remaining until certification expires.

        Returns:
            True if email sent successfully, False if person has no email or send failed.

        Note:
            Urgency levels are determined by days remaining:
            - <= 7 days: URGENT (red)
            - <= 30 days: ACTION REQUIRED (orange)
            - <= 90 days: REMINDER (yellow)
            - > 90 days: NOTICE (blue)
        """
        if not person.email:
            logger.warning(f"No email for Person {person.id}, skipping reminder")
            return False

        cert_name = certification.certification_type.name
        cert_full_name = certification.certification_type.full_name or cert_name
        expiration_date = certification.expiration_date.strftime("%B %d, %Y")

        # Determine urgency level for styling
        if days_until_expiration <= 7:
            urgency = "URGENT"
            urgency_color = "#dc3545"  # Red
        elif days_until_expiration <= 30:
            urgency = "ACTION REQUIRED"
            urgency_color = "#fd7e14"  # Orange
        elif days_until_expiration <= 90:
            urgency = "REMINDER"
            urgency_color = "#ffc107"  # Yellow
        else:
            urgency = "NOTICE"
            urgency_color = "#17a2b8"  # Blue

        subject = f"[{urgency}] Your {cert_name} certification expires in {days_until_expiration} days"

        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {urgency_color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .details {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid {urgency_color}; }}
                .footer {{ padding: 15px; font-size: 12px; color: #666; text-align: center; }}
                .btn {{ display: inline-block; padding: 10px 20px; background-color: {urgency_color}; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{urgency}: Certification Expiring</h1>
                </div>
                <div class="content">
                    <p>Dear {person.name},</p>

                    <p>This is a reminder that your <strong>{cert_full_name} ({cert_name})</strong> certification
                    will expire in <strong>{days_until_expiration} days</strong>.</p>

                    <div class="details">
                        <p><strong>Certification:</strong> {cert_full_name} ({cert_name})</p>
                        <p><strong>Expiration Date:</strong> {expiration_date}</p>
                        <p><strong>Days Remaining:</strong> {days_until_expiration}</p>
                    </div>

                    <p>Please renew your certification before the expiration date to maintain compliance.</p>

                    <p>If you have already renewed, please update your records in the scheduling system.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from the Residency Scheduling System.</p>
                    <p>Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        body_text = f"""
{urgency}: Certification Expiring

Dear {person.name},

This is a reminder that your {cert_full_name} ({cert_name}) certification
will expire in {days_until_expiration} days.

Certification: {cert_full_name} ({cert_name})
Expiration Date: {expiration_date}
Days Remaining: {days_until_expiration}

Please renew your certification before the expiration date to maintain compliance.

If you have already renewed, please update your records in the scheduling system.

---
This is an automated message from the Residency Scheduling System.
        """

        return self.send_email(cast(str, person.email), subject, body_html, body_text)

    def send_compliance_summary(
        self,
        to_email: str,
        expiring_certs: list[PersonCertification],
        expired_certs: list[PersonCertification],
    ) -> bool:
        """Send a compliance summary email to administrators.

        Generates a formatted HTML email with tables showing expired and expiring
        certifications. Used for daily/weekly compliance reports.

        Args:
            to_email: Administrator email address to receive the summary.
            expiring_certs: List of certifications expiring within 6 months.
            expired_certs: List of certifications that have already expired.

        Returns:
            True if email sent successfully, False otherwise.

        Note:
            If both lists are empty, sends a "All certifications current" message.
        """
        subject = (
            f"Certification Compliance Summary - {date.today().strftime('%B %d, %Y')}"
        )

        # Build expiring list HTML
        expiring_rows = ""
        for cert in expiring_certs:
            expiring_rows += f"""
            <tr>
                <td>{cert.person.name}</td>
                <td>{cert.certification_type.name}</td>
                <td>{cert.expiration_date.strftime("%Y-%m-%d")}</td>
                <td>{cert.days_until_expiration} days</td>
            </tr>
            """

        # Build expired list HTML
        expired_rows = ""
        for cert in expired_certs:
            expired_rows += f"""
            <tr style="background-color: #ffe6e6;">
                <td>{cert.person.name}</td>
                <td>{cert.certification_type.name}</td>
                <td>{cert.expiration_date.strftime("%Y-%m-%d")}</td>
                <td style="color: red;">EXPIRED</td>
            </tr>
            """

        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #343a40; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
                th {{ background-color: #f8f9fa; }}
                .section {{ margin: 20px 0; }}
                .section h2 {{ color: #343a40; border-bottom: 2px solid #343a40; padding-bottom: 10px; }}
                .alert {{ padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .alert-danger {{ background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }}
                .alert-warning {{ background-color: #fff3cd; border: 1px solid #ffeeba; color: #856404; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Certification Compliance Summary</h1>
                    <p>{date.today().strftime("%B %d, %Y")}</p>
                </div>
                <div class="content">
                    {
            "<div class='alert alert-danger'><strong>"
            + str(len(expired_certs))
            + " certifications have EXPIRED and require immediate attention.</strong></div>"
            if expired_certs
            else ""
        }

                    {
            "<div class='alert alert-warning'><strong>"
            + str(len(expiring_certs))
            + " certifications are expiring within the next 6 months.</strong></div>"
            if expiring_certs
            else ""
        }

                    {
            f'''
                    <div class="section">
                        <h2>Expired Certifications ({len(expired_certs)})</h2>
                        <table>
                            <thead>
                                <tr>
                                    <th>Person</th>
                                    <th>Certification</th>
                                    <th>Expiration Date</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {expired_rows}
                            </tbody>
                        </table>
                    </div>
                    '''
            if expired_certs
            else ""
        }

                    {
            f'''
                    <div class="section">
                        <h2>Expiring Soon ({len(expiring_certs)})</h2>
                        <table>
                            <thead>
                                <tr>
                                    <th>Person</th>
                                    <th>Certification</th>
                                    <th>Expiration Date</th>
                                    <th>Time Remaining</th>
                                </tr>
                            </thead>
                            <tbody>
                                {expiring_rows}
                            </tbody>
                        </table>
                    </div>
                    '''
            if expiring_certs
            else ""
        }

                    {
            '''<p style="color: green;"><strong>All certifications are current!</strong></p>'''
            if not expired_certs and not expiring_certs
            else ""
        }
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(to_email, subject, body_html)

    def send_invitation_email(
        self,
        to_email: str,
        invite_token: str,
        invited_by: str,
    ) -> bool:
        """Send an invitation email to a new user.

        This is a placeholder implementation that logs the invitation details
        without actually sending an email. When SMTP is configured, this will
        send a proper invitation email with a link to complete registration.

        Args:
            to_email: Email address of the invited user.
            invite_token: Unique token for completing the invitation.
            invited_by: Name or email of the person who sent the invitation.

        Returns:
            True if the email was logged/sent successfully, False otherwise.

        Note:
            Currently a stub implementation - logs invitation details but does not
            send actual emails until SMTP is configured. The token should be used
            to construct a registration URL like:
            {base_url}/register?token={invite_token}
        """
        if not to_email:
            logger.warning("No email address provided for invitation, skipping")
            return False

        # Placeholder: Log the invitation instead of sending
        # TODO: Implement actual email sending when SMTP is configured
        logger.info(
            f"[INVITATION STUB] Would send invitation email to {to_email} "
            f"(invited by: {invited_by}, token: {invite_token[:8]}...)"
        )

        # Build the email content for when SMTP is enabled
        subject = "You've been invited to the Residency Scheduler"

        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2563eb; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .btn {{ display: inline-block; padding: 12px 24px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 5px; margin: 15px 0; }}
                .footer {{ padding: 15px; font-size: 12px; color: #666; text-align: center; }}
                .token-box {{ background-color: #e5e7eb; padding: 10px; border-radius: 5px; font-family: monospace; word-break: break-all; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Residency Scheduler</h1>
                </div>
                <div class="content">
                    <p>Hello,</p>

                    <p>You have been invited by <strong>{invited_by}</strong> to join the
                    Residency Scheduling System.</p>

                    <p>To complete your registration, please click the button below:</p>

                    <p style="text-align: center;">
                        <a href="#" class="btn">Complete Registration</a>
                    </p>

                    <p>Or use this invitation token:</p>
                    <div class="token-box">{invite_token}</div>

                    <p><strong>This invitation will expire in 7 days.</strong></p>

                    <p>If you did not expect this invitation, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from the Residency Scheduling System.</p>
                    <p>Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        body_text = f"""
Welcome to Residency Scheduler

Hello,

You have been invited by {invited_by} to join the Residency Scheduling System.

To complete your registration, use the following invitation token:

{invite_token}

This invitation will expire in 7 days.

If you did not expect this invitation, you can safely ignore this email.

---
This is an automated message from the Residency Scheduling System.
        """

        # When SMTP is not configured, we still want to "succeed" for testing
        if not self.config.enabled:
            logger.info("Email disabled. Invitation logged for: [EMAIL REDACTED]")
            return True

        return self.send_email(to_email, subject, body_html, body_text)

    def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
    ) -> bool:
        """Send a password reset email.

        This is a placeholder implementation that logs the reset details
        without actually sending an email. When SMTP is configured, this will
        send a proper password reset email with a secure link.

        Args:
            to_email: Email address of the user requesting password reset.
            reset_token: Unique token for password reset verification.

        Returns:
            True if the email was logged/sent successfully, False otherwise.

        Note:
            Currently a stub implementation - logs reset details but does not
            send actual emails until SMTP is configured. The token should be used
            to construct a reset URL like:
            {base_url}/reset-password?token={reset_token}

        Security:
            - Reset tokens should expire within 1 hour
            - Tokens should be single-use
            - Never reveal if an email exists in the system
        """
        if not to_email:
            logger.warning("No email address provided for password reset, skipping")
            return False

        # Placeholder: Log the reset request instead of sending
        # TODO: Implement actual email sending when SMTP is configured
        logger.info(
            f"[PASSWORD RESET STUB] Would send password reset email to {to_email} "
            f"(token: {reset_token[:8]}...)"
        )

        # Build the email content for when SMTP is enabled
        subject = "Password Reset Request - Residency Scheduler"

        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc2626; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .btn {{ display: inline-block; padding: 12px 24px; background-color: #dc2626; color: white; text-decoration: none; border-radius: 5px; margin: 15px 0; }}
                .footer {{ padding: 15px; font-size: 12px; color: #666; text-align: center; }}
                .warning {{ background-color: #fef3c7; border: 1px solid #f59e0b; padding: 10px; border-radius: 5px; margin: 15px 0; }}
                .token-box {{ background-color: #e5e7eb; padding: 10px; border-radius: 5px; font-family: monospace; word-break: break-all; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>Hello,</p>

                    <p>We received a request to reset your password for the
                    Residency Scheduling System.</p>

                    <p>To reset your password, click the button below:</p>

                    <p style="text-align: center;">
                        <a href="#" class="btn">Reset Password</a>
                    </p>

                    <p>Or use this reset token:</p>
                    <div class="token-box">{reset_token}</div>

                    <div class="warning">
                        <strong>Important:</strong> This link will expire in 1 hour.
                        If you did not request a password reset, please ignore this email
                        and your password will remain unchanged.
                    </div>

                    <p>For security reasons, never share this link or token with anyone.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from the Residency Scheduling System.</p>
                    <p>Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        body_text = f"""
Password Reset Request

Hello,

We received a request to reset your password for the Residency Scheduling System.

To reset your password, use the following reset token:

{reset_token}

IMPORTANT: This link will expire in 1 hour.
If you did not request a password reset, please ignore this email
and your password will remain unchanged.

For security reasons, never share this link or token with anyone.

---
This is an automated message from the Residency Scheduling System.
        """

        # When SMTP is not configured, we still want to "succeed" for testing
        if not self.config.enabled:
            logger.info("Email disabled. Password reset logged for: [EMAIL REDACTED]")
            return True

        return self.send_email(to_email, subject, body_html, body_text)
