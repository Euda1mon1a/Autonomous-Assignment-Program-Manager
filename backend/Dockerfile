***REMOVED*** Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

***REMOVED*** Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

***REMOVED*** Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

***REMOVED*** Copy application code
COPY . .

***REMOVED*** Expose port
EXPOSE 8000

***REMOVED*** Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
