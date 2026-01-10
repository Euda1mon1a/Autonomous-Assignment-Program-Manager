#!/bin/bash
# ============================================================
# Script: validate-performance-regression.sh
# Purpose: Pre-commit hook for performance regression detection
# Domain: QA Advisory
# Session: 085
#
# Problem: Slow tests and performance regressions are caught
#          late in CI. This hook provides early warning at
#          commit time.
#
# Checks:
#   1. Staged test file detection
#   2. Quick timing analysis (--durations)
#   3. Slow test warning (>2s threshold)
#   4. Optional full performance run with PERF_FULL=1
#
# Philosophy (Auftragstaktik):
#   Fast by default, thorough on demand. Monitor test timing
#   to catch regressions before they reach CI.
#
# Exit Codes:
#   0 - Validation passed (warnings allowed)
#   1 - Validation failed (only with PERF_FULL=1)
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

# Threshold in seconds for slow test warning
SLOW_THRESHOLD="${SLOW_THRESHOLD:-2.0}"

echo -e "${CYAN}Running Performance Regression Check...${NC}"

# ============================================================
# Check 0: Are backend files staged?
# ============================================================
BACKEND_STAGED=$(git diff --cached --name-only 2>/dev/null | grep -E "^backend/(app|tests)/.*\.py$" || true)
TEST_FILES_STAGED=$(git diff --cached --name-only 2>/dev/null | grep -E "^backend/tests/.*\.py$" || true)

if [ -z "$BACKEND_STAGED" ]; then
    echo -e "${GREEN}No backend code changes staged.${NC}"
    exit 0
fi

# ============================================================
# Check 1: Test File Detection
# ============================================================
echo -n "Checking staged files... "

BACKEND_COUNT=$(echo "$BACKEND_STAGED" | wc -l | tr -d ' ')
TEST_COUNT=0
if [ -n "$TEST_FILES_STAGED" ]; then
    TEST_COUNT=$(echo "$TEST_FILES_STAGED" | wc -l | tr -d ' ')
fi

echo -e "${GREEN}OK${NC}"
echo -e "${BLUE}$BACKEND_COUNT backend file(s) staged ($TEST_COUNT test files)${NC}"

# ============================================================
# Check 2: Existing Slow Test Markers
# ============================================================
echo -n "Checking for slow test markers... "

SLOW_MARKED=0
if [ -n "$TEST_FILES_STAGED" ]; then
    for file in $TEST_FILES_STAGED; do
        if [ -f "$file" ]; then
            # Count @pytest.mark.slow decorators
            MARKS=$(grep -c "@pytest.mark.slow" "$file" 2>/dev/null | tr -d '[:space:]' || echo "0")
            MARKS=${MARKS:-0}
            SLOW_MARKED=$((SLOW_MARKED + MARKS))
        fi
    done
fi

if [ "$SLOW_MARKED" -gt 0 ]; then
    echo -e "${GREEN}OK${NC} ($SLOW_MARKED slow-marked tests found)"
else
    echo -e "${GREEN}OK${NC} (no slow-marked tests in staged files)"
fi

# ============================================================
# Check 3: Performance Test File Detection
# ============================================================
echo -n "Checking for performance test changes... "

PERF_TESTS_STAGED=$(echo "$TEST_FILES_STAGED" | grep -E "performance/" || true)
if [ -n "$PERF_TESTS_STAGED" ]; then
    PERF_COUNT=$(echo "$PERF_TESTS_STAGED" | wc -l | tr -d ' ')
    echo -e "${BLUE}INFO${NC}"
    echo -e "${BLUE}$PERF_COUNT performance test file(s) modified:${NC}"
    echo "$PERF_TESTS_STAGED" | head -5 | while read -r file; do
        echo "  - $file"
    done
else
    echo -e "${GREEN}OK${NC} (no performance tests changed)"
fi

# ============================================================
# Check 4: Known Slow Patterns
# ============================================================
echo -n "Checking for slow patterns in staged code... "

SLOW_PATTERNS=0
SLOW_PATTERN_FILES=""

for file in $BACKEND_STAGED; do
    if [ -f "$file" ]; then
        # Check for patterns that typically indicate slow operations
        # - time.sleep (intentional delays)
        # - large iterations (for i in range(10000))
        # - heavy DB operations in tests (create 100+ records)

        if git show ":$file" 2>/dev/null | grep -qE "time\.sleep\([0-9]+\)|range\([0-9]{4,}\)|for .* in range\(100"; then
            SLOW_PATTERNS=$((SLOW_PATTERNS + 1))
            SLOW_PATTERN_FILES="$SLOW_PATTERN_FILES $file"
        fi
    fi
done

