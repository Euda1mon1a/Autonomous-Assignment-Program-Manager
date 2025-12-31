#!/bin/bash

# Celery Startup Script for Residency Scheduler
# Starts Celery worker and beat scheduler with proper configuration
#
# Usage:
#   ./scripts/start-celery.sh [worker|beat|both]
#
# Examples:
#   ./scripts/start-celery.sh both      # Start worker and beat (default)
#   ./scripts/start-celery.sh worker    # Start worker only
#   ./scripts/start-celery.sh beat      # Start beat only

set -e

# Configuration
CELERY_APP="app.core.celery_app"
LOG_LEVEL="${CELERY_LOG_LEVEL:-info}"
WORKER_CONCURRENCY="${CELERY_WORKER_CONCURRENCY:-4}"
WORKER_QUEUES="${CELERY_QUEUES:-default,resilience,notifications}"
WORKER_MAX_TASKS="${CELERY_MAX_TASKS_PER_CHILD:-1000}"
BEAT_PIDFILE="${CELERY_BEAT_PIDFILE:-/tmp/celerybeat.pid}"
WORKER_PIDFILE="${CELERY_WORKER_PIDFILE:-/tmp/celeryworker.pid}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Determine what to start
# Options: worker, beat, or both (default)
MODE="${1:-both}"

# Function to cleanup on exit
# Handles SIGINT (Ctrl+C) and SIGTERM (kill command)
# Ensures graceful shutdown of Celery processes
cleanup() {
    echo -e "${YELLOW}Shutting down Celery services...${NC}"

    # Stop Celery worker if running
    # TERM signal allows tasks to finish before shutdown
    if [ -f "$WORKER_PIDFILE" ]; then
        WORKER_PID=$(cat "$WORKER_PIDFILE")
        echo "Stopping Celery worker (PID: $WORKER_PID)..."
        kill -TERM "$WORKER_PID" 2>/dev/null || true
        rm -f "$WORKER_PIDFILE"
    fi

    # Stop Celery beat if running
    # Beat scheduler can stop immediately (no tasks in progress)
    if [ -f "$BEAT_PIDFILE" ]; then
        BEAT_PID=$(cat "$BEAT_PIDFILE")
        echo "Stopping Celery beat (PID: $BEAT_PID)..."
        kill -TERM "$BEAT_PID" 2>/dev/null || true
        rm -f "$BEAT_PIDFILE"
    fi

    echo -e "${GREEN}Celery services stopped gracefully${NC}"
    exit 0
}

# Trap signals for graceful shutdown
trap cleanup SIGINT SIGTERM

# Check if we're in the backend directory
# Celery app requires backend directory structure to import modules
if [ ! -f "app/core/celery_app.py" ]; then
    echo -e "${RED}Error: Must be run from the backend directory${NC}"
    echo "Usage: cd backend && ../scripts/start-celery.sh"
    exit 1
fi

# Check if Redis is available
# Redis is required as Celery broker and result backend
echo "Checking Redis connection..."
REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
if ! python -c "import redis; r = redis.from_url('$REDIS_URL'); r.ping()" 2>/dev/null; then
    echo -e "${RED}Error: Cannot connect to Redis at $REDIS_URL${NC}"
    echo "Make sure Redis is running and REDIS_URL is configured correctly"
    exit 1
fi
echo -e "${GREEN}Redis connection OK${NC}"

# Check if database is available
# Non-fatal warning since some tasks don't require database
echo "Checking database connection..."
if ! python -c "from app.core.database import engine; engine.connect()" 2>/dev/null; then
    echo -e "${YELLOW}Warning: Cannot connect to database${NC}"
    echo "Some tasks may fail if database is not available"
fi

# Start Celery worker
# Processes background tasks from configured queues
start_worker() {
    echo -e "${GREEN}Starting Celery worker...${NC}"
    echo "  App: $CELERY_APP"
    echo "  Queues: $WORKER_QUEUES"
    echo "  Concurrency: $WORKER_CONCURRENCY"
    echo "  Log level: $LOG_LEVEL"
    echo "  Max tasks per child: $WORKER_MAX_TASKS"

    # Start worker with production-grade limits
    # --time-limit: Hard kill tasks after 10 minutes
    # --soft-time-limit: Send SIGTERM after 9 minutes
    # --max-tasks-per-child: Restart worker after N tasks (prevent memory leaks)
    # Try --detach first (requires log directory), fallback to background process
    celery -A "$CELERY_APP" worker \
        --loglevel="$LOG_LEVEL" \
        -Q "$WORKER_QUEUES" \
        --concurrency="$WORKER_CONCURRENCY" \
        --max-tasks-per-child="$WORKER_MAX_TASKS" \
        --time-limit=600 \
        --soft-time-limit=540 \
        --pidfile="$WORKER_PIDFILE" \
        --logfile=/var/log/celery/worker.log \
        --detach 2>/dev/null || \
    celery -A "$CELERY_APP" worker \
        --loglevel="$LOG_LEVEL" \
        -Q "$WORKER_QUEUES" \
        --concurrency="$WORKER_CONCURRENCY" \
        --max-tasks-per-child="$WORKER_MAX_TASKS" \
        --time-limit=600 \
        --soft-time-limit=540 \
        --pidfile="$WORKER_PIDFILE" &

    echo -e "${GREEN}Celery worker started${NC}"
}

# Start Celery beat
# Scheduler for periodic tasks (like cron)
start_beat() {
    echo -e "${GREEN}Starting Celery beat scheduler...${NC}"
    echo "  App: $CELERY_APP"
    echo "  Log level: $LOG_LEVEL"

    # Beat manages the schedule, doesn't execute tasks
    # Only one beat instance should run at a time
    # Try --detach first (requires log directory), fallback to background process
    celery -A "$CELERY_APP" beat \
        --loglevel="$LOG_LEVEL" \
        --pidfile="$BEAT_PIDFILE" \
        --logfile=/var/log/celery/beat.log \
        --detach 2>/dev/null || \
    celery -A "$CELERY_APP" beat \
        --loglevel="$LOG_LEVEL" \
        --pidfile="$BEAT_PIDFILE" &

    echo -e "${GREEN}Celery beat started${NC}"
}

# Main execution
echo "========================================="
echo "Celery Startup Script"
echo "========================================="

case "$MODE" in
    worker)
        start_worker
        ;;
    beat)
        start_beat
        ;;
    both)
        start_worker
        start_beat
        ;;
    *)
        echo -e "${RED}Error: Invalid mode '$MODE'${NC}"
        echo "Usage: $0 [worker|beat|both]"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Celery services are running${NC}"
echo "Press Ctrl+C to stop gracefully"
echo ""

# Monitor processes
# Display PID file locations for process management
if [ "$MODE" == "both" ] || [ "$MODE" == "worker" ]; then
    echo "Worker PID file: $WORKER_PIDFILE"
fi

if [ "$MODE" == "both" ] || [ "$MODE" == "beat" ]; then
    echo "Beat PID file: $BEAT_PIDFILE"
fi

# Keep script running to handle signals
# This allows graceful cleanup on Ctrl+C or SIGTERM
if [ -n "$BASH" ]; then
    # In bash, wait for all background jobs
    # More efficient than polling
    wait
else
    # In other shells, poll with sleep
    # Keeps script alive for signal handling
    while true; do
        sleep 60
    done
fi
