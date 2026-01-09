#!/bin/bash
# ============================================================
# Hook: pre-bash-dev-check.sh
# Purpose: Ensure dev environment for fast iteration (hot reload)
# Event: PreToolUse:Bash
# Session: 082
#
# Prevents:
#   - Running production docker-compose without dev overlay
#   - npm build when npm run dev would suffice
#   - Docker rebuilds when volume mounts would work
#   - Missing --reload on uvicorn commands
# ============================================================

INPUT=$(cat)

# Extract command using jq or fallback
if command -v jq &> /dev/null; then
    COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null || echo "")
else
    COMMAND=$(echo "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' | head -1)
fi

[ -z "$COMMAND" ] && exit 0

# ============================================================
# Check 1: Docker Compose without dev overlay
# ============================================================
if echo "$COMMAND" | grep -qE 'docker-compose\s+up|docker\s+compose\s+up'; then
    if ! echo "$COMMAND" | grep -qE '\-f\s+docker-compose\.(dev|local)\.yml'; then
        echo "" >&2
        echo "⚠️  DEV CHECK: docker-compose up without dev config detected" >&2
        echo "   For hot reload, use:" >&2
        echo "   docker-compose -f docker-compose.dev.yml up" >&2
        echo "   Or for full local stack:" >&2
        echo "   docker-compose -f docker-compose.local.yml up" >&2
        echo "" >&2
        # Don't block, just warn
    fi
fi

# ============================================================
# Check 2: Docker build when not necessary
# ============================================================
if echo "$COMMAND" | grep -qE 'docker-compose.*build|docker\s+build'; then
    if ! echo "$COMMAND" | grep -qE '\-\-no-cache|\-\-force'; then
        echo "" >&2
        echo "⚠️  DEV CHECK: Docker build detected" >&2
        echo "   Volume mounts in dev mode avoid rebuilds." >&2
        echo "   If you need to rebuild, consider:" >&2
        echo "   - docker-compose -f docker-compose.dev.yml up --build" >&2
        echo "   - Or ./scripts/rebuild-containers.sh for fresh rebuild" >&2
        echo "" >&2
    fi
fi

# ============================================================
# Check 3: npm build instead of npm run dev
# ============================================================
if echo "$COMMAND" | grep -qE 'npm\s+run\s+build'; then
    # Check if we're in frontend directory context
    if echo "$COMMAND" | grep -qE 'frontend|cd\s+frontend'; then
        echo "" >&2
        echo "⚠️  DEV CHECK: npm run build detected" >&2
        echo "   For hot reload during development, use:" >&2
        echo "   cd frontend && npm run dev" >&2
        echo "   Build is only needed for production deployment." >&2
        echo "" >&2
    fi
fi

# ============================================================
# Check 4: uvicorn without --reload
# ============================================================
if echo "$COMMAND" | grep -qE 'uvicorn.*app\.main:app'; then
    if ! echo "$COMMAND" | grep -q '\-\-reload'; then
        echo "" >&2
        echo "⚠️  DEV CHECK: uvicorn without --reload detected" >&2
        echo "   For hot reload during development, add --reload:" >&2
        echo "   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" >&2
        echo "" >&2
    fi
fi

# ============================================================
# Check 5: next start instead of next dev
# ============================================================
if echo "$COMMAND" | grep -qE 'npm\s+run\s+start|next\s+start'; then
    if echo "$COMMAND" | grep -qE 'frontend|cd\s+frontend'; then
        echo "" >&2
        echo "⚠️  DEV CHECK: next start (production mode) detected" >&2
        echo "   For hot reload during development, use:" >&2
        echo "   npm run dev" >&2
        echo "   'next start' requires a prior build and has no hot reload." >&2
        echo "" >&2
    fi
fi

# ============================================================
# Check 6: pytest with docker exec (slow) vs local
# ============================================================
if echo "$COMMAND" | grep -qE 'docker\s+exec.*pytest'; then
    echo "" >&2
    echo "💡 DEV TIP: Running pytest via docker exec" >&2
    echo "   For faster iteration, run locally if deps are installed:" >&2
    echo "   cd backend && pytest tests/" >&2
    echo "" >&2
fi

# ============================================================
# Check 7: Alembic migrations inside container
# ============================================================
if echo "$COMMAND" | grep -qE 'docker\s+exec.*alembic'; then
    echo "" >&2
    echo "💡 DEV TIP: Running alembic via docker exec" >&2
    echo "   If DATABASE_URL is set locally, run directly:" >&2
    echo "   cd backend && alembic upgrade head" >&2
    echo "" >&2
fi

# Always allow the command to proceed (warnings only)
exit 0
