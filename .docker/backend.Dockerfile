***REMOVED*** =============================================================================
***REMOVED*** Production Dockerfile for Residency Scheduler Backend
***REMOVED*** =============================================================================
***REMOVED*** Multi-stage build with security hardening
***REMOVED*** Python 3.11 slim base with minimal attack surface
***REMOVED***
***REMOVED*** Build context should be the repository root:
***REMOVED***   docker build -f .docker/backend.Dockerfile .
***REMOVED*** =============================================================================

***REMOVED*** -----------------------------------------------------------------------------
***REMOVED*** Stage 1: Builder - Install dependencies and build wheels
***REMOVED*** -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

***REMOVED*** Set build-time environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /build

***REMOVED*** Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

***REMOVED*** Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

***REMOVED*** Copy only requirements first for better layer caching
COPY backend/requirements.txt .

***REMOVED*** Install Python dependencies into virtual environment
***REMOVED*** Separate production dependencies from dev dependencies
RUN pip install --upgrade pip setuptools wheel && \
    grep -v -E "^(black|ruff|mypy|pytest|httpx|factory-boy|faker|freezegun)" requirements.txt > requirements.prod.txt && \
    pip install --no-cache-dir -r requirements.prod.txt

***REMOVED*** -----------------------------------------------------------------------------
***REMOVED*** Stage 2: Runtime - Minimal production image
***REMOVED*** -----------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

***REMOVED*** Labels for container identification
LABEL org.opencontainers.image.title="Residency Scheduler Backend" \
    org.opencontainers.image.description="FastAPI backend for medical residency scheduling" \
    org.opencontainers.image.vendor="Residency Scheduler" \
    org.opencontainers.image.version="1.0.0" \
    maintainer="devops@residency-scheduler.local"

***REMOVED*** Set production environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    ***REMOVED*** Virtual environment path
    PATH="/opt/venv/bin:$PATH" \
    ***REMOVED*** Application settings
    APP_HOME=/app \
    APP_USER=appuser \
    APP_GROUP=appgroup \
    ***REMOVED*** Security settings
    PYTHONPATH=/app

WORKDIR $APP_HOME

***REMOVED*** Install only runtime dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ***REMOVED*** Security: Install dumb-init for proper signal handling
    dumb-init \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* \
    ***REMOVED*** Security: Remove unnecessary packages
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false

***REMOVED*** Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

***REMOVED*** Create non-root user with specific UID/GID for security
RUN groupadd --gid 1001 $APP_GROUP && \
    useradd --uid 1001 --gid $APP_GROUP --shell /bin/false --home-dir $APP_HOME $APP_USER && \
    ***REMOVED*** Create necessary directories with proper permissions
    mkdir -p $APP_HOME/logs $APP_HOME/data && \
    chown -R $APP_USER:$APP_GROUP $APP_HOME

***REMOVED*** Copy application code
COPY --chown=$APP_USER:$APP_GROUP backend/ .

***REMOVED*** Security: Remove unnecessary files
RUN rm -rf \
    tests/ \
    .pytest_cache/ \
    .mypy_cache/ \
    .ruff_cache/ \
    __pycache__/ \
    *.pyc \
    *.pyo \
    *.md \
    .git/ \
    .gitignore \
    .env* \
    pyproject.toml \
    pytest.ini \
    2>/dev/null || true

***REMOVED*** Security: Set restrictive file permissions
RUN chmod -R 550 $APP_HOME && \
    chmod -R 770 $APP_HOME/logs $APP_HOME/data && \
    ***REMOVED*** Alembic needs write access for migrations
    chmod -R 750 $APP_HOME/alembic

***REMOVED*** Switch to non-root user
USER $APP_USER

***REMOVED*** Expose port
EXPOSE 8000

***REMOVED*** Health check - verify application is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

***REMOVED*** Use dumb-init as PID 1 for proper signal handling
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

***REMOVED*** Run database migrations and start uvicorn with production settings
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --loop uvloop --http httptools --no-access-log"]
