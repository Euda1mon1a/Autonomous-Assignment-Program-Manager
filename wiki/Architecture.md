***REMOVED*** Architecture

This document describes the system architecture of Residency Scheduler, including component design, data flow, and key architectural decisions.

---

***REMOVED******REMOVED*** System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Layer                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Browser    │  │  Mobile App  │  │  Calendar    │  │  API Client  │    │
│  │  (Next.js)   │  │   (Future)   │  │  (ICS Feed)  │  │  (External)  │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
└─────────┼─────────────────┼─────────────────┼─────────────────┼────────────┘
          │                 │                 │                 │
          └─────────────────┴────────┬────────┴─────────────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────────────┐
│                              API Gateway                                     │
├────────────────────────────────────┼────────────────────────────────────────┤
│                          ┌─────────┴─────────┐                              │
│                          │      Nginx        │                              │
│                          │  (Reverse Proxy)  │                              │
│                          │  - Rate Limiting  │                              │
│                          │  - SSL/TLS        │                              │
│                          │  - Load Balancing │                              │
│                          └─────────┬─────────┘                              │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────────────┐
│                            Application Layer                                 │
├────────────────────────────────────┼────────────────────────────────────────┤
│  ┌─────────────────────────────────┴─────────────────────────────────┐      │
│  │                        FastAPI Backend                             │      │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │      │
│  │  │   Routes    │→│ Controllers │→│  Services   │                │      │
│  │  │  (30+)      │  │             │  │  (37+)      │                │      │
│  │  └─────────────┘  └─────────────┘  └──────┬──────┘                │      │
│  │                                           │                        │      │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────┴──────┐                │      │
│  │  │ Validators  │  │ Scheduling  │  │Repositories │                │      │
│  │  │  (ACGME)    │  │   Engine    │  │             │                │      │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                │      │
│  └───────────────────────────────────────────────────────────────────┘      │
│                                     │                                        │
│  ┌──────────────────────────────────┼────────────────────────────────┐      │
│  │                          Background Tasks                          │      │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │      │
│  │  │   Celery    │  │   Celery    │  │ Resilience  │                │      │
│  │  │   Worker    │  │    Beat     │  │   Tasks     │                │      │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                │      │
│  └───────────────────────────────────────────────────────────────────┘      │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────────────┐
│                              Data Layer                                      │
├────────────────────────────────────┼────────────────────────────────────────┤
│  ┌─────────────────┐  ┌────────────┴───────────┐  ┌─────────────────┐       │
│  │   PostgreSQL    │  │         Redis          │  │   Prometheus    │       │
│  │   (Primary DB)  │  │  (Cache/Message Queue) │  │    (Metrics)    │       │
│  └─────────────────┘  └────────────────────────┘  └─────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

***REMOVED******REMOVED*** Layered Architecture

The backend follows a clean layered architecture pattern:

```
HTTP Request
     ↓
┌─────────────────┐
│     Routes      │  → Request routing and authentication
└────────┬────────┘
         ↓
┌─────────────────┐
│   Controllers   │  → Request validation, response formatting
└────────┬────────┘
         ↓
┌─────────────────┐
│    Services     │  → Business logic and orchestration
└────────┬────────┘
         ↓
┌─────────────────┐
│  Repositories   │  → Data access abstraction
└────────┬────────┘
         ↓
┌─────────────────┐
│     Models      │  → SQLAlchemy ORM entities
└────────┬────────┘
         ↓
    PostgreSQL
```

***REMOVED******REMOVED******REMOVED*** Layer Responsibilities

| Layer | Responsibility | Examples |
|-------|---------------|----------|
| **Routes** | URL mapping, middleware | `/api/schedule`, `/api/people` |
| **Controllers** | Request/response handling | Validate input, format output |
| **Services** | Business logic | Schedule generation, ACGME validation |
| **Repositories** | Data access | CRUD operations, queries |
| **Models** | Data structures | Person, Assignment, Block |

---

***REMOVED******REMOVED*** Directory Structure

