#!/bin/bash
# ============================================================
# Script: start-mcp.sh
# Purpose: Start MCP (Model Context Protocol) server
# Usage: ./scripts/start-mcp.sh
#
# Description:
#   Starts the MCP server for AI assistant integration.
#   Ensures FastAPI backend is running before starting MCP.
#   Provides 29+ specialized scheduling tools for Claude Code.
#
# Prerequisites:
#   - FastAPI backend running on port 8000
#   - Redis available
#   - Python environment with scheduler_mcp installed
#
# Environment Variables:
#   API_BASE_URL     - Backend API URL (default: http://localhost:8000)
#   LOG_LEVEL        - Logging level (default: INFO)
#   PYTHONPATH       - Python module path
# ============================================================

set -e

# Ensure we're in project root
cd "$(dirname "$0")/.."

# Check if FastAPI backend is running
echo "Checking FastAPI backend..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "FastAPI backend not running. Starting with Docker Compose..."
    docker-compose up -d backend
    echo "Waiting for backend to be healthy..."
    sleep 5
fi

# Verify backend is healthy
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "ERROR: FastAPI backend failed to start"
    exit 1
fi

echo "FastAPI backend is healthy"

# Set environment
export API_BASE_URL="http://localhost:8000"
export PYTHONPATH="${PWD}/mcp-server/src"
export LOG_LEVEL="INFO"

# Start MCP server
echo "Starting MCP server..."
cd mcp-server/src
python -m scheduler_mcp.server
