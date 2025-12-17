# System Overview

High-level architecture and component interaction.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
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
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Data Layer                                │
│    PostgreSQL         Redis           Prometheus                 │
│    (Primary DB)       (Cache)         (Metrics)                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Interaction

1. **Client** sends request to Nginx
2. **Nginx** handles SSL, rate limiting, proxies to backend
3. **FastAPI** routes request through layers
4. **Services** execute business logic
5. **Repositories** interact with database
6. **Response** flows back through layers
