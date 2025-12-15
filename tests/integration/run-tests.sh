#!/bin/bash

# Integration Test Runner Script
# Runs API integration tests for Residency Scheduler

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Residency Scheduler Integration Tests${NC}"
echo -e "${GREEN}================================${NC}\n"

# Check if backend is running
echo -e "${YELLOW}Checking backend API...${NC}"
API_URL="${API_BASE_URL:-http://localhost:8000}"
if curl -s -f "${API_URL}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend API is running at ${API_URL}${NC}\n"
else
    echo -e "${RED}✗ Backend API is not running at ${API_URL}${NC}"
    echo -e "${YELLOW}Please start the backend first:${NC}"
    echo -e "  cd backend"
    echo -e "  uvicorn app.main:app --reload --port 8000\n"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    npm install
    echo -e "${GREEN}✓ Dependencies installed${NC}\n"
fi

# Run tests based on argument
case "${1}" in
    "watch")
        echo -e "${YELLOW}Running tests in watch mode...${NC}\n"
        npm run test:watch
        ;;
    "coverage")
        echo -e "${YELLOW}Running tests with coverage...${NC}\n"
        npm run test:coverage
        ;;
    "verbose")
        echo -e "${YELLOW}Running tests in verbose mode...${NC}\n"
        npm run test:verbose
        ;;
    "ci")
        echo -e "${YELLOW}Running tests for CI...${NC}\n"
        npm run test:ci
        ;;
    *)
        echo -e "${YELLOW}Running all tests...${NC}\n"
        npm test
        ;;
esac

# Check exit code
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}================================${NC}"
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo -e "${GREEN}================================${NC}"
else
    echo -e "\n${RED}================================${NC}"
    echo -e "${RED}✗ Some tests failed${NC}"
    echo -e "${RED}================================${NC}"
    exit 1
fi
