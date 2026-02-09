#!/bin/bash
# ============================================================
# Script: start-native.sh
# Purpose: Start ALL services natively (no Docker)
# Usage: ./scripts/start-native.sh [--bootstrap] [--mlx] [--skip-infra] [--follow]
#
# Description:
#   Native replacement for docker compose in local development.
#   Starts the complete stack: Postgres, Redis, FastAPI backend,
#   Celery worker/beat, Next.js frontend, and MCP server.
#
# Options:
#   --bootstrap   Install/start Postgres+Redis via Homebrew
#   --mlx         Also start MLX inference server on :8082
#   --skip-infra  Skip Postgres/Redis availability checks
#   --follow      Tail combined logs after startup
#
# Requires:
#   - Python 3.11+ with backend virtualenv activated
#   - Node.js 18+ with frontend deps installed
#   - Postgres 15 and Redis (native or via brew)
# ============================================================

set -euo pipefail

# Source shared library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./_native-lib.sh
source "${SCRIPT_DIR}/_native-lib.sh"

# -----------------------------------------------------------
# Parse arguments
# -----------------------------------------------------------
BOOTSTRAP=false
MLX=false
SKIP_INFRA=false
FOLLOW=false

for arg in "$@"; do
    case "$arg" in
        --bootstrap)  BOOTSTRAP=true ;;
        --mlx)        MLX=true ;;
        --skip-infra) SKIP_INFRA=true ;;
        --follow)     FOLLOW=true ;;
        -h|--help)
            echo "Usage: $0 [--bootstrap] [--mlx] [--skip-infra] [--follow]"
            echo ""
            echo "Options:"
            echo "  --bootstrap   Install/start Postgres+Redis via brew services"
            echo "  --mlx         Also start MLX inference server on :8082"
            echo "  --skip-infra  Skip Postgres/Redis checks"
            echo "  --follow      Tail combined logs after startup"
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
# Cleanup trap
# -----------------------------------------------------------
STARTED_SERVICES=()

cleanup() {
    echo ""
    echo -e "${YELLOW}Caught signal, cleaning up partially-started services...${NC}"
    for svc in "${STARTED_SERVICES[@]}"; do
        if is_running "$svc"; then
            echo "  Stopping $svc..."
            kill_service "$svc"
        fi
    done
    echo -e "${GREEN}Cleanup complete${NC}"
    exit 1
}

trap cleanup SIGINT SIGTERM

# -----------------------------------------------------------
# start_service helper
# -----------------------------------------------------------
start_service() {
    local name="$1"
    local workdir="$2"
    shift 2
    local cmd="$*"

    if is_running "$name"; then
        echo -e "  ${GREEN}[OK]${NC} $name already running (PID $(read_pid "$name"))"
        return 0
    fi

    local port
    port=$(get_service_port "$name")
    if [ -n "$port" ] && check_port "$port"; then
        echo -e "  ${RED}[!!]${NC} $name: port $port already in use"
        return 1
    fi

    ensure_dirs
    cd "$workdir"
    # shellcheck disable=SC2086
    $cmd >> "${LOG_DIR}/${name}.log" 2>&1 &
    local pid=$!
    write_pid "$name" "$pid"
    STARTED_SERVICES+=("$name")

    if [ -n "$port" ]; then
        # Backend loads ML models at startup — needs longer timeout
        local timeout=30
        [ "$name" = "backend" ] && timeout=90
        if wait_for_port "$port" "$timeout"; then
            echo -e "  ${GREEN}[OK]${NC} $name on :${port} (PID $pid)"
        else
            echo -e "  ${RED}[!!]${NC} $name failed to start (check ${LOG_DIR}/${name}.log)"
            kill_service "$name"
            return 1
        fi
    else
        sleep 2
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "  ${GREEN}[OK]${NC} $name (PID $pid)"
        else
            echo -e "  ${RED}[!!]${NC} $name died. Check ${LOG_DIR}/${name}.log"
            return 1
        fi
    fi

    cd "$PROJECT_ROOT"
}

# ===========================================================
# Phase 1: Infrastructure checks
# ===========================================================
echo -e "${BLUE}=== Phase 1: Infrastructure ===${NC}"

if [ "$SKIP_INFRA" = true ]; then
    echo -e "  ${YELLOW}[--]${NC} Skipping infrastructure checks (--skip-infra)"
