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

set -euo pipefail

# Ensure we're in project root
# This allows the script to be called from anywhere
cd "$(dirname "$0")/.." || {
    echo "ERROR: Failed to change to project root" >&2
    exit 1
}

# Check if curl is available for health checks
if ! command -v curl >/dev/null 2>&1; then
    echo "ERROR: curl command not found (required for health checks)" >&2
    exit 1
fi

# Check if FastAPI backend is running
# MCP server requires backend to be accessible for API integration
echo "Checking FastAPI backend..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "FastAPI backend not running. Starting with Docker Compose..."

    # Verify docker-compose is available
    if ! command -v docker-compose >/dev/null 2>&1; then
        echo "ERROR: docker-compose command not found" >&2
        exit 1
    fi

    # Start only backend service to minimize resource usage
    if ! docker-compose up -d backend; then
        echo "ERROR: Failed to start backend with docker-compose" >&2
        exit 1
    fi

    echo "Waiting for backend to be healthy..."
    # Allow time for database connection and migrations
    sleep 5
fi

# Verify backend is healthy after startup
# Fail fast if backend cannot be started
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "ERROR: FastAPI backend failed to start or is unhealthy" >&2
    exit 1
fi

echo "FastAPI backend is healthy"

# Set environment variables for MCP server
# API_BASE_URL: Backend API endpoint for scheduling operations
# PYTHONPATH: Ensures scheduler_mcp module can be imported
# LOG_LEVEL: Controls verbosity of MCP server logs
export API_BASE_URL="http://localhost:8000"
export PYTHONPATH="${PWD}/mcp-server/src"
export LOG_LEVEL="INFO"

# Start MCP server
echo "Starting MCP server..."
cd mcp-server/src
python -m scheduler_mcp.server
