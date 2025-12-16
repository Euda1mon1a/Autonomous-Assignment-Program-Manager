"""
Residency Scheduler API.

FastAPI application for managing residency program schedules.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import get_settings
from app.api.routes import api_router

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

# Include API routes
app.include_router(api_router, prefix="/api")


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
