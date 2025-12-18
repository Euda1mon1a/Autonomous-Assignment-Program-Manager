#!/bin/bash
#
# Pre-flight check for load tests
# Validates that the environment is ready to run load tests
#

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL=${K6_BASE_URL:-http://localhost:8000}
TEST_USERNAME=${TEST_USERNAME:-loadtest@example.com}
TEST_PASSWORD=${TEST_PASSWORD:-LoadTest123!@#}

echo "================================================================================"
echo "                    LOAD TEST PRE-FLIGHT CHECK                                 "
echo "================================================================================"
echo ""

CHECKS_PASSED=0
CHECKS_FAILED=0

# Check function
check() {
    local name=$1
    local command=$2
    local error_msg=$3

    echo -n "Checking $name... "

    if eval "$command" &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC}"
        echo -e "${RED}  Error: $error_msg${NC}"
        ((CHECKS_FAILED++))
        return 1
    fi
}

# Check if k6 is installed
check "k6 installation" \
    "command -v k6" \
    "k6 is not installed. Install from: https://k6.io/docs/getting-started/installation/"

# Check if Docker is running
check "Docker daemon" \
    "docker info" \
    "Docker is not running. Start Docker with: sudo systemctl start docker"

# Check if application containers are running
check "Application containers" \
    "docker-compose ps | grep -q 'Up'" \
    "Application containers are not running. Start with: docker-compose up -d"

# Check if backend is accessible
check "Backend API health endpoint" \
    "curl -s -f -m 5 '$BASE_URL/health'" \
    "Backend API not responding at $BASE_URL/health"

# Check if Redis is accessible (for rate limiting)
check "Redis connection" \
    "docker-compose exec -T redis redis-cli PING | grep -q PONG" \
    "Redis is not accessible. Rate limiting may not work."

# Check if database is accessible
check "PostgreSQL database" \
    "docker-compose exec -T db psql -U scheduler -d residency_scheduler -c 'SELECT 1;'" \
    "Database is not accessible."

# Test authentication endpoint
echo -n "Checking authentication endpoint... "
AUTH_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X POST "$BASE_URL/api/auth/login/json" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"test@test.com\",\"password\":\"wrong\"}")

if [ "$AUTH_RESPONSE" = "401" ] || [ "$AUTH_RESPONSE" = "429" ]; then
    echo -e "${GREEN}✓${NC} (status: $AUTH_RESPONSE)"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} (status: $AUTH_RESPONSE)"
    echo -e "${RED}  Error: Expected 401 or 429, got $AUTH_RESPONSE${NC}"
    ((CHECKS_FAILED++))
fi

# Check if test user exists (optional)
echo -n "Checking test user existence... "
USER_CHECK=$(docker-compose exec -T db psql -U scheduler -d residency_scheduler -t -c \
    "SELECT COUNT(*) FROM persons WHERE email = '$TEST_USERNAME';" 2>/dev/null | tr -d ' ' || echo "0")

if [ "$USER_CHECK" -ge "1" ]; then
    echo -e "${GREEN}✓${NC} (user: $TEST_USERNAME)"
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC} (user not found: $TEST_USERNAME)"
    echo -e "${YELLOW}  Warning: Test user doesn't exist. Some tests may fail.${NC}"
    echo -e "${YELLOW}  Create user or set TEST_USERNAME and TEST_PASSWORD environment variables.${NC}"
    # Not counting this as a failure since it's optional
fi

# Check if results directory exists
check "Results directory" \
    "[ -d 'results' ] || mkdir -p 'results'" \
    "Could not create results directory"

# Check for jq (optional, for result parsing)
echo -n "Checking jq (optional for result parsing)... "
if command -v jq &> /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠${NC} (not installed, but optional)"
fi

echo ""
echo "================================================================================"
echo "                              SUMMARY                                          "
echo "================================================================================"
echo -e "Checks passed: ${GREEN}$CHECKS_PASSED${NC}"
echo -e "Checks failed: ${RED}$CHECKS_FAILED${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ Environment is ready for load testing!${NC}"
    echo ""
    echo "Run tests with:"
    echo "  ./run-load-tests.sh"
    echo ""
    echo "Or run individual tests:"
    echo "  k6 run load-tests/scenarios/rate-limit-attack.js"
    echo "  k6 run load-tests/scenarios/auth-security.js"
    echo "================================================================================"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please fix the issues above before running tests.${NC}"
    echo "================================================================================"
    exit 1
fi
