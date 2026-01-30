"""
Content negotiation middleware for FastAPI.

Provides automatic content negotiation based on:
- Accept header (for response format)
- Content-Type header (for request parsing)
- Quality value (q-value) handling
- Default format fallback

Features:
- Accept header parsing with q-values
- Content-Type negotiation
- JSON, XML, YAML, MessagePack support
- Custom format registration
- Request body parsing
- Response serialization
- Quality-based format selection
"""

import logging

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.middleware.content.parsers import (
    ParserRegistry,
    ParsingError,
    get_parser_registry,
)
from app.middleware.content.serializers import (
    SerializationError,
    SerializerRegistry,
    get_serializer_registry,
)

logger = logging.getLogger(__name__)


class AcceptHeader:
    """
    Parser for HTTP Accept header.

    Handles Accept header parsing including quality values (q-values).
    Format: "type1;q=0.9, type2, type3;q=0.5"
    """

    def __init__(self, header_value: str) -> None:
        """
        Initialize Accept header parser.

        Args:
            header_value: Accept header string
        """
        self.header_value = header_value
        self.media_types = self._parse()

    def _parse(self) -> list[tuple[str, float]]:
        """
        Parse Accept header into list of (media_type, quality) tuples.

        Returns:
            List of (media_type, quality) sorted by quality (highest first)
        """
        media_types = []

        if not self.header_value:
            return media_types

            # Split by comma to get individual media types
        for part in self.header_value.split(","):
            part = part.strip()
            if not part:
                continue

                # Split by semicolon to separate media type from parameters
            components = [c.strip() for c in part.split(";")]
            media_type = components[0].lower()

            # Extract quality value (default is 1.0)
            quality = 1.0
            for component in components[1:]:
                if component.startswith("q="):
                    try:
                        quality = float(component[2:])
                        # Clamp quality to valid range [0, 1]
                        quality = max(0.0, min(1.0, quality))
                    except ValueError:
                        logger.warning(
                            f"Invalid quality value in Accept header: {component}"
                        )
                        quality = 1.0
                    break

            media_types.append((media_type, quality))

            # Sort by quality (highest first), then by specificity
        media_types.sort(key=lambda x: (-x[1], self._specificity(x[0])))

        return media_types

    def _specificity(self, media_type: str) -> int:
        """
        Calculate specificity of media type.

        More specific types (e.g., "application/json") should be
        preferred over wildcards (e.g., "*/*").

        Args:
            media_type: Media type string

        Returns:
            Specificity score (higher is more specific)
        """
        if "/" not in media_type:
            return 0

        type_part, subtype_part = media_type.split("/", 1)

        # */* is least specific
        if type_part == "*" and subtype_part == "*":
            return 0

            # type/* is more specific
        if subtype_part == "*":
            return 1

            # type/subtype is most specific
        return 2

    def get_preferred_types(self) -> list[str]:
        """
        Get list of media types ordered by preference.

        Returns:
            List of media type strings (without quality values)
        """
        return [media_type for media_type, _ in self.media_types]

    def accepts(self, media_type: str) -> bool:
        """
        Check if Accept header accepts given media type.

        Args:
            media_type: Media type to check

        Returns:
            True if media type is acceptable
        """
        media_type_lower = media_type.lower()

        for accepted_type, quality in self.media_types:
            # Skip if quality is 0 (explicitly not acceptable)
            if quality == 0:
                continue

                # Exact match
            if accepted_type == media_type_lower:
                return True

                # Wildcard matching
            if "/" in accepted_type:
                type_part, subtype_part = accepted_type.split("/", 1)

                if subtype_part == "*":
                    # Match type/*
                    if media_type_lower.startswith(f"{type_part}/"):
                        return True
                elif type_part == "*" and subtype_part == "*":
                    # Match */*
                    return True

        return False

    def get_best_match(self, available_types: list[str]) -> str | None:
        """
        Get best matching media type from available types.

        Args:
            available_types: List of available media types

        Returns:
            Best matching media type, or None if no match
        """
        # Try each accepted type in order of preference
        for accepted_type, quality in self.media_types:
            # Skip if quality is 0
            if quality == 0:
                continue

                # Check for exact match
            if accepted_type in available_types:
                return accepted_type

                # Check for wildcard match
            if "/" in accepted_type:
                type_part, subtype_part = accepted_type.split("/", 1)

                for available_type in available_types:
                    if subtype_part == "*":
                        # Match type/*
                        if available_type.startswith(f"{type_part}/"):
                            return available_type
                    elif type_part == "*" and subtype_part == "*":
                        # Match */* - return first available
                        return available_type

        return None


class ContentNegotiationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for content negotiation.

    Handles:
    1. Request Content-Type parsing
    2. Response Accept header negotiation
    3. Automatic serialization/deserialization
    4. Quality value handling
    5. Default format fallback

    The middleware:
    - Parses request body based on Content-Type header
    - Selects response format based on Accept header
    - Handles quality values (q-values)
    - Falls back to default format (JSON) if no match
    - Stores parsed request data in request.state
    """

    def __init__(
        self,
        app: ASGIApp,
        default_content_type: str = "application/json",
        parser_registry: ParserRegistry | None = None,
        serializer_registry: SerializerRegistry | None = None,
    ) -> None:
        """
        Initialize content negotiation middleware.

        Args:
            app: FastAPI application
            default_content_type: Default content type for responses
            parser_registry: Custom parser registry (uses global if not provided)
            serializer_registry: Custom serializer registry (uses global if not provided)
        """
        super().__init__(app)
        self.default_content_type = default_content_type
        self.parser_registry = parser_registry or get_parser_registry()
        self.serializer_registry = serializer_registry or get_serializer_registry()

        logger.info(
            f"ContentNegotiationMiddleware initialized: "
            f"default={default_content_type}, "
            f"parsers={self.parser_registry.get_available_types()}, "
            f"serializers={self.serializer_registry.get_available_types()}"
        )

    async def dispatch(self, request: Request, call_next):
        """
        Process request and response with content negotiation.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            HTTP response with negotiated content type
        """
        # Parse request body if present
        if request.method in ("POST", "PUT", "PATCH"):
            await self._parse_request_body(request)

            # Process request
        response = await call_next(request)

        # Negotiate response content type
        response = await self._negotiate_response(request, response)

        return response

    async def _parse_request_body(self, request: Request) -> None:
        """
        Parse request body based on Content-Type header.

        Stores parsed data in request.state.parsed_body.

        Args:
            request: HTTP request
        """
        content_type = request.headers.get("content-type", "")

        if not content_type:
            return

            # Get parser for content type
        parser = self.parser_registry.get_parser(content_type)

        if not parser:
            logger.debug(f"No parser available for content type: {content_type}")
            return

        try:
            # Read request body
            body = await request.body()

            if not body:
                return

                # Parse body
            parsed_data = parser.parse(body)

            # Store in request state
            request.state.parsed_body = parsed_data
            request.state.content_type = content_type

            logger.debug(f"Parsed request body: {content_type}")

        except ParsingError as e:
            logger.error(f"Failed to parse request body: {e}")
            # Don't raise - let route handler deal with invalid body
        except Exception as e:
            logger.error(f"Unexpected error parsing request body: {e}", exc_info=True)

    async def _negotiate_response(
        self, request: Request, response: Response
    ) -> Response:
        """
        Negotiate response content type based on Accept header.

        Args:
            request: HTTP request (for Accept header)
            response: Original HTTP response

        Returns:
            Response with negotiated content type
        """
        # Skip negotiation if response already has content encoding
        if "content-encoding" in response.headers:
            return response

            # Skip negotiation if response has no body
        if not hasattr(response, "body") or not response.body:
            return response

            # Skip negotiation for non-serializable responses
        current_content_type = response.headers.get("content-type", "")
        if not self._should_negotiate(current_content_type):
            return response

            # Parse Accept header
        accept_header = request.headers.get("accept", "")
        accept = AcceptHeader(accept_header)

        # Get available serializers
        available_types = self.serializer_registry.get_available_types()

        # Find best match
        best_match = accept.get_best_match(available_types)

        # Fall back to default if no match
        if not best_match:
            # Check if Accept header is present and restrictive
            if accept_header and not accept.accepts("*/*"):
                # Client specified Accept header but we can't satisfy it
                logger.debug(
                    f"No acceptable content type found. "
                    f"Accept: {accept_header}, Available: {available_types}"
                )
                # Fall back to default anyway (better than 406)
            best_match = self.default_content_type

            # Get serializer
        serializer = self.serializer_registry.get_serializer(best_match)

        if not serializer:
            # Should not happen, but handle gracefully
            logger.error(f"Serializer not found for type: {best_match}")
            return response

            # Skip if already in correct format
        if current_content_type.startswith(best_match):
            return response

        try:
            # Parse current response body (assume JSON)
            import json

            data = json.loads(response.body.decode("utf-8"))

            # Serialize to negotiated format
            serialized_body = serializer.serialize(data)

            # Update response
            response.body = serialized_body
            response.headers["content-type"] = best_match
            response.headers["content-length"] = str(len(serialized_body))

            # Add Vary header
            if "Vary" in response.headers:
                if "Accept" not in response.headers["Vary"]:
                    response.headers["Vary"] += ", Accept"
            else:
                response.headers["Vary"] = "Accept"

            logger.debug(
                f"Negotiated response content type: {best_match} "
                f"(from {current_content_type})"
            )

        except SerializationError as e:
            logger.error(f"Failed to serialize response: {e}")
            # Return original response
        except Exception as e:
            logger.error(f"Unexpected error during negotiation: {e}", exc_info=True)
            # Return original response

        return response

    def _should_negotiate(self, content_type: str) -> bool:
        """
        Check if content type should be negotiated.

        Only negotiate for JSON responses (our API default).
        Don't negotiate for HTML, images, etc.

        Args:
            content_type: Current content type

        Returns:
            True if should negotiate
        """
        if not content_type:
            return True

            # Only negotiate for JSON responses
        negotiable_types = [
            "application/json",
            "text/json",
        ]

        base_type = content_type.split(";")[0].strip().lower()
        return base_type in negotiable_types


class ContentNegotiationStats:
    """
    Statistics tracker for content negotiation.

    Tracks negotiation metrics:
    - Total requests processed
    - Requests by content type
    - Responses by content type
    - Negotiation failures
    """

    def __init__(self) -> None:
        """Initialize content negotiation statistics."""
        self.total_requests = 0
        self.request_content_types: dict[str, int] = {}
        self.response_content_types: dict[str, int] = {}
        self.negotiation_failures = 0
        self.parsing_errors = 0
        self.serialization_errors = 0

    def record_request(self, content_type: str | None) -> None:
        """
        Record incoming request.

        Args:
            content_type: Request Content-Type header
        """
        self.total_requests += 1
        if content_type:
            base_type = content_type.split(";")[0].strip().lower()
            self.request_content_types[base_type] = (
                self.request_content_types.get(base_type, 0) + 1
            )

    def record_response(self, content_type: str) -> None:
        """
        Record response content type.

        Args:
            content_type: Response Content-Type header
        """
        base_type = content_type.split(";")[0].strip().lower()
        self.response_content_types[base_type] = (
            self.response_content_types.get(base_type, 0) + 1
        )

    def record_negotiation_failure(self) -> None:
        """Record failed content negotiation."""
        self.negotiation_failures += 1

    def record_parsing_error(self) -> None:
        """Record request parsing error."""
        self.parsing_errors += 1

    def record_serialization_error(self) -> None:
        """Record response serialization error."""
        self.serialization_errors += 1

    def get_stats(self) -> dict:
        """
        Get current statistics.

        Returns:
            Dictionary of negotiation statistics
        """
        return {
            "total_requests": self.total_requests,
            "request_content_types": dict(self.request_content_types),
            "response_content_types": dict(self.response_content_types),
            "negotiation_failures": self.negotiation_failures,
            "parsing_errors": self.parsing_errors,
            "serialization_errors": self.serialization_errors,
        }

    def reset(self) -> None:
        """Reset all statistics."""
        self.__init__()
