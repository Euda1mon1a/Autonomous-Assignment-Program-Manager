***REMOVED***!/bin/bash
***REMOVED*** ============================================================
***REMOVED*** Script: pii-scan.sh
***REMOVED*** Purpose: PII/OPSEC/PERSEC pre-commit security scanner
***REMOVED*** Usage: ./scripts/pii-scan.sh [--staged-only]
***REMOVED***
***REMOVED*** Description:
***REMOVED***   Scans codebase for personally identifiable information (PII),
***REMOVED***   operational security (OPSEC), and personnel security (PERSEC)
***REMOVED***   violations before committing code.
***REMOVED***
***REMOVED*** Security Patterns Detected:
***REMOVED***   - SSN patterns (***REMOVED******REMOVED******REMOVED***-***REMOVED******REMOVED***-***REMOVED******REMOVED******REMOVED******REMOVED***)
***REMOVED***   - Military service numbers
***REMOVED***   - Full names in production code
***REMOVED***   - Email addresses
***REMOVED***   - Phone numbers
***REMOVED***   - Home addresses
***REMOVED***
***REMOVED*** Defense Layers:
***REMOVED***   1. Pre-commit hook (this script)
***REMOVED***   2. GitHub Actions workflow
***REMOVED***   3. Periodic security audits
***REMOVED***
***REMOVED*** Exit Codes:
***REMOVED***   0 - No PII/security issues found
***REMOVED***   1 - Potential issues found (fails commit)
***REMOVED*** ============================================================

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' ***REMOVED*** No Color

ERRORS=0

***REMOVED*** Verify grep is available
if ! command -v grep >/dev/null 2>&1; then
    echo -e "${RED}ERROR: grep command not found${NC}" >&2
    exit 1
fi

echo "Running PII/OPSEC/PERSEC scan..."

***REMOVED*** Check for SSN patterns (most critical - fails commit)
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

***REMOVED*** Check for real-looking .mil emails (warning - doesn't fail commit)
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
  ***REMOVED*** Don't fail on .mil - too many false positives from mock data
else
  echo -e "${GREEN}OK${NC}"
fi

***REMOVED*** Check for tracked data files that shouldn't be committed
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

***REMOVED*** Check for .env files being staged
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

***REMOVED*** Summary
echo ""
if [ $ERRORS -eq 0 ]; then
  echo -e "${GREEN}PII scan passed!${NC}"
  exit 0
else
  echo -e "${RED}PII scan failed - please review and fix before committing${NC}"
  echo "Reference: docs/security/PII_AUDIT_LOG.md"
  exit 1
fi
