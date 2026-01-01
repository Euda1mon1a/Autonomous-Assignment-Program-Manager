***REMOVED*** ADR-007: Monorepo with Docker Compose

**Date:** 2024-12
**Status:** Adopted

***REMOVED******REMOVED*** Context

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

***REMOVED******REMOVED*** Decision

Use a **monorepo structure** with **Docker Compose** for orchestration:

***REMOVED******REMOVED******REMOVED*** Monorepo Structure
```
Autonomous-Assignment-Program-Manager/
├── backend/              ***REMOVED*** FastAPI backend
│   ├── app/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             ***REMOVED*** Next.js frontend
│   ├── app/
│   ├── components/
│   ├── Dockerfile
│   └── package.json
├── mcp-server/           ***REMOVED*** FastMCP AI integration
│   ├── scheduler_mcp/
│   ├── Dockerfile
│   └── requirements.txt
├── load-tests/           ***REMOVED*** k6 load testing
│   ├── scenarios/
│   └── package.json
├── docs/                 ***REMOVED*** Documentation
├── scripts/              ***REMOVED*** Utility scripts
├── docker-compose.yml    ***REMOVED*** Service orchestration
└── .env.example          ***REMOVED*** Environment template
```

***REMOVED******REMOVED******REMOVED*** Docker Compose Services
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

***REMOVED******REMOVED*** Consequences

***REMOVED******REMOVED******REMOVED*** Positive
- **Single clone for full stack**: One `git clone` gets all code
- **Consistent environments**: Dev, staging, and production use same Docker configs
- **Easy onboarding**: `docker-compose up` starts entire application
- **Service discovery**: Services reference each other by name (e.g., `http://backend:8000`)
- **Dependency management**: `depends_on` ensures services start in correct order
- **Shared configuration**: Environment variables defined in `.env` file
- **Integration testing**: Full stack available for end-to-end tests
- **Version alignment**: Frontend and backend versions stay synchronized

***REMOVED******REMOVED******REMOVED*** Negative
- **Large repository**: Harder to navigate with multiple languages/frameworks
- **Docker required**: Local development requires Docker installation
- **Build time**: Initial `docker-compose build` takes 5-10 minutes
- **Resource usage**: Running all services requires ~4GB RAM
- **Monorepo complexity**: Need clear boundaries between services
- **Git history**: Frontend and backend changes interleaved in commit history

***REMOVED******REMOVED*** Implementation Notes

***REMOVED******REMOVED******REMOVED*** Local Development Workflow
```bash
***REMOVED*** First-time setup
git clone https://github.com/org/residency-scheduler.git
cd residency-scheduler
cp .env.example .env
***REMOVED*** Edit .env with your configuration

***REMOVED*** Start all services
docker-compose up -d

***REMOVED*** View logs
docker-compose logs -f backend

***REMOVED*** Run backend tests
docker-compose exec backend pytest

***REMOVED*** Run frontend tests
docker-compose exec frontend npm test

***REMOVED*** Stop all services
docker-compose down
```

***REMOVED******REMOVED******REMOVED*** Service Communication
```python
***REMOVED*** Backend API (backend/app/main.py)
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

***REMOVED*** MCP Server (mcp-server/scheduler_mcp/server.py)
import httpx

async def get_backend_health():
    async with httpx.AsyncClient() as client:
        ***REMOVED*** Service discovery via Docker network
        response = await client.get("http://backend:8000/health")
        return response.json()
```

***REMOVED******REMOVED******REMOVED*** Environment Configuration
```bash
***REMOVED*** .env file (not committed)
***REMOVED*** Database
POSTGRES_DB=residency_scheduler
POSTGRES_USER=scheduler
POSTGRES_PASSWORD=<generate-secure-password>

***REMOVED*** Backend
SECRET_KEY=<generate-32-char-secret>
API_BASE_URL=http://backend:8000

***REMOVED*** Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

***REMOVED*** MCP Server
MCP_API_BASE_URL=http://backend:8000
```

***REMOVED******REMOVED******REMOVED*** Development vs Production
```yaml
***REMOVED*** docker-compose.yml (development)
services:
  backend:
    build: ./backend
    volumes:
      - ./backend:/app  ***REMOVED*** Live code reload
    environment:
      - DEBUG=true

***REMOVED*** docker-compose.prod.yml (production)
services:
  backend:
    build: ./backend
    ***REMOVED*** No volumes (use image code)
    environment:
      - DEBUG=false
    restart: always
```

***REMOVED******REMOVED******REMOVED*** Dependency Graph
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

***REMOVED******REMOVED*** References

- `docker-compose.yml` - Service orchestration configuration
- `docker-compose.dev.yml` - Development overrides
- `docker-compose.prod.yml` - Production configuration
- `.env.example` - Environment variable template
- `backend/Dockerfile` - Backend container definition
- `frontend/Dockerfile` - Frontend container definition
- `mcp-server/Dockerfile` - MCP server container definition
- `docs/admin-manual/deployment.md` - Deployment guide
- `docs/development/DOCKER_GUIDE.md` - Docker development guide
