# Architecture Review Brief for Claude Code

Date: 2026-01-17
Owner: Architecture Review

## Purpose

Provide a comprehensive brief for Claude Code to review the system architecture,
identify gaps, false premises, and systemic risks, and produce actionable findings.

## Scope

- Backend: FastAPI, SQLAlchemy, Celery, Redis, Postgres
- Frontend: Next.js (App Router), React, TanStack Query
- Integrations: MCP server, Slack bot, optional automation
- Protocols: REST, GraphQL, gRPC, WebSocket, SSE
- Observability: logging, telemetry, metrics
- Security/compliance: PHI, audit, auth, rate limits

## Source-of-Truth Artifacts (Start Here)

- `ARCHITECTURE.md` (current architecture overview)
- `docs/architecture/README.md` and `docs/architecture/decisions/*.md` (ADRs)
- `docker-compose.yml` (runtime topology and dependencies)
- `backend/app/main.py` (middleware, routes, telemetry, startup)
- `backend/app/grpc/`, `backend/app/graphql/`, `backend/app/websocket/`, `backend/app/streaming/`
- `backend/app/cqrs/`, `backend/app/saga/`, `backend/app/eventbus/`
- `frontend/src/app/`, `frontend/src/lib/`, `frontend/src/hooks/`
- `slack-bot/README.md` (external client surface)

## Dependency Map (Expected Runtime Topology)

Core services:
- Backend API depends on Postgres and Redis.
- Celery worker/beat depend on Redis and Postgres.
- Frontend depends on Backend API.

Integrations:
- MCP server depends on Backend API and Redis.
- Slack bot is a separate process and can invoke CLI workflows.

Data stores:
- Postgres is primary system of record.
- Redis is cache and broker (also used for eventing).

Protocols:
- REST (primary)
- GraphQL
- gRPC
- WebSocket
- SSE (streaming)

## Known/Probable Gaps to Verify

1) Monolith premise vs reality
   - Architecture overview presents a single layered stack, but runtime is
     multi-service with async workers, brokers, and external clients.

2) API surface mismatch
   - GraphQL, gRPC, WebSocket, and SSE are present in code but not described
     in architecture docs. Contract boundaries and auth behavior may be unclear.

3) Event-driven subsystems without clear boundaries
   - CQRS, saga orchestration, event bus exist but are not tied to the primary
     request flow. Risk of duplicated business logic and inconsistent writes.

4) Operational dependencies absent from docs
   - Telemetry, metrics, cache, audit, PHI middleware, and bootstrap logic are
     critical runtime behaviors but not documented in the architecture overview.

5) Data model coverage
   - Schema diagram only shows scheduling core entities; analytics, resilience,
     eventing, and audit data are not covered.

## False Premises to Challenge

- "REST is the only interface."
- "All business logic lives in services."
- "Architecture is single-process and synchronous."
- "Database schema is limited to scheduling entities."
- "External integrations are optional and low impact."

## Review Checklist (Systemic Risks)

Service topology:
- All running services documented with dependencies and failure modes.
- Single source of truth for runtime wiring.

API boundaries:
- Every protocol documented with auth, versioning, and data contract rules.
- External clients (MCP, Slack) documented with permissions and auth flow.

Data architecture:
- Canonical source-of-truth per domain.
- Read/write paths defined for async jobs and event-driven flows.
- Retention/audit requirements documented for PHI-sensitive data.

Reliability and resilience:
- Redis dependency impact documented (cache, broker, event bus).
- Backpressure, retries, and idempotency for async paths clarified.
- Health checks and degradation behavior defined.

Security and compliance:
- AuthN/AuthZ boundaries across REST/GraphQL/gRPC/WebSockets.
- Audit trail coverage for all write paths.
- PHI exposure points identified and mitigations documented.

Observability:
- Metrics, tracing, logging, and correlation IDs documented end-to-end.
- Production visibility for async tasks and event-driven flows.

Documentation governance:
- ADRs aligned with actual code and deployment topology.
- "Architecture overview" matches runtime reality.

## Expected Review Output (Claude Code)

Provide findings ordered by severity:
- Critical: systemic risks or incorrect premises that can cause failures or
  compliance violations.
- High: major architecture gaps or missing dependencies.
- Medium/Low: documentation drift or unclear boundaries.

Each finding should include:
- What is missing or wrong.
- Why it matters (impact).
- Where to confirm (file references).
- Suggested fix (doc update or design decision).

## Open Questions to Resolve

- Which protocols are production-supported vs experimental?
- Are CQRS/saga/eventbus production paths or prototyping artifacts?
- Is MCP/Slack integration first-class or optional?
- Who owns and updates architecture docs and ADRs?

## Success Criteria

- Architecture overview reflects runtime topology and protocol surfaces.
- Dependencies and failure modes are explicit.
- Data flows include async/event-driven paths.
- Security and compliance coverage is clearly mapped.

---

## Addendum: Claude Code Findings (2026-01-18)

### Underutilized Infrastructure (Verify Status)

| Module | Location | Expected Use | Actual Use |
|--------|----------|--------------|------------|
| Feature Flags | `backend/app/features/` | All feature rollouts | 1 flag (`swap_marketplace_enabled`) |
| A/B Testing | `backend/app/experiments/ab_testing.py` | UI experiments | Unknown |
| Canary Deploy | `backend/app/deployment/canary.py` | Gradual rollouts | Unknown |
| MCP Placeholders | `mcp-server/src/scheduler_mcp/server.py` | Real data | Some return stubs (e.g., Shapley) |

**Action:** Audit usage, either wire up or document as intentionally deferred.

### Core Domain (Must Review)

Scheduling engine (not covered in original brief):
- `backend/app/scheduling/engine.py` - OR-Tools CP-SAT solver
- `backend/app/scheduling/acgme_validator.py` - ACGME compliance rules
- `backend/app/scheduling/constraints/*.py` - 30+ constraint types

Resilience framework:
- `backend/app/resilience/` - N-1/N-2 tolerance, defense levels, circuit breakers
- 34+ MCP tools for resilience monitoring (`mcp__residency-scheduler__*`)

### Known Technical Debt

Cross-reference these tracking documents:
- `docs/TODO_INVENTORY.md` - 9 tracked items (3 High, 3 Medium, 3 Low)
- `docs/PRIORITY_LIST.md` - Architecture issues and resolution status
- **Critical:** PII in git history needs `git filter-repo` (see TODO_INVENTORY)

### Frontend Reality Check

Custom implementations exist (verify before recommending libraries):
- `Toast.tsx` - Full notification system
- `DataTable.tsx` - Sorting, filtering, pagination
- `ConfirmDialog.tsx` - ARIA-compliant modal
- `AbsenceCalendar.tsx`, `ScheduleCalendar.tsx` - Calendar views

Recent additions:
- `CommandPalette/` - ⌘K global search (implemented 2026-01-18)

Labs hub (`/admin/labs/*`):
- 12 experimental visualizations
- 8 use WebGL/Three.js (performance consideration for rollout)

### Additional Open Questions

- Should Labs features be behind feature flags for gradual rollout?
- Which MCP tools are returning placeholder data vs real calculations?
- Is the constraint system documented anywhere for maintainability?
