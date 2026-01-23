#!/usr/bin/env bash
# ============================================================================
# GORGON'S GAZE - Petrifies camelCase enum values before they cause runtime failures
# ============================================================================
#
# Named after the D&D Medusa/Gorgon - whose gaze turns victims to stone.
# camelCase enum values will petrify your code at runtime when comparisons
# silently fail against snake_case backend values.
#
# The Gorgon's curse: Axios interceptor converts object KEYS to camelCase
# but enum VALUES pass through unchanged. If frontend uses 'cpSat' but
# backend sends 'cp_sat', comparisons fail silently:
#   - Backend sends:    { algorithm: "cp_sat" }
#   - Frontend expects: algorithm === 'cpSat'
#   - Result: Never matches, logic breaks silently
#
# This hook catches camelCase enum values before they reach production.
# See CLAUDE.md "Enum Values Stay snake_case (Gorgon's Gaze)" for details.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

echo -e "${MAGENTA}Gorgon's Gaze: Seeking camelCase enum values...${NC}"

# Known camelCase enum values that should be snake_case
# These are backend enum values that MUST match exactly
# Add new patterns here as violations are discovered
CAMEL_ENUMS="deptChief|sportsMed|cpSat|titForTat|suspiciousTft|forgivingTft|timeOff|fmClinic"

# Pattern explanation:
# - Match string literals containing known camelCase enum values
# - Look for: 'enumValue' or "enumValue"
# - Captures both type definitions and runtime usage

VIOLATIONS=$(grep -rn --include="*.ts" --include="*.tsx" \
  -E "['\"](${CAMEL_ENUMS})['\"]" \
  frontend/src/ 2>/dev/null | \
  grep -v "// @enum-ok" | \
  grep -v "// @gorgon-ok" | \
  grep -v "__mocks__" || true)

if [ -n "$VIOLATIONS" ]; then
  echo -e "${RED}PETRIFIED! camelCase enum values detected!${NC}"
  echo -e "${YELLOW}The Gorgon's curse: Backend sends snake_case, frontend must match${NC}"
  echo ""
  echo "$VIOLATIONS"
  echo ""
  echo -e "${YELLOW}Fix by converting to snake_case:${NC}"
  echo "  'deptChief'     → 'dept_chief'"
  echo "  'sportsMed'     → 'sports_med'"
  echo "  'cpSat'         → 'cp_sat'"
  echo "  'titForTat'     → 'tit_for_tat'"
  echo "  'suspiciousTft' → 'suspicious_tft'"
  echo "  'forgivingTft'  → 'forgiving_tft'"
  echo "  'timeOff'       → 'time_off'"
  echo "  'fmClinic'      → 'fm_clinic'"
  echo ""
  echo -e "${CYAN}Why this matters:${NC}"
  echo "  Axios converts object KEYS (snake→camel) but NOT enum VALUES."
  echo "  Backend: { faculty_role: 'dept_chief' } → Frontend: { facultyRole: 'dept_chief' }"
  echo "  If frontend checks: role === 'deptChief' → NEVER MATCHES!"
  echo ""
  echo -e "${YELLOW}To suppress a false positive, add comment: // @enum-ok or // @gorgon-ok${NC}"
  exit 1
fi

echo -e "${GREEN}✓ No petrification risk - all enum values use snake_case${NC}"
exit 0
