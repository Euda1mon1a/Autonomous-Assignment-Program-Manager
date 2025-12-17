"""
Residency Scheduler API.

FastAPI application for managing residency program schedules.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.routes import api_router
from app.core.config import get_settings
from app.middleware.audit import AuditContextMiddleware

settings = get_settings()
logger = logging.getLogger(__name__)


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
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Backwards compatibility redirect - redirect /api/... to /api/v1/...
@app.middleware("http")
async def redirect_old_api(request: Request, call_next):
    """Redirect legacy /api routes to /api/v1 for backwards compatibility."""
    if request.url.path.startswith("/api/") and not request.url.path.startswith("/api/v1/"):
        new_path = request.url.path.replace("/api/", "/api/v1/", 1)
        return RedirectResponse(url=new_path, status_code=307)
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
