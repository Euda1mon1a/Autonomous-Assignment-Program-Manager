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

# Supported Homebrew PostgreSQL versions (newest first)
POSTGRES_VERSIONS=(18 17 16 15)

find_brew_postgres_bin_dir() {
    local version
    local pg_dir
    for version in "${POSTGRES_VERSIONS[@]}"; do
        for pg_dir in \
            "/opt/homebrew/opt/postgresql@${version}/bin" \
            "/usr/local/opt/postgresql@${version}/bin"
        do
            if [ -d "$pg_dir" ]; then
                echo "$pg_dir"
                return 0
            fi
        done
    done
    return 1
}

detect_brew_postgres_service() {
    if ! command -v brew >/dev/null 2>&1; then
        return 1
    fi

    local version
    for version in "${POSTGRES_VERSIONS[@]}"; do
        if brew list --versions "postgresql@${version}" >/dev/null 2>&1; then
            echo "postgresql@${version}"
            return 0
        fi
    done
    return 1
}

# Add keg-only Homebrew PostgreSQL to PATH if not already available.
if ! command -v pg_isready &>/dev/null; then
    PG_BREW_BIN_DIR="$(find_brew_postgres_bin_dir || true)"
    if [ -n "${PG_BREW_BIN_DIR}" ]; then
        export PATH="${PG_BREW_BIN_DIR}:${PATH}"
    fi
fi

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

# Port assignments (Bash 3 compatible — no associative arrays on macOS)
get_service_port() {
  case "$1" in
    backend)  echo 8000 ;;
    frontend) echo 3000 ;;
    mcp)      echo 8081 ;;
    mlx)      echo 8082 ;;
    *)        echo "" ;;
  esac
}

# Health check URLs
get_service_health_url() {
  case "$1" in
    backend)  echo "http://localhost:8000/health" ;;
    mcp)      echo "http://localhost:8081/health" ;;
    frontend) echo "http://localhost:3000" ;;
    *)        echo "" ;;
  esac
}

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
