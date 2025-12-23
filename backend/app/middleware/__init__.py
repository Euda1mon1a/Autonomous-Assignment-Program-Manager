"""Middleware components for the application."""

from app.middleware.audit import AuditContextMiddleware, get_audit_info
from app.middleware.content import (
    AcceptHeader,
    ContentNegotiationMiddleware,
    ContentNegotiationStats,
    Parser,
    ParserRegistry,
    ParsingError,
    SerializationError,
    Serializer,
    SerializerRegistry,
    get_parser_registry,
    get_serializer_registry,
    register_parser,
    register_serializer,
)
from app.middleware.logging import (
    RequestLoggingConfig,
    RequestLoggingMiddleware,
    SensitiveDataFilter,
    get_recent_logs,
    get_response_metrics,
)
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.throttling import (
    ThrottleConfig,
    ThrottlePriority,
    ThrottlingMiddleware,
)
from app.middleware.versioning import (
    APIVersion,
    DeprecationManager,
    DeprecationWarning,
    ResponseTransformer,
    TransformRegistry,
    VersionedAPIRouter,
    VersioningMiddleware,
    VersionStatus,
    get_api_version,
    register_transformer,
)

__all__ = [
    "AuditContextMiddleware",
    "get_audit_info",
    "SecurityHeadersMiddleware",
    "RateLimitMiddleware",
    "ThrottlingMiddleware",
    "ThrottleConfig",
    "ThrottlePriority",
    "VersioningMiddleware",
    "APIVersion",
    "get_api_version",
    "VersionedAPIRouter",
    "DeprecationManager",
    "DeprecationWarning",
    "VersionStatus",
    "ResponseTransformer",
    "TransformRegistry",
    "register_transformer",
    "RequestLoggingMiddleware",
    "RequestLoggingConfig",
    "SensitiveDataFilter",
    "get_recent_logs",
    "get_response_metrics",
    "ContentNegotiationMiddleware",
    "ContentNegotiationStats",
    "AcceptHeader",
    "Serializer",
    "SerializerRegistry",
    "SerializationError",
    "Parser",
    "ParserRegistry",
    "ParsingError",
    "get_serializer_registry",
    "get_parser_registry",
    "register_serializer",
    "register_parser",
]
