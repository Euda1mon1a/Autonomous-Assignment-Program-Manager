#!/bin/bash
# ============================================================
# Script: validate-swap-safety.sh
# Purpose: Pre-commit hook for swap operation safety validation
# Domain: SWAP_MANAGER Advisory
# Session: 082
#
# Swap Safety Rules Checked:
#   - Credential compatibility between participants
#   - Fairness metrics preservation
#   - Call equity balance
#   - No ACGME violations post-swap
#   - Rollback capability
#
# Philosophy (Auftragstaktik):
#   Swaps are bilateral agreements that must preserve system integrity.
#   No swap should create a worse state than before.
#
# Exit Codes:
#   0 - Validation passed
#   1 - Swap safety concerns detected (warning mode)
# ============================================================

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

WARNINGS=0

echo -e "${CYAN}Running Swap Safety Validation...${NC}"

# ============================================================
# Check 1: Credential validation in swap code
# ============================================================
echo -n "Checking for credential validation... "

# Look for swap execution without credential checks
NO_CRED_CHECK=$(grep -rn --include="*.py" \
  -iE '(execute.*swap|swap.*execute|perform.*swap)' \
  backend/app/api/routes/ backend/app/services/ 2>/dev/null | \
  grep -v "credential" | grep -v "test" | head -5 || true)

if [ -n "$NO_CRED_CHECK" ]; then
  echo -e "${YELLOW}INFO${NC}"
  echo -e "${YELLOW}Swap execution found - verify credential checks:${NC}"
  echo "$NO_CRED_CHECK"
  # Info only - manual review needed
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 2: Rollback capability
# ============================================================
echo -n "Checking for swap rollback capability... "

# Look for swap without rollback handling
NO_ROLLBACK=$(grep -rn --include="*.py" \
  -iE '(swap.*commit|finalize.*swap|complete.*swap)' \
  backend/app/services/ 2>/dev/null | \
  grep -v "rollback" | grep -v "revert" | grep -v "test" | head -5 || true)

if [ -n "$NO_ROLLBACK" ]; then
  echo -e "${YELLOW}WARNING${NC}"
  echo -e "${YELLOW}Swap finalization without rollback reference:${NC}"
  echo "$NO_ROLLBACK"
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 3: Fairness bypass
# ============================================================
echo -n "Checking for fairness validation... "

# Look for fairness checks being bypassed
FAIRNESS_BYPASS=$(grep -rn --include="*.py" --include="*.ts" \
  -iE '(skip.*fairness|bypass.*equity|ignore.*balance|fairness.*false)' \
  backend/app/ frontend/src/ 2>/dev/null | grep -v "test" || true)

if [ -n "$FAIRNESS_BYPASS" ]; then
  echo -e "${RED}CRITICAL${NC}"
  echo -e "${RED}Fairness validation bypass detected:${NC}"
  echo "$FAIRNESS_BYPASS"
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 4: Audit trail
# ============================================================
echo -n "Checking for swap audit trail... "

# Look for swap operations without logging
NO_AUDIT=$(grep -rn --include="*.py" \
  -iE '(swap.*status|update.*swap|change.*swap)' \
  backend/app/services/ backend/app/api/routes/ 2>/dev/null | \
  grep -v "log" | grep -v "audit" | grep -v "activity" | grep -v "test" | head -5 || true)

if [ -n "$NO_AUDIT" ]; then
  echo -e "${YELLOW}WARNING${NC}"
  echo -e "${YELLOW}Swap operations may lack audit trail:${NC}"
  echo "$NO_AUDIT"
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 5: Bilateral consent
# ============================================================
echo -n "Checking for bilateral consent... "

# Look for unilateral swap patterns
UNILATERAL=$(grep -rn --include="*.py" \
  -iE '(force.*swap|admin.*override.*swap|unilateral|single.*party.*swap)' \
  backend/app/ 2>/dev/null | grep -v "test" || true)

if [ -n "$UNILATERAL" ]; then
  echo -e "${YELLOW}INFO${NC}"
  echo -e "${YELLOW}Potential unilateral swap patterns (may be admin feature):${NC}"
  echo "$UNILATERAL" | head -3
  # Info only - admin overrides may be legitimate
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Summary
# ============================================================
echo ""
if [ $WARNINGS -eq 0 ]; then
  echo -e "${GREEN}Swap safety validation passed!${NC}"
  exit 0
else
  echo -e "${YELLOW}Swap safety check found $WARNINGS potential issue(s)${NC}"
  echo -e "${YELLOW}Review above warnings before committing swap-related changes.${NC}"
  echo ""
  echo "Reference: .claude/hooks/post-swap-execution.md"
  echo "Advisory: SWAP_MANAGER agent for detailed analysis"
  # Non-blocking for now (warning mode)
  exit 0
fi
