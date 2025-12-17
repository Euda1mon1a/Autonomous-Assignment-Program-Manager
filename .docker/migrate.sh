***REMOVED***!/bin/bash
***REMOVED*** migrate.sh - Run database migrations
***REMOVED***
***REMOVED*** Usage as init container:
***REMOVED***   docker run --rm myapp:latest /app/migrate.sh
***REMOVED***
***REMOVED*** Or in docker-compose:
***REMOVED***   migrate:
***REMOVED***     image: myapp:latest
***REMOVED***     command: /app/migrate.sh
***REMOVED***     depends_on:
***REMOVED***       - db

set -e

echo "Running database migrations..."
cd /app
alembic upgrade head
echo "Migrations complete."
