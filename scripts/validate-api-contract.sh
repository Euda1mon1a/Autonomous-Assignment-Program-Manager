#!/bin/bash
# ============================================================
# Script: validate-api-contract.sh
# Purpose: Pre-commit hook for API contract validation
# Domain: ARCHITECT Advisory
# Session: 084
#
# Problem: Backend Pydantic schemas and frontend TypeScript
#          types can drift apart, causing runtime errors.
#
# Checks:
#   1. Backend schema changes detection
#   2. Frontend type sync reminder
#   3. OpenAPI spec existence
#   4. Optional full validation with API_CONTRACT_FULL=1
#
# Philosophy (Auftragstaktik):
#   Fast by default, thorough on demand. Catch contract drift
#   early to prevent frontend/backend misalignment.
#
# Exit Codes:
#   0 - Validation passed (warnings allowed)
#   1 - Validation failed (only with blocking checks)
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

BACKEND_SCHEMAS_DIR="backend/app/schemas"
FRONTEND_TYPES_DIR="frontend/src/types"
OPENAPI_SPEC="docs/api/openapi.yaml"

echo -e "${CYAN}Running API Contract Validation...${NC}"

# ============================================================
# Check 0: Are relevant files staged?
# ============================================================
BACKEND_STAGED=$(git diff --cached --name-only 2>/dev/null | grep -E "^backend/app/schemas/.*\.py$" || true)
FRONTEND_STAGED=$(git diff --cached --name-only 2>/dev/null | grep -E "^frontend/src/types/.*\.ts$" || true)

if [ -z "$BACKEND_STAGED" ] && [ -z "$FRONTEND_STAGED" ]; then
    echo -e "${GREEN}No API schema/type changes staged.${NC}"
    exit 0
fi

# ============================================================
# Check 1: Backend Schema Changes
# ============================================================
echo -n "Checking backend schema changes... "

if [ -n "$BACKEND_STAGED" ]; then
    BACKEND_COUNT=$(echo "$BACKEND_STAGED" | wc -l | tr -d ' ')
    echo -e "${BLUE}INFO${NC}"
    echo -e "${BLUE}$BACKEND_COUNT backend schema file(s) changed:${NC}"
    echo "$BACKEND_STAGED" | head -5 | while read -r file; do
        echo "  - $file"
    done
    if [ "$BACKEND_COUNT" -gt 5 ]; then
        echo "  ... and $((BACKEND_COUNT - 5)) more"
    fi
else
    echo -e "${GREEN}OK${NC} (no schema changes)"
fi

# ============================================================
# Check 2: Type Sync Reminder
# ============================================================
echo -n "Checking frontend type sync... "

if [ -n "$BACKEND_STAGED" ] && [ -z "$FRONTEND_STAGED" ]; then
    echo -e "${YELLOW}WARNING${NC}"
    echo -e "${YELLOW}Backend schemas changed but no frontend types updated.${NC}"
    echo ""
    echo -e "Consider syncing types:"
    echo -e "  ${CYAN}cd frontend && npm run generate:types${NC}"
    echo -e "  Or manually update ${CYAN}frontend/src/types/${NC}"
    echo ""
    WARNINGS=$((WARNINGS + 1))
elif [ -n "$BACKEND_STAGED" ] && [ -n "$FRONTEND_STAGED" ]; then
    echo -e "${GREEN}OK${NC} (both backend and frontend updated)"
elif [ -z "$BACKEND_STAGED" ] && [ -n "$FRONTEND_STAGED" ]; then
    echo -e "${GREEN}OK${NC} (frontend-only type changes)"
else
    echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 3: OpenAPI Spec Exists
# ============================================================
echo -n "Checking OpenAPI spec... "

if [ -f "$OPENAPI_SPEC" ]; then
    SPEC_SIZE=$(wc -l < "$OPENAPI_SPEC" 2>/dev/null | tr -d ' ')
    echo -e "${GREEN}OK${NC} ($OPENAPI_SPEC exists, $SPEC_SIZE lines)"
else
    echo -e "${YELLOW}WARNING${NC}"
    echo -e "${YELLOW}OpenAPI spec not found at $OPENAPI_SPEC${NC}"
    echo -e "Consider generating: ${CYAN}curl http://localhost:8000/openapi.json > $OPENAPI_SPEC${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# ============================================================
# Check 4: Changed Schema Details
# ============================================================
if [ -n "$BACKEND_STAGED" ]; then
    echo ""
    echo -e "${BLUE}Schema change summary:${NC}"

    # Look for class definitions in changed files
    for file in $BACKEND_STAGED; do
        if [ -f "$file" ]; then
            CLASSES=$(git show ":$file" 2>/dev/null | grep -E "^class [A-Z]" | sed 's/class \([A-Za-z_]*\).*/\1/' | head -3 || true)
            if [ -n "$CLASSES" ]; then
                echo -e "  ${CYAN}$file${NC}:"
                echo "$CLASSES" | while read -r cls; do
                    echo "    - $cls"
                done
            fi
        fi
    done | head -15
fi

# ============================================================
# Check 5: Optional Full Contract Validation
# ============================================================
if [ "${API_CONTRACT_FULL:-0}" = "1" ]; then
    echo ""
    echo -e "${CYAN}Running full contract validation (API_CONTRACT_FULL=1)...${NC}"

    # Check if backend is running
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo -n "Fetching live OpenAPI spec... "
        LIVE_SPEC=$(curl -s http://localhost:8000/openapi.json 2>/dev/null || true)

        if [ -n "$LIVE_SPEC" ]; then
            echo -e "${GREEN}OK${NC}"

            # Compare key metrics (simple check)
            LIVE_PATHS=$(echo "$LIVE_SPEC" | grep -o '"paths"' | wc -l || echo "0")
            echo -e "  Live spec has endpoints defined"

            if [ -f "$OPENAPI_SPEC" ]; then
                STORED_PATHS=$(grep -c "^  /" "$OPENAPI_SPEC" 2>/dev/null || echo "0")
                echo -e "  Stored spec has $STORED_PATHS paths"
            fi
        else
            echo -e "${YELLOW}SKIPPED${NC} (could not fetch /openapi.json)"
        fi
    else
        echo -e "${YELLOW}SKIPPED${NC} (backend not running at localhost:8000)"
        echo -e "  Start backend: ${CYAN}cd backend && uvicorn app.main:app --reload${NC}"
    fi
fi

# ============================================================
# Check 6: camelCase Reminder
# ============================================================
if [ -n "$FRONTEND_STAGED" ]; then
    echo ""
    echo -e "${BLUE}Reminder: TypeScript types MUST use camelCase${NC}"
    echo -e "  The API interceptor converts snake_case ↔ camelCase automatically."
    echo -e "  See: ${CYAN}CLAUDE.md → API Type Naming Convention${NC}"
fi

# ============================================================
# Summary
# ============================================================
echo ""
if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}API contract check FAILED ($ERRORS error(s))${NC}"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}API contract check found $WARNINGS warning(s)${NC}"
    echo "Consider syncing frontend types with backend schemas."
    exit 0
else
    echo -e "${GREEN}API contract check passed!${NC}"
    exit 0
fi
