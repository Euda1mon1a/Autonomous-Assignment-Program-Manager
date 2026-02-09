#!/bin/bash
# ============================================================
# Native process management shared library
# Sourced by start-native.sh, stop-native.sh, status-native.sh
#
# Provides constants, color codes, PID management, and service
# lifecycle helpers for running the residency scheduler stack
# without Docker.
# ============================================================

# Resolve project root (parent of scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Directories
PID_DIR="/tmp/residency-scheduler"
LOG_DIR="${PROJECT_ROOT}/logs/native"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Service list (ordered)
SERVICES=(backend frontend celery-worker celery-beat mcp)

# Port assignments
declare -A SERVICE_PORTS=(
  [backend]=8000
  [frontend]=3000
  [mcp]=8081
  [mlx]=8082
)

# Health check URLs
declare -A SERVICE_HEALTH_URLS=(
  [backend]="http://localhost:8000/health"
  [mcp]="http://localhost:8081/health"
  [frontend]="http://localhost:3000"
)

# -----------------------------------------------------------
# Directory helpers
# -----------------------------------------------------------

ensure_dirs() {
    mkdir -p "$PID_DIR" "$LOG_DIR"
}

# -----------------------------------------------------------
# PID management
# -----------------------------------------------------------

write_pid() {
    local service="$1"
    local pid="$2"
    ensure_dirs
    echo "$pid" > "${PID_DIR}/${service}.pid"
}

read_pid() {
    local service="$1"
    local pidfile="${PID_DIR}/${service}.pid"
    if [ -f "$pidfile" ]; then
        cat "$pidfile"
    fi
}

is_running() {
    local service="$1"
    local pid
    pid=$(read_pid "$service")
    if [ -z "$pid" ]; then
        return 1
    fi
    kill -0 "$pid" 2>/dev/null
}

kill_service() {
    local service="$1"
    local pid
    pid=$(read_pid "$service")
    if [ -z "$pid" ]; then
        return 0
    fi

    # SIGTERM first
    kill -TERM "$pid" 2>/dev/null || true

    # Wait up to 10 seconds for graceful shutdown
    local waited=0
    while [ $waited -lt 10 ] && kill -0 "$pid" 2>/dev/null; do
        sleep 1
        waited=$((waited + 1))
    done

    # SIGKILL if still alive
    if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid" 2>/dev/null || true
    fi

    rm -f "${PID_DIR}/${service}.pid"
}

# -----------------------------------------------------------
# Port helpers
# -----------------------------------------------------------

check_port() {
    local port="$1"
    lsof -i ":${port}" -sTCP:LISTEN >/dev/null 2>&1
}

wait_for_port() {
    local port="$1"
    local timeout="${2:-30}"
    local elapsed=0
    while [ $elapsed -lt "$timeout" ]; do
        if check_port "$port"; then
            return 0
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done
    return 1
}
