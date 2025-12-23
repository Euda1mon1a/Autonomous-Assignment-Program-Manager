#!/bin/bash
# PII/OPSEC/PERSEC Pre-commit Scanner
# Runs locally before commits to catch potential data leakage
# Part of layered defense (pre-commit -> GitHub Actions -> periodic audit)

set -e

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

ERRORS=0

echo "Running PII/OPSEC/PERSEC scan..."

# Check for SSN patterns (most critical - fails commit)
echo -n "Checking for SSN patterns... "
SSNS=$(grep -rn --include="*.py" --include="*.ts" --include="*.tsx" --include="*.json" \
  -E '\b\d{3}-\d{2}-\d{4}\b' \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=venv \
  --exclude-dir=__pycache__ --exclude-dir=htmlcov \
  . 2>/dev/null || true)

if [ -n "$SSNS" ]; then
  echo -e "${RED}FOUND${NC}"
  echo -e "${RED}ERROR: Potential SSN patterns detected!${NC}"
  echo "$SSNS" | head -10
  ERRORS=1
else
  echo -e "${GREEN}OK${NC}"
fi

# Check for real-looking .mil emails (warning - doesn't fail commit)
echo -n "Checking for .mil email addresses... "
MIL=$(grep -rn --include="*.py" --include="*.ts" --include="*.json" \
  -E '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.mil\b' \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=venv \
  --exclude-dir=__pycache__ \
  . 2>/dev/null | \
  grep -viE '(example|test|fake|dummy|sample|hospital\.mil|@test\.mil|noreply)' || true)

if [ -n "$MIL" ]; then
  echo -e "${YELLOW}WARNING${NC}"
  echo -e "${YELLOW}Review these .mil addresses (may be mock data):${NC}"
  echo "$MIL" | head -5
  # Don't fail on .mil - too many false positives from mock data
else
  echo -e "${GREEN}OK${NC}"
fi

# Check for tracked data files that shouldn't be committed
echo -n "Checking for staged data files... "
STAGED_DATA=$(git diff --cached --name-only 2>/dev/null | grep -E '\.(csv|dump|sql)$' | grep -v 'alembic' || true)

if [ -n "$STAGED_DATA" ]; then
  echo -e "${RED}FOUND${NC}"
  echo -e "${RED}ERROR: Data files staged for commit:${NC}"
  echo "$STAGED_DATA"
  ERRORS=1
else
  echo -e "${GREEN}OK${NC}"
fi

# Check for .env files being staged
echo -n "Checking for .env files... "
STAGED_ENV=$(git diff --cached --name-only 2>/dev/null | grep -E '\.env$|\.env\.' | grep -v '.example' || true)

if [ -n "$STAGED_ENV" ]; then
  echo -e "${RED}FOUND${NC}"
  echo -e "${RED}ERROR: Environment files staged for commit:${NC}"
  echo "$STAGED_ENV"
  ERRORS=1
else
  echo -e "${GREEN}OK${NC}"
fi

# Summary
echo ""
if [ $ERRORS -eq 0 ]; then
  echo -e "${GREEN}PII scan passed!${NC}"
  exit 0
else
  echo -e "${RED}PII scan failed - please review and fix before committing${NC}"
  echo "Reference: docs/security/PII_AUDIT_LOG.md"
  exit 1
fi
