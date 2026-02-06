#!/usr/bin/env bash
set -euo pipefail

BACKEND_CONTAINER="${BACKEND_CONTAINER:-residency-scheduler-backend}"

info() { echo "==> $*"; }
die() { echo "ERROR: $*" >&2; exit 1; }

command -v docker >/dev/null 2>&1 || die "docker is required"

if ! docker ps --format '{{.Names}}' | grep -q "^${BACKEND_CONTAINER}$"; then
  if docker ps --format '{{.Names}}' | grep -q "^scheduler-local-backend$"; then
    BACKEND_CONTAINER="scheduler-local-backend"
    info "Detected local backend container: ${BACKEND_CONTAINER}"
  else
    die "Backend container not running: ${BACKEND_CONTAINER}"
  fi
fi

if [[ ! -f scripts/verify_constraints.py ]]; then
  die "scripts/verify_constraints.py not found"
fi

info "Copying verify_constraints.py into ${BACKEND_CONTAINER}..."
docker cp scripts/verify_constraints.py "${BACKEND_CONTAINER}:/tmp/verify_constraints.py"

info "Running constraint preflight inside ${BACKEND_CONTAINER}..."
docker exec -i -w /app -e PYTHONPATH=/app "${BACKEND_CONTAINER}" python /tmp/verify_constraints.py
