#!/usr/bin/env bash
#
# validate-migration-names.sh - Validate Alembic migration revision ID lengths
#
# This script prevents the recurring alembic_version varchar(32) overflow issue
# by validating that all migration revision IDs are within safe limits.
#
# The alembic_version table has been extended to varchar(128), but we enforce
# a 64-char limit to leave headroom and encourage concise naming.
#
# Usage:
#   ./scripts/validate-migration-names.sh           # Check all migrations
#   ./scripts/validate-migration-names.sh --staged  # Check only staged files
#
# Exit codes:
#   0 - All migrations valid
#   1 - One or more migrations exceed length limit
#

set -euo pipefail

# Configuration
MAX_REVISION_LENGTH=64  # Conservative limit (column is varchar(128))
MIGRATIONS_DIR="backend/alembic/versions"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
CHECK_STAGED_ONLY=false
if [[ "${1:-}" == "--staged" ]]; then
    CHECK_STAGED_ONLY=true
fi

# Change to project root
cd "$PROJECT_ROOT"

# Get list of migration files to check
if $CHECK_STAGED_ONLY; then
    # Only check staged migration files
    FILES=$(git diff --cached --name-only --diff-filter=ACM | grep "^${MIGRATIONS_DIR}/.*\.py$" || true)
else
    # Check all migration files
    FILES=$(find "$MIGRATIONS_DIR" -name "*.py" -type f 2>/dev/null || true)
fi

if [[ -z "$FILES" ]]; then
    echo -e "${GREEN}No migration files to check.${NC}"
    exit 0
fi

# Track violations
VIOLATIONS=0
CHECKED=0

echo "Checking migration revision ID lengths (max: $MAX_REVISION_LENGTH chars)..."
echo ""

while IFS= read -r file; do
    if [[ -z "$file" ]]; then
        continue
    fi

    # Extract revision ID from file
    # Handles both: revision: str = 'xxx' and revision = 'xxx'
    REVISION=$(grep -E "^revision[: str]*= ['\"]" "$file" 2>/dev/null | head -1 | sed -E "s/.*['\"]([^'\"]+)['\"].*/\1/" || true)

    if [[ -z "$REVISION" ]]; then
        echo -e "${YELLOW}WARN:${NC} Could not extract revision from: $file"
        continue
    fi

    CHECKED=$((CHECKED + 1))
    LENGTH=${#REVISION}

    if [[ $LENGTH -gt $MAX_REVISION_LENGTH ]]; then
        echo -e "${RED}FAIL:${NC} $file"
        echo "       Revision: '$REVISION'"
        echo "       Length: $LENGTH chars (max: $MAX_REVISION_LENGTH)"
        echo ""
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done <<< "$FILES"

echo ""
echo "Checked $CHECKED migration files."

if [[ $VIOLATIONS -gt 0 ]]; then
    echo -e "${RED}FAILED:${NC} $VIOLATIONS migration(s) exceed the $MAX_REVISION_LENGTH char limit."
    echo ""
    echo "To fix:"
    echo "  1. Use shorter, more concise revision IDs"
    echo "  2. Format: YYYYMMDD_short_desc (e.g., 20260105_res_weekly)"
    echo "  3. Keep descriptions under 50 chars total"
    echo ""
    echo "See: CLAUDE.md section 'Migration Naming Convention'"
    exit 1
else
    echo -e "${GREEN}PASSED:${NC} All migrations have valid revision ID lengths."
    exit 0
fi
