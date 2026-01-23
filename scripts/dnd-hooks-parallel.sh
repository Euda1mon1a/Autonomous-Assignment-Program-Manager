#!/bin/bash
# ============================================================
# Script: dnd-hooks-parallel.sh
# Purpose: Run D&D-themed pre-commit hooks in parallel
# Domain: COORD_TOOLING
#
# Combines:
#   - Couatl Killer (snake_case query params)
#   - Beholder Bane (SQLAlchemy anti-magic)
#   - Gorgon's Gaze (snake_case enum values)
#
# These checks are independent and can run simultaneously.
# ============================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FAILED=0

echo "Running D&D hooks in parallel..."

# Run all hooks in parallel
"$SCRIPT_DIR/couatl-killer.sh" &
PID_COUATL=$!

"$SCRIPT_DIR/beholder-bane.sh" &
PID_BEHOLDER=$!

"$SCRIPT_DIR/gorgons-gaze.sh" &
PID_GORGON=$!

# Wait for all and collect exit codes
wait $PID_COUATL
EXIT_COUATL=$?

wait $PID_BEHOLDER
EXIT_BEHOLDER=$?

wait $PID_GORGON
EXIT_GORGON=$?

# Report results
if [ $EXIT_COUATL -ne 0 ]; then
    echo "Couatl Killer: FAILED"
    FAILED=1
fi

if [ $EXIT_BEHOLDER -ne 0 ]; then
    echo "Beholder Bane: FAILED"
    FAILED=1
fi

if [ $EXIT_GORGON -ne 0 ]; then
    echo "Gorgon's Gaze: FAILED"
    FAILED=1
fi

if [ $FAILED -eq 0 ]; then
    echo "D&D hooks: PASSED"
fi

exit $FAILED
