#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
RUN_DIR="$ROOT_DIR/.local/run"

WITH_SERVICES=false

for arg in "$@"; do
  case "$arg" in
    --with-services)
      WITH_SERVICES=true
      ;;
    *)
      echo "Unknown argument: $arg"
      echo "Usage: scripts/dev/stop-local.sh [--with-services]"
      exit 1
      ;;
  esac
done

log() {
  printf "[stop-local] %s\n" "$*"
}

stop_pid_file() {
  local pid_file="$1"
  local name
  name="$(basename "$pid_file" .pid)"

  if [ ! -f "$pid_file" ]; then
    return 0
  fi

  local pid
  pid="$(cat "$pid_file")"

  if kill -0 "$pid" >/dev/null 2>&1; then
    log "Stopping $name (pid=$pid)"
    kill "$pid" >/dev/null 2>&1 || true

    local retries=10
    while kill -0 "$pid" >/dev/null 2>&1 && (( retries > 0 )); do
      sleep 1
      retries=$((retries - 1))
    done

    if kill -0 "$pid" >/dev/null 2>&1; then
      log "Force stopping $name (pid=$pid)"
      kill -9 "$pid" >/dev/null 2>&1 || true
    fi
  else
    log "$name is not running"
  fi

  rm -f "$pid_file"
}

if [ -d "$RUN_DIR" ]; then
  while IFS= read -r pid_file; do
    stop_pid_file "$pid_file"
  done < <(find "$RUN_DIR" -name '*.pid' | sort)
fi

if [ "$WITH_SERVICES" = true ]; then
  "$ROOT_DIR/scripts/dev/local-services-stop.sh"
fi

log "Local process shutdown complete"
