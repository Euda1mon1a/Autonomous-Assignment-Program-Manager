"""
gRPC Interceptors for authentication, logging, and error handling.

Interceptors wrap all gRPC calls to provide cross-cutting concerns:
- Authentication: Validate JWT tokens from metadata
- Logging: Record all RPC calls for audit
- Error handling: Convert Python exceptions to gRPC status codes
- Metrics: Track RPC latency and success rates
"""

import logging
import time
from typing import Any, Callable

import grpc
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import verify_token
from app.db.session import SessionLocal
from app.models.token_blacklist import TokenBlacklist

settings = get_settings()
logger = logging.getLogger(__name__)


class AuthenticationInterceptor(grpc.ServerInterceptor):
    """
    Interceptor for JWT-based authentication.

    Validates JWT tokens passed in gRPC metadata under 'authorization' key.
    Token format: "Bearer <jwt_token>"

    Exempt methods (no auth required):
    - /Health/Check
    - /grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo
    """

    EXEMPT_METHODS = {
        "/Health/Check",
        "/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo",
    }

    def intercept_service(
        self,
        continuation: Callable[[Any], Any],
        handler_call_details: grpc.HandlerCallDetails
    ) -> grpc.RpcMethodHandler:
        """
        Intercept gRPC call to validate authentication.

        Args:
            continuation: Function to invoke the next interceptor or handler
            handler_call_details: Details about the RPC call

        Returns:
            RpcMethodHandler for the call
        """
        method = handler_call_details.method

        # Skip authentication for exempt methods
        if method in self.EXEMPT_METHODS:
            return continuation(handler_call_details)

        # Extract authorization metadata
        metadata_dict = dict(handler_call_details.invocation_metadata)
        auth_header = metadata_dict.get("authorization", "")

        if not auth_header.startswith("Bearer "):
            # Missing or invalid authorization header
            return self._unauthenticated_handler()

        token = auth_header[7:]  # Remove "Bearer " prefix

        # Validate token
        db = SessionLocal()
        try:
            token_data = verify_token(token, db)
            if not token_data:
                return self._unauthenticated_handler()

            # Check token blacklist
            jti = token_data.jti
            if jti:
                blacklisted = db.query(TokenBlacklist).filter_by(jti=jti).first()
                if blacklisted:
                    logger.warning(f"Rejected blacklisted token: {jti}")
                    return self._unauthenticated_handler()

            # Token is valid - store user info in context for handlers to use
            # We'll pass it via a custom context object
            handler_call_details.user_id = token_data.user_id
            handler_call_details.username = token_data.username

            return continuation(handler_call_details)

        except Exception as e:
            logger.error(f"Authentication error: {e}", exc_info=True)
            return self._unauthenticated_handler()
        finally:
            db.close()

    @staticmethod
    def _unauthenticated_handler() -> grpc.RpcMethodHandler:
        """Return handler that sends UNAUTHENTICATED status."""
        def abort(ignored_request, context: grpc.ServicerContext):
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED,
                "Invalid or missing authentication token"
            )

        return grpc.unary_unary_rpc_method_handler(
            abort,
            request_deserializer=lambda x: x,
            response_serializer=lambda x: x,
        )


