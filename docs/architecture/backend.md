# Backend Design

FastAPI application structure and patterns.

---

## Layered Architecture

```
Routes → Controllers → Services → Repositories → Models
```

| Layer | Responsibility |
|-------|---------------|
| **Routes** | URL mapping, authentication |
| **Controllers** | Request validation, formatting |
| **Services** | Business logic |
| **Repositories** | Data access |
| **Models** | ORM entities |

---

## Directory Structure

```
backend/app/
├── api/routes/       # API endpoints (30+)
├── controllers/      # Request handlers
├── services/         # Business logic (37+)
├── repositories/     # Data access layer
├── models/           # SQLAlchemy models
├── schemas/          # Pydantic schemas
├── scheduling/       # Scheduling engine
├── resilience/       # Resilience framework
├── validators/       # ACGME validators
└── tasks/            # Celery tasks
```

---

## Key Patterns

- **Dependency Injection** via FastAPI `Depends`
- **Repository Pattern** for data abstraction
- **Event-Driven** async processing with Celery
