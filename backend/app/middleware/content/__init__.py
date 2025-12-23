"""
Content negotiation middleware package.

Provides automatic content negotiation for FastAPI applications.

Features:
- Accept header parsing with quality values
- Content-Type negotiation
- JSON, XML, YAML, MessagePack support
- Custom format registration
- Request body parsing
- Response serialization
- Default format fallback

Usage:
    from app.middleware.content import ContentNegotiationMiddleware

    # Basic usage with defaults (JSON)
    app.add_middleware(ContentNegotiationMiddleware)

    # Custom default content type
    app.add_middleware(
        ContentNegotiationMiddleware,
        default_content_type="application/xml"
    )

    # Register custom serializer
    from app.middleware.content import register_serializer, Serializer

    class CustomSerializer(Serializer):
        @property
        def content_type(self) -> str:
            return "application/custom"

        @property
        def available(self) -> bool:
            return True

        def serialize(self, data):
            # Custom serialization logic
            return b"..."

    register_serializer(CustomSerializer())

Content Type Support:
    - application/json (always available)
    - application/xml (always available)
    - application/yaml (requires PyYAML)
    - application/msgpack (requires msgpack)
    - application/x-www-form-urlencoded (always available)

Examples:
    # Client requests JSON
    GET /api/users
    Accept: application/json

    # Client requests XML
    GET /api/users
    Accept: application/xml

    # Client requests with quality values
    GET /api/users
    Accept: application/json;q=0.9, application/xml;q=0.8

    # POST with JSON
    POST /api/users
    Content-Type: application/json
    {"name": "John"}

    # POST with XML
    POST /api/users
    Content-Type: application/xml
    <user><name>John</name></user>
"""

from app.middleware.content.negotiation import (
    AcceptHeader,
    ContentNegotiationMiddleware,
    ContentNegotiationStats,
)
from app.middleware.content.parsers import (
    FormDataParser,
    JSONParser,
    MessagePackParser,
    Parser,
    ParserRegistry,
    ParsingError,
    XMLParser,
    YAMLParser,
    get_parser_registry,
    register_parser,
)
from app.middleware.content.serializers import (
    JSONSerializer,
    MessagePackSerializer,
    SerializationError,
    Serializer,
    SerializerRegistry,
    XMLSerializer,
    YAMLSerializer,
    get_serializer_registry,
    register_serializer,
)

__all__ = [
    # Middleware
    "ContentNegotiationMiddleware",
    "ContentNegotiationStats",
    "AcceptHeader",
    # Serializers
    "Serializer",
    "SerializerRegistry",
    "SerializationError",
    "JSONSerializer",
    "XMLSerializer",
    "YAMLSerializer",
    "MessagePackSerializer",
    "get_serializer_registry",
    "register_serializer",
    # Parsers
    "Parser",
    "ParserRegistry",
    "ParsingError",
    "JSONParser",
    "XMLParser",
    "YAMLParser",
    "MessagePackParser",
    "FormDataParser",
    "get_parser_registry",
    "register_parser",
]