```
residency-scheduler/
├── backend/
│   ├── app/
│   │   ├── api/routes/          ***REMOVED*** API endpoints (30+ files)
│   │   ├── controllers/         ***REMOVED*** Request handlers
│   │   ├── services/            ***REMOVED*** Business logic (37+ files)
│   │   ├── repositories/        ***REMOVED*** Data access layer
│   │   ├── models/              ***REMOVED*** SQLAlchemy models (20 models)
│   │   ├── schemas/             ***REMOVED*** Pydantic validation
│   │   ├── scheduling/          ***REMOVED*** Scheduling engine
│   │   ├── resilience/          ***REMOVED*** Resilience framework (19 modules)
│   │   ├── analytics/           ***REMOVED*** Analytics engines
│   │   ├── validators/          ***REMOVED*** ACGME validators
│   │   ├── notifications/       ***REMOVED*** Alert delivery
│   │   ├── maintenance/         ***REMOVED*** Backup/restore
│   │   ├── tasks/               ***REMOVED*** Celery tasks
│   │   ├── core/                ***REMOVED*** Config, security, Celery
│   │   ├── db/                  ***REMOVED*** Database session
│   │   ├── middleware/          ***REMOVED*** Cross-cutting concerns
│   │   ├── cli/                 ***REMOVED*** Admin CLI tools
│   │   └── main.py              ***REMOVED*** FastAPI app
│   ├── alembic/                 ***REMOVED*** Database migrations
│   ├── tests/                   ***REMOVED*** Backend tests
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/                 ***REMOVED*** Next.js App Router
│   │   ├── features/            ***REMOVED*** Feature modules (13)
│   │   ├── components/          ***REMOVED*** Reusable components
│   │   ├── contexts/            ***REMOVED*** React Context
│   │   ├── hooks/               ***REMOVED*** Custom hooks
│   │   ├── lib/                 ***REMOVED*** API client, utilities
│   │   ├── types/               ***REMOVED*** TypeScript types
│   │   └── mocks/               ***REMOVED*** MSW mocks
│   ├── __tests__/               ***REMOVED*** Unit tests
│   ├── e2e/                     ***REMOVED*** E2E tests
│   └── package.json
│
├── nginx/                       ***REMOVED*** Reverse proxy
├── monitoring/                  ***REMOVED*** Prometheus setup
├── n8n/                         ***REMOVED*** ChatOps workflows
├── docs/                        ***REMOVED*** Documentation
├── scripts/                     ***REMOVED*** Helper scripts
└── docker-compose.yml           ***REMOVED*** Container orchestration
```

---

***REMOVED******REMOVED*** Core Components

***REMOVED******REMOVED******REMOVED*** Backend Services (37+)

***REMOVED******REMOVED******REMOVED******REMOVED*** Scheduling Services
| Service | Purpose |
|---------|---------|
| `schedule_service.py` | Schedule generation and management |
| `assignment_service.py` | Assignment operations |
| `block_service.py` | Block management |
| `fmit_scheduler_service.py` | FMIT scheduling logic |

***REMOVED******REMOVED******REMOVED******REMOVED*** People & Credentials
| Service | Purpose |
|---------|---------|
| `person_service.py` | Resident/faculty management |
| `certification_service.py` | Certification tracking |
| `credential_service.py` | Procedure credentials |
| `procedure_service.py` | Procedure management |

***REMOVED******REMOVED******REMOVED******REMOVED*** Swap System
| Service | Purpose |
|---------|---------|
| `swap_request_service.py` | Swap request handling |
| `swap_auto_matcher.py` | 5-factor scoring algorithm |
| `swap_validation.py` | Swap validation logic |
| `swap_executor.py` | Transaction execution |

***REMOVED******REMOVED******REMOVED******REMOVED*** Conflict Management
| Service | Purpose |
|---------|---------|
| `conflict_alert_service.py` | Conflict detection |
| `conflict_auto_detector.py` | Automated detection |
| `conflict_auto_resolver.py` | 5 resolution strategies |

***REMOVED******REMOVED******REMOVED******REMOVED*** Analytics & Optimization
| Service | Purpose |
|---------|---------|
| `pareto_optimization_service.py` | Multi-objective optimization |
| `heatmap_service.py` | Visualization data |
| `unified_heatmap_service.py` | Unified heatmap |

