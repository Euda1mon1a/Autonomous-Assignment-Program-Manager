#!/usr/bin/env bash
# Full backend security scan with bandit
#
# Usage:
#   ./scripts/bandit-full.sh         # Default: medium+ severity
#   ./scripts/bandit-full.sh -ll     # Low+ severity (verbose)
#   ./scripts/bandit-full.sh -lll    # High only (strict)
#   ./scripts/bandit-full.sh -f html -o report.html  # HTML report
#
# This runs a comprehensive scan of all backend code.
# Pre-commit hook only scans staged files for faster commits.

set -euo pipefail

cd "$(dirname "$0")/../backend"

echo "Running full bandit security scan on backend/app/..."
echo "=================================================="

# Default to -ll (low severity, low confidence) if no args
if [ $# -eq 0 ]; then
    bandit -r app -ll
else
    bandit -r app "$@"
fi

echo ""
echo "Scan complete."
