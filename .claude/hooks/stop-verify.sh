#!/bin/bash
# Stop Verification Hook - Session End Checks
# Runs when Claude Code session ends

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_FILE="$PROJECT_ROOT/.antigravity/logs/session-stop.log"

log() {
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $1" >> "$LOG_FILE" 2>/dev/null || true
}

log "SESSION_STOP"

# Check for uncommitted changes
if [ -d "$PROJECT_ROOT/.git" ]; then
    DIRTY=$(git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    if [ "$DIRTY" -gt 0 ]; then
        log "WARNING: Session ending with $DIRTY uncommitted changes"
        echo "Note: $DIRTY uncommitted changes remaining"

        # List the changed files
        git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null | head -10 | while read line; do
            log "  - $line"
        done
    else
        log "Git status: clean"
    fi
fi

# Check if tests were run (look for recent pytest cache)
if [ -d "$PROJECT_ROOT/backend/.pytest_cache" ]; then
    CACHE_AGE=$(find "$PROJECT_ROOT/backend/.pytest_cache" -name "*.json" -mmin -30 2>/dev/null | wc -l | tr -d ' ')
    if [ "$CACHE_AGE" -gt 0 ]; then
        log "Tests: run within last 30 minutes"
    else
        log "Tests: not run recently"
        echo "Note: Consider running tests before ending session"
    fi
fi

log "SESSION_STOP complete"
exit 0
