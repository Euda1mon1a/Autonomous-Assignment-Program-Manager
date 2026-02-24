"""Tests for upload file processors."""

from types import SimpleNamespace

from app.services.upload.processors import ImageProcessor


class _FakeImage:
    def __init__(self) -> None:
        self.format = None
        self.mode = "RGB"
        self.size = (10, 10)
        self.width = 10
        self.height = 10


def test_process_image_defaults_to_jpeg_when_format_missing(monkeypatch):
    processor = ImageProcessor.__new__(ImageProcessor)
    fake_image = _FakeImage()

    processor.Image = SimpleNamespace(open=lambda _: fake_image)
    processor.ImageOps = SimpleNamespace(exif_transpose=lambda image: image)

    monkeypatch.setattr(processor, "_extract_exif", lambda _: {})

    captured = {}

    def fake_save(image, format, quality):
        captured["format"] = format
        return {
            "bytes": b"x",
            "size": 1,
            "width": image.width,
            "height": image.height,
            "format": format,
        }

    monkeypatch.setattr(processor, "_save_image", fake_save)

    result = processor.process_image(b"data", sizes=None, quality=85, format=None)

    assert captured["format"] == "JPEG"
    assert result["versions"]["original"]["format"] == "JPEG"
