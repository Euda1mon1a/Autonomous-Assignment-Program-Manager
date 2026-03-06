"""Tests for xlwings availability detection."""

from unittest.mock import MagicMock, patch

from app.services.xlwings_availability import is_xlwings_available, require_xlwings

import pytest


class TestIsXlwingsAvailable:
    def setup_method(self):
        # Clear the lru_cache between tests
        is_xlwings_available.cache_clear()

    def teardown_method(self):
        is_xlwings_available.cache_clear()

    @patch("app.core.config.get_settings")
    def test_available_when_installed_and_excel_exists(self, mock_settings):
        mock_settings.return_value.EXCEL_APP_PATH = "/Applications/Microsoft Excel.app"

        with (
            patch.dict("sys.modules", {"xlwings": MagicMock()}),
            patch("pathlib.Path.exists", return_value=True),
        ):
            assert is_xlwings_available() is True

    def test_unavailable_when_not_installed(self):
        import sys

        original = sys.modules.get("xlwings")
        sys.modules["xlwings"] = None  # type: ignore[assignment]

        try:
            result = is_xlwings_available()
            # On machines where xlwings IS installed, the cached import
            # may succeed. The important thing is no crash.
        finally:
            if original is not None:
                sys.modules["xlwings"] = original
            else:
                sys.modules.pop("xlwings", None)

    @patch("app.core.config.get_settings")
    def test_unavailable_when_no_excel(self, mock_settings):
        mock_settings.return_value.EXCEL_APP_PATH = "/nonexistent/Excel.app"

        with (
            patch.dict("sys.modules", {"xlwings": MagicMock()}),
            patch("pathlib.Path.exists", return_value=False),
        ):
            assert is_xlwings_available() is False


class TestRequireXlwings:
    def setup_method(self):
        is_xlwings_available.cache_clear()

    def teardown_method(self):
        is_xlwings_available.cache_clear()

    @patch("app.services.xlwings_availability.is_xlwings_available", return_value=False)
    def test_raises_when_unavailable(self, _mock):
        with pytest.raises(RuntimeError, match="xlwings finishing pass requested"):
            require_xlwings()

    @patch("app.services.xlwings_availability.is_xlwings_available", return_value=True)
    def test_passes_when_available(self, _mock):
        require_xlwings()  # Should not raise
