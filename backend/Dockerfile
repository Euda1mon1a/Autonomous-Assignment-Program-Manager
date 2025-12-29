# Backend Dockerfile for Residency Scheduler
# Multi-stage build for minimal attack surface and optimized image size

# =============================================================================
# Python Version Selection: 3.12
# =============================================================================
# Python 3.12 is chosen for ortools compatibility:
# - ortools>=9.8 officially supports Python 3.9, 3.10, 3.11, 3.12, and 3.13
# - Python 3.12 provides pre-built wheels for ortools on Linux x86-64
# - All other dependencies (FastAPI, SQLAlchemy, etc.) support Python 3.12
#
# Verified compatibility (as of 2025-12-18):
# - ortools 9.14.6206 (latest) includes cp312 wheels for Linux x86-64
# - Source: https://pypi.org/project/ortools/
#
# =============================================================================
# Build Stage - includes compilers and build tools
# =============================================================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies for psycopg2 and other compiled packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies into a virtual environment
# Combined into fewer layers for better caching
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip --no-cache-dir \
    && pip install --no-cache-dir --use-deprecated=legacy-resolver -r requirements.txt

# =============================================================================
# Runtime Stage - minimal production image
# =============================================================================
FROM python:3.12-slim AS runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install only runtime dependencies (libpq for psycopg2, libmagic for python-magic)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY . .

# Copy and make entrypoint executable
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create non-root user for security
RUN adduser --disabled-password --gecos '' --uid 1001 appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# No healthcheck here - it will be defined in docker-compose.yml per service
# since different services (backend, celery-worker, celery-beat) need different checks

# Run migrations and start server
ENTRYPOINT ["docker-entrypoint.sh"]
CMD []
