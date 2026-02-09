#!/bin/bash
# ============================================================
# Script: status-native.sh
# Purpose: Show status of native (non-Docker) services
# Usage: ./scripts/status-native.sh [--json] [--logs]
#
# Options:
#   --json   Output JSON format
#   --logs   Tail all native log files after displaying status
# ============================================================

set -euo pipefail

# Source shared library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./_native-lib.sh
source "${SCRIPT_DIR}/_native-lib.sh"

# -----------------------------------------------------------
# Parse arguments
# -----------------------------------------------------------
JSON_OUTPUT=false
SHOW_LOGS=false

for arg in "$@"; do
    case "$arg" in
        --json) JSON_OUTPUT=true ;;
        --logs) SHOW_LOGS=true ;;
        -h|--help)
            echo "Usage: $0 [--json] [--logs]"
            echo ""
            echo "Options:"
            echo "  --json   Output JSON format"
            echo "  --logs   Tail all native log files after status"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $arg${NC}"
            echo "Run $0 --help for usage"
            exit 1
            ;;
    esac
done

# -----------------------------------------------------------
# Health check helpers
# -----------------------------------------------------------
check_postgres() {
    pg_isready -q -h localhost -p 5432 2>/dev/null
}

check_redis() {
    redis-cli ping 2>/dev/null | grep -q PONG
}

check_http() {
    local url="$1"
    curl -sf --max-time 3 "$url" >/dev/null 2>&1
}

# -----------------------------------------------------------
# Check a tracked service — sets SVC_STATUS, SVC_DETAIL, SVC_PID
# -----------------------------------------------------------
check_service() {
    local name="$1"
    SVC_PID=""
    SVC_STATUS="stopped"
    SVC_DETAIL="not running"

    SVC_PID=$(read_pid "$name")

    if [ -n "$SVC_PID" ] && kill -0 "$SVC_PID" 2>/dev/null; then
        SVC_STATUS="running"
        SVC_DETAIL="PID $SVC_PID"

        # Health check for services with HTTP endpoints
        local health_url
        health_url=$(get_service_health_url "$name")
        if [ -n "$health_url" ]; then
            if check_http "$health_url"; then
                SVC_DETAIL="PID $SVC_PID, healthy"
            else
                SVC_DETAIL="PID $SVC_PID, unhealthy"
                SVC_STATUS="degraded"
            fi
        fi
    elif [ -n "$SVC_PID" ]; then
        # PID file exists but process is dead
        SVC_DETAIL="stale PID $SVC_PID"
        SVC_STATUS="dead"
    fi
}