class ErrorHandlingInterceptor(grpc.ServerInterceptor):
    """
    Interceptor for converting Python exceptions to gRPC status codes.

    Maps common exceptions to appropriate gRPC status codes:
    - ValueError, ValidationError -> INVALID_ARGUMENT
    - PermissionError -> PERMISSION_DENIED
    - FileNotFoundError, KeyError -> NOT_FOUND
    - TimeoutError -> DEADLINE_EXCEEDED
    - Other exceptions -> INTERNAL
    """

    def intercept_service(
        self,
        continuation: Callable[[Any], Any],
        handler_call_details: grpc.HandlerCallDetails
    ) -> grpc.RpcMethodHandler:
        """Wrap handler with error handling."""
        handler = continuation(handler_call_details)

        if handler and handler.unary_unary:
            return self._wrap_unary_unary(handler)
        elif handler and handler.unary_stream:
            return self._wrap_unary_stream(handler)
        elif handler and handler.stream_unary:
            return self._wrap_stream_unary(handler)
        elif handler and handler.stream_stream:
            return self._wrap_stream_stream(handler)

        return handler

    def _wrap_unary_unary(self, handler: grpc.RpcMethodHandler) -> grpc.RpcMethodHandler:
        """Wrap unary-unary handler with error handling."""
        def wrapper(request, context: grpc.ServicerContext):
            try:
                return handler.unary_unary(request, context)
            except Exception as e:
                return self._handle_exception(e, context)

        return grpc.unary_unary_rpc_method_handler(
            wrapper,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def _wrap_unary_stream(self, handler: grpc.RpcMethodHandler) -> grpc.RpcMethodHandler:
        """Wrap unary-stream handler with error handling."""
        def wrapper(request, context: grpc.ServicerContext):
            try:
                for response in handler.unary_stream(request, context):
                    yield response
            except Exception as e:
                self._handle_exception(e, context)

        return grpc.unary_stream_rpc_method_handler(
            wrapper,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def _wrap_stream_unary(self, handler: grpc.RpcMethodHandler) -> grpc.RpcMethodHandler:
        """Wrap stream-unary handler with error handling."""
        def wrapper(request_iterator, context: grpc.ServicerContext):
            try:
                return handler.stream_unary(request_iterator, context)
            except Exception as e:
                return self._handle_exception(e, context)

        return grpc.stream_unary_rpc_method_handler(
            wrapper,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def _wrap_stream_stream(self, handler: grpc.RpcMethodHandler) -> grpc.RpcMethodHandler:
        """Wrap stream-stream handler with error handling."""
        def wrapper(request_iterator, context: grpc.ServicerContext):
            try:
                for response in handler.stream_stream(request_iterator, context):
                    yield response
            except Exception as e:
                self._handle_exception(e, context)

        return grpc.stream_stream_rpc_method_handler(
            wrapper,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    @staticmethod
    def _handle_exception(exception: Exception, context: grpc.ServicerContext) -> None:
        """
        Convert Python exception to gRPC status code.

        Args:
            exception: The exception to handle
            context: gRPC context for setting status

        Returns:
            None (aborts the RPC)
        """
        logger.error(f"gRPC error: {exception}", exc_info=True)

        # Map exception types to gRPC status codes
        if isinstance(exception, (ValueError, TypeError)):
            status_code = grpc.StatusCode.INVALID_ARGUMENT
            message = str(exception)
        elif isinstance(exception, PermissionError):
            status_code = grpc.StatusCode.PERMISSION_DENIED
            message = "Permission denied"
        elif isinstance(exception, (FileNotFoundError, KeyError)):
            status_code = grpc.StatusCode.NOT_FOUND
            message = "Resource not found"
        elif isinstance(exception, TimeoutError):
            status_code = grpc.StatusCode.DEADLINE_EXCEEDED
            message = "Operation timed out"
        elif hasattr(exception, 'status_code'):
            # Handle custom exceptions with status_code attribute
            status_code = grpc.StatusCode.INTERNAL
            message = getattr(exception, 'message', str(exception))
        else:
            status_code = grpc.StatusCode.INTERNAL
            # Don't leak internal details in production
            if settings.DEBUG:
                message = f"Internal error: {exception}"
            else:
                message = "An internal error occurred"

        context.abort(status_code, message)


class LoggingInterceptor(grpc.ServerInterceptor):
    """
    Interceptor for logging all gRPC calls.

    Logs:
    - Method name
    - Request size
    - Response size
    - Latency
    - Status code
    - User (if authenticated)
    """

    def intercept_service(
        self,
        continuation: Callable[[Any], Any],
        handler_call_details: grpc.HandlerCallDetails
    ) -> grpc.RpcMethodHandler:
        """Wrap handler with logging."""
        start_time = time.time()
        method = handler_call_details.method
        user = getattr(handler_call_details, 'username', 'anonymous')

        handler = continuation(handler_call_details)

        if handler and handler.unary_unary:
            return self._wrap_unary_unary(handler, method, user, start_time)
        elif handler and handler.unary_stream:
            return self._wrap_unary_stream(handler, method, user, start_time)

        return handler

    def _wrap_unary_unary(
        self,
        handler: grpc.RpcMethodHandler,
        method: str,
        user: str,
        start_time: float
    ) -> grpc.RpcMethodHandler:
        """Wrap unary-unary handler with logging."""
        def wrapper(request, context: grpc.ServicerContext):
            try:
                response = handler.unary_unary(request, context)
                latency = time.time() - start_time
                logger.info(
                    f"gRPC {method} - user={user} latency={latency:.3f}s status=OK"
                )
                return response
            except Exception as e:
                latency = time.time() - start_time
                logger.error(
                    f"gRPC {method} - user={user} latency={latency:.3f}s status=ERROR error={e}"
                )
                raise

        return grpc.unary_unary_rpc_method_handler(
            wrapper,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def _wrap_unary_stream(
        self,
        handler: grpc.RpcMethodHandler,
        method: str,
        user: str,
        start_time: float
    ) -> grpc.RpcMethodHandler:
        """Wrap unary-stream handler with logging."""
        def wrapper(request, context: grpc.ServicerContext):
            try:
                response_count = 0
                for response in handler.unary_stream(request, context):
                    response_count += 1
                    yield response
                latency = time.time() - start_time
                logger.info(
                    f"gRPC {method} - user={user} latency={latency:.3f}s "
                    f"responses={response_count} status=OK"
                )
            except Exception as e:
                latency = time.time() - start_time
                logger.error(
                    f"gRPC {method} - user={user} latency={latency:.3f}s status=ERROR error={e}"
                )
                raise

        return grpc.unary_stream_rpc_method_handler(
            wrapper,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )


class MetricsInterceptor(grpc.ServerInterceptor):
    """
    Interceptor for recording Prometheus metrics.

    Metrics recorded:
    - grpc_requests_total: Counter of total requests
    - grpc_request_duration_seconds: Histogram of request latency
    - grpc_requests_in_flight: Gauge of active requests
    """

    def __init__(self):
        """Initialize Prometheus metrics."""
        try:
            from prometheus_client import Counter, Histogram, Gauge

            self.requests_total = Counter(
                "grpc_requests_total",
                "Total gRPC requests",
                ["method", "status"]
            )
            self.request_duration = Histogram(
                "grpc_request_duration_seconds",
                "gRPC request latency",
                ["method"]
            )
            self.requests_in_flight = Gauge(
                "grpc_requests_in_flight",
                "Active gRPC requests",
                ["method"]
            )
            self.metrics_enabled = True
        except ImportError:
            logger.warning("prometheus_client not available - metrics disabled")
            self.metrics_enabled = False

    def intercept_service(
        self,
        continuation: Callable[[Any], Any],
        handler_call_details: grpc.HandlerCallDetails
    ) -> grpc.RpcMethodHandler:
        """Wrap handler with metrics collection."""
        if not self.metrics_enabled:
            return continuation(handler_call_details)

        method = handler_call_details.method
        handler = continuation(handler_call_details)

        if handler and handler.unary_unary:
            return self._wrap_unary_unary(handler, method)

        return handler

    def _wrap_unary_unary(
        self,
        handler: grpc.RpcMethodHandler,
        method: str
    ) -> grpc.RpcMethodHandler:
        """Wrap unary-unary handler with metrics."""
        def wrapper(request, context: grpc.ServicerContext):
            self.requests_in_flight.labels(method=method).inc()
            start_time = time.time()
            status = "success"

            try:
                response = handler.unary_unary(request, context)
                return response
            except Exception:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                self.requests_in_flight.labels(method=method).dec()
                self.request_duration.labels(method=method).observe(duration)
                self.requests_total.labels(method=method, status=status).inc()

        return grpc.unary_unary_rpc_method_handler(
            wrapper,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )
