# Makefile for Residency Scheduler
# Unified command interface for development tasks

.PHONY: help dev-start dev-stop local-start local-start-build local-stop local-status local-logs local-mlx test lint build clean install health db-migrate db-reset native-start native-start-mlx native-stop native-stop-all native-status native-logs native-restart native-bootstrap automation-preflight

# Default target
help:
	@echo "Residency Scheduler - Development Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Development:"
	@echo "  dev-start       Start Docker services (db, redis, backend, frontend)"
	@echo "  dev-stop        Stop all Docker services"
	@echo "  dev-rebuild     Rebuild and start Docker services"
	@echo "  dev-logs        View Docker logs (follow mode)"
	@echo "  local-start     One-command full local stack boot (recommended)"
	@echo "  local-start-build  Rebuild + start local stack"
	@echo "  local-stop      Stop local development stack"
	@echo "  local-status    Show local development stack status"
	@echo "  local-logs      Follow local development stack logs"
	@echo ""
	@echo "Native Development (non-Docker):"
	@echo "  native-start      Start all services natively (no Docker)"
	@echo "  native-start-mlx  Start all services + MLX inference"
	@echo "  native-stop       Stop application processes"
	@echo "  native-stop-all   Stop everything (incl. Postgres/Redis)"
	@echo "  native-status     Show status of all services"
	@echo "  native-logs       Follow native service logs"
	@echo "  native-restart    Stop and restart all services"
	@echo "  native-bootstrap  First-time setup (install + start Postgres/Redis)"
	@echo ""
	@echo "Testing:"
	@echo "  test            Run all tests (backend + frontend)"
	@echo "  test-backend    Run backend tests only"
	@echo "  test-frontend   Run frontend tests only"
	@echo "  test-coverage   Run tests with coverage report"
	@echo "  test-acgme      Run ACGME compliance tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint            Run all linters"
	@echo "  lint-fix        Run linters with auto-fix"
	@echo "  type-check      Run type checking (mypy + tsc)"
	@echo ""
	@echo "Database:"
	@echo "  db-migrate      Run database migrations"
	@echo "  db-downgrade    Rollback last migration"
	@echo "  db-reset        Reset database (WARNING: deletes data)"
	@echo ""
	@echo "Build:"
	@echo "  build           Build all containers"
	@echo "  build-backend   Build backend container only"
	@echo "  build-frontend  Build frontend container only"
	@echo ""
	@echo "Utilities:"
	@echo "  health          Check health of all services"
	@echo "  automation-preflight  Run quick full-stack checks for 0100 automations"
	@echo "  clean           Remove build artifacts and caches"
	@echo "  install         Install all dependencies"

# =============================================================================
# Development
# =============================================================================

dev-start:
	docker-compose up -d

dev-stop:
	docker-compose down

dev-rebuild:
	docker-compose up -d --build

dev-logs:
	docker-compose logs -f

local-start:
	./scripts/start-local.sh

local-start-build:
	./scripts/start-local.sh --build

local-stop:
	./scripts/dev/stop-local.sh

local-status:
	./scripts/dev/status-local.sh

local-logs:
	./scripts/dev/status-local.sh && tail -f .local/log/*.log

local-mlx:
	@echo "Starting MLX inference server on :8082 (Apple Silicon native)..."
	python -m mlx_lm.server --port 8082

# =============================================================================
# Native Development (non-Docker)
# =============================================================================

native-start:
	./scripts/start-native.sh

native-start-mlx:
	./scripts/start-native.sh --mlx

native-stop:
	./scripts/stop-native.sh

native-stop-all:
	./scripts/stop-native.sh --all

native-status:
	./scripts/status-native.sh

native-logs:
	./scripts/status-native.sh --logs

native-restart:
	./scripts/stop-native.sh && sleep 2 && ./scripts/start-native.sh

native-bootstrap:
	./scripts/start-native.sh --bootstrap

# =============================================================================
# Testing
# =============================================================================

test: test-backend test-frontend

test-backend:
	cd backend && pytest -v --tb=short

test-frontend:
	cd frontend && npm test -- --watchAll=false

test-coverage:
	cd backend && pytest --cov=app --cov-report=html --cov-report=term
	cd frontend && npm test -- --coverage --watchAll=false

test-acgme:
	cd backend && pytest -m acgme -v

# =============================================================================
# Code Quality
# =============================================================================

lint: lint-backend lint-frontend

lint-backend:
	cd backend && ruff check .

lint-frontend:
	cd frontend && npm run lint

lint-fix:
	cd backend && ruff check . --fix && ruff format .
	cd frontend && npm run lint:fix

type-check:
	cd backend && mypy app --ignore-missing-imports
	cd frontend && npm run type-check

# =============================================================================
# Database
# =============================================================================

db-migrate:
	cd backend && alembic upgrade head

db-downgrade:
	cd backend && alembic downgrade -1

db-reset:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ]
	cd backend && alembic downgrade base && alembic upgrade head

# =============================================================================
# Build
# =============================================================================

build:
	docker-compose build

build-backend:
	docker-compose build backend

build-frontend:
	docker-compose build frontend

# =============================================================================
# Utilities
# =============================================================================

health:
	@echo "=== Service Health ==="
	@echo ""
	@echo "Backend:"
	@curl -s http://localhost:8000/health 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "  Not running"
	@echo ""
	@echo "Frontend:"
	@curl -s -o /dev/null -w "  Status: %{http_code}\n" http://localhost:3000 2>/dev/null || echo "  Not running"
	@echo ""
	@echo "MCP Server:"
	@curl -s http://localhost:8081/health 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "  Not running"
	@echo ""
	@echo "PostgreSQL:"
	@pg_isready -h localhost -p 5432 2>/dev/null && echo "  Accepting connections" || echo "  Not running"
	@echo ""
	@echo "Redis:"
	@redis-cli ping 2>/dev/null && echo "  Connected" || echo "  Not running"

automation-preflight:
	@echo "=== 0100 Automation Preflight ==="
	@stack_rc=0; codex_rc=0; \
	python3 scripts/ops/stack_audit.py --quick --no-report || stack_rc=$$?; \
	./scripts/ops/codex_daily_health.sh --skip-scans || codex_rc=$$?; \
	if [ $$stack_rc -ne 0 ] || [ $$codex_rc -ne 0 ]; then \
		echo ""; \
		echo "Preflight detected issues (stack_audit=$$stack_rc, codex_daily_health=$$codex_rc)."; \
		exit 1; \
	fi

clean:
	@echo "Cleaning build artifacts..."
	rm -rf backend/__pycache__ backend/.pytest_cache backend/.mypy_cache backend/htmlcov
	rm -rf frontend/.next frontend/node_modules/.cache
	rm -rf .coverage coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Done!"

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install
