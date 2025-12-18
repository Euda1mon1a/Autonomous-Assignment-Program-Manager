# Backend Dockerfile for Residency Scheduler
# Docker Hardened Image (DHI) with multi-stage build for minimal attack surface
# Requires: docker login (Docker Hub credentials) to pull from dhi.io

# =============================================================================
# Python Version Selection: 3.12
# =============================================================================
# Python 3.12 is chosen for ortools compatibility and security:
# - ortools>=9.8 officially supports Python 3.9, 3.10, 3.11, 3.12, and 3.13
# - Python 3.12 provides pre-built wheels for ortools on Linux x86-64
# - DHI (Docker Hardened Images) 3.12 offers ~95% fewer CVEs vs standard images
# - All other dependencies (FastAPI, SQLAlchemy, etc.) support Python 3.12
#
# Verified compatibility (as of 2025-12-18):
# - ortools 9.14.6206 (latest) includes cp312 wheels for Linux x86-64
# - Source: https://pypi.org/project/ortools/
#
# =============================================================================
# Build Stage - includes compilers and build tools
# =============================================================================
FROM dhi.io/python:3.12-dev AS builder

WORKDIR /app

# Install build dependencies for psycopg2 and other compiled packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Runtime Stage - minimal distroless image (~95% fewer CVEs)
# =============================================================================
FROM dhi.io/python:3.12 AS runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install only runtime dependencies (libpq for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY . .

# Create non-root user for security
RUN adduser --disabled-password --gecos '' --uid 1001 appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check using Python (no curl in distroless)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run migrations and start server with uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
