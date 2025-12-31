"""Email image handling."""

import base64
from pathlib import Path
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailImageHandler:
    """
    Handles images in emails.

    Features:
    - Inline embedding (base64)
    - External hosting
    - Responsive images
    - Optimization
    """

    def embed_image(self, image_path: str | Path) -> str:
        """
        Embed image as base64 data URI.

        Args:
            image_path: Path to image file

        Returns:
            Data URI string
        """
        image_path = Path(image_path)

        with open(image_path, "rb") as f:
            data = f.read()

        # Determine MIME type
        suffix = image_path.suffix.lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
        }

        mime_type = mime_types.get(suffix, "image/png")

        # Encode to base64
        encoded = base64.b64encode(data).decode("utf-8")

        data_uri = f"data:{mime_type};base64,{encoded}"

        logger.debug("Embedded image: %s", image_path.name)

        return data_uri

    def generate_img_tag(
        self,
        src: str,
        alt: str = "",
        width: int | None = None,
        height: int | None = None,
        responsive: bool = True,
    ) -> str:
        """
        Generate HTML img tag.

        Args:
            src: Image source (URL or data URI)
            alt: Alt text
            width: Image width
            height: Image height
            responsive: Make image responsive

        Returns:
            HTML img tag
        """
        attrs = [
            f'src="{src}"',
            f'alt="{alt}"',
        ]

        if width:
            attrs.append(f'width="{width}"')

        if height:
            attrs.append(f'height="{height}"')

        if responsive:
            attrs.append('style="max-width: 100%; height: auto;"')

        img_tag = f'<img {" ".join(attrs)} />'

        return img_tag
