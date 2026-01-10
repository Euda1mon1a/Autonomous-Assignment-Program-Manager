#!/bin/bash
# ============================================================
# Script: validate-bundle-size.sh
# Purpose: Pre-commit hook for bundle size monitoring
# Domain: FRONTEND Advisory
# Session: 084
#
# Problem: Bundle size regressions are caught late in CI.
#          This hook provides early warning when dependencies change.
#
# Checks:
#   1. New dependencies added to package.json
#   2. Large package detection (known heavy deps)
#   3. Build reminder when deps change
#   4. Optional full build with BUNDLE_FULL=1
#
# Philosophy (Auftragstaktik):
#   Fast by default, thorough on demand. Monitor inputs (deps)
#   rather than outputs (bundle) for commit-time speed.
#
# Exit Codes:
#   0 - Validation passed (warnings allowed)
#   1 - Validation failed (only with BUNDLE_FULL=1)
# ============================================================

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

WARNINGS=0
ERRORS=0

FRONTEND_DIR="frontend"
PACKAGE_JSON="$FRONTEND_DIR/package.json"

echo -e "${CYAN}Running Bundle Size Monitor...${NC}"

# ============================================================
# Check 0: Is package.json staged?
# ============================================================
PACKAGE_STAGED=$(git diff --cached --name-only 2>/dev/null | grep -E "^frontend/package\.json$" || true)

if [ -z "$PACKAGE_STAGED" ]; then
    echo -e "${GREEN}No frontend dependency changes staged.${NC}"
    exit 0
fi

echo -e "${BLUE}Dependency changes detected in package.json${NC}"
echo ""

# ============================================================
# Check 1: New Dependencies Added
# ============================================================
echo -n "Checking for new dependencies... "

# Get dependencies from staged version
STAGED_DEPS=$(git show :frontend/package.json 2>/dev/null | \
    grep -E '"[^"]+"\s*:\s*"[\^~]?[0-9]' | \
    sed 's/.*"\([^"]*\)"\s*:.*/\1/' | sort -u || true)

# Get dependencies from HEAD version
HEAD_DEPS=$(git show HEAD:frontend/package.json 2>/dev/null | \
    grep -E '"[^"]+"\s*:\s*"[\^~]?[0-9]' | \
    sed 's/.*"\([^"]*\)"\s*:.*/\1/' | sort -u || true)

# Find new dependencies (in staged but not in HEAD)
NEW_DEPS=""
for dep in $STAGED_DEPS; do
    if ! echo "$HEAD_DEPS" | grep -q "^${dep}$" 2>/dev/null; then
        NEW_DEPS="$NEW_DEPS $dep"
    fi
done

NEW_COUNT=$(echo "$NEW_DEPS" | wc -w)
if [ "$NEW_COUNT" -gt 0 ]; then
    echo -e "${BLUE}INFO${NC}"
    echo -e "${BLUE}New dependencies added:${NC}"
    for dep in $NEW_DEPS; do
        echo "  + $dep"
    done
else
    echo -e "${GREEN}OK${NC} (no new deps)"
fi

# ============================================================
# Check 2: Large Package Detection
# ============================================================
echo -n "Checking for large packages... "

# Known large packages and recommendations
LARGE_PACKAGES=(
    "moment:Consider dayjs (2KB vs 67KB)"
    "lodash:Use lodash-es or specific imports (import get from 'lodash/get')"
    "@mui/icons-material:Import specific icons instead of full package"
    "antd:Large bundle - ensure tree-shaking works"
    "firebase:Import only needed modules (firebase/auth, firebase/firestore)"
    "aws-sdk:Use @aws-sdk/* v3 modular packages"
    "rxjs:Ensure tree-shaking - import from 'rxjs/operators'"
)

LARGE_FOUND=""
for entry in "${LARGE_PACKAGES[@]}"; do
    PKG="${entry%%:*}"
    REASON="${entry#*:}"

    # Check if this large package is in NEW deps
    if echo "$NEW_DEPS" | grep -q "$PKG" 2>/dev/null; then
        LARGE_FOUND="$LARGE_FOUND\n  - $PKG: $REASON"
    fi
done

if [ -n "$LARGE_FOUND" ]; then
    echo -e "${YELLOW}WARNING${NC}"
    echo -e "${YELLOW}Large packages detected:${NC}"
    echo -e "$LARGE_FOUND"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 3: Removed Dependencies
# ============================================================
echo -n "Checking for removed dependencies... "

# Find removed dependencies (in HEAD but not in staged)
REMOVED_DEPS=""
for dep in $HEAD_DEPS; do
    if ! echo "$STAGED_DEPS" | grep -q "^${dep}$" 2>/dev/null; then
        REMOVED_DEPS="$REMOVED_DEPS $dep"
    fi
done

REMOVED_COUNT=$(echo "$REMOVED_DEPS" | wc -w)
if [ "$REMOVED_COUNT" -gt 0 ]; then
    echo -e "${GREEN}GOOD${NC}"
    echo -e "${GREEN}Dependencies removed (potential bundle reduction):${NC}"
    for dep in $REMOVED_DEPS; do
        echo "  - $dep"
    done
else
    echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 4: Build Reminder
# ============================================================
if [ "$NEW_COUNT" -gt 0 ] || [ "$REMOVED_COUNT" -gt 0 ]; then
    echo ""
    echo -e "${BLUE}Bundle may have changed. Before push:${NC}"
    echo -e "  ${CYAN}cd frontend && npm run build${NC}"
    echo -e "  ${CYAN}du -sh .next/  # Check output size${NC}"
    echo ""
fi

# ============================================================
# Check 5: Optional Full Build
# ============================================================
if [ "${BUNDLE_FULL:-0}" = "1" ]; then
    echo -e "${CYAN}Running full build check (BUNDLE_FULL=1)...${NC}"
    echo ""

    # Run build
    echo -n "Building frontend... "
    if cd "$FRONTEND_DIR" && npm run build >/dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"

        # Report size
        BUILD_SIZE=$(du -sh .next 2>/dev/null | cut -f1)
        echo -e "Build output size: ${CYAN}$BUILD_SIZE${NC}"

        # Check standalone size if exists
        if [ -d ".next/standalone" ]; then
            STANDALONE_SIZE=$(du -sh .next/standalone 2>/dev/null | cut -f1)
            echo -e "Standalone size: ${CYAN}$STANDALONE_SIZE${NC}"
        fi

        cd ..
    else
        echo -e "${RED}FAILED${NC}"
        echo -e "${RED}Frontend build failed${NC}"
        ERRORS=$((ERRORS + 1))
        cd ..
    fi
fi

# ============================================================
# Summary
# ============================================================
echo ""
if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}Bundle size check FAILED ($ERRORS error(s))${NC}"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}Bundle size check found $WARNINGS warning(s)${NC}"
    echo "Consider reviewing large package additions."
    exit 0
else
    echo -e "${GREEN}Bundle size check passed!${NC}"
    exit 0
fi
