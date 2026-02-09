# AAPM — Coding Context

## Architecture
Route → Controller → Service → Repository → Model
- backend/app/ — FastAPI, SQLAlchemy 2.0, Pydantic 2, async everywhere
- frontend/src/ — Next.js 14 (App Router), React 18, TypeScript strict, TailwindCSS

## CRITICAL Naming Rules
- Python: snake_case everywhere
- TypeScript interfaces: camelCase (axios interceptor auto-converts keys)
- Enum VALUES: snake_case (NOT converted by axios — will break if camelCase)
- URL query params: snake_case (NOT converted — goes direct to API)
- After backend schema changes: cd frontend && npm run generate:types

## Key Paths
backend/app/api/routes/     — HTTP endpoints
backend/app/services/       — Business logic (put logic HERE, not routes)
backend/app/models/         — SQLAlchemy ORM
backend/app/schemas/        — Pydantic request/response validation
backend/app/scheduling/     — Schedule engine, ACGME validator
frontend/src/app/           — Next.js pages
frontend/src/hooks/         — React hooks
frontend/src/types/         — TypeScript types (auto-generated, never hand-edit)
frontend/src/components/    — React components

## Before Editing
1. Read the file first — follow existing patterns
2. Async for all DB operations, Depends() for DI
3. Type hints required (Python), no `any` (TypeScript)
4. Use ~column not `not column` for SQLAlchemy boolean negation
5. Use ORM only — no raw SQL

## Never Modify Without Asking
- backend/app/core/config.py, security.py
- backend/app/db/base.py, session.py
- backend/app/main.py
- Existing alembic migrations
- .env files

## Security
- Military medical data: never commit names, schedules, deployments
- No sensitive data in logs or error responses
- Pydantic for all input validation
- No hardcoded secrets
