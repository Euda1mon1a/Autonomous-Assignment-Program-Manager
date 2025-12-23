"""
Documentation templates package.

Contains templates for generating various documentation formats:
- OpenAPI schema enhancements
- Markdown documentation
- Code examples
"""

from app.docs.templates.markdown_generator import MarkdownGenerator
from app.docs.templates.openapi_enhancements import OpenAPIEnhancer

__all__ = ["OpenAPIEnhancer", "MarkdownGenerator"]
