"""
Logging utilities for CLI.
"""

import logging
from pathlib import Path

from rich.logging import RichHandler

from cli.config import get_config_dir


def setup_logging(verbose: bool = False):
    """
    Setup logging for CLI.

    Args:
        verbose: Enable verbose logging
    """
    log_level = logging.DEBUG if verbose else logging.INFO

    # Create logs directory
    log_dir = get_config_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=[
            RichHandler(rich_tracebacks=True, show_time=False),
            logging.FileHandler(log_dir / "cli.log"),
        ],
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
