#!/bin/bash
# ============================================================
# Script: validate-resilience-constraints.sh
# Purpose: Pre-commit hook for resilience/contingency validation
# Domain: RESILIENCE_ENGINEER Advisory
# Session: 082
#
# Resilience Rules Checked:
#   - N-1 contingency (system functions with 1 person absent)
#   - N-2 contingency (system functions with 2 people absent)
#   - Single-point-of-failure detection
#   - Critical role redundancy
#   - Burnout risk indicators
#
# Philosophy (Auftragstaktik):
#   Resilience is a boundary condition, not a suggestion.
#   Schedules must degrade gracefully, not catastrophically.
#
# Exit Codes:
#   0 - Validation passed
#   1 - Resilience concerns detected (warning mode)
# ============================================================

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

WARNINGS=0

echo -e "${CYAN}Running Resilience Constraint Check...${NC}"

# ============================================================
# Check 1: Single-point-of-failure patterns
# ============================================================
echo -n "Checking for single-point-of-failure risks... "

# Look for SPOF patterns in scheduling code (not the resilience framework itself)
# Tuned in Session 083: exclude resilience code, metrics fields, docstrings
SPOF_PATTERNS=$(grep -rn --include="*.py" --include="*.ts" \
  -iE '(only.?one.*available|single.*provider|sole.*coverage|no.*backup|without.*redundancy)' \
  backend/app/scheduling/ 2>/dev/null | \
  grep -v "test" | grep -v "__pycache__" | grep -v '"""' | grep -v "'''" | grep -v ':[ ]*#' | grep -v ':[ ]*- ' | grep -v '\.\.\.' | grep -v 'resilience' | grep -v 'sole_coverage_blocks' || true)

if [ -n "$SPOF_PATTERNS" ]; then
  echo -e "${YELLOW}WARNING${NC}"
  echo -e "${YELLOW}Potential single-point-of-failure patterns:${NC}"
  echo "$SPOF_PATTERNS" | head -5
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 2: N-1 contingency handling
# ============================================================
echo -n "Checking for N-1 contingency code... "

# Look for explicit N-1 bypass intent (not result fields like n1_pass=False)
# Tuned in Session 083 to reduce false positives
N1_ISSUES=$(grep -rn --include="*.py" --include="*.ts" \
  -iE '(skip_n1|bypass_n1|skip_contingency|bypass_resilience|disable_n1_check|force_n1_pass)' \
  backend/app/ 2>/dev/null | grep -v "test" || true)

if [ -n "$N1_ISSUES" ]; then
  echo -e "${RED}CRITICAL${NC}"
  echo -e "${RED}N-1 contingency bypass detected:${NC}"
  echo "$N1_ISSUES"
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 3: Critical role coverage
# ============================================================
echo -n "Checking for critical role definitions... "

# Look for critical roles without backup definitions
CRITICAL_ROLE_ISSUES=$(grep -rn --include="*.py" \
  -iE '(critical.*role|essential.*position|key.*personnel)' \
  backend/app/scheduling/ backend/app/models/ 2>/dev/null | \
  grep -v "backup" | grep -v "redundant" | grep -v "test" | head -5 || true)

if [ -n "$CRITICAL_ROLE_ISSUES" ]; then
  echo -e "${YELLOW}INFO${NC}"
  echo -e "${YELLOW}Critical roles found - verify backup coverage:${NC}"
  echo "$CRITICAL_ROLE_ISSUES"
  # Info only, not a warning
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 4: Burnout risk indicators
# ============================================================
echo -n "Checking for burnout risk patterns... "

# Look for consecutive shift patterns or high workload indicators
BURNOUT_PATTERNS=$(grep -rn --include="*.py" --include="*.ts" \
  -iE '(consecutive.*(7|8|9|[1-9][0-9]).*days?|workload.*exceed|overtime.*unlimited)' \
  backend/app/scheduling/ 2>/dev/null | grep -v "test" || true)

if [ -n "$BURNOUT_PATTERNS" ]; then
  echo -e "${YELLOW}WARNING${NC}"
  echo -e "${YELLOW}Potential burnout risk patterns:${NC}"
  echo "$BURNOUT_PATTERNS" | head -5
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 5: Resilience metrics bypass
# ============================================================
echo -n "Checking for resilience metric handling... "

# Look for explicit resilience bypass patterns (not config documentation like disable_reason=)
# Tuned in Session 083 to reduce false positives
METRIC_BYPASS=$(grep -rn --include="*.py" --include="*.ts" \
  -iE '(ignore_resilience|skip_burnout_check|disable_burnout_alert|force_Rt_zero|bypass_burnout)' \
  backend/app/resilience/ backend/app/scheduling/ 2>/dev/null | grep -v "test" || true)

if [ -n "$METRIC_BYPASS" ]; then
  echo -e "${RED}CRITICAL${NC}"
  echo -e "${RED}Resilience metric bypass detected:${NC}"
  echo "$METRIC_BYPASS"
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 6: Emergency coverage gaps
# ============================================================
echo -n "Checking for emergency coverage handling... "

# Look for emergency coverage being optional
EMERGENCY_GAPS=$(grep -rn --include="*.py" --include="*.ts" \
  -iE '(emergency.*optional|no.*emergency.*coverage|skip.*emergency)' \
  backend/app/scheduling/ 2>/dev/null | grep -v "test" || true)

if [ -n "$EMERGENCY_GAPS" ]; then
  echo -e "${YELLOW}WARNING${NC}"
  echo -e "${YELLOW}Emergency coverage gaps detected:${NC}"
  echo "$EMERGENCY_GAPS" | head -5
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Summary
# ============================================================
echo ""
if [ $WARNINGS -eq 0 ]; then
  echo -e "${GREEN}Resilience constraint check passed!${NC}"
  exit 0
else
  echo -e "${YELLOW}Resilience check found $WARNINGS potential issue(s)${NC}"
  echo -e "${YELLOW}Review above warnings before committing scheduling changes.${NC}"
  echo ""
  echo "Reference: docs/resilience/N1_N2_CONTINGENCY.md"
  echo "Advisory: RESILIENCE_ENGINEER agent for detailed analysis"
  # Blocking mode - graduated Session 083 after pattern tuning
  exit 1
fi
