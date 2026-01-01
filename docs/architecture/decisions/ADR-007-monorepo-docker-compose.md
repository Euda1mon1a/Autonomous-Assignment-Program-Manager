# ADR-007: Monorepo with Docker Compose

**Date:** 2024-12
**Status:** Adopted

## Context

The Residency Scheduler is a full-stack application requiring multiple services:
- **Backend API**: FastAPI application with SQLAlchemy
- **Frontend UI**: Next.js application
- **Database**: PostgreSQL for persistent data
- **Cache/Queue**: Redis for Celery and rate limiting
- **Background Workers**: Celery for periodic tasks
- **AI Integration**: MCP server for AI agent tools

Development and deployment require:
- **Consistent environments**: Dev, staging, and production should be identical
- **Easy onboarding**: New developers should run entire stack quickly
- **Local testing**: Full integration tests require all services
- **Version control**: Infrastructure as code alongside application code
- **Service orchestration**: Services must start in correct order with proper networking

## Decision

Use a **monorepo structure** with **Docker Compose** for orchestration:

### Monorepo Structure
```
Autonomous-Assignment-Program-Manager/
├── backend/              # FastAPI backend
│   ├── app/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             # Next.js frontend
│   ├── app/
│   ├── components/
│   ├── Dockerfile
│   └── package.json
├── mcp-server/           # FastMCP AI integration
│   ├── scheduler_mcp/
│   ├── Dockerfile
│   └── requirements.txt
├── load-tests/           # k6 load testing
│   ├── scenarios/
│   └── package.json
├── docs/                 # Documentation
├── scripts/              # Utility scripts
├── docker-compose.yml    # Service orchestration
└── .env.example          # Environment template
```

### Docker Compose Services
```yaml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: residency_scheduler
      POSTGRES_USER: scheduler

  redis:
    image: redis:latest

  backend:
    build: ./backend
    depends_on:
      - db
      - redis
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    depends_on:
      - backend
    ports:
      - "3000:3000"

  mcp-server:
    build: ./mcp-server
    depends_on:
      - backend
    environment:
      API_BASE_URL: http://backend:8000

  celery-worker:
    build: ./backend
    command: celery -A app.core.celery worker
    depends_on:
      - redis

  celery-beat:
    build: ./backend
    command: celery -A app.core.celery beat
    depends_on:
      - redis
```

## Consequences

### Positive
- **Single clone for full stack**: One `git clone` gets all code
- **Consistent environments**: Dev, staging, and production use same Docker configs
- **Easy onboarding**: `docker-compose up` starts entire application
- **Service discovery**: Services reference each other by name (e.g., `http://backend:8000`)
- **Dependency management**: `depends_on` ensures services start in correct order
- **Shared configuration**: Environment variables defined in `.env` file
- **Integration testing**: Full stack available for end-to-end tests
- **Version alignment**: Frontend and backend versions stay synchronized

### Negative
- **Large repository**: Harder to navigate with multiple languages/frameworks
- **Docker required**: Local development requires Docker installation
- **Build time**: Initial `docker-compose build` takes 5-10 minutes
- **Resource usage**: Running all services requires ~4GB RAM
- **Monorepo complexity**: Need clear boundaries between services
- **Git history**: Frontend and backend changes interleaved in commit history

## Implementation Notes

### Local Development Workflow
```bash
# First-time setup
git clone https://github.com/org/residency-scheduler.git
cd residency-scheduler
cp .env.example .env
# Edit .env with your configuration

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Run backend tests
docker-compose exec backend pytest

# Run frontend tests
docker-compose exec frontend npm test

# Stop all services
docker-compose down
```

### Service Communication
```python
# Backend API (backend/app/main.py)
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# MCP Server (mcp-server/scheduler_mcp/server.py)
import httpx

async def get_backend_health():
    async with httpx.AsyncClient() as client:
        # Service discovery via Docker network
        response = await client.get("http://backend:8000/health")
        return response.json()
```

### Environment Configuration
```bash
# .env file (not committed)
# Database
POSTGRES_DB=residency_scheduler
POSTGRES_USER=scheduler
POSTGRES_PASSWORD=<generate-secure-password>

# Backend
SECRET_KEY=<generate-32-char-secret>
API_BASE_URL=http://backend:8000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# MCP Server
MCP_API_BASE_URL=http://backend:8000
```

### Development vs Production
```yaml
# docker-compose.yml (development)
services:
  backend:
    build: ./backend
    volumes:
      - ./backend:/app  # Live code reload
    environment:
      - DEBUG=true

# docker-compose.prod.yml (production)
services:
  backend:
    build: ./backend
    # No volumes (use image code)
    environment:
      - DEBUG=false
    restart: always
```

### Dependency Graph
```
frontend  ──→  backend  ──→  db
                 ↓           ↑
           celery-worker  ──┘
                 ↓
               redis
                 ↑
           celery-beat  ────┘

mcp-server ──→  backend
```

## References

- `docker-compose.yml` - Service orchestration configuration
- `docker-compose.dev.yml` - Development overrides
- `docker-compose.prod.yml` - Production configuration
- `.env.example` - Environment variable template
- `backend/Dockerfile` - Backend container definition
- `frontend/Dockerfile` - Frontend container definition
- `mcp-server/Dockerfile` - MCP server container definition
- `docs/admin-manual/deployment.md` - Deployment guide
- `docs/development/DOCKER_GUIDE.md` - Docker development guide
