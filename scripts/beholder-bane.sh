#!/bin/bash
# beholder-bane.sh - SQLAlchemy Filter Anti-Magic Detector
#
#   "The beholder's central eye emits a cone of anti-magic..."
#                                    - D&D Monster Manual
#
# Named after the D&D Beholder's anti-magic cone that nullifies magic.
# Similarly, `not Column` in SQLAlchemy filters nullifies your query,
# returning nothing instead of filtered results.
#
# The Beholder's Eye:     `not Column`
# The Anti-Magic Effect:  Evaluates to `False`, killing the filter
# The Victim:             Your query results (0 rows returned)
#
# This script hunts down these anti-magic patterns before they
# reach production and silently break your queries.
#
# Usage:
#   ./scripts/beholder-bane.sh [path]
#   ./scripts/beholder-bane.sh backend/app/
#
# Exit codes:
#   0 - Beholder slain (no issues found)
#   1 - Beholder detected (issues found, prints file:line)

set -e

SEARCH_PATH="${1:-backend}"
ISSUES_FOUND=0

echo "🔮 Beholder Bane scanning: $SEARCH_PATH"
echo ""

# Pattern 1: `not Model.column` inside .filter()
# This is the most dangerous pattern - `not Column` evaluates to False
PATTERN1='\.filter\([^)]*\bnot [A-Z][a-z_]+\.'

# Pattern 2: Standalone `not column_name` that looks like a model attribute
# Catches: `not block.is_weekend` inside filter chains
PATTERN2='filter.*\bnot [a-z_]+\.is_|filter.*\bnot [a-z_]+\.has_'

echo "=== Scanning for anti-magic eye rays (not Model.column) ==="
if grep -rn --include="*.py" -E "$PATTERN1" "$SEARCH_PATH" 2>/dev/null; then
    ISSUES_FOUND=1
else
    echo "  Clear."
fi

echo ""
echo "=== Scanning for petrification gaze (not instance.is_*) ==="
# More targeted search for the common pattern
if grep -rn --include="*.py" -E '\.filter\([^)]*not [a-z_]+\.(is_|has_|can_)' "$SEARCH_PATH" 2>/dev/null; then
    ISSUES_FOUND=1
else
    echo "  Clear."
fi

echo ""
if [ $ISSUES_FOUND -eq 1 ]; then
    echo "👁️  BEHOLDER DETECTED!"
    echo ""
    echo "The anti-magic cone nullifies your filter. Slay it with:"
    echo "  - Column == False      (silver sword)"
    echo "  - Column.is_(False)    (magic missile)"
    echo "  - ~Column              (fireball)"
    echo ""
    echo "Example:"
    echo "  CURSED:  .filter(not Block.is_weekend)"
    echo "  BLESSED: .filter(Block.is_weekend == False)"
    exit 1
else
    echo "⚔️  Beholder slain. No anti-magic detected."
    exit 0
fi
