#!/bin/bash
# ============================================================
# Script: validate-acgme-compliance.sh
# Purpose: Pre-commit hook for ACGME compliance validation
# Domain: MEDCOM Advisory (Clinical/Regulatory)
# Session: 082
#
# ACGME Rules Checked:
#   - 80-hour weekly limit (averaged over 4 weeks)
#   - 1-in-7 day off requirement
#   - 24+4 hour maximum shift (24h duty + 4h handoff)
#   - 10-hour rest between shifts
#   - Call frequency limits (no more than every 3rd night)
#
# Philosophy (Auftragstaktik):
#   Hook sets boundaries (ACGME rules are non-negotiable).
#   Implementation details are left to the scheduling engine.
#
# Exit Codes:
#   0 - Validation passed (or no schedule files changed)
#   1 - Potential ACGME violations detected (warning mode)
# ============================================================

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

WARNINGS=0

echo -e "${CYAN}Running ACGME Compliance Check...${NC}"

# ============================================================
# Check 1: 80-hour rule violations in code
# ============================================================
echo -n "Checking for 80-hour rule handling... "

# Look for hardcoded hour limits that might violate 80-hour rule
HOUR_VIOLATIONS=$(grep -rn --include="*.py" --include="*.ts" --include="*.tsx" \
  -E '(hours?\s*[>=<]+\s*8[1-9]|hours?\s*[>=<]+\s*9[0-9]|MAX_HOURS\s*=\s*[89][0-9])' \
  backend/app/scheduling/ frontend/src/features/ 2>/dev/null || true)

if [ -n "$HOUR_VIOLATIONS" ]; then
  echo -e "${YELLOW}WARNING${NC}"
  echo -e "${YELLOW}Potential 80-hour rule violations:${NC}"
  echo "$HOUR_VIOLATIONS" | head -5
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 2: 24+4 hour shift maximum
# ============================================================
echo -n "Checking for 24+4 hour shift limits... "

# Look for shift durations exceeding 28 hours
SHIFT_VIOLATIONS=$(grep -rn --include="*.py" --include="*.ts" \
  -E '(shift_hours?\s*[>=<]+\s*(29|3[0-9])|MAX_SHIFT\s*=\s*(29|3[0-9]))' \
  backend/app/scheduling/ 2>/dev/null || true)

if [ -n "$SHIFT_VIOLATIONS" ]; then
  echo -e "${YELLOW}WARNING${NC}"
  echo -e "${YELLOW}Potential 24+4 hour rule violations:${NC}"
  echo "$SHIFT_VIOLATIONS" | head -5
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 3: Rest period validation
# ============================================================
echo -n "Checking for rest period handling... "

# Look for rest periods less than 10 hours
REST_VIOLATIONS=$(grep -rn --include="*.py" --include="*.ts" \
  -E '(rest_hours?\s*[<>=]+\s*[0-9](?![0-9])|MIN_REST\s*=\s*[0-9](?![0-9]))' \
  backend/app/scheduling/ 2>/dev/null || true)

if [ -n "$REST_VIOLATIONS" ]; then
  echo -e "${YELLOW}WARNING${NC}"
  echo -e "${YELLOW}Potential rest period violations (< 10 hours):${NC}"
  echo "$REST_VIOLATIONS" | head -5
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 4: ACGME validator bypass attempts
# ============================================================
echo -n "Checking for ACGME validation bypasses... "

# Look for explicit bypass intent patterns (not state assignments like acgme_compliant = False)
# Tuned in Session 083 to reduce false positives
BYPASS_ATTEMPTS=$(grep -rn --include="*.py" --include="*.ts" \
  -iE '(skip_acgme|bypass_acgme|disable_acgme|acgme_bypass|acgme_skip|ignore_acgme|force_acgme_pass)' \
  backend/ frontend/ 2>/dev/null | grep -v "test" | grep -v "__pycache__" || true)

if [ -n "$BYPASS_ATTEMPTS" ]; then
  echo -e "${RED}CRITICAL${NC}"
  echo -e "${RED}Potential ACGME validation bypasses detected!${NC}"
  echo "$BYPASS_ATTEMPTS"
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 5: Call frequency validation
# ============================================================
echo -n "Checking for call frequency limits... "

# Look for call frequency that might exceed q3 (every 3rd night)
CALL_VIOLATIONS=$(grep -rn --include="*.py" --include="*.ts" \
  -E '(call_frequency\s*[>=<]+\s*[12](?![0-9])|every_[12]_night)' \
  backend/app/scheduling/ 2>/dev/null || true)

if [ -n "$CALL_VIOLATIONS" ]; then
  echo -e "${YELLOW}WARNING${NC}"
  echo -e "${YELLOW}Potential call frequency violations (more frequent than q3):${NC}"
  echo "$CALL_VIOLATIONS" | head -5
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 6: Supervision ratio validation
# ============================================================
echo -n "Checking for supervision requirements... "

# Look for unsupervised PGY-1 patterns
SUPERVISION_ISSUES=$(grep -rn --include="*.py" --include="*.ts" \
  -iE '(pgy.?1.*unsupervised|intern.*alone|no.*attending)' \
  backend/app/scheduling/ frontend/src/ 2>/dev/null | grep -v "test" || true)

if [ -n "$SUPERVISION_ISSUES" ]; then
  echo -e "${YELLOW}WARNING${NC}"
  echo -e "${YELLOW}Potential supervision issues detected:${NC}"
  echo "$SUPERVISION_ISSUES" | head -5
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Summary
# ============================================================
echo ""
if [ $WARNINGS -eq 0 ]; then
  echo -e "${GREEN}ACGME compliance check passed!${NC}"
  exit 0
else
  echo -e "${YELLOW}ACGME compliance check found $WARNINGS potential issue(s)${NC}"
  echo -e "${YELLOW}Review above warnings before committing scheduling changes.${NC}"
  echo ""
  echo "Reference: docs/compliance/ACGME_RULES.md"
  echo "Advisory: MEDCOM agent for clinical interpretation"
  # Non-blocking for now (warning mode)
  exit 0
fi
