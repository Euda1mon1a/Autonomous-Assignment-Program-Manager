#!/usr/bin/env bash
# =============================================================================
# init-keychain.sh - Seed macOS Keychain with project secrets
# =============================================================================
#
# Usage:
#   ./scripts/init-keychain.sh
#
# This script interactively prompts for each secret and stores it in the
# macOS Keychain under the service name "residency-scheduler".
#
# Secrets are stored as generic passwords and can be retrieved with:
#   security find-generic-password -s residency-scheduler -a <KEY> -w
#
# The -U flag makes this idempotent: existing entries are updated in place.
#
# After running, use load-secrets.sh to inject them into your environment:
#   ./scripts/load-secrets.sh uvicorn app.main:app --reload
#
# To verify stored secrets:
#   ./scripts/init-keychain.sh --verify
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
# Verify mode: check which secrets exist in Keychain
# ---------------------------------------------------------------------------
if [[ "${1:-}" == "--verify" ]]; then
    echo "Checking Keychain for service: ${SERVICE}"
    echo "-------------------------------------------"
    for key in "${SECRETS[@]}"; do
        if security find-generic-password -s "${SERVICE}" -a "${key}" -w >/dev/null 2>&1; then
            echo "  [OK]    ${key}"
        else
            echo "  [MISS]  ${key}"
        fi
    done
    exit 0
fi

# ---------------------------------------------------------------------------
# Interactive secret seeding
# ---------------------------------------------------------------------------
echo "============================================="
echo " Residency Scheduler - Keychain Secret Setup"
echo "============================================="
echo ""
echo "This will store secrets in macOS Keychain under service: ${SERVICE}"
echo "Press Enter to keep an existing value unchanged (if one exists)."
echo ""

for key in "${SECRETS[@]}"; do
    existing=""
    if security find-generic-password -s "${SERVICE}" -a "${key}" -w >/dev/null 2>&1; then
        existing="(current value exists)"
    fi

    read -r -s -p "  ${key} ${existing}: " value
    echo ""

    # Skip if user pressed Enter without typing anything
    if [[ -z "${value}" ]]; then
        if [[ -n "${existing}" ]]; then
            echo "    -> Keeping existing value"
        else
            echo "    -> Skipped (no value provided)"
        fi
        continue
    fi

    # -U = update if exists, -T "" = allow command-line access without prompt
    security add-generic-password \
        -U \
        -s "${SERVICE}" \
        -a "${key}" \
        -w "${value}" \
        -T ""

    echo "    -> Stored in Keychain"
done

echo ""
echo "Done. Verify with: $0 --verify"
echo "Load into env with: ./scripts/load-secrets.sh <command>"
