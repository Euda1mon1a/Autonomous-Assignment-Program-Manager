"""File processors for uploaded files.

Provides processing capabilities for uploaded files including:
- Image resizing and optimization
- Thumbnail generation
- Format conversion
- Metadata extraction
"""

import io
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ProcessorError(Exception):
    """Exception raised when file processing fails."""

    pass


class ImageProcessor:
    """
    Image processing for uploaded files.

    Supports:
    - Resizing to multiple sizes
    - Thumbnail generation
    - Format conversion
    - Quality optimization
    - EXIF data extraction
    """

    # Standard image sizes
    SIZES = {
        "thumbnail": (150, 150),
        "small": (320, 320),
        "medium": (640, 640),
        "large": (1024, 1024),
        "xlarge": (2048, 2048),
    }

    def __init__(self) -> None:
        """Initialize image processor with PIL/Pillow."""
        try:
            from PIL import Image, ImageOps

            self.Image = Image
            self.ImageOps = ImageOps
        except ImportError:
            raise ImportError(
                "Pillow is required for image processing. Install with: pip install Pillow"
            )

    def process_image(
        self,
        file_content: bytes,
        sizes: list[str] | None = None,
        quality: int = 85,
        format: str | None = None,
    ) -> dict[str, Any]:
        """
        Process image with resizing and optimization.

        Args:
            file_content: Original image bytes
            sizes: List of size names to generate (from SIZES dict)
            quality: JPEG quality (1-100)
            format: Output format (JPEG, PNG, WEBP) - None preserves original

        Returns:
            dict: Processing result with original and resized versions
        """
        try:
            # Load image
            image = self.Image.open(io.BytesIO(file_content))

            # Extract EXIF data
            exif_data = self._extract_exif(image)

            # Auto-rotate based on EXIF orientation
            image = self.ImageOps.exif_transpose(image)

            # Get original dimensions
            original_width, original_height = image.size

            # Convert RGBA to RGB if saving as JPEG
            if format == "JPEG" or (format is None and image.format in ["JPEG", "JPG"]):
                if image.mode in ("RGBA", "LA", "P"):
                    # Create white background
                    background = self.Image.new("RGB", image.size, (255, 255, 255))
                    if image.mode == "P":
                        image = image.convert("RGBA")
                    background.paste(
                        image, mask=image.split()[-1] if image.mode == "RGBA" else None
                    )
                    image = background
                elif image.mode != "RGB":
                    image = image.convert("RGB")

            # Prepare result
            result = {
                "original": {
                    "width": original_width,
                    "height": original_height,
                    "format": image.format,
                    "mode": image.mode,
                },
                "exif": exif_data,
                "versions": {},
            }

            # Process original
            output_format = format or image.format
            result["versions"]["original"] = self._save_image(
                image, output_format, quality
            )

            # Generate resized versions
            if sizes:
                for size_name in sizes:
                    if size_name not in self.SIZES:
                        logger.warning(f"Unknown size: {size_name}, skipping")
                        continue

                    target_width, target_height = self.SIZES[size_name]

                    # Only resize if image is larger
                    if original_width > target_width or original_height > target_height:
                        resized = self._resize_image(image, target_width, target_height)
                        result["versions"][size_name] = self._save_image(
                            resized, output_format, quality
                        )
                    else:
                        # Image is already smaller, use original
                        result["versions"][size_name] = result["versions"]["original"]

            return result

        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            raise ProcessorError(f"Image processing failed: {e}")

    def generate_thumbnail(
        self,
        file_content: bytes,
        size: tuple[int, int] = (150, 150),
        quality: int = 85,
    ) -> bytes:
        """
        Generate thumbnail from image.

        Args:
            file_content: Original image bytes
            size: Thumbnail size (width, height)
            quality: JPEG quality

        Returns:
            bytes: Thumbnail image bytes
        """
        try:
            image = self.Image.open(io.BytesIO(file_content))

            # Auto-rotate based on EXIF
            image = self.ImageOps.exif_transpose(image)

            # Convert to RGB if needed
            if image.mode in ("RGBA", "LA", "P"):
                background = self.Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(
                    image, mask=image.split()[-1] if image.mode == "RGBA" else None
                )
                image = background
            elif image.mode != "RGB":
                image = image.convert("RGB")

            # Create thumbnail
            image.thumbnail(size, self.Image.Resampling.LANCZOS)

            # Save to bytes
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=quality, optimize=True)
            return output.getvalue()

        except Exception as e:
            logger.error(f"Thumbnail generation failed: {e}")
            raise ProcessorError(f"Thumbnail generation failed: {e}")

    def _resize_image(self, image: Any, max_width: int, max_height: int) -> Any:
        """
        Resize image while maintaining aspect ratio.

        Args:
            image: PIL Image object
            max_width: Maximum width
            max_height: Maximum height

        Returns:
            PIL Image: Resized image
        """
        # Calculate new dimensions maintaining aspect ratio
        width, height = image.size
        aspect = width / height

        if width > max_width or height > max_height:
            if width / max_width > height / max_height:
                # Width is the limiting factor
                new_width = max_width
                new_height = int(max_width / aspect)
            else:
                # Height is the limiting factor
                new_height = max_height
                new_width = int(max_height * aspect)

            return image.resize((new_width, new_height), self.Image.Resampling.LANCZOS)

        return image

    def _save_image(self, image: Any, format: str, quality: int) -> dict[str, Any]:
        """
        Save image to bytes with optimization.

        Args:
            image: PIL Image object
            format: Output format
            quality: Quality setting

        Returns:
            dict: Image data with bytes and metadata
        """
        output = io.BytesIO()

        save_kwargs = {"format": format, "optimize": True}

        if format in ["JPEG", "JPG"]:
            save_kwargs["quality"] = quality
        elif format == "PNG":
            # PNG optimization
            save_kwargs["compress_level"] = 9
        elif format == "WEBP":
            save_kwargs["quality"] = quality

        image.save(output, **save_kwargs)

        return {
            "bytes": output.getvalue(),
            "size": len(output.getvalue()),
            "width": image.width,
            "height": image.height,
            "format": format,
        }

    def _extract_exif(self, image: Any) -> dict[str, Any]:
        """
        Extract EXIF metadata from image.

        Args:
            image: PIL Image object

        Returns:
            dict: EXIF data
        """
        exif_data = {}

        try:
            from PIL.ExifTags import TAGS

            if hasattr(image, "_getexif") and image._getexif():
                exif = image._getexif()
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = (
                        str(value)
                        if not isinstance(value, (str, int, float))
                        else value
                    )

        except Exception as e:
            logger.debug(f"EXIF extraction failed: {e}")

        return exif_data


