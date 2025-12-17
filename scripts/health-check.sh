#!/bin/bash

# Health Check Script for Residency Scheduler
# Verifies all services are running and healthy
#
# Exit codes:
#   0 - All services healthy
#   1 - One or more services unhealthy
#   2 - Critical service failure
#
# Usage:
#   ./scripts/health-check.sh [--verbose] [--docker]
#
# Options:
#   --verbose    Show detailed output
#   --docker     Check Docker containers instead of local services

set -e

# Configuration
VERBOSE=false
DOCKER_MODE=false
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
DATABASE_URL="${DATABASE_URL:-postgresql://scheduler:password@localhost:5432/residency_scheduler}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse arguments
for arg in "$@"; do
    case $arg in
        --verbose|-v)
            VERBOSE=true
            ;;
        --docker|-d)
            DOCKER_MODE=true
            ;;
    esac
done

# Exit code tracking
EXIT_CODE=0

# Helper functions
log_info() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[INFO]${NC} $1"
    fi
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
    if [ $EXIT_CODE -eq 0 ]; then
        EXIT_CODE=1
    fi
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    EXIT_CODE=2
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "Required command not found: $1"
        return 1
    fi
    return 0
}

# Check PostgreSQL
check_postgres() {
    log_info "Checking PostgreSQL..."

    if [ "$DOCKER_MODE" = true ]; then
        if docker compose exec -T db pg_isready -U scheduler -d residency_scheduler &>/dev/null; then
            log_success "PostgreSQL (Docker): Healthy"
            return 0
        else
            log_error "PostgreSQL (Docker): Unhealthy or not running"
            return 1
        fi
    else
        if command -v psql &> /dev/null; then
            if psql "$DATABASE_URL" -c "SELECT 1;" &>/dev/null; then
                log_success "PostgreSQL: Connected and responsive"
                return 0
            else
                log_error "PostgreSQL: Cannot connect or query failed"
                return 1
            fi
        else
            # Try using Python
            if python3 -c "import psycopg2; conn = psycopg2.connect('$DATABASE_URL'); conn.close()" 2>/dev/null; then
                log_success "PostgreSQL: Connected (via Python)"
                return 0
            else
                log_error "PostgreSQL: Connection failed"
                return 1
            fi
        fi
    fi
}

# Check Redis
check_redis() {
    log_info "Checking Redis..."

    if [ "$DOCKER_MODE" = true ]; then
        if docker compose exec -T redis redis-cli ping | grep -q PONG; then
            log_success "Redis (Docker): Healthy"
            return 0
        else
            log_error "Redis (Docker): Unhealthy or not running"
            return 1
        fi
    else
        if command -v redis-cli &> /dev/null; then
            if redis-cli ping | grep -q PONG; then
                log_success "Redis: Healthy"
                return 0
            else
                log_error "Redis: Not responding"
                return 1
            fi
        else
            # Try using Python
            if python3 -c "import redis; r = redis.from_url('$REDIS_URL'); r.ping()" 2>/dev/null; then
                log_success "Redis: Connected (via Python)"
                return 0
            else
                log_error "Redis: Connection failed"
                return 1
            fi
        fi
    fi
}

# Check Backend API
check_backend() {
    log_info "Checking Backend API..."

    if command -v curl &> /dev/null; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health" 2>/dev/null || echo "000")

        if [ "$HTTP_CODE" = "200" ]; then
            log_success "Backend API: Healthy (HTTP $HTTP_CODE)"

            # Check resilience endpoint if verbose
            if [ "$VERBOSE" = true ]; then
                RESILIENCE_STATUS=$(curl -s "$BACKEND_URL/health/resilience" 2>/dev/null || echo "{}")
                if echo "$RESILIENCE_STATUS" | grep -q "defense_level"; then
                    DEFENSE_LEVEL=$(echo "$RESILIENCE_STATUS" | grep -o '"defense_level":"[^"]*"' | cut -d'"' -f4)
                    log_info "  Resilience Status: Defense Level $DEFENSE_LEVEL"
                fi
            fi
            return 0
        elif [ "$HTTP_CODE" = "000" ]; then
            log_error "Backend API: Cannot connect"
            return 1
        else
            log_warning "Backend API: Unexpected status (HTTP $HTTP_CODE)"
            return 1
        fi
    else
        log_warning "Backend API: Cannot check (curl not installed)"
        return 1
    fi
}

