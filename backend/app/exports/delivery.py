"""
Export delivery service.

Handles delivery of export files via:
- Email (with attachments)
- S3 storage
- Combined email + S3
"""

import io
import logging
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import BinaryIO

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DeliveryResult:
    """Result of a delivery attempt."""

    def __init__(
        self,
        success: bool,
        message: str,
        email_sent: bool = False,
        s3_url: str | None = None,
        file_path: str | None = None,
    ) -> None:
        self.success = success
        self.message = message
        self.email_sent = email_sent
        self.s3_url = s3_url
        self.file_path = file_path


class EmailDeliveryService:
    """Service for delivering exports via email."""

    def __init__(self) -> None:
        """Initialize email delivery service."""
        self.smtp_host = (
            settings.SMTP_HOST if hasattr(settings, "SMTP_HOST") else "localhost"
        )
        self.smtp_port = settings.SMTP_PORT if hasattr(settings, "SMTP_PORT") else 587
        self.smtp_user = settings.SMTP_USER if hasattr(settings, "SMTP_USER") else None
        self.smtp_password = (
            settings.SMTP_PASSWORD if hasattr(settings, "SMTP_PASSWORD") else None
        )
        self.from_email = (
            settings.SMTP_FROM_EMAIL
            if hasattr(settings, "SMTP_FROM_EMAIL")
            else "noreply@hospital.org"
        )
        self.from_name = (
            settings.SMTP_FROM_NAME
            if hasattr(settings, "SMTP_FROM_NAME")
            else "Residency Scheduler"
        )
        self.enabled = (
            settings.SMTP_ENABLED if hasattr(settings, "SMTP_ENABLED") else True
        )

    def send_export(
        self,
        recipients: list[str],
        subject: str,
        body: str,
        file_data: bytes | BinaryIO,
        filename: str,
        content_type: str = "application/octet-stream",
    ) -> bool:
        """
        Send export file via email.

        Args:
            recipients: List of email addresses
            subject: Email subject
            body: Email body (HTML)
            file_data: File content (bytes or file-like object)
            filename: Attachment filename
            content_type: MIME content type

        Returns:
            bool: True if email sent successfully
        """
        if not self.enabled:
            logger.info(f"Email disabled. Would send to {recipients}: {subject}")
            return True

        if not recipients:
            logger.warning("No recipients provided for email delivery")
            return False

        try:
            import smtplib

            # Create multipart message
            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = ", ".join(recipients)

            # Add body
            msg.attach(MIMEText(body, "html"))

            # Add attachment
            if isinstance(file_data, bytes):
                attachment_data = file_data
            else:
                # Read from file-like object
                file_data.seek(0)
                attachment_data = file_data.read()

            attachment = MIMEApplication(attachment_data, _subtype=None)
            attachment.add_header("Content-Type", content_type)
            attachment.add_header(
                "Content-Disposition", "attachment", filename=filename
            )
            msg.attach(attachment)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if hasattr(settings, "SMTP_USE_TLS") and settings.SMTP_USE_TLS:
                    server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, recipients, msg.as_string())

            logger.info(f"Export email sent to {len(recipients)} recipients: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send export email: {e}", exc_info=True)
            return False


