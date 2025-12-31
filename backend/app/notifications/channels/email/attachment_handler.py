"""Email attachment handling."""

import base64
import mimetypes
from email.mime.application import MIMEApplication
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class AttachmentHandler:
    """
    Handles email attachments.

    Supports:
    - File attachments
    - Inline images
    - PDF reports
    - CSV exports
    """

    MAX_ATTACHMENT_SIZE_MB = 10

    def add_file_attachment(
        self, file_path: str | Path, filename: str | None = None
    ) -> Any:
        """
        Create attachment from file.

        Args:
            file_path: Path to file
            filename: Optional filename override

        Returns:
            MIME attachment part

        Raises:
            ValueError: If file too large or invalid
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")

        # Check file size
        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > self.MAX_ATTACHMENT_SIZE_MB:
            raise ValueError(
                f"File too large: {size_mb:.1f}MB (max: {self.MAX_ATTACHMENT_SIZE_MB}MB)"
            )

        # Read file
        with open(file_path, "rb") as f:
            data = f.read()

        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(file_path)

        if not mime_type:
            mime_type = "application/octet-stream"

        # Create appropriate MIME part
        main_type, sub_type = mime_type.split("/", 1)

        if main_type == "text":
            part = MIMEText(data.decode("utf-8"), _subtype=sub_type)
        elif main_type == "image":
            part = MIMEImage(data, _subtype=sub_type)
        elif main_type == "audio":
            part = MIMEAudio(data, _subtype=sub_type)
        else:
            part = MIMEApplication(data, _subtype=sub_type)

        # Set filename
        part.add_header(
            "Content-Disposition",
            "attachment",
            filename=filename or file_path.name,
        )

        logger.debug("Created attachment: %s (%s)", filename or file_path.name, mime_type)

        return part

    def add_data_attachment(
        self, data: bytes, filename: str, mime_type: str = "application/octet-stream"
    ) -> Any:
        """
        Create attachment from data.

        Args:
            data: File data
            filename: Filename
            mime_type: MIME type

        Returns:
            MIME attachment part
        """
        main_type, sub_type = mime_type.split("/", 1)

        if main_type == "text":
            part = MIMEText(data.decode("utf-8"), _subtype=sub_type)
        elif main_type == "image":
            part = MIMEImage(data, _subtype=sub_type)
        elif main_type == "audio":
            part = MIMEAudio(data, _subtype=sub_type)
        else:
            part = MIMEApplication(data, _subtype=sub_type)

        part.add_header("Content-Disposition", "attachment", filename=filename)

        logger.debug("Created data attachment: %s (%s)", filename, mime_type)

        return part

    def add_inline_image(self, image_path: str | Path, content_id: str) -> Any:
        """
        Add inline image for HTML emails.

        Args:
            image_path: Path to image
            content_id: Content ID for referencing in HTML

        Returns:
            MIME image part
        """
        image_path = Path(image_path)

        with open(image_path, "rb") as f:
            data = f.read()

        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type or not mime_type.startswith("image/"):
            mime_type = "image/png"

        _, sub_type = mime_type.split("/", 1)
        part = MIMEImage(data, _subtype=sub_type)

        part.add_header("Content-ID", f"<{content_id}>")
        part.add_header("Content-Disposition", "inline")

        logger.debug("Created inline image: %s (cid:%s)", image_path.name, content_id)

        return part
