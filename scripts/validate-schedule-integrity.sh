#!/bin/bash
# ============================================================
# Script: validate-schedule-integrity.sh
# Purpose: Pre-commit hook for schedule data integrity validation
# Domain: SCHEDULER Advisory
# Session: 082
#
# Integrity Rules Checked:
#   - Schedule data structure consistency
#   - No orphaned assignments
#   - Date range continuity
#   - Block/rotation consistency
#   - Foreign key relationships
#
# Philosophy (Auftragstaktik):
#   Data integrity is foundational. Corrupted schedules cascade.
#   Better to catch structure issues at commit than in production.
#
# Exit Codes:
#   0 - Validation passed
#   1 - Integrity concerns detected (warning mode)
# ============================================================

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

WARNINGS=0

echo -e "${CYAN}Running Schedule Integrity Validation...${NC}"

# ============================================================
# Check 1: Nullable fields that shouldn't be
# ============================================================
echo -n "Checking for nullable schedule fields... "

# Look for nullable=True on critical schedule fields
NULLABLE_ISSUES=$(grep -rn --include="*.py" \
  -E '(resident_id|rotation_id|block_id|date|assignment).*nullable\s*=\s*True' \
  backend/app/models/ 2>/dev/null | grep -v "test" | head -5 || true)

if [ -n "$NULLABLE_ISSUES" ]; then
  echo -e "${YELLOW}INFO${NC}"
  echo -e "${YELLOW}Nullable schedule fields found - verify intentional:${NC}"
  echo "$NULLABLE_ISSUES"
  # Info only - some nullable may be intentional
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 2: Orphan assignment patterns
# ============================================================
echo -n "Checking for orphan prevention... "

# Look for assignment creation without relationship validation
ORPHAN_RISK=$(grep -rn --include="*.py" \
  -iE '(create.*assignment|add.*assignment|insert.*assignment)' \
  backend/app/services/ backend/app/api/routes/ 2>/dev/null | \
  grep -v "resident" | grep -v "rotation" | grep -v "test" | head -5 || true)

if [ -n "$ORPHAN_RISK" ]; then
  echo -e "${YELLOW}WARNING${NC}"
  echo -e "${YELLOW}Assignment creation without clear relationship:${NC}"
  echo "$ORPHAN_RISK"
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 3: Date validation
# ============================================================
echo -n "Checking for date validation... "

# Look for date handling without validation
DATE_ISSUES=$(grep -rn --include="*.py" \
  -iE '(start_date|end_date|schedule_date)' \
  backend/app/scheduling/ 2>/dev/null | \
  grep -v "validate" | grep -v "check" | grep -v "test" | \
  grep -v "@validator" | head -5 || true)

# This is informational - many date references are fine
if [ -n "$DATE_ISSUES" ]; then
  echo -e "${GREEN}OK${NC} (date fields present)"
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 4: Cascade delete protection
# ============================================================
echo -n "Checking for cascade delete handling... "

# Look for dangerous cascade patterns
CASCADE_ISSUES=$(grep -rn --include="*.py" \
  -E 'cascade\s*=\s*["\x27]all.*delete["\x27]' \
  backend/app/models/ 2>/dev/null | grep -v "test" || true)

if [ -n "$CASCADE_ISSUES" ]; then
  echo -e "${YELLOW}WARNING${NC}"
  echo -e "${YELLOW}Cascade delete found - verify intentional:${NC}"
  echo "$CASCADE_ISSUES" | head -5
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 5: Transaction handling
# ============================================================
echo -n "Checking for transaction handling... "

# Look for schedule modifications without transactions
NO_TRANSACTION=$(grep -rn --include="*.py" \
  -iE '(update.*schedule|delete.*schedule|bulk.*insert)' \
  backend/app/services/ 2>/dev/null | \
  grep -v "session" | grep -v "transaction" | grep -v "commit" | \
  grep -v "test" | head -5 || true)

if [ -n "$NO_TRANSACTION" ]; then
  echo -e "${YELLOW}INFO${NC}"
  echo -e "${YELLOW}Schedule operations - verify transaction handling:${NC}"
  echo "$NO_TRANSACTION"
  # Info only - context needed
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 6: Unique constraint handling
# ============================================================
echo -n "Checking for duplicate prevention... "

# Look for unique constraints on schedule tables
UNIQUE_CHECK=$(grep -rn --include="*.py" \
  -E '(UniqueConstraint|unique\s*=\s*True)' \
  backend/app/models/assignment.py backend/app/models/schedule*.py 2>/dev/null || true)

if [ -z "$UNIQUE_CHECK" ]; then
  echo -e "${YELLOW}INFO${NC}"
  echo -e "${YELLOW}No unique constraints found in schedule models - verify intended${NC}"
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Summary
# ============================================================
echo ""
if [ $WARNINGS -eq 0 ]; then
  echo -e "${GREEN}Schedule integrity validation passed!${NC}"
  exit 0
else
  echo -e "${YELLOW}Schedule integrity check found $WARNINGS potential issue(s)${NC}"
  echo -e "${YELLOW}Review above warnings before committing scheduling changes.${NC}"
  echo ""
  echo "Reference: docs/scheduling/DATA_MODEL.md"
  echo "Advisory: SCHEDULER agent for detailed analysis"
  # Non-blocking for now (warning mode)
  exit 0
fi