class S3DeliveryService:
    """Service for delivering exports to S3."""

    def __init__(self) -> None:
        """Initialize S3 delivery service."""
        self.bucket = (
            settings.UPLOAD_S3_BUCKET if hasattr(settings, "UPLOAD_S3_BUCKET") else None
        )
        self.region = (
            settings.UPLOAD_S3_REGION
            if hasattr(settings, "UPLOAD_S3_REGION")
            else "us-east-1"
        )
        self.access_key = (
            settings.UPLOAD_S3_ACCESS_KEY
            if hasattr(settings, "UPLOAD_S3_ACCESS_KEY")
            else None
        )
        self.secret_key = (
            settings.UPLOAD_S3_SECRET_KEY
            if hasattr(settings, "UPLOAD_S3_SECRET_KEY")
            else None
        )
        self.endpoint_url = (
            settings.UPLOAD_S3_ENDPOINT_URL
            if hasattr(settings, "UPLOAD_S3_ENDPOINT_URL")
            else None
        )

    def upload_export(
        self,
        file_data: bytes | BinaryIO,
        key: str,
        bucket: str | None = None,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> tuple[bool, str | None]:
        """
        Upload export file to S3.

        Args:
            file_data: File content (bytes or file-like object)
            key: S3 object key
            bucket: S3 bucket (defaults to configured bucket)
            content_type: MIME content type
            metadata: Additional metadata to store

        Returns:
            tuple[bool, str | None]: (success, s3_url)
        """
        bucket = bucket or self.bucket
        if not bucket:
            logger.error("No S3 bucket configured for export delivery")
            return False, None

        try:
            import boto3
            from botocore.exceptions import ClientError

            # Create S3 client
            s3_config = {
                "region_name": self.region,
            }
            if self.access_key and self.secret_key:
                s3_config["aws_access_key_id"] = self.access_key
                s3_config["aws_secret_access_key"] = self.secret_key
            if self.endpoint_url:
                s3_config["endpoint_url"] = self.endpoint_url

            s3_client = boto3.client("s3", **s3_config)

            # Prepare upload parameters
            upload_params = {
                "ContentType": content_type,
            }
            if metadata:
                upload_params["Metadata"] = metadata

                # Upload file
            if isinstance(file_data, bytes):
                file_obj = io.BytesIO(file_data)
            else:
                file_obj = file_data
                file_obj.seek(0)

            s3_client.upload_fileobj(file_obj, bucket, key, ExtraArgs=upload_params)

            # Generate S3 URL
            if self.endpoint_url:
                s3_url = f"{self.endpoint_url}/{bucket}/{key}"
            else:
                s3_url = f"https://{bucket}.s3.{self.region}.amazonaws.com/{key}"

            logger.info(f"Export uploaded to S3: {s3_url}")
            return True, s3_url

        except ImportError:
            logger.error("boto3 not installed. Cannot upload to S3.")
            return False, None
        except Exception as e:
            logger.error(f"Failed to upload export to S3: {e}", exc_info=True)
            return False, None


class ExportDeliveryService:
    """Main service for delivering exports via configured methods."""

    def __init__(self) -> None:
        """Initialize delivery service."""
        self.email_service = EmailDeliveryService()
        self.s3_service = S3DeliveryService()

    def deliver(
        self,
        file_data: bytes | BinaryIO,
        filename: str,
        delivery_method: str,
        email_recipients: list[str] | None = None,
        email_subject: str | None = None,
        email_body: str | None = None,
        s3_bucket: str | None = None,
        s3_key_prefix: str | None = None,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> DeliveryResult:
        """
        Deliver export file via configured method(s).

        Args:
            file_data: File content (bytes or file-like object)
            filename: File name
            delivery_method: 'email', 's3', or 'both'
            email_recipients: Email addresses (for email delivery)
            email_subject: Email subject (for email delivery)
            email_body: Email body (for email delivery)
            s3_bucket: S3 bucket (for S3 delivery)
            s3_key_prefix: S3 key prefix (for S3 delivery)
            content_type: MIME content type
            metadata: Additional metadata

        Returns:
            DeliveryResult: Result of delivery attempt
        """
        email_sent = False
        s3_url = None
        success = True
        messages = []

        # Email delivery
        if delivery_method in ("email", "both"):
            if not email_recipients:
                messages.append("No email recipients configured")
                success = False
            else:
                subject = email_subject or f"Export: {filename}"
                body = email_body or self._generate_default_email_body(filename)

                email_sent = self.email_service.send_export(
                    recipients=email_recipients,
                    subject=subject,
                    body=body,
                    file_data=file_data,
                    filename=filename,
                    content_type=content_type,
                )

                if email_sent:
                    messages.append(f"Email sent to {len(email_recipients)} recipients")
                else:
                    messages.append("Email delivery failed")
                    success = False

                    # S3 delivery
        if delivery_method in ("s3", "both"):
            # Generate S3 key
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            s3_key = f"{s3_key_prefix or 'exports'}/{timestamp}_{filename}"

            s3_success, s3_url = self.s3_service.upload_export(
                file_data=file_data,
                key=s3_key,
                bucket=s3_bucket,
                content_type=content_type,
                metadata=metadata,
            )

            if s3_success:
                messages.append(f"Uploaded to S3: {s3_url}")
            else:
                messages.append("S3 upload failed")
                success = False

        message = "; ".join(messages) if messages else "No delivery method executed"

        return DeliveryResult(
            success=success,
            message=message,
            email_sent=email_sent,
            s3_url=s3_url,
        )

    def _generate_default_email_body(self, filename: str) -> str:
        """Generate default email body for export delivery."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #343a40; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .footer {{ padding: 15px; font-size: 12px; color: #666; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Scheduled Export</h1>
                </div>
                <div class="content">
                    <p>Your scheduled export is attached to this email.</p>
                    <p><strong>File:</strong> {filename}</p>
                    <p><strong>Generated:</strong> {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from the Residency Scheduling System.</p>
                    <p>Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
