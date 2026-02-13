#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
PROCFILE="$ROOT_DIR/Procfile.local"
RUN_DIR="$ROOT_DIR/.local/run"
LOG_DIR="$ROOT_DIR/.local/log"

FOLLOW=false
NO_SERVICES=false
NO_DB_INIT=false

for arg in "$@"; do
  case "$arg" in
    --follow)
      FOLLOW=true
      ;;
    --no-services)
      NO_SERVICES=true
      ;;
    --no-db-init)
      NO_DB_INIT=true
      ;;
    *)
      echo "Unknown argument: $arg"
      echo "Usage: scripts/dev/start-local.sh [--follow] [--no-services] [--no-db-init]"
      exit 1
      ;;
  esac
done

log() {
  printf "[start-local] %s\n" "$*"
}

trim() {
  local var="$*"
  var="${var#${var%%[![:space:]]*}}"
  var="${var%${var##*[![:space:]]}}"
  printf "%s" "$var"
}

start_process() {
  local name="$1"
  local cmd="$2"
  local pid_file="$RUN_DIR/${name}.pid"
  local log_file="$LOG_DIR/${name}.log"
  local expected_port=""

  if [ -f "$pid_file" ]; then
    local pid
    pid="$(cat "$pid_file")"
    if kill -0 "$pid" >/dev/null 2>&1; then
      log "$name already running (pid=$pid)"
      return 0
    fi
    rm -f "$pid_file"
  fi

  case "$name" in
    backend) expected_port="8000" ;;
    frontend) expected_port="3000" ;;
    mcp) expected_port="8080" ;;
  esac

  if [ -n "$expected_port" ] && lsof -nP -iTCP:"$expected_port" -sTCP:LISTEN >/dev/null 2>&1; then
    log "Port $expected_port is already in use; refusing to start '$name'."
    return 1
  fi

  log "Starting $name"
  nohup /bin/zsh -lc "cd '$ROOT_DIR' && $cmd" >"$log_file" 2>&1 &
  local pid=$!
  echo "$pid" >"$pid_file"
}

mkdir -p "$RUN_DIR" "$LOG_DIR"

if [ ! -f "$PROCFILE" ]; then
  log "Missing $PROCFILE"
  exit 1
fi

if [ "$NO_SERVICES" = false ]; then
  "$ROOT_DIR/scripts/dev/local-services-start.sh"
fi

if [ "$NO_DB_INIT" = false ]; then
  "$ROOT_DIR/scripts/dev/local-db-init.sh"
fi

required_bins=(
  "$ROOT_DIR/backend/.venv/bin/uvicorn"
  "$ROOT_DIR/backend/.venv/bin/celery"
  "$ROOT_DIR/mcp-server/.venv/bin/python"
)
for bin in "${required_bins[@]}"; do
  if [ ! -x "$bin" ]; then
    log "Missing executable: $bin"
    log "Run make setup-mac before make local-up"
    exit 1
  fi
done

while IFS= read -r raw_line || [ -n "$raw_line" ]; do
  line="$(trim "$raw_line")"

  if [ -z "$line" ] || [ "${line#\#}" != "$line" ]; then
    continue
  fi

  name="$(trim "${line%%:*}")"
  cmd="$(trim "${line#*:}")"

  if [ -z "$name" ] || [ -z "$cmd" ]; then
    continue
  fi

  start_process "$name" "$cmd"
done <"$PROCFILE"

sleep 2
"$ROOT_DIR/scripts/dev/status-local.sh" || true

if [ "$FOLLOW" = true ]; then
  log "Following logs. Press Ctrl+C to exit."
  tail -n 50 -f "$LOG_DIR"/*.log
fi
