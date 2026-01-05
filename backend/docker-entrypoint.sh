#!/bin/sh
# Docker entrypoint script for backend and celery services
# Runs migrations then execs the appropriate command

set -e

# Check for dependency staleness
# Compare current requirements.txt hash with hash at build time
if [ -f /app/.requirements_hash ]; then
    BUILT_HASH=$(cat /app/.requirements_hash)
    CURRENT_HASH=$(md5sum /app/requirements.txt 2>/dev/null | cut -d' ' -f1 || md5 -q /app/requirements.txt 2>/dev/null || echo "unknown")
    if [ "$BUILT_HASH" != "$CURRENT_HASH" ] && [ "$CURRENT_HASH" != "unknown" ]; then
        echo "⚠️  WARNING: requirements.txt has changed since container was built!"
        echo "   Built with:  $BUILT_HASH"
        echo "   Current:     $CURRENT_HASH"
        echo "   Run: docker compose build backend --no-cache"
        echo ""
    fi
fi

echo "Running database migrations..."
alembic upgrade head

# Create default admin user for development environments (idempotent)
if [ "${TELEMETRY_ENVIRONMENT:-development}" = "development" ] || [ "${ENV:-development}" = "development" ]; then
    echo "Setting up default admin user for development..."
    python -c "
import sys
try:
    from app.db.session import SessionLocal
    from app.models.user import User
    from app.core.security import get_password_hash

    db = SessionLocal()
    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.email == 'admin@example.com').first()
        if existing_admin:
            print('Admin user already exists, skipping creation')
        else:
            # Create default admin user
            admin_user = User(
                username='admin',
                email='admin@example.com',
                hashed_password=get_password_hash('admin123'),
                role='admin',
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print('Admin user created successfully')
    finally:
        db.close()
except Exception as e:
    print(f'Warning: Could not create admin user: {e}', file=sys.stderr)
    # Don't exit with error - allow startup to continue
    sys.exit(0)
" 2>/dev/null || true
fi

# Check if the first argument is 'celery'
if [ "$1" = "celery" ]; then
    echo "Starting celery..."
    exec "$@"
else
    echo "Starting uvicorn..."
    # Use exec to replace shell with uvicorn (proper PID 1 signal handling)
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
fi
