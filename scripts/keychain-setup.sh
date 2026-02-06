#!/bin/bash
# ============================================================
# Script: keychain-setup.sh
# Purpose: Seed AAPM production secrets into macOS Keychain
# Usage: ./scripts/keychain-setup.sh
#
# Description:
#   One-time setup to store production secrets in macOS Keychain
#   instead of plaintext .env files. Uses the same ai-secrets
#   keychain pattern as the Mac Mini bootstrap.
#
#   Secrets stored:
#     aapm-db-password       PostgreSQL password
#     aapm-redis-password    Redis auth password
#     aapm-secret-key        JWT signing key
#     aapm-webhook-secret    Webhook validation secret
#     aapm-api-username      MCP server API username
#     aapm-api-password      MCP server API password
#
#   After running this script, use launch-with-keychain.sh
#   to start Docker with secrets pulled from Keychain.
#
# Options:
#   --rotate    Regenerate all auto-generated secrets
#   --verify    Check which secrets exist without modifying
# ============================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

KEYCHAIN="ai-secrets.keychain"
SERVICE_ACCOUNT="aapm"

# Secrets that get auto-generated (random tokens)
AUTO_SECRETS=(
    "aapm-db-password"
    "aapm-redis-password"
    "aapm-secret-key"
    "aapm-webhook-secret"
)

# Secrets that require user input
MANUAL_SECRETS=(
    "aapm-api-username"
    "aapm-api-password"
)

# --- Helpers ---

get_secret() {
    security find-generic-password -a "$SERVICE_ACCOUNT" -s "$1" -w "$KEYCHAIN" 2>/dev/null || \
        security find-generic-password -a "$SERVICE_ACCOUNT" -s "$1" -w 2>/dev/null || \
        echo ""
}

set_secret() {
    local key="$1"
    local value="$2"
    # -U updates if exists, -T "" allows any app to access
    security add-generic-password -a "$SERVICE_ACCOUNT" -s "$key" -w "$value" -T "" -U "$KEYCHAIN" 2>/dev/null || \
        security add-generic-password -a "$SERVICE_ACCOUNT" -s "$key" -w "$value" -T "" -U 2>/dev/null
}

generate_token() {
    python3 -c "import secrets; print(secrets.token_urlsafe(${1:-48}))"
}

# --- Parse args ---

MODE="setup"
for arg in "$@"; do
    case $arg in
        --rotate) MODE="rotate" ;;
        --verify) MODE="verify" ;;
    esac
done

# --- Verify keychain exists ---

echo -e "${CYAN}AAPM Keychain Secret Manager${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! security show-keychain-info "$KEYCHAIN" &>/dev/null; then
    echo -e "${YELLOW}Keychain '$KEYCHAIN' not found.${NC}"
    echo "Create it with: security create-keychain \"$KEYCHAIN\""
    echo "Then add to search list: security list-keychains -d user -s \"$KEYCHAIN\" \$(security list-keychains -d user | tr -d '\"')"
    exit 1
fi

# --- Verify mode ---

if [ "$MODE" = "verify" ]; then
    echo -e "\n${CYAN}Checking existing secrets:${NC}"
    ALL_GOOD=true
    for key in "${AUTO_SECRETS[@]}" "${MANUAL_SECRETS[@]}"; do
        val=$(get_secret "$key")
        if [ -n "$val" ]; then
            # Show first 8 chars only
            preview="${val:0:8}..."
            echo -e "  ${GREEN}✓${NC} $key = $preview"
        else
            echo -e "  ${RED}✗${NC} $key = (not set)"
            ALL_GOOD=false
        fi
    done
    if $ALL_GOOD; then
        echo -e "\n${GREEN}All secrets present. Ready for launch-with-keychain.sh${NC}"
    else
        echo -e "\n${YELLOW}Missing secrets. Run: ./scripts/keychain-setup.sh${NC}"
    fi
    exit 0
fi

# --- Setup / Rotate ---

echo ""

# Auto-generated secrets
for key in "${AUTO_SECRETS[@]}"; do
    existing=$(get_secret "$key")
    if [ -n "$existing" ] && [ "$MODE" != "rotate" ]; then
        echo -e "  ${GREEN}✓${NC} $key already set (skip)"
    else
        if [ "$MODE" = "rotate" ] && [ -n "$existing" ]; then
            echo -e "  ${YELLOW}↻${NC} Rotating $key..."
        else
            echo -e "  ${CYAN}+${NC} Generating $key..."
        fi
        token=$(generate_token 48)
        set_secret "$key" "$token"
        echo -e "    ${GREEN}✓${NC} Stored (${token:0:8}...)"
    fi
done

# Manual secrets
for key in "${MANUAL_SECRETS[@]}"; do
    existing=$(get_secret "$key")
    if [ -n "$existing" ] && [ "$MODE" != "rotate" ]; then
        echo -e "  ${GREEN}✓${NC} $key already set (skip)"
    else
        echo -e -n "  ${CYAN}?${NC} Enter value for $key: "
        read -r value
        if [ -z "$value" ]; then
            echo -e "    ${YELLOW}⚠${NC} Skipped (empty input)"
        else
            set_secret "$key" "$value"
            echo -e "    ${GREEN}✓${NC} Stored"
        fi
    fi
done

echo ""
echo -e "${GREEN}Done.${NC} Verify with: ./scripts/keychain-setup.sh --verify"
echo -e "Launch with:  ./scripts/launch-with-keychain.sh"
echo ""
echo -e "${YELLOW}Security notes:${NC}"
echo "  • Secrets never touch disk as plaintext"
echo "  • Keychain is encrypted at rest by macOS"
echo "  • Delete all: security delete-keychain $KEYCHAIN"
echo "  • Rotate all: ./scripts/keychain-setup.sh --rotate"
