#!/bin/bash
# =============================================================================
# MCP Configuration Validator
# =============================================================================
# This script validates MCP configuration to prevent the recurring transport
# and authentication issues that have plagued this project.
#
# Run this:
#   - Before commits (via pre-commit hook)
#   - In CI/CD pipeline
#   - After any MCP-related changes
#
# Created: 2026-01-03 (Session 051)
# Reference: .claude/Scratchpad/MCP_TRANSPORT_FIX_20260102.md
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

error() {
    echo -e "${RED}ERROR: $1${NC}"
    ((ERRORS++))
}

warn() {
    echo -e "${YELLOW}WARNING: $1${NC}"
    ((WARNINGS++))
}

ok() {
    echo -e "${GREEN}OK: $1${NC}"
}

echo "=========================================="
echo "MCP Configuration Validator"
echo "=========================================="
echo ""

# -----------------------------------------------------------------------------
# 1. Validate .mcp.json client config
# -----------------------------------------------------------------------------
echo "--- Checking .mcp.json ---"

if [ ! -f ".mcp.json" ]; then
    error ".mcp.json not found"
else
    # Check type field
    TYPE=$(jq -r '.mcpServers["residency-scheduler"].type // "missing"' .mcp.json 2>/dev/null)
    if [ "$TYPE" = "http" ]; then
        ok "type = 'http' (correct for FastMCP 2.x stateless mode)"
    elif [ "$TYPE" = "sse" ]; then
        warn "type = 'sse' (deprecated, use 'http' instead)"
    elif [ "$TYPE" = "missing" ]; then
        error "type field is missing"
    else
        error "type = '$TYPE' (invalid, must be 'http')"
    fi

    # Check URL
    URL=$(jq -r '.mcpServers["residency-scheduler"].url // "missing"' .mcp.json 2>/dev/null)
    if [[ "$URL" == *"/mcp"* ]]; then
        ok "url = '$URL' (correct /mcp endpoint)"
    elif [[ "$URL" == *"/sse"* ]]; then
        error "url = '$URL' (wrong endpoint, should be /mcp not /sse)"
    else
        warn "url = '$URL' (should contain /mcp)"
    fi

    # Check for deprecated/invalid fields
    TRANSPORT=$(jq -r '.mcpServers["residency-scheduler"].transport // "not_present"' .mcp.json 2>/dev/null)
    if [ "$TRANSPORT" != "not_present" ]; then
        error "Found 'transport' field (invalid schema, use 'type' instead)"
    fi
fi

echo ""

# -----------------------------------------------------------------------------
# 2. Validate pyproject.toml FastMCP version
# -----------------------------------------------------------------------------
echo "--- Checking mcp-server/pyproject.toml ---"

if [ ! -f "mcp-server/pyproject.toml" ]; then
    error "mcp-server/pyproject.toml not found"
else
    # Check FastMCP version - MUST be pinned to exact version
    FASTMCP_LINE=$(grep -E "fastmcp" mcp-server/pyproject.toml 2>/dev/null || echo "")
    if [ -z "$FASTMCP_LINE" ]; then
        error "fastmcp dependency not found"
    elif [[ "$FASTMCP_LINE" == *"==2.14.2"* ]]; then
        ok "FastMCP pinned to 2.14.2 (known working version)"
    elif [[ "$FASTMCP_LINE" == *"=="* ]]; then
        warn "FastMCP pinned to different version: $FASTMCP_LINE (recommended: 2.14.2)"
    elif [[ "$FASTMCP_LINE" == *">="* ]]; then
        error "FastMCP NOT pinned (uses >=). Pin to ==2.14.2 to prevent breakage"
    elif [[ "$FASTMCP_LINE" == *"<2.0"* ]]; then
        error "FastMCP pinned to 1.x (need 2.14.2 for http_app() + stateless_http)"
    else
        warn "FastMCP version may be incorrect: $FASTMCP_LINE"
    fi
fi

echo ""

# -----------------------------------------------------------------------------
# 3. Validate server.py stateless_http setting
# -----------------------------------------------------------------------------
echo "--- Checking mcp-server/src/scheduler_mcp/server.py ---"

if [ ! -f "mcp-server/src/scheduler_mcp/server.py" ]; then
    error "server.py not found"
else
    # Check for stateless_http=True
    if grep -q "stateless_http=True" mcp-server/src/scheduler_mcp/server.py; then
        ok "stateless_http=True is set (disables session requirement)"
    elif grep -q "stateless_http" mcp-server/src/scheduler_mcp/server.py; then
        error "stateless_http found but not set to True"
    else
        error "stateless_http=True not found (required for Claude Code compatibility)"
    fi

    # Check for lifespan
    if grep -q "lifespan=mcp_app.lifespan" mcp-server/src/scheduler_mcp/server.py; then
        ok "lifespan is properly configured"
    else
        warn "lifespan configuration may be missing"
    fi
fi

echo ""

# -----------------------------------------------------------------------------
# 4. Validate docker-compose.yml MCP settings
# -----------------------------------------------------------------------------
echo "--- Checking docker-compose.yml ---"

if [ ! -f "docker-compose.yml" ]; then
    error "docker-compose.yml not found"
else
    # Check MCP_TRANSPORT
    if grep -q "MCP_TRANSPORT: http" docker-compose.yml; then
        ok "MCP_TRANSPORT: http (correct)"
    elif grep -q "MCP_TRANSPORT: sse" docker-compose.yml; then
        warn "MCP_TRANSPORT: sse (should be http for FastMCP 2.x)"
    else
        warn "MCP_TRANSPORT not found"
    fi

    # Check API credentials reference
    if grep -q 'API_USERNAME:' docker-compose.yml && grep -q 'API_PASSWORD:' docker-compose.yml; then
        ok "API_USERNAME and API_PASSWORD references found"
    else
        error "API_USERNAME/API_PASSWORD not configured for MCP service"
    fi
fi

echo ""

# -----------------------------------------------------------------------------
# 5. Validate .env.example has MCP auth vars documented
# -----------------------------------------------------------------------------
echo "--- Checking .env.example ---"

if [ ! -f ".env.example" ]; then
    warn ".env.example not found"
else
    if grep -q "API_USERNAME" .env.example && grep -q "API_PASSWORD" .env.example; then
        ok "API_USERNAME and API_PASSWORD documented in .env.example"
    else
        error "API_USERNAME/API_PASSWORD not documented in .env.example"
    fi
fi

echo ""

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo "=========================================="
echo "Validation Summary"
echo "=========================================="

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}FAILED: $ERRORS error(s), $WARNINGS warning(s)${NC}"
    echo ""
    echo "See .claude/Scratchpad/MCP_TRANSPORT_FIX_20260102.md for fix details"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}PASSED with $WARNINGS warning(s)${NC}"
    exit 0
else
    echo -e "${GREEN}PASSED: All checks OK${NC}"
    exit 0
fi
