#!/bin/bash
# ============================================================
# Script: validate-documentation.sh
# Purpose: Pre-commit hook for documentation completeness
# Domain: META_UPDATER Advisory
# Session: 082
#
# Documentation Rules Checked:
#   - CHANGELOG.md updated for feature/fix commits
#   - Session documentation for significant changes
#   - API docstrings for new endpoints
#   - README updates for new features
#
# Philosophy (Auftragstaktik):
#   Documentation is how knowledge persists across sessions.
#   Undocumented features are lost features.
#
# Exit Codes:
#   0 - Validation passed
#   1 - Documentation gaps detected (warning mode)
# ============================================================

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

WARNINGS=0

echo -e "${CYAN}Running Documentation Completeness Check...${NC}"

# Get staged files
STAGED_FILES=$(git diff --cached --name-only 2>/dev/null || echo "")

if [ -z "$STAGED_FILES" ]; then
  echo -e "${GREEN}No staged files - skipping documentation check${NC}"
  exit 0
fi

# ============================================================
# Check 1: CHANGELOG for feature/fix commits
# ============================================================
echo -n "Checking CHANGELOG.md updates... "

# Count significant code changes
CODE_CHANGES=$(echo "$STAGED_FILES" | grep -cE '\.(py|ts|tsx)$' || echo "0")
CHANGELOG_UPDATED=$(echo "$STAGED_FILES" | grep -c "CHANGELOG.md" || echo "0")

if [ "$CODE_CHANGES" -gt 5 ] && [ "$CHANGELOG_UPDATED" -eq 0 ]; then
  echo -e "${YELLOW}WARNING${NC}"
  echo -e "${YELLOW}$CODE_CHANGES code files changed but CHANGELOG.md not updated${NC}"
  echo "Consider updating CHANGELOG.md for significant changes"
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 2: Session documentation for significant changes
# ============================================================
echo -n "Checking session documentation... "

# Check if session doc exists for today's changes
SESSION_DOC=$(echo "$STAGED_FILES" | grep -E 'SESSION_[0-9]+.*\.md$' || echo "")

if [ "$CODE_CHANGES" -gt 10 ] && [ -z "$SESSION_DOC" ]; then
  echo -e "${YELLOW}INFO${NC}"
  echo -e "${YELLOW}Large change set ($CODE_CHANGES files) - consider session documentation${NC}"
  # Info only - not all changes need session docs
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 3: New API endpoints have docstrings
# ============================================================
echo -n "Checking API endpoint documentation... "

# Look for new route definitions
NEW_ROUTES=$(echo "$STAGED_FILES" | grep -E 'backend/app/api/routes/.*\.py$' || echo "")

if [ -n "$NEW_ROUTES" ]; then
  # Check if routes have docstrings
  UNDOCUMENTED=$(for route in $NEW_ROUTES; do
    if [ -f "$route" ]; then
      # Look for @router definitions without docstrings
      grep -l '@router\.' "$route" 2>/dev/null | while read f; do
        if ! grep -q '"""' "$f" 2>/dev/null; then
          echo "$f"
        fi
      done
    fi
  done | head -3)

  if [ -n "$UNDOCUMENTED" ]; then
    echo -e "${YELLOW}INFO${NC}"
    echo -e "${YELLOW}New routes may need docstrings:${NC}"
    echo "$UNDOCUMENTED"
  else
    echo -e "${GREEN}OK${NC}"
  fi
else
  echo -e "${GREEN}OK${NC} (no new routes)"
fi

# ============================================================
# Check 4: New skills have prompt.md
# ============================================================
echo -n "Checking skill documentation... "

NEW_SKILLS=$(echo "$STAGED_FILES" | grep -E '\.claude/skills/[^/]+/' | \
  sed 's|\.claude/skills/\([^/]*\)/.*|\1|' | sort -u || echo "")

if [ -n "$NEW_SKILLS" ]; then
  MISSING_PROMPT=""
  for skill in $NEW_SKILLS; do
    if [ ! -f ".claude/skills/$skill/prompt.md" ]; then
      MISSING_PROMPT="$MISSING_PROMPT $skill"
    fi
  done

  if [ -n "$MISSING_PROMPT" ]; then
    echo -e "${YELLOW}WARNING${NC}"
    echo -e "${YELLOW}Skills missing prompt.md:$MISSING_PROMPT${NC}"
    WARNINGS=$((WARNINGS + 1))
  else
    echo -e "${GREEN}OK${NC}"
  fi
else
  echo -e "${GREEN}OK${NC} (no new skills)"
fi

# ============================================================
# Check 5: New hooks have README entry
# ============================================================
echo -n "Checking hook documentation... "

NEW_HOOKS=$(echo "$STAGED_FILES" | grep -E '\.claude/hooks/.*\.sh$' || echo "")
README_UPDATED=$(echo "$STAGED_FILES" | grep -c "\.claude/hooks/README.md" || echo "0")

if [ -n "$NEW_HOOKS" ] && [ "$README_UPDATED" -eq 0 ]; then
  echo -e "${YELLOW}INFO${NC}"
  echo -e "${YELLOW}New hooks added - consider updating .claude/hooks/README.md${NC}"
  # Info only
else
  echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 6: Migration documentation
# ============================================================
echo -n "Checking migration documentation... "

NEW_MIGRATIONS=$(echo "$STAGED_FILES" | grep -E 'alembic/versions/.*\.py$' || echo "")

if [ -n "$NEW_MIGRATIONS" ]; then
  # Check if migration has docstring
  UNDOC_MIGRATION=""
  for mig in $NEW_MIGRATIONS; do
    if [ -f "$mig" ]; then
      if ! head -20 "$mig" | grep -q '"""'; then
        UNDOC_MIGRATION="$UNDOC_MIGRATION $mig"
      fi
    fi
  done

  if [ -n "$UNDOC_MIGRATION" ]; then
    echo -e "${YELLOW}WARNING${NC}"
    echo -e "${YELLOW}Migrations may lack docstrings:$UNDOC_MIGRATION${NC}"
    WARNINGS=$((WARNINGS + 1))
  else
    echo -e "${GREEN}OK${NC}"
  fi
else
  echo -e "${GREEN}OK${NC} (no new migrations)"
fi

# ============================================================
# Summary
# ============================================================
echo ""
if [ $WARNINGS -eq 0 ]; then
  echo -e "${GREEN}Documentation completeness check passed!${NC}"
  exit 0
else
  echo -e "${YELLOW}Documentation check found $WARNINGS potential gap(s)${NC}"
  echo -e "${YELLOW}Consider updating documentation before committing.${NC}"
  echo ""
  echo "Reference: docs/development/DOCUMENTATION_STANDARDS.md"
  echo "Advisory: META_UPDATER agent for documentation patterns"
  # Non-blocking for now (warning mode)
  exit 0
fi