# -----------------------------------------------------------
# JSON output
# -----------------------------------------------------------
print_json() {
    local pg_status="stopped"
    local redis_status="stopped"
    check_postgres && pg_status="running"
    check_redis && redis_status="running"

    local all_services=(backend frontend celery-worker celery-beat mcp mlx)
    local count=${#all_services[@]}
    local running=0
    local total=$count

    # Build services JSON and count running
    local svc_json=""
    local i=0
    for svc in "${all_services[@]}"; do
        i=$((i + 1))
        check_service "$svc"
        local port
        port=$(get_service_port "$svc")
        port="${port:-null}"
        local pid_val="${SVC_PID:-null}"
        local comma=","
        [ $i -eq $count ] && comma=""

        svc_json="${svc_json}    \"$svc\": {\"status\": \"$SVC_STATUS\", \"pid\": $pid_val, \"port\": $port, \"detail\": \"$SVC_DETAIL\"}${comma}
"
        if [ "$SVC_STATUS" = "running" ] || [ "$SVC_STATUS" = "degraded" ]; then
            running=$((running + 1))
        fi
    done

    local overall="DOWN"
    if [ $running -eq $total ]; then
        overall="HEALTHY"
    elif [ $running -gt 0 ]; then
        overall="DEGRADED"
    fi

    cat <<EOF
{
  "infrastructure": {
    "postgresql": {"status": "$pg_status", "port": 5432},
    "redis": {"status": "$redis_status", "port": 6379}
  },
  "services": {
${svc_json}  },
  "overall": {"status": "$overall", "running": $running, "total": $total}
}
EOF
}

# -----------------------------------------------------------
# Terminal output
# -----------------------------------------------------------
print_terminal() {
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}  Residency Scheduler - Native Status${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo ""

    # Infrastructure
    echo -e "${BLUE}Infrastructure:${NC}"

    if check_postgres; then
        echo -e "  ${GREEN}[OK]${NC} PostgreSQL   :5432  (running)"
    else
        echo -e "  ${RED}[!!]${NC} PostgreSQL   :5432  (not running)"
    fi

    if check_redis; then
        echo -e "  ${GREEN}[OK]${NC} Redis        :6379  (running)"
    else
        echo -e "  ${RED}[!!]${NC} Redis        :6379  (not running)"
    fi

    echo ""
    echo -e "${BLUE}Application:${NC}"

    # Application services in display order
    local all_services=(backend frontend mcp celery-worker celery-beat mlx)
    local running=0
    local total=${#all_services[@]}

    for svc in "${all_services[@]}"; do
        check_service "$svc"
        local port
        port=$(get_service_port "$svc")
        local port_str=""
        [ -n "$port" ] && port_str=":${port}  "

        # Pad service name for alignment
        local label
        case "$svc" in
            backend)       label="Backend     " ;;
            frontend)      label="Frontend    " ;;
            mcp)           label="MCP Server  " ;;
            celery-worker) label="Celery Worker" ;;
            celery-beat)   label="Celery Beat  " ;;
            mlx)           label="MLX Server  " ;;
            *)             label="$svc" ;;
        esac

        if [ "$SVC_STATUS" = "running" ]; then
            echo -e "  ${GREEN}[OK]${NC} ${label} ${port_str}(${SVC_DETAIL})"
            running=$((running + 1))
        elif [ "$SVC_STATUS" = "degraded" ]; then
            echo -e "  ${YELLOW}[!!]${NC} ${label} ${port_str}(${SVC_DETAIL})"
            running=$((running + 1))
        elif [ "$SVC_STATUS" = "dead" ]; then
            echo -e "  ${RED}[!!]${NC} ${label} ${port_str}(${SVC_DETAIL})"
        else
            echo -e "  ${YELLOW}[--]${NC} ${label} ${port_str}(not running)"
        fi
    done

    # Access points
    echo ""
    echo -e "${BLUE}Access Points:${NC}"
    echo "  Frontend:  http://localhost:3000"
    echo "  Backend:   http://localhost:8000"
    echo "  API Docs:  http://localhost:8000/docs"
    echo "  MCP:       http://localhost:8081"

    # Overall status
    echo ""
    local overall="DOWN"
    local color="$RED"
    if [ $running -eq $total ]; then
        overall="HEALTHY"
        color="$GREEN"
    elif [ $running -gt 0 ]; then
        overall="DEGRADED"
        color="$YELLOW"
    fi

    echo -e "${GREEN}=========================================${NC}"
    echo -e "  Overall: ${color}${overall}${NC} (${running}/${total} services up)"
    echo -e "${GREEN}=========================================${NC}"
}

# -----------------------------------------------------------
# Main
# -----------------------------------------------------------
if [ "$JSON_OUTPUT" = true ]; then
    print_json
else
    print_terminal
fi

# Show logs if requested
if [ "$SHOW_LOGS" = true ]; then
    echo ""
    if ls "$LOG_DIR"/*.log >/dev/null 2>&1; then
        echo -e "${YELLOW}Following logs (Ctrl+C to exit)...${NC}"
        tail -f "$LOG_DIR"/*.log
    else
        echo -e "${YELLOW}No log files found in $LOG_DIR${NC}"
    fi
fi
