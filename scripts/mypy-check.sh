#!/usr/bin/env bash
# Backend type checking with mypy
#
# Usage:
#   ./scripts/mypy-check.sh              # Full backend check
#   ./scripts/mypy-check.sh app/services # Specific directory
#   ./scripts/mypy-check.sh --strict     # Strict mode
#
# Removed from pre-commit because:
# - Full scan needed for accurate type inference
# - ~50 pre-existing errors would block all commits
# - Was running with || true (never blocked anyway)
#
# CI runs this on PRs. Use locally before major changes.

set -euo pipefail

cd "$(dirname "$0")/../backend"

TARGET="${1:-app/}"
shift 2>/dev/null || true

echo "Running mypy on backend/$TARGET..."
echo "=================================="

mypy "$TARGET" --config-file pyproject.toml "$@"

echo ""
echo "Type check complete."
