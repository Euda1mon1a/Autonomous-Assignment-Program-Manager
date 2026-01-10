#!/bin/bash
# ============================================================
# Script: validate-dependency-versions.sh
# Purpose: Pre-commit hook for dependency version protection
# Domain: ARCHITECT Advisory
# Session: 085
#
# Problem: "Getting Dependabot'd" - automatic or careless
#          dependency upgrades break production. This hook
#          catches version drift before commit.
#
# Checks:
#   1. Lock file freshness (package-lock vs package.json)
#   2. Major version bump detection
#   3. Critical dependency changes (blocking)
#   4. Version format drift (exact → range)
#
# Philosophy (Auftragstaktik):
#   Block dangerous changes, warn on risky ones, inform on
#   format drift. Override with DEP_ALLOW=1 for intentional
#   upgrades.
#
# Exit Codes:
#   0 - Validation passed (warnings allowed)
#   1 - Critical dependency changed without DEP_ALLOW=1
# ============================================================

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

WARNINGS=0
ERRORS=0
CRITICAL_CHANGES=""

# Critical dependencies that block without DEP_ALLOW=1
FRONTEND_CRITICAL="next react react-dom @tanstack/react-query"
BACKEND_CRITICAL="fastapi sqlalchemy pydantic pydantic-settings python-jose passlib bcrypt alembic"

echo -e "${CYAN}Running Dependency Version Guard...${NC}"

# ============================================================
# Check 0: Are dependency files staged?
# ============================================================
PKG_JSON_STAGED=$(git diff --cached --name-only 2>/dev/null | grep -E "^frontend/package\.json$" || true)
PKG_LOCK_STAGED=$(git diff --cached --name-only 2>/dev/null | grep -E "^frontend/package-lock\.json$" || true)
REQUIREMENTS_STAGED=$(git diff --cached --name-only 2>/dev/null | grep -E "^backend/requirements\.txt$" || true)

if [ -z "$PKG_JSON_STAGED" ] && [ -z "$PKG_LOCK_STAGED" ] && [ -z "$REQUIREMENTS_STAGED" ]; then
    echo -e "${GREEN}No dependency files staged.${NC}"
    exit 0
fi

# ============================================================
# Check 1: Lock File Freshness
# ============================================================
echo -n "Checking lock file freshness... "

if [ -n "$PKG_JSON_STAGED" ] && [ -z "$PKG_LOCK_STAGED" ]; then
    echo -e "${YELLOW}WARNING${NC}"
    echo -e "${YELLOW}package.json changed but package-lock.json not staged.${NC}"
    echo -e "Run: ${CYAN}cd frontend && npm install${NC}"
    echo ""
    WARNINGS=$((WARNINGS + 1))
elif [ -n "$PKG_JSON_STAGED" ] && [ -n "$PKG_LOCK_STAGED" ]; then
    echo -e "${GREEN}OK${NC} (both package.json and lock file updated)"
elif [ -z "$PKG_JSON_STAGED" ] && [ -n "$PKG_LOCK_STAGED" ]; then
    echo -e "${BLUE}INFO${NC} (lock file only - likely npm install)"
else
    echo -e "${GREEN}OK${NC}"
fi

