#!/bin/bash
# ============================================================
# Script: health-check.sh (monitoring)
# Purpose: Verify monitoring stack health
# Usage: ./monitoring/scripts/health-check.sh
#
# Description:
#   Checks health status of all monitoring services:
#   Prometheus, Grafana, Alertmanager, Loki, and backend metrics.
#   Validates HTTP endpoints and service responsiveness.
#
# Services Checked:
#   - Prometheus (metrics collection)
#   - Grafana (visualization)
#   - Alertmanager (alert routing)
#   - Loki (log aggregation)
#   - Backend metrics endpoint
#
# Exit Codes:
#   0 - All services healthy
#   1 - One or more services degraded
#   2 - Critical service failure
#
# Environment Variables:
#   PROMETHEUS_URL    - Prometheus endpoint (default: http://localhost:9090)
#   GRAFANA_URL       - Grafana endpoint (default: http://localhost:3001)
#   ALERTMANAGER_URL  - Alertmanager endpoint (default: http://localhost:9093)
#   LOKI_URL          - Loki endpoint (default: http://localhost:3100)
# ============================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Service endpoints
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3001}"
ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://localhost:9093}"
LOKI_URL="${LOKI_URL:-http://localhost:3100}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

# Timeout for HTTP requests
TIMEOUT=5

# Verify curl or wget is available for health checks
if ! command -v curl >/dev/null 2>&1 && ! command -v wget >/dev/null 2>&1; then
    echo -e "${RED}ERROR: curl or wget required for health checks${NC}" >&2
    exit 1
fi

echo "============================================"
echo "  Residency Scheduler Health Check"
echo "============================================"
echo ""

check_service() {
    local name=$1
    local url=$2
    local endpoint=$3

    printf "Checking %-20s ... " "$name"

    if curl -sf --connect-timeout $TIMEOUT "${url}${endpoint}" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
}

check_prometheus_targets() {
    printf "Checking %-20s ... " "Prometheus Targets"

    targets=$(curl -sf --connect-timeout $TIMEOUT "${PROMETHEUS_URL}/api/v1/targets" 2>/dev/null)
    if [ $? -eq 0 ]; then
        up_count=$(echo "$targets" | grep -o '"health":"up"' | wc -l)
        down_count=$(echo "$targets" | grep -o '"health":"down"' | wc -l)

        if [ "$down_count" -gt 0 ]; then
            echo -e "${YELLOW}⚠ $up_count up, $down_count down${NC}"
        else
            echo -e "${GREEN}✓ $up_count targets up${NC}"
        fi
    else
        echo -e "${RED}✗ FAILED${NC}"
    fi
}

check_prometheus_alerts() {
    printf "Checking %-20s ... " "Active Alerts"

    alerts=$(curl -sf --connect-timeout $TIMEOUT "${PROMETHEUS_URL}/api/v1/alerts" 2>/dev/null)
    if [ $? -eq 0 ]; then
        firing=$(echo "$alerts" | grep -o '"state":"firing"' | wc -l)
        pending=$(echo "$alerts" | grep -o '"state":"pending"' | wc -l)

        if [ "$firing" -gt 0 ]; then
            echo -e "${RED}⚠ $firing firing, $pending pending${NC}"
        elif [ "$pending" -gt 0 ]; then
            echo -e "${YELLOW}⚠ $pending pending${NC}"
        else
            echo -e "${GREEN}✓ No active alerts${NC}"
        fi
    else
        echo -e "${RED}✗ FAILED${NC}"
    fi
}

failed=0

echo "--- Core Services ---"
check_service "Backend API" "$BACKEND_URL" "/health" || ((failed++))
check_service "Prometheus" "$PROMETHEUS_URL" "/-/healthy" || ((failed++))
check_service "Grafana" "$GRAFANA_URL" "/api/health" || ((failed++))
check_service "Alertmanager" "$ALERTMANAGER_URL" "/-/healthy" || ((failed++))
check_service "Loki" "$LOKI_URL" "/ready" || ((failed++))

echo ""
echo "--- Prometheus Status ---"
check_prometheus_targets
check_prometheus_alerts

echo ""
echo "============================================"

if [ $failed -gt 0 ]; then
    echo -e "${RED}Health check completed with $failed failure(s)${NC}"
    exit 1
else
    echo -e "${GREEN}All health checks passed!${NC}"
    exit 0
fi
