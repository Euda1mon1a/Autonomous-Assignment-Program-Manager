#!/usr/bin/env bash
set -euo pipefail

log() {
  printf "[local-services-stop] %s\n" "$*"
}

if ! command -v brew >/dev/null 2>&1; then
  log "Homebrew not found; skipping service stop."
  exit 0
fi

for service in redis postgresql@15 postgresql; do
  if brew services list | awk '{print $1}' | grep -qx "$service"; then
    log "Stopping brew service: $service"
    brew services stop "$service" >/dev/null || true
  fi
done

log "Requested local services shutdown"
