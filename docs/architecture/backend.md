***REMOVED*** Backend Design

FastAPI application structure and patterns.

---

***REMOVED******REMOVED*** Layered Architecture

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

***REMOVED******REMOVED*** Directory Structure

```
backend/app/
├── api/routes/       ***REMOVED*** API endpoints (30+)
├── controllers/      ***REMOVED*** Request handlers
├── services/         ***REMOVED*** Business logic (37+)
├── repositories/     ***REMOVED*** Data access layer
├── models/           ***REMOVED*** SQLAlchemy models
├── schemas/          ***REMOVED*** Pydantic schemas
├── scheduling/       ***REMOVED*** Scheduling engine
├── resilience/       ***REMOVED*** Resilience framework
├── validators/       ***REMOVED*** ACGME validators
└── tasks/            ***REMOVED*** Celery tasks
```

---

***REMOVED******REMOVED*** Key Patterns

- **Dependency Injection** via FastAPI `Depends`
- **Repository Pattern** for data abstraction
- **Event-Driven** async processing with Celery
