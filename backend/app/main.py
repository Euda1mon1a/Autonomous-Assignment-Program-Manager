"""
Residency Scheduler API.

FastAPI application for managing residency program schedules.
"""
from contextlib import asynccontextmanager
from ipaddress import ip_address, ip_network

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.routes import api_router
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.logging import get_logger, setup_logging
from app.middleware.audit import AuditContextMiddleware

settings = get_settings()

# Initialize structured logging
setup_logging(
    level=settings.LOG_LEVEL,
    format_type=settings.LOG_FORMAT,
    log_file=settings.LOG_FILE if settings.LOG_FILE else None,
)

logger = get_logger(__name__)


def _validate_security_config() -> None:
    """
    Validate security configuration at startup.

    Checks that SECRET_KEY and WEBHOOK_SECRET are properly set.
    In production mode (DEBUG=False), raises ValueError if secrets are insecure.
    In development mode (DEBUG=True), logs warnings.
    """
    insecure_defaults = [
        "",
        "your-secret-key-change-in-production",
        "your-webhook-secret-change-in-production",
    ]

    errors = []

    # Check SECRET_KEY
    if settings.SECRET_KEY in insecure_defaults:
        errors.append("SECRET_KEY is not set or uses an insecure default value")
    elif len(settings.SECRET_KEY) < 32:
        errors.append(f"SECRET_KEY is too short ({len(settings.SECRET_KEY)} chars, minimum 32)")

    # Check WEBHOOK_SECRET
    if settings.WEBHOOK_SECRET in insecure_defaults:
        errors.append("WEBHOOK_SECRET is not set or uses an insecure default value")
    elif len(settings.WEBHOOK_SECRET) < 32:
        errors.append(f"WEBHOOK_SECRET is too short ({len(settings.WEBHOOK_SECRET)} chars, minimum 32)")

    if errors:
        error_msg = "Security configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
        if not settings.DEBUG:
            # Production mode: fail fast
            raise ValueError(
                f"{error_msg}\n\n"
                "Set strong random values for SECRET_KEY and WEBHOOK_SECRET environment variables.\n"
                "Generate secrets using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        else:
            # Development mode: warn but allow
            logger.warning(
                f"\n{'='*80}\n"
                f"WARNING: Running in DEBUG mode with insecure configuration!\n"
                f"{error_msg}\n"
                f"This is only acceptable for local development.\n"
                f"{'='*80}\n"
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events:
    - Initialize Prometheus metrics
    - Set up resilience monitoring
    """
    # Startup
    logger.info("Starting Residency Scheduler API")

    # Validate security configuration at startup
    _validate_security_config()

    # Initialize Prometheus instrumentation
    try:
        from prometheus_fastapi_instrumentator import Instrumentator

        instrumentator = Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
            should_respect_env_var=True,
            should_instrument_requests_inprogress=True,
            excluded_handlers=["/health", "/metrics"],
            inprogress_name="http_requests_inprogress",
            inprogress_labels=True,
        )
        instrumentator.instrument(app).expose(app, endpoint="/metrics")
        logger.info("Prometheus instrumentation enabled at /metrics")
    except ImportError:
        logger.warning("prometheus-fastapi-instrumentator not available")

    # Initialize resilience metrics
    try:
        from app.resilience.metrics import setup_metrics
        setup_metrics()
        logger.info("Resilience metrics initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize resilience metrics: {e}")

    # Initialize service cache
    try:
        from app.core.cache import get_service_cache
        cache = get_service_cache()
        if cache.is_available:
            stats = cache.get_stats()
            logger.info(
                f"Service cache initialized (Redis connected, TTL: {stats['default_ttl']}s)"
            )
        else:
            logger.warning("Service cache unavailable - Redis not connected")
    except Exception as e:
        logger.warning(f"Failed to initialize service cache: {e}")

    # Start certification scheduler for expiration reminders
    try:
        from app.services.certification_scheduler import start_scheduler
        start_scheduler()
        logger.info("Certification scheduler started")
    except Exception as e:
        logger.warning(f"Failed to start certification scheduler: {e}")

    # Log audit system status (without exposing sensitive config values)
    logger.info("Audit versioning enabled for: Assignment, Absence, ScheduleRun")

    yield

    # Shutdown
    logger.info("Shutting down Residency Scheduler API")

    # Log final cache stats
    try:
        from app.core.cache import get_service_cache
        cache = get_service_cache()
        if cache.is_available:
            stats = cache.get_stats()
            logger.info(
                f"Cache stats at shutdown - hits: {stats['hits']}, "
                f"misses: {stats['misses']}, hit_rate: {stats['hit_rate']:.2%}"
            )
    except Exception:
        pass

    # Stop certification scheduler
    try:
        from app.services.certification_scheduler import stop_scheduler
        stop_scheduler()
        logger.info("Certification scheduler stopped")
    except Exception as e:
        logger.warning(f"Failed to stop certification scheduler: {e}")


app = FastAPI(
    title="Residency Scheduler API",
    description="API for medical residency scheduling with ACGME compliance",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)


# =============================================================================
# Global Exception Handlers
# =============================================================================


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions with user-friendly messages."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions without leaking internal details."""
    # Log the full error for debugging
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True
    )

    # Return generic error to client
    if settings.DEBUG:
        # In debug mode, include more details for development
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "type": type(exc).__name__
            }
        )
    else:
        # In production, hide implementation details
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred. Please try again later."}
        )