# ============================================================
# Check 2: Frontend Major Version Bumps
# ============================================================
if [ -n "$PKG_JSON_STAGED" ]; then
    echo -n "Checking frontend version changes... "

    # Get old and new versions of package.json
    OLD_PKG=$(git show HEAD:frontend/package.json 2>/dev/null || echo "{}")
    NEW_PKG=$(git show :frontend/package.json 2>/dev/null || echo "{}")

    MAJOR_BUMPS=""

    # Extract dependencies and compare major versions
    # This is a simplified check - looks for version patterns
    while IFS= read -r line; do
        # Extract package name and version from lines like: "react": "^18.2.0"
        if [[ $line =~ \"([^\"]+)\":[[:space:]]*\"[\^~]?([0-9]+)\. ]]; then
            PKG_NAME="${BASH_REMATCH[1]}"
            NEW_MAJOR="${BASH_REMATCH[2]}"

            # Get old major version
            OLD_LINE=$(echo "$OLD_PKG" | grep "\"$PKG_NAME\":" | head -1 || true)
            if [[ $OLD_LINE =~ \"[\^~]?([0-9]+)\. ]]; then
                OLD_MAJOR="${BASH_REMATCH[1]}"
                if [ "$OLD_MAJOR" != "$NEW_MAJOR" ] && [ -n "$OLD_MAJOR" ]; then
                    MAJOR_BUMPS="$MAJOR_BUMPS\n  $PKG_NAME: $OLD_MAJOR.x → $NEW_MAJOR.x"

                    # Check if critical
                    if echo "$FRONTEND_CRITICAL" | grep -qw "$PKG_NAME"; then
                        CRITICAL_CHANGES="$CRITICAL_CHANGES\n  $PKG_NAME: $OLD_MAJOR.x → $NEW_MAJOR.x (frontend)"
                    fi
                fi
            fi
        fi
    done < <(echo "$NEW_PKG" | grep -E '"[^"]+"\s*:\s*"[\^~]?[0-9]+\.' || true)

    if [ -n "$MAJOR_BUMPS" ]; then
        echo -e "${YELLOW}WARNING${NC}"
        echo -e "${YELLOW}Major version bumps detected:${NC}"
        echo -e "$MAJOR_BUMPS"
        echo ""
        echo -e "Review changelogs before committing."
        echo ""
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${GREEN}OK${NC}"
    fi

    # Check for critical dependency ANY version change
    echo -n "Checking critical frontend deps... "
    FRONTEND_CRITICAL_CHANGED=""

    for dep in $FRONTEND_CRITICAL; do
        OLD_VER=$(echo "$OLD_PKG" | grep -E "\"$dep\":" | grep -oE '": "[^"]+"' | grep -oE '[0-9][^"]*' | head -1 || true)
        NEW_VER=$(echo "$NEW_PKG" | grep -E "\"$dep\":" | grep -oE '": "[^"]+"' | grep -oE '[0-9][^"]*' | head -1 || true)

        if [ -n "$OLD_VER" ] && [ -n "$NEW_VER" ] && [ "$OLD_VER" != "$NEW_VER" ]; then
            FRONTEND_CRITICAL_CHANGED="$FRONTEND_CRITICAL_CHANGED\n  $dep: $OLD_VER → $NEW_VER"
            CRITICAL_CHANGES="$CRITICAL_CHANGES\n  $dep: $OLD_VER → $NEW_VER"
        fi
    done

    if [ -n "$FRONTEND_CRITICAL_CHANGED" ]; then
        echo -e "${RED}CRITICAL${NC}"
        echo -e "${RED}Critical frontend dependencies changed:${NC}"
        echo -e "$FRONTEND_CRITICAL_CHANGED"
        echo ""
    else
        echo -e "${GREEN}OK${NC}"
    fi
fi

# ============================================================
# Check 3: Backend Version Changes
# ============================================================
if [ -n "$REQUIREMENTS_STAGED" ]; then
    echo -n "Checking backend version changes... "

    OLD_REQ=$(git show HEAD:backend/requirements.txt 2>/dev/null || echo "")
    NEW_REQ=$(git show :backend/requirements.txt 2>/dev/null || echo "")

    BACKEND_CHANGES=""
    BACKEND_CRITICAL_CHANGED=""

    # Compare each line for version changes
    while IFS= read -r line; do
        # Skip comments and empty lines
        [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue

        # Extract package name (before ==, >=, etc.)
        PKG_NAME=$(echo "$line" | sed -E 's/([a-zA-Z0-9_-]+).*/\1/' | tr '[:upper:]' '[:lower:]')

        # Get versions
        NEW_VER=$(echo "$line" | grep -oE '(==|>=|<=|~=|>|<)[0-9][^,# ]*' | head -1 || true)
        OLD_LINE=$(echo "$OLD_REQ" | grep -iE "^$PKG_NAME(==|>=|<=|~=|>|<|\[)" | head -1 || true)
        OLD_VER=$(echo "$OLD_LINE" | grep -oE '(==|>=|<=|~=|>|<)[0-9][^,# ]*' | head -1 || true)

        if [ -n "$OLD_VER" ] && [ -n "$NEW_VER" ] && [ "$OLD_VER" != "$NEW_VER" ]; then
            BACKEND_CHANGES="$BACKEND_CHANGES\n  $PKG_NAME: $OLD_VER → $NEW_VER"

            # Check if critical
            if echo "$BACKEND_CRITICAL" | grep -qiw "$PKG_NAME"; then
                BACKEND_CRITICAL_CHANGED="$BACKEND_CRITICAL_CHANGED\n  $PKG_NAME: $OLD_VER → $NEW_VER"
                CRITICAL_CHANGES="$CRITICAL_CHANGES\n  $PKG_NAME: $OLD_VER → $NEW_VER"
            fi
        fi
    done < <(echo "$NEW_REQ")

    if [ -n "$BACKEND_CHANGES" ]; then
        echo -e "${BLUE}INFO${NC}"
        echo -e "${BLUE}Backend version changes:${NC}"
        echo -e "$BACKEND_CHANGES"
        echo ""
    else
        echo -e "${GREEN}OK${NC}"
    fi

    if [ -n "$BACKEND_CRITICAL_CHANGED" ]; then
        echo -n "Checking critical backend deps... "
        echo -e "${RED}CRITICAL${NC}"
        echo -e "${RED}Critical backend dependencies changed:${NC}"
        echo -e "$BACKEND_CRITICAL_CHANGED"
        echo ""
    fi

    # Check 4: Version format drift (== → >=)
    echo -n "Checking version format drift... "
    FORMAT_DRIFT=""

    while IFS= read -r line; do
        [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue

        PKG_NAME=$(echo "$line" | sed -E 's/([a-zA-Z0-9_-]+).*/\1/' | tr '[:upper:]' '[:lower:]')
        OLD_LINE=$(echo "$OLD_REQ" | grep -iE "^$PKG_NAME(==|>=|<=|~=|>|<|\[)" | head -1 || true)

        # Check if was pinned (==) and now is range (>=, etc.)
        if echo "$OLD_LINE" | grep -qE "==[0-9]" && ! echo "$line" | grep -qE "==[0-9]"; then
            FORMAT_DRIFT="$FORMAT_DRIFT\n  $PKG_NAME: == (pinned) → range"
        fi
    done < <(echo "$NEW_REQ")

    if [ -n "$FORMAT_DRIFT" ]; then
        echo -e "${YELLOW}WARNING${NC}"
        echo -e "${YELLOW}Version format changed from pinned to range:${NC}"
        echo -e "$FORMAT_DRIFT"
        echo ""
        echo -e "Consider keeping exact pins for stability."
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${GREEN}OK${NC}"
    fi
fi

# ============================================================
# Check 5: Block on Critical Changes (unless DEP_ALLOW=1)
# ============================================================
if [ -n "$CRITICAL_CHANGES" ]; then
    echo ""
    if [ "${DEP_ALLOW:-0}" = "1" ]; then
        echo -e "${YELLOW}ALLOWED: Critical dependency changes (DEP_ALLOW=1)${NC}"
        echo -e "$CRITICAL_CHANGES"
        echo ""
        echo -e "Make sure you've tested these changes thoroughly!"
    else
        echo -e "${RED}BLOCKED: Critical dependency changes detected${NC}"
        echo -e "$CRITICAL_CHANGES"
        echo ""
        echo -e "These packages are critical to system stability."
        echo -e "Override with: ${CYAN}DEP_ALLOW=1 git commit ...${NC}"
        echo ""
        ERRORS=$((ERRORS + 1))
    fi
fi

# ============================================================
# Summary
# ============================================================
echo ""
if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}Dependency check BLOCKED ($ERRORS critical change(s))${NC}"
    echo "Use DEP_ALLOW=1 to override after reviewing changes."
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}Dependency check found $WARNINGS warning(s)${NC}"
    echo "Review version changes before pushing."
    exit 0
else
    echo -e "${GREEN}Dependency check passed!${NC}"
    exit 0
fi
