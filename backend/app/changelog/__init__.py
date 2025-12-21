"""
API changelog generation and tracking.

This module provides functionality for:
- OpenAPI schema comparison and versioning
- Automatic changelog generation
- Breaking change detection
- Migration guide generation
- Semantic version suggestions
"""

from app.changelog.differ import APIDiffer, ChangeType
from app.changelog.formatter import ChangelogFormatter, OutputFormat
from app.changelog.generator import ChangelogGenerator

__all__ = [
    "APIDiffer",
    "ChangeType",
    "ChangelogFormatter",
    "OutputFormat",
    "ChangelogGenerator",
]
