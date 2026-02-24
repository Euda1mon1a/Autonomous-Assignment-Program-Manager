#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MCP_PYTHON="${ROOT_DIR}/mcp-server/.venv/bin/python"

if [[ ! -x "${MCP_PYTHON}" ]]; then
  echo "MCP virtual environment not found. Run: make setup-mac" >&2
  exit 1
fi

if ! curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then
  echo "Backend is not healthy on http://127.0.0.1:8000/health." >&2
  echo "Start stack with: make local-up" >&2
  exit 1
fi

cd "${ROOT_DIR}/mcp-server"
PYTHONPATH="${ROOT_DIR}/mcp-server/src:${ROOT_DIR}/backend" \
API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}" \
API_USERNAME="${API_USERNAME:-admin}" \
API_PASSWORD="${API_PASSWORD:?API_PASSWORD must be set for MCP server}" \
exec "${MCP_PYTHON}" -m scheduler_mcp.server --transport http --host 127.0.0.1 --port 8080
