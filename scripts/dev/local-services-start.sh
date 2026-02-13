#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

log() {
  printf "[local-services-start] %s\n" "$*"
}

is_listening() {
  local host="$1"
  local port="$2"
  nc -z "$host" "$port" >/dev/null 2>&1
}

start_service() {
  local service="$1"
  if brew services list | awk '{print $1}' | grep -qx "$service"; then
    log "Starting brew service: $service"
    brew services start "$service" >/dev/null
    return 0
  fi
  return 1
}

wait_for_port() {
  local host="$1"
  local port="$2"
  local label="$3"
  local retries=30

  while (( retries > 0 )); do
    if nc -z "$host" "$port" >/dev/null 2>&1; then
      log "$label is accepting connections on ${host}:${port}"
      return 0
    fi
    sleep 1
    retries=$((retries - 1))
  done

  log "Timed out waiting for $label on ${host}:${port}"
  return 1
}

if is_listening "127.0.0.1" 5432 && is_listening "127.0.0.1" 6379; then
  log "PostgreSQL and Redis already listening; skipping service startup"
  exit 0
fi

if ! command -v brew >/dev/null 2>&1; then
  if is_listening "127.0.0.1" 5432 && is_listening "127.0.0.1" 6379; then
    log "Using already-running PostgreSQL/Redis services"
    exit 0
  fi
  log 'Homebrew is required when PostgreSQL/Redis are not already running. Install with: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
  exit 1
fi

if ! start_service "postgresql@15"; then
  if ! start_service "postgresql"; then
    if is_listening "127.0.0.1" 5432; then
      log "PostgreSQL already listening on 5432 (non-brew service)"
    else
      log "Homebrew formula 'postgresql@15' or 'postgresql' is required, or provide a running PostgreSQL on 5432."
      exit 1
    fi
  fi
fi

if ! start_service "redis"; then
  if is_listening "127.0.0.1" 6379; then
    log "Redis already listening on 6379 (non-brew service)"
  else
    log "Homebrew formula 'redis' is required, or provide a running Redis on 6379."
    exit 1
  fi
fi

wait_for_port "127.0.0.1" 5432 "PostgreSQL"
wait_for_port "127.0.0.1" 6379 "Redis"

log "Local services started"
