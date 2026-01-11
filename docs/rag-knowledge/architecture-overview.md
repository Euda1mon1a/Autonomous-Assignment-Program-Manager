# Architecture Overview

## System Design

The Residency Scheduler is a full-stack application for medical residency scheduling with ACGME compliance. It uses a layered architecture pattern with clear separation of concerns.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│                   Next.js 14 (React 18)                          │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway (Nginx)                           │
│                  SSL/TLS, Rate Limiting                          │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Application Layer                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  FastAPI Backend                         │    │
│  │    Routes → Controllers → Services → Repositories       │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Background Tasks (Celery)                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              MCP Server (AI Tools)                       │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Data Layer                                │
│    PostgreSQL         Redis           Prometheus                 │
│    (Primary DB)       (Cache)         (Metrics)                  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Interaction Flow

1. **Client** sends request to Nginx
2. **Nginx** handles SSL, rate limiting, proxies to backend
3. **FastAPI** routes request through layers
4. **Services** execute business logic
5. **Repositories** interact with database
6. **Response** flows back through layers

## Tech Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Core language |
| FastAPI | 0.109.0 | Web framework |
| SQLAlchemy | 2.0.25 | ORM (async) |
| Pydantic | 2.5.3 | Validation |
| Alembic | 1.13.1 | Migrations |
| PostgreSQL | 15 | Database |
| Redis | Latest | Cache/broker |
| Celery | 5.x | Background tasks |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 14.0.4 | App Router |
| React | 18.2.0 | UI library |
| TypeScript | 5.0+ | Type safety |
| TailwindCSS | 3.3.0 | Styling |
| TanStack Query | 5.17.0 | Data fetching |

## Layered Architecture

### Request Flow
```
Route → Controller → Service → Repository → Model
```

### Layer Responsibilities

**Routes** (`backend/app/api/routes/`)
- Define API endpoints
- Handle HTTP concerns (status codes, headers)
- Delegate to controllers
- Must be thin - no business logic

**Controllers** (`backend/app/controllers/`)
- Request/response transformation
- Input validation via Pydantic
- Orchestrate service calls
- Error handling

**Services** (`backend/app/services/`)
- Business logic lives here
- ACGME compliance validation
- Schedule generation algorithms
- Cross-cutting concerns

**Repositories** (`backend/app/repositories/`)
- Database operations
- Query building
- Data access patterns

**Models** (`backend/app/models/`)
- SQLAlchemy ORM definitions
- Database schema
- Relationships

## Directory Structure

```
├── backend/
│   ├── app/
│   │   ├── api/routes/      # Endpoints
│   │   ├── controllers/     # Request handling
│   │   ├── services/        # Business logic
│   │   ├── models/          # SQLAlchemy ORM
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── scheduling/      # Engine & validator
│   │   ├── resilience/      # Framework
│   │   └── core/            # Config, security
│   ├── alembic/             # Migrations
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js App Router
│   │   ├── components/     # React components
│   │   ├── features/       # Feature modules
│   │   └── lib/            # Utilities
│   └── tests/
├── mcp-server/             # MCP tools server (34+ tools)
├── docs/                   # Human documentation
└── .claude/                # AI agent infrastructure
```

## Key Patterns

### Dependency Injection
Use FastAPI's `Depends()` for:
- Database sessions
- Authentication
- Service instances

```python
async def get_people(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ...
```

### Async Everywhere
All database operations must be async:
```python
result = await db.execute(select(Person).where(Person.id == person_id))
return result.scalar_one_or_none()
```

### Pydantic for Validation
All request/response models use Pydantic:
```python
class PersonCreate(BaseModel):
    name: str
    pgy_level: int = Field(ge=1, le=7)
```

## Port Reference

| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 3000 | Next.js dev server |
| Backend | 8000 | FastAPI |
| Database | 5432 | PostgreSQL |
| Redis | 6379 | Cache/Celery broker |
| MCP | 8081 | AI tools server |

## Security Architecture

- JWT authentication with httpOnly cookies
- RBAC with 8 role levels
- Rate limiting on auth endpoints
- Input validation at all boundaries
- No raw SQL (SQLAlchemy ORM only)

## Background Processing

Celery handles:
- Long-running schedule generation
- Resilience analysis
- Metrics computation
- Report generation

Redis serves as:
- Celery message broker
- Cache layer
- Rate limit storage

## MCP Integration

The MCP (Model Context Protocol) server provides 34+ AI tools:
- Schedule validation
- ACGME compliance checking
- Resilience analysis
- RAG knowledge search
- Conflict detection
- Swap analysis

## Monitoring

- Prometheus metrics collection
- Grafana dashboards
- Health check endpoints
- Structured logging (JSON)
