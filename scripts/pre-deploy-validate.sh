#!/bin/bash
# ============================================================
# Script: pre-deploy-validate.sh
# Purpose: Pre-deployment validation and safety checks
# Usage: ./scripts/pre-deploy-validate.sh
#
# Description:
#   Comprehensive validation script to verify system readiness
#   before deploying to production. Checks configuration,
#   code quality, security settings, and dependencies.
#
# Validation Checks:
#   1. Environment configuration (.env file, required variables)
#   2. Code quality (no debug statements, formatting)
#   3. Security (no hardcoded secrets, CORS configured)
#   4. Configuration files (docker-compose, requirements)
#   5. Database migrations (Alembic setup)
#   6. Dependencies (all required packages listed)
#
# Exit Codes:
#   0 - All checks passed or warnings only
#   1 - Critical errors found (do not deploy)
# ============================================================

set -euo pipefail

echo "=============================================="
echo "Pre-Deployment Validation Script"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Verify we're in project root
if [ ! -f "docker-compose.yml" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}ERROR: Must be run from project root directory${NC}" >&2
    exit 1
fi

check_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

check_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ERRORS=$((ERRORS + 1))
}

check_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

echo "1. Checking environment configuration..."
echo "-------------------------------------------"

# Check for required environment variables
# .env file must exist and contain critical configuration
if [ -f ".env" ]; then
    check_pass "Environment file (.env) exists"

    # Check SECRET_KEY - must be at least 32 characters for security
    # Used for JWT token signing and session encryption
    if grep -q "SECRET_KEY=" .env && [ "$(grep SECRET_KEY= .env | cut -d= -f2 | wc -c)" -gt 32 ]; then
        check_pass "SECRET_KEY is set and has minimum length"
    else
        check_fail "SECRET_KEY is missing or too short (min 32 chars)"
    fi

    # Check DATABASE_URL - required for all database operations
    # Format: postgresql://user:password@host:port/database
    if grep -q "DATABASE_URL=" .env; then
        check_pass "DATABASE_URL is configured"
    else
        check_fail "DATABASE_URL is not configured"
    fi

    # Check REDIS_URL - required for Celery task queue
    # Missing Redis will prevent background task processing
    if grep -q "REDIS_URL=" .env; then
        check_pass "REDIS_URL is configured"
    else
        check_warn "REDIS_URL is not configured (Celery may not work)"
    fi
else
    check_fail "Environment file (.env) not found - copy from .env.example"
fi

echo ""
echo "2. Checking code quality..."
echo "-------------------------------------------"

# Check for debug statements that should not be in production
# These can leak sensitive information or cause performance issues
if grep -rn --include="*.py" "breakpoint()\|pdb\|debugger" backend/app/ 2>/dev/null | grep -v "^Binary"; then
    check_fail "Debug statements found in backend code"
else
    check_pass "No debug statements in backend code"
fi

# Check for console.log and debugger in frontend code
# console.log is less critical but should be reviewed
# debugger statements will halt execution in browser dev tools
if grep -rn --include="*.ts" --include="*.tsx" "debugger\|console.log" frontend/src/ 2>/dev/null | head -5; then
    check_warn "Console.log statements found in frontend (review before deploy)"
else
    check_pass "No debugger statements in frontend code"
fi

echo ""
echo "3. Checking for hardcoded secrets..."
echo "-------------------------------------------"

# Check for potential hardcoded secrets (basic pattern matching)
SECRET_PATTERNS="password\s*=\s*['\"][^'\"]+['\"]|api_key\s*=\s*['\"][^'\"]+['\"]|secret\s*=\s*['\"][^'\"]+['\"]"
if grep -rniE "$SECRET_PATTERNS" --include="*.py" --include="*.ts" --include="*.tsx" backend/app/ frontend/src/ 2>/dev/null | grep -v "test\|mock\|example\|env\|config" | head -5; then
    check_warn "Potential hardcoded secrets found - review manually"
else
    check_pass "No obvious hardcoded secrets detected"
fi

echo ""
echo "4. Checking configuration files..."
echo "-------------------------------------------"

# Check Docker Compose files
for compose_file in docker-compose.yml docker-compose.prod.yml; do
    if [ -f "$compose_file" ]; then
        if command -v docker &> /dev/null; then
            if docker compose -f "$compose_file" config --quiet 2>/dev/null; then
                check_pass "Docker Compose file ($compose_file) is valid"
            else
                check_fail "Docker Compose file ($compose_file) has errors"
            fi
        else
            check_warn "Docker not available - skipping compose validation for $compose_file"
        fi
    else
        check_warn "Docker Compose file ($compose_file) not found"
    fi
done

# Check Python requirements
if [ -f "backend/requirements.txt" ]; then
    check_pass "Backend requirements.txt exists"
else
    check_fail "Backend requirements.txt not found"
fi

# Check package.json
if [ -f "frontend/package.json" ]; then
    check_pass "Frontend package.json exists"
else
    check_fail "Frontend package.json not found"
fi

echo ""
echo "5. Checking database migrations..."
echo "-------------------------------------------"

# Check if alembic is configured
if [ -f "backend/alembic.ini" ]; then
    check_pass "Alembic configuration exists"
else
    check_warn "Alembic configuration not found"
fi

# Check for migration files
MIGRATION_COUNT=$(find backend/alembic/versions -name "*.py" 2>/dev/null | wc -l)
if [ "$MIGRATION_COUNT" -gt 0 ]; then
    check_pass "Found $MIGRATION_COUNT migration files"
else
    check_warn "No migration files found"
fi

echo ""
echo "6. Checking security configurations..."
echo "-------------------------------------------"

# Check CORS settings
if grep -rq "CORS_ORIGINS\|CORSMiddleware" backend/app/; then
    check_pass "CORS middleware is configured"
else
    check_warn "CORS configuration not found"
fi

# Check rate limiting
if grep -rq "slowapi\|RateLimiter" backend/app/; then
    check_pass "Rate limiting is configured"
else
    check_warn "Rate limiting not found"
fi

echo ""
echo "=============================================="
echo "SUMMARY"
echo "=============================================="
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}All checks passed! Ready for deployment.${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}Passed with $WARNINGS warning(s). Review before deploying.${NC}"
    exit 0
else
    echo -e "${RED}Found $ERRORS error(s) and $WARNINGS warning(s). Fix errors before deploying.${NC}"
    exit 1
fi
