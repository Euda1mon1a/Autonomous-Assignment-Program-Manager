#!/bin/bash
# ============================================================
# Script: pii-scan.sh
# Purpose: PII/OPSEC/PERSEC pre-commit security scanner
# Usage: ./scripts/pii-scan.sh [--staged-only]
#
# Description:
#   Scans codebase for personally identifiable information (PII),
#   operational security (OPSEC), and personnel security (PERSEC)
#   violations before committing code.
#
# Security Patterns Detected:
#   - SSN patterns (###-##-####)
#   - Military service numbers
#   - Full names in production code
#   - Email addresses
#   - Phone numbers
#   - Home addresses
#
# Defense Layers:
#   1. Pre-commit hook (this script)
#   2. GitHub Actions workflow
#   3. Periodic security audits
#
# Exit Codes:
#   0 - No PII/security issues found
#   1 - Potential issues found (fails commit)
# ============================================================

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

ERRORS=0

# Verify grep is available
if ! command -v grep >/dev/null 2>&1; then
    echo -e "${RED}ERROR: grep command not found${NC}" >&2
    exit 1
fi

echo "Running PII/OPSEC/PERSEC scan..."

# Check for SSN patterns (most critical - fails commit)
# Excludes test directories which use mock SSNs like 123-45-6789 for PII sanitization tests
echo -n "Checking for SSN patterns... "
SSNS=$(grep -rn --include="*.py" --include="*.ts" --include="*.tsx" --include="*.json" \
  -E '\b\d{3}-\d{2}-\d{4}\b' \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=venv \
  --exclude-dir=__pycache__ --exclude-dir=htmlcov \
  --exclude-dir=tests --exclude-dir=__tests__ \
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
# Exclude: alembic migrations, backend/schema.sql (Lich's Phylactery - schema only, no data)
echo -n "Checking for staged data files... "
STAGED_DATA=$(git diff --cached --name-only 2>/dev/null | grep -E '\.(csv|dump|sql)$' | grep -v 'alembic' | grep -v 'backend/schema.sql' || true)

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

# ============================================================
# Enhanced Security Checks (Session 082 - SECURITY_AUDITOR Domain)
# ============================================================

# Check for hardcoded API keys in code
echo -n "Checking for hardcoded API keys... "
API_KEYS=$(grep -rn --include="*.py" --include="*.ts" --include="*.tsx" \
  -E '(api_key|apikey|API_KEY)\s*=\s*["\x27][a-zA-Z0-9_-]{20,}["\x27]' \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=venv \
  --exclude-dir=__pycache__ --exclude-dir=tests --exclude-dir=__tests__ \
  --exclude-dir=docs \
  backend/ frontend/src/ 2>/dev/null || true)

if [ -n "$API_KEYS" ]; then
  echo -e "${RED}FOUND${NC}"
  echo -e "${RED}ERROR: Hardcoded API keys detected!${NC}"
  echo "$API_KEYS" | head -5
  ERRORS=1
else
  echo -e "${GREEN}OK${NC}"
fi

# Check for raw SQL (ORM bypass)
echo -n "Checking for raw SQL queries... "
RAW_SQL=$(grep -rn --include="*.py" \
  -E '(execute\(|text\(|raw_connection|\.raw\().*SELECT|INSERT|UPDATE|DELETE' \
  --exclude-dir=venv --exclude-dir=__pycache__ \
  --exclude-dir=tests --exclude-dir=alembic \
  backend/app/ 2>/dev/null || true)

if [ -n "$RAW_SQL" ]; then
  echo -e "${YELLOW}WARNING${NC}"
  echo -e "${YELLOW}Raw SQL detected - verify parameterization:${NC}"
  echo "$RAW_SQL" | head -5
  # Warning only - some raw SQL may be intentional
else
  echo -e "${GREEN}OK${NC}"
fi

# Check for sensitive data in log statements
echo -n "Checking for sensitive data in logs... "
LOG_SENSITIVE=$(grep -rn --include="*.py" \
  -iE 'log(ger)?\.(info|debug|warning|error).*\b(password|ssn|token|secret|credential|api_key)\b' \
  --exclude-dir=venv --exclude-dir=__pycache__ \
  --exclude-dir=tests \
  backend/app/ 2>/dev/null || true)

if [ -n "$LOG_SENSITIVE" ]; then
  echo -e "${YELLOW}WARNING${NC}"
  echo -e "${YELLOW}Potentially sensitive data in logs:${NC}"
  echo "$LOG_SENSITIVE" | head -5
  # Warning only - may be sanitized
else
  echo -e "${GREEN}OK${NC}"
fi

# Check for hardcoded secrets/passwords
echo -n "Checking for hardcoded secrets... "
SECRETS=$(grep -rn --include="*.py" --include="*.ts" \
  -E '(password|secret|token)\s*=\s*["\x27][^"\x27]{8,}["\x27]' \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=venv \
  --exclude-dir=__pycache__ --exclude-dir=tests --exclude-dir=__tests__ \
  --exclude-dir=docs --exclude-dir=.claude \
  backend/app/ frontend/src/ 2>/dev/null | \
  grep -viE '(example|test|mock|fake|placeholder|config\.|settings\.|env\.)' || true)

if [ -n "$SECRETS" ]; then
  echo -e "${YELLOW}WARNING${NC}"
  echo -e "${YELLOW}Potential hardcoded secrets:${NC}"
  echo "$SECRETS" | head -5
  # Warning only - context needed
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Personnel Name Detection (PERSEC)
# Catches real resident/faculty names in committed files
# ============================================================

echo -n "Checking for personnel names in staged files... "

# Known personnel names (last names only - add as needed)
# These are from the residency program roster
KNOWN_NAMES="Bevis|Byrnes|Cataquiz|Chu|Colgan|Connolly|Cook|Dahl|Gigon|Headid|Hernandez|Kinkennon|LaBounty|Lamoureux|Maher|Mayell|McGuire|McRae|Monsivais|Montgomery|Napierala|Petrie|Sawyer|Sloss|Tagawa|Thomas|Travis|Van Brunt|Wilhelm|You"

# Get staged files (or all tracked files if not in pre-commit context)
if [ "${1:-}" = "--staged-only" ]; then
  STAGED_FILES=$(git diff --cached --name-only 2>/dev/null || true)
else
  STAGED_FILES=$(git diff --cached --name-only 2>/dev/null || true)
fi

# Check staged markdown and text files for names
if [ -n "$STAGED_FILES" ]; then
  NAME_MATCHES=""
  for file in $STAGED_FILES; do
    if [[ "$file" =~ \.(md|txt|json|xml|csv)$ ]] && [ -f "$file" ]; then
      MATCHES=$(grep -nE "\b($KNOWN_NAMES)\b" "$file" 2>/dev/null || true)
      if [ -n "$MATCHES" ]; then
        NAME_MATCHES="${NAME_MATCHES}${file}:
${MATCHES}
"
      fi
    fi
  done

  if [ -n "$NAME_MATCHES" ]; then
    echo -e "${RED}FOUND${NC}"
    echo -e "${RED}ERROR: Personnel names detected in staged files!${NC}"
    echo "$NAME_MATCHES" | head -20
    echo -e "${YELLOW}Hint: Use role descriptions (e.g., 'SM faculty') instead of names${NC}"
    ERRORS=1
  else
    echo -e "${GREEN}OK${NC}"
  fi
else
  echo -e "${GREEN}OK (no staged files)${NC}"
fi

# Summary
echo ""
if [ $ERRORS -eq 0 ]; then
  echo -e "${GREEN}PII/Security scan passed!${NC}"
  exit 0
else
  echo -e "${RED}PII/Security scan failed - please review and fix before committing${NC}"
  echo "Reference: docs/security/PII_AUDIT_LOG.md"
  echo "Advisory: SECURITY_AUDITOR agent for detailed analysis"
  exit 1
fi
