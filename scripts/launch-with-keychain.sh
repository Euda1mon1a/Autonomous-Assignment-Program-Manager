#!/bin/bash
# ============================================================
# Script: launch-with-keychain.sh
# Purpose: Start AAPM production stack with secrets from Keychain
# Usage: ./scripts/launch-with-keychain.sh [--build] [--logs]
#
# Description:
#   Pulls secrets from macOS Keychain, exports them as env vars,
#   and starts the Docker Compose production stack. Secrets exist
#   only in process memory — never written to disk.
#
#   Replaces the .env file pattern for production deployments.
#   For local development, continue using docker-compose.local.yml
#   which has hardcoded dev passwords.
#
# Prerequisites:
#   1. Run keychain-setup.sh first to seed secrets
#   2. Keychain must be unlocked (macOS handles this on login)
#
# Options:
#   --build    Rebuild containers before starting
#   --logs     Follow logs after starting
#   --dry-run  Show what would be exported without starting
# ============================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

KEYCHAIN="ai-secrets.keychain"
SERVICE_ACCOUNT="aapm"

# --- Parse args ---

BUILD=""
LOGS=""
DRY_RUN=""
for arg in "$@"; do
    case $arg in
        --build) BUILD="--build" ;;
        --logs) LOGS="true" ;;
        --dry-run) DRY_RUN="true" ;;
    esac
done

# --- Helpers ---

get_secret() {
    security find-generic-password -a "$SERVICE_ACCOUNT" -s "$1" -w "$KEYCHAIN" 2>/dev/null || \
        security find-generic-password -a "$SERVICE_ACCOUNT" -s "$1" -w 2>/dev/null || \
        echo ""
}

# --- Ensure project root ---

cd "$(dirname "$0")/.." || {
    echo -e "${RED}ERROR: Failed to change to project root${NC}" >&2
    exit 1
}

echo -e "${CYAN}AAPM Production Launch (Keychain)${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# --- Pull secrets from Keychain ---

echo -e "\n${YELLOW}Loading secrets from Keychain...${NC}"

SECRETS_MAP=(
    "aapm-db-password:DB_PASSWORD"
    "aapm-redis-password:REDIS_PASSWORD"
    "aapm-secret-key:SECRET_KEY"
    "aapm-webhook-secret:WEBHOOK_SECRET"
    "aapm-api-username:API_USERNAME"
    "aapm-api-password:API_PASSWORD"
)

MISSING=()
for mapping in "${SECRETS_MAP[@]}"; do
    keychain_key="${mapping%%:*}"
    env_var="${mapping##*:}"
    value=$(get_secret "$keychain_key")

    if [ -z "$value" ]; then
        MISSING+=("$keychain_key → $env_var")
        echo -e "  ${RED}✗${NC} $env_var (missing: $keychain_key)"
    else
        export "$env_var=$value"
        echo -e "  ${GREEN}✓${NC} $env_var ← $keychain_key"
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo -e "\n${RED}Missing ${#MISSING[@]} secret(s). Run keychain-setup.sh first.${NC}"
    exit 1
fi

# --- Non-secret config (safe defaults) ---

export DEBUG="${DEBUG:-false}"
export CORS_ORIGINS="${CORS_ORIGINS:-[\"http://localhost:3000\"]}"
export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000}"
export MCP_LOG_LEVEL="${MCP_LOG_LEVEL:-INFO}"
export TELEMETRY_ENABLED="${TELEMETRY_ENABLED:-false}"

echo -e "\n${GREEN}All secrets loaded.${NC}"

# --- Dry run ---

if [ -n "$DRY_RUN" ]; then
    echo -e "\n${CYAN}Dry run — env vars that would be set:${NC}"
    for mapping in "${SECRETS_MAP[@]}"; do
        env_var="${mapping##*:}"
        val="${!env_var}"
        echo "  $env_var=${val:0:8}..."
    done
    echo ""
    echo "  DEBUG=$DEBUG"
    echo "  CORS_ORIGINS=$CORS_ORIGINS"
    echo "  TELEMETRY_ENABLED=$TELEMETRY_ENABLED"
    echo -e "\n${YELLOW}No containers started (dry run).${NC}"
    exit 0
fi

# --- Launch Docker ---

echo -e "\n${YELLOW}Starting production stack...${NC}"

if [ -n "$BUILD" ]; then
    echo -e "${YELLOW}Rebuilding containers...${NC}"
    docker compose up -d --build
else
    docker compose up -d
fi

# Wait for health checks
echo -e "${YELLOW}Waiting for services...${NC}"
sleep 10

# Status
echo ""
echo -e "${GREEN}Service Status:${NC}"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# Verify critical services
echo ""
BACKEND_HEALTH=$(docker inspect residency-scheduler-backend --format '{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
if [ "$BACKEND_HEALTH" = "healthy" ]; then
    echo -e "${GREEN}✓ Backend healthy${NC}"
else
    echo -e "${YELLOW}⚠ Backend status: $BACKEND_HEALTH (may still be starting)${NC}"
fi

echo ""
echo -e "${GREEN}Access Points:${NC}"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  MCP:       http://localhost:8080 (localhost only)"
echo ""
echo -e "${CYAN}Secrets loaded from Keychain — no .env file needed.${NC}"

if [ -n "$LOGS" ]; then
    echo ""
    echo -e "${YELLOW}Following logs (Ctrl+C to exit)...${NC}"
    docker compose logs -f
fi
