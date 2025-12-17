# Architecture

System architecture and design documentation.

---

## Overview

Residency Scheduler is built with a modern, layered architecture designed for scalability, maintainability, and resilience.

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Browser    │  │  Calendar    │  │  API Client  │          │
│  │  (Next.js)   │  │  (ICS Feed)  │  │  (External)  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼─────────────────┼─────────────────┼───────────────────┘
          └─────────────────┴────────┬────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────┐
│                           API Gateway                            │
│                    ┌───────┴───────┐                            │
│                    │     Nginx     │                            │
│                    │  (SSL, Proxy) │                            │
│                    └───────┬───────┘                            │
└────────────────────────────┼────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                     Application Layer                            │
│  ┌─────────────────────────┴─────────────────────────────┐      │
│  │                    FastAPI Backend                     │      │
│  │  Routes → Controllers → Services → Repositories       │      │
│  └─────────────────────────┬─────────────────────────────┘      │
│                             │                                    │
│  ┌──────────────────────────┼────────────────────────────┐      │
│  │              Background Tasks (Celery)                 │      │
│  └────────────────────────────────────────────────────────┘      │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                        Data Layer                                │
│  ┌─────────────┐  ┌──────┴──────┐  ┌─────────────┐              │
│  │ PostgreSQL  │  │    Redis    │  │ Prometheus  │              │
│  │ (Primary)   │  │   (Cache)   │  │  (Metrics)  │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture Sections

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### :material-layers: [System Overview](overview.md)
High-level architecture and component interaction.
</div>

<div class="feature-card" markdown>
### :material-server: [Backend Design](backend.md)
FastAPI application structure and patterns.
</div>

<div class="feature-card" markdown>
### :material-monitor: [Frontend Design](frontend.md)
Next.js application architecture.
</div>

<div class="feature-card" markdown>
### :material-shield: [Resilience Framework](resilience.md)
Fault tolerance and system stability.
</div>

<div class="feature-card" markdown>
### :material-database: [Database Schema](database.md)
Data models and relationships.
</div>

</div>

---

## Technology Stack

### Backend

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Framework** | FastAPI | Async REST API |
| **Language** | Python 3.11+ | Backend logic |
| **ORM** | SQLAlchemy 2.0 | Database access |
| **Validation** | Pydantic | Request/response schemas |
| **Auth** | python-jose | JWT tokens |
| **Tasks** | Celery | Background processing |

### Frontend

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Framework** | Next.js 14 | React framework |
| **UI** | React 18 | Component library |
| **Types** | TypeScript | Type safety |
| **Styling** | TailwindCSS | Utility CSS |
| **State** | TanStack Query | Server state |
| **Animation** | Framer Motion | UI animations |

### Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Database** | PostgreSQL 15 | Primary storage |
| **Cache** | Redis 7 | Caching, message queue |
| **Proxy** | Nginx | Reverse proxy, SSL |
| **Monitoring** | Prometheus | Metrics collection |
| **Containers** | Docker | Containerization |

---

## Design Principles

### Layered Architecture

```
HTTP Request
     ↓
┌─────────────┐
│   Routes    │  → URL routing, authentication
└──────┬──────┘
       ↓
┌─────────────┐
│ Controllers │  → Request validation, response formatting
└──────┬──────┘
       ↓
┌─────────────┐
│  Services   │  → Business logic, orchestration
└──────┬──────┘
       ↓
┌─────────────┐
│Repositories │  → Data access abstraction
└──────┬──────┘
       ↓
┌─────────────┐
│   Models    │  → ORM entities
└──────┬──────┘
       ↓
   PostgreSQL
```

### Key Principles

- **Separation of Concerns**: Each layer has distinct responsibilities
- **Dependency Injection**: Services injected via FastAPI `Depends`
- **Repository Pattern**: Abstracts data access from business logic
- **Event-Driven**: Background tasks via Celery for async operations
- **Defense in Depth**: Multiple safety levels in resilience framework