# =============================================================================
# Middleware Configuration
# =============================================================================

# CORS middleware
# Support both explicit origins list and regex pattern for flexible domain matching
cors_kwargs = {
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

# Add explicit origins if configured
if settings.CORS_ORIGINS:
    cors_kwargs["allow_origins"] = settings.CORS_ORIGINS

# Add regex pattern if configured (allows flexible domain matching)
if settings.CORS_ORIGINS_REGEX:
    cors_kwargs["allow_origin_regex"] = settings.CORS_ORIGINS_REGEX

app.add_middleware(CORSMiddleware, **cors_kwargs)

# Trusted host middleware - prevents host header attacks (production only)
if settings.TRUSTED_HOSTS:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.TRUSTED_HOSTS,
    )
    # Log count only, not actual values (security: avoid exposing infrastructure)
    logger.info(f"Trusted hosts middleware enabled. {len(settings.TRUSTED_HOSTS)} host(s) configured.")

# Audit context middleware - captures user for version history tracking
app.add_middleware(AuditContextMiddleware)

# Request ID middleware - adds X-Request-ID for distributed tracing
try:
    from app.core.observability import RequestIDMiddleware
    app.add_middleware(RequestIDMiddleware)
    logger.info("Request ID middleware enabled for distributed tracing")
except ImportError:
    logger.warning("observability module not available - X-Request-ID disabled")

# Internal network IP ranges for metrics endpoint restriction
INTERNAL_NETWORKS = [
    ip_network("127.0.0.0/8"),
    ip_network("10.0.0.0/8"),
    ip_network("172.16.0.0/12"),
    ip_network("192.168.0.0/16"),
]

# Backwards compatibility redirect - redirect /api/... to /api/v1/...
@app.middleware("http")
async def redirect_old_api(request: Request, call_next):
    """Redirect legacy /api routes to /api/v1 for backwards compatibility."""
    if request.url.path.startswith("/api/") and not request.url.path.startswith("/api/v1/"):
        new_path = request.url.path.replace("/api/", "/api/v1/", 1)
        return RedirectResponse(url=new_path, status_code=307)
    return await call_next(request)


# Metrics endpoint protection - restrict to internal IPs in production
@app.middleware("http")
async def restrict_metrics_endpoint(request: Request, call_next):
    """Restrict /metrics endpoint to internal networks in production."""
    if request.url.path == "/metrics" and not settings.DEBUG:
        try:
            client_ip = ip_address(request.client.host)
            is_internal = any(client_ip in network for network in INTERNAL_NETWORKS)
            if not is_internal:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Access denied"}
                )
        except (ValueError, TypeError):
            # Invalid IP address
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied"}
            )
    return await call_next(request)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": "Residency Scheduler API",
        "version": "1.0.0",
        "status": "healthy",
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",  # Would check actual DB connection in production
    }


@app.get("/health/resilience")
async def resilience_health():
    """
    Resilience system health check.

    Returns current resilience status including:
    - Utilization level
    - Defense level
    - Load shedding status
    - Active fallbacks
    """
    try:
        from app.resilience.metrics import get_metrics

        metrics = get_metrics()
        return {
            "status": "operational",
            "metrics_enabled": metrics._enabled if hasattr(metrics, '_enabled') else False,
            "components": [
                "utilization_monitor",
                "defense_in_depth",
                "contingency_analyzer",
                "fallback_scheduler",
                "sacrifice_hierarchy",
            ],
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
        }


@app.get("/health/cache")
async def cache_health():
    """
    Cache system health check.

    Returns current cache status including:
    - Redis availability
    - Hit/miss statistics
    - Cache hit rate
    """
    try:
        from app.core.cache import get_service_cache

        cache = get_service_cache()
        stats = cache.get_stats()
        return {
            "status": "operational" if stats["available"] else "unavailable",
            "enabled": stats["enabled"],
            "redis_connected": stats["available"],
            "hits": stats["hits"],
            "misses": stats["misses"],
            "hit_rate": stats["hit_rate"],
            "approximate_entries": stats["approximate_size"],
            "default_ttl_seconds": stats["default_ttl"],
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }
