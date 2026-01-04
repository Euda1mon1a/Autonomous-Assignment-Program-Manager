# =============================================================================
# MCP Server Dockerfile
# =============================================================================
# Multi-stage build for the Model Context Protocol server
# Provides containerized MCP tools for AI assistant integration
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./
COPY src/ ./src/

# Build wheel
RUN pip install --no-cache-dir build \
    && python -m build --wheel

# -----------------------------------------------------------------------------
# Stage 2: Runtime
# -----------------------------------------------------------------------------
FROM python:3.11-slim as runtime

# Labels for container metadata
LABEL org.opencontainers.image.title="Residency Scheduler MCP Server"
LABEL org.opencontainers.image.description="Model Context Protocol server for medical residency scheduling"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.vendor="Residency Scheduler Team"

# Create non-root user for security
RUN groupadd --gid 1000 mcp \
    && useradd --uid 1000 --gid mcp --shell /bin/bash --create-home mcp

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheel from builder and install
COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl \
    && rm /tmp/*.whl

# Copy source for development/debugging (optional, can be removed for production)
COPY --chown=mcp:mcp src/ ./src/

# Set environment defaults
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO \
    API_BASE_URL=http://backend:8000 \
    PYTHONPATH=/app/src

# Switch to non-root user
USER mcp

# Health check - verify the server can import correctly
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from scheduler_mcp.server import mcp; print('healthy')" || exit 1

# Default command - run MCP server in HTTP mode
ENTRYPOINT ["python", "-m", "scheduler_mcp.server", "--host", "0.0.0.0", "--port", "8080"]

# Expose port for HTTP transport mode (optional)
EXPOSE 8080
