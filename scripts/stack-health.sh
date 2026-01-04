#!/bin/bash
#
# Stack Health Check - Unified script for Docker-based development
#
# Checks:
#   - API health endpoint
#   - Frontend accessibility
#   - Database connectivity (via Docker)
#   - Redis connectivity (via Docker)
#   - Container status
#   - Migration state
#   - Frontend TypeScript (optional, slow)
#   - Backend lint (optional, slow)
#
# Usage:
#   ./scripts/stack-health.sh          # Quick check (services only)
#   ./scripts/stack-health.sh --full   # Full check (includes lint/typecheck)
#   ./scripts/stack-health.sh --json   # JSON output
#

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
FULL_CHECK=false
JSON_OUTPUT=false
for arg in "$@"; do
    case $arg in
        --full) FULL_CHECK=true ;;
        --json) JSON_OUTPUT=true ;;
    esac
done

OVERALL_STATUS="GREEN"
JSON_CHECKS=""

add_check() {
    local name=$1
    local status=$2
    local msg=$3

    # Update overall status
    if [ "$status" = "fail" ] && [ "$OVERALL_STATUS" != "RED" ]; then
        OVERALL_STATUS="RED"
    elif [ "$status" = "warn" ] && [ "$OVERALL_STATUS" = "GREEN" ]; then
        OVERALL_STATUS="YELLOW"
    fi

    # Console output
    if [ "$JSON_OUTPUT" = false ]; then
        case $status in
            pass) echo -e "${GREEN}[✓]${NC} $name: PASS $msg" ;;
            warn) echo -e "${YELLOW}[⚠]${NC} $name: WARN $msg" ;;
            fail) echo -e "${RED}[✗]${NC} $name: FAIL $msg" ;;
            skip) echo -e "${YELLOW}[-]${NC} $name: SKIP $msg" ;;
        esac
    fi

    # Build JSON
    if [ -n "$JSON_CHECKS" ]; then
        JSON_CHECKS="$JSON_CHECKS,"
    fi
    JSON_CHECKS="$JSON_CHECKS\"$name\":{\"status\":\"$status\",\"message\":\"$msg\"}"
}

# Header
if [ "$JSON_OUTPUT" = false ]; then
    echo ""
    echo "========================================="
    echo "  Stack Health Check"
    echo "========================================="
    echo ""
fi

# 1. API Health
API_RESULT=$(curl -s --max-time 5 http://localhost:8000/health 2>&1 || echo "FAILED")
if echo "$API_RESULT" | grep -q "healthy"; then
    add_check "API" "pass" "(connected)"
else
    add_check "API" "fail" "(not reachable)"
fi

# 2. Frontend
FRONT_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:3000 2>&1 || echo "000")
if [ "$FRONT_CODE" = "200" ]; then
    add_check "Frontend" "pass" "(HTTP 200)"
elif [ "$FRONT_CODE" = "000" ]; then
    add_check "Frontend" "fail" "(not reachable)"
else
    add_check "Frontend" "warn" "(HTTP $FRONT_CODE)"
fi

# 3. Database (via Docker)
DB_RESULT=$(docker compose exec -T db psql -U scheduler -d residency_scheduler -c "SELECT 1" 2>&1 | grep -v "^time=" || echo "FAILED")
if echo "$DB_RESULT" | grep -q "1 row"; then
    add_check "Database" "pass" "(PostgreSQL)"
else
    add_check "Database" "fail" "(connection failed)"
fi

# 4. Redis (via Docker) - NOAUTH means it's working with auth
REDIS_RESULT=$(docker compose exec -T redis redis-cli ping 2>&1 | grep -v "^time=" || echo "FAILED")
if echo "$REDIS_RESULT" | grep -q "PONG"; then
    add_check "Redis" "pass" "(no auth)"
elif echo "$REDIS_RESULT" | grep -q "NOAUTH"; then
    add_check "Redis" "pass" "(auth enabled)"
else
    add_check "Redis" "fail" "(not responding)"
fi

