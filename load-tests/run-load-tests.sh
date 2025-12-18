#!/bin/bash
#
# Load Test Runner Script
# Runs all rate limiting and authentication security tests
#
# Usage:
#   ./run-load-tests.sh [options]
#
# Options:
#   --rate-limit-only    Run only rate limiting attack tests
#   --auth-only          Run only authentication security tests
#   --base-url URL       Override base URL (default: http://localhost:8000)
#   --results-dir DIR    Output directory for results (default: results/)
#   --skip-wait          Skip cooldown period between tests
#

set -e

# Default configuration
BASE_URL=${K6_BASE_URL:-http://localhost:8000}
RESULTS_DIR="results"
COOLDOWN_SECONDS=60
RUN_RATE_LIMIT=true
RUN_AUTH=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --rate-limit-only)
            RUN_AUTH=false
            shift
            ;;
        --auth-only)
            RUN_RATE_LIMIT=false
            shift
            ;;
        --base-url)
            BASE_URL="$2"
            shift 2
            ;;
        --results-dir)
            RESULTS_DIR="$2"
            shift 2
            ;;
        --skip-wait)
            COOLDOWN_SECONDS=0
            shift
            ;;
        --help)
            echo "Load Test Runner Script"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --rate-limit-only    Run only rate limiting attack tests"
            echo "  --auth-only          Run only authentication security tests"
            echo "  --base-url URL       Override base URL (default: http://localhost:8000)"
            echo "  --results-dir DIR    Output directory for results (default: results/)"
            echo "  --skip-wait          Skip cooldown period between tests"
            echo "  --help               Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Ensure results directory exists
mkdir -p "$RESULTS_DIR"

# Timestamp for result files
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if k6 is installed
if ! command -v k6 &> /dev/null; then
    echo -e "${RED}Error: k6 is not installed${NC}"
    echo "Please install k6 from: https://k6.io/docs/getting-started/installation/"
    exit 1
fi

# Check if application is running
echo -e "${BLUE}Checking if application is running...${NC}"
if ! curl -s -f -m 5 "$BASE_URL/health" > /dev/null; then
    echo -e "${RED}Error: Application not responding at $BASE_URL${NC}"
    echo "Please start the application first:"
    echo "  docker-compose up -d"
    exit 1
fi
echo -e "${GREEN}✓ Application is running${NC}"
echo ""

# Display test configuration
echo "================================================================================"
echo "                        LOAD TEST EXECUTION                                   "
echo "================================================================================"
echo "Base URL:       $BASE_URL"
echo "Results Dir:    $RESULTS_DIR"
echo "Timestamp:      $TIMESTAMP"
echo "Tests to run:   $([ "$RUN_RATE_LIMIT" = true ] && echo -n "Rate Limit " )$([ "$RUN_AUTH" = true ] && echo -n "Auth Security")"
echo "================================================================================"
echo ""

# Function to run a test
run_test() {
    local test_name=$1
    local test_file=$2
    local output_file=$3

    echo -e "${BLUE}Starting: $test_name${NC}"
    echo "Output: $output_file"
    echo ""

    if K6_BASE_URL="$BASE_URL" k6 run \
        --out "json=$output_file" \
        "$test_file"; then
        echo ""
        echo -e "${GREEN}✓ $test_name completed successfully${NC}"
        return 0
    else
        echo ""
        echo -e "${RED}✗ $test_name failed${NC}"
        return 1
    fi
}

# Track overall status
OVERALL_STATUS=0

# Run Rate Limit Attack Tests
if [ "$RUN_RATE_LIMIT" = true ]; then
    run_test \
        "Rate Limit Attack Simulation" \
        "load-tests/scenarios/rate-limit-attack.js" \
        "$RESULTS_DIR/rate-limit-attack_$TIMESTAMP.json" || OVERALL_STATUS=1

    # Cooldown period between tests
    if [ "$RUN_AUTH" = true ] && [ "$COOLDOWN_SECONDS" -gt 0 ]; then
        echo ""
        echo -e "${YELLOW}Waiting ${COOLDOWN_SECONDS}s for rate limits to reset...${NC}"
        sleep "$COOLDOWN_SECONDS"
        echo ""
    fi
fi

# Run Authentication Security Tests
if [ "$RUN_AUTH" = true ]; then
    run_test \
        "Authentication Security Tests" \
        "load-tests/scenarios/auth-security.js" \
        "$RESULTS_DIR/auth-security_$TIMESTAMP.json" || OVERALL_STATUS=1
fi

# Summary
echo ""
echo "================================================================================"
echo "                        TEST EXECUTION COMPLETE                                "
echo "================================================================================"
echo "Results saved in: $RESULTS_DIR/"
echo ""

if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${RED}✗ Some tests failed - check results for details${NC}"
fi

echo "================================================================================"
echo ""

# Display quick metrics summary if jq is available
if command -v jq &> /dev/null; then
    echo "Quick Metrics Summary:"
    echo "----------------------"

    if [ "$RUN_RATE_LIMIT" = true ]; then
        echo ""
        echo "Rate Limit Attack:"
        RATE_LIMIT_FILE="$RESULTS_DIR/rate-limit-attack_$TIMESTAMP.json"
        if [ -f "$RATE_LIMIT_FILE" ]; then
            echo "  - Total requests: $(grep -c '"type":"Point"' "$RATE_LIMIT_FILE" || echo "N/A")"
            echo "  - Check result file for detailed metrics"
        fi
    fi

    if [ "$RUN_AUTH" = true ]; then
        echo ""
        echo "Authentication Security:"
        AUTH_FILE="$RESULTS_DIR/auth-security_$TIMESTAMP.json"
        if [ -f "$AUTH_FILE" ]; then
            echo "  - Total requests: $(grep -c '"type":"Point"' "$AUTH_FILE" || echo "N/A")"
            echo "  - Check result file for detailed metrics"
        fi
    fi

    echo ""
fi

exit $OVERALL_STATUS
