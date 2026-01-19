# Full Stack Wiring Recovery Runbook

Purpose: restore a working local stack (frontend, backend, database, Redis/Celery, MCP) and document the correct wiring for both humans and Claude Code.

---

## System Map (Ports + Dependencies)

```
Browser (localhost:3000)  ->  Next.js (frontend)
                                 |
                                 | /api/* rewrite (next.config.js)
                                 v
FastAPI (localhost:8000)   ->  /api/v1/*  (HTTP)
                                 |
                                 | WebSockets
                                 v
ws://localhost:8000/api/v1/ws
ws://localhost:8000/api/v1/claude-chat/ws

FastAPI -> PostgreSQL (localhost:5432)
FastAPI -> Redis (localhost:6379)
Celery worker/beat -> Redis + PostgreSQL

MCP Server (localhost:8080 or 8081) -> FastAPI /api/v1 (HTTP)
```

---

## Required Environment (Minimum)

Copy `.env.example` to `.env` and set at least:

- `DB_PASSWORD` (used by docker-compose)
- `SECRET_KEY`, `WEBHOOK_SECRET` (required when DEBUG=false; ok to use dev values locally)
- `REDIS_PASSWORD` (docker-compose Redis requires auth; default is `dev_only_password` if unset)
- `API_USERNAME`, `API_PASSWORD` (MCP server needs a real backend user)
- `NEXT_PUBLIC_API_URL` (see Wiring Notes below)
- Optional for Claude Chat: `ANTHROPIC_API_KEY` (backend Claude chat bridge)

Local (non-docker) backend uses `DATABASE_URL` + `REDIS_URL` from `backend/.env.example`.

---

## Bring-Up Options

### Option A: Docker Compose (recommended baseline)

```
cp .env.example .env
docker compose up -d
```

Notes:
- Backend + Redis + Postgres + Celery + frontend + MCP start together.
- Frontend is built (no hot reload). Rebuild to pick up UI changes:
  `docker compose build frontend && docker compose up -d frontend`

### Option B: Docker Compose + Dev Override (backend hot reload)

```
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

Notes:
- Backend hot reload is enabled.
- MCP server runs on port 8081 (matches `.mcp.json`).
- Frontend is still a production build; rebuild to pick up UI changes.

### Option C: Full Hot Reload (local dev stack)

```
docker compose -f docker-compose.local.yml up --build
```

Notes:
- Hot reload for backend and frontend.
- Uses `NEXT_PUBLIC_API_URL=/api/v1` and `BACKEND_INTERNAL_URL=http://backend:8000`
- MCP server runs on 8081.

### Option D: Hybrid Local (Docker DB/Redis + local backend/frontend)

```
docker compose up -d db redis

cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

cd frontend
npm install
npm run dev
```

Optional: start Celery locally
```
cd backend
../scripts/start-celery.sh both
```

### Option E: Hybrid Local DB/Redis + Dockerized App

Use this when PostgreSQL and Redis run on the host, while FastAPI, Celery, frontend,
and MCP run in Docker.

```
# Ensure local services are running:
# - PostgreSQL on localhost:5432
# - Redis on localhost:6379 (with auth if configured)

# Set env vars so containers can reach host services
export DATABASE_URL=postgresql://scheduler:<password>@host.docker.internal:5432/residency_scheduler
export REDIS_PASSWORD=<redis_password>
export REDIS_URL=redis://:${REDIS_PASSWORD}@host.docker.internal:6379/0
export CELERY_BROKER_URL=$REDIS_URL
export CELERY_RESULT_BACKEND=$REDIS_URL

docker compose up -d backend celery-worker celery-beat frontend mcp-server
```

Notes:
- `host.docker.internal` works on macOS/Windows. On Linux, add
  `extra_hosts: ["host.docker.internal:host-gateway"]` to services or use the host IP.
- You do not need to run the `db` or `redis` compose services in this mode.

---

## Health Checks

Docker:
```
./scripts/health-check.sh --docker
docker compose ps
```

Manual:
- API: `http://localhost:8000/health`
- Swagger: `http://localhost:8000/docs`
- Frontend: `http://localhost:3000`

---

## Wiring Notes (Critical)

1) API base path is `/api/v1`.
   - Backend mounts routes at `/api/v1` in `backend/app/main.py`.
   - There is an HTTP redirect from `/api/*` to `/api/v1/*` but **this does not apply to WebSockets**.

2) Recommended `NEXT_PUBLIC_API_URL` values:
   - Same-origin via Next rewrites: `NEXT_PUBLIC_API_URL=/api/v1`
   - Direct backend: `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`
   - Avoid `http://localhost:8000` (missing `/api/v1` will break endpoints like `/export`).

3) WebSockets must hit the backend directly (port 8000):
   - Schedule updates: `ws://localhost:8000/api/v1/ws`
   - Claude chat: `ws://localhost:8000/api/v1/claude-chat/ws`

4) MCP server ports:
   - `docker-compose.yml`: 8080
   - `docker-compose.dev.yml` or `docker-compose.local.yml`: 8081
   - `.mcp.json` currently points to 8081 (`http://127.0.0.1:8081/mcp`)

---

## Known Wiring Breaks (Fix List)

These are the current mismatches that prevent end-to-end function:

1) Claude Chat streaming endpoint mismatch.
   - Frontend uses HTTP stream: `frontend/src/hooks/useClaudeChat.ts`
     `const CLAUDE_STREAM_ENDPOINT = ${API_BASE_URL}/api/claude/chat/stream`
   - Backend exposes **WebSocket only**: `ws://localhost:8000/api/v1/claude-chat/ws`
   - Fix: update the frontend hook to use WebSocket + correct path, or add a matching HTTP streaming endpoint.

2) Claude Chat bridge docs path is stale.
   - `docs/development/CLAUDE_CHAT_BRIDGE.md` shows `/api/claude-chat/ws`
   - Actual path is `/api/v1/claude-chat/ws` (redirect does **not** apply to WebSockets)

3) `NEXT_PUBLIC_API_URL` defaults are inconsistent.
   - `.env.example` and `frontend/.env.example` set `http://localhost:8000`
   - Frontend code expects `/api/v1` to avoid 307/CORS and to keep `/export` working
   - Fix: standardize on `/api/v1` or `http://localhost:8000/api/v1`

4) MCP port mismatch depending on compose file.
   - `.mcp.json` uses 8081
   - `docker-compose.yml` exposes 8080
   - Fix: use `docker-compose.dev.yml` or update `.mcp.json` when using base compose.

---

## Claude Code Quick Checklist

1) Decide which compose file you are using.
2) Ensure `.env` (or `.env.local`) matches the API base and MCP port.
3) Start services:
   - `docker compose up -d`
   - or `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d`
4) Verify health:
   - `./scripts/health-check.sh --docker`
5) Validate MCP:
   - `curl http://127.0.0.1:8081/health` (or 8080)
6) Confirm API base:
   - `curl http://localhost:8000/api/v1/health`
