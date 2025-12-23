#!/bin/bash
# Session Start Hook - Environment Verification
# Runs at the beginning of each Claude Code session

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_FILE="$PROJECT_ROOT/.antigravity/logs/session-start.log"

log() {
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $1" >> "$LOG_FILE" 2>/dev/null || true
}

log "SESSION_START"

# Check git status
if [ -d "$PROJECT_ROOT/.git" ]; then
    DIRTY=$(git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    if [ "$DIRTY" -gt 0 ]; then
        log "WARNING: $DIRTY uncommitted changes detected"
        echo "Note: $DIRTY uncommitted changes in working directory"
    fi
fi

# Verify critical files exist
CRITICAL_FILES=(
    "CLAUDE.md"
    "backend/app/core/config.py"
    "backend/app/core/security.py"
    "docs/development/AI_RULES_OF_ENGAGEMENT.md"
    "docs/development/CLAUDE_GIT_SAFE_SYNC_CHECKLIST.md"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ ! -f "$PROJECT_ROOT/$file" ]; then
        log "ERROR: Critical file missing: $file"
        echo "Warning: Critical file missing: $file" >&2
    fi
done

# Display AI rules at session start
RULES_FILES=(
    "CLAUDE.md"
    "docs/development/AI_RULES_OF_ENGAGEMENT.md"
    "docs/development/CLAUDE_GIT_SAFE_SYNC_CHECKLIST.md"
)

# Check for debug session notes from previous sessions
DEBUG_NOTES=$(find "$PROJECT_ROOT" -maxdepth 1 -name "debug-session*.md" -type f 2>/dev/null)
if [ -n "$DEBUG_NOTES" ]; then
    log "Found debug session notes from previous session"
    echo ""
    echo "=================================================="
    echo "PREVIOUS DEBUG SESSION NOTES FOUND:"
    echo "=================================================="
    for note in $DEBUG_NOTES; do
        echo "  - $(basename "$note")"
    done
    echo ""
    echo "Consider reading these to resume debugging work."
    echo "Use: 'Read [filename] and continue debugging'"
    echo "=================================================="
    echo ""
fi

for file in "${RULES_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        echo "----- BEGIN $file -----"
        cat "$PROJECT_ROOT/$file"
        echo "----- END $file -----"
    fi
done

# Check if Docker is running (optional)
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        log "Docker: available"
    else
        log "Docker: not running"
        echo "Note: Docker is not running"
    fi
fi

log "SESSION_START complete"
exit 0
