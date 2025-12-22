"""
Documentation templates package.

Contains templates for generating various documentation formats:
- OpenAPI schema enhancements
- Markdown documentation
- Code examples
"""

from app.docs.templates.openapi_enhancements import OpenAPIEnhancer
from app.docs.templates.markdown_generator import MarkdownGenerator

__all__ = ["OpenAPIEnhancer", "MarkdownGenerator"]
