***REMOVED*** Backend Dockerfile for Residency Scheduler
***REMOVED*** Docker Hardened Image (DHI) with multi-stage build for minimal attack surface
***REMOVED*** Requires: docker login (Docker Hub credentials) to pull from dhi.io

***REMOVED*** =============================================================================
***REMOVED*** Python Version Selection: 3.12
***REMOVED*** =============================================================================
***REMOVED*** Python 3.12 is chosen for ortools compatibility and security:
***REMOVED*** - ortools>=9.8 officially supports Python 3.9, 3.10, 3.11, 3.12, and 3.13
***REMOVED*** - Python 3.12 provides pre-built wheels for ortools on Linux x86-64
***REMOVED*** - DHI (Docker Hardened Images) 3.12 offers ~95% fewer CVEs vs standard images
***REMOVED*** - All other dependencies (FastAPI, SQLAlchemy, etc.) support Python 3.12
***REMOVED***
***REMOVED*** Verified compatibility (as of 2025-12-18):
***REMOVED*** - ortools 9.14.6206 (latest) includes cp312 wheels for Linux x86-64
***REMOVED*** - Source: https://pypi.org/project/ortools/
***REMOVED***
***REMOVED*** =============================================================================
***REMOVED*** Build Stage - includes compilers and build tools
***REMOVED*** =============================================================================
FROM dhi.io/python:3.12-dev AS builder

WORKDIR /app

***REMOVED*** Install build dependencies for psycopg2 and other compiled packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

***REMOVED*** Copy requirements first for better caching
COPY requirements.txt .

***REMOVED*** Install Python dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

***REMOVED*** =============================================================================
***REMOVED*** Runtime Stage - minimal distroless image (~95% fewer CVEs)
***REMOVED*** =============================================================================
FROM dhi.io/python:3.12 AS runtime

***REMOVED*** Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

***REMOVED*** Install only runtime dependencies (libpq for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

***REMOVED*** Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

***REMOVED*** Copy application code
COPY . .

***REMOVED*** Create non-root user for security
RUN adduser --disabled-password --gecos '' --uid 1001 appuser \
    && chown -R appuser:appuser /app
USER appuser

***REMOVED*** Expose port
EXPOSE 8000

***REMOVED*** Health check using Python (no curl in distroless)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

***REMOVED*** Run migrations and start server with uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
