***REMOVED***!/bin/bash
***REMOVED*** ============================================================
***REMOVED*** Script: start-mcp.sh
***REMOVED*** Purpose: Start MCP (Model Context Protocol) server
***REMOVED*** Usage: ./scripts/start-mcp.sh
***REMOVED***
***REMOVED*** Description:
***REMOVED***   Starts the MCP server for AI assistant integration.
***REMOVED***   Ensures FastAPI backend is running before starting MCP.
***REMOVED***   Provides 29+ specialized scheduling tools for Claude Code.
***REMOVED***
***REMOVED*** Prerequisites:
***REMOVED***   - FastAPI backend running on port 8000
***REMOVED***   - Redis available
***REMOVED***   - Python environment with scheduler_mcp installed
***REMOVED***
***REMOVED*** Environment Variables:
***REMOVED***   API_BASE_URL     - Backend API URL (default: http://localhost:8000)
***REMOVED***   LOG_LEVEL        - Logging level (default: INFO)
***REMOVED***   PYTHONPATH       - Python module path
***REMOVED*** ============================================================

set -euo pipefail

***REMOVED*** Ensure we're in project root
***REMOVED*** This allows the script to be called from anywhere
cd "$(dirname "$0")/.." || {
    echo "ERROR: Failed to change to project root" >&2
    exit 1
}

***REMOVED*** Check if curl is available for health checks
if ! command -v curl >/dev/null 2>&1; then
    echo "ERROR: curl command not found (required for health checks)" >&2
    exit 1
fi

***REMOVED*** Check if FastAPI backend is running
***REMOVED*** MCP server requires backend to be accessible for API integration
echo "Checking FastAPI backend..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "FastAPI backend not running. Starting with Docker Compose..."

    ***REMOVED*** Verify docker-compose is available
    if ! command -v docker-compose >/dev/null 2>&1; then
        echo "ERROR: docker-compose command not found" >&2
        exit 1
    fi

    ***REMOVED*** Start only backend service to minimize resource usage
    if ! docker-compose up -d backend; then
        echo "ERROR: Failed to start backend with docker-compose" >&2
        exit 1
    fi

    echo "Waiting for backend to be healthy..."
    ***REMOVED*** Allow time for database connection and migrations
    sleep 5
fi

***REMOVED*** Verify backend is healthy after startup
***REMOVED*** Fail fast if backend cannot be started
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "ERROR: FastAPI backend failed to start or is unhealthy" >&2
    exit 1
fi

echo "FastAPI backend is healthy"

***REMOVED*** Set environment variables for MCP server
***REMOVED*** API_BASE_URL: Backend API endpoint for scheduling operations
***REMOVED*** PYTHONPATH: Ensures scheduler_mcp module can be imported
***REMOVED*** LOG_LEVEL: Controls verbosity of MCP server logs
export API_BASE_URL="http://localhost:8000"
export PYTHONPATH="${PWD}/mcp-server/src"
export LOG_LEVEL="INFO"

***REMOVED*** Start MCP server
echo "Starting MCP server..."
cd mcp-server/src
python -m scheduler_mcp.server
