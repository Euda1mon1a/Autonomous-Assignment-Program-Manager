***REMOVED***!/bin/bash
***REMOVED*** Start MCP server with required dependencies

set -e

***REMOVED*** Ensure we're in project root
cd "$(dirname "$0")/.."

***REMOVED*** Check if FastAPI backend is running
echo "Checking FastAPI backend..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "FastAPI backend not running. Starting with Docker Compose..."
    docker-compose up -d backend
    echo "Waiting for backend to be healthy..."
    sleep 5
fi

***REMOVED*** Verify backend is healthy
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "ERROR: FastAPI backend failed to start"
    exit 1
fi

echo "FastAPI backend is healthy"

***REMOVED*** Set environment
export API_BASE_URL="http://localhost:8000"
export PYTHONPATH="${PWD}/mcp-server/src"
export LOG_LEVEL="INFO"

***REMOVED*** Start MCP server
echo "Starting MCP server..."
cd mcp-server/src
python -m scheduler_mcp.server