class DocumentProcessor:
    """
    Document processor for PDFs and Office documents.

    Supports:
    - PDF page count extraction
    - Document metadata extraction
    - Text extraction (future)
    """

    def process_pdf(self, file_content: bytes) -> dict[str, Any]:
        """
        Process PDF document and extract metadata.

        Args:
            file_content: PDF file bytes

        Returns:
            dict: PDF metadata
        """
        try:
            import PyPDF2

            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))

            metadata = {
                "num_pages": len(pdf_reader.pages),
                "info": {},
            }

            # Extract document info
            if pdf_reader.metadata:
                info = pdf_reader.metadata
                metadata["info"] = {
                    "title": info.get("/Title", ""),
                    "author": info.get("/Author", ""),
                    "subject": info.get("/Subject", ""),
                    "creator": info.get("/Creator", ""),
                    "producer": info.get("/Producer", ""),
                    "creation_date": info.get("/CreationDate", ""),
                }

            return metadata

        except ImportError:
            logger.warning("PyPDF2 not installed, skipping PDF processing")
            return {"num_pages": None, "info": {}}
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            raise ProcessorError(f"PDF processing failed: {e}")


class FileProcessorFactory:
    """Factory for creating appropriate file processor based on file type."""

    @staticmethod
    def get_processor(mime_type: str) -> ImageProcessor | DocumentProcessor | None:
        """
        Get appropriate processor for file type.

        Args:
            mime_type: File MIME type

        Returns:
            Processor instance or None if no processor available
        """
        if mime_type.startswith("image/"):
            return ImageProcessor()
        elif mime_type == "application/pdf":
            return DocumentProcessor()
        else:
            return None
