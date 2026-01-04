#!/bin/bash
# ============================================================
# Script: start-local.sh
# Purpose: Start ALL local development services
# Usage: ./scripts/start-local.sh
#
# Description:
#   Starts the complete local development stack including:
#   - PostgreSQL database
#   - Redis cache/broker
#   - FastAPI backend
#   - Celery worker & beat
#   - Next.js frontend
#   - MCP server (CRITICAL for AI assistant RAG/tools)
#   - n8n workflow automation
#
# IMPORTANT: Always use this script to ensure MCP is running.
#   Without MCP, Claude Code loses access to:
#   - RAG knowledge base search
#   - 30+ scheduling/resilience MCP tools
#   - ACGME validation tools
#   - All specialized scheduling intelligence
#
# Options:
#   --build    Rebuild containers before starting
#   --logs     Follow logs after starting
# ============================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
BUILD=""
LOGS=""
for arg in "$@"; do
    case $arg in
        --build)
            BUILD="--build"
            ;;
        --logs)
            LOGS="true"
            ;;
    esac
done

# Ensure we're in project root
cd "$(dirname "$0")/.." || {
    echo -e "${RED}ERROR: Failed to change to project root${NC}" >&2
    exit 1
}

echo -e "${GREEN}Starting local development stack...${NC}"

# Start all services
if [ -n "$BUILD" ]; then
    echo -e "${YELLOW}Rebuilding containers...${NC}"
    docker compose -f docker-compose.local.yml up -d --build
else
    docker compose -f docker-compose.local.yml up -d
fi

# Wait for health checks
echo -e "${YELLOW}Waiting for services to become healthy...${NC}"
sleep 10

# Check status
echo ""
echo -e "${GREEN}Service Status:${NC}"
docker compose -f docker-compose.local.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# Verify critical services
echo ""
BACKEND_HEALTH=$(docker inspect scheduler-local-backend --format '{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
MCP_HEALTH=$(docker inspect scheduler-local-mcp --format '{{.State.Health.Status}}' 2>/dev/null || echo "unknown")

if [ "$BACKEND_HEALTH" != "healthy" ]; then
    echo -e "${YELLOW}WARNING: Backend not yet healthy (status: $BACKEND_HEALTH)${NC}"
    echo "  Wait a moment and check: docker compose -f docker-compose.local.yml ps"
fi

if [ "$MCP_HEALTH" != "healthy" ]; then
    echo -e "${YELLOW}WARNING: MCP not yet healthy (status: $MCP_HEALTH)${NC}"
    echo "  Without MCP, Claude Code has no RAG access!"
else
    echo -e "${GREEN}MCP server healthy - Claude Code has full RAG/tool access${NC}"
fi

# Ensure admin user exists (required for MCP auth)
echo ""
echo -e "${YELLOW}Checking admin user for MCP authentication...${NC}"
ADMIN_CHECK=$(docker exec scheduler-local-backend python -c "
from app.db.session import SessionLocal
from app.models.user import User
db = SessionLocal()
admin = db.query(User).filter(User.username == 'admin').first()
print('exists' if admin else 'missing')
db.close()
" 2>/dev/null || echo "error")

if [ "$ADMIN_CHECK" = "missing" ]; then
    echo -e "${YELLOW}Admin user not found - creating...${NC}"
    docker exec scheduler-local-backend python -c "
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from uuid import uuid4
db = SessionLocal()
admin = User(
    id=str(uuid4()),
    username='admin',
    hashed_password=get_password_hash('admin123'),
    role='admin',
    is_active=True
)
db.add(admin)
db.commit()
print('created')
db.close()
" 2>/dev/null && echo -e "${GREEN}Admin user created (admin/admin123)${NC}" || echo -e "${RED}Failed to create admin user${NC}"
elif [ "$ADMIN_CHECK" = "exists" ]; then
    echo -e "${GREEN}Admin user exists - MCP can authenticate${NC}"
else
    echo -e "${YELLOW}Could not verify admin user (backend may still be starting)${NC}"
fi

echo ""
echo -e "${GREEN}Access Points:${NC}"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  MCP:       http://localhost:8080"
echo "  n8n:       http://localhost:5679"

if [ -n "$LOGS" ]; then
    echo ""
    echo -e "${YELLOW}Following logs (Ctrl+C to exit)...${NC}"
    docker compose -f docker-compose.local.yml logs -f
fi