else
    # --- Postgres ---
    PG_OK=false
    if pg_isready -q -h localhost -p 5432 2>/dev/null; then
        echo -e "  ${GREEN}[OK]${NC} PostgreSQL is running"
        PG_OK=true
    else
        if [ "$BOOTSTRAP" = true ]; then
            echo -e "  ${YELLOW}[..]${NC} Starting PostgreSQL via brew..."
            brew services start postgresql@15
            sleep 3
            if pg_isready -q -h localhost -p 5432 2>/dev/null; then
                echo -e "  ${GREEN}[OK]${NC} PostgreSQL started"
                PG_OK=true
            else
                echo -e "  ${RED}[!!]${NC} PostgreSQL failed to start"
            fi
        else
            echo -e "  ${RED}[!!]${NC} PostgreSQL not running on localhost:5432"
            echo "         Run: brew services start postgresql@15"
            echo "         Or use: $0 --bootstrap"
        fi
    fi

    # --- Redis ---
    REDIS_OK=false
    if redis-cli ping 2>/dev/null | grep -q PONG; then
        echo -e "  ${GREEN}[OK]${NC} Redis is running"
        REDIS_OK=true
    else
        if [ "$BOOTSTRAP" = true ]; then
            echo -e "  ${YELLOW}[..]${NC} Starting Redis via brew..."
            brew services start redis
            sleep 2
            if redis-cli ping 2>/dev/null | grep -q PONG; then
                echo -e "  ${GREEN}[OK]${NC} Redis started"
                REDIS_OK=true
            else
                echo -e "  ${RED}[!!]${NC} Redis failed to start"
            fi
        else
            echo -e "  ${RED}[!!]${NC} Redis not running"
            echo "         Run: brew services start redis"
            echo "         Or use: $0 --bootstrap"
        fi
    fi

    # Abort if infra is missing
    if [ "$PG_OK" = false ] || [ "$REDIS_OK" = false ]; then
        echo ""
        echo -e "${RED}Required infrastructure not available. Aborting.${NC}"
        exit 1
    fi
fi

# ===========================================================
# Phase 2: Environment
# ===========================================================
echo ""
echo -e "${BLUE}=== Phase 2: Environment ===${NC}"

# Activate Python virtual environment if present
VENV_DIR="${PROJECT_ROOT}/backend/.venv"
if [ -f "${VENV_DIR}/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "${VENV_DIR}/bin/activate"
    echo -e "  ${GREEN}[OK]${NC} Python venv activated ($(python3 --version))"
else
    echo -e "  ${YELLOW}[--]${NC} No venv at ${VENV_DIR} — using system Python"
fi

export DATABASE_URL="postgresql://scheduler:scheduler@localhost:5432/residency_scheduler"
export REDIS_URL="redis://localhost:6379/0"
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/0"
export DEBUG="true"
export CORS_ORIGINS='["http://localhost:3000"]'
export SECRET_KEY="${SECRET_KEY:-local_dev_secret_key_not_for_production_use_only_12345678901234567890}"

echo -e "  ${GREEN}[OK]${NC} Environment variables set"

# ===========================================================
# Phase 3: Migrations
# ===========================================================
echo ""
echo -e "${BLUE}=== Phase 3: Migrations ===${NC}"

if cd "$PROJECT_ROOT/backend" && python -m alembic upgrade head 2>/dev/null; then
    echo -e "  ${GREEN}[OK]${NC} Database migrations applied"
else
    echo -e "  ${YELLOW}[--]${NC} Migrations skipped (may already be current)"
fi
cd "$PROJECT_ROOT"

# ===========================================================
# Phase 4: Start services
# ===========================================================
echo ""
echo -e "${BLUE}=== Phase 4: Starting Services ===${NC}"

ensure_dirs
echo -e "  ${GREEN}[OK]${NC} PID dir: $PID_DIR"
echo -e "  ${GREEN}[OK]${NC} Log dir: $LOG_DIR"
echo ""

# 1. Backend
start_service "backend" "$PROJECT_ROOT/backend" \
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Wait for backend health before dependent services
echo -e "  ${YELLOW}[..]${NC} Waiting for backend health check..."
HEALTH_OK=false
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "  ${GREEN}[OK]${NC} Backend health check passed"
        HEALTH_OK=true
        break
    fi
    sleep 1
done
if [ "$HEALTH_OK" = false ]; then
    echo -e "  ${YELLOW}[--]${NC} Backend health endpoint not responding (service may still work)"
fi

# 2. Celery worker
start_service "celery-worker" "$PROJECT_ROOT/backend" \
    celery -A app.core.celery_app worker \
    --loglevel=info \
    -Q default,resilience,notifications \
    --concurrency=4 \
    --time-limit=600 \
    --soft-time-limit=540 \
    --max-tasks-per-child=1000

# 3. Celery beat
start_service "celery-beat" "$PROJECT_ROOT/backend" \
    celery -A app.core.celery_app beat \
    --loglevel=info

# 4. Frontend
start_service "frontend" "$PROJECT_ROOT/frontend" \
    npx next dev --port 3000

# 5. MCP server
export PYTHONPATH="${PROJECT_ROOT}/mcp-server/src"
export API_BASE_URL="http://localhost:8000"

start_service "mcp" "$PROJECT_ROOT/mcp-server/src" \
    python -m scheduler_mcp.server

# 6. Optional MLX server
if [ "$MLX" = true ]; then
    echo ""
    echo -e "  ${YELLOW}[..]${NC} Starting MLX inference server..."
    start_service "mlx" "$PROJECT_ROOT" \
        python -m mlx_lm.server --port 8082
fi

# ===========================================================
# Phase 5: Access points
# ===========================================================
echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN} All services started${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "${GREEN}Access Points:${NC}"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  MCP:       http://localhost:8081"
if [ "$MLX" = true ]; then
    echo "  MLX:       http://localhost:8082"
fi
echo ""
echo "  PID files: $PID_DIR/"
echo "  Logs:      $LOG_DIR/"
echo ""
echo "Stop all: ./scripts/stop-native.sh"
echo ""

# Follow logs if requested
if [ "$FOLLOW" = true ]; then
    echo -e "${YELLOW}Following logs (Ctrl+C to exit)...${NC}"
    tail -f "$LOG_DIR"/*.log
fi
