***REMOVED*** Backend Dockerfile for Residency Scheduler
***REMOVED*** Python 3.11 slim base image for production

FROM python:3.11-slim AS base

***REMOVED*** Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

***REMOVED*** Set work directory
WORKDIR /app

***REMOVED*** Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

***REMOVED*** Copy requirements first for better caching
COPY requirements.txt .

***REMOVED*** Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

***REMOVED*** Copy application code
COPY . .

***REMOVED*** Create non-root user for security
RUN adduser --disabled-password --gecos '' --uid 1001 appuser \
    && chown -R appuser:appuser /app
USER appuser

***REMOVED*** Expose port
EXPOSE 8000

***REMOVED*** Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

***REMOVED*** Run migrations and start server with uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
