#!/bin/bash
# ============================================================
# Script: validate-test-coverage.sh
# Purpose: Pre-commit hook for test coverage validation
# Domain: QA Advisory
# Session: 084
#
# Problem: Coverage drops are only caught in CI after push.
#          This hook provides earlier feedback at commit time.
#
# Checks:
#   1. Backend test file existence for changed Python files
#   2. Frontend test file existence for changed TypeScript files
#   3. Reminder to run tests before push
#   4. Optional full coverage run with COVERAGE_FULL=1
#
# Philosophy (Auftragstaktik):
#   Fast by default, thorough on demand. CI enforces hard gates;
#   pre-commit provides early warning and developer guidance.
#
# Exit Codes:
#   0 - Validation passed (warnings allowed)
#   1 - Validation failed (only with COVERAGE_FULL=1)
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

echo -e "${CYAN}Running Test Coverage Check...${NC}"

# ============================================================
# Check 1: Backend Test File Existence
# ============================================================
echo -n "Checking backend test file coverage... "

# Get staged Python files in backend/app (excluding __init__.py, alembic)
BACKEND_FILES=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null | \
    grep -E "^backend/app/.*\.py$" | \
    grep -v "__init__\.py" | \
    grep -v "alembic" || true)

MISSING_BACKEND_TESTS=""
if [ -n "$BACKEND_FILES" ]; then
    for file in $BACKEND_FILES; do
        # Extract module path: backend/app/services/foo.py -> services/foo
        MODULE_PATH=$(echo "$file" | sed 's|backend/app/||' | sed 's|\.py$||')
        MODULE_NAME=$(basename "$MODULE_PATH")

        # Skip if it's already a test file
        if [[ "$MODULE_NAME" == test_* ]]; then
            continue
        fi

        # Check for corresponding test file patterns
        # Pattern 1: backend/tests/test_<module>.py
        # Pattern 2: backend/tests/<path>/test_<module>.py
        TEST_FOUND=false

        # Check direct test file
        if [ -f "backend/tests/test_${MODULE_NAME}.py" ]; then
            TEST_FOUND=true
        fi

        # Check nested test file
        PARENT_DIR=$(dirname "$MODULE_PATH")
        if [ -f "backend/tests/${PARENT_DIR}/test_${MODULE_NAME}.py" ]; then
            TEST_FOUND=true
        fi

        # Check for any test file containing the module name
        if find backend/tests -name "test_*${MODULE_NAME}*.py" -type f 2>/dev/null | grep -q .; then
            TEST_FOUND=true
        fi

        if [ "$TEST_FOUND" = false ]; then
            MISSING_BACKEND_TESTS="$MISSING_BACKEND_TESTS $file"
        fi
    done
fi

MISSING_BACKEND_COUNT=$(echo "$MISSING_BACKEND_TESTS" | wc -w)
if [ "$MISSING_BACKEND_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}WARNING${NC}"
    echo -e "${YELLOW}Python files without obvious test coverage:${NC}"
    for f in $MISSING_BACKEND_TESTS; do
        echo "  - $f"
    done | head -5
    if [ "$MISSING_BACKEND_COUNT" -gt 5 ]; then
        echo "  ... and $((MISSING_BACKEND_COUNT - 5)) more"
    fi
    WARNINGS=$((WARNINGS + 1))
else
    STAGED_BACKEND_COUNT=$(echo "$BACKEND_FILES" | wc -w)
    if [ "$STAGED_BACKEND_COUNT" -gt 0 ]; then
        echo -e "${GREEN}OK${NC} ($STAGED_BACKEND_COUNT files have tests)"
    else
        echo -e "${GREEN}OK${NC} (no Python files staged)"
    fi
fi

# ============================================================
# Check 2: Frontend Test File Existence
# ============================================================
echo -n "Checking frontend test file coverage... "

# Get staged TypeScript files in frontend/src (excluding types, mocks)
FRONTEND_FILES=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null | \
    grep -E "^frontend/src/.*\.(ts|tsx)$" | \
    grep -v "\.d\.ts$" | \
    grep -v "__tests__" | \
    grep -v "__mocks__" | \
    grep -v "types/" | \
    grep -v "mocks/" || true)

