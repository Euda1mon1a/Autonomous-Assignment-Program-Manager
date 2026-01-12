#!/usr/bin/env bash
# Pre-commit hook: Validate query parameters use snake_case
# Backend API expects snake_case, axios interceptor doesn't convert query strings
#
# Why this matters:
# - Axios interceptor converts request/response BODY keys (camelCase <-> snake_case)
# - But URL query strings bypass the interceptor entirely
# - Backend FastAPI expects snake_case: start_date, end_date, page_size, person_id
# - Frontend camelCase params are silently ignored, causing data not to load

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Checking for camelCase query parameters..."

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
  echo -e "${RED}ERROR: camelCase query parameters detected!${NC}"
  echo -e "${YELLOW}Backend API expects snake_case (e.g., start_date, not startDate)${NC}"
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

echo -e "${GREEN}✓ All query parameters use snake_case${NC}"
exit 0
