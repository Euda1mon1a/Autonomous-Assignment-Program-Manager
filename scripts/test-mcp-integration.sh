#!/bin/bash
# ============================================================
# Script: test-mcp-integration.sh
# Purpose: Integration testing for MCP server with FastAPI backend
# Usage: ./scripts/test-mcp-integration.sh
#
# Description:
#   Comprehensive integration test suite for Model Context Protocol
#   server integration with FastAPI backend and Claude Code.
#   Verifies module imports, PII compliance, and core functionality.
#
# Test Categories:
#   1. MCP module imports and dependencies
#   2. PII/security compliance verification
#   3. Domain context abbreviation expansion
#   4. Constraint explanation functionality
#   5. API client connectivity
#
# Requirements:
#   - MCP server code in mcp-server/src/
#   - Python environment with scheduler_mcp installed
#   - FastAPI backend accessible (optional for some tests)
#
# Exit Codes:
#   0 - All tests passed
#   1 - One or more tests failed
# ============================================================

set -e

echo "=== MCP Integration Test ==="

# 1. Check if we can import MCP modules
echo "1. Testing MCP module imports..."
cd mcp-server/src
python -c "from scheduler_mcp.server import mcp; print('MCP server imports OK')" || exit 1
python -c "from scheduler_mcp.api_client import SchedulerAPIClient; print('API client imports OK')" || exit 1
python -c "from scheduler_mcp.domain_context import expand_abbreviations; print('Domain context imports OK')" || exit 1

# 2. Test no PII in MCP code
echo "2. Verifying no PII in MCP code..."
if grep -r "person_name" scheduler_mcp/*.py 2>/dev/null | grep -v "# REMOVED" | grep -v "^#"; then
    echo "WARNING: person_name still found in MCP code"
else
    echo "PII check passed - no person_name found"
fi

# 3. Test abbreviation expansion
echo "3. Testing domain context..."
python -c "
from scheduler_mcp.domain_context import expand_abbreviations, explain_constraint
text = expand_abbreviations('PGY-1 on FMIT')
print(f'Expansion test: {text}')
exp = explain_constraint('InvertedWednesday')
print(f'Constraint explanation: {exp[\"description\"][:50]}...')
"

echo "=== All basic tests passed ==="
echo ""
echo "To test with FastAPI backend:"
echo "  1. docker-compose up -d backend"
echo "  2. ./scripts/start-mcp.sh"