***REMOVED******REMOVED******REMOVED*** Database Models (20)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Core Entities                             │
├─────────────────────────────────────────────────────────────────┤
│  Person ←──────→ Assignment ←──────→ Block                      │
│    │                  │                │                        │
│    │                  ↓                │                        │
│    │           ScheduleRun             │                        │
│    │                                   │                        │
│    ↓                                   │                        │
│  Absence                               │                        │
│  Certification                         │                        │
│  ProcedureCredential ←──→ Procedure    │                        │
│  FacultyPreference                     │                        │
│                                        │                        │
├─────────────────────────────────────────────────────────────────┤
│                       Swap System                                │
├─────────────────────────────────────────────────────────────────┤
│  Swap ←──────→ Person (requester/responder)                     │
│    │                                                            │
│    ↓                                                            │
│  ConflictAlert                                                  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    Support Entities                              │
├─────────────────────────────────────────────────────────────────┤
│  User ←──→ TokenBlacklist                                       │
│  RotationTemplate                                               │
│  CallAssignment                                                 │
│  CalendarSubscription                                           │
│  Settings                                                       │
│  Notification                                                   │
│  ResilienceMetrics                                              │
│  AuditLog                                                       │
└─────────────────────────────────────────────────────────────────┘
```

***REMOVED******REMOVED******REMOVED*** Frontend Features (13 modules)

| Feature | Description |
|---------|-------------|
| `analytics` | Multi-panel analytics dashboard |
| `audit` | Audit log viewer |
| `call-roster` | Call rotation management |
| `conflicts` | Conflict resolution UI |
| `daily-manifest` | Daily briefing view |
| `fmit-timeline` | Gantt-style timeline |
| `heatmap` | Workload visualizations |
| `import-export` | Data import/export |
| `my-dashboard` | Personal dashboard |
| `swap-marketplace` | Swap trading platform |
| `templates` | Template management |

---

***REMOVED******REMOVED*** Scheduling Engine

The scheduling engine uses multiple algorithms:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Scheduling Engine                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   Greedy    │     │   CP-SAT    │     │    PuLP     │       │
│  │  Algorithm  │     │  (OR-Tools) │     │   (LP/MIP)  │       │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘       │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
│                             ↓                                   │
│                    ┌─────────────┐                              │
│                    │   Hybrid    │                              │
│                    │  Selector   │                              │
│                    └──────┬──────┘                              │
│                           ↓                                     │
│                    ┌─────────────┐                              │
│                    │   ACGME     │                              │
│                    │  Validator  │                              │
│                    └──────┬──────┘                              │
│                           ↓                                     │
│                    ┌─────────────┐                              │
│                    │   Pareto    │                              │
│                    │ Optimizer   │                              │
│                    │  (NSGA-II)  │                              │
│                    └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

***REMOVED******REMOVED******REMOVED*** Algorithm Selection

| Algorithm | Use Case | Trade-offs |
|-----------|----------|------------|
| **Greedy** | Fast initial schedules | May miss optimal solutions |
| **CP-SAT** | Constraint satisfaction | Slower but guaranteed feasibility |
| **PuLP** | Linear optimization | Good for fairness metrics |
| **Hybrid** | Production use | Combines strengths of all |

***REMOVED******REMOVED******REMOVED*** ACGME Constraints

The validator enforces:

- **80-hour rule**: Max 80 hours/week (rolling 4-week average)
- **1-in-7 rule**: One 24-hour period off per 7 days
- **Supervision ratios**:
  - PGY-1: 1:2 faculty-to-resident
  - PGY-2/3: 1:4 faculty-to-resident
- **24-hour shift limits**: Maximum continuous duty hours

---

***REMOVED******REMOVED*** Resilience Framework

The resilience system implements cross-industry patterns:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Resilience Framework                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              Defense in Depth (5 Levels)              │      │
│  │  GREEN → YELLOW → ORANGE → RED → BLACK               │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Utilization │  │ Contingency │  │   Static    │            │
│  │  Monitor    │  │  Analysis   │  │  Stability  │            │
│  │   (80%)     │  │  (N-1/N-2)  │  │ (Fallbacks) │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Sacrifice  │  │  Prometheus │  │   Celery    │            │
│  │  Hierarchy  │  │   Metrics   │  │   Tasks     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

***REMOVED******REMOVED******REMOVED*** Defense Levels

| Level | Threshold | Response |
|-------|-----------|----------|
| GREEN | < 70% | Normal operations |
| YELLOW | 70-80% | Warning alerts |
| ORANGE | 80-90% | Active mitigation |
| RED | 90-95% | Emergency protocols |
| BLACK | > 95% | Crisis management |

See [Resilience Framework](Resilience-Framework) for details.

---

***REMOVED******REMOVED*** Data Flow

***REMOVED******REMOVED******REMOVED*** Schedule Generation Flow

```
User Request
     ↓
┌─────────────────┐
│  Validate Input │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Load Constraints│  ← People, Absences, Templates
└────────┬────────┘
         ↓
┌─────────────────┐
│ Run Algorithms  │  ← Greedy/CP-SAT/PuLP/Hybrid
└────────┬────────┘
         ↓
┌─────────────────┐
│ ACGME Validation│  ← 80-hour, 1-in-7, Supervision
└────────┬────────┘
         ↓
┌─────────────────┐
│ Pareto Optimize │  ← Fairness, Coverage, Preferences
└────────┬────────┘
         ↓
┌─────────────────┐
│  Save Schedule  │  → Assignments, ScheduleRun
└────────┬────────┘
         ↓
    Response
