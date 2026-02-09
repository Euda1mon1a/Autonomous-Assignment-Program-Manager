# Local Runbook (No Containers)

Operational runbook for local-native Residency Scheduler on macOS.

## Standard Commands

- Start all app processes: `make local-up`
- Stop all app processes: `make local-down`
- Start local services only: `make local-services-start`
- Stop local services only: `make local-services-stop`
- Initialize DB + migrations + pgvector: `make local-db-init`
- Check status and health: `make local-status`

## Process Model

`Procfile.local` defines these processes:

- `backend` -> `uvicorn` on `:8000`
- `worker` -> Celery worker (default concurrency `6`)
- `beat` -> Celery beat scheduler
- `frontend` -> Next.js on `:3000`
- `mcp` -> FastMCP server on `:8080`

Runtime artifacts:

- PID files: `.local/run/*.pid`
- Logs: `.local/log/*.log`

## Health Checks

- Backend: `curl -fsS http://127.0.0.1:8000/health`
- MCP: `curl -fsS http://127.0.0.1:8080/health`
- Ports: `lsof -nP -iTCP:8000 -sTCP:LISTEN` (repeat for `3000`, `8080`, `5432`, `6379`)

## Troubleshooting

### PostgreSQL not reachable

1. Start services: `make local-services-start`
2. Verify listener: `lsof -nP -iTCP:5432 -sTCP:LISTEN`
3. Re-run DB init: `make local-db-init`

### Redis not reachable

1. Start services: `make local-services-start`
2. Verify listener: `lsof -nP -iTCP:6379 -sTCP:LISTEN`

### MCP authentication fails

1. Verify backend is up: `curl http://127.0.0.1:8000/health`
2. Check `API_USERNAME`/`API_PASSWORD` in `mcp-server/.env`
3. Ensure default admin exists (created in DEBUG when DB is empty)

### Frontend cannot reach backend

1. Confirm backend on `:8000`
2. Confirm `frontend/.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8000`

## Performance Notes (M4 Pro 64GB)

- Celery worker default concurrency is set to `6`; increase to `8` only if queue latency warrants it.
- For backend throughput testing, run uvicorn without reload and with `--workers 4` to `--workers 6`.
- PostgreSQL local tuning baseline:
  - `shared_buffers`: 2GB to 4GB
  - `work_mem`: 32MB to 64MB
  - checkpoint tuning: raise `max_wal_size` and tune checkpoint interval for bulk schedule runs
