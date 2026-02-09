# macOS Local Setup (Apple Silicon)

This guide is the primary setup path for Residency Scheduler on a Mac mini M4 Pro or any macOS arm64 host.

## Prerequisites

- macOS arm64 (`uname -m` should be `arm64`)
- Xcode Command Line Tools
- Homebrew
- Git

Install required Homebrew packages:

```bash
brew install python@3.11 node@20 postgresql@15 redis pgvector libpq pkg-config cmake openblas rust jq uv
```

## One-Time Bootstrap

From the repository root:

```bash
make setup-mac
```

`make setup-mac` runs `scripts/dev/setup-macos.sh` and performs:

1. Toolchain validation for macOS arm64.
2. Environment file bootstrap from examples.
3. Local PostgreSQL/Redis startup.
4. Local database initialization (`residency_scheduler`) and `pgvector` extension creation.
5. Dependency installation for backend, frontend, and MCP server.

## Start The Full Stack

```bash
make local-up
```

This starts:

- Backend API on `http://127.0.0.1:8000`
- Celery worker
- Celery beat
- Frontend on `http://127.0.0.1:3000`
- MCP server on `http://127.0.0.1:8080`

## Validate Startup

```bash
make local-status
make health
```

Expected endpoints:

- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`
- MCP health: `http://localhost:8080/health`
- API docs: `http://localhost:8000/docs`

## Stop

```bash
make local-down
```

To also stop PostgreSQL and Redis:

```bash
./scripts/dev/stop-local.sh --with-services
```