if [ "$SLOW_PATTERNS" -gt 0 ]; then
    echo -e "${YELLOW}WARNING${NC}"
    echo -e "${YELLOW}Potentially slow patterns detected in $SLOW_PATTERNS file(s):${NC}"
    for file in $SLOW_PATTERN_FILES; do
        echo "  - $file"
    done
    echo ""
    echo -e "Consider marking with ${CYAN}@pytest.mark.slow${NC} if intentional."
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 5: Test Timing Reminder
# ============================================================
if [ -n "$TEST_FILES_STAGED" ]; then
    echo ""
    echo -e "${BLUE}Test files modified. Before push, verify timing:${NC}"
    echo -e "  ${CYAN}cd backend && pytest --durations=10 -q${NC}"
    echo -e "  ${CYAN}pytest -m 'not slow' --durations=5${NC}"
    echo ""
fi

# ============================================================
# Check 6: Optional Full Performance Run
# ============================================================
if [ "${PERF_FULL:-0}" = "1" ]; then
    echo ""
    echo -e "${CYAN}Running full performance check (PERF_FULL=1)...${NC}"
    echo ""

    # Check if we're in the backend directory or need to cd
    if [ -d "backend" ]; then
        BACKEND_DIR="backend"
    elif [ -f "pyproject.toml" ] && grep -q "app.main" pyproject.toml 2>/dev/null; then
        BACKEND_DIR="."
    else
        echo -e "${YELLOW}SKIPPED${NC} (not in project root or backend directory)"
        echo ""
        echo -e "${YELLOW}Performance check found $WARNINGS warning(s)${NC}"
        exit 0
    fi

    # Run quick subset with timing
    echo -n "Running fast tests with timing... "
    cd "$BACKEND_DIR"

    # Run pytest with durations, capture output
    PYTEST_OUTPUT=$(pytest tests/ -m "not slow and not integration" --durations=10 -q 2>&1 || true)
    PYTEST_EXIT=$?

    if [ $PYTEST_EXIT -eq 0 ] || [ $PYTEST_EXIT -eq 5 ]; then
        # Exit 5 means no tests collected (not an error)
        echo -e "${GREEN}OK${NC}"

        # Parse slowest tests from durations output
        SLOW_TESTS=$(echo "$PYTEST_OUTPUT" | grep -E "^[0-9]+\.[0-9]+s" | head -5 || true)
        if [ -n "$SLOW_TESTS" ]; then
            echo ""
            echo -e "${BLUE}Slowest tests:${NC}"
            echo "$SLOW_TESTS" | while read -r line; do
                # Extract time and check against threshold
                TIME=$(echo "$line" | grep -oE "^[0-9]+\.[0-9]+" || echo "0")
                if (( $(echo "$TIME > $SLOW_THRESHOLD" | bc -l 2>/dev/null || echo "0") )); then
                    echo -e "  ${YELLOW}$line${NC} (exceeds ${SLOW_THRESHOLD}s threshold)"
                    WARNINGS=$((WARNINGS + 1))
                else
                    echo "  $line"
                fi
            done
        fi
    else
        echo -e "${RED}FAILED${NC}"
        echo -e "${RED}Tests failed - check output above${NC}"
        ERRORS=$((ERRORS + 1))
    fi

    cd - > /dev/null

    # Run performance tests specifically
    if [ -d "$BACKEND_DIR/tests/performance" ]; then
        echo ""
        echo -n "Running performance tests... "
        cd "$BACKEND_DIR"

        PERF_OUTPUT=$(pytest tests/performance/ -v --durations=0 -q 2>&1 || true)
        PERF_EXIT=$?

        if [ $PERF_EXIT -eq 0 ]; then
            echo -e "${GREEN}OK${NC}"

            # Show summary
            PERF_PASSED=$(echo "$PERF_OUTPUT" | grep -oE "[0-9]+ passed" | head -1 || echo "0 passed")
            echo -e "  Performance tests: ${GREEN}$PERF_PASSED${NC}"
        elif [ $PERF_EXIT -eq 5 ]; then
            echo -e "${YELLOW}SKIPPED${NC} (no performance tests found)"
        else
            echo -e "${RED}FAILED${NC}"
            echo -e "${RED}Performance tests failed - potential regression${NC}"
            ERRORS=$((ERRORS + 1))
        fi

        cd - > /dev/null
    fi
fi

# ============================================================
# Summary
# ============================================================
echo ""
if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}Performance check FAILED ($ERRORS error(s))${NC}"
    echo "Fix test failures before committing."
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}Performance check found $WARNINGS warning(s)${NC}"
    echo "Consider reviewing slow patterns or test timing."
    exit 0
else
    echo -e "${GREEN}Performance check passed!${NC}"
    exit 0
fi
