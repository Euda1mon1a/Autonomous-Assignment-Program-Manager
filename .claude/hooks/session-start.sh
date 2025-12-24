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

# Display current git branch prominently
if [ -d "$PROJECT_ROOT/.git" ]; then
    CURRENT_BRANCH=$(git -C "$PROJECT_ROOT" branch --show-current 2>/dev/null || echo "unknown")
    if [ -n "$CURRENT_BRANCH" ]; then
        echo ""
        echo "========================================"
        echo "  Current Branch: $CURRENT_BRANCH"
        echo "========================================"
        echo ""
        log "BRANCH: $CURRENT_BRANCH"

        # Warn if on main/master
        if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
            echo "WARNING: You are on the $CURRENT_BRANCH branch!"
            echo "Create a feature branch before making changes."
            echo ""
        fi

        # Check if branch is tracking a remote
        UPSTREAM=$(git -C "$PROJECT_ROOT" rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "")
        if [ -z "$UPSTREAM" ]; then
            echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            echo "  DANGER: Branch '$CURRENT_BRANCH' has NO REMOTE TRACKING!"
            echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            echo ""
            echo "  This branch is LOCAL ONLY. Work here will NOT"
            echo "  be on GitHub until you push with:"
            echo ""
            echo "    git push -u origin $CURRENT_BRANCH"
            echo ""
            echo "  Or create a proper branch from origin/main:"
            echo ""
            echo "    git fetch origin"
            echo "    git checkout -b <new-branch> origin/main"
            echo "    git push -u origin <new-branch>"
            echo ""
            echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            echo ""
            log "DANGER: No remote tracking for branch $CURRENT_BRANCH"
        else
            # Branch has upstream, verify it exists on remote
            git -C "$PROJECT_ROOT" fetch origin "$CURRENT_BRANCH" --dry-run 2>/dev/null
            if [ $? -ne 0 ]; then
                echo "WARNING: Remote branch may not exist yet."
                echo "Run: git push -u origin $CURRENT_BRANCH"
                echo ""
                log "WARNING: Remote branch may not exist: $CURRENT_BRANCH"
            else
                log "Remote tracking OK: $UPSTREAM"
            fi
        fi
    fi
fi

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
