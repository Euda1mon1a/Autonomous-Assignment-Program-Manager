#!/bin/bash
# ============================================================
# Script: stop-native.sh
# Purpose: Stop native (non-Docker) services
# Usage: ./scripts/stop-native.sh [--all] [--force] [--only SERVICE]
#
# Options:
#   --all          Also stop Postgres and Redis (brew services)
#   --force        SIGKILL immediately instead of graceful SIGTERM
#   --only SERVICE Stop a single service only
# ============================================================

set -euo pipefail

# Source shared library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./_native-lib.sh
source "${SCRIPT_DIR}/_native-lib.sh"

# -----------------------------------------------------------
# Parse arguments
# -----------------------------------------------------------
STOP_ALL=false
FORCE=false
ONLY=""

for arg in "$@"; do
    case "$arg" in
        --all)   STOP_ALL=true ;;
        --force) FORCE=true ;;
        --only)  ;; # value captured below
        -h|--help)
            echo "Usage: $0 [--all] [--force] [--only SERVICE]"
            echo ""
            echo "Options:"
            echo "  --all          Also stop Postgres and Redis via brew"
            echo "  --force        SIGKILL immediately (no graceful wait)"
            echo "  --only SERVICE Stop only the named service"
            echo ""
            echo "Services: ${SERVICES[*]} mlx"
            exit 0
            ;;
        *)
            # Capture --only value (previous arg was --only)
            if [ "${PREV_ARG:-}" = "--only" ]; then
                ONLY="$arg"
            else
                echo -e "${RED}Unknown option: $arg${NC}"
                echo "Run $0 --help for usage"
                exit 1
            fi
            ;;
    esac
    PREV_ARG="$arg"
done

# -----------------------------------------------------------
# Force-kill variant
# -----------------------------------------------------------
force_kill_service() {
    local service="$1"
    local pid
    pid=$(read_pid "$service")
    if [ -z "$pid" ]; then
        return 0
    fi
    kill -9 "$pid" 2>/dev/null || true
    rm -f "${PID_DIR}/${service}.pid"
}

# -----------------------------------------------------------
# Stop a single service with output
# -----------------------------------------------------------
stop_one() {
    local service="$1"

    if ! is_running "$service"; then
        # Clean up stale PID file if it exists
        local pidfile="${PID_DIR}/${service}.pid"
        if [ -f "$pidfile" ]; then
            rm -f "$pidfile"
            echo -e "  ${YELLOW}[--]${NC} $service: stale PID file cleaned"
        else
            echo -e "  ${YELLOW}[--]${NC} $service: not running"
        fi
        return 0
    fi

    local pid
    pid=$(read_pid "$service")

    if [ "$FORCE" = true ]; then
        force_kill_service "$service"
        echo -e "  ${GREEN}[OK]${NC} $service (PID $pid) killed"
    else
        kill_service "$service"
        echo -e "  ${GREEN}[OK]${NC} $service (PID $pid) stopped"
    fi
}

# -----------------------------------------------------------
# Main
# -----------------------------------------------------------
echo -e "${BLUE}=== Stopping Native Services ===${NC}"
echo ""

# Reverse dependency order (+ optional mlx)
STOP_ORDER=(mlx mcp frontend celery-beat celery-worker backend)

if [ -n "$ONLY" ]; then
    stop_one "$ONLY"
else
    for svc in "${STOP_ORDER[@]}"; do
        stop_one "$svc"
    done
fi

# Optionally stop infrastructure
if [ "$STOP_ALL" = true ]; then
    echo ""
    echo -e "${BLUE}=== Stopping Infrastructure ===${NC}"

    echo -n "  Redis: "
    if brew services stop redis >/dev/null 2>&1; then
        echo -e "${GREEN}stopped${NC}"
    else
        echo -e "${YELLOW}already stopped or not managed by brew${NC}"
    fi

    echo -n "  PostgreSQL: "
    if command -v brew >/dev/null 2>&1; then
        PG_STOPPED=false
        for version in 18 17 16 15; do
            formula="postgresql@${version}"
            if brew list --versions "${formula}" >/dev/null 2>&1; then
                if brew services stop "${formula}" >/dev/null 2>&1; then
                    echo -e "${GREEN}stopped (${formula})${NC}"
                    PG_STOPPED=true
                    break
                fi
            fi
        done
        if [ "$PG_STOPPED" = false ]; then
            echo -e "${YELLOW}already stopped or not managed by brew${NC}"
        fi
    else
        echo -e "${YELLOW}brew not available${NC}"
    fi
fi

# Summary
echo ""
STILL_RUNNING=0
for svc in "${STOP_ORDER[@]}"; do
    if is_running "$svc"; then
        STILL_RUNNING=$((STILL_RUNNING + 1))
    fi
done

if [ $STILL_RUNNING -eq 0 ]; then
    echo -e "${GREEN}All services stopped.${NC}"
else
    echo -e "${YELLOW}${STILL_RUNNING} service(s) still running.${NC}"
fi
