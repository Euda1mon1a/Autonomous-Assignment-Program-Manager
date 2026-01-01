#!/bin/bash
# CCW Validation Gate - Run after every ~20 CCW tasks
# Usage: ./.claude/scripts/ccw-validation-gate.sh

set -e

echo "╔════════════════════════════════════════╗"
echo "║     CCW VALIDATION GATE                ║"
echo "╚════════════════════════════════════════╝"
echo ""

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT/frontend"

# Gate 1: Type Check
echo "▶ Running type-check..."
if npm run type-check 2>&1; then
    echo "✅ Type-check PASSED"
else
    echo ""
    echo "❌ TYPE-CHECK FAILED"
    echo ""
    echo "Action: STOP burn, diagnose root cause, fix before continuing"
    exit 1
fi

echo ""

# Gate 2: Build
echo "▶ Running build..."
if npm run build > /dev/null 2>&1; then
    echo "✅ Build PASSED"
else
    echo ""
    echo "❌ BUILD FAILED"
    echo ""
    npm run build 2>&1 | tail -20
    exit 1
fi

echo ""

# Gate 3: Token Corruption Check
echo "▶ Checking for token corruption..."
CORRUPTED=$(grep -rE "[a-z]await [a-z]" "$REPO_ROOT/backend" --include="*.py" 2>/dev/null | grep -v venv || true)
if [ -n "$CORRUPTED" ]; then
    echo ""
    echo "❌ TOKEN CORRUPTION DETECTED"
    echo ""
    echo "$CORRUPTED"
    echo ""
    echo "Pattern: 'await sawait ervice' should be 'await service'"
    exit 1
fi
echo "✅ No token corruption"

echo ""
echo "════════════════════════════════════════"
echo "✅ ALL GATES PASSED - Safe to continue burn"
echo "════════════════════════════════════════"