MISSING_FRONTEND_TESTS=""
if [ -n "$FRONTEND_FILES" ]; then
    for file in $FRONTEND_FILES; do
        # Extract component/module name
        FILENAME=$(basename "$file")
        MODULE_NAME="${FILENAME%.*}"  # Remove extension
        MODULE_NAME="${MODULE_NAME%.test}"  # Remove .test if present

        # Skip if it's already a test file
        if [[ "$FILENAME" == *.test.* ]] || [[ "$FILENAME" == *.spec.* ]]; then
            continue
        fi

        # Check for corresponding test file patterns
        # Pattern 1: Same directory __tests__/<name>.test.ts(x)
        # Pattern 2: Adjacent <name>.test.ts(x)
        TEST_FOUND=false

        DIR=$(dirname "$file")

        # Check __tests__ subdirectory
        if [ -f "${DIR}/__tests__/${MODULE_NAME}.test.ts" ] || \
           [ -f "${DIR}/__tests__/${MODULE_NAME}.test.tsx" ]; then
            TEST_FOUND=true
        fi

        # Check adjacent test file
        if [ -f "${DIR}/${MODULE_NAME}.test.ts" ] || \
           [ -f "${DIR}/${MODULE_NAME}.test.tsx" ]; then
            TEST_FOUND=true
        fi

        # Check for any test file containing the module name
        if find frontend/src -name "*${MODULE_NAME}*.test.*" -type f 2>/dev/null | grep -q .; then
            TEST_FOUND=true
        fi

        if [ "$TEST_FOUND" = false ]; then
            MISSING_FRONTEND_TESTS="$MISSING_FRONTEND_TESTS $file"
        fi
    done
fi

MISSING_FRONTEND_COUNT=$(echo "$MISSING_FRONTEND_TESTS" | wc -w)
if [ "$MISSING_FRONTEND_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}WARNING${NC}"
    echo -e "${YELLOW}TypeScript files without obvious test coverage:${NC}"
    for f in $MISSING_FRONTEND_TESTS; do
        echo "  - $f"
    done | head -5
    if [ "$MISSING_FRONTEND_COUNT" -gt 5 ]; then
        echo "  ... and $((MISSING_FRONTEND_COUNT - 5)) more"
    fi
    WARNINGS=$((WARNINGS + 1))
else
    STAGED_FRONTEND_COUNT=$(echo "$FRONTEND_FILES" | wc -w)
    if [ "$STAGED_FRONTEND_COUNT" -gt 0 ]; then
        echo -e "${GREEN}OK${NC} ($STAGED_FRONTEND_COUNT files have tests)"
    else
        echo -e "${GREEN}OK${NC} (no TypeScript files staged)"
    fi
fi

# ============================================================
# Check 3: Test Run Reminder
# ============================================================
HAS_BACKEND_CHANGES=$(echo "$BACKEND_FILES" | wc -w)
HAS_FRONTEND_CHANGES=$(echo "$FRONTEND_FILES" | wc -w)

if [ "$HAS_BACKEND_CHANGES" -gt 0 ] || [ "$HAS_FRONTEND_CHANGES" -gt 0 ]; then
    echo ""
    echo -e "${BLUE}Remember to run tests before push:${NC}"
    if [ "$HAS_BACKEND_CHANGES" -gt 0 ]; then
        echo -e "  ${CYAN}cd backend && pytest --cov=app --cov-report=term-missing${NC}"
    fi
    if [ "$HAS_FRONTEND_CHANGES" -gt 0 ]; then
        echo -e "  ${CYAN}cd frontend && npm test:coverage${NC}"
    fi
    echo ""
fi

# ============================================================
# Check 4: Optional Full Coverage Run
# ============================================================
if [ "${COVERAGE_FULL:-0}" = "1" ]; then
    echo -e "${CYAN}Running full coverage check (COVERAGE_FULL=1)...${NC}"
    echo ""

    # Backend coverage
    if [ "$HAS_BACKEND_CHANGES" -gt 0 ]; then
        echo -n "Running backend tests with coverage... "
        if cd backend && pytest --cov=app --cov-fail-under=70 -q 2>/dev/null; then
            echo -e "${GREEN}PASSED${NC}"
            cd ..
        else
            echo -e "${RED}FAILED${NC}"
            echo -e "${RED}Backend coverage below 70% threshold${NC}"
            ERRORS=$((ERRORS + 1))
            cd ..
        fi
    fi

    # Frontend coverage
    if [ "$HAS_FRONTEND_CHANGES" -gt 0 ]; then
        echo -n "Running frontend tests with coverage... "
        if cd frontend && npm test -- --coverage --passWithNoTests 2>/dev/null; then
            echo -e "${GREEN}PASSED${NC}"
            cd ..
        else
            echo -e "${RED}FAILED${NC}"
            echo -e "${RED}Frontend coverage below threshold${NC}"
            ERRORS=$((ERRORS + 1))
            cd ..
        fi
    fi
fi

# ============================================================
# Summary
# ============================================================
echo ""
if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}Test coverage check FAILED ($ERRORS error(s))${NC}"
    echo "Fix coverage issues before committing."
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}Test coverage check found $WARNINGS warning(s)${NC}"
    echo "Consider adding tests for files without coverage."
    # Warnings only - don't block
    exit 0
else
    echo -e "${GREEN}Test coverage check passed!${NC}"
    exit 0
fi
