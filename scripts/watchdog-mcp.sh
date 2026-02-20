#!/bin/bash
# ============================================================
# Script: watchdog-mcp.sh
# Purpose: Health-check MCP server and restart if down
# Usage: ./scripts/watchdog-mcp.sh
#
# Designed to run every 60s via launchd (com.aapm.mcp-watchdog).
# Idempotent — exits immediately if MCP is healthy.
#
# Logs restarts to logs/native/mcp-watchdog.log
# Uses PID files at /tmp/residency-scheduler/mcp.pid
# ============================================================

set -euo pipefail

# Resolve project root and source shared library
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "${PROJECT_ROOT}/scripts/_native-lib.sh"

# Constants
MCP_PORT=$(get_service_port mcp)
MCP_HOST="127.0.0.1"
HEALTH_URL="http://${MCP_HOST}:${MCP_PORT}/health"
PID_FILE="${PID_DIR}/mcp.pid"
WATCHDOG_LOG="${LOG_DIR}/mcp-watchdog.log"
MAX_LOG_LINES=5000

# Ensure directories exist
ensure_dirs

# -----------------------------------------------------------
# Logging
# -----------------------------------------------------------
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [watchdog] $*" >> "$WATCHDOG_LOG"
}

# Rotate log if too large
if [ -f "$WATCHDOG_LOG" ] && [ "$(wc -l < "$WATCHDOG_LOG")" -gt "$MAX_LOG_LINES" ]; then
    tail -n $((MAX_LOG_LINES / 2)) "$WATCHDOG_LOG" > "${WATCHDOG_LOG}.tmp"
    mv "${WATCHDOG_LOG}.tmp" "$WATCHDOG_LOG"
    log "Log rotated (exceeded ${MAX_LOG_LINES} lines)"
fi

# -----------------------------------------------------------
# Health check
# -----------------------------------------------------------
if curl -sf --max-time 5 "$HEALTH_URL" >/dev/null 2>&1; then
    # MCP is healthy — nothing to do
    exit 0
fi

# MCP is down or unhealthy
log "MCP health check FAILED at ${HEALTH_URL}"

# -----------------------------------------------------------
# Kill stale process if PID file exists
# -----------------------------------------------------------
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        log "Killing stale MCP process (PID $OLD_PID)"
        kill -TERM "$OLD_PID" 2>/dev/null || true
        sleep 2
        # Force kill if still alive
        if kill -0 "$OLD_PID" 2>/dev/null; then
            kill -9 "$OLD_PID" 2>/dev/null || true
            log "Force-killed MCP process (PID $OLD_PID)"
        fi
    fi
    rm -f "$PID_FILE"
fi

# Also kill any orphan processes on the port
ORPHAN_PID=$(lsof -ti ":${MCP_PORT}" 2>/dev/null || true)
if [ -n "$ORPHAN_PID" ]; then
    log "Killing orphan process on port ${MCP_PORT} (PID $ORPHAN_PID)"
    kill -TERM "$ORPHAN_PID" 2>/dev/null || true
    sleep 1
fi

# -----------------------------------------------------------
# Environment setup (via shared _native-lib.sh)
# -----------------------------------------------------------

# Activate Python virtualenv
VENV_MCP="${PROJECT_ROOT}/mcp-server/.venv/bin/activate"
VENV_BACKEND="${PROJECT_ROOT}/backend/.venv/bin/activate"

if [ -f "$VENV_MCP" ]; then
    # shellcheck disable=SC1090
    source "$VENV_MCP"
elif [ -f "$VENV_BACKEND" ]; then
    # shellcheck disable=SC1090
    source "$VENV_BACKEND"
fi

# Database and API environment (from _native-lib.sh)
setup_db_env
export PYTHONPATH="${PROJECT_ROOT}/mcp-server/src:${PROJECT_ROOT}/backend"

# -----------------------------------------------------------
# Check prerequisites
# -----------------------------------------------------------

# Warn if backend is down (MCP tools won't work, but MCP server itself can start)
if ! curl -sf --max-time 3 "http://127.0.0.1:8000/health" >/dev/null 2>&1; then
    log "WARNING: Backend not running on :8000 — MCP tools will fail but server will start"
fi

# -----------------------------------------------------------
# Start MCP server
# -----------------------------------------------------------
log "Starting MCP server on ${MCP_HOST}:${MCP_PORT}..."

# Use double-fork to fully detach MCP from the watchdog's process group.
# launchd kills child processes when the watchdog exits, so we need a
# grandchild process that survives.
cd "${PROJECT_ROOT}/mcp-server/src"
python3 -c "
import os, sys
# First fork
if os.fork() > 0:
    sys.exit(0)
# New session
os.setsid()
# Second fork
if os.fork() > 0:
    sys.exit(0)
# Write PID
with open('${PID_FILE}', 'w') as f:
    f.write(str(os.getpid()))
# Redirect stdout/stderr
log = open('${LOG_DIR}/mcp.log', 'a')
os.dup2(log.fileno(), 1)
os.dup2(log.fileno(), 2)
# Exec MCP server
os.execvp('python3', [
    'python3', '-m', 'scheduler_mcp.server',
    '--host', '${MCP_HOST}',
    '--port', '${MCP_PORT}',
    '--transport', 'http',
])
"

# Wait for MCP to come up (double-fork writes PID file itself)
STARTED=false
for i in $(seq 1 30); do
    if curl -sf --max-time 3 "$HEALTH_URL" >/dev/null 2>&1; then
        STARTED=true
        break
    fi
    sleep 1
done

NEW_PID=""
if [ -f "$PID_FILE" ]; then
    NEW_PID=$(cat "$PID_FILE")
fi

if [ "$STARTED" = true ]; then
    log "MCP server started successfully (PID ${NEW_PID:-unknown})"
else
    log "MCP server failed to start within 30s (PID ${NEW_PID:-unknown}) — check ${LOG_DIR}/mcp.log"
fi
