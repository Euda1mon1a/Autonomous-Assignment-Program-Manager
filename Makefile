# Makefile for Residency Scheduler
# Unified command interface for development tasks

.PHONY: help dev-start dev-stop test lint build clean install health db-migrate db-reset

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
	@echo "=== Docker Services ==="
	@docker-compose ps
	@echo ""
	@echo "=== Backend Health ==="
	@curl -s http://localhost:8000/health 2>/dev/null | jq . || echo "Backend not running"
	@echo ""
	@echo "=== Frontend ==="
	@curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:3000 2>/dev/null || echo "Frontend not running"

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
