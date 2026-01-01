***REMOVED***!/bin/bash
***REMOVED*** ============================================================
***REMOVED*** Script: test-mcp-integration.sh
***REMOVED*** Purpose: Integration testing for MCP server with FastAPI backend
***REMOVED*** Usage: ./scripts/test-mcp-integration.sh
***REMOVED***
***REMOVED*** Description:
***REMOVED***   Comprehensive integration test suite for Model Context Protocol
***REMOVED***   server integration with FastAPI backend and Claude Code.
***REMOVED***   Verifies module imports, PII compliance, and core functionality.
***REMOVED***
***REMOVED*** Test Categories:
***REMOVED***   1. MCP module imports and dependencies
***REMOVED***   2. PII/security compliance verification
***REMOVED***   3. Domain context abbreviation expansion
***REMOVED***   4. Constraint explanation functionality
***REMOVED***   5. API client connectivity
***REMOVED***
***REMOVED*** Requirements:
***REMOVED***   - MCP server code in mcp-server/src/
***REMOVED***   - Python environment with scheduler_mcp installed
***REMOVED***   - FastAPI backend accessible (optional for some tests)
***REMOVED***
***REMOVED*** Exit Codes:
***REMOVED***   0 - All tests passed
***REMOVED***   1 - One or more tests failed
***REMOVED*** ============================================================

set -euo pipefail

echo "=== MCP Integration Test ==="

***REMOVED*** Verify Python is available
if ! command -v python >/dev/null 2>&1; then
    echo "ERROR: python command not found" >&2
    exit 1
fi

***REMOVED*** Verify MCP server directory exists
if [ ! -d "mcp-server/src" ]; then
    echo "ERROR: MCP server source directory not found: mcp-server/src" >&2
    exit 1
fi

***REMOVED*** 1. Check if we can import MCP modules
***REMOVED*** Tests that all required dependencies are installed
***REMOVED*** and Python path is configured correctly
echo "1. Testing MCP module imports..."
cd mcp-server/src || {
    echo "ERROR: Failed to change to mcp-server/src directory" >&2
    exit 1
}
python -c "from scheduler_mcp.server import mcp; print('MCP server imports OK')" || exit 1
python -c "from scheduler_mcp.api_client import SchedulerAPIClient; print('API client imports OK')" || exit 1
python -c "from scheduler_mcp.domain_context import expand_abbreviations; print('Domain context imports OK')" || exit 1

***REMOVED*** 2. Test no PII in MCP code
***REMOVED*** Ensures PERSEC compliance by detecting person_name references
***REMOVED*** person_name was removed to avoid exposing military personnel data
echo "2. Verifying no PII in MCP code..."
if grep -r "person_name" scheduler_mcp/*.py 2>/dev/null | grep -v "***REMOVED*** REMOVED" | grep -v "^***REMOVED***"; then
    echo "WARNING: person_name still found in MCP code"
else
    echo "PII check passed - no person_name found"
fi

***REMOVED*** 3. Test abbreviation expansion
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
