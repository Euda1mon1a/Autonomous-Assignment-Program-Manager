#!/usr/bin/env bash
# ============================================================================
# COUATL KILLER - Slays the camelCase serpent in query parameters
# ============================================================================
#
# Named after the D&D Couatl (feathered serpent) - camelCase is serpentine naming
# that slithers through your codebase causing silent API failures.
#
# The Couatl's curse: Axios interceptor converts request/response BODY keys
# but URL query strings bypass the interceptor entirely, causing:
#   - Backend expects: /api?start_date=2026-01-01
#   - Frontend sends:  /api?startDate=2026-01-01
#   - Result: Silent failure, data not loaded
#
# This hook slays any camelCase serpents before they reach production.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}Couatl Killer: Hunting camelCase serpents...${NC}"

# Pattern: Common camelCase param names that should be snake_case
# Add new patterns here as they're discovered
CAMEL_PARAMS="startDate|endDate|pageSize|personId|blockId|academicYear|pgyLevel|weekNumber|sourceFacultyId|sourceWeek|complexityLevel|entityType|entityId|rotationId|blockNumber|createdAt|updatedAt"

# Search in frontend source (exclude node_modules, tests, mocks)
VIOLATIONS=$(grep -rn --include="*.ts" --include="*.tsx" \
  -E "[?&]($CAMEL_PARAMS)=" \
  frontend/src/ 2>/dev/null | \
  grep -v "__tests__" | \
  grep -v "\.test\." | \
  grep -v "\.mock\." | \
  grep -v "// @query-param-ok" || true)

if [ -n "$VIOLATIONS" ]; then
  echo -e "${RED}SERPENT DETECTED! camelCase query parameters found!${NC}"
  echo -e "${YELLOW}The Couatl's curse: Backend expects snake_case, not camelCase${NC}"
  echo ""
  echo "$VIOLATIONS"
  echo ""
  echo -e "${YELLOW}Fix by converting to snake_case:${NC}"
  echo "  startDate    → start_date"
  echo "  endDate      → end_date"
  echo "  pageSize     → page_size"
  echo "  personId     → person_id"
  echo "  blockId      → block_id"
  echo "  academicYear → academic_year"
  echo "  pgyLevel     → pgy_level"
  echo ""
  echo -e "${YELLOW}To suppress a false positive, add comment: // @query-param-ok${NC}"
  exit 1
fi

echo -e "${GREEN}✓ No serpents found - all query params use snake_case${NC}"
exit 0
