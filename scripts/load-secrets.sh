#!/usr/bin/env bash
# =============================================================================
# load-secrets.sh - Load secrets from macOS Keychain, then exec a command
# =============================================================================
#
# Usage:
#   ./scripts/load-secrets.sh <command> [args...]
#
# Examples:
#   ./scripts/load-secrets.sh uvicorn app.main:app --reload
#   ./scripts/load-secrets.sh docker compose up -d
#   ./scripts/load-secrets.sh pytest
#
# Behavior:
#   - Reads each secret from macOS Keychain (service: residency-scheduler)
#   - Only sets the env var if it is NOT already set (env takes precedence)
#   - Execs the given command with the enriched environment
#
# Prerequisites:
#   Run ./scripts/init-keychain.sh first to seed the Keychain.
#
# =============================================================================

set -euo pipefail

SERVICE="residency-scheduler"

SECRETS=(
    "DB_PASSWORD"
    "REDIS_PASSWORD"
    "SECRET_KEY"
    "WEBHOOK_SECRET"
    "ANTHROPIC_API_KEY"
    "API_PASSWORD"
)

# ---------------------------------------------------------------------------
# Load each secret from Keychain if not already in the environment
# ---------------------------------------------------------------------------
for key in "${SECRETS[@]}"; do
    # Skip if already set in environment
    if [[ -n "${!key:-}" ]]; then
        continue
    fi

    # Attempt to read from Keychain; silently skip on failure
    value="$(security find-generic-password -s "${SERVICE}" -a "${key}" -w 2>/dev/null || true)"

    if [[ -n "${value}" ]]; then
        export "${key}=${value}"
    fi
done

# ---------------------------------------------------------------------------
# Exec the requested command
# ---------------------------------------------------------------------------
if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <command> [args...]" >&2
    echo "Example: $0 uvicorn app.main:app --reload" >&2
    exit 1
fi

exec "$@"