```

***REMOVED******REMOVED******REMOVED*** Swap Request Flow

```
Swap Request
     ↓
┌─────────────────┐
│ Auto-Matching   │  ← 5-factor scoring
└────────┬────────┘
         ↓
┌─────────────────┐
│ Notify Matches  │  → Email/In-app/Slack
└────────┬────────┘
         ↓
┌─────────────────┐
│ Accept/Reject   │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Validate Swap   │  ← Conflict detection
└────────┬────────┘
         ↓
┌─────────────────┐
│ Execute Swap    │  → Update assignments
└────────┬────────┘
         ↓
┌─────────────────┐
│ Audit & Notify  │
└─────────────────┘
```

---

***REMOVED******REMOVED*** Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Security Layers                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │                  Transport (HTTPS)                   │       │
│  └─────────────────────────────────────────────────────┘       │
│                             ↓                                   │
│  ┌─────────────────────────────────────────────────────┐       │
│  │           Authentication (JWT + Bcrypt)              │       │
│  └─────────────────────────────────────────────────────┘       │
│                             ↓                                   │
│  ┌─────────────────────────────────────────────────────┐       │
│  │        Authorization (Role-Based Access)             │       │
│  │        Admin | Coordinator | Faculty                 │       │
│  └─────────────────────────────────────────────────────┘       │
│                             ↓                                   │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              Input Validation (Pydantic)             │       │
│  └─────────────────────────────────────────────────────┘       │
│                             ↓                                   │
│  ┌─────────────────────────────────────────────────────┐       │
│  │            SQL Injection Prevention (ORM)            │       │
│  └─────────────────────────────────────────────────────┘       │
│                             ↓                                   │
│  ┌─────────────────────────────────────────────────────┐       │
│  │           Audit Logging (All Changes)                │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

***REMOVED******REMOVED******REMOVED*** Role-Based Access Control

| Role | Permissions |
|------|-------------|
| **Admin** | Full system access, settings, user management |
| **Coordinator** | Schedule management, no settings access |
| **Faculty** | View-only, personal schedule management |

---

***REMOVED******REMOVED*** Scalability

***REMOVED******REMOVED******REMOVED*** Horizontal Scaling Points

```
                    Load Balancer
                         │
         ┌───────────────┼───────────────┐
         ↓               ↓               ↓
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │ Backend │    │ Backend │    │ Backend │
    │   ***REMOVED***1    │    │   ***REMOVED***2    │    │   ***REMOVED***n    │
    └────┬────┘    └────┬────┘    └────┬────┘
         │              │              │
         └──────────────┼──────────────┘
                        ↓
              ┌─────────────────┐
              │  PostgreSQL     │
              │  (Connection    │
              │   Pooling)      │
              └─────────────────┘
```

***REMOVED******REMOVED******REMOVED*** Scaling Strategies

| Component | Strategy |
|-----------|----------|
| **Backend** | Stateless, horizontal scaling |
| **Celery** | Multiple workers with queues |
| **Database** | Connection pooling, read replicas |
| **Cache** | Redis cluster |
| **Frontend** | CDN, static generation |

---

***REMOVED******REMOVED*** Monitoring & Observability

```
┌─────────────────────────────────────────────────────────────────┐
│                    Observability Stack                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Prometheus │  │   Grafana   │  │   Sentry    │            │
│  │  (Metrics)  │  │ (Dashboards)│  │  (Errors)   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
│  Endpoints:                                                     │
│  • /health         - Basic health check                        │
│  • /health/ready   - Readiness probe                           │
│  • /metrics        - Prometheus metrics                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

***REMOVED******REMOVED*** Technology Decisions

***REMOVED******REMOVED******REMOVED*** Why FastAPI?
- Automatic OpenAPI documentation
- Async support for I/O operations
- Type hints with Pydantic validation
- High performance

***REMOVED******REMOVED******REMOVED*** Why PostgreSQL?
- ACID compliance for scheduling data
- Advanced query capabilities
- JSON support for flexible schemas
- Proven reliability

***REMOVED******REMOVED******REMOVED*** Why Celery?
- Distributed task processing
- Scheduled jobs (beat)
- Result tracking
- Retry mechanisms

***REMOVED******REMOVED******REMOVED*** Why Next.js?
- Server-side rendering
- API routes
- Optimized builds
- React ecosystem

---

***REMOVED******REMOVED*** Related Documentation

- [API Reference](API-Reference) - Endpoint documentation
- [Configuration](Configuration) - Environment variables
- [Resilience Framework](Resilience-Framework) - Advanced resilience
- [Development](Development) - Contributing guide