# Check Frontend
check_frontend() {
    log_info "Checking Frontend..."

    if command -v curl &> /dev/null; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" 2>/dev/null || echo "000")

        if [ "$HTTP_CODE" = "200" ]; then
            log_success "Frontend: Healthy (HTTP $HTTP_CODE)"
            return 0
        elif [ "$HTTP_CODE" = "000" ]; then
            log_error "Frontend: Cannot connect"
            return 1
        else
            log_warning "Frontend: Unexpected status (HTTP $HTTP_CODE)"
            return 1
        fi
    else
        log_warning "Frontend: Cannot check (curl not installed)"
        return 1
    fi
}

# Check Celery Workers
check_celery_workers() {
    log_info "Checking Celery workers..."

    if [ "$DOCKER_MODE" = true ]; then
        if docker compose ps celery-worker | grep -q "Up"; then
            log_success "Celery Worker (Docker): Running"
            return 0
        else
            log_warning "Celery Worker (Docker): Not running"
            return 1
        fi
    else
        # Check via Celery inspect
        if command -v celery &> /dev/null; then
            cd backend 2>/dev/null || true
            ACTIVE_WORKERS=$(celery -A app.core.celery_app inspect active 2>/dev/null | grep -c "celery@" || echo "0")
            cd - &>/dev/null || true

            if [ "$ACTIVE_WORKERS" -gt 0 ]; then
                log_success "Celery Workers: $ACTIVE_WORKERS active"
                return 0
            else
                log_warning "Celery Workers: No active workers found"
                return 1
            fi
        else
            log_warning "Celery Workers: Cannot check (celery command not available)"
            return 1
        fi
    fi
}

# Check Celery Beat
check_celery_beat() {
    log_info "Checking Celery beat..."

    if [ "$DOCKER_MODE" = true ]; then
        if docker compose ps celery-beat | grep -q "Up"; then
            log_success "Celery Beat (Docker): Running"
            return 0
        else
            log_warning "Celery Beat (Docker): Not running"
            return 1
        fi
    else
        # Check if beat process is running
        if pgrep -f "celery.*beat" > /dev/null; then
            log_success "Celery Beat: Running"
            return 0
        else
            log_warning "Celery Beat: Not running"
            return 1
        fi
    fi
}

# Check Docker containers (if in Docker mode)
check_docker_containers() {
    if [ "$DOCKER_MODE" = false ]; then
        return 0
    fi

    log_info "Checking Docker containers..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker: Command not found"
        return 1
    fi

    CONTAINERS=("db" "redis" "backend" "frontend" "celery-worker" "celery-beat")
    ALL_HEALTHY=true

    for container in "${CONTAINERS[@]}"; do
        STATUS=$(docker compose ps "$container" 2>/dev/null | grep "$container" | awk '{print $3}' || echo "not found")

        if echo "$STATUS" | grep -q "Up"; then
            if [ "$VERBOSE" = true ]; then
                log_success "  Container $container: Up"
            fi
        else
            log_warning "  Container $container: $STATUS"
            ALL_HEALTHY=false
        fi
    done

    if [ "$ALL_HEALTHY" = true ]; then
        log_success "Docker Containers: All running"
        return 0
    else
        return 1
    fi
}

# Main health check
main() {
    echo "========================================="
    echo "Residency Scheduler Health Check"
    echo "========================================="

    if [ "$DOCKER_MODE" = true ]; then
        echo "Mode: Docker"
    else
        echo "Mode: Local"
    fi

    if [ "$VERBOSE" = true ]; then
        echo "Verbose: Enabled"
    fi

    echo ""

    # Run checks
    check_postgres || true
    check_redis || true
    check_backend || true
    check_frontend || true
    check_celery_workers || true
    check_celery_beat || true

    if [ "$DOCKER_MODE" = true ]; then
        check_docker_containers || true
    fi

    echo ""
    echo "========================================="

    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}Overall Status: HEALTHY${NC}"
    elif [ $EXIT_CODE -eq 1 ]; then
        echo -e "${YELLOW}Overall Status: DEGRADED${NC}"
    else
        echo -e "${RED}Overall Status: UNHEALTHY${NC}"
    fi

    echo "========================================="

    exit $EXIT_CODE
}

# Run main function
main
