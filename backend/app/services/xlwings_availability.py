"""xlwings availability detection.

Checks both runtime conditions: xlwings installed AND Excel.app present.
Uses @lru_cache since result won't change during process lifetime.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def is_xlwings_available() -> bool:
    """Check if xlwings is installed AND Excel is present on this machine."""
    try:
        import xlwings  # noqa: F401
    except ImportError:
        logger.debug("xlwings not installed — finishing pass unavailable")
        return False

    from app.core.config import get_settings

    excel_path = Path(get_settings().EXCEL_APP_PATH)
    if not excel_path.exists():
        logger.info(
            "xlwings installed but Excel not found at %s — finishing pass unavailable",
            excel_path,
        )
        return False

    logger.info("xlwings available — Excel finishing pass enabled")
    return True


def require_xlwings() -> None:
    """Raise RuntimeError if xlwings is not available."""
    if not is_xlwings_available():
        raise RuntimeError(
            "xlwings finishing pass requested but not available. "
            "Install xlwings (pip install xlwings) and ensure Excel is installed."
        )
