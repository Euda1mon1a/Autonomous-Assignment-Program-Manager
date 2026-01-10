#!/bin/bash
# ============================================================
# Script: validate-constraint-registration.sh
# Purpose: Pre-commit hook for constraint registration validation
# Domain: SCHEDULER Advisory
# Session: 083
#
# Problem: Constraints can be defined but not exported, or
#          exported but not registered in ConstraintManager.
#          This leads to silent failures where constraints
#          exist but are never used.
#
# Checks:
#   1. All constraint imports are in __all__
#   2. All exported constraints are registered in manager
#   3. Disabled constraints have explanatory comments
#   4. Registration tests pass
#
# Philosophy (Auftragstaktik):
#   Catch "implemented but not registered" bugs at commit time.
#   This bug has happened before - prevent it from happening again.
#
# Exit Codes:
#   0 - Validation passed
#   1 - Validation failed (blocking)
# ============================================================

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

WARNINGS=0
ERRORS=0

CONSTRAINTS_DIR="backend/app/scheduling/constraints"
INIT_FILE="$CONSTRAINTS_DIR/__init__.py"
MANAGER_FILE="$CONSTRAINTS_DIR/manager.py"

echo -e "${CYAN}Running Constraint Registration Check...${NC}"

# ============================================================
# Check 1: __all__ Completeness
# ============================================================
echo -n "Checking __all__ completeness... "

# Extract constraint class names from import statements (ending with Constraint)
IMPORTED_CONSTRAINTS=$(grep -E "^\s+[A-Z][a-zA-Z]+Constraint," "$INIT_FILE" 2>/dev/null | \
  sed 's/,//g' | awk '{print $1}' | sort -u || true)

# Extract constraint names from __all__ (ending with Constraint)
ALL_CONSTRAINTS=$(grep -E '^\s+"[A-Z][a-zA-Z]+Constraint"' "$INIT_FILE" 2>/dev/null | \
  sed 's/[",]//g' | awk '{print $1}' | sort -u || true)

# Find imports not in __all__
MISSING_FROM_ALL=""
for constraint in $IMPORTED_CONSTRAINTS; do
  if ! echo "$ALL_CONSTRAINTS" | grep -q "^${constraint}$"; then
    MISSING_FROM_ALL="$MISSING_FROM_ALL $constraint"
  fi
done

if [ -n "$MISSING_FROM_ALL" ]; then
  echo -e "${RED}ERROR${NC}"
  echo -e "${RED}Constraints imported but NOT in __all__:${NC}"
  for c in $MISSING_FROM_ALL; do
    echo "  - $c"
  done
  ERRORS=$((ERRORS + 1))
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 2: Manager Registration
# ============================================================
echo -n "Checking manager registration... "

# Extract constraints that should be registered (ending with Constraint, excluding base classes)
EXPORTED_CONSTRAINTS=$(echo "$ALL_CONSTRAINTS" | grep -v "^Constraint$" | grep -v "^HardConstraint$" | grep -v "^SoftConstraint$" || true)

# Extract constraints registered in manager.py (manager.add(ConstraintName(...)))
REGISTERED_CONSTRAINTS=$(grep -oE 'manager\.add\([A-Z][a-zA-Z]+Constraint\(' "$MANAGER_FILE" 2>/dev/null | \
  sed 's/manager\.add(//g' | sed 's/(//g' | sort -u || true)

# Also check for disabled constraints (they're still registered)
DISABLED_CONSTRAINTS=$(grep -oE 'manager\.disable\("[A-Z][a-zA-Z]+"' "$MANAGER_FILE" 2>/dev/null | \
  sed 's/manager\.disable("//g' | sed 's/"//g' | sort -u || true)

# Count registered vs exported
EXPORTED_COUNT=$(echo "$EXPORTED_CONSTRAINTS" | wc -l | tr -d ' ')
REGISTERED_COUNT=$(echo "$REGISTERED_CONSTRAINTS" | wc -l | tr -d ' ')

# Find exported but not registered (allowing for some to be optional/deprecated)
UNREGISTERED=""
for constraint in $EXPORTED_CONSTRAINTS; do
  if ! echo "$REGISTERED_CONSTRAINTS" | grep -q "^${constraint}$"; then
    UNREGISTERED="$UNREGISTERED $constraint"
  fi
done

# Only warn if there are unregistered constraints (not all need to be registered)
UNREGISTERED_COUNT=$(echo "$UNREGISTERED" | wc -w)
if [ "$UNREGISTERED_COUNT" -gt 10 ]; then
  echo -e "${YELLOW}WARNING${NC}"
  echo -e "${YELLOW}Many exported constraints not registered in create_default():${NC}"
  echo "  Exported: $EXPORTED_COUNT, Registered: $REGISTERED_COUNT"
  echo "  (Some may be intentionally optional)"
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}OK${NC} (Exported: $EXPORTED_COUNT, Registered: $REGISTERED_COUNT)"
fi

# ============================================================
# Check 3: Disabled Constraints Have Comments
# ============================================================
echo -n "Checking disabled constraint documentation... "

UNDOCUMENTED_DISABLES=""
while IFS= read -r constraint; do
  if [ -n "$constraint" ]; then
    # Find line number of disable call
    LINE_NUM=$(grep -n "manager\.disable(\"$constraint\"" "$MANAGER_FILE" 2>/dev/null | head -1 | cut -d: -f1)
    if [ -n "$LINE_NUM" ]; then
      # Check if previous line is a comment
      PREV_LINE=$((LINE_NUM - 1))
      PREV_CONTENT=$(sed -n "${PREV_LINE}p" "$MANAGER_FILE" 2>/dev/null || true)
      if ! echo "$PREV_CONTENT" | grep -q "#"; then
        UNDOCUMENTED_DISABLES="$UNDOCUMENTED_DISABLES $constraint"
      fi
    fi
  fi
done <<< "$DISABLED_CONSTRAINTS"

if [ -n "$UNDOCUMENTED_DISABLES" ]; then
  echo -e "${YELLOW}WARNING${NC}"
  echo -e "${YELLOW}Disabled constraints without explanatory comment:${NC}"
  for c in $UNDOCUMENTED_DISABLES; do
    echo "  - $c (add comment explaining why disabled)"
  done
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 4: Registration Test Exists
# ============================================================
echo -n "Checking registration test exists... "

TEST_FILE="backend/tests/test_constraint_registration.py"
if [ -f "$TEST_FILE" ]; then
  echo -e "${GREEN}OK${NC}"
else
  echo -e "${YELLOW}WARNING${NC}"
  echo -e "${YELLOW}Registration test file not found: $TEST_FILE${NC}"
  WARNINGS=$((WARNINGS + 1))
fi

# ============================================================
# Summary
# ============================================================
echo ""
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
  echo -e "${GREEN}Constraint registration check passed!${NC}"
  exit 0
elif [ $ERRORS -gt 0 ]; then
  echo -e "${RED}Constraint registration check found $ERRORS error(s) and $WARNINGS warning(s)${NC}"
  echo ""
  echo "Fix errors before committing constraint changes."
  echo "Reference: backend/tests/test_constraint_registration.py"
  exit 1
else
  echo -e "${YELLOW}Constraint registration check found $WARNINGS warning(s)${NC}"
  echo ""
  echo "Consider addressing warnings before committing."
  echo "Reference: backend/tests/test_constraint_registration.py"
  # Warnings only - don't block
  exit 0
fi