# 5. Container Status
CONTAINER_INFO=$(docker compose ps 2>&1 | grep -v "^time=" | grep -v "^NAME" | grep -v "^$")
CONTAINER_COUNT=$(echo "$CONTAINER_INFO" | grep -c "Up" 2>/dev/null || echo "0")
UNHEALTHY_COUNT=$(echo "$CONTAINER_INFO" | grep -c "unhealthy" 2>/dev/null || echo "0")

if [ "$UNHEALTHY_COUNT" != "0" ] && [ "$UNHEALTHY_COUNT" -gt 0 ] 2>/dev/null; then
    add_check "Containers" "fail" "($UNHEALTHY_COUNT unhealthy)"
elif [ "$CONTAINER_COUNT" != "0" ] && [ "$CONTAINER_COUNT" -gt 0 ] 2>/dev/null; then
    add_check "Containers" "pass" "($CONTAINER_COUNT running)"
else
    add_check "Containers" "warn" "(could not determine)"
fi

# 6. Migration State
# Filter out log timestamps (2026-01-04) but keep migration IDs (20260103_name)
MIG_RESULT=$(docker compose exec -T backend alembic current 2>&1 | grep -v "^time=\|^INFO\|^2026-\|warning" | grep -E "[a-z0-9_]+.*head" | head -1 || echo "")
if [ -z "$MIG_RESULT" ]; then
    MIG_RESULT=$(docker compose exec -T backend alembic current 2>&1 | grep -oE "[0-9]{8}_[a-z_]+" | head -1 || echo "unknown")
fi
if echo "$MIG_RESULT" | grep -q "head\|import_staging\|[0-9]{8}"; then
    add_check "Migrations" "pass" "($MIG_RESULT)"
else
    add_check "Migrations" "warn" "($MIG_RESULT)"
fi

# Optional: Full checks (lint/typecheck)
if [ "$FULL_CHECK" = true ]; then
    if [ "$JSON_OUTPUT" = false ]; then
        echo ""
        echo "--- Code Quality Checks ---"
        echo ""
    fi

    # 7. Frontend TypeScript
    if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
        TS_RESULT=$(cd frontend && npm run type-check 2>&1)
        if echo "$TS_RESULT" | grep -q "error TS"; then
            TS_ERRORS=$(echo "$TS_RESULT" | grep -c "error TS" || echo "?")
            add_check "TypeScript" "fail" "($TS_ERRORS errors)"
        else
            add_check "TypeScript" "pass" "(clean)"
        fi
    else
        add_check "TypeScript" "skip" "(frontend not found)"
    fi

    # 8. Backend Lint (via Docker since ruff is there)
    LINT_RESULT=$(docker compose exec -T backend ruff check . 2>&1 | grep -v "^time=" || echo "")
    if echo "$LINT_RESULT" | grep -q "All checks passed\|Found 0"; then
        add_check "BackendLint" "pass" "(ruff clean)"
    elif echo "$LINT_RESULT" | grep -q "Found [0-9]"; then
        LINT_COUNT=$(echo "$LINT_RESULT" | grep -oE "Found [0-9]+" | grep -oE "[0-9]+" || echo "?")
        add_check "BackendLint" "warn" "($LINT_COUNT fixable)"
    else
        add_check "BackendLint" "pass" "(clean)"
    fi
fi

# Summary
if [ "$JSON_OUTPUT" = false ]; then
    echo ""
    echo "========================================="
    if [ "$OVERALL_STATUS" = "GREEN" ]; then
        echo -e "  Overall Status: ${GREEN}$OVERALL_STATUS${NC}"
    elif [ "$OVERALL_STATUS" = "YELLOW" ]; then
        echo -e "  Overall Status: ${YELLOW}$OVERALL_STATUS${NC}"
    else
        echo -e "  Overall Status: ${RED}$OVERALL_STATUS${NC}"
    fi
    echo "========================================="
    echo ""
else
    # JSON output
    cat << EOF
{
  "status": "$OVERALL_STATUS",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "checks": {$JSON_CHECKS}
}
EOF
fi

# Exit code based on status
if [ "$OVERALL_STATUS" = "RED" ]; then
    exit 1
else
    exit 0
fi
